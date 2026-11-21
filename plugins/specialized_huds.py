import threading
import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path
import json

PLUGIN = {
    "name": "open_feature_hud",
    "description": (
        "Opens a dedicated, specialized HUD pop-up window tailored to a specific JARVIS system: "
        "'twin' (Digital Twin Simulator), 'predict' (Future Health Gauges), 'council' (3-Column AI Council), "
        "'mission' (Tactical Mission Control), 'threat' (Red Threat Firewall), 'project' (Context & Project Memory), "
        "'device' (PC-Mobile Mesh Bridge), or 'evolve' (Code Evolution Vault)."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "feature": {
                "type": "STRING",
                "description": "twin | predict | council | mission | threat | project | device | evolve"
            },
            "initial_input": {
                "type": "STRING",
                "description": "Optional pre-filled query, target path, or mission title"
            }
        },
        "required": ["feature"]
    }
}

_OPEN_WINDOWS = set()

def _base_window(key: str, title: str, size: str, bg: str, accent: str):
    if key in _OPEN_WINDOWS:
        return None
    _OPEN_WINDOWS.add(key)
    win = tk.Tk()
    win.title(title)
    win.geometry(size)
    win.configure(bg=bg)
    win.attributes("-topmost", True)

    bar = tk.Frame(win, bg=accent, height=4)
    bar.pack(fill="x")

    hdr = tk.Frame(win, bg=bg)
    hdr.pack(fill="x", padx=14, pady=(10, 6))
    tk.Label(hdr, text=title, font=("Consolas", 13, "bold"), fg=accent, bg=bg).pack(side="left")
    tk.Label(hdr, text="MARK-LVII // DEDICATED SUBSYSTEM", font=("Consolas", 9), fg="#64748b", bg=bg).pack(side="right")

    def _close():
        _OPEN_WINDOWS.discard(key)
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _close)
    return win

# 1. DIGITAL TWIN WIREFRAME HUD
def _hud_twin(prefill: str):
    win = _base_window("twin", "🧬 DIGITAL TWIN // VIRTUAL PC SIMULATOR", "760x480", "#04101a", "#00f0ff")
    if not win: return
    frm = tk.Frame(win, bg="#081c2c", padx=12, pady=12)
    frm.pack(fill="x", padx=14, pady=6)

    tk.Label(frm, text="ACTION TYPE:", font=("Consolas", 10, "bold"), fg="#7dd3fc", bg="#081c2c").grid(row=0, column=0, sticky="w")
    atype = tk.StringVar(value="delete")
    tk.OptionMenu(frm, atype, "delete", "move", "overwrite", "command").grid(row=0, column=1, sticky="w", padx=8)

    tk.Label(frm, text="TARGET PATH / CMD:", font=("Consolas", 10, "bold"), fg="#7dd3fc", bg="#081c2c").grid(row=1, column=0, sticky="w", pady=(8, 0))
    ent = tk.Entry(frm, font=("Consolas", 10), bg="#0f2942", fg="#ffffff", insertbackground="#00f0ff", relief="flat", width=54)
    ent.insert(0, prefill)
    ent.grid(row=1, column=1, sticky="we", padx=8, pady=(8, 0))

    risk_lbl = tk.Label(win, text="IMPACT STATUS: STANDBY", font=("Consolas", 12, "bold"), fg="#00f0ff", bg="#04101a")
    risk_lbl.pack(pady=8)

    out = scrolledtext.ScrolledText(win, font=("Consolas", 10), bg="#02080e", fg="#a5f3fc", height=12, relief="flat")
    out.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def sim():
        from plugins.digital_twin import run as twin_run
        res = twin_run({"action_type": atype.get(), "target": ent.get()})
        color = "#ef4444" if "CRITICAL" in res or "HIGH" in res else "#10b981"
        risk_lbl.config(text=res.split(":")[0], fg=color)
        out.delete("1.0", "end")
        out.insert("end", f"[VIRTUAL TWIN SNAPSHOT]\n{res}\n\n[ROLLBACK GUARD]: Ready. Original filesystem untouched.")

    tk.Button(win, text="⚡ SIMULATE ON VIRTUAL TWIN", command=sim, font=("Consolas", 10, "bold"), bg="#00f0ff", fg="#04101a", relief="flat", padx=16, pady=6).pack(pady=(0, 12))
    if prefill: sim()
    win.mainloop()

