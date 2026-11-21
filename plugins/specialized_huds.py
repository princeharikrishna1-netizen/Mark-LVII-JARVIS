import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path
import json

PLUGIN = {
    "name": "open_feature_hud",
    "description": (
        "Opens a dedicated, specialized holographic HUD pop-up window tailored to a specific JARVIS system: "
        "'twin' (Digital Twin Simulator), 'predict' (Future Health Gauges + Live Sparkline), 'council' (3-Column AI Council), "
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

def _style_dark_scrollbars(win: tk.Tk, bg: str, accent: str):
    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        "Jarvis.Vertical.TScrollbar",
        gripcount=0,
        background=accent,
        darkcolor=bg,
        lightcolor=bg,
        troughcolor=bg,
        bordercolor=bg,
        arrowcolor=bg,
        width=8,
    )

def _dark_textbox(parent, bg: str, fg: str, accent: str, height: int = 10, font=("Consolas", 10)):
    wrap = tk.Frame(parent, bg=bg, highlightbackground=accent, highlightthickness=1)
    txt = tk.Text(
        wrap, font=font, bg=bg, fg=fg, insertbackground=accent,
        relief="flat", height=height, wrap="word", padx=10, pady=8, bd=0
    )
    sb = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview, style="Jarvis.Vertical.TScrollbar")
    txt.configure(yscrollcommand=sb.set)
    txt.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return wrap, txt

def _base_window(key: str, title: str, size: str, bg: str, accent: str):
    if key in _OPEN_WINDOWS:
        return None
    _OPEN_WINDOWS.add(key)
    win = tk.Tk()
    win.title(title)
    win.geometry(size)
    win.configure(bg=bg)
    win.attributes("-topmost", True)
    _style_dark_scrollbars(win, bg, accent)

    outer = tk.Frame(win, bg=bg, highlightbackground=accent, highlightthickness=1)
    outer.pack(fill="both", expand=True, padx=4, pady=4)

    bar = tk.Frame(outer, bg=accent, height=3)
    bar.pack(fill="x")

    hdr = tk.Frame(outer, bg=bg)
    hdr.pack(fill="x", padx=14, pady=(10, 6))
    tk.Label(hdr, text=title, font=("Consolas", 13, "bold"), fg=accent, bg=bg).pack(side="left")

    def _close(*_):
        _OPEN_WINDOWS.discard(key)
        win.destroy()

    tk.Button(
        hdr, text="✕ ESC", command=_close, font=("Consolas", 9, "bold"),
        bg="#1e293b", fg=accent, activebackground=accent, activeforeground=bg,
        relief="flat", padx=8, pady=2, cursor="hand2"
    ).pack(side="right", padx=(8, 0))
    tk.Label(hdr, text="MARK-LVII // HOLOGRAPHIC SUBSYSTEM", font=("Consolas", 8, "bold"), fg="#64748b", bg=bg).pack(side="right")

    win.bind("<Escape>", _close)
    win.protocol("WM_DELETE_WINDOW", _close)
    return win, outer

# 1. DIGITAL TWIN WIREFRAME HUD
def _hud_twin(prefill: str):
    res_w = _base_window("twin", "🧬 DIGITAL TWIN // VIRTUAL PC SIMULATOR", "780x500", "#04101a", "#00f0ff")
    if not res_w: return
    win, root = res_w
    frm = tk.Frame(root, bg="#081c2c", padx=12, pady=12, highlightbackground="#0e3a5c", highlightthickness=1)
    frm.pack(fill="x", padx=14, pady=6)

    tk.Label(frm, text="ACTION TYPE:", font=("Consolas", 10, "bold"), fg="#7dd3fc", bg="#081c2c").grid(row=0, column=0, sticky="w")
    atype = tk.StringVar(value="delete")
    om = tk.OptionMenu(frm, atype, "delete", "move", "overwrite", "command")
    om.config(bg="#0f2942", fg="#00f0ff", activebackground="#0284c7", relief="flat", highlightthickness=0, font=("Consolas", 10, "bold"))
    om.grid(row=0, column=1, sticky="w", padx=8)

    tk.Label(frm, text="TARGET PATH / CMD:", font=("Consolas", 10, "bold"), fg="#7dd3fc", bg="#081c2c").grid(row=1, column=0, sticky="w", pady=(8, 0))
    ent = tk.Entry(frm, font=("Consolas", 10), bg="#0f2942", fg="#ffffff", insertbackground="#00f0ff", relief="flat", width=54)
    ent.insert(0, prefill)
    ent.grid(row=1, column=1, sticky="we", padx=8, pady=(8, 0))

    risk_lbl = tk.Label(root, text="IMPACT STATUS: STANDBY", font=("Consolas", 12, "bold"), fg="#00f0ff", bg="#04101a")
    risk_lbl.pack(pady=8)

    box_wrap, out = _dark_textbox(root, "#02080e", "#a5f3fc", "#00f0ff", height=11)
    box_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def sim():
        from plugins.digital_twin import run as twin_run
        res = twin_run({"action_type": atype.get(), "target": ent.get()})
        color = "#ef4444" if "CRITICAL" in res or "HIGH" in res else "#10b981"
        risk_lbl.config(text=res.split(":")[0], fg=color)
        out.delete("1.0", "end")
        out.insert("end", f"[VIRTUAL TWIN SNAPSHOT]\n{res}\n\n[ROLLBACK GUARD]: Ready. Original filesystem untouched.")

    tk.Button(root, text="⚡ SIMULATE ON VIRTUAL TWIN", command=sim, font=("Consolas", 10, "bold"), bg="#00f0ff", fg="#04101a", relief="flat", padx=16, pady=6, cursor="hand2").pack(pady=(0, 12))
    if prefill: sim()
    win.mainloop()

