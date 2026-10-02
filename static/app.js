import { mountOs } from "./os-shell.js";

const root = document.querySelector("#app");
const state = { cases: [], session: null, selected: null, replay: false, activeApp: null, visualActions: [], sessionKey: null };

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const api = async (url, options={}) => {
  const response = await fetch(url, {headers:{"Content-Type":"application/json",...(options.headers||{})}, ...options});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
  return body;
};
const titleCase = s => String(s).split(/[-_]/).map(x=>x.charAt(0).toUpperCase()+x.slice(1)).join(" ");
function toast(message){ const el=document.createElement("div");el.className="toast";el.textContent=message;document.body.append(el);setTimeout(()=>el.remove(),2600); }
function notifyParent(type, extra={}){
  if(window.parent===window)return;
  const configured=new URLSearchParams(location.search).get("parent_origin");
  const target=configured||location.origin;
  window.parent.postMessage({source:"vibe-os-icl",version:"1.0",type,episodeId:state.session?.id,...extra},target);
}

function header(extra="") { return `<header class="studio-header"><div class="brand"><div class="brand-mark">VO</div>Vibe OS-ICL</div><div class="header-sub">Deterministic demonstration and evaluation studio</div><div class="header-spacer"></div>${extra}<div class="status-pill">36 executable cases</div></header>`; }

async function loadCases(){
  const data=await api("/api/v1/cases"); state.cases=data.cases;
  const params=new URLSearchParams(location.search); const sid=params.get("session");
  state.replay=params.get("replay")==="1";
  if(sid){ document.title="Vibe OS Task"; state.session=await api(`/api/v1/sessions/${sid}`); renderSession(); notifyParent("VIBE_READY",{status:state.session.status}); }
  else if(location.pathname==="/studio"||params.get("studio")==="1"){document.title="Vibe OS-ICL Studio";renderDashboard()}
  else {document.title="Vibe OS";mountOs(root)}
}

function renderDashboard(){
  document.body.classList.remove("os-home-mode");
  const families=[...new Set(state.cases.map(c=>c.family))];
  root.innerHTML=header()+`<main class="dashboard"><section class="hero"><div><h1>OS in-context learning workspace</h1><p>Record demonstrations, inspect deterministic episodes, and run visual agents against the same English-only simulated operating system.</p></div><div class="filters"><label class="field">Demo rule<select id="demo-rule"><option value="0">Rule 0</option><option value="1">Rule 1</option><option value="2">Rule 2</option></select></label><label class="field">Family<select id="family"><option value="">All families</option>${families.map(f=>`<option value="${f}">${titleCase(f)}</option>`).join("")}</select></label><label class="field">Search<input id="search" placeholder="Case name or ID" /></label></div></section><section id="case-grid" class="case-grid"></section></main>`;
  document.querySelector("#family").onchange=paintCases; document.querySelector("#search").oninput=paintCases; paintCases();
}
function paintCases(){
  const family=document.querySelector("#family").value; const q=document.querySelector("#search").value.toLowerCase();
  const list=state.cases.filter(c=>(!family||c.family===family)&&(!q||`${c.id} ${c.title}`.toLowerCase().includes(q)));
  document.querySelector("#case-grid").innerHTML=list.map(c=>`<article class="case-card"><div class="case-top"><span class="case-id">${c.id}</span><span class="level">${c.difficulty}</span></div><h3>${esc(c.title)}</h3><p>${esc(c.task)}</p><div class="case-meta"><span class="tag">${esc(c.app)}</span><span class="tag">${titleCase(c.family)}</span></div><div class="card-actions"><button class="btn primary" data-start="evaluation" data-id="${c.id}">Run evaluation</button><button class="btn" data-start="demo" data-id="${c.id}">Record demo</button></div></article>`).join("");
  document.querySelectorAll("[data-start]").forEach(b=>b.onclick=()=>createSession(b.dataset.id,b.dataset.start));
}
async function createSession(caseId,mode){
  try{
    const body={case_id:caseId,mode};
    if(mode==="demo") body.rule=Number(document.querySelector("#demo-rule")?.value||0);
    state.session=await api("/api/v1/sessions",{method:"POST",body:JSON.stringify(body)});
    history.pushState({},"",state.session.launch_url); state.selected=null; renderSession();
  }catch(e){toast(e.message)}
}

