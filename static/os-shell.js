const APPS = [
  { id: "files", title: "Files", glyph: "F" },
  { id: "settings", title: "Settings", glyph: "S" },
  { id: "monitor", title: "System Monitor", glyph: "M" },
  { id: "terminal", title: "Terminal", glyph: ">_" },
  { id: "devices", title: "Devices", glyph: "D" },
  { id: "notifications", title: "Notifications", glyph: "N" },
  { id: "jobs", title: "Jobs", glyph: "J" },
  { id: "transfers", title: "Transfers", glyph: "X" },
  { id: "editor", title: "Text Editor", glyph: "T" },
  { id: "calendar", title: "Calendar", glyph: "C" },
];

const FILES = [
  ["desktop", null, "Desktop", "folder"], ["documents", null, "Documents", "folder"],
  ["downloads", null, "Downloads", "folder"], ["pictures", null, "Pictures", "folder"],
  ["projects", null, "Projects", "folder"], ["trash", null, "Trash", "folder"],
  ["reports", "documents", "Reports", "folder"], ["research", "documents", "Research", "folder"],
  ["q1", "reports", "Q1", "folder"], ["q2", "reports", "Q2", "folder"],
  ["notes", "research", "Notes", "folder"], ["datasets", "research", "Datasets", "folder"],
  ["complete", "downloads", "Complete", "folder"], ["in-progress", "downloads", "In progress", "folder"],
  ["atlas", "projects", "Atlas", "folder"], ["vela", "projects", "Vela", "folder"],
  ["atlas-source", "atlas", "Source", "folder"], ["atlas-builds", "atlas", "Builds", "folder"],
  ["brief", "desktop", "Project brief.txt", "text", "4 KB"],
  ["readme", "documents", "Welcome.txt", "text", "2 KB"],
  ["report-vib", "q2", "Quarterly report.vib", "document", "1.8 MB"],
  ["budget", "q2", "Budget notes.txt", "text", "12 KB"],
  ["dataset", "datasets", "signals.csv", "data", "8.4 MB"],
  ["photo", "pictures", "Harbour.png", "image", "3.1 MB"],
  ["package", "complete", "VibeTools.vib", "package", "24 MB"],
  ["transfer", "in-progress", "Research archive.zip", "archive", "61 MB"],
  ["main-js", "atlas-source", "main.js", "code", "9 KB"],
  ["build-log", "atlas-builds", "build-104.log", "text", "42 KB"],
].map(([id, parent, name, type, size = "—"], index) => ({
  id, parent, name, type, size, modified: `Oct ${String(2 - Math.min(index % 2, 1)).padStart(2, "0")}, 2026`,
  starred: ["report-vib", "dataset", "main-js"].includes(id), deleted: false,
  content: type === "text" || type === "code" ? `${name}\n\nThis is a simulated Vibe OS document.\nChanges are stored in frontend state.` : "",
}));

const SETTINGS = {
  system: { title: "System", pages: {
    display: ["Display", ["Brightness", "Scale", "Night light"]],
    sound: ["Sound", ["Output device", "Volume", "System sounds"]],
    power: ["Power & battery", ["Battery saver", "Screen timeout", "Power mode"]],
    notifications: ["Notifications", ["App notifications", "Do not disturb", "Priority alerts"]],
  }},
  devices: { title: "Bluetooth & devices", pages: {
    bluetooth: ["Bluetooth", ["Bluetooth", "Discoverable", "Swift pair"]],
    printers: ["Printers & scanners", ["Default printer", "Queue alerts", "Automatic setup"]],
    mouse: ["Mouse", ["Primary button", "Pointer speed", "Scroll inactive windows"]],
  }},
  network: { title: "Network", pages: {
    wifi: ["Wi-Fi", ["Wi-Fi", "Random hardware address", "Metered connection"]],
    vpn: ["VPN", ["Auto-connect", "Allow roaming", "Advanced options"]],
    proxy: ["Proxy", ["Detect settings", "Setup script", "Manual proxy"]],
  }},
  personalization: { title: "Personalisation", pages: {
    background: ["Background", ["Picture", "Fit", "Desktop slideshow"]],
    colors: ["Colours", ["Dark mode", "Accent colour", "Transparency"]],
    taskbar: ["Taskbar", ["Search", "Task view", "Auto-hide"]],
  }},
  apps: { title: "Apps", pages: { installed: ["Installed apps", ["App updates", "Archive apps", "App aliases"]], startup: ["Startup", ["Terminal", "Transfers", "Calendar"]] }},
  accessibility: { title: "Accessibility", pages: { vision: ["Vision", ["Text size", "Contrast", "Motion"]], interaction: ["Interaction", ["Sticky keys", "Filter keys", "Voice access"]] }},
  privacy: { title: "Privacy", pages: { permissions: ["App permissions", ["Location", "Camera", "Microphone"]], diagnostics: ["Diagnostics", ["Optional data", "Tailored experiences", "Feedback"]] }},
  update: { title: "Update", pages: { status: ["Update status", ["Automatic updates", "Restart notification", "Early updates"]], history: ["Update history", ["Quality updates", "Driver updates", "Recovery"]] }},
};