# 2. FUTURE PREDICTION TELEMETRY HUD + LIVE SPARKLINE GRAPH
def _hud_predict(_prefill: str):
    res_w = _base_window("predict", "📈 FUTURE PREDICTION // TELEMETRY & FORECAST", "760x530", "#041410", "#10b981")
    if not res_w: return
    win, root = res_w
    card = tk.Frame(root, bg="#08241d", padx=16, pady=12, highlightbackground="#065f46", highlightthickness=1)
    card.pack(fill="both", expand=True, padx=14, pady=(4, 12))

    bars = {}
    for metric in ("CPU LOAD", "RAM PRESSURE", "STORAGE USED"):
        row = tk.Frame(card, bg="#08241d")
        row.pack(fill="x", pady=6)
        lbl = tk.Label(row, text=f"{metric}: --%", font=("Consolas", 11, "bold"), fg="#6ee7b7", bg="#08241d", width=26, anchor="w")
        lbl.pack(side="left")
        canvas = tk.Canvas(row, width=360, height=18, bg="#020b09", highlightthickness=1, highlightbackground="#065f46")
        canvas.pack(side="right")
        bars[metric] = (lbl, canvas)

    tk.Label(card, text="LIVE CPU / RAM TELEMETRY WAVEFORM (AUTO-REFRESH 2s)", font=("Consolas", 9, "bold"), fg="#34d399", bg="#08241d").pack(anchor="w", pady=(10, 4))
    spark = tk.Canvas(card, height=85, bg="#020b09", highlightthickness=1, highlightbackground="#065f46")
    spark.pack(fill="x", pady=(0, 10))

    cpu_hist = [5.0] * 36
    ram_hist = [42.0] * 36

    box_wrap, forecast_box = _dark_textbox(card, "#020b09", "#a7f3d0", "#10b981", height=6)
    box_wrap.pack(fill="both", expand=True)

    def refresh():
        if "predict" not in _OPEN_WINDOWS: return
        import shutil
        total, used, _ = shutil.disk_usage(".")
        disk_pct = (used / total) * 100
        cpu_pct, ram_pct = 5.0, 42.0
        try:
            import psutil
            cpu_pct = psutil.cpu_percent(interval=0.1)
            ram_pct = psutil.virtual_memory().percent
        except Exception:
            pass

        cpu_hist.append(cpu_pct); cpu_hist.pop(0)
        ram_hist.append(ram_pct); ram_hist.pop(0)

        for name, val in [("CPU LOAD", cpu_pct), ("RAM PRESSURE", ram_pct), ("STORAGE USED", disk_pct)]:
            lbl, c = bars[name]
            lbl.config(text=f"{name}: {val:.1f}%")
            c.delete("all")
            fill_col = "#ef4444" if val > 80 else ("#f59e0b" if val > 65 else "#10b981")
            c.create_rectangle(0, 0, int(3.6 * min(100, val)), 18, fill=fill_col, width=0)

        # Draw Sparkline
        spark.delete("all")
        w = max(300, spark.winfo_width())
        h = 85
        for gy in (21, 42, 63):
            spark.create_line(0, gy, w, gy, fill="#062c22", dash=(2, 4))
        step = w / (len(cpu_hist) - 1)
        ram_pts = [(i * step, h - (v / 100.0) * (h - 10) - 5) for i, v in enumerate(ram_hist)]
        cpu_pts = [(i * step, h - (v / 100.0) * (h - 10) - 5) for i, v in enumerate(cpu_hist)]
        spark.create_line(ram_pts, fill="#059669", width=2, smooth=True)
        spark.create_line(cpu_pts, fill="#34d399", width=2, smooth=True)
        spark.create_text(8, 10, anchor="w", text="— CPU % (Bright)   — RAM % (Deep)", fill="#6ee7b7", font=("Consolas", 8))

        from plugins.future_predictor import run as pred_run
        forecast_box.delete("1.0", "end")
        forecast_box.insert("end", pred_run({}))
        win.after(2000, refresh)

    refresh()
    win.mainloop()

