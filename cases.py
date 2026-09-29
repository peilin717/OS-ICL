"""Case catalogue and deterministic episode generator for Vibe OS-ICL.

The browser never receives the descriptions in RULES for evaluation sessions.
They are exposed only to an authorised human while preparing a demonstration.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    app: str
    family: str
    difficulty: str
    task: str
    rules: tuple[str, str, str]

    def public(self) -> dict:
        data = asdict(self)
        data.pop("rules")
        return data


CASES = [
    Case("OS-SEL-01", "File attribute selection", "Files", "selection", "L1", "Mark the correct item.", ("Mark the largest file.", "Mark the oldest file.", "Mark the item with the shortest name.")),
    Case("OS-SEL-02", "Compound file filtering", "Files", "selection_set", "L2", "Select every matching item, then submit.", ("Select blue items with an even value.", "Select starred items with a value above 30.", "Select triangle items modified today.")),
    Case("OS-SEL-03", "Process target selection", "Monitor", "selection", "L1", "Select the correct process.", ("Select the process with the highest CPU.", "Select the process with the highest memory.", "Select the longest-running process.")),
    Case("OS-SEL-04", "Conditional process selection", "Monitor", "selection", "L3", "Select the correct process.", ("If a paused process exists, select its highest-memory member; otherwise highest CPU.", "If a warning process exists, select its lowest-CPU member; otherwise lowest memory.", "If a background process exists, select its longest-running member; otherwise lowest PID.")),
    Case("OS-SEL-05", "Device selection", "Devices", "selection", "L2", "Open the correct device.", ("Open the strongest unpaired device.", "Open the lowest-battery paired device.", "Open the most recent device whose name has no digit.")),
    Case("OS-SEL-06", "Notification filtering", "Notifications", "selection_set", "L2", "Select every matching notification, then submit.", ("Select circle notifications with even values.", "Select unread notifications with odd values.", "Select triangle notifications whose names are short.")),

    Case("OS-MAP-01", "File colour action mapping", "Files", "mapping", "L2", "Apply the learned action to each item.", ("Blue→Copy, Amber→Move, Violet→Star.", "Blue→Star, Amber→Copy, Violet→Move.", "Blue→Move, Amber→Star, Violet→Copy.")),
    Case("OS-MAP-02", "Notification icon action mapping", "Notifications", "mapping", "L2", "Apply the learned action to each notification.", ("Circle→Pin, Triangle→Mute, Square→Clear.", "Circle→Clear, Triangle→Pin, Square→Mute.", "Circle→Mute, Triangle→Clear, Square→Pin.")),
    Case("OS-MAP-03", "File type destination mapping", "Files", "mapping", "L2", "Route each item using the learned mapping.", ("VIB→Dax, NOX→Kiv, LUM→Wug.", "VIB→Kiv, NOX→Wug, LUM→Dax.", "VIB→Wug, NOX→Dax, LUM→Kiv.")),
    Case("OS-MAP-04", "Process state action mapping", "Monitor", "mapping", "L3", "Apply the learned control to each process.", ("Running→Pause, Paused→Resume, Warning→Mark.", "Running→Mark, Paused→Stop, Warning→Resume.", "Running→Stop, Paused→Mark, Warning→Pause.")),
    Case("OS-MAP-05", "Mode switch mapping", "Settings", "mapping", "L1", "Set the two switches for every mode card.", ("Triangle→Alpha, Circle→Beta, Square→Gamma.", "Triangle→Beta, Circle→Gamma, Square→Alpha.", "Triangle→Gamma, Circle→Alpha, Square→Beta.")),
    Case("OS-MAP-06", "Command-result action mapping", "Terminal", "mapping", "L3", "Apply the learned action to each result.", ("K→Save, M→Copy, R→Mark.", "K→Copy, M→Mark, R→Save.", "K→Mark, M→Save, R→Copy.")),

    Case("OS-ORD-01", "File processing priority", "Files", "ordering", "L2", "Process all items in the learned order.", ("Ascending value.", "Oldest to newest.", "Longest name to shortest.")),
    Case("OS-ORD-02", "Notification type priority", "Notifications", "ordering", "L2", "Acknowledge all notifications in the learned order.", ("Triangle, then Circle, then Square.", "Square, then Triangle, then Circle.", "Circle, then Square, then Triangle.")),
    Case("OS-ORD-03", "Window organisation order", "Desktop", "ordering", "L2", "Minimise all windows in the learned order.", ("Front to back.", "Shortest title to longest.", "Oldest activity to newest.")),
    Case("OS-ORD-04", "Two-stage file organisation", "Files", "ordering", "L3", "Process all items in the learned two-stage order.", ("Even values before odd values.", "Digit names before non-digit names.", "Starred items before unstarred items.")),
    Case("OS-ORD-05", "Settings page route", "Settings", "ordering", "L3", "Visit every page in the learned order.", ("Triangle, Circle, Square.", "Square, Circle, Triangle.", "Circle, Triangle, Square.")),
    Case("OS-ORD-06", "Terminal job schedule", "Terminal", "ordering", "L3", "Run all jobs in the learned order.", ("Ascending value.", "Descending value.", "Shortest name to longest.")),

    Case("OS-SM-01", "Command return-code branch", "Terminal", "state_machine", "L2", "Handle each result using the learned policy.", ("OK→Continue, Error→Open log, Warning→Pause.", "OK→Save, Error→Retry, Warning→Continue.", "OK→Mark, Error→Skip, Warning→Save.")),
    Case("OS-SM-02", "Warning state machine", "Terminal", "state_machine", "L3", "Handle each result using the learned policy.", ("OK→Continue, Warn→Pause, Error→Open log.", "OK→Save, Warn→Continue, Error→Retry.", "OK→Mark, Warn→Save, Error→Skip.")),
    Case("OS-SM-03", "Transfer state machine", "Transfers", "state_machine", "L3", "Handle each transfer using the learned policy.", ("Slow→Pause, Failed→Delete, Ready→Continue.", "Slow→Continue, Failed→Retry, Ready→Save.", "Slow→Lower, Failed→Mark, Ready→Continue.")),
    Case("OS-SM-04", "Battery-network policy", "Settings", "state_machine", "L3", "Apply the learned action to each system state.", ("Low-offline→Enable, otherwise Disable.", "Low or weak→Enable, otherwise Disable.", "Charging→Enable, otherwise Disable.")),
    Case("OS-SM-05", "Window modal state machine", "Desktop", "state_machine", "L3", "Resolve each window state using the learned policy.", ("Modal→Close, Normal→Maximise, Alert→Confirm.", "Modal→Move, Normal→Minimise, Alert→Close.", "Modal→Confirm, Normal→Pin, Alert→Confirm.")),
    Case("OS-SM-06", "Queue processing state machine", "Jobs", "state_machine", "L4", "Handle every queue result using the learned policy.", ("OK→Continue, Error→Stop, Warning→Pause.", "OK→Skip, Error→Retry, Warning→Continue.", "OK→Continue, Error→Mark, Warning→Retry.")),

    Case("OS-REC-01", "Name-conflict recovery", "Files", "recovery", "L2", "Resolve each conflict using the learned policy.", ("Overwrite conflicts.", "Rename conflicts with a numeric suffix.", "Skip conflicts and continue.")),
    Case("OS-REC-02", "Locked-file recovery", "Files", "recovery", "L3", "Resolve each locked item using the learned policy.", ("Pause owner and retry.", "Skip locked items.", "Create and process a copy.")),
    Case("OS-REC-03", "Device connection recovery", "Devices", "recovery", "L2", "Recover from each failed connection.", ("Refresh and retry.", "Select the fallback device.", "Toggle pairing and retry.")),
    Case("OS-REC-04", "Missing dependency recovery", "Terminal", "recovery", "L3", "Recover from each dependency error.", ("Enable dependency and retry.", "Run the fallback command.", "Record failure and continue.")),
    Case("OS-REC-05", "Permission-denied recovery", "Files", "recovery", "L3", "Resolve each permission error.", ("Grant temporary access and retry.", "Move to the fallback destination.", "Create a reference and keep the original.")),
    Case("OS-REC-06", "Partial batch failure", "Jobs", "recovery", "L4", "Resolve every failed batch item.", ("Move failure to end and retry once.", "Mark failure and continue.", "Switch mode and rerun remaining items.")),

    Case("OS-XAPP-01", "Log to file manager", "Terminal + Files", "cross_app", "L3", "Use the source panel to identify and process the target.", ("Use the final K target and Star it.", "Use the first M target and Move it.", "Use the repeated target and Copy it.")),
    Case("OS-XAPP-02", "Notification to device settings", "Notifications + Devices", "cross_app", "L3", "Use the source panel to identify and process the target.", ("Use the Circle code and Connect it.", "Use the newest unread code and Mark it.", "Use the repeated code and Disconnect it.")),
    Case("OS-XAPP-03", "Process to file", "Monitor + Files", "cross_app", "L3", "Use the source panel to identify and process the target.", ("Use the highest-CPU code and Delete its item.", "Use the lowest-memory code and Move its item.", "Use the longest-running code and Star its item.")),
    Case("OS-XAPP-04", "Settings to terminal parameters", "Settings + Terminal", "cross_app", "L3", "Use the source panel to choose the correct encoded target.", ("Encode switches as 1/0 in X-Y-Z order.", "Encode switches as on/off in Z-X-Y order.", "Use enabled codes in reverse order.")),
    Case("OS-XAPP-05", "Files to job scheduler", "Files + Jobs", "cross_app", "L4", "Use the source panel to identify and process the target.", ("Use the VIB target and Queue it.", "Use the digit-name target and Schedule it.", "Use the starred target and Prioritise it.")),
    Case("OS-XAPP-06", "Multi-app conditional workflow", "Notifications + Monitor + Files", "cross_app", "L4", "Use the source panels to identify and process the target.", ("High CPU→Move, otherwise Star.", "Paused→Copy, otherwise Move.", "Even runtime→Star, otherwise Copy.")),
]

CASE_BY_ID = {case.id: case for case in CASES}

NAMES = ["A", "Bex", "Cyra", "Doran", "Elowen", "Finchly"]
SYMBOLS = ["Triangle", "Circle", "Square"]
COLORS = ["Blue", "Amber", "Violet"]
STATUSES = ["OK", "Warning", "Error"]


def _items(rng: random.Random, count: int = 6) -> list[dict]:
    # Attribute extrema deliberately belong to different stable object IDs. The
    # row order is randomised later, so position remains non-predictive while
    # the three counterfactual rules keep distinct answers for the same query.
    names = NAMES[:count]
    values = [34, 96, 61, 22, 75, 48][:count]
    cpu = [94, 41, 12, 68, 30, 55][:count]
    memory = [260, 940, 510, 180, 720, 390][:count]
    runtime = [31, 57, 166, 82, 14, 109][:count]
    items = []
    for i, name in enumerate(names):
        items.append({
            "id": f"item-{i+1}", "name": name + (str(i + 2) if i == 1 else ""),
            "value": values[i], "size": values[i], "age": i + 1,
            "cpu": cpu[i], "memory": memory[i], "runtime": runtime[i], "pid": 410 + i * 7,
            "symbol": SYMBOLS[i % 3], "color": COLORS[i % 3],
            "code": ["K", "M", "R"][i % 3],
            "status": ["Running", "Paused", "Warning", "Background", "Running", "Paused"][i],
            "signal": [35, 97, 60, 74, 48, 81][i], "battery": [88, 76, 9, 63, 41, 55][i],
            "paired": i % 2 == 0, "starred": i % 3 == 0, "today": i % 2 == 1,
            "unread": i % 2 == 0, "extension": ["VIB", "NOX", "LUM"][i % 3],
        })
    rng.shuffle(items)
    return items


def _metric_pick(items: list[dict], key: str, maximum: bool = True) -> dict:
    return (max if maximum else min)(items, key=lambda x: x[key])


def _selection_expected(case: Case, rule: int, items: list[dict]) -> list[dict]:
    if case.id == "OS-SEL-01":
        target = [_metric_pick(items, "size", True), _metric_pick(items, "age", True), min(items, key=lambda x: len(x["name"]))][rule]
    elif case.id == "OS-SEL-03":
        target = [_metric_pick(items, "cpu", True), _metric_pick(items, "memory", True), _metric_pick(items, "runtime", True)][rule]
    elif case.id == "OS-SEL-04":
        if rule == 0:
            pool = [x for x in items if x["status"] == "Paused"]
            target = _metric_pick(pool, "memory", True) if pool else _metric_pick(items, "cpu", True)
        elif rule == 1:
            pool = [x for x in items if x["status"] == "Warning"]
            target = _metric_pick(pool, "cpu", False) if pool else _metric_pick(items, "memory", False)
        else:
            pool = [x for x in items if x["status"] == "Background"]
            target = _metric_pick(pool, "runtime", True) if pool else _metric_pick(items, "pid", False)
    elif case.id == "OS-SEL-05":
        if rule == 0:
            target = _metric_pick([x for x in items if not x["paired"]], "signal", True)
        elif rule == 1:
            target = _metric_pick([x for x in items if x["paired"]], "battery", False)
        else:
            target = min([x for x in items if not any(c.isdigit() for c in x["name"])], key=lambda x: x["age"])
    else:
        target = items[rule]
    return [{"verb": "select", "target": target["id"]}]


def _selection_set_expected(case: Case, rule: int, items: list[dict]) -> list[dict]:
    predicates = [
        lambda x: x["color"] == "Blue" and x["value"] % 2 == 0,
        lambda x: x["starred"] and x["value"] > 30,
        lambda x: x["symbol"] == "Triangle" and x["today"],
    ] if case.id == "OS-SEL-02" else [
        lambda x: x["symbol"] == "Circle" and x["value"] % 2 == 0,
        lambda x: x["unread"] and x["value"] % 2 == 1,
        lambda x: x["symbol"] == "Triangle" and len(x["name"]) <= 6,
    ]
    chosen = [x for x in items if predicates[rule](x)]
    if not chosen:
        chosen = [items[rule]]
    return [{"verb": "toggle", "target": x["id"]} for x in sorted(chosen, key=lambda x: x["id"])] + [{"verb": "submit", "target": "workspace"}]


def _mapping_expected(case: Case, rule: int, items: list[dict]) -> list[dict]:
    if case.id in {"OS-MAP-01"}:
        field, categories, actions = "color", COLORS, ["copy", "move", "star"]
    elif case.id in {"OS-MAP-02"}:
        field, categories, actions = "symbol", SYMBOLS, ["pin", "mute", "clear"]
    elif case.id in {"OS-MAP-03"}:
        field, categories, actions = "extension", ["VIB", "NOX", "LUM"], ["dax", "kiv", "wug"]
    elif case.id == "OS-MAP-04":
        field, categories = "status", ["Running", "Paused", "Warning"]
        actions = ["pause", "resume", "mark"] if rule == 0 else (["mark", "stop", "resume"] if rule == 1 else ["stop", "mark", "pause"])
        rule = 0
    elif case.id == "OS-MAP-05":
        field, categories, actions = "symbol", SYMBOLS, ["alpha", "beta", "gamma"]
    else:
        field, categories, actions = "code", ["K", "M", "R"], ["save", "copy", "mark"]
    perm = actions[rule:] + actions[:rule]
    table = dict(zip(categories, perm))
    sample = []
    seen = set()
    for item in items:
        key = item[field]
        if key in table and key not in seen:
            sample.append(item); seen.add(key)
    return [{"verb": table[x[field]], "target": x["id"]} for x in sample]


def _ordering_expected(case: Case, rule: int, items: list[dict]) -> list[dict]:
    if case.id == "OS-ORD-01":
        ordered = [sorted(items, key=lambda x: x["value"]), sorted(items, key=lambda x: -x["age"]), sorted(items, key=lambda x: (-len(x["name"]), x["name"]))][rule]
    elif case.id in {"OS-ORD-02", "OS-ORD-05"}:
        priorities = [["Triangle", "Circle", "Square"], ["Square", "Triangle", "Circle"], ["Circle", "Square", "Triangle"]][rule]
        ordered = sorted(items, key=lambda x: (priorities.index(x["symbol"]), x["id"]))
    elif case.id == "OS-ORD-03":
        ordered = [items, sorted(items, key=lambda x: (len(x["name"]), x["name"])), sorted(items, key=lambda x: -x["age"])][rule]
    elif case.id == "OS-ORD-04":
        keys = [lambda x: (x["value"] % 2, x["id"]), lambda x: (not any(c.isdigit() for c in x["name"]), x["id"]), lambda x: (not x["starred"], x["id"])]
        ordered = sorted(items, key=keys[rule])
    else:
        ordered = [sorted(items, key=lambda x: x["value"]), sorted(items, key=lambda x: -x["value"]), sorted(items, key=lambda x: (len(x["name"]), x["name"]))][rule]
    verb = {"OS-ORD-01": "archive", "OS-ORD-02": "ack", "OS-ORD-03": "minimise", "OS-ORD-04": "process", "OS-ORD-05": "visit", "OS-ORD-06": "run"}[case.id]
    return [{"verb": verb, "target": x["id"]} for x in ordered]


def _state_expected(case: Case, rule: int, items: list[dict]) -> list[dict]:
    if case.id == "OS-SM-03":
        categories, tables = ["Ready", "Slow", "Failed"], [
            {"Ready": "continue", "Slow": "pause", "Failed": "delete"},
            {"Ready": "save", "Slow": "continue", "Failed": "retry"},
            {"Ready": "continue", "Slow": "lower", "Failed": "mark"},
        ]
    elif case.id == "OS-SM-04":
        categories, tables = STATUSES, [
            {"OK": "disable", "Warning": "enable", "Error": "disable"},
            {"OK": "disable", "Warning": "enable", "Error": "enable"},
            {"OK": "enable", "Warning": "disable", "Error": "disable"},
        ]
    elif case.id == "OS-SM-05":
        categories, tables = ["Normal", "Modal", "Alert"], [
            {"Normal": "maximise", "Modal": "close", "Alert": "confirm"},
            {"Normal": "minimise", "Modal": "move", "Alert": "close"},
            {"Normal": "pin", "Modal": "confirm", "Alert": "confirm"},
        ]
    else:
        categories, tables = STATUSES, [
            {"OK": "continue", "Warning": "pause", "Error": "open-log" if case.id != "OS-SM-06" else "stop"},
            {"OK": "save" if case.id != "OS-SM-06" else "skip", "Warning": "continue", "Error": "retry"},
            {"OK": "mark" if case.id != "OS-SM-06" else "continue", "Warning": "save" if case.id != "OS-SM-06" else "retry", "Error": "skip" if case.id != "OS-SM-06" else "mark"},
        ]
    for i, item in enumerate(items):
        item["scenario"] = categories[i % 3]
    return [{"verb": tables[rule][x["scenario"]], "target": x["id"]} for x in items]


def _recovery_expected(case: Case, rule: int, items: list[dict]) -> list[dict]:
    strategies = {
        "OS-REC-01": ["overwrite", "rename", "skip"],
        "OS-REC-02": ["pause-retry", "skip", "copy"],
        "OS-REC-03": ["refresh-retry", "fallback", "pair-retry"],
        "OS-REC-04": ["enable-retry", "fallback", "record-continue"],
        "OS-REC-05": ["grant-retry", "fallback", "reference"],
        "OS-REC-06": ["defer-retry", "mark-continue", "switch-rerun"],
    }
    return [{"verb": strategies[case.id][rule], "target": x["id"]} for x in items[:3]]


def _cross_expected(case: Case, rule: int, items: list[dict]) -> tuple[list[dict], list[str]]:
    targets = sorted(items[:3], key=lambda x: x["id"])
    target = targets[rule]
    actions = {
        "OS-XAPP-01": ["star", "move", "copy"],
        "OS-XAPP-02": ["connect", "mark", "disconnect"],
        "OS-XAPP-03": ["delete", "move", "star"],
        "OS-XAPP-04": ["encode-a", "encode-b", "encode-c"],
        "OS-XAPP-05": ["queue", "schedule", "prioritise"],
        "OS-XAPP-06": ["move", "copy", "star"],
    }[case.id]
    clues = [f"K: {targets[0]['name']}", f"M: {targets[1]['name']}", f"R: {targets[2]['name']}", f"K: {targets[2]['name']}"]
    return [{"verb": actions[rule], "target": target["id"]}], clues


def generate_episode(case_id: str, rule: int, seed: int) -> dict:
    case = CASE_BY_ID[case_id]
    # Rule is intentionally excluded: all three contexts must operate on the
    # exact same query state for context-intervention evaluation.
    rng = random.Random(f"{case_id}:{seed}")
    items = _items(rng, 6)
    if case_id == "OS-MAP-03":
        for item in items: item["display_type"] = item["extension"]
    elif case_id == "OS-MAP-04":
        for item in items: item["display_type"] = item["status"]
    elif case_id == "OS-MAP-06":
        for item in items: item["display_type"] = item["code"]
    else:
        for item in items: item["display_type"] = item["symbol"]
    clues: list[str] = []
    if case.family == "selection":
        expected = _selection_expected(case, rule, items)
    elif case.family == "selection_set":
        expected = _selection_set_expected(case, rule, items)
    elif case.family == "mapping":
        expected = _mapping_expected(case, rule, items)
    elif case.family == "ordering":
        expected = _ordering_expected(case, rule, items)
    elif case.family == "state_machine":
        expected = _state_expected(case, rule, items)
    elif case.family == "recovery":
        expected = _recovery_expected(case, rule, items)
    else:
        expected, clues = _cross_expected(case, rule, items)
    return {
        "case": case.public(), "seed": seed, "items": items, "clues": clues,
        "expected": expected, "rule": rule, "rule_text": case.rules[rule],
    }


def available_actions(case_id: str) -> list[str]:
    case = CASE_BY_ID[case_id]
    if case.family in {"selection", "selection_set"}: return ["select", "toggle", "submit"]
    if case.family == "ordering": return [x["verb"] for x in generate_episode(case_id, 0, 1)["expected"][:1]]
    if case.family == "mapping":
        return sorted({x["verb"] for r in range(3) for x in generate_episode(case_id, r, 1)["expected"]})
    if case.family == "state_machine":
        return sorted({x["verb"] for r in range(3) for x in generate_episode(case_id, r, 1)["expected"]})
    if case.family == "recovery":
        return sorted({x["verb"] for r in range(3) for x in generate_episode(case_id, r, 1)["expected"]})
    return sorted({x["verb"] for r in range(3) for x in generate_episode(case_id, r, 1)["expected"]})
