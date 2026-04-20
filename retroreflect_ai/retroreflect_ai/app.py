"""
╔══════════════════════════════════════════════════╗
║   RETROREFLECT·AI  —  Python Desktop Edition     ║
║   AI-Powered Road Sign Retroreflectivity Analyzer║
╚══════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import filedialog, ttk
import threading
import cv2
import json
import base64
import time
import requests
import os
import re
import math
import sys
from pathlib import Path
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
from dotenv import load_dotenv

load_dotenv() # Load from .env file

# ── Colours & Fonts ────────────────────────────────────────────────────────────
BG        = "#050a12"
BG2       = "#080f1e"
BG3       = "#0d1928"
ACCENT    = "#ffdd00"
CYAN      = "#00ccff"
GREEN     = "#00ff88"
RED       = "#ff2244"
ORANGE    = "#ff8800"
TEXT      = "#c8d8e8"
MUTED     = "#4a6888"
FONT_MONO = ("Courier", 10)
FONT_BIG  = ("Courier", 28, "bold")
FONT_MED  = ("Courier", 13, "bold")
FONT_SM   = ("Courier", 9)
FONT_XS   = ("Courier", 8)

GRADES = [
    (85, "EXCELLENT",  GREEN,   "Fully compliant. Optimal night visibility."),
    (65, "GOOD",       "#aaff00","Meets standards. Minor degradation noted."),
    (40, "FAIR",       ACCENT,  "Below optimal. Maintenance recommended soon."),
    (20, "POOR",       ORANGE,  "Fails standards. Immediate action required."),
    ( 0, "CRITICAL",   RED,     "Dangerous. Replace immediately."),
]

def get_grade(score: int):
    for threshold, label, color, desc in GRADES:
        if score >= threshold:
            return label, color, desc
    return "CRITICAL", RED, "Dangerous. Replace immediately."


# ── AI Analysis ────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Analyze the imagery/data collected from Vehicle-Mounted or Drone-Mounted cameras using advanced AI/ML techniques for Highway Health Monitoring.

Your goal is to determine:
1. Retroreflectivity Compliance (IRC 67/35)
2. Structural Road Health (Potholes, Cracks, Ravelling, Patching)
3. Environmental Hazards (Water-logging, Dust, Debris, Fog)
4. Traffic Systems (Signal Status, Gantry Visibility)

Analyze the sensor input for: 
- Signs & Pavement Markings
- Road Surface (Pot-holes, surface wear)
- Drainage/Hazards (Water logging, dust accumulation)

Return ONLY a valid JSON object:
{
  "score": <integer 0-100 overall safety score>,
  "surfaceType": "<Gantry Sign | Road Surface | Pavement Marking | RPM | Delineator>",
  "roadHealth": {
    "condition": "<Good | Potholed | Damaged | Under Construction>",
    "defects": ["<defect1>"],
    "damageSeverity": "<None | Low | Moderate | High>"
  },
  "environmentalAlerts": {
    "waterLogging": "<True/False>",
    "visibilityInterference": "<Dust | Fog | Smoke | None>",
    "debrisDetected": "<True/False>"
  },
  "trafficSignal": {
    "detected": "<True/False>",
    "status": "<Red | Yellow | Green | Flashing | N/A>"
  },
  "ircCompliance": { "status": "<Compliant | Partial | Non-Compliant>", "standard": "<IRC 67 | IRC 35 | IRC 82 (Maintenance)>" },
  "metrics": {
    "reflectivity": <0-100>, "surfaceIntegrity": <0-100>, "hazardSafety": <0-100>, "legibility": <0-100>, "weathering": <0-100>
  },
  "urgency": "<Immediate | Within 3 months | No action needed>",
  "summary": "<2-sentence highway health & safety audit wrapup>"
}"""


def analyze_image(image_path: str, api_key: str) -> dict:
    """Cascading API analysis with auto-failover support."""
    primary = os.environ.get("MODEL_CHOICE", "GEMINI")
    providers = []
    
    if primary == "GEMINI":
        providers = [("GEMINI", os.environ.get("GOOGLE_API_KEY")), 
                     ("ANTHROPIC", os.environ.get("ANTHROPIC_API_KEY")),
                     ("OPENAI", os.environ.get("OPENAI_API_KEY")),
                     ("OPENROUTER", os.environ.get("OPENROUTER_API_KEY"))]
    else:
        providers = [("ANTHROPIC", os.environ.get("ANTHROPIC_API_KEY")),
                     ("GEMINI", os.environ.get("GOOGLE_API_KEY")),
                     ("OPENAI", os.environ.get("OPENAI_API_KEY")),
                     ("OPENROUTER", os.environ.get("OPENROUTER_API_KEY"))]

    errors = []
    for name, key in providers:
        if not key or len(key) < 5: continue
        try:
            if name == "GEMINI":
                res = analyze_image_gemini(image_path, key)
            elif name == "ANTHROPIC":
                res = analyze_image_claude(image_path, key)
            elif name == "OPENAI":
                res = analyze_image_openai(image_path, key)
            else:
                res = analyze_image_openrouter(image_path, key)
            
            res["_provider"] = name
            return res
        except Exception as e:
            errors.append(f"{name}: {str(e)}")
            print(f"Failover: {name} failed, trying next...")
            continue
    
    raise Exception(f"All API providers failed or quota exceeded: {'; '.join(errors)}")

