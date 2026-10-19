import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Bot, CheckCircle2, ClipboardList, Plus, Search, X } from 'lucide-react'
import { approveTriage, createRequest, getRequest, getRequests, getStats, updateRequest } from './api'
import type { Category, Priority, RequestDetail, RequestItem, Stats, Status } from './types'

const categories:Category[]=['Safety','IT','Facilities','People','Supply Chain','Quality','Other']
const priorities:Priority[]=['Low','Medium','High','Critical']
const statuses:Status[]=['New','Under Review','Approved','In Progress','Completed']

function App(){
  const [items,setItems]=useState<RequestItem[]>([]), [stats,setStats]=useState<Stats|null>(null)
  const [selected,setSelected]=useState<RequestDetail|null>(null), [showForm,setShowForm]=useState(false)
  const [query,setQuery]=useState(''), [status,setStatus]=useState('All'), [busy,setBusy]=useState(false), [error,setError]=useState('')
  const refresh=async()=>{try{setError('');const [a,b]=await Promise.all([getRequests(),getStats()]);setItems(a);setStats(b)}catch(e){setError(e instanceof Error?e.message:'Unable to load data')}}
  useEffect(()=>{refresh()},[])
  const open=async(id:number)=>{try{setSelected(await getRequest(id))}catch(e){setError(e instanceof Error?e.message:'Unable to load request')}}
  const filtered=useMemo(()=>items.filter(i=>(status==='All'||i.status===status)&&(`${i.title} ${i.requester} ${i.department}`.toLowerCase().includes(query.toLowerCase()))),[items,query,status])
  const changed=async()=>{await refresh();if(selected)await open(selected.id)}
  return <div className="app">
    <aside><div className="brand"><div className="brandMark">O</div><div><strong>OpsFlow</strong><span>Intelligent triage</span></div></div>
      <nav><button className="active"><ClipboardList size={18}/>Request queue</button><button><Bot size={18}/>AI review</button></nav>
      <div className="asideFoot"><span>Portfolio demonstration</span><small>Human-led AI workflow</small></div>
    </aside>
    <main>
      <header><div><p className="eyebrow">Digital Operations</p><h1>Request and triage workspace</h1><p>Turn operational needs into accountable, reviewable work.</p></div><button className="primary" onClick={()=>setShowForm(true)}><Plus size={18}/>New request</button></header>
      {error&&<div className="error">{error}<button onClick={()=>setError('')}><X size={16}/></button></div>}
      <section className="stats">
        <Stat label="Total requests" value={stats?.total??0} icon={<ClipboardList/>}/><Stat label="Open work" value={stats?.open??0} icon={<AlertTriangle/>}/><Stat label="Critical" value={stats?.critical??0} icon={<AlertTriangle/>} tone="red"/><Stat label="Awaiting approval" value={stats?.pending_approval??0} icon={<Bot/>} tone="gold"/>
      </section>
      <section className="panel"><div className="toolbar"><div className="search"><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search requests, people, departments"/></div><select value={status} onChange={e=>setStatus(e.target.value)}><option>All</option>{statuses.map(s=><option key={s}>{s}</option>)}</select></div>
        <div className="tableWrap"><table><thead><tr><th>Request</th><th>Department</th><th>AI triage</th><th>Priority</th><th>Status</th><th>Owner</th></tr></thead><tbody>
          {filtered.map(i=><tr key={i.id} onClick={()=>open(i.id)}><td><strong>{i.title}</strong><span>#{i.id} · {i.requester}</span></td><td>{i.department}</td><td><span className="aiTag"><Bot size={14}/>{i.category}</span></td><td><Badge value={i.priority}/></td><td><Badge value={i.status}/></td><td>{i.owner||<span className="muted">Unassigned</span>}</td></tr>)}
          {!filtered.length&&<tr><td colSpan={6} className="empty">No requests match this view.</td></tr>}
        </tbody></table></div>
      </section>
    </main>
    {showForm&&<NewRequest onClose={()=>setShowForm(false)} onSaved={async()=>{setShowForm(false);await refresh()}}/>}
    {selected&&<Detail item={selected} busy={busy} onClose={()=>setSelected(null)} onAction={async(action)=>{setBusy(true);try{await action();await changed()}finally{setBusy(false)}}}/>} 
  </div>
}

function Stat({label,value,icon,tone='blue'}:{label:string;value:number;icon:React.ReactNode;tone?:string}){return <div className={`stat ${tone}`}><div>{icon}</div><span>{label}</span><strong>{value}</strong></div>}
function Badge({value}:{value:string}){return <span className={`badge ${value.toLowerCase().replaceAll(' ','-')}`}>{value}</span>}

function NewRequest({onClose,onSaved}:{onClose:()=>void;onSaved:()=>void}){
  const [form,setForm]=useState({title:'',description:'',requester:'',department:''}),[saving,setSaving]=useState(false),[error,setError]=useState('')
  const submit=async(e:React.FormEvent)=>{e.preventDefault();setSaving(true);try{await createRequest(form);onSaved()}catch(x){setError(x instanceof Error?x.message:'Unable to save')}finally{setSaving(false)}}
  return <div className="overlay"><div className="modal"><div className="modalHead"><div><p className="eyebrow">New operational need</p><h2>Create a request</h2></div><button className="icon" onClick={onClose}><X/></button></div>
    <form onSubmit={submit}><label>Title<input required minLength={4} value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="What needs attention?"/></label>
      <label>Description<textarea required minLength={10} value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Describe the problem, impact, and desired outcome."/></label>
      <div className="grid2"><label>Requester<input required value={form.requester} onChange={e=>setForm({...form,requester:e.target.value})}/></label><label>Department<input required value={form.department} onChange={e=>setForm({...form,department:e.target.value})}/></label></div>
      {error&&<p className="formError">{error}</p>}<div className="actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={saving}><Bot size={17}/>{saving?'Triaging…':'Submit and triage'}</button></div>
    </form></div></div>
}

function Detail({item,onClose,onAction,busy}:{item:RequestDetail;onClose:()=>void;onAction:(a:()=>Promise<unknown>)=>void;busy:boolean}){
  const [cat,setCat]=useState<Category>(item.category),[pri,setPri]=useState<Priority>(item.priority),[owner,setOwner]=useState(item.owner||'')
  return <div className="overlay right"><div className="drawer"><div className="modalHead"><div><p className="eyebrow">Request #{item.id}</p><h2>{item.title}</h2></div><button className="icon" onClick={onClose}><X/></button></div>
    <div className="meta"><span>{item.requester}</span><span>{item.department}</span><span>{new Date(item.created_at).toLocaleString()}</span></div><p className="description">{item.description}</p>
    <section className="aiReview"><div className="aiTitle"><Bot/><div><strong>AI-assisted triage</strong><span>{item.triage_provider} · {Math.round((item.ai_confidence||0)*100)}% confidence</span></div></div><p>{item.ai_summary}</p>
      <div className="grid2"><label>Category<select value={cat} onChange={e=>setCat(e.target.value as Category)}>{categories.map(x=><option key={x}>{x}</option>)}</select></label><label>Priority<select value={pri} onChange={e=>setPri(e.target.value as Priority)}>{priorities.map(x=><option key={x}>{x}</option>)}</select></label></div>
      {!item.triage_approved?<button className="primary full" disabled={busy} onClick={()=>onAction(()=>approveTriage(item.id,cat,pri))}><CheckCircle2 size={17}/>Approve human review</button>:<div className="approved"><CheckCircle2 size={17}/>Triage approved by a person</div>}
    </section>
    <section><h3>Workflow</h3><div className="grid2"><label>Status<select value={item.status} onChange={e=>onAction(()=>updateRequest(item.id,{status:e.target.value as Status}))}>{statuses.map(x=><option key={x}>{x}</option>)}</select></label><label>Owner<div className="inline"><input value={owner} onChange={e=>setOwner(e.target.value)} placeholder="Assign owner"/><button disabled={busy||owner===item.owner} onClick={()=>onAction(()=>updateRequest(item.id,{owner}))}>Save</button></div></label></div></section>
    <section><h3>Activity</h3><div className="timeline">{item.activity.map(a=><div key={a.id}><i></i><p><strong>{a.action}</strong><span>{a.detail}</span><small>{a.actor} · {new Date(a.created_at).toLocaleString()}</small></p></div>)}</div></section>
  </div></div>
}
export default App

