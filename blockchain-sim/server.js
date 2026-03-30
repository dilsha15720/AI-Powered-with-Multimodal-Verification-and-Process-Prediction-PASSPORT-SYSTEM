const express = require('express');
const bodyParser = require('body-parser');
const crypto = require('crypto');

const app = express();
app.use(bodyParser.json());

let chain = [];

function sha256(d){
  return crypto.createHash('sha256').update(JSON.stringify(d)).digest('hex');
}

app.post('/hash', (req,res)=>{
  const { source, data } = req.body || {};
  const timestamp = new Date().toISOString();
  const payload = { source, data };
  const index = chain.length + 1;
  const prevHash = chain.length ? chain[chain.length - 1].hash : null;
  const toHash = { index, timestamp, payload, prevHash };
  const hash = sha256(toHash);
  const block = { index, timestamp, payload, prevHash, hash };
  chain.push(block);
  res.json({ ok:true, hash, block });
});

app.get('/chain', (req,res)=>{
  res.json({ chain, length: chain.length });
});

// Validate chain integrity: check prevHash links and recompute hashes
app.get('/validate', (req,res)=>{
  const errors = [];
  for(let i=0;i<chain.length;i++){
    const b = chain[i];
    const expectedPrev = i===0 ? null : chain[i-1].hash;
    if(b.prevHash !== expectedPrev){
      errors.push({ index: b.index, problem: 'prevHash mismatch', expected: expectedPrev, found: b.prevHash });
    }
    const toHash = { index: b.index, timestamp: b.timestamp, payload: b.payload, prevHash: b.prevHash };
    const recomputed = sha256(toHash);
    if(recomputed !== b.hash){
      errors.push({ index: b.index, problem: 'hash mismatch', expected: recomputed, found: b.hash });
    }
  }
  res.json({ ok: errors.length===0, errors });
});

const PORT = process.env.PORT || 7000;
app.listen(PORT, ()=>console.log(`blockchain-sim listening on ${PORT}`));