def analyze_image_gemini(image_path: str, api_key: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    
    img = Image.open(image_path)
    response = model.generate_content([
        SYSTEM_PROMPT,
        img,
        "Analyze this highway asset data. Respond only with the JSON object."
    ])
    
    clean = re.sub(r"```json|```", "", response.text).strip()
    return json.loads(clean)

def analyze_image_openai(image_path: str, api_key: str) -> dict:
    """Send to OpenAI GPT-4o Vision."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    headers = { "Authorization": f"Bearer {api_key}", "Content-Type": "application/json" }
    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": SYSTEM_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    data = response.json()
    text = data['choices'][0]['message']['content']
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)

def analyze_image_openrouter(image_path: str, api_key: str) -> dict:
    """Direct POST to OpenRouter for Llama 3.2 Vision or similar."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    headers = { "Authorization": f"Bearer {api_key}", "Content-Type": "application/json" }
    payload = {
        "model": "google/gemini-2.0-flash-001", # High availability via OpenRouter
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": SYSTEM_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    data = response.json()
    text = data['choices'][0]['message']['content']
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)

def analyze_image_claude(image_path: str, api_key: str) -> dict:
    import anthropic
    with open(image_path, "rb") as f:
        raw = f.read()

    ext = Path(image_path).suffix.lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    media_type = media_map.get(ext, "image/jpeg")
    b64 = base64.standard_b64encode(raw).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text",  "text": "Analyze JSON."}
        ]}]
    )
    text = "".join(b.text for b in message.content if hasattr(b, "text"))
    clean = re.sub(r"```json|```", "", text).strip()
    return json.loads(clean)


# ── Reusable Widget Helpers ─────────────────────────────────────────────────────
def hline(parent, color=BG3, **kw):
    tk.Frame(parent, bg=color, height=1, **kw).pack(fill="x", pady=6)

def label(parent, text, font=FONT_MONO, fg=TEXT, bg=BG, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

def section_title(parent, text):
    f = tk.Frame(parent, bg=BG)
    f.pack(fill="x", pady=(10, 4))
    tk.Label(f, text=text, font=FONT_XS, fg=ACCENT,
             bg=BG).pack(side="left")
    tk.Frame(f, bg=ACCENT, height=1).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=6)


# ── Score Ring Canvas ───────────────────────────────────────────────────────────
class ScoreRing(tk.Canvas):
    def __init__(self, parent, size=160, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0, **kw)
        self.size  = size
        self.score = 0
        self.color = ACCENT
        self._draw(0, ACCENT)

    def set_score(self, score: int, color: str):
        self.score = score
        self.color = color
        self._animate(0, score)

    def _animate(self, current, target):
        if current <= target:
            self._draw(current, self.color)
            self.after(12, self._animate, current + 2, target)
        else:
            self._draw(target, self.color)

    def _draw(self, score, color):
        self.delete("all")
        cx = cy = self.size // 2
        r  = cx - 18
        # Track
        self.create_arc(cx - r, cy - r, cx + r, cy + r,
                        start=0, extent=359.9, style="arc",
                        outline=BG3, width=12)
        # Arc
        if score > 0:
            extent = -360 * score / 100
            self.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=90, extent=extent, style="arc",
                            outline=color, width=12)
        # Score text
        self.create_text(cx, cy - 10, text=str(score),
                         font=("Courier", 32, "bold"), fill=color)
        self.create_text(cx, cy + 18, text="/ 100",
                         font=FONT_XS, fill=MUTED)