const PROCESSES = [
  ["Files", 12, 340, "Running"], ["Terminal", 4, 188, "Running"],
  ["Sync Service", 28, 512, "Warning"], ["Media Indexer", 7, 224, "Paused"],
  ["Update Agent", 42, 680, "Running"], ["Window Manager", 9, 156, "Running"],
].map(([name, cpu, memory, status], i) => ({ id: `proc-${i}`, name, pid: 840 + i * 17, cpu, memory, status }));

const DEVICES = [
  { id: "dev-1", name: "Vibe Keyboard", kind: "Keyboard", status: "Connected", battery: 82, signal: 91 },
  { id: "dev-2", name: "Orbit Headphones", kind: "Audio", status: "Paired", battery: 64, signal: 76 },
  { id: "dev-3", name: "Studio Display", kind: "Display", status: "Connected", battery: null, signal: 100 },
  { id: "dev-4", name: "Nova Phone", kind: "Nearby", status: "Available", battery: 48, signal: 67 },
];

const NOTICES = [
  { id: "notice-1", app: "System", title: "Update ready", body: "Restart when convenient.", unread: true },
  { id: "notice-2", app: "Transfers", title: "Download completed", body: "VibeTools.vib is ready.", unread: true },
  { id: "notice-3", app: "Devices", title: "Orbit Headphones connected", body: "Battery is 64%.", unread: false },
];

const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const appById = id => APPS.find(app => app.id === id) || APPS[0];

function initialState() {
  return {
    files: structuredClone(FILES), settings: {}, processes: structuredClone(PROCESSES),
    devices: structuredClone(DEVICES), notices: structuredClone(NOTICES),
    jobs: [
      { id:"job-1", name:"Nightly backup", status:"Scheduled", detail:"23:30" },
      { id:"job-2", name:"Build Atlas", status:"Running", detail:"68%" },
      { id:"job-3", name:"Index research", status:"Failed", detail:"Retry available" },
    ],
    transfers: [
      { id:"tx-1", name:"Research archive.zip", status:"Downloading", progress:61 },
      { id:"tx-2", name:"VibeTools.vib", status:"Completed", progress:100 },
      { id:"tx-3", name:"Dataset mirror", status:"Failed", progress:34 },
    ],
    windows: [], activeWindow: null, nextWindow: 1, startOpen: false, startSearch: "", quickOpen: false,
    noticeOpen: false, desktopMenu: null, contextMenu: null, dialog: null,
    clipboard: null, selectedDesktop: null, terminalLines: ["Vibe Terminal 1.0", "Type 'help' for simulated commands."],
  };
}

function makeWindow(state, appId, options = {}) {
  const app = appById(appId), count = state.nextWindow++;
  const win = {
    id: `win-${appId}-${count}`, appId, title: options.title || app.title,
    x: options.x ?? 130 + (count % 4) * 26, y: options.y ?? 64 + (count % 3) * 24,
    width: options.width ?? (appId === "settings" ? 990 : 920), height: options.height ?? 570,
    mode: "normal", restore: null, z: count + 10,
    route: options.route || (appId === "files" ? "documents" : "home"),
    history: [], selected: null, search: "", sort: "name", section: options.section || null,
    page: options.page || null, fileId: options.fileId || null,
  };
  state.windows.push(win); state.activeWindow = win.id; return win;
}

function children(state, parent) {
  return state.files.filter(file => file.parent === parent && (parent === "trash" ? file.deleted : !file.deleted));
}

function fileById(state, id) { return state.files.find(file => file.id === id); }

function breadcrumbs(state, route) {
  const result = []; let current = fileById(state, route);
  while (current) { result.unshift(current); current = fileById(state, current.parent); }
  return result;
}

function renderFiles(state, win) {
  const locations = ["desktop","documents","downloads","pictures","projects","trash"];
  const folder = fileById(state, win.route) || fileById(state, "documents");
  let list = children(state, folder.id);
  if (win.search) list = list.filter(file => file.name.toLowerCase().includes(win.search.toLowerCase()));
  list.sort((a,b) => win.sort === "type" ? a.type.localeCompare(b.type) : a.name.localeCompare(b.name));
  const crumbs = breadcrumbs(state, folder.id);
  return `<div class="vos-app vos-files"><aside class="vos-nav"><div class="vos-nav-label">Locations</div>${locations.map(id=>{const item=fileById(state,id);return `<button data-files-location="${id}" class="${folder.id===id?"active":""}"><span>${item.type==="folder"?"▰":"•"}</span>${esc(item.name)}</button>`}).join("")}</aside><section class="vos-content"><div class="vos-commandbar"><button data-files-back title="Back">←</button><button data-files-up title="Up">↑</button><div class="vos-breadcrumb">${crumbs.map((item,index)=>`<button data-files-location="${item.id}">${esc(item.name)}</button>${index<crumbs.length-1?"<span>›</span>":""}`).join("")}</div><button data-new-folder>New folder</button><button data-paste ${state.clipboard?"":"disabled"}>Paste</button><select data-file-sort><option value="name" ${win.sort==="name"?"selected":""}>Name</option><option value="type" ${win.sort==="type"?"selected":""}>Type</option></select><input data-file-search placeholder="Search ${esc(folder.name)}" value="${esc(win.search)}"></div><div class="vos-file-head"><span>Name</span><span>Type</span><span>Size</span><span>Modified</span></div><div class="vos-file-list">${list.length?list.map(file=>`<button class="vos-file-row ${win.selected===file.id?"selected":""}" data-file-id="${file.id}"><span class="vos-file-name"><i class="vos-file-icon ${file.type}">${file.type==="folder"?"▰":file.type.slice(0,1).toUpperCase()}</i><span><strong>${esc(file.name)}</strong>${file.starred?"<small>★ Starred</small>":""}</span></span><span>${esc(file.type)}</span><span>${esc(file.size)}</span><span>${esc(file.modified)}</span></button>`).join(""):`<div class="vos-empty">This folder is empty.</div>`}</div><footer class="vos-statusbar"><span>${list.length} item${list.length===1?"":"s"}</span><span>${state.clipboard?`${state.clipboard.mode}: ${fileById(state,state.clipboard.id)?.name||"item"}`:"Ready"}</span></footer></section></div>`;
}

