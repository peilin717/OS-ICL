# Vibe OS Simulator — Product and Interaction Design Specification

## 1. Product definition

Vibe OS is a deterministic, English-only desktop operating-system simulator for
human demonstration recording and VLM-agent interaction. It is not a dashboard
of benchmark cases. The default URL opens the operating system itself. Benchmark
administration is a separate surface.

The simulator does not need real filesystem, process, network, Bluetooth, or
terminal backends. It must nevertheless behave consistently: every visible
control changes frontend state, every destructive action has a realistic
confirmation path, and every task can be completed through ordinary desktop
interactions.

Canonical viewport: **1280 × 720, 16:9**.

## 2. Non-negotiable experience rules

| ID | Requirement | Acceptance criterion |
|---|---|---|
| UX-01 | Root URL is the OS | `/` contains no case cards, rule selectors, seeds, evaluator results, or recording controls. |
| UX-02 | Real navigation depth | Core applications provide at least three navigable levels: app → section/folder → item/detail/dialog. |
| UX-03 | Real window model | Windows open, focus, move, resize, minimise, maximise, restore, and close. Z-order is visible. |
| UX-04 | Multiple interaction paths | Common actions are available through toolbar, context menu, keyboard shortcut, or drag-and-drop where appropriate. |
| UX-05 | Stateful operations | Rename, move, delete, toggle, connect, retry, sort, filter, and schedule visibly update state. |
| UX-06 | Frontend-only is acceptable | Operations use a deterministic in-memory store; realism is judged by visible behaviour, not a real OS backend. |
| UX-07 | Agent-safe geometry | Controls do not move unpredictably; menus and dialogs stay within the 1280×720 viewport. |
| UX-08 | One OS for demo and test | Demonstrations and agent queries use the same shell and applications; only initial state and hidden policy differ. |

## 3. Five-level information architecture

| Level | Name | Examples | Stable index format |
|---|---|---|---|
| L0 | System surface | Boot, lock screen, desktop, taskbar, start menu | `surface.desktop` |
| L1 | Application | Files, Settings, Monitor, Terminal | `app.files` |
| L2 | Section / location | Files/Downloads, Settings/System, Monitor/Processes | `app.files.location.downloads` |
| L3 | Entity / detail page | File properties, Wi-Fi network, process detail | `entity.file.report-vib` |
| L4 | Transient interaction | Context menu, modal, picker, toast, permission dialog | `dialog.file.conflict` |

No benchmark task may jump directly from L0 to an answer table. It must operate
through one or more normal OS levels.

## 4. Global shell index

| Index | Surface | Required contents | Required interactions |
|---|---|---|---|
| `surface.boot` | Boot | Logo, spinner, deterministic short transition | Continue to lock screen |
| `surface.lock` | Lock screen | Time, date, wallpaper, connectivity | Click/key to reveal sign-in |
| `surface.signin` | Sign-in | Local profile, password-free demo sign-in | Sign in, return to lock |
| `surface.desktop` | Desktop | Wallpaper, icons, open windows, selection rectangle | Select, double-click, right-click, drag icons |
| `shell.start` | Start menu | Pinned apps, all apps, recent files, search | Search, launch, keyboard navigation |
| `shell.taskbar` | Taskbar | Start, search, running apps, tray, clock | Launch, focus, minimise, preview |
| `shell.quick-settings` | Quick settings | Wi-Fi, Bluetooth, volume, brightness, power | Toggle, slider, open Settings |
| `shell.notifications` | Notification centre | Grouped notifications and calendar | Expand, dismiss, clear, follow action |
| `shell.context.desktop` | Desktop context menu | View, sort, refresh, new, display settings | Nested submenu and action |
| `shell.window` | Window frame | Title, app icon, controls, resize boundaries | Move, resize, minimise, maximise, close |

## 5. Application and route index

### 5.1 Files