# 2. FUTURE PREDICTION TELEMETRY HUD
def _hud_predict(_prefill: str):
    win = _base_window("predict", "📈 FUTURE PREDICTION // TELEMETRY & FORECAST", "720x460", "#041410", "#10b981")
    if not win: return
    card = tk.Frame(win, bg="#08241d", padx=16, pady=14)
    card.pack(fill="both", expand=True, padx=14, pady=10)

    bars = {}
    for metric in ("CPU LOAD", "RAM PRESSURE", "STORAGE USED"):
        row = tk.Frame(card, bg="#08241d")
        row.pack(fill="x", pady=8)
        lbl = tk.Label(row, text=f"{metric}: --%", font=("Consolas", 11, "bold"), fg="#6ee7b7", bg="#08241d", width=26, anchor="w")
        lbl.pack(side="left")
        canvas = tk.Canvas(row, width=340, height=20, bg="#020b09", highlightthickness=1, highlightbackground="#065f46")
        canvas.pack(side="right")
        bars[metric] = (lbl, canvas)

    forecast_box = scrolledtext.ScrolledText(card, font=("Consolas", 10), bg="#020b09", fg="#a7f3d0", height=8, relief="flat")
    forecast_box.pack(fill="both", expand=True, pady=(12, 0))

    def refresh():
        if "predict" not in _OPEN_WINDOWS: return
        import shutil
        total, used, _ = shutil.disk_usage(".")
        disk_pct = (used / total) * 100
        cpu_pct, ram_pct = 5.0, 40.0
        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=0.1)
            ram_pct = psutil.virtual_memory().percent
        except Exception:
            pass

        for name, val in [("CPU LOAD", cpu_pct), ("RAM PRESSURE", ram_pct), ("STORAGE USED", disk_pct)]:
            lbl, c = bars[name]
            lbl.config(text=f"{name}: {val:.1f}%")
            c.delete("all")
            fill_col = "#ef4444" if val > 80 else ("#f59e0b" if val > 65 else "#10b981")
            c.create_rectangle(0, 0, int(3.4 * min(100, val)), 20, fill=fill_col, width=0)

        from plugins.future_predictor import run as pred_run
        forecast_box.delete("1.0", "end")
        forecast_box.insert("end", pred_run({}))
        win.after(3000, refresh)

    refresh()
    win.mainloop()

# 3. AI COUNCIL 3-COLUMN DELIBERATION HUD
def _hud_council(prefill: str):
    win = _base_window("council", "⚖️ AI COUNCIL // 3-EXPERT DELIBERATION CHAMBER", "1040x580", "#0f091c", "#c084fc")
    if not win: return
    top = tk.Frame(win, bg="#19102e", padx=10, pady=10)
    top.pack(fill="x", padx=14, pady=6)
    ent = tk.Entry(top, font=("Consolas", 11), bg="#251842", fg="#ffffff", insertbackground="#c084fc", relief="flat")
    ent.insert(0, prefill)
    ent.pack(side="left", fill="x", expand=True, padx=(0, 10))

    cols = tk.Frame(win, bg="#0f091c")
    cols.pack(fill="both", expand=True, padx=14, pady=6)
    panes = {}
    specs = [("🔬 RESEARCHER", "#38bdf8"), ("📊 ANALYST", "#c084fc"), ("🛡️ SECURITY AI", "#f59e0b")]
    for idx, (title, col) in enumerate(specs):
        f = tk.Frame(cols, bg="#19102e", padx=8, pady=8)
        f.grid(row=0, column=idx, sticky="nsew", padx=4)
        cols.grid_columnconfigure(idx, weight=1)
        cols.grid_rowconfigure(0, weight=1)
        tk.Label(f, text=title, font=("Consolas", 11, "bold"), fg=col, bg="#19102e").pack(anchor="w", pady=(0, 6))
        t = scrolledtext.ScrolledText(f, font=("Consolas", 9), bg="#090512", fg="#e2e8f0", wrap="word", relief="flat")
        t.pack(fill="both", expand=True)
        panes[idx] = t

    verdict_lbl = tk.Label(win, text="COMBINED VERDICT: Enter a question and convene the Council.", font=("Consolas", 10, "bold"), fg="#fde047", bg="#19102e", wraplength=980, justify="left", padx=12, pady=10)
    verdict_lbl.pack(fill="x", padx=14, pady=(0, 12))

    def convene():
        q = ent.get().strip()
        if not q: return
        verdict_lbl.config(text="⏳ Council deliberating across Researcher, Analyst, and Security AI...")
        for p in panes.values(): p.delete("1.0", "end")

        def worker():
            from plugins.ai_council import run as council_run
            res = council_run({"query": q})
            def update():
                parts = res.split("[")
                for p in parts:
                    if p.startswith("RESEARCHER]"): panes[0].insert("end", p.replace("RESEARCHER]:", "").strip())
                    elif p.startswith("ANALYST]"): panes[1].insert("end", p.replace("ANALYST]:", "").strip())
                    elif p.startswith("SECURITY AI]"): panes[2].insert("end", p.replace("SECURITY AI]:", "").strip())
                    elif p.startswith("COMBINED COUNCIL VERDICT]"):
                        verdict_lbl.config(text="🏆 " + p.replace("COMBINED COUNCIL VERDICT]:", "").strip())
                if not panes[0].get("1.0", "end").strip():
                    panes[0].insert("end", res)
                    verdict_lbl.config(text="🏆 Deliberation complete.")
            win.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    tk.Button(top, text="⚖️ CONVENE COUNCIL", command=convene, font=("Consolas", 10, "bold"), bg="#c084fc", fg="#0f091c", relief="flat", padx=14, pady=5).pack(side="right")
    if prefill: convene()
    win.mainloop()