function renderSettings(state, win) {
  const section = win.section && SETTINGS[win.section] ? win.section : "system";
  const pages = SETTINGS[section].pages;
  const page = win.page && pages[win.page] ? win.page : Object.keys(pages)[0];
  const [title, controls] = pages[page];
  const sectionEntries=Object.entries(SETTINGS).filter(([,item])=>!win.search||item.title.toLowerCase().includes(win.search.toLowerCase()));
  return `<div class="vos-app vos-settings"><aside class="vos-settings-sections"><div class="vos-profile"><span>VP</span><strong>Vibe Profile</strong><small>Local account</small></div><input data-settings-search placeholder="Find a setting" value="${esc(win.search)}">${sectionEntries.map(([id,item])=>`<button data-settings-section="${id}" class="${section===id?"active":""}">${esc(item.title)}</button>`).join("")}</aside><section class="vos-settings-pages"><header><button data-settings-home>‹</button><div><small>${esc(SETTINGS[section].title)}</small><h2>${esc(title)}</h2></div></header><div class="vos-settings-grid"><nav>${Object.entries(pages).map(([id,item])=>`<button data-settings-page="${id}" class="${page===id?"active":""}"><strong>${esc(item[0])}</strong><small>Open settings</small></button>`).join("")}</nav><main><h3>${esc(title)}</h3>${controls.map((name,index)=>{const key=`${section}.${page}.${index}`,on=state.settings[key]??index%2===0;return `<button class="vos-setting-row" data-setting-toggle="${key}"><span><strong>${esc(name)}</strong><small>${on?"On":"Off"}</small></span><i class="vos-switch ${on?"on":""}"></i></button>`}).join("")}</main></div></section></div>`;
}

function renderMonitor(state, win) {
  const section = win.section || "processes";
  const tabs = ["processes","performance","startup","users","details","services"];
  const content = section === "performance" ? `<div class="vos-performance"><div><small>CPU</small><strong>37%</strong><i style="--value:37%"></i></div><div><small>Memory</small><strong>5.8 / 16 GB</strong><i style="--value:46%"></i></div><div><small>Disk</small><strong>18%</strong><i style="--value:18%"></i></div><div><small>Network</small><strong>42 Mbps</strong><i style="--value:62%"></i></div></div>` : `<div class="vos-process-head"><span>Name</span><span>PID</span><span>Status</span><span>CPU</span><span>Memory</span><span></span></div><div class="vos-processes">${state.processes.map(proc=>`<div class="vos-process"><strong>${esc(proc.name)}</strong><span>${proc.pid}</span><span>${proc.status}</span><span>${proc.cpu}%</span><span>${proc.memory} MB</span><button data-end-process="${proc.id}">End task</button></div>`).join("")}</div>`;
  return `<div class="vos-app vos-monitor"><aside class="vos-nav"><div class="vos-nav-label">System Monitor</div>${tabs.map(id=>`<button data-monitor-section="${id}" class="${section===id?"active":""}">${id[0].toUpperCase()+id.slice(1)}</button>`).join("")}</aside><section class="vos-content"><div class="vos-page-title"><div><h2>${section[0].toUpperCase()+section.slice(1)}</h2><p>Live simulated system information</p></div><button data-run-task>Run new task</button></div>${content}</section></div>`;
}

function renderTerminal(state) {
  return `<div class="vos-terminal"><div class="vos-terminal-tabs"><button class="active" data-terminal-close>Terminal 1 ×</button><button data-terminal-new>＋</button></div><div class="vos-terminal-output">${state.terminalLines.map(line=>`<div>${esc(line)}</div>`).join("")}<form data-terminal-form><span>vibe@desktop:~$</span><input data-terminal-input autocomplete="off" autofocus></form></div></div>`;
}

