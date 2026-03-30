const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const DB_DIR = path.join(__dirname, '..', 'data');
const DB_PATH = path.join(DB_DIR, 'app.db');

if(!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });

const db = new sqlite3.Database(DB_PATH, (err)=>{
  if(err){
    console.error('Failed to open DB', err);
    process.exit(2);
  }
  db.serialize(()=>{
    db.run(`CREATE TABLE IF NOT EXISTS apps (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT,
      country TEXT,
      status TEXT,
      submitted_at TEXT,
      document_quality TEXT
    )`, (e)=>{
      if(e){ console.error('Migration failed', e); process.exit(2); }
      console.log('Migration complete — apps table created (if missing)');
      db.close();
    });
  });
});
