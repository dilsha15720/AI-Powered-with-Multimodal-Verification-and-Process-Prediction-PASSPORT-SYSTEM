const express = require("express");
const cors = require("cors");
const axios = require("axios");
const crypto = require("crypto");
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const dbModule = require('./db');

const app = express();
app.use(cors());
app.use(express.json());

function hash(data){
  return crypto.createHash("sha256").update(data).digest("hex");
}

// Configurable service endpoints (useful for local dev vs docker compose)
const AI_URL = process.env.AI_URL || 'http://ai-service:8000';
const BLOCKCHAIN_URL = process.env.BLOCKCHAIN_URL || 'http://blockchain-sim:7000';

// Admin auth: switch to JWT (stateless). Use ADMIN_PASSWORD and ADMIN_JWT_SECRET from env.
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'pass1234';
const ADMIN_JWT_SECRET = process.env.ADMIN_JWT_SECRET || 'dev-secret';

// Admin login issues a JWT (expires in 2 hours)
app.post('/api/admin/login', (req, res) => {
  const { username, password } = req.body || {};
  if (username === 'admin' && password === ADMIN_PASSWORD) {
    const token = jwt.sign({ user: 'admin' }, ADMIN_JWT_SECRET, { expiresIn: '2h' });
    return res.json({ token });
  }
  return res.status(401).json({ error: 'invalid credentials' });
});

// Logout (stateless for JWT) — client can just drop token; endpoint present for parity
app.post('/api/admin/logout', (req, res) => {
  res.json({ ok: true });
});

// middleware to verify Authorization: Bearer <token>
function verifyAdminMiddleware(req, res, next){
  const auth = req.header('authorization') || '';
  const parts = auth.split(' ');
  if(parts.length!==2 || parts[0].toLowerCase()!=='bearer') return res.status(401).json({ error: 'admin authentication required' });
  const token = parts[1];
  try{
    const payload = jwt.verify(token, ADMIN_JWT_SECRET);
    req.admin = payload;
    next();
  }catch(e){
    return res.status(401).json({ error: 'invalid or expired token' });
  }
}

const fs = require('fs');
const path = require('path');

// Attempt to initialize DB; fall back to file-based store if DB not available
let usingDb = false;
dbModule.init().then(()=>{
  console.log('SQLite DB initialized');
  usingDb = true;
}).catch((e)=>{
  console.warn('SQLite initialization failed, falling back to file store', e?.message||e);
  usingDb = false;
});

// File fallback
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

app.get('/api/apps', async (req,res)=>{
  try{
    if(usingDb){
      const rows = await dbModule.getAllApps();
      return res.json({ applications: rows });
    }
    loadApps();
    return res.json({ applications });
  }catch(e){
    console.error('Failed to fetch apps', e);
    res.status(500).json({ error: 'failed to load applications' });
  }
});

// Create a new application (in-memory)
app.post('/api/apps', async (req,res)=>{
  try{
    const body = req.body || {};
    const newApp = {
      name: body.name || 'Applicant',
      country: body.country || 'Unknown',
      status: body.status || 'Submitted',
      submitted_at: new Date().toISOString().slice(0,10),
      document_quality: body.document_quality || 'Unknown'
    };
    if(usingDb){
      const created = await dbModule.createApp(newApp);
      return res.status(201).json(created);
    }
    const nextId = applications.length ? Math.max(...applications.map(a=>a.id)) + 1 : 1;
    const withId = { id: nextId, ...newApp };
    applications.push(withId);
    const ok = saveApps();
    if(!ok) return res.status(500).json({error:'failed to persist application'});
    return res.status(201).json(withId);
  }catch(e){
    console.error('Failed to create app', e);
    res.status(500).json({ error: 'failed to create application' });
  }
});

app.get('/api/apps/:id', async (req,res)=>{
  try{
    const appId = Number(req.params.id);
    if(usingDb){
      const row = await dbModule.getAppById(appId);
      if(!row) return res.status(404).json({ error: 'not found' });
      return res.json(row);
    }
    const a = applications.find(x=>x.id===appId);
    if(!a) return res.status(404).json({error:'not found'});
    res.json(a);
  }catch(e){ res.status(500).json({ error: 'failed to load application' }) }
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
app.post('/api/apps/:id/process', verifyAdminMiddleware, async (req,res)=>{
  try{
    const appId = Number(req.params.id);
    if(usingDb){
      const row = await dbModule.getAppById(appId);
      if(!row) return res.status(404).json({ error: 'not found' });
      const newStatus = req.body.status || 'Processing';
      await dbModule.updateAppStatus(appId, newStatus);
      const updated = await dbModule.getAppById(appId);
      const ai = await axios.post(`${AI_URL}/predict`, updated).catch(()=>null);
      return res.json({ application: updated, prediction: ai?.data });
    }
    const a = applications.find(x=>x.id===appId);
    if(!a) return res.status(404).json({error:'not found'});
    a.status = req.body.status || 'Processing';
    saveApps();
    const ai = await axios.post(`${AI_URL}/predict`, a).catch(()=>null);
    res.json({application: a, prediction: ai?.data});
  }catch(e){console.error(e); res.status(500).json({ error: 'processing failed' })}
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
