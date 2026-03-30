const path = require('path');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();

const DB_DIR = path.join(__dirname, 'data');
const DB_PATH = path.join(DB_DIR, 'app.db');

let db = null;

function init(){
  return new Promise((resolve,reject)=>{
    try{
      if(!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });
      db = new sqlite3.Database(DB_PATH, (err)=>{
        if(err) return reject(err);
        // create apps table if missing
        db.run(`CREATE TABLE IF NOT EXISTS apps (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          country TEXT,
          status TEXT,
          submitted_at TEXT,
          document_quality TEXT
        )`, (err2)=>{
          if(err2) return reject(err2);
          resolve();
        });
      });
    }catch(e){reject(e)}
  })
}

function getAllApps(){
  return new Promise((resolve,reject)=>{
    db.all('SELECT * FROM apps ORDER BY id DESC', [], (err, rows)=>{
      if(err) return reject(err);
      resolve(rows||[]);
    })
  })
}

function getAppById(id){
  return new Promise((resolve,reject)=>{
    db.get('SELECT * FROM apps WHERE id = ?', [id], (err,row)=>{
      if(err) return reject(err);
      resolve(row||null);
    })
  })
}

function createApp(app){
  return new Promise((resolve,reject)=>{
    const stmt = db.prepare('INSERT INTO apps (name,country,status,submitted_at,document_quality) VALUES (?,?,?,?,?)');
    stmt.run([app.name, app.country, app.status, app.submitted_at, app.document_quality], function(err){
      if(err) return reject(err);
      resolve({ id: this.lastID, ...app });
    });
  })
}

function updateAppStatus(id, status){
  return new Promise((resolve,reject)=>{
    db.run('UPDATE apps SET status = ? WHERE id = ?', [status, id], function(err){
      if(err) return reject(err);
      resolve(this.changes);
    })
  })
}

module.exports = { init, getAllApps, getAppById, createApp, updateAppStatus };