# 3. AI COUNCIL 3-COLUMN DELIBERATION HUD
def _hud_council(prefill: str):
    res_w = _base_window("council", "⚖️ AI COUNCIL // 3-EXPERT DELIBERATION CHAMBER", "1060x600", "#0f091c", "#c084fc")
    if not res_w: return
    win, root = res_w
    top = tk.Frame(root, bg="#19102e", padx=10, pady=10, highlightbackground="#4c1d95", highlightthickness=1)
    top.pack(fill="x", padx=14, pady=6)
    ent = tk.Entry(top, font=("Consolas", 11), bg="#251842", fg="#ffffff", insertbackground="#c084fc", relief="flat")
    ent.insert(0, prefill)
    ent.pack(side="left", fill="x", expand=True, padx=(0, 10))

    cols = tk.Frame(root, bg="#0f091c")
    cols.pack(fill="both", expand=True, padx=14, pady=6)
    panes = {}
    specs = [("🔬 RESEARCHER", "#38bdf8"), ("📊 ANALYST", "#c084fc"), ("🛡️ SECURITY AI", "#f59e0b")]
    for idx, (title, col) in enumerate(specs):
        f = tk.Frame(cols, bg="#19102e", padx=8, pady=8, highlightbackground=col, highlightthickness=1)
        f.grid(row=0, column=idx, sticky="nsew", padx=4)
        cols.grid_columnconfigure(idx, weight=1)
        cols.grid_rowconfigure(0, weight=1)
        tk.Label(f, text=title, font=("Consolas", 11, "bold"), fg=col, bg="#19102e").pack(anchor="w", pady=(0, 6))
        bw, t = _dark_textbox(f, "#090512", "#e2e8f0", col, height=14, font=("Consolas", 9))
        bw.pack(fill="both", expand=True)
        panes[idx] = t

    verdict_lbl = tk.Label(root, text="COMBINED VERDICT: Enter a question and convene the Council.", font=("Consolas", 10, "bold"), fg="#fde047", bg="#19102e", wraplength=1000, justify="left", padx=12, pady=10, highlightbackground="#eab308", highlightthickness=1)
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

    tk.Button(top, text="⚖️ CONVENE COUNCIL", command=convene, font=("Consolas", 10, "bold"), bg="#c084fc", fg="#0f091c", relief="flat", padx=14, pady=5, cursor="hand2").pack(side="right")
    if prefill: convene()
    win.mainloop()

# 4. MISSION CONTROL TACTICAL BOARD
def _hud_mission(_prefill: str):
    res_w = _base_window("mission", "🎯 MISSION CONTROL // TACTICAL OPS BOARD", "740x520", "#170c04", "#fb923c")
    if not res_w: return
    win, root = res_w
    prog_lbl = tk.Label(root, text="LOADING MISSION...", font=("Consolas", 12, "bold"), fg="#fdba74", bg="#170c04")
    prog_lbl.pack(pady=8)

    board = tk.Frame(root, bg="#261407", padx=14, pady=12, highlightbackground="#9a3412", highlightthickness=1)
    board.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    def render():
        for w in board.winfo_children(): w.destroy()
        sf = Path("memory/mission_control.json")
        if not sf.exists():
            tk.Label(board, text="No active mission. Ask JARVIS: 'Start mission: Title | Step 1; Step 2'", font=("Consolas", 10), fg="#fed7aa", bg="#261407").pack(pady=20)
            return
        data = json.loads(sf.read_text(encoding="utf-8"))
        done = sum(1 for s in data["steps"] if s["done"])
        tot = max(1, len(data["steps"]))
        pct = int((done / tot) * 100)
        prog_lbl.config(text=f"MISSION: {data['title']}  —  {pct}% COMPLETE ({done}/{tot})")

        for idx, step in enumerate(data["steps"], 1):
            row = tk.Frame(board, bg="#261407")
            row.pack(fill="x", pady=5)
            mark = "✅" if step["done"] else "⬜"
            tk.Label(row, text=f"{mark}  STEP {idx}: {step['task']}", font=("Consolas", 11), fg="#86efac" if step["done"] else "#ffedd5", bg="#261407").pack(side="left")
            if not step["done"]:
                tk.Button(row, text="MARK DONE", command=lambda i=idx: (
                    __import__("plugins.mission_control").mission_control.run({"action": "complete_step", "step_index": i}),
                    render()
                ), font=("Consolas", 9, "bold"), bg="#fb923c", fg="#170c04", relief="flat", padx=8, cursor="hand2").pack(side="right")

    render()
    win.mainloop()