function renderDevices(state, win) {
  const section=win.section||"overview";
  const tabs=["overview","bluetooth","displays","audio","printers"];
  return `<div class="vos-app"><aside class="vos-nav"><div class="vos-nav-label">Devices</div>${tabs.map(id=>`<button data-device-section="${id}" class="${section===id?"active":""}">${id[0].toUpperCase()+id.slice(1)}</button>`).join("")}</aside><section class="vos-content"><div class="vos-page-title"><div><h2>${section==="overview"?"Connected devices":section[0].toUpperCase()+section.slice(1)}</h2><p>Manage nearby and paired hardware</p></div><button data-device-refresh>Refresh</button></div><div class="vos-card-grid">${state.devices.map(device=>`<article class="vos-device-card"><i>${device.kind[0]}</i><div><h3>${esc(device.name)}</h3><p>${esc(device.kind)} · ${device.battery===null?"Powered":`${device.battery}% battery`} · Signal ${device.signal}%</p></div><button data-device-action="${device.id}">${device.status==="Connected"?"Disconnect":device.status==="Available"?"Pair":"Connect"}</button><span class="vos-status ${device.status.toLowerCase()}">${esc(device.status)}</span></article>`).join("")}</div></section></div>`;
}

function renderNotificationsApp(state) {
  return `<div class="vos-simple-app"><div class="vos-page-title"><div><h2>Notifications</h2><p>Recent activity from apps and the system</p></div><button data-clear-notices>Clear all</button></div><div class="vos-notice-list">${state.notices.length?state.notices.map(n=>`<article class="${n.unread?"unread":""}"><i>${n.app[0]}</i><div><small>${esc(n.app)}</small><h3>${esc(n.title)}</h3><p>${esc(n.body)}</p></div><button data-dismiss-notice="${n.id}">×</button></article>`).join(""):`<div class="vos-empty">You're all caught up.</div>`}</div></div>`;
}

function renderJobs(state, type) {
  const items=type==="jobs"?state.jobs:state.transfers;
  return `<div class="vos-simple-app"><div class="vos-page-title"><div><h2>${type==="jobs"?"Jobs":"Transfers"}</h2><p>${type==="jobs"?"Scheduled and background work":"Downloads, uploads, and shared files"}</p></div><button data-add-work="${type}">Add</button></div><div class="vos-work-list">${items.map(item=>`<article><i>${item.status[0]}</i><div><h3>${esc(item.name)}</h3><p>${esc(item.status)} · ${esc(item.detail??`${item.progress}%`)}</p>${item.progress!==undefined?`<span><b style="width:${item.progress}%"></b></span>`:""}</div><button data-work-action="${type}:${item.id}">${item.status==="Failed"?"Retry":item.status==="Running"||item.status==="Downloading"?"Pause":"Open"}</button></article>`).join("")}</div></div>`;
}

function renderEditor(state, win) {
  const file=fileById(state,win.fileId)||fileById(state,"brief");
  return `<div class="vos-editor"><div class="vos-editor-menu">File &nbsp; Edit &nbsp; View <span>${esc(file.name)}</span></div><textarea data-editor-text="${file.id}" spellcheck="false">${esc(file.content)}</textarea><footer>Ln 1, Col 1 · UTF-8 · Saved locally</footer></div>`;
}

function renderCalendar() {
  const days=Array.from({length:35},(_,i)=>i<3?"":i-2);
  return `<div class="vos-simple-app vos-calendar"><div class="vos-page-title"><div><h2>October 2026</h2><p>Thursday, October 2</p></div><button data-new-event>New event</button></div><div class="vos-calendar-grid">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat",...days].map((day,i)=>`<div class="${day===2?"today":""} ${i<7?"weekday":""}">${day}</div>`).join("")}</div></div>`;
}

function renderApp(state, win) {
  return win.appId==="files"?renderFiles(state,win):win.appId==="settings"?renderSettings(state,win):
    win.appId==="monitor"?renderMonitor(state,win):win.appId==="terminal"?renderTerminal(state):
    win.appId==="devices"?renderDevices(state,win):win.appId==="notifications"?renderNotificationsApp(state):
    win.appId==="jobs"?renderJobs(state,"jobs"):win.appId==="transfers"?renderJobs(state,"transfers"):
    win.appId==="editor"?renderEditor(state,win):renderCalendar();
}

function renderWindow(state, win) {
  if(win.mode==="closed"||win.mode==="minimised")return "";
  const app=appById(win.appId),max=win.mode==="maximised";
  return `<section class="vos-window ${state.activeWindow===win.id?"active":""} ${max?"maximised":""}" data-window="${win.id}" style="left:${win.x}px;top:${win.y}px;width:${win.width}px;height:${win.height}px;z-index:${win.z}"><header class="vos-titlebar" data-drag-window="${win.id}"><span class="vos-appmark">${esc(app.glyph)}</span><strong>${esc(win.title)}</strong><span class="vos-title-spacer"></span><button data-win-min="${win.id}" aria-label="Minimise">—</button><button data-win-max="${win.id}" aria-label="Maximise">□</button><button data-win-close="${win.id}" class="close" aria-label="Close">×</button></header><div class="vos-window-content">${renderApp(state,win)}</div>${max?"":`<i class="vos-resizer" data-resize-window="${win.id}"></i>`}</section>`;
}

