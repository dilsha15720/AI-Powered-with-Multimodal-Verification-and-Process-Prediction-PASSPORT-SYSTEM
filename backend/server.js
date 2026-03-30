const express = require("express");
const cors = require("cors");
const axios = require("axios");
const crypto = require("crypto");

const app = express();
app.use(cors());
app.use(express.json());

function hash(data){
  return crypto.createHash("sha256").update(data).digest("hex");
}

// Configurable service endpoints (useful for local dev vs docker compose)
const AI_URL = process.env.AI_URL || 'http://ai-service:8000';
const BLOCKCHAIN_URL = process.env.BLOCKCHAIN_URL || 'http://blockchain-sim:7000';

// Simple admin auth: use env ADMIN_PASSWORD or default. Tokens are stored in-memory for this prototype.
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'pass1234';
const adminTokens = new Set();

// Admin login endpoint (returns a short-lived token stored in memory)
app.post('/api/admin/login', (req, res) => {
  const { username, password } = req.body || {};
  // very small check for demo purposes
  if (username === 'admin' && password === ADMIN_PASSWORD) {
    const token = crypto.randomBytes(16).toString('hex');
    adminTokens.add(token);
    return res.json({ token });
  }
  return res.status(401).json({ error: 'invalid credentials' });
});

// Admin logout (optional)
app.post('/api/admin/logout', (req, res) => {
  const token = req.header('x-admin-token');
  if (token && adminTokens.has(token)) {
    adminTokens.delete(token);
  }
  res.json({ ok: true });
});

const fs = require('fs');
const path = require('path');

// Load applications from a data file if present. This moves away from hard-coded mock data.
const APPS_FILE = path.join(__dirname, 'data', 'apps.json');
let applications = [];
function loadApps(){
  try{
    if(fs.existsSync(APPS_FILE)){
      const raw = fs.readFileSync(APPS_FILE,'utf8');
      applications = JSON.parse(raw || '[]');
      console.log(`Loaded ${applications.length} applications from ${APPS_FILE}`);
      return;
    }
  }catch(e){ console.warn('Failed to load apps.json', e); }
  // fallback to empty list
  applications = [];
}

function saveApps(){
  try{
    const dir = path.dirname(APPS_FILE);
    if(!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(APPS_FILE, JSON.stringify(applications, null, 2), 'utf8');
    return true;
  }catch(e){ console.error('Failed to save apps.json', e); return false; }
}

loadApps();

app.get('/api/apps', (req,res)=>{
  // Always reload to reflect external edits
  loadApps();
  res.json({applications});
});

// Create a new application (in-memory)
app.post('/api/apps', (req,res)=>{
  const body = req.body || {};
  const nextId = applications.length ? Math.max(...applications.map(a=>a.id)) + 1 : 1;
  const newApp = {
    id: nextId,
    name: body.name || `Applicant ${nextId}`,
    country: body.country || 'Unknown',
    status: body.status || 'Submitted',
    submitted_at: new Date().toISOString().slice(0,10),
    document_quality: body.document_quality || 'Unknown'
  };
  applications.push(newApp);
  const ok = saveApps();
  if(!ok) return res.status(500).json({error:'failed to persist application'});
  res.status(201).json(newApp);
});

app.get('/api/apps/:id', (req,res)=>{
  const appId = Number(req.params.id);
  const a = applications.find(x=>x.id===appId);
  if(!a) return res.status(404).json({error:'not found'});
  res.json(a);
});

// Proxy to AI service for process prediction
app.post('/api/analyze', async (req,res)=>{
  try{
  const ai = await axios.post(`${AI_URL}/predict`, req.body);
  // send to blockchain-sim to store a hash
  const payload = { source: 'backend-analyze', data: req.body };
  const chainResp = await axios.post(`${BLOCKCHAIN_URL}/hash`, payload).catch(()=>null);
    const blockchainHash = chainResp?.data?.hash || hash(JSON.stringify(req.body));

    res.json({...ai.data, blockchainHash});
  }catch(err){
    console.error(err?.message||err);
    res.status(500).json({error:'ai-service error'});
  }
});

// Endpoint to run verification (multimodal) via AI service
app.post('/api/verify', async (req,res)=>{
  try{
  const ai = await axios.post(`${AI_URL}/verify`, req.body);
    res.json(ai.data);
  }catch(err){
    console.error(err?.message||err);
    res.status(500).json({error:'ai-service error'});
  }
});

// Simulate state transition on an application and request a new prediction
app.post('/api/apps/:id/process', async (req,res)=>{
  const appId = Number(req.params.id);
  const a = applications.find(x=>x.id===appId);
  if(!a) return res.status(404).json({error:'not found'});
  // move status forward for demo
  // Require admin token for processing actions
  const adminToken = req.header('x-admin-token');
  if(!adminToken || !adminTokens.has(adminToken)){
    return res.status(401).json({error:'admin authentication required'});
  }
  a.status = req.body.status || 'Processing';
  // request prediction for updated app
  const ai = await axios.post(`${AI_URL}/predict`, a).catch(()=>null);
  res.json({application: a, prediction: ai?.data});
});

// Query blockchain chain
app.get('/api/blockchain/chain', async (req,res)=>{
  try{
  const r = await axios.get(`${BLOCKCHAIN_URL}/chain`);
    res.json(r.data);
  }catch(e){
    res.status(500).json({error:'blockchain unreachable'});
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, ()=>console.log(`Backend running on ${PORT}`));