| Route index | Screen | Children / secondary views | Operations |
|---|---|---|---|
| `files.home` | Home | Quick access, recent, favourites | Open, pin, sort |
| `files.desktop` | Desktop folder | Files and folders | New, rename, move, delete |
| `files.documents` | Documents | Nested project folders | Breadcrumb navigation |
| `files.downloads` | Downloads | Mixed types and transfer states | Filter, group, retry |
| `files.pictures` | Pictures | Grid/list modes | Preview, rotate, properties |
| `files.projects` | Projects | At least three folder levels | Copy, move, duplicate |
| `files.trash` | Trash | Deleted entities | Restore, empty, delete permanently |
| `files.search` | Search results | Query chips and filters | Search, clear, open location |
| `files.detail.{id}` | Details pane | Metadata, tags, permissions | Star, tag, edit metadata |
| `files.properties.{id}` | Properties dialog | General, details, permissions tabs | Apply, cancel |

Minimum seeded tree:

```text
Home
├── Desktop
├── Documents
│   ├── Reports
│   │   ├── Q1
│   │   └── Q2
│   └── Research
│       ├── Notes
│       └── Datasets
├── Downloads
│   ├── Complete
│   └── In progress
├── Pictures
├── Projects
│   ├── Atlas
│   │   ├── Source
│   │   └── Builds
│   └── Vela
└── Trash
```

### 5.2 Settings

| L1 section | L2 pages | L3 detail examples | Operations |
|---|---|---|---|
| System | Display, Sound, Notifications, Power, Storage | Display scale, output device, battery policy | Toggle, slider, dropdown |
| Bluetooth & devices | Devices, Printers, Mouse, Keyboard | Device detail and pairing state | Pair, connect, disconnect, remove |
| Network | Wi-Fi, Ethernet, VPN, Proxy | Network detail, saved network | Connect, forget, edit |
| Personalisation | Background, Colours, Themes, Taskbar | Theme preview | Select and apply |
| Apps | Installed apps, Defaults, Startup | App detail | Enable, disable, uninstall simulation |
| Accounts | Profile, Sign-in, Backup | Sync status | Toggle and resolve warning |
| Time & language | Date, Region, Language, Typing | Locale detail | Select and apply |
| Accessibility | Vision, Hearing, Interaction | Contrast, captions, keyboard | Toggle and slider |
| Privacy | Permissions, Diagnostics | Per-app permission | Allow, deny, reset |
| Update | Status, History, Advanced | Update package detail | Check, pause, retry, restart simulation |

### 5.3 System Monitor

| Route index | Screen | Data | Operations |
|---|---|---|---|
| `monitor.processes` | Processes | Name, status, CPU, memory, disk, network | Sort, filter, select, end task |
| `monitor.performance` | Performance | CPU, memory, disk, network charts | Select resource, inspect values |
| `monitor.startup` | Startup apps | Impact and enabled state | Enable, disable |
| `monitor.users` | Users | Session and resource totals | Expand, disconnect simulation |
| `monitor.details` | Process details | PID, runtime, priority | Set priority, end process |
| `monitor.services` | Services | Running/stopped state | Start, stop, restart |

### 5.4 Terminal

| Route index | Screen | Required behaviour |
|---|---|---|
| `terminal.session.{id}` | Terminal tab | Prompt, typed input, cursor, history |
| `terminal.tabs` | Tab strip | New, rename, close, switch |
| `terminal.history` | Command history | Search and rerun |
| `terminal.jobs` | Background jobs | Running, completed, failed states |

Supported simulated commands should include `ls`, `cd`, `pwd`, `cat`, `find`,
`status`, `retry`, `clear`, and case-specific fictional commands. Output is
generated from frontend state; no host shell is invoked.

### 5.5 Devices

| Route index | Screen | Child detail | Operations |
|---|---|---|---|
| `devices.overview` | Device overview | Paired and nearby groups | Refresh, filter |
| `devices.bluetooth` | Bluetooth | Device detail | Pair, connect, disconnect, forget |
| `devices.displays` | Displays | Display arrangement | Select, rearrange, set primary |
| `devices.audio` | Audio | Input/output detail | Select, test, volume |
| `devices.printers` | Printers | Queue and printer state | Add, remove, retry job |

