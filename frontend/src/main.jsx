import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const API = 'http://127.0.0.1:8000';
const demoUsers = [
  ['member', 'member123', 'Member'], ['lead', 'lead123', 'Lead'],
  ['admin', 'admin123', 'Admin'], ['viewer', 'viewer123', 'Viewer'], ['other', 'other123', 'Finance Member']
];

function App() {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('opsUser') || 'null'));
  const [username, setUsername] = useState('member');
  const [password, setPassword] = useState('member123');
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [itemPriority, setItemPriority] = useState('medium');
  const [selected, setSelected] = useState(null);
  const [activity, setActivity] = useState([]);
  const [comment, setComment] = useState('');

  const headers = useMemo(() => user ? { Authorization: `Bearer ${user.token}`, 'Content-Type': 'application/json' } : {}, [user]);
  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...(options.headers || {}) } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : data.detail?.message || 'Request failed');
    return data;
  }
  async function login(e) {
    e.preventDefault(); setError('');
    try {
      const data = await fetch(`${API}/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }).then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail || 'Login failed'); return d; });
      setUser(data); localStorage.setItem('opsUser', JSON.stringify(data));
    } catch (err) { setError(err.message); }
  }
  async function loadItems() {
    if (!user) return;
    try {
      const params = new URLSearchParams(); if (query) params.set('q', query); if (status) params.set('status', status); if (priority) params.set('priority', priority); params.set('page_size', '50');
      const data = await request(`/items?${params}`); setItems(data.items); setError('');
    } catch (err) { setError(err.message); }
  }
  useEffect(() => { loadItems(); }, [user, query, status, priority]);
  async function createItem(e) {
    e.preventDefault();
    try {
      await request('/items', { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ title, description, item_type: 'task', priority: itemPriority, team: user.team }) });
      setTitle(''); setDescription(''); setShowForm(false); await loadItems();
    } catch (err) { setError(err.message); }
  }
  async function action(path, body) {
    try { await request(path, { method: 'POST', body: JSON.stringify(body) }); await loadItems(); if (selected) await openItem(selected.id); }
    catch (err) { setError(err.message); }
  }
  async function claim(item) { try { await request(`/items/${item.id}/claim`, { method: 'POST' }); await loadItems(); } catch (err) { setError(err.message); } }
  async function openItem(id) {
    try { const [item, events] = await Promise.all([request(`/items/${id}`), request(`/items/${id}/activity`)]); setSelected(item); setActivity(events); }
    catch (err) { setError(err.message); }
  }
  function logout() { localStorage.removeItem('opsUser'); setUser(null); setItems([]); setSelected(null); }

  if (!user) return <main className="login-wrap"><section className="login-card"><div className="brand-mark">N</div><p className="eyebrow">NEWTONITE · OPERATIONS</p><h1>Work moves forward.</h1><p className="muted">Sign in to manage operational work items across teams.</p><form onSubmit={login} className="stack"><label>Username<input value={username} onChange={e => setUsername(e.target.value)} required /></label><label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} required /></label><button className="primary">Sign in <span>→</span></button></form>{error && <p className="error">{error}</p>}<div className="demo-box"><b>Demo accounts</b>{demoUsers.map(u => <button className="demo-user" key={u[0]} onClick={() => { setUsername(u[0]); setPassword(u[1]); }}>{u[0]} <span>{u[2]}</span></button>)}</div></section></main>;

  const urgent = items.filter(i => i.priority === 'urgent' && !i.assignee).length;
  const mine = items.filter(i => i.assignee === user.username).length;
  const approvals = items.filter(i => i.status === 'Awaiting Approval').length;
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark">N</div><div><b>Newtonite</b><small>OPERATIONS</small></div></div><div className="side-label">WORKSPACE</div><button className="nav active">▦ <span>Overview</span></button><button className="nav" onClick={() => { setStatus('Open'); }}>◷ <span>Open work</span></button><button className="nav" onClick={() => { setStatus('Awaiting Approval'); }}>✓ <span>Approvals</span></button><div className="sidebar-bottom"><div className="avatar">{user.username[0].toUpperCase()}</div><div className="user-info"><b>{user.username}</b><small>{user.role} · {user.team}</small></div><button className="logout" onClick={logout} title="Log out">↗</button></div></aside>
    <main className="main"><header className="topbar"><div><span className="breadcrumb">Workspace /</span> <b>Operations overview</b></div><div className="top-right"><span className="online-dot"/> System operational <div className="avatar small">{user.username[0].toUpperCase()}</div></div></header>
      <section className="page-heading"><div><p className="eyebrow">MONDAY · TEAM WORKSPACE</p><h1>Good to have you back, {user.username}.</h1><p className="muted">Here’s what’s happening across your team today.</p></div><button className="primary create-btn" onClick={() => setShowForm(!showForm)}>＋ Create work item</button></section>
      {error && <div className="notice">{error}<button onClick={() => setError('')}>×</button></div>}
      <section className="metrics"><div className="metric"><div className="metric-top">Total work items <span>↗</span></div><strong>{items.length}</strong><small>In your current view</small></div><div className="metric"><div className="metric-top">Assigned to me <span>◎</span></div><strong>{mine}</strong><small>Your active ownership</small></div><div className="metric"><div className="metric-top">Urgent unassigned <span className="orange">!</span></div><strong>{urgent}</strong><small>Needs an owner</small></div><div className="metric"><div className="metric-top">Awaiting approval <span>◷</span></div><strong>{approvals}</strong><small>Waiting for a team lead</small></div></section>
      {showForm && <form className="create-panel" onSubmit={createItem}><div className="panel-title"><h2>Create work item</h2><button type="button" className="icon-btn" onClick={() => setShowForm(false)}>×</button></div><label>Title<input value={title} onChange={e => setTitle(e.target.value)} required minLength="2" placeholder="e.g. Investigate failed payment alerts" /></label><label>Description<textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Add context for the team" /></label><label>Priority<select value={itemPriority} onChange={e => setItemPriority(e.target.value)}><option>low</option><option>medium</option><option>high</option><option>urgent</option></select></label><button className="primary">Create item</button></form>}
      <section className="work-panel"><div className="work-header"><div><h2>Work items</h2><p className="muted">Track and manage your team's operational queue.</p></div><span className="count-pill">{items.length} items</span></div><div className="filters"><div className="search">⌕ <input placeholder="Search work items..." value={query} onChange={e => setQuery(e.target.value)} /></div><select value={status} onChange={e => setStatus(e.target.value)}><option value="">All statuses</option>{['Open','In Progress','Awaiting Approval','Resolved','Closed'].map(s => <option key={s}>{s}</option>)}</select><select value={priority} onChange={e => setPriority(e.target.value)}><option value="">All priorities</option>{['urgent','high','medium','low'].map(s => <option key={s}>{s}</option>)}</select><button className="reset-btn" onClick={() => { setQuery(''); setStatus(''); setPriority(''); }}>Reset</button></div>
      <div className="table-wrap"><table><thead><tr><th>WORK ITEM</th><th>PRIORITY</th><th>STATUS</th><th>ASSIGNEE</th><th>TEAM</th><th>ACTIONS</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td><button className="item-title" onClick={() => openItem(item.id)}><span className="item-icon">{item.item_type === 'incident' ? '⚠' : '▤'}</span><span><b>{item.title}</b><small>OPS-{String(item.id).padStart(4,'0')} · {item.item_type}</small></span></button></td><td><span className={`priority ${item.priority}`}>● {item.priority}</span></td><td><span className={`status ${item.status.toLowerCase().replaceAll(' ','-')}`}>{item.status}</span></td><td>{item.assignee || <span className="muted">Unassigned</span>}</td><td>{item.team}</td><td><div className="actions"><button onClick={() => openItem(item.id)} title="Details">↗</button>{!item.assignee && user.role !== 'Viewer' && <button onClick={() => claim(item)} title="Claim item">＋</button>}</div></td></tr>)}</tbody></table>{items.length === 0 && <div className="empty"><div>◫</div><b>No work items found</b><p>Try changing the filters or create a new item.</p></div>}</div><div className="table-footer">Showing {items.length} items <span>Server-side filtering · page 1</span></div></section>
      {selected && <div className="modal-backdrop" onClick={() => setSelected(null)}><section className="detail-modal" onClick={e => e.stopPropagation()}><div className="panel-title"><div><p className="eyebrow">OPS-{String(selected.id).padStart(4,'0')}</p><h2>{selected.title}</h2></div><button className="icon-btn" onClick={() => setSelected(null)}>×</button></div><p className="muted">{selected.description || 'No description provided.'}</p><div className="detail-grid"><div><small>STATUS</small><b>{selected.status}</b></div><div><small>PRIORITY</small><b>{selected.priority}</b></div><div><small>ASSIGNEE</small><b>{selected.assignee || 'Unassigned'}</b></div><div><small>VERSION</small><b>{selected.version}</b></div></div><div className="transition-actions"><b>Update status</b><div className="button-row">{(selected.status === 'Open' ? ['In Progress'] : selected.status === 'In Progress' ? ['Awaiting Approval','Open'] : selected.status === 'Awaiting Approval' ? ['Resolved','In Progress'] : selected.status === 'Resolved' ? ['Closed','In Progress'] : []).map(s => <button key={s} className="secondary" onClick={() => action(`/items/${selected.id}/transition`, { status: s })}>{s}</button>)}</div></div><div className="activity"><h3>Activity history</h3>{activity.map(ev => <div className="event" key={ev.id}><span className="event-dot"/><div><b>{ev.actor}</b> <span>{ev.event.replaceAll('_',' ')}</span><small>{JSON.stringify(ev.details)} · {new Date(ev.created_at).toLocaleString()}</small></div></div>)}</div><form className="comment-form" onSubmit={e => { e.preventDefault(); action(`/items/${selected.id}/comments`, { comment }); setComment(''); }}><input placeholder="Add a comment..." value={comment} onChange={e => setComment(e.target.value)} required/><button className="primary">Comment</button></form></section></div>}
    </main></div>;
}

createRoot(document.getElementById('root')).render(<App />);
