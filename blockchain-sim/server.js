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
  const payload = { source, data, timestamp };
  const hash = sha256(payload);
  const block = { index: chain.length + 1, timestamp, hash, payload };
  chain.push(block);
  res.json({ ok:true, hash, block });
});

app.get('/chain', (req,res)=>{
  res.json({ chain, length: chain.length });
});

const PORT = process.env.PORT || 7000;
app.listen(PORT, ()=>console.log(`blockchain-sim listening on ${PORT}`));