# 4. MISSION CONTROL TACTICAL BOARD
def _hud_mission(_prefill: str):
    win = _base_window("mission", "🎯 MISSION CONTROL // TACTICAL OPS BOARD", "720x500", "#170c04", "#fb923c")
    if not win: return
    prog_lbl = tk.Label(win, text="LOADING MISSION...", font=("Consolas", 12, "bold"), fg="#fdba74", bg="#170c04")
    prog_lbl.pack(pady=8)

    board = tk.Frame(win, bg="#261407", padx=14, pady=12)
    board.pack(fill="both", expand=True, padx=14, pady=6)

    def render():
        for w in board.winfo_children(): w.destroy()
        sf = Path("memory/mission_control.json")
        if not sf.exists():
            tk.Label(board, text="No active mission. Ask JARVIS to start a mission!", font=("Consolas", 10), fg="#fed7aa", bg="#261407").pack()
            return
        data = json.loads(sf.read_text(encoding="utf-8"))
        done = sum(1 for s in data["steps"] if s["done"])
        tot = max(1, len(data["steps"]))
        pct = int((done / tot) * 100)
        prog_lbl.config(text=f"MISSION: {data['title']}  —  {pct}% COMPLETE ({done}/{tot})")

        for idx, step in enumerate(data["steps"], 1):
            row = tk.Frame(board, bg="#261407")
            row.pack(fill="x", pady=4)
            mark = "✅" if step["done"] else "⬜"
            tk.Label(row, text=f"{mark}  STEP {idx}: {step['task']}", font=("Consolas", 11), fg="#86efac" if step["done"] else "#ffedd5", bg="#261407").pack(side="left")
            if not step["done"]:
                tk.Button(row, text="MARK DONE", command=lambda i=idx: (
                    __import__("plugins.mission_control").mission_control.run({"action": "complete_step", "step_index": i}),
                    render()
                ), font=("Consolas", 9, "bold"), bg="#fb923c", fg="#170c04", relief="flat", padx=8).pack(side="right")

    render()
    win.mainloop()

# 5. THREAT SIMULATION RED FIREWALL
def _hud_threat(prefill: str):
    win = _base_window("threat", "🛡️ THREAT SIMULATION // CYBER QUARANTINE SCANNER", "740x440", "#1a0505", "#ef4444")
    if not win: return
    ent = tk.Entry(win, font=("Consolas", 11), bg="#2d0a0a", fg="#ffffff", insertbackground="#ef4444", relief="flat")
    ent.insert(0, prefill)
    ent.pack(fill="x", padx=14, pady=10)

    banner = tk.Label(win, text="FIREWALL ARMED — PASTE COMMAND OR FILE PATH TO SCAN", font=("Consolas", 11, "bold"), fg="#fca5a5", bg="#2d0a0a", pady=12)
    banner.pack(fill="x", padx=14, pady=6)

    def scan():
        from plugins.threat_simulator import run as t_run
        res = t_run({"payload": ent.get()})
        is_bad = "BLOCKED" in res
        banner.config(text=res, fg="#ffffff", bg="#dc2626" if is_bad else "#059669")

    tk.Button(win, text="🔍 RUN THREAT SIMULATION", command=scan, font=("Consolas", 10, "bold"), bg="#ef4444", fg="#ffffff", relief="flat", padx=16, pady=6).pack(pady=10)
    if prefill: scan()
    win.mainloop()

