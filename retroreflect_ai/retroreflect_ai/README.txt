╔══════════════════════════════════════════════════════════╗
║   RETROREFLECT·AI  —  Python Desktop Edition            ║
║   AI-Powered Road Sign Retroreflectivity Analyzer       ║
╚══════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT IT DOES
────────────
Upload any road sign or road marking image and the AI will:

  ◈ Score retroreflectivity (0–100 index)
  ◈ Grade as EXCELLENT / GOOD / FAIR / POOR / CRITICAL
  ◈ Detect material type (Type III Sheeting, Glass Bead, etc.)
  ◈ Estimate night-time visibility distance
  ◈ Assess degradation level and estimated age
  ◈ Check compliance status (Compliant / Non-Compliant / Borderline)
  ◈ Set action urgency (Immediate → No action needed)
  ◈ List issues detected and expert recommendations
  ◈ Provide 2-sentence expert AI analysis

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIREMENTS
────────────
  • Python 3.9 or higher
  • Tkinter (usually bundled with Python)
  • Anthropic API key  →  https://console.anthropic.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SETUP & RUN
───────────

1. Install dependencies:

     pip install -r requirements.txt

2. Run the app:

     python app.py

   OR set your API key as environment variable (optional):

     # Windows
     set ANTHROPIC_API_KEY=sk-ant-...
     python app.py

     # macOS / Linux
     export ANTHROPIC_API_KEY=sk-ant-...
     python app.py

3. In the app:
   ▸ Paste your Anthropic API key in the top bar
   ▸ Click "BROWSE IMAGE" to select a road sign photo
   ▸ Click "ANALYZE" to run the AI analysis
   ▸ View the full retroreflectivity report on the right panel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPPORTED IMAGE FORMATS
───────────────────────
  JPG / JPEG / PNG / WEBP / BMP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TROUBLESHOOTING
───────────────
  ✗ "tkinter not found"  →  Install python3-tk:
       Ubuntu/Debian:  sudo apt install python3-tk
       macOS:          brew install python-tk
       Windows:        Re-install Python with tcl/tk option

  ✗ "API error"          →  Check your API key is valid and
                             you have sufficient credits.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROJECT STRUCTURE
─────────────────
  retroreflect_ai/
  ├── app.py            ← Main application (single file)
  ├── requirements.txt  ← Python dependencies
  └── README.txt        ← This file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RETROREFLECT·AI  •  POWERED BY CLAUDE AI  •  2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
