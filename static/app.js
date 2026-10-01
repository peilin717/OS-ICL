const root = document.querySelector("#app");
const state = { cases: [], session: null, selected: null, replay: false };

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
  if(sid){ state.session=await api(`/api/v1/sessions/${sid}`); renderSession(); notifyParent("VIBE_READY",{status:state.session.status}); } else renderDashboard();
}

function renderDashboard(){
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
  const simulator=`<section class="simulator-frame"><div class="vibe-os" id="capture-area"><div class="os-topbar"><div class="os-topbar-left"><div class="os-logo">V</div><strong>Vibe OS</strong><span>Workspace</span></div><div class="os-topbar-right"><span>English (US)</span><span>● Online</span><strong>10:24</strong></div></div><div class="os-workspace"><div class="window"><div class="window-titlebar"><div class="traffic"><i class="dot"></i><i class="dot"></i><i class="dot"></i></div><span class="window-title">${esc(c.app)}</span><span class="window-sub">Simulation · ${esc(c.id)}</span></div><div class="app-shell"><aside class="app-sidebar"><div class="side-title">Applications</div>${["Files","Monitor","Terminal","Settings","Devices","Notifications","Jobs","Transfers"].map(x=>`<div class="side-item ${c.app.includes(x)?"active":""}">${appGlyph(x)} &nbsp;${x}</div>`).join("")}</aside><section class="app-main"><div class="app-toolbar"><span class="crumb">Vibe OS / <strong>${esc(c.app)}</strong></span><span style="margin-left:auto" class="tag">Seed ${s.seed}</span></div><div class="task-banner"><span class="task-badge">TASK</span><strong>${esc(c.task)}</strong></div>${s.clues?.length?`<div class="source-panel">${s.clues.map(x=>`<span>${esc(x)}</span>`).join("")}</div>`:""}<div class="items">${renderItems(s)}</div>${renderActionBar(s)}</section></div></div></div><div class="os-dock">${["F","M","T","S","D","N"].map(x=>`<div class="dock-icon">${x}</div>`).join("")}</div></div></section>`;
  if(state.replay){
    document.body.classList.add("replay-mode");
    root.innerHTML=`<main class="replay-only">${simulator}<div class="replay-cursor" id="replay-cursor"></div><div class="replay-label" id="replay-label">Demonstration</div></main>`;
    window.__REPLAY_DONE__=false; setTimeout(runReplay,700); return;
  }
  document.body.classList.remove("replay-mode");
  root.innerHTML=header(`<button class="btn" id="back">All cases</button>`)+`<main class="session-layout">${simulator}<aside class="control-panel">${renderControls(s)}</aside></main>`;
  bindSession();
}
function renderItems(s){
  const acted=state.replay?new Set():new Set(s.actions.map(a=>a.target));
  return `<div class="item-head"><span></span><span>Name</span><span>Type</span><span>Value</span><span>CPU</span><span>Memory</span><span>Status</span></div>${s.items.map(item=>`<div class="item-row ${state.selected===item.id?"selected":""} ${acted.has(item.id)?"done":""}" data-item="${item.id}"><div class="item-icon" style="background:${item.color==="Blue"?"#536ee5":item.color==="Amber"?"#d9962e":"#8b63d5"}">${esc((item.display_type||item.symbol)[0])}</div><div><div class="item-name">${esc(item.name)}</div><div class="item-sub">${item.extension} · PID ${item.pid}</div></div><span class="metric">${esc(item.display_type||item.symbol)}</span><span class="metric">${item.value}</span><span class="metric">${item.cpu}%</span><span class="metric">${item.memory} MB</span><span class="metric">${esc(item.scenario||item.status)}</span></div>`).join("")}`;
}
function renderActionBar(s){
  const f=s.case.family;
  if(f==="selection") return `<div class="action-bar"><span class="hint">Click a row to select the target.</span></div>`;
  if(f==="selection_set") return `<div class="action-bar"><span class="hint">Click rows to toggle them.</span><button class="btn primary" data-action="submit">Submit selection</button></div>`;
  const canAct=state.selected||state.replay;
  return `<div class="action-bar"><span class="hint">Select an item, then choose an action.</span>${s.available_actions.map(a=>`<button class="btn ${canAct?"":"disabled"}" data-action="${esc(a)}" ${canAct?"":"disabled"}>${titleCase(a)}</button>`).join("")}</div>`;
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
  document.querySelector("#back").onclick=()=>{history.pushState({},"","/");state.session=null;state.selected=null;renderDashboard()};
  document.querySelectorAll("[data-item]").forEach(row=>row.onclick=async()=>{
    const id=row.dataset.item,f=state.session.case.family;
    if(f==="selection") return sendAction("select",id);
    if(f==="selection_set") return sendAction("toggle",id);
    state.selected=id; renderSession();
  });
  document.querySelectorAll("[data-action]").forEach(btn=>btn.onclick=()=>sendAction(btn.dataset.action,btn.dataset.action==="submit"?"workspace":state.selected));
  document.querySelector("#finish")?.addEventListener("click",()=>command("finish")); document.querySelector("#reset").onclick=()=>command("reset");
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
      if(action.target!=="workspace"){
        const row=document.querySelector(`[data-item="${CSS.escape(action.target)}"]`);
        await moveReplayCursor(row,`Select ${row?.querySelector(".item-name")?.textContent||action.target}`);
        row?.classList.add("selected");
      }
      if(!["select","toggle"].includes(action.verb)){
        const button=document.querySelector(`[data-action="${CSS.escape(action.verb)}"]`);
        await moveReplayCursor(button,titleCase(action.verb));
      }
      document.querySelector(`[data-item="${CSS.escape(action.target)}"]`)?.classList.add("done");
      await wait(350);
    }
    const caption=document.querySelector("#replay-label");if(caption)caption.textContent="Completed";await wait(900);
  }finally{window.__REPLAY_DONE__=true}
}
window.onpopstate=()=>location.reload();
loadCases().catch(e=>root.innerHTML=`<div class="loading">Could not start Vibe OS: ${esc(e.message)}</div>`);
