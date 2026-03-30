import React, { useEffect, useState } from 'react'
import axios from 'axios'
import './styles.scss'

function statusClass(s){
  if(!s) return '';
  if(s.toLowerCase().includes('submit')) return 'status-submitted';
  if(s.toLowerCase().includes('verify')) return 'status-verified';
  return 'status-review';
}

function Dashboard({onBack}){
  const [apps,setApps] = useState([])
  const [selected,setSelected] = useState(null)
  const [chain,setChain] = useState([])
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000'
  const [showApplyModal,setShowApplyModal] = useState(false)
  const [applyData,setApplyData] = useState({name:'',country:'',document_quality:''})

  const load = async ()=>{
    try{const r = await axios.get(`${API_BASE}/api/apps`); setApps(r.data.applications || [])}catch(e){console.error(e)}
    try{const c = await axios.get(`${API_BASE}/api/blockchain/chain`); setChain(c.data.chain || [])}catch(e){console.warn('chain fetch failed')}
  }

  useEffect(()=>{load()},[])

  // if there is a prefill from landing, open apply modal with that data
  useEffect(()=>{
    try{
      const p = sessionStorage.getItem('sp_apply_prefill')
      if(p){
        const obj = JSON.parse(p)
        setApplyData(prev=>({...prev,...obj}))
        setShowApplyModal(true)
        sessionStorage.removeItem('sp_apply_prefill')
      }
    }catch(e){/* ignore */}
  },[])

  const analyze = async (app)=>{
    const r = await axios.post(`${API_BASE}/api/analyze`, app)
    alert(`Prediction: ${r.data.risk} (confidence:${r.data.confidence})\nHash: ${r.data.blockchainHash}`)
    load()
  }

  const verify = async (app)=>{
    const r = await axios.post(`${API_BASE}/api/verify`, app)
    alert(`Verify: ${r.data.verdict} (conf:${r.data.confidence})`)
  }

  const submitApplication = async (payload)=>{
    try{
      const r = await axios.post(`${API_BASE}/api/apps`, payload)
      alert('Application submitted: #' + r.data.id)
      setShowApplyModal(false)
      load()
    }catch(e){
      alert('Failed to submit')
    }
  }

  return (
    <div className="container">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
        <div style={{display:'flex',gap:12,alignItems:'center'}}>
          <div className="logo">AI</div>
          <div>
            <h2 style={{margin:0}}>Smart Passport System</h2>
            <div className="small">AI-powered multimodal verification & blockchain logging</div>
          </div>
        </div>
        <div style={{display:'flex',gap:8}}>
          <button className="pill" onClick={onBack}>Back to Home</button>
          <div className="pill">Research Prototype</div>
        </div>
      </div>

      <div className="grid">
        <div>
          <div className="card apps-list">
            <h3>Applications</h3>
            <table>
              <thead>
                <tr><th>ID</th><th>Name</th><th>Country</th><th>Status</th><th></th></tr>
              </thead>
              <tbody>
                {apps.map(a=> (
                  <tr key={a.id} onClick={()=>setSelected(a)} style={{cursor:'pointer'}}>
                    <td>{a.id}</td>
                    <td>{a.name}</td>
                    <td>{a.country}</td>
                    <td className={statusClass(a.status)}>{a.status}</td>
                    <td><button className="btn" onClick={(e)=>{e.stopPropagation(); analyze(a)}}>Analyze</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selected && <div className="card detail" style={{marginTop:16}}>
            <h3>Application #{selected.id}</h3>
            <p><strong>{selected.name}</strong> — <span className="small">{selected.country}</span></p>
            <p className="small">Submitted: {selected.submitted_at}</p>
            <p>Doc quality: <span className="pill">{selected.document_quality}</span></p>
            <div style={{display:'flex',gap:12,marginTop:8}}>
              <button className="btn" onClick={()=>verify(selected)}>Run Verification</button>
              <button className="btn" onClick={async ()=>{
                try{
                  const token = sessionStorage.getItem('sp_admin_token')
                  const headers = token ? { headers: { 'x-admin-token': token } } : {}
                  await axios.post(`${API_BASE}/api/apps/${selected.id}/process`, {status:'Processing'}, headers)
                  load()
                }catch(e){
                  alert('Processing failed (ensure you are logged in as admin)')
                }
              }}>Process</button>
            </div>
          </div>}
        </div>

        <div>
          <div className="card">
            <h4>Blockchain Log</h4>
            <div className="chain-list">
              {chain.length===0 && <div className="small">No records yet</div>}
              {chain.map(b=> (
                <div key={b.index} style={{padding:'8px 0',borderBottom:'1px solid rgba(255,255,255,0.03)'}}>
                  <div style={{fontSize:13}}><strong>#{b.index}</strong> <span className="small">{b.timestamp}</span></div>
                  <div className="small">hash: {b.hash.substring(0,28)}...</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{marginTop:16}}>
            <h4>About</h4>
            <p className="small">This dashboard demonstrates multimodal verification (face/document/liveness), process prediction and a lightweight blockchain hashing simulation to log evidence. Mock data is used for research prototyping.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Apply modal component
function ApplyModal({visible,data,onClose,onSubmit}){
  const [form,setForm] = useState({...data})
  useEffect(()=>setForm({...data}),[data])
  if(!visible) return null
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={e=>e.stopPropagation()}>
        <h3>Apply Passport</h3>
        <div className="form-row">
          <input placeholder="Full name" value={form.name||''} onChange={e=>setForm({...form,name:e.target.value})} />
          <input placeholder="Country" value={form.country||''} onChange={e=>setForm({...form,country:e.target.value})} />
        </div>
        <div style={{marginTop:8}}>
          <select value={form.document_quality||''} onChange={e=>setForm({...form,document_quality:e.target.value})}>
            <option value="Good">Good</option>
            <option value="Poor">Poor</option>
          </select>
        </div>
        <div className="actions">
          <button className="btn" onClick={()=>onSubmit(form)}>Submit</button>
          <button className="btn" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

export default function App(){
  const [view,setView] = useState('landing')

  return (
    <div>
      {view === 'landing' && (
        <Landing onApply={()=>setView('submit')} onAdmin={()=>setView('admin-login')} />
      )}
      {view === 'submit' && (
        <SubmitPage onBack={()=>setView('landing')} />
      )}
      {view === 'admin-login' && (
        <AdminLogin onSuccess={()=>setView('dashboard')} onBack={()=>setView('landing')} />
      )}
      {view === 'dashboard' && (
        <Dashboard onBack={()=>setView('landing')} />
      )}
    </div>
  )
}

// Customer-facing submit page (full page form)
function SubmitPage({onBack}){
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000'
  const [form,setForm] = useState({name:'',country:'',document_quality:'Good'})
  const submit = async ()=>{
    try{
      const r = await axios.post(`${API_BASE}/api/apps`, form)
      alert('Submitted application #' + r.data.id)
      onBack()
    }catch(e){
      alert('Submit failed')
    }
  }
  return (
    <div className="container">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
        <div style={{display:'flex',gap:12,alignItems:'center'}}>
          <div className="logo">AI</div>
          <div>
            <h2 style={{margin:0}}>Submit Application</h2>
            <div className="small">Fill and submit your passport application</div>
          </div>
        </div>
        <div style={{display:'flex',gap:8}}>
          <button className="pill" onClick={onBack}>Home</button>
        </div>
      </div>
      <div className="card">
        <div className="form-row">
          <input placeholder="Full name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} />
          <input placeholder="Country" value={form.country} onChange={e=>setForm({...form,country:e.target.value})} />
        </div>
        <div style={{marginTop:8}}>
          <select value={form.document_quality||''} onChange={e=>setForm({...form,document_quality:e.target.value})}>
            <option value="Good">Good</option>
            <option value="Poor">Poor</option>
          </select>
        </div>
        <div className="actions" style={{marginTop:12}}>
          <button className="btn" onClick={submit}>Submit Application</button>
        </div>
      </div>
    </div>
  )
}

// Simple admin login page — stores token in sessionStorage on success
function AdminLogin({onSuccess,onBack}){
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000'
  const [user,setUser] = useState('admin')
  const [pass,setPass] = useState('')
  const login = async ()=>{
    try{
      const r = await axios.post(`${API_BASE}/api/admin/login`, {username:user,password:pass})
      if(r.data?.token){
        sessionStorage.setItem('sp_admin_token', r.data.token)
        alert('Admin login successful')
        onSuccess()
      }else{
        alert('Login failed')
      }
    }catch(e){ alert('Login failed') }
  }
  return (
    <div className="container">
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:12}}>
        <div style={{display:'flex',gap:12,alignItems:'center'}}>
          <div className="logo">AI</div>
          <div>
            <h2 style={{margin:0}}>Admin Login</h2>
          </div>
        </div>
        <div style={{display:'flex',gap:8}}>
          <button className="pill" onClick={onBack}>Home</button>
        </div>
      </div>
      <div className="card" style={{maxWidth:480}}>
        <div className="form-row">
          <input placeholder="Username" value={user} onChange={e=>setUser(e.target.value)} />
          <input placeholder="Password" type="password" value={pass} onChange={e=>setPass(e.target.value)} />
        </div>
        <div className="actions" style={{marginTop:12}}>
          <button className="btn" onClick={login}>Login</button>
        </div>
      </div>
    </div>
  )
}

function Landing({onApply,onAdmin}){
  // hero image — use a neutral stock image. You can replace with a local asset later.
  const heroUrl = 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1800&q=60'
  return (
    <div className="container">
      <div className="topbar">
        <div className="logo-small">
          <div className="icon">SP</div>
          <div style={{color:'#fff'}}>Online Passport Application System</div>
        </div>
        <div className="lang-bar">
          <button className="lang-btn">English</button>
          <button className="lang-btn">සිංහල</button>
          <button className="lang-btn">தமிழ்</button>
          <button className="lang-btn" onClick={onAdmin} style={{marginLeft:12}}>Admin</button>
        </div>
      </div>

      <div className="hero" style={{backgroundImage:`url(${heroUrl})`}}>
        <div className="hero-overlay">
          <h1>We facilitate Sri Lankan citizens to apply passports through online comfortably at their fingertips.</h1>
          <p className="lead">Secure, fast and AI-assisted verification for smooth processing.</p>

          <LandingCards onApply={onApply} />
        </div>
      </div>
    </div>
  )
}

function LandingCards({onApply}){
  const [showInstructions,setShowInstructions] = useState(false)
  const [instructionsFor,setInstructionsFor] = useState('')
  const [applyPrefill,setApplyPrefill] = useState(null)

  const openInstructions = (forWho)=>{ setInstructionsFor(forWho); setShowInstructions(true) }
  const closeInstructions = ()=>setShowInstructions(false)

  const startApply = (forWho)=>{
    const prefill = forWho === 'overseas' ? {country:'Other', document_quality:'Good'} : {country:'Sri Lanka', document_quality:'Good'}
    // pass prefill to dashboard by storing in sessionStorage (simple for prototype)
    sessionStorage.setItem('sp_apply_prefill', JSON.stringify(prefill))
    onApply()
  }

  return (
    <>
    <div className="landing-cards">
      <div className="landing-card">
        <h3>Applicants residing Overseas</h3>
        <p>Apply from overseas.</p>
        <div className="actions">
          <button className="btn" onClick={()=>openInstructions('overseas')}>Instructions</button>
          <button className="btn" onClick={()=>startApply('overseas')}>Apply Passport</button>
        </div>
      </div>

      <div className="landing-card">
        <h3>Applicants residing in Sri Lanka</h3>
        <p>Apply from Sri Lanka.</p>
        <div className="actions">
          <button className="btn" onClick={()=>openInstructions('local')}>Instructions</button>
          <button className="btn" onClick={()=>startApply('local')}>Apply Passport</button>
        </div>
      </div>
    </div>

    {showInstructions && (
      <div className="modal-backdrop" onClick={closeInstructions}>
        <div className="modal" onClick={e=>e.stopPropagation()}>
          <h3>Application Instructions ({instructionsFor})</h3>
          <p>Please ensure you have a valid ID, a recent photo, and scanned copies of supporting documents. For overseas applicants, attach proof of residency.</p>
          <div className="actions"><button className="btn" onClick={closeInstructions}>Close</button></div>
        </div>
      </div>
    )}
    </>
  )
}