# 5. THREAT SIMULATION RED FIREWALL
def _hud_threat(prefill: str):
    res_w = _base_window("threat", "🛡️ THREAT SIMULATION // CYBER QUARANTINE SCANNER", "760x440", "#1a0505", "#ef4444")
    if not res_w: return
    win, root = res_w
    ent = tk.Entry(root, font=("Consolas", 11), bg="#2d0a0a", fg="#ffffff", insertbackground="#ef4444", relief="flat")
    ent.insert(0, prefill)
    ent.pack(fill="x", padx=14, pady=10)

    banner = tk.Label(root, text="FIREWALL ARMED — PASTE COMMAND OR FILE PATH TO SCAN", font=("Consolas", 11, "bold"), fg="#fca5a5", bg="#2d0a0a", pady=14, wraplength=700)
    banner.pack(fill="x", padx=14, pady=6)

    def scan():
        from plugins.threat_simulator import run as t_run
        res = t_run({"payload": ent.get()})
        is_bad = "BLOCKED" in res
        banner.config(text=res, fg="#ffffff", bg="#dc2626" if is_bad else "#059669")

    tk.Button(root, text="🔍 RUN THREAT SIMULATION", command=scan, font=("Consolas", 10, "bold"), bg="#ef4444", fg="#ffffff", relief="flat", padx=16, pady=6, cursor="hand2").pack(pady=10)
    if prefill: scan()
    win.mainloop()

# 6. CONTEXT AWARENESS & INFINITE PROJECT MEMORY HUD
def _hud_project(_prefill: str):
    res_w = _base_window("project", "🧠 CONTEXT AWARENESS & INFINITE PROJECT MEMORY", "800x520", "#06101e", "#38bdf8")
    if not res_w: return
    win, root = res_w
    ctx_lbl = tk.Label(root, text="Scanning active window...", font=("Consolas", 10, "bold"), fg="#7dd3fc", bg="#0c1e38", wraplength=760, justify="left", padx=10, pady=10, highlightbackground="#0284c7", highlightthickness=1)
    ctx_lbl.pack(fill="x", padx=14, pady=8)

    bw, box = _dark_textbox(root, "#030811", "#bae6fd", "#38bdf8", height=16)
    bw.pack(fill="both", expand=True, padx=14, pady=(0, 12))

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
    res_w = _base_window("device", "📱 DEVICE INTELLIGENCE NETWORK // PC ↔ MOBILE MESH", "720x460", "#04151a", "#06b6d4")
    if not res_w: return
    win, root = res_w
    bw, feed = _dark_textbox(root, "#020a0d", "#67e8f9", "#06b6d4", height=14)
    bw.pack(fill="both", expand=True, padx=14, pady=8)

    row = tk.Frame(root, bg="#04151a")
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

    tk.Button(row, text="📤 PUSH TO MOBILE", command=push, font=("Consolas", 9, "bold"), bg="#06b6d4", fg="#04151a", relief="flat", padx=12, pady=5, cursor="hand2").pack(side="right")
    reload_feed()
    win.mainloop()

# 8. CONTROLLED SELF-EVOLUTION VAULT
def _hud_evolve(_prefill: str):
    res_w = _base_window("evolve", "🧬 CONTROLLED SELF-EVOLUTION // SANDBOX APPROVAL VAULT", "760x480", "#171404", "#eab308")
    if not res_w: return
    win, root = res_w
    bw, box = _dark_textbox(root, "#0a0902", "#fef08a", "#eab308", height=16)
    bw.pack(fill="both", expand=True, padx=14, pady=8)

    def refresh():
        from plugins.controlled_evolution import run as ev_run
        box.delete("1.0", "end")
        box.insert("end", ev_run({"action": "list"}))

    tk.Button(root, text="🔄 REFRESH STAGED PROPOSALS", command=refresh, font=("Consolas", 9, "bold"), bg="#eab308", fg="#171404", relief="flat", padx=12, pady=5, cursor="hand2").pack(pady=(0, 12))
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