function renderStart(state) {
  if(!state.startOpen)return "";
  const apps=APPS.slice(0,8).filter(app=>!state.startSearch||app.title.toLowerCase().includes(state.startSearch.toLowerCase()));
  return `<section class="vos-start-panel"><div class="vos-start-search">⌕ <input data-start-search placeholder="Search apps, settings, and files" value="${esc(state.startSearch)}"></div><div class="vos-start-head"><strong>${state.startSearch?"Search results":"Pinned"}</strong><span>All apps ›</span></div><div class="vos-start-apps">${apps.map(app=>`<button data-launch-app="${app.id}"><i>${esc(app.glyph)}</i><span>${esc(app.title)}</span></button>`).join("")}</div><div class="vos-recommended"><strong>Recommended</strong><button data-open-file="report-vib"><i>V</i><span>Quarterly report.vib<small>Recently opened</small></span></button><button data-open-file="brief"><i>T</i><span>Project brief.txt<small>Today</small></span></button></div><footer><span class="vos-avatar">VP</span><strong>Vibe Profile</strong><button data-power>⏻</button></footer></section>`;
}

function renderQuick(state){return state.quickOpen?`<section class="vos-quick-panel"><h3>Quick settings</h3><div>${["Wi-Fi","Bluetooth","Airplane mode","Night light","Accessibility","Battery saver"].map((x,i)=>`<button data-quick-toggle="quick.${i}" class="${state.settings[`quick.${i}`]??i<2?"on":""}"><i>${i<2?"●":"○"}</i>${x}</button>`).join("")}</div><label>Volume <input type="range" value="72"></label><label>Brightness <input type="range" value="84"></label></section>`:""}

function renderNoticePanel(state){return state.noticeOpen?`<section class="vos-notice-panel"><header><strong>Notifications</strong><button data-clear-notices>Clear all</button></header>${state.notices.map(n=>`<article><i>${n.app[0]}</i><div><strong>${esc(n.title)}</strong><p>${esc(n.body)}</p></div><button data-dismiss-notice="${n.id}">×</button></article>`).join("")||"<div class='vos-empty'>No new notifications</div>"}</section>`:""}

function renderContext(state){
  const menu=state.contextMenu||state.desktopMenu;if(!menu)return"";
  const isFile=menu.fileId;
  const items=isFile?[["open","Open"],["copy","Copy"],["cut","Cut"],["rename","Rename"],["delete","Move to Trash"],["properties","Properties"]]:[["new-folder","New folder"],["refresh","Refresh"],["sort-name","Sort by name"],["settings","Display settings"]];
  return `<div class="vos-context-menu" style="left:${menu.x}px;top:${menu.y}px">${items.map(([action,label])=>`<button data-context-action="${action}" ${isFile?`data-context-file="${menu.fileId}"`:""}>${label}</button>`).join("")}</div>`;
}

function renderDialog(state){
  const d=state.dialog;if(!d)return"";
  if(d.type==="rename")return `<div class="vos-modal-shade"><form class="vos-dialog" data-rename-form><h2>Rename item</h2><p>Enter a new name for <strong>${esc(fileById(state,d.fileId)?.name)}</strong>.</p><input name="name" value="${esc(fileById(state,d.fileId)?.name)}" autofocus><footer><button type="button" data-dialog-cancel>Cancel</button><button class="primary">Rename</button></footer></form></div>`;
  if(d.type==="properties"){const f=fileById(state,d.fileId),tab=d.tab||"general";return `<div class="vos-modal-shade"><section class="vos-dialog"><h2>${esc(f.name)} properties</h2><div class="vos-dialog-tabs">${["general","details","permissions"].map(id=>`<button data-prop-tab="${id}" class="${tab===id?"active":""}">${id[0].toUpperCase()+id.slice(1)}</button>`).join("")}</div><dl>${tab==="permissions"?`<dt>Owner</dt><dd>Vibe Profile</dd><dt>Access</dt><dd>Read and write</dd><dt>Shared</dt><dd>No</dd>`:tab==="details"?`<dt>Name</dt><dd>${esc(f.name)}</dd><dt>Modified</dt><dd>${esc(f.modified)}</dd><dt>Starred</dt><dd>${f.starred?"Yes":"No"}</dd>`:`<dt>Type</dt><dd>${esc(f.type)}</dd><dt>Location</dt><dd>${esc(fileById(state,f.parent)?.name||"Desktop")}</dd><dt>Size</dt><dd>${esc(f.size)}</dd><dt>Modified</dt><dd>${esc(f.modified)}</dd>`}</dl><footer><button data-dialog-cancel>Close</button></footer></section></div>`}
  if(d.type==="power")return `<div class="vos-modal-shade"><section class="vos-dialog"><h2>Power</h2><p>Choose a simulated power action.</p><div class="vos-power-options"><button data-power-action="lock">Lock</button><button data-power-action="restart">Restart</button><button data-power-action="shutdown">Shut down</button></div><footer><button data-dialog-cancel>Cancel</button></footer></section></div>`;
  if(d.type==="event")return `<div class="vos-modal-shade"><form class="vos-dialog" data-event-form><h2>New event</h2><p>Create a simulated calendar event.</p><input name="title" placeholder="Event title" autofocus><footer><button type="button" data-dialog-cancel>Cancel</button><button class="primary">Save</button></footer></form></div>`;
  return"";
}