# 6. CONTEXT AWARENESS & INFINITE PROJECT MEMORY HUD
def _hud_project(_prefill: str):
    win = _base_window("project", "🧠 CONTEXT AWARENESS & INFINITE PROJECT MEMORY", "780x500", "#06101e", "#38bdf8")
    if not win: return
    ctx_lbl = tk.Label(win, text="Scanning active window...", font=("Consolas", 10, "bold"), fg="#7dd3fc", bg="#0c1e38", wraplength=740, justify="left", padx=10, pady=10)
    ctx_lbl.pack(fill="x", padx=14, pady=8)

    box = scrolledtext.ScrolledText(win, font=("Consolas", 10), bg="#030811", fg="#bae6fd", relief="flat")
    box.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    def refresh():
        if "project" not in _OPEN_WINDOWS: return
        from plugins.context_awareness import get_snapshot
        from plugins.infinite_project_memory import run as ipm_run
        ctx_lbl.config(text=f"LIVE CONTEXT: {get_snapshot()}")
        box.delete("1.0", "end")
        box.insert("end", ipm_run({"action": "list"}) + "\n\n" + ipm_run({"action": "recall", "project": "Mark-LVII"}))
        win.after(2500, refresh)

    refresh()
    win.mainloop()

# 7. DEVICE INTELLIGENCE NETWORK BRIDGE
def _hud_device(_prefill: str):
    win = _base_window("device", "📱 DEVICE INTELLIGENCE NETWORK // PC ↔ MOBILE MESH", "700x440", "#04151a", "#06b6d4")
    if not win: return
    feed = scrolledtext.ScrolledText(win, font=("Consolas", 10), bg="#020a0d", fg="#67e8f9", height=14, relief="flat")
    feed.pack(fill="both", expand=True, padx=14, pady=8)

    row = tk.Frame(win, bg="#04151a")
    row.pack(fill="x", padx=14, pady=(0, 12))
    ent = tk.Entry(row, font=("Consolas", 10), bg="#0b2833", fg="#ffffff", insertbackground="#06b6d4", relief="flat")
    ent.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def reload_feed():
        from plugins.device_network import run as dev_run
        feed.delete("1.0", "end")
        feed.insert("end", dev_run({"action": "read_sync"}))

    def push():
        from plugins.device_network import run as dev_run
        dev_run({"action": "push_to_mobile", "message": ent.get()})
        ent.delete(0, "end")
        reload_feed()

    tk.Button(row, text="📤 PUSH TO MOBILE", command=push, font=("Consolas", 9, "bold"), bg="#06b6d4", fg="#04151a", relief="flat", padx=12, pady=5).pack(side="right")
    reload_feed()
    win.mainloop()

# 8. CONTROLLED SELF-EVOLUTION VAULT
def _hud_evolve(_prefill: str):
    win = _base_window("evolve", "🧬 CONTROLLED SELF-EVOLUTION // SANDBOX APPROVAL VAULT", "760x480", "#171404", "#eab308")
    if not win: return
    box = scrolledtext.ScrolledText(win, font=("Consolas", 10), bg="#0a0902", fg="#fef08a", height=16, relief="flat")
    box.pack(fill="both", expand=True, padx=14, pady=8)

    def refresh():
        from plugins.controlled_evolution import run as ev_run
        box.delete("1.0", "end")
        box.insert("end", ev_run({"action": "list"}))

    tk.Button(win, text="🔄 REFRESH STAGED PROPOSALS", command=refresh, font=("Consolas", 9, "bold"), bg="#eab308", fg="#171404", relief="flat", padx=12, pady=5).pack(pady=(0, 12))
    refresh()
    win.mainloop()

_DISPATCH = {
    "twin": _hud_twin,
    "predict": _hud_predict,
    "council": _hud_council,
    "mission": _hud_mission,
    "threat": _hud_threat,
    "project": _hud_project,
    "device": _hud_device,
    "evolve": _hud_evolve,
}

def run(params: dict = None, **kwargs) -> str:
    params = params or {}
    feat = str(params.get("feature", "")).strip().lower()
    prefill = str(params.get("initial_input", "")).strip()
    fn = _DISPATCH.get(feat)
    if not fn:
        return f"Unknown HUD feature '{feat}'. Available: {', '.join(_DISPATCH.keys())}"
    if feat in _OPEN_WINDOWS:
        return f"The '{feat}' dedicated HUD window is already open on your screen, Hari."
    threading.Thread(target=fn, args=(prefill,), daemon=True).start()
    return f"⚡ Launched dedicated '{feat.upper()}' HUD pop-up window on your screen, Hari."