### 5.6 Notifications

| Route index | Screen | Operations |
|---|---|---|
| `notifications.inbox` | All notifications | Read, unread, expand, dismiss |
| `notifications.group.{app}` | Per-app group | Clear group, open source app |
| `notifications.settings` | Notification preferences | Enable, mute, priority |

### 5.7 Jobs and Transfers

| App | Main indexes | Operations |
|---|---|---|
| Jobs | Queue, Scheduled, Running, Failed, History | Queue, reprioritise, pause, retry, cancel |
| Transfers | Active, Completed, Failed, Peers | Pause, resume, retry, change destination |

### 5.8 Supporting applications

| App | Purpose | Minimum depth |
|---|---|---|
| Text Editor | Open/edit/save simulated text files | Recent → document → find/replace dialog |
| Image Viewer | Inspect picture assets | Gallery → image → details |
| Calendar | Date and scheduled task context | Month → day → event detail |
| Help | Explain generic OS controls, never hidden task rules | Topic → article |

## 6. Interaction index

| Interaction ID | Input | Visual response | State mutation |
|---|---|---|---|
| `int.click.select` | Single click | Selection highlight | `selection.activeIds` |
| `int.click.open` | Double click / Enter | Open folder, file, app, or detail | Navigation/window state |
| `int.context` | Right click | Anchored context menu | None until command chosen |
| `int.drag.move` | Drag entity to folder | Drag ghost and drop target | Parent/location changes |
| `int.drag.window` | Drag title bar | Window follows pointer | Position changes |
| `int.resize.window` | Drag edge/corner | Live resize | Size changes |
| `int.keyboard.rename` | F2 | Inline editable name | Name changes on commit |
| `int.keyboard.delete` | Delete | Confirmation or move to Trash | Entity status changes |
| `int.keyboard.nav` | Arrows/Tab/Enter/Escape | Focus ring/menu navigation | Focus/open state |
| `int.multiselect` | Ctrl/Shift click | Multiple highlights | Selection set |
| `int.sort` | Header/menu | Sort indicator and reordered rows | View preference |
| `int.filter` | Search/filter field | Result subset and clear button | Query state |
| `int.dialog` | Command requiring confirmation | Modal with primary/secondary actions | Mutation only on confirm |
| `int.toast` | Successful operation | Timed toast with optional Undo | Undo snapshot created |

## 7. Window-management state index

Every window uses the following model:

```json
{
  "windowId": "win-files-1",
  "appId": "files",
  "title": "Downloads",
  "bounds": {"x": 150, "y": 82, "width": 920, "height": 560},
  "restoreBounds": null,
  "mode": "normal",
  "zIndex": 4,
  "focused": true,
  "route": "files.downloads",
  "history": ["files.home", "files.downloads"]
}
```

Supported modes: `normal`, `minimised`, `maximised`, `closed`. At least three
windows can be open simultaneously, overlap, and be switched through the
taskbar.

## 8. Frontend state indexes

| Store | Key entities | Why it exists |
|---|---|---|
| `systemStore` | boot state, clock, locale, theme, connectivity | Global shell |
| `windowStore` | windows, focus, z-order, bounds | Window manager |
| `fileStore` | folders, files, metadata, trash, clipboard | Files and cross-app operations |
| `settingsStore` | toggles, sliders, selected devices, policies | Settings persistence |
| `processStore` | processes, services, resource values | Monitor and terminal linkage |
| `deviceStore` | nearby, paired, connection, battery, signal | Devices and recovery tasks |
| `notificationStore` | groups, unread, priority, dismissed | Notification workflows |
| `jobStore` | queue, schedule, failures, attempts | Jobs and recovery workflows |
| `transferStore` | progress, peer, destination, status | Transfer workflows |
| `uiStore` | selection, menus, dialogs, toasts, drag state | Transient UI |
| `episodeStore` | case, hidden rule, seed, initial snapshot | Benchmark injection only |
| `eventStore` | semantic actions and timestamps | Recording/export |