function renderDesktop(state, root){
  const openWindows=state.windows.filter(w=>w.mode!=="closed");
  root.innerHTML=`<main class="vos-shell" data-desktop><div class="vos-wallpaper"><div class="vos-desktop-icons">${["files","settings","terminal","trash"].map(id=>{const app=id==="trash"?{id:"files",title:"Trash",glyph:"R"}:appById(id);return `<button data-desktop-app="${app.id}" ${id==="trash"?'data-route="trash"':""}><i>${app.glyph}</i><span>${app.title}</span></button>`}).join("")}</div>${state.windows.map(win=>renderWindow(state,win)).join("")}</div><footer class="vos-taskbar"><button class="vos-start-button ${state.startOpen?"active":""}" data-start-button>V</button><button data-taskbar-search>⌕</button><div class="vos-task-apps">${APPS.slice(0,6).map(app=>{const running=openWindows.some(w=>w.appId===app.id),active=openWindows.some(w=>w.appId===app.id&&w.id===state.activeWindow);return `<button data-task-app="${app.id}" class="${running?"running":""} ${active?"active":""}" title="${app.title}">${app.glyph}</button>`}).join("")}</div><div class="vos-tray"><button data-quick-button>⌃ &nbsp;◉ &nbsp;▰</button><button data-notice-button>${state.notices.some(n=>n.unread)?"● ":""}10:24<br><small>10/02/2026</small></button></div></footer>${renderStart(state)}${renderQuick(state)}${renderNoticePanel(state)}${renderContext(state)}${renderDialog(state)}</main>`;
}

function runCommand(state, value){
  const command=value.trim();if(!command)return;
  state.terminalLines.push(`vibe@desktop:~$ ${command}`);
  const [verb,arg]=command.split(/\s+/,2);
  if(verb==="help")state.terminalLines.push("Commands: ls, pwd, cd, cat, status, retry, clear, date");
  else if(verb==="ls")state.terminalLines.push("Documents  Downloads  Pictures  Projects");
  else if(verb==="pwd")state.terminalLines.push("/home/vibe");
  else if(verb==="date")state.terminalLines.push("Fri Oct 2 10:24:00 2026");
  else if(verb==="status")state.terminalLines.push("System online · 6 processes · 1 failed job");
  else if(verb==="retry"){const failed=state.jobs.find(j=>j.status==="Failed");if(failed)failed.status="Running";state.terminalLines.push(failed?`Retrying ${failed.name}…`:"No failed jobs.")}
  else if(verb==="clear")state.terminalLines=[];
  else if(verb==="cat")state.terminalLines.push(arg?`Simulated contents of ${arg}`:"cat: missing file operand");
  else if(verb==="cd")state.terminalLines.push(arg?`Changed simulated directory to ${arg}`:"/home/vibe");
  else state.terminalLines.push(`${verb}: command not found`);
}