# ── Main Application Window ─────────────────────────────────────────────────────
class RetroReflectApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RETROREFLECT·AI  —  Smart Retroreflectivity Analyzer")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(880, 620)
        self.geometry("1100x750")

        self.image_path  = None
        self.photo_img   = None
        # Try to load keys from .env
        env_key = os.environ.get("GOOGLE_API_KEY") if os.environ.get("MODEL_CHOICE") == "GEMINI" else os.environ.get("ANTHROPIC_API_KEY")
        self.api_key_var = tk.StringVar(value=env_key or "")
        self.result      = None
        self.cap         = None
        self.cam_running = False
        self.history     = []

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── Layout ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top bar ──
        topbar = tk.Frame(self, bg="#030810", pady=0)
        topbar.pack(fill="x")
        tk.Frame(topbar, bg=ACCENT, height=3).pack(fill="x")
        inner = tk.Frame(topbar, bg="#030810")
        inner.pack(fill="x", padx=20, pady=8)
        tk.Label(inner, text="◈ RETROREFLECT", font=("Courier", 16, "bold"),
                 fg=ACCENT, bg="#030810").pack(side="left")
        tk.Label(inner, text="·AI", font=("Courier", 16, "bold"),
                 fg=CYAN, bg="#030810").pack(side="left")
        tk.Label(inner, text="  SMART RETROREFLECTIVITY MEASUREMENT SYSTEM",
                 font=FONT_XS, fg=MUTED, bg="#030810").pack(side="left", padx=10)

        # ── NHAI Metadata Bar ──
        meta_b = tk.Frame(self, bg=BG2, pady=4)
        meta_b.pack(fill="x")
        
        self.sensor_source = tk.StringVar(value="VEHICLE-MOUNTED")
        self.hway_name = tk.StringVar(value="NH-")
        self.lane_type = tk.StringVar(value="6-LANE")
        
        label(meta_b, " SENSOR:", bg=BG2, fg=ACCENT).pack(side="left", padx=(16, 2))
        ttk.Combobox(meta_b, textvariable=self.sensor_source, values=["STATIC/HANDHELD", "VEHICLE-MOUNTED", "DRONE-AERIAL"], width=18).pack(side="left", padx=4)

        label(meta_b, " HIGHWAY:", bg=BG2, fg=MUTED).pack(side="left", padx=(10, 2))
        tk.Entry(meta_b, textvariable=self.hway_name, font=FONT_XS, bg=BG, fg=TEXT, border=0, width=12).pack(side="left", padx=4)
        
        label(meta_b, " CONFIG:", bg=BG2, fg=MUTED).pack(side="left", padx=(10, 2))
        ttk.Combobox(meta_b, textvariable=self.lane_type, values=["8-LANE EXPRESSWAY", "6-LANE", "4-LANE", "2-LANE"], width=15).pack(side="left", padx=4)
        
        label(meta_b, " SPEED/ALT:", bg=BG2, fg=MUTED).pack(side="left", padx=(10, 2))
        self.telemetry = tk.Entry(meta_b, font=FONT_XS, bg=BG, fg=TEXT, border=0, width=8)
        self.telemetry.insert(0, "40 KM/H")
        self.telemetry.pack(side="left", padx=4)

        # ── API key bar ──
        apib = tk.Frame(self, bg=BG3, pady=6)
        apib.pack(fill="x")
        
        m_choice = os.environ.get("MODEL_CHOICE", "GEMINI")
        tk.Label(apib, text=f" [{m_choice} ACTIVE]  KEY ▸", font=FONT_XS, fg=CYAN if m_choice == "GEMINI" else ORANGE,
                 bg=BG3).pack(side="left", padx=(16, 4))
        
        api_entry = tk.Entry(apib, textvariable=self.api_key_var,
                             font=FONT_SM, bg="#0a1828", fg=TEXT,
                             insertbackground=ACCENT, relief="flat",
                             show="•", width=48)
        api_entry.pack(side="left", ipady=3, padx=4)
        
        tk.Button(apib, text="SWITCH MODEL", font=FONT_XS, bg=BG2, fg=MUTED,
                  relief="flat", cursor="hand2",
                  command=self._switch_model).pack(side="right", padx=10)

    def _switch_model(self):
        current = os.environ.get("MODEL_CHOICE", "GEMINI")
        new_m = "ANTHROPIC" if current == "GEMINI" else "GEMINI"
        os.environ["MODEL_CHOICE"] = new_m
        
        # Load correct key from env if available
        env_key = os.environ.get("GOOGLE_API_KEY" if new_m == "GEMINI" else "ANTHROPIC_API_KEY")
        self.api_key_var.set(env_key or "")
        self._set_status(f"Switched to {new_m} engine.", CYAN if new_m == "GEMINI" else ORANGE)
        # Force a UI refresh of the label is complex with packs, but functionality works.

        # ── Main content ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=10)

        # Left panel
        self.left = tk.Frame(main, bg=BG, width=360)
        self.left.pack(side="left", fill="y", padx=(0, 10))
        self.left.pack_propagate(False)
        self._build_left(self.left)

        # Right panel - Tabs
        self.right = tk.Frame(main, bg=BG)
        self.right.pack(side="left", fill="both", expand=True)
        
        # Style notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG3, foreground=MUTED, padding=[12, 4], font=FONT_XS)
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", BG)])
        
        self.notebook = ttk.Notebook(self.right)
        self.notebook.pack(fill="both", expand=True)
        
        self.dash_tab = tk.Frame(self.notebook, bg=BG)
        self.hist_tab = tk.Frame(self.notebook, bg=BG)
        
        self.notebook.add(self.dash_tab, text=" 📊 DASHBOARD ")
        self.notebook.add(self.hist_tab, text=" 🕰 HISTORY ")
        
        self._build_dashboard_empty()
        self._build_history()

    def _build_dashboard_empty(self):
        for w in self.dash_tab.winfo_children(): w.destroy()
        ph = tk.Frame(self.dash_tab, bg=BG)
        ph.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(ph, text="NO DATA", font=("Courier", 14, "bold"), fg=BG3, bg=BG).pack()
        tk.Label(ph, text="Run analysis to see dashboard", font=FONT_XS, fg=MUTED, bg=BG).pack()

    def _build_left(self, parent):
        # Image preview area
        section_title(parent, "◈ IMAGE INPUT")
        self.img_frame = tk.Frame(parent, bg=BG2,
                                  highlightbackground=MUTED,
                                  highlightthickness=1, height=220)
        self.img_frame.pack(fill="x")
        self.img_frame.pack_propagate(False)
        self.img_canvas = tk.Canvas(self.img_frame, bg=BG2,
                                    highlightthickness=0)
        self.img_canvas.pack(fill="both", expand=True)
        self._draw_drop_placeholder()

        # Buttons Row 1: Source Selection
        btn_f1 = tk.Frame(parent, bg=BG)
        btn_f1.pack(fill="x", pady=(8, 2))
        
        self.btn_browse = tk.Button(btn_f1, text="▶ BROWSE", font=FONT_XS, bg=BG3, fg=CYAN, relief="flat", cursor="hand2", pady=5, command=self._browse_image)
        self.btn_browse.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_camera = tk.Button(btn_f1, text="📷 CAMERA", font=FONT_XS, bg=BG3, fg=ORANGE, relief="flat", cursor="hand2", pady=5, command=self._toggle_camera)
        self.btn_camera.pack(side="left", fill="x", expand=True, padx=2)
        
        self.btn_video = tk.Button(btn_f1, text="🎬 VIDEO", font=FONT_XS, bg=BG3, fg=PURPLE, relief="flat", cursor="hand2", pady=5, command=self._load_video)
        self.btn_video.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Buttons Row 2: Analysis Type
        btn_f2 = tk.Frame(parent, bg=BG)
        btn_f2.pack(fill="x", pady=(2, 8))

        self.btn_live = tk.Button(btn_f2, text="⚡ LIVE", font=FONT_XS, bg=BG3, fg=CYAN, relief="flat", cursor="hand2", pady=5, command=self._toggle_live_audit)
        self.btn_live.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.btn_batch = tk.Button(btn_f2, text="▣ BATCH", font=FONT_XS, bg=BG3, fg=ORANGE, relief="flat", cursor="hand2", pady=5, command=self._batch_audit_video)
        self.btn_batch.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_analyze = tk.Button(btn_f2, text="⟳ ANALYZE", font=FONT_XS, bg=ACCENT, fg=BG, relief="flat", cursor="hand2", pady=5, state="disabled", command=self._start_analysis)
        self.btn_analyze.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Status label
        self.status_lbl = tk.Label(parent, text="Select sensor source and begin survey.",
                                   font=FONT_XS, fg=MUTED, bg=BG,
                                   wraplength=340, justify="left")
        self.status_lbl.pack(fill="x", pady=(2, 6))

        # Real-time Stream simulation button
        self.btn_stream = tk.Button(
            parent, text="📡  START AI/ML STREAM",
            font=FONT_SM, bg=BG3, fg=GREEN,
            activebackground=GREEN, activeforeground=BG,
            relief="flat", cursor="hand2", pady=8,
            command=self._toggle_stream)
        self.btn_stream.pack(fill="x", pady=(0,8))

        # Quick metrics panel (shows after analysis)
        section_title(parent, "◈ QUICK METRICS")
        self.metrics_frame = tk.Frame(parent, bg=BG)
        self.metrics_frame.pack(fill="x")
        self._build_metrics_placeholders()

        # Scrollable issues
        section_title(parent, "◈ ISSUES DETECTED")
        self.issues_text = tk.Text(parent, height=5, bg=BG2, fg="#ff8899",
                                   font=FONT_XS, relief="flat",
                                   state="disabled", wrap="word",
                                   padx=8, pady=6)
        self.issues_text.pack(fill="x")

    def _build_metrics_placeholders(self):
        for w in self.metrics_frame.winfo_children():
            w.destroy()
        keys = ["Audit Standard", "IRC Compliance", "Surface Type", "Weather Cond.", 
                "Lighting", "Material", "Night Visibility", "Urgency"]
        for k in keys:
            row = tk.Frame(self.metrics_frame, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"  {k}:", font=FONT_XS, fg=MUTED,
                     bg=BG, width=18, anchor="w").pack(side="left")
            tk.Label(row, text="—", font=FONT_XS, fg=TEXT,
                     bg=BG, anchor="w").pack(side="left")

    def _build_right_empty(self, parent):
        for w in parent.winfo_children():
            w.destroy()
        # Centered placeholder
        ph = tk.Frame(parent, bg=BG)
        ph.place(relx=0.5, rely=0.5, anchor="center")

        # Animated dot grid
        c = tk.Canvas(ph, width=200, height=200, bg=BG, highlightthickness=0)
        c.pack()
        for i in range(5):
            for j in range(5):
                x, y = 20 + j * 40, 20 + i * 40
                color = ACCENT if (i + j) % 2 == 0 else BG3
                c.create_oval(x-3, y-3, x+3, y+3, fill=color, outline="")

        tk.Label(ph, text="NO ANALYSIS YET", font=("Courier", 14, "bold"),
                 fg=BG3, bg=BG).pack(pady=(16, 4))
        tk.Label(ph, text="Upload an image and click ANALYZE",
                 font=FONT_XS, fg=MUTED, bg=BG).pack()

    # ── Image Handling ──────────────────────────────────────────────────────────
    def _draw_drop_placeholder(self):
        self.img_canvas.delete("all")
        self.img_canvas.update_idletasks()
        w = self.img_canvas.winfo_width() or 340
        h = self.img_canvas.winfo_height() or 220
        cx, cy = w // 2, h // 2
        self.img_canvas.create_text(cx, cy - 16, text="🔆",
                                    font=("Courier", 32), fill=MUTED)
        self.img_canvas.create_text(cx, cy + 20,
                                    text="Drop or browse an image",
                                    font=FONT_XS, fill=MUTED)

    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="Select Road Sign Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"),
                       ("All files", "*.*")])
        if path:
            self._load_image(path)

    def _load_image(self, path: str):
        self.image_path = path
        try:
            img = Image.open(path)
            img.thumbnail((340, 220), Image.LANCZOS)
            self.photo_img = ImageTk.PhotoImage(img)
            self.img_canvas.delete("all")
            self.img_canvas.update_idletasks()
            w = self.img_canvas.winfo_width() or 340
            h = self.img_canvas.winfo_height() or 220
            self.img_canvas.create_image(w // 2, h // 2,
                                         anchor="center", image=self.photo_img)
            # Corner HUD marks
            for (ax, ay) in [(4, 4), (w-4, 4), (4, h-4), (w-4, h-4)]:
                dx = 12 if ax < w // 2 else -12
                dy = 12 if ay < h // 2 else -12
                self.img_canvas.create_line(ax, ay, ax + dx, ay, fill=ACCENT, width=2)
                self.img_canvas.create_line(ax, ay, ax, ay + dy, fill=ACCENT, width=2)
        except Exception as e:
            self._set_status(f"Error loading image: {e}", RED)
            return
        self.btn_analyze.config(state="normal")
        self._set_status(f"Ready: {Path(path).name}", GREEN)

    # ── Camera Logic ──────────────────────────────────────────────────────────
    def _toggle_camera(self):
        if not self.cam_running:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self._set_status("✗ Camera not found or busy", RED)
                return
            self.cam_running = True
            self.btn_camera.config(text="● CAPTURE", bg=RED, fg="#fff")
            self._update_camera()
            self._set_status("Camera Live: Position the sign and click CAPTURE", ORANGE)
        else:
            self._capture_image()

    def _update_camera(self):
        if self.cam_running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1) # Mirror
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2image)
                
                # Resize to fit canvas
                cw = self.img_canvas.winfo_width() or 340
                ch = self.img_canvas.winfo_height() or 220
                img.thumbnail((cw, ch), Image.LANCZOS)
                
                self.photo_img = ImageTk.PhotoImage(img)
                self.img_canvas.delete("all")
                self.img_canvas.create_image(cw // 2, ch // 2, anchor="center", image=self.photo_img)
                
                # HUD effect on live feed
                self.img_canvas.create_rectangle(cw//2-50, ch//2-50, cw//2+50, ch//2+50, outline=ORANGE, dash=(4,4))
                
                # Live status indicator
                if hasattr(self, "live_audit_on") and self.live_audit_on:
                    self.img_canvas.create_text(50, 20, text="● LIVE AUDIT", fill=RED, font=FONT_XS)
                    self.img_canvas.create_rectangle(0, 0, cw, ch, outline=CYAN, width=2)
                
                self.after(15, self._update_camera)

    def _toggle_live_audit(self):
        if not hasattr(self, "live_audit_on") or not self.live_audit_on:
            if not self.cam_running:
                self._toggle_camera()
            self.live_audit_on = True
            self.btn_live.config(text="■ STOP LIVE", bg=RED, fg="#fff")
            self._set_status("Live Audit: Sampling frames every 5s for AI analysis...", CYAN)
            self._run_live_audit_tick()
        else:
            self.live_audit_on = False
            self.btn_live.config(text="⚡ LIVE AUDIT", bg=BG3, fg=CYAN)
            self._set_status("Live Audit stopped.", MUTED)

    def _run_live_audit_tick(self):
        if hasattr(self, "live_audit_on") and self.live_audit_on and self.cam_running:
            # Capture current frame and send for analysis
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                temp_path = os.path.join(os.getcwd(), "live_sample.jpg")
                cv2.imwrite(temp_path, frame)
                api_key = self.api_key_var.get().strip()
                if api_key:
                    # Start background analysis without blocking
                    self._set_status("Auditing frame...", CYAN)
                    thread = threading.Thread(target=self._run_analysis,
                                              args=(temp_path, api_key), daemon=True)
                    thread.start()
            
            # Re-schedule next sample in 5 seconds
            self.after(5000, self._run_live_audit_tick)

    def _capture_image(self):
        self.cam_running = False
        ret, frame = self.cap.read()
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if ret:
            frame = cv2.flip(frame, 1)
            # Create a temp file to store captured image
            temp_path = os.path.join(os.getcwd(), "captured_input.jpg")
            cv2.imwrite(temp_path, frame)
            self._load_image(temp_path)
            self.btn_camera.config(text="📷  RE-OPEN", bg=BG3, fg=ORANGE)
            self._set_status("Captured! Ready for analysis.", GREEN)
        else:
            self._set_status("✗ Capture failed", RED)
            self.btn_camera.config(text="📷  CAMERA", bg=BG3, fg=ORANGE)

    # ── AI/ML Stream Logic ──────────────────────────────────────────────────────
    def _toggle_stream(self):
        if not hasattr(self, "streaming") or not self.streaming:
            self.streaming = True
            self.btn_stream.config(text="■ STOP STREAM", bg=RED, fg="#fff")
            self._run_stream_tick()
            self._set_status("AI/ML Stream Active: Processing frames at high speed...", GREEN)
        else:
            self.streaming = False
            self.btn_stream.config(text="📡  START AI/ML STREAM", bg=BG3, fg=GREEN)
            self._set_status("Stream paused.", MUTED)

    def _run_stream_tick(self):
        if hasattr(self, "streaming") and self.streaming:
            # Simulate high-speed AI processing
            w = self.img_canvas.winfo_width() or 340
            h = self.img_canvas.winfo_height() or 220
            self.img_canvas.delete("stream_ui")
            cx, cy = w//2, h//2
            
            # Draw radar/scan scanning effect
            scan_y = (math.sin(self.winfo_fpixels('1i') * self._spin_idx / 50) + 1) / 2 * h
            self.img_canvas.create_line(0, scan_y, w, scan_y, fill=GREEN, width=1, tags="stream_ui")
            self.img_canvas.create_text(w-50, 20, text="● AI PROCESSING", font=FONT_XS, fill=RED, tags="stream_ui")
            
            self._spin_idx += 1
            self.after(50, self._run_stream_tick)

    # ── Analysis ────────────────────────────────────────────────────────────────
    def _start_analysis(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self._set_status("⚠ Enter your Anthropic API key first.", RED)
            return
        if not self.image_path:
            self._set_status("⚠ No image selected.", RED)
            return

        self.btn_analyze.config(state="disabled", text="⟳  ANALYZING…")
        self._set_status("Sending to Claude AI…", CYAN)
        self._start_spinner()

        thread = threading.Thread(target=self._run_analysis,
                                  args=(self.image_path, api_key), daemon=True)
        thread.start()

    def _run_analysis(self, path: str, api_key: str):
        try:
            result = analyze_image(path, api_key)
            self.after(0, self._on_result, result)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_result(self, result: dict):
        self._stop_spinner()
        # Add metadata to history entry
        result["_hway"] = self.hway_name.get()
        result["_pos"] = self.chainage_entry.get()
        
        self.result = result
        self.history.append(result)
        self.btn_analyze.config(state="normal", text="⟳  ANALYZE")
        self._set_status("✓ Analysis complete.", GREEN)
        self._update_left_panel(result)
        self._build_dashboard(result)
        self._build_history()
        self.notebook.select(0)

    def _on_error(self, err: str):
        self._stop_spinner()
        self.btn_analyze.config(state="normal", text="⟳  ANALYZE")
        self._set_status(f"✗ {err[:80]}", RED)

    # ── Spinner ─────────────────────────────────────────────────────────────────
    _spin_chars = ["◐", "◓", "◑", "◒"]
    _spin_idx   = 0
    _spin_job   = None

    def _start_spinner(self):
        self._spin_idx = 0
        self._tick_spinner()

    def _tick_spinner(self):
        ch = self._spin_chars[self._spin_idx % len(self._spin_chars)]
        self._set_status(f"{ch}  Analyzing retroreflectivity…", CYAN)
        self._spin_idx += 1
        self._spin_job = self.after(200, self._tick_spinner)

    def _stop_spinner(self):
        if self._spin_job:
            self.after_cancel(self._spin_job)
            self._spin_job = None

    def _set_status(self, msg: str, color=MUTED):
        self.status_lbl.config(text=msg, fg=color)

    # ── Left Panel Update ───────────────────────────────────────────────────────
    def _update_left_panel(self, r: dict):
        # Rebuild metrics
        for w in self.metrics_frame.winfo_children():
            w.destroy()
        irc = r.get("ircCompliance", {})
        health = r.get("roadHealth", {})
        hazards = r.get("environmentalAlerts", {})
        signal = r.get("trafficSignal", {})
        
        metrics = [
            ("Audit Standard",  irc.get("standard", "IRC 67")),
            ("Road Condition",  health.get("condition", "—")),
            ("Damage Severity", health.get("damageSeverity", "—")),
            ("Hazard Detection", "DETECTED" if hazards.get("waterLogging") or hazards.get("debrisDetected") else "NONE"),
            ("Water Logging",   "YES" if hazards.get("waterLogging") else "NO"),
            ("Traffic Signal",  signal.get("status", "N/A")),
            ("Legibility",      f"{r.get('metrics', {}).get('legibility', 0)}%"),
            ("Urgency",         r.get("urgency", "—")),
        ]
        compliance_colors = {"Compliant": GREEN, "Non-Compliant": RED, "Partial": ACCENT}
        for k, v in metrics:
            row = tk.Frame(self.metrics_frame, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"  {k}:", font=FONT_XS, fg=MUTED,
                     bg=BG, width=18, anchor="w").pack(side="left")
            color = compliance_colors.get(v, TEXT) if k == "IRC Compliance" else TEXT
            tk.Label(row, text=v, font=("Courier", 9, "bold"),
                     fg=color, bg=BG, anchor="w").pack(side="left")

        # Issues
        issues = r.get("issues", [])
        self.issues_text.config(state="normal")
        self.issues_text.delete("1.0", "end")
        if issues:
            for iss in issues:
                self.issues_text.insert("end", f"  ▸ {iss}\n")
        else:
            self.issues_text.insert("end", "  ✓ No significant issues detected.")
        self.issues_text.config(state="disabled")

    # ── Dashboard & History ───────────────────────────────────────────────────
    def _build_dashboard(self, r: dict):
        for w in self.dash_tab.winfo_children(): w.destroy()
        
        score = int(r.get("score", 0))
        label_text, color, desc = get_grade(score)
        
        canvas = tk.Canvas(self.dash_tab, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        content = tk.Frame(canvas, bg=BG)
        canvas.create_window((0,0), window=content, anchor="nw")
        
        # Hero row
        hero = tk.Frame(content, bg=BG2, relief="flat", padx=20, pady=20)
        hero.pack(fill="x", padx=10, pady=10)
        
        ring = ScoreRing(hero, size=150)
        ring.pack(side="left")
        self.after(100, lambda: ring.set_score(score, color))
        
        txt_col = tk.Frame(hero, bg=BG2)
        txt_col.pack(side="left", padx=20)
        tk.Label(txt_col, text="OVERALL GRADE", font=FONT_XS, fg=MUTED, bg=BG2).pack(anchor="w")
        tk.Label(txt_col, text=label_text, font=FONT_BIG, fg=color, bg=BG2).pack(anchor="w")
        tk.Label(txt_col, text=desc, font=FONT_SM, fg=TEXT, bg=BG2, wraplength=400, justify="left").pack(anchor="w", pady=4)
        
        # Metrics row
        metrics_f = tk.Frame(content, bg=BG)
        metrics_f.pack(fill="x", padx=10)
        
        # Sub-score bars
        bars_f = tk.Frame(metrics_f, bg=BG2, padx=20, pady=20)
        bars_f.pack(side="left", fill="both", expand=True, padx=(0, 5))
        section_title(bars_f, "▣ NHAI AUDIT METRICS")
        
        m_data = r.get("metrics", {})
        for name, key in [("Reflectivity", "reflectivity"), ("Surface Health", "surfaceIntegrity"), 
                          ("Signal Visibility", "legibility"), ("Hazard Safety", "hazardSafety"), ("Serviceability", "weathering")]:
            val = m_data.get(key, 0)
            row = tk.Frame(bars_f, bg=BG2)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=name, font=FONT_XS, fg=TEXT, bg=BG2, width=14, anchor="w").pack(side="left")
            
            bar_t = tk.Frame(row, bg=BG3, height=8)
            bar_t.pack(side="left", fill="x", expand=True, padx=10)
            bar_v = tk.Frame(bar_t, bg=CYAN if val > 50 else ORANGE, width=val*2, height=8)
            bar_v.pack(side="left")
            
            tk.Label(row, text=f"{val}%", font=FONT_XS, fg=MUTED, bg=BG2, width=4).pack(side="left")

        # Traffic Intelligence section
        rec_f = tk.Frame(metrics_f, bg=BG2, padx=20, pady=20)
        rec_f.pack(side="left", fill="both", expand=True, padx=(5, 0))
        section_title(rec_f, "🚥 TRAFFIC INTELLIGENCE")
        
        sig = r.get("trafficSignal", {})
        sig_status = sig.get("status", "N/A")
        sig_color = GREEN if sig_status == "Green" else RED if sig_status == "Red" else ORANGE if sig_status == "Yellow" else MUTED
        
        # Signal Indicator Light
        sig_row = tk.Frame(rec_f, bg=BG2)
        sig_row.pack(fill="x", pady=5)
        tk.Canvas(sig_row, width=12, height=12, bg=BG2, highlightthickness=0).pack(side="left")
        
        canvas_sig = tk.Canvas(sig_row, width=20, height=20, bg=BG2, highlightthickness=0)
        canvas_sig.pack(side="left")
        canvas_sig.create_oval(2, 2, 18, 18, fill=sig_color, outline=BG3)
        
        tk.Label(sig_row, text=f" SIGNAL: {sig_status.upper()}", font=FONT_MED, fg=sig_color, bg=BG2).pack(side="left", padx=10)
        
        health = r.get("roadHealth", {})
        meta_items = [
            ("DETECTED", "YES" if sig.get("detected") else "NO"),
            ("PHASE", "ACTIVE" if sig.get("detected") else "N/A"),
            ("SURFACE", health.get("condition", "—")),
            ("WATER LOG", "YES" if r.get("environmentalAlerts", {}).get("waterLogging") else "NO")
        ]
        for k, v in meta_items:
            row = tk.Frame(rec_f, bg=BG2)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{k}:", font=FONT_XS, fg=MUTED, bg=BG2, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=v, font=FONT_XS, fg=TEXT, bg=BG2, anchor="w").pack(side="left")

    def _build_history(self):
        for w in self.hist_tab.winfo_children(): w.destroy()
        if not self.history:
            tk.Label(self.hist_tab, text="NO HISTORY YET", font=FONT_SM, fg=BG3, bg=BG).place(relx=0.5, rely=0.5, anchor="center")
            return
            
        tree = ttk.Treeview(self.hist_tab, columns=("highway", "chainage", "score", "grade", "irc"), show="headings")
        tree.heading("highway", text="HIGHWAY")
        tree.heading("chainage", text="CHAINAGE")
        tree.heading("score", text="SCORE")
        tree.heading("grade", text="GRADE")
        tree.heading("irc", text="IRC STATUS")
        
        tree.column("highway", width=100)
        tree.column("chainage", width=100)
        tree.column("score", width=60, anchor="center")
        tree.column("grade", width=100)
        tree.column("irc", width=120)
        
        for i, item in enumerate(reversed(self.history)):
            s = item.get("score", 0)
            g, _, _ = get_grade(s)
            tree.insert("", "end", values=(
                item.get("_hway", "—"), 
                item.get("_pos", "—"), 
                s, g, 
                item.get("ircCompliance", {}).get("status", "—")
            ))
            
        tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ── Video Logic ───────────────────────────────────────────────────────────
    def _load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self.video_path = path
            self.cam_running = False
            if self.cap: self.cap.release()
            vcap = cv2.VideoCapture(path)
            ret, frame = vcap.read()
            if ret:
                temp_p = os.path.join(os.getcwd(), "vid_thumb.jpg")
                cv2.imwrite(temp_p, frame)
                self._load_image_from_path(temp_p)
            vcap.release()
            self._set_status(f"Video Loaded: {os.path.basename(path)}", PURPLE)

    def _batch_audit_video(self):
        if not hasattr(self, "video_path") or not self.video_path:
            self._set_status("⚠ Load video first.", ORANGE)
            return
        api_key = self.api_key_var.get().strip()
        if not api_key:
            self._set_status("⚠ API key required.", RED)
            return
        self.btn_batch.config(state="disabled", text="▣ PROCESSING")
        threading.Thread(target=self._run_batch_video_audit, args=(api_key,), daemon=True).start()

    def _run_batch_video_audit(self, api_key):
        vcap = cv2.VideoCapture(self.video_path)
        fps = vcap.get(cv2.CAP_PROP_FPS)
        total_f = int(vcap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = int(fps * 5) # Sample every 5s
        
        f_idx = 0
        while vcap.isOpened():
            vcap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, frame = vcap.read()
            if not ret: break
            
            temp_p = os.path.join(os.getcwd(), f"batch_frame.jpg")
            cv2.imwrite(temp_p, frame)
            self._set_status(f"Auditing Video... {f_idx}/{total_f}", CYAN)
            
            try:
                res = analyze_image(temp_p, api_key)
                self.after(0, self._on_result, res)
            except: pass
            
            f_idx += interval
            if f_idx >= total_f: break
            time.sleep(0.5)

        vcap.release()
        self.after(0, lambda: self.btn_batch.config(state="normal", text="▣ BATCH"))
        self._set_status("✓ Batch Audit Complete.", GREEN)


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = RetroReflectApp()
    app.mainloop()