All stores reset from a deterministic seed. The agent-facing UI never exposes
`episodeStore.hiddenRule`.

## 9. Menu and dialog index

| Index | Trigger | Contents |
|---|---|---|
| `menu.file.entity` | Right-click file | Open, Cut, Copy, Rename, Move, Delete, Properties |
| `menu.file.background` | Right-click folder background | New, Paste, Sort, Group, Refresh |
| `menu.taskbar.app` | Right-click taskbar app | Open new window, Pin, Close all |
| `menu.desktop` | Right-click desktop | View, Sort, Refresh, New, Display settings |
| `dialog.rename` | Rename action | Name input, validation, Save/Cancel |
| `dialog.delete` | Delete protected/permanent item | Consequence copy, Confirm/Cancel |
| `dialog.conflict` | Name collision | Replace, Keep both, Skip |
| `dialog.permission` | Restricted operation | Request access, fallback, cancel |
| `dialog.connect` | Device/network connection | Progress, success/failure, retry |
| `dialog.properties` | Properties action | Tabbed metadata view |
| `dialog.shutdown` | Power menu | Sleep, restart, shut down simulation |

## 10. Benchmark integration rule

Cases are not pages. A case is an initial-state patch plus a goal and hidden
policy injected into the normal OS:

```json
{
  "startRoute": "files.downloads",
  "openWindows": ["files"],
  "statePatch": {"files": [], "notifications": []},
  "visibleTask": "Organise the downloaded files.",
  "hiddenRuleId": "rule-0",
  "successPredicate": {"type": "frontend-state"}
}
```

The task prompt appears as a notification or task strip, not as an answer table.
The user/agent completes it through the same applications and menus available on
the ordinary desktop.

## 11. Recording-mode rule

| Mode | Rule visible? | Studio visible? | OS geometry | Output |
|---|---:|---:|---:|---|
| Authoring | Yes, before start | Yes | Preview 16:9 | None |
| Demonstration operation | No | No | 1280×720 | Semantic events |
| Rendered replay | No | No | 1280×720 | WebM |
| Agent query | No | No | 1280×720 | Event trace + final state |

## 12. Implementation phases and exit gates

| Phase | Scope | Exit gate |
|---|---|---|
| P1 Shell | Desktop, taskbar, start, tray, window manager | Three simultaneous movable windows; minimise/maximise/close work |
| P2 Files | Hierarchical filesystem, menus, dialogs, clipboard, trash | Complete create/rename/copy/move/delete/restore workflow |
| P3 Settings & Devices | Multi-level settings and connection flows | State persists and cross-links between apps |
| P4 Monitor & Terminal | Process tables, services, simulated commands | Actions update shared process/job state |
| P5 Notifications, Jobs, Transfers | Queues, failures, retries, notification centre | Recovery workflows operate end-to-end |
| P6 Benchmark adapter | State injection, task strip, event export | A case launches inside the OS without bespoke task UI |
| P7 Demo recorder | Rule-gated authoring and replay renderer | Demo and query share identical OS geometry |
| P8 QA | Keyboard, focus, overflow, deterministic reset | 36 cases pass visual and state-transition tests |

## 13. Definition of “sufficiently realistic”

The simulator is ready only when a reviewer can spend several minutes using it
without encountering a dead control, and can complete a workflow such as:

1. Open Start and launch Files.
2. Navigate Documents → Reports → Q2.
3. Search and sort files.
4. Rename one file through its context menu.
5. Drag it to another folder and resolve a name conflict.
6. Open Properties and inspect metadata.
7. Open Settings in a second window and change a related policy.
8. Switch windows through the taskbar.
9. Observe a notification and follow it into another application.
10. Undo or verify the resulting state.

If those steps are not possible, the product is still a mockup rather than an
OS interaction simulator.