export function mountOs(root){
  const state=initialState();makeWindow(state,"files",{route:"documents",x:120,y:58,width:980,height:580});
  const paint=()=>renderDesktop(state,root);
  const active=()=>state.windows.find(w=>w.id===state.activeWindow);
  const focus=id=>{const win=state.windows.find(w=>w.id===id);if(!win)return;win.z=Math.max(10,...state.windows.map(w=>w.z))+1;state.activeWindow=id;if(win.mode==="minimised")win.mode="normal"};
  const launch=(appId,options={})=>{state.startOpen=false;state.quickOpen=false;state.noticeOpen=false;const existing=!options.newWindow&&state.windows.find(w=>w.appId===appId&&w.mode!=="closed");if(existing){focus(existing.id);if(options.route)existing.route=options.route}else makeWindow(state,appId,options);paint()};
  const closeMenus=()=>{state.startOpen=false;state.quickOpen=false;state.noticeOpen=false;state.contextMenu=null;state.desktopMenu=null};

  root.onclick=event=>{
    const button=event.target.closest("button,[data-window]");
    if(!button){if(!event.target.closest(".vos-context-menu,.vos-start-panel,.vos-quick-panel,.vos-notice-panel")){closeMenus();paint()}return}
    const data=button.dataset;
    if(data.window&&!event.target.closest("button")){focus(data.window);paint();return}
    if(data.startButton!==undefined){state.startOpen=!state.startOpen;state.quickOpen=false;state.noticeOpen=false;paint();return}
    if(data.taskbarSearch!==undefined){state.startOpen=true;state.startSearch="";state.quickOpen=false;state.noticeOpen=false;paint();setTimeout(()=>root.querySelector("[data-start-search]")?.focus(),0);return}
    if(data.quickButton!==undefined){state.quickOpen=!state.quickOpen;state.startOpen=false;state.noticeOpen=false;paint();return}
    if(data.noticeButton!==undefined){state.noticeOpen=!state.noticeOpen;state.startOpen=false;state.quickOpen=false;paint();return}
    if(data.desktopApp) return launch(data.desktopApp,{route:data.route||undefined,newWindow:true});
    if(data.launchApp) return launch(data.launchApp);
    if(data.taskApp){const wins=state.windows.filter(w=>w.appId===data.taskApp&&w.mode!=="closed");if(!wins.length)return launch(data.taskApp);const win=wins.find(w=>w.id===state.activeWindow)||wins[0];if(win.id===state.activeWindow&&win.mode!=="minimised")win.mode="minimised";else focus(win.id);paint();return}
    if(data.winMin){const w=state.windows.find(x=>x.id===data.winMin);w.mode="minimised";state.activeWindow=null;paint();return}
    if(data.winMax){const w=state.windows.find(x=>x.id===data.winMax);if(w.mode==="maximised"){Object.assign(w,w.restore);w.restore=null;w.mode="normal"}else{w.restore={x:w.x,y:w.y,width:w.width,height:w.height};w.mode="maximised"}focus(w.id);paint();return}
    if(data.winClose){state.windows.find(x=>x.id===data.winClose).mode="closed";state.activeWindow=null;paint();return}
    const win=active();if(!win)return;
    if(data.filesLocation){win.history.push(win.route);win.route=data.filesLocation;win.selected=null;paint();return}
    if(data.filesBack!==undefined&&win.history.length){win.route=win.history.pop();paint();return}
    if(data.filesUp!==undefined){const folder=fileById(state,win.route);if(folder?.parent)win.route=folder.parent;paint();return}
    if(data.fileId){win.selected=data.fileId;root.querySelectorAll(".vos-file-row.selected").forEach(row=>row.classList.remove("selected"));button.classList.add("selected");return}
    if(data.newFolder!==undefined){const id=`folder-${Date.now()}`;state.files.push({id,parent:win.route,name:"New folder",type:"folder",size:"—",modified:"Oct 02, 2026",starred:false,deleted:false,content:""});state.dialog={type:"rename",fileId:id};paint();return}
    if(data.paste!==undefined&&state.clipboard){const source=fileById(state,state.clipboard.id);if(source){if(state.clipboard.mode==="cut")source.parent=win.route;else state.files.push({...source,id:`${source.id}-copy-${Date.now()}`,parent:win.route,name:`${source.name} copy`});state.clipboard=null}paint();return}
    if(data.settingsSection){win.section=data.settingsSection;win.page=null;paint();return}
    if(data.settingsPage){win.page=data.settingsPage;paint();return}
    if(data.settingsHome!==undefined){win.section="system";win.page="display";paint();return}
    if(data.settingToggle){state.settings[data.settingToggle]=!(state.settings[data.settingToggle]??true);paint();return}
    if(data.monitorSection){win.section=data.monitorSection;paint();return}
    if(data.endProcess){state.processes=state.processes.filter(p=>p.id!==data.endProcess);paint();return}
    if(data.runTask!==undefined){state.processes.push({id:`proc-${Date.now()}`,name:"New task",pid:900+state.processes.length*11,cpu:0,memory:32,status:"Running"});paint();return}
    if(data.deviceSection){win.section=data.deviceSection;paint();return}
    if(data.deviceRefresh!==undefined){state.devices.forEach((device,index)=>device.signal=Math.max(20,Math.min(100,device.signal+(index%2?2:-2))));state.notices.unshift({id:`notice-${Date.now()}`,app:"Devices",title:"Device list refreshed",body:"Nearby device signals were updated.",unread:true});paint();return}
    if(data.deviceAction){const device=state.devices.find(d=>d.id===data.deviceAction);device.status=device.status==="Connected"?"Paired":"Connected";state.notices.unshift({id:`notice-${Date.now()}`,app:"Devices",title:`${device.name} ${device.status.toLowerCase()}`,body:"Device state updated.",unread:true});paint();return}
    if(data.dismissNotice){state.notices=state.notices.filter(n=>n.id!==data.dismissNotice);paint();return}
    if(data.clearNotices!==undefined){state.notices=[];paint();return}
    if(data.workAction){const [type,id]=data.workAction.split(":");const item=(type==="jobs"?state.jobs:state.transfers).find(x=>x.id===id);item.status=item.status==="Failed"?"Running":item.status==="Running"||item.status==="Downloading"?"Paused":"Opened";paint();return}
    if(data.addWork){if(data.addWork==="jobs")state.jobs.push({id:`job-${Date.now()}`,name:"New scheduled job",status:"Scheduled",detail:"Tomorrow"});else state.transfers.push({id:`tx-${Date.now()}`,name:"New transfer",status:"Downloading",progress:0});paint();return}
    if(data.terminalNew!==undefined){state.terminalLines.push("Opened a new simulated terminal tab.");paint();return}
    if(data.terminalClose!==undefined){win.mode="closed";state.activeWindow=null;paint();return}
    if(data.newEvent!==undefined){state.dialog={type:"event"};paint();return}
    if(data.openFile){const file=fileById(state,data.openFile);state.startOpen=false;if(file.type==="folder")return launch("files",{route:file.id,newWindow:true});return launch("editor",{fileId:file.id,title:file.name,newWindow:true,width:760,height:520})}
    if(data.power!==undefined){state.dialog={type:"power"};state.startOpen=false;paint();return}
    if(data.powerAction){state.dialog=null;state.notices.unshift({id:`notice-${Date.now()}`,app:"System",title:`${data.powerAction[0].toUpperCase()+data.powerAction.slice(1)} simulated`,body:"No host system action was performed.",unread:true});paint();return}
    if(data.propTab){state.dialog.tab=data.propTab;paint();return}
    if(data.dialogCancel!==undefined){state.dialog=null;paint();return}
    if(data.quickToggle){state.settings[data.quickToggle]=!(state.settings[data.quickToggle]??false);paint();return}
    if(data.contextAction){const fileId=data.contextFile,action=data.contextAction;state.contextMenu=null;state.desktopMenu=null;if(action==="open"){const file=fileById(state,fileId);if(file.type==="folder"){win.history.push(win.route);win.route=file.id}else return launch("editor",{fileId,title:file.name,newWindow:true})}if(action==="copy"||action==="cut")state.clipboard={id:fileId,mode:action};if(action==="rename")state.dialog={type:"rename",fileId};if(action==="delete"){const file=fileById(state,fileId);file.deleted=true;file.parent="trash"}if(action==="properties")state.dialog={type:"properties",fileId};if(action==="new-folder"){const id=`folder-${Date.now()}`;state.files.push({id,parent:win?.route||"desktop",name:"New folder",type:"folder",size:"—",modified:"Oct 02, 2026",starred:false,deleted:false,content:""});state.dialog={type:"rename",fileId:id}}if(action==="settings")return launch("settings",{section:"system",page:"display"});paint();return}
  };

  root.ondblclick=event=>{const row=event.target.closest("[data-file-id]");if(!row)return;const win=active(),file=fileById(state,row.dataset.fileId);if(file.type==="folder"){win.history.push(win.route);win.route=file.id;win.selected=null;paint()}else launch("editor",{fileId:file.id,title:file.name,newWindow:true,width:760,height:520})};
  root.oncontextmenu=event=>{event.preventDefault();const row=event.target.closest("[data-file-id]");if(row)state.contextMenu={x:event.clientX,y:event.clientY,fileId:row.dataset.fileId};else if(event.target.closest("[data-desktop]"))state.desktopMenu={x:event.clientX,y:event.clientY};paint()};
  root.oninput=event=>{const win=active();if(event.target.matches("[data-file-search]")){win.search=event.target.value;root.querySelectorAll(".vos-file-row").forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(win.search.toLowerCase()))}if(event.target.matches("[data-settings-search]")){win.search=event.target.value;root.querySelectorAll(".vos-settings-sections>button").forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(win.search.toLowerCase()))}if(event.target.matches("[data-start-search]")){state.startSearch=event.target.value;root.querySelectorAll(".vos-start-apps button").forEach(row=>row.hidden=!row.textContent.toLowerCase().includes(state.startSearch.toLowerCase()))}if(event.target.matches("[data-editor-text]")){fileById(state,event.target.dataset.editorText).content=event.target.value}};
  root.onchange=event=>{if(event.target.matches("[data-file-sort]")){active().sort=event.target.value;paint()}};
  root.onsubmit=event=>{event.preventDefault();if(event.target.matches("[data-terminal-form]")){const input=event.target.querySelector("input");runCommand(state,input.value);paint();setTimeout(()=>root.querySelector("[data-terminal-input]")?.focus(),0)}if(event.target.matches("[data-rename-form]")){const name=new FormData(event.target).get("name")?.toString().trim();if(name)fileById(state,state.dialog.fileId).name=name;state.dialog=null;paint()}if(event.target.matches("[data-event-form]")){const title=new FormData(event.target).get("title")?.toString().trim()||"Untitled event";state.dialog=null;state.notices.unshift({id:`notice-${Date.now()}`,app:"Calendar",title:"Event created",body:title,unread:true});paint()}};
  root.onpointerdown=event=>{
    if(event.target.closest("button,input,select,textarea"))return;
    const title=event.target.closest("[data-drag-window]"),resize=event.target.closest("[data-resize-window]");
    if(!title&&!resize)return;const id=(title||resize).dataset[title?"dragWindow":"resizeWindow"],win=state.windows.find(w=>w.id===id);if(!win||win.mode==="maximised")return;focus(id);
    const start={x:event.clientX,y:event.clientY,wx:win.x,wy:win.y,ww:win.width,wh:win.height};
    const move=e=>{if(title){win.x=Math.max(0,start.wx+e.clientX-start.x);win.y=Math.max(36,start.wy+e.clientY-start.y)}else{win.width=Math.max(620,start.ww+e.clientX-start.x);win.height=Math.max(400,start.wh+e.clientY-start.y)}const el=root.querySelector(`[data-window="${id}"]`);if(el){el.style.left=`${win.x}px`;el.style.top=`${win.y}px`;el.style.width=`${win.width}px`;el.style.height=`${win.height}px`}};
    const up=()=>{document.removeEventListener("pointermove",move);document.removeEventListener("pointerup",up);paint()};document.addEventListener("pointermove",move);document.addEventListener("pointerup",up);
  };
  paint();
  return { state, launch };
}