function appGlyph(app){ return ({Files:"F",Monitor:"M",Devices:"D",Notifications:"N",Settings:"S",Terminal:"T",Desktop:"W",Transfers:"X",Jobs:"J"})[app.split(" ")[0]]||"V"; }
function renderSession(){
  const s=state.session,c=s.case;
  if(state.sessionKey!==s.id){
    state.sessionKey=s.id; state.selected=null; state.visualActions=[];
    state.activeApp=s.workflow?"Overview":c.app.split("+")[0].trim();
  }
  const apps=["Files","Monitor","Terminal","Settings","Devices","Notifications","Jobs","Transfers"];
  const simulator=`<section class="simulator-frame"><div class="vibe-os" id="capture-area"><div class="os-topbar"><div class="os-topbar-left"><div class="os-logo">V</div><strong>Vibe OS</strong><span>Workspace</span></div><div class="os-topbar-right"><span>English (US)</span><span>● Online</span><strong>10:24</strong></div></div><div class="os-workspace"><div class="window"><div class="window-titlebar"><div class="traffic"><i class="dot"></i><i class="dot"></i><i class="dot"></i></div><span class="window-title">${esc(state.activeApp||c.app)}</span><span class="window-sub">Simulation · ${esc(c.id)}</span></div><div class="app-shell"><aside class="app-sidebar"><div class="side-title">Applications</div>${s.workflow?`<button class="side-item ${state.activeApp==="Overview"?"active":""}" data-app="Overview">V &nbsp;Overview</button>`:""}${apps.map(x=>`<button class="side-item ${state.activeApp===x?"active":""}" data-app="${esc(x)}">${appGlyph(x)} &nbsp;${x}</button>`).join("")}</aside><section class="app-main" id="dynamic-app-main">${renderAppMain(s)}</section></div></div></div><div class="os-dock">${["F","M","T","S","D","N"].map(x=>`<div class="dock-icon">${x}</div>`).join("")}</div></div></section>`;
  if(state.replay){
    document.body.classList.remove("recording-mode"); document.body.classList.add("replay-mode");
    root.innerHTML=`<main class="replay-only">${simulator}<div class="replay-cursor" id="replay-cursor"></div><div class="replay-label" id="replay-label">Demonstration</div></main>`;
    window.__REPLAY_DONE__=false; setTimeout(runReplay,700); return;
  }
  if(s.mode==="demo"&&s.recording){
    document.body.classList.remove("replay-mode"); document.body.classList.add("recording-mode");
    root.innerHTML=`<main class="recording-only">${simulator}<div class="recording-toolbar"><span>Recording demonstration · 16:9</span><button class="btn success" id="finish-demo">Finish and build video</button></div></main>`;
    bindSession(); return;
  }
  document.body.classList.remove("replay-mode","recording-mode");
  root.innerHTML=header(`<button class="btn" id="back">All cases</button>`)+`<main class="session-layout">${simulator}<aside class="control-panel">${renderControls(s)}</aside></main>`;
  bindSession();
}
function renderAppMain(s){
  const active=state.activeApp||s.case.app.split("+")[0].trim();
  const toolbar=`<div class="app-toolbar"><span class="crumb">Vibe OS / <strong>${esc(active)}</strong></span><span style="margin-left:auto" class="tag">Seed ${s.seed}</span></div>`;
  const task=`<div class="task-banner"><span class="task-badge">TASK</span><strong>${esc(s.case.task)}</strong></div>`;
  if(s.workflow){
    const sources=s.workflow.source_apps||[], target=s.workflow.target_app;
    if(active==="Overview") return `${toolbar}${task}<div class="workflow-overview"><div class="workflow-icon">↗</div><h3>Cross-application workflow</h3><p>Inspect the source application${sources.length>1?"s":""}, remember the referenced record, then finish the operation in <strong>${esc(target)}</strong>.</p><div class="workflow-route">${[...sources,target].map((x,i)=>`<span>${i+1}. ${esc(x)}</span>`).join("<b>→</b>")}</div></div>`;
    if(sources.includes(active)) return `${toolbar}${task}<div class="source-workspace"><div class="source-window-title">${esc(active)} · Reference records</div><p>Inspect the record required by the learned policy. The temporary K/M/R labels are defined only in this source window.</p><div class="source-cards">${s.workflow.records.map(record=>`<button class="source-card ${visualActions(s).some(a=>a.verb==="inspect"&&a.target===`source:${record.key}`)?"inspected":""}" data-source="source:${esc(record.key)}"><strong>${esc(record.key)}</strong><span>${esc(record.name)}</span><small>${esc(record.detail)}</small></button>`).join("")}</div></div>`;
    if(active!==target) return `${toolbar}${task}<div class="empty-app"><h3>${esc(active)}</h3><p>This application is not part of the current workflow.</p></div>`;
  }
  return `${toolbar}${task}<div class="items">${renderItems(s)}</div>${renderActionBar(s)}`;
}
function paintDynamicWorkspace(){
  const main=document.querySelector("#dynamic-app-main"); if(main)main.innerHTML=renderAppMain(state.session);
  document.querySelectorAll("[data-app]").forEach(el=>el.classList.toggle("active",el.dataset.app===state.activeApp));
}
function itemColumns(s){
  const id=s.case.id,yes=value=>value?"Yes":"No";
  const common={
    index:{label:"Index",value:x=>x.index}, layer:{label:"Layer",value:x=>x.layer},
    type:{label:"Type",value:x=>x.display_type||x.symbol}, value:{label:"Value",value:x=>x.value}, size:{label:"Size",value:x=>`${x.size} MB`},
    color:{label:"Color",value:x=>x.color}, symbol:{label:"Symbol",value:x=>x.symbol},
    age:{label:"Age",value:x=>x.age}, cpu:{label:"CPU",value:x=>`${x.cpu}%`},
    memory:{label:"Memory",value:x=>`${x.memory} MB`}, runtime:{label:"Runtime",value:x=>`${x.runtime} min`},
    status:{label:"Status",value:x=>x.scenario||x.status}, code:{label:"Code",value:x=>x.code},
    signal:{label:"Signal",value:x=>`${x.signal}%`}, battery:{label:"Battery",value:x=>`${x.battery}%`},
    paired:{label:"Paired",value:x=>yes(x.paired)}, starred:{label:"Starred",value:x=>yes(x.starred)},
    today:{label:"Today",value:x=>yes(x.today)}, unread:{label:"Unread",value:x=>yes(x.unread)},
    network:{label:"Network",value:x=>x.network}, charging:{label:"Charging",value:x=>yes(x.charging)},
  };
  const keys=id==="OS-SEL-01"?["type","size","age","color","status"]:
    id==="OS-SEL-02"?["color","value","starred","today","symbol"]:
    ["OS-SEL-03","OS-SEL-04"].includes(id)?["status","cpu","memory","runtime","age"]:
    id==="OS-SEL-05"?["paired","signal","battery","age","status"]:
    id==="OS-SEL-06"?["symbol","value","unread","color","today"]:
    id==="OS-MAP-01"?["color","value","type","status","age"]:
    id==="OS-MAP-02"?["symbol","unread","value","status","age"]:
    id==="OS-MAP-03"?["type","value","color","age","status"]:
    id==="OS-MAP-04"?["status","cpu","memory","runtime","age"]:
    id==="OS-MAP-05"?["symbol","value","color","status","age"]:
    id==="OS-MAP-06"?["code","value","status","runtime","age"]:
    id==="OS-ORD-01"?["index","value","age","type","status"]:
    id==="OS-ORD-02"?["index","symbol","value","unread","status"]:
    id==="OS-ORD-03"?["index","layer","age","status","type"]:
    id==="OS-ORD-04"?["index","value","starred","type","age"]:
    id==="OS-ORD-05"?["index","symbol","age","status","value"]:
    id==="OS-ORD-06"?["index","value","runtime","status","age"]:
    id==="OS-SM-04"?["battery","network","charging","signal","age"]:
    s.case.family==="state_machine"?["status","value","cpu","runtime","age"]:
    s.case.family==="recovery"?["status","type","value","age","color"]:
    id==="OS-XAPP-02"?["index","symbol","unread","age","status"]:
    id==="OS-XAPP-03"?["index","cpu","memory","runtime","status"]:
    id==="OS-XAPP-05"?["index","type","starred","value","status"]:
    id==="OS-XAPP-06"?["index","cpu","status","runtime","value"]:
    ["index","type","value","status","age"];
  return keys.map(key=>common[key]);
}
function visualActions(s){ return state.replay?state.visualActions:s.actions; }
function deriveItems(s){
  const items=s.items.map(item=>({...item,outcome:""}));
  const byId=Object.fromEntries(items.map(item=>[item.id,item]));
  const toggled=new Set();
  for(const action of visualActions(s)){
    const item=byId[action.target]; if(!item)continue;
    if(action.verb==="toggle"){toggled.has(item.id)?toggled.delete(item.id):toggled.add(item.id);item.outcome=toggled.has(item.id)?"Selected":"Unselected";continue}
    const effects={star:"Starred",copy:"Copied",move:"Moved",clear:"Cleared",pin:"Pinned",mute:"Muted",pause:"Paused",resume:"Running",stop:"Stopped",connect:"Connected",disconnect:"Disconnected",delete:"Deleted",enable:"Enabled",disable:"Disabled",maximise:"Maximised",minimise:"Minimised",confirm:"Confirmed",retry:"Retried",continue:"Continued",save:"Saved",skip:"Skipped",mark:"Marked",run:"Completed",visit:"Visited",archive:"Archived",ack:"Acknowledged",process:"Processed",lower:"Lower priority",fallback:"Fallback selected"};
    item.outcome=effects[action.verb]||titleCase(action.verb);
    if(action.verb==="star")item.starred=true;
    if(["pause","resume","stop","connect","disconnect"].includes(action.verb))item.status=item.outcome;
    if(["overwrite","confirm","continue","retry","process-copy","connect","run-fallback","move","keep-original","rerun"].includes(action.verb))item.scenario="Resolved";
  }
  return {items,toggled};
}
function renderItems(s){
  const actions=visualActions(s),acted=new Set(actions.filter(a=>!["open-app","inspect"].includes(a.verb)).map(a=>a.target));
  const derived=deriveItems(s);
  const columns=itemColumns(s);
  return `<div class="item-head"><span></span><span>Name</span>${columns.map(column=>`<span>${esc(column.label)}</span>`).join("")}</div>${derived.items.map(item=>`<div class="item-row ${state.selected===item.id||derived.toggled.has(item.id)?"selected":""} ${acted.has(item.id)?"done":""}" data-item="${item.id}"><div class="item-icon" style="background:${item.color==="Blue"?"#536ee5":item.color==="Amber"?"#d9962e":"#8b63d5"}">${esc((item.display_type||item.symbol)[0])}</div><div><div class="item-name">${esc(item.name)}</div><div class="item-sub">${item.outcome?`<span class="outcome">${esc(item.outcome)}</span>`:`${item.extension} · PID ${item.pid}`}</div></div>${columns.map(column=>`<span class="metric">${esc(column.value(item))}</span>`).join("")}</div>`).join("")}`;
}
function renderActionBar(s){
  const f=s.case.family;
  if(f==="selection") return `<div class="action-bar"><span class="hint">Click a row to select the target.</span></div>`;
  if(f==="selection_set") return `<div class="action-bar"><span class="hint">Click rows to toggle them.</span><button class="btn primary" data-action="submit">Submit selection</button></div>`;
  const canAct=state.selected||state.replay;
  const visibleActions=s.available_actions.filter(a=>!["open-app","inspect"].includes(a));
  return `<div class="action-bar"><span class="hint">Select an item, then choose an action.</span>${visibleActions.map(a=>`<button class="btn ${canAct?"":"disabled"}" data-action="${esc(a)}" ${canAct?"":"disabled"}>${titleCase(a)}</button>`).join("")}</div>`;
}
function renderControls(s){
  const isDemo=s.mode==="demo";
  const videoState=s.video_status==="ready"?`<div class="result pass">Video ready · deterministic replay rendered</div>`:s.video_status==="error"?`<div class="result fail">Video rendering failed · ${esc(s.video_error||"")}</div>`:s.video_status?`<div class="result pending">Video ${esc(s.video_status)}…</div>`:"";
  return `<section class="panel"><h2>${esc(s.case.title)}</h2><p>${esc(s.case.id)} · ${titleCase(s.case.family)} · ${s.case.difficulty}</p><div class="session-id">${s.id}</div></section>${isDemo&&!s.recording&&!s.result?`<section class="panel rule-card"><div class="rule-label">Recorder brief · hidden from generated video</div><div class="rule-text">${esc(s.recorder_brief)}</div></section>`:""}${!isDemo?renderDemos(s):""}<section class="panel"><h3>${isDemo?"Demonstration capture":"Episode controls"}</h3><p>${isDemo?"Start the demonstration, perform the task, then let the server render a clean replay video. No screen-sharing permission is required.":"The hidden rule is determined by the demonstration context. Finish when the task is complete."}</p><div class="control-stack">${isDemo&&!s.recording&&!s.result?`<button class="btn primary" id="start-record">Start demonstration</button>`:""}${isDemo&&s.recording?`<button class="btn success" id="finish-demo">Finish and build video</button>`:""}${!isDemo?`<button class="btn success" id="finish">Finish and evaluate</button>`:""}<button class="btn" id="reset">Reset episode</button></div>${s.result?`<div class="result ${s.result.success?"pass":"fail"}">${s.result.success?"Passed":"Not passed"} · trajectory ${(s.result.trajectory_compliance*100).toFixed(0)}% · ${s.result.agent_steps}/${s.result.optimal_steps} steps</div>`:""}${videoState}${s.video_url?`<video controls preload="metadata" src="${s.video_url}" class="result-video"></video>`:""}</section><section class="panel"><h3>Semantic event log</h3><p>Authoritative actions used for deterministic evaluation.</p><div class="progress-list">${s.actions.length?s.actions.map((a,i)=>`<div class="event"><code>${i+1}. ${esc(a.verb)}</code><span>${esc(a.target)}</span></div>`).join(""):`<div class="empty">No actions yet.</div>`}</div></section>`;
}
function renderDemos(s){
  const demos=(s.demonstrations||[]).filter(x=>x.video_url);
  return `<section class="panel"><h3>Video demonstrations</h3><p>Infer the temporary policy before operating the query.</p><div class="demo-list">${demos.length?demos.map((d,i)=>`<video controls preload="metadata" src="${d.video_url}" aria-label="Demonstration ${i+1}"></video>`).join(""):`<div class="empty">No recorded videos for this hidden context yet. The episode remains usable for interface and evaluator testing.</div>`}</div></section>`;
}
function bindSession(){
  const back=document.querySelector("#back");if(back)back.onclick=()=>{history.pushState({},"","/");state.session=null;state.selected=null;renderDashboard()};
  document.querySelectorAll("[data-item]").forEach(row=>row.onclick=async()=>{
    const id=row.dataset.item,f=state.session.case.family;
    if(f==="selection") return sendAction("select",id);
    if(f==="selection_set") return sendAction("toggle",id);
    state.selected=id; renderSession();
  });
  document.querySelectorAll("[data-action]").forEach(btn=>btn.onclick=()=>sendAction(btn.dataset.action,btn.dataset.action==="submit"?"workspace":state.selected));
  document.querySelectorAll("[data-app]").forEach(btn=>btn.onclick=()=>{
    if(!state.session.workflow)return;
    if(btn.dataset.app==="Overview"){state.activeApp="Overview";renderSession();return}
    state.activeApp=btn.dataset.app;sendAction("open-app",btn.dataset.app);
  });
  document.querySelectorAll("[data-source]").forEach(card=>card.onclick=()=>sendAction("inspect",card.dataset.source));
  document.querySelector("#finish")?.addEventListener("click",()=>command("finish")); document.querySelector("#reset")?.addEventListener("click",()=>command("reset"));
  document.querySelector("#start-record")?.addEventListener("click",startRecording);
  document.querySelector("#finish-demo")?.addEventListener("click",finishDemo);
}
async function sendAction(verb,target){ if(!target)return; try{state.session=await api(`/api/v1/sessions/${state.session.id}/action`,{method:"POST",body:JSON.stringify({verb,target})});state.selected=null;renderSession()}catch(e){toast(e.message)} }
async function command(name){ try{state.session=await api(`/api/v1/sessions/${state.session.id}/${name}`,{method:"POST",body:"{}"});state.selected=null;renderSession();if(name==="finish")notifyParent("EPISODE_FINISHED",{result:state.session.result});if(name==="reset")notifyParent("EPISODE_RESET");}catch(e){toast(e.message)} }
async function startRecording(){
  try{state.session=await api(`/api/v1/sessions/${state.session.id}/recording`,{method:"POST",body:JSON.stringify({active:true})});renderSession();notifyParent("RECORDING_STARTED")}catch(e){toast(e.message)}
}
async function finishDemo(){
  await command("finish");
  if(state.session?.result?.success)pollVideo();
}
async function pollVideo(){
  for(let i=0;i<120;i++){
    if(!state.session||state.session.video_status==="ready"||state.session.video_status==="error")break;
    await new Promise(resolve=>setTimeout(resolve,1000));
    state.session=await api(`/api/v1/sessions/${state.session.id}`);renderSession();
  }
  if(state.session?.video_status==="ready")notifyParent("RECORDING_STOPPED",{videoUrl:state.session.video_url});
  if(state.session?.video_status==="error")toast(`Video rendering failed: ${state.session.video_error||"unknown error"}`);
}
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function moveReplayCursor(element,label){
  if(!element)return;
  element.scrollIntoView({block:"center"});await wait(150);
  const rect=element.getBoundingClientRect(),cursor=document.querySelector("#replay-cursor"),caption=document.querySelector("#replay-label");
  cursor.style.transform=`translate(${rect.left+rect.width/2}px,${rect.top+rect.height/2}px)`;
  if(caption)caption.textContent=label;await wait(650);element.classList.add("replay-click");await wait(260);element.classList.remove("replay-click");
}
async function runReplay(){
  try{
    await wait(700);
    for(const action of state.session.actions){
      document.querySelectorAll(".item-row.selected").forEach(row=>row.classList.remove("selected"));
      if(action.verb==="open-app"){
        const appButton=document.querySelector(`[data-app="${CSS.escape(action.target)}"]`);
        await moveReplayCursor(appButton,`Open ${action.target}`);
        state.activeApp=action.target;state.visualActions.push(action);paintDynamicWorkspace();await wait(300);continue;
      }
      if(action.verb==="inspect"){
        const source=document.querySelector(`[data-source="${CSS.escape(action.target)}"]`);
        await moveReplayCursor(source,`Inspect ${action.target.split(":").pop()}`);
        source?.classList.add("inspected");state.visualActions.push(action);await wait(350);continue;
      }
      if(action.target!=="workspace"){
        const row=document.querySelector(`[data-item="${CSS.escape(action.target)}"]`);
        await moveReplayCursor(row,`Select ${row?.querySelector(".item-name")?.textContent||action.target}`);
        row?.classList.add("selected");
      }
      if(!["select","toggle"].includes(action.verb)){
        const button=document.querySelector(`[data-action="${CSS.escape(action.verb)}"]`);
        await moveReplayCursor(button,titleCase(action.verb));
      }
      state.visualActions.push(action);paintDynamicWorkspace();await wait(450);
    }
    const caption=document.querySelector("#replay-label");if(caption)caption.textContent="Completed";await wait(900);
  }finally{window.__REPLAY_DONE__=true}
}
window.onpopstate=()=>location.reload();
loadCases().catch(e=>root.innerHTML=`<div class="loading">Could not start Vibe OS: ${esc(e.message)}</div>`);
