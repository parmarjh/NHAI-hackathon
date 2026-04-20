# 🔆 RetroReflect·AI v3.0

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![YOLOv8](https://img.shields.io/badge/Vision-YOLOv8-FFCC00?style=for-the-badge&logo=googlesheets&logoColor=black)](https://ultralytics.com)
[![Claude AI](https://img.shields.io/badge/AI-Claude%203.5-7A98B8?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-00ff88?style=for-the-badge)](LICENSE)

**Unified Highway Health Intelligence Platform** — Designed for NHAI audit teams to perform high-speed road safety surveys at 100km/h.

---

## ◈ The Vision
Traditional road auditing is slow, manual, and dangerous. **RetroReflect·AI** transforms standard vehicle or drone footage into actionable safety intelligence using a dual-engine AI approach. 

- **Level 1 (Local):** YOLOv8 Real-Time Vision Engine detects potholes, cracks, and safety signs at 30+ FPS.
- **Level 2 (Cloud):** Multi-model failover (Claude 3.5 / Gemini 1.5) provides deep radiometric analysis for IRC 67/35 compliance.

---

## ⚡ Core Capabilities

- 🛣️ **Real-Time Highway Audit**: Process live camera feeds from vehicle-mounted sensors.
- 🚧 **Structural Health Detection**: Autonomous identification of potholes, cracks, ravelling, and edge failures.
- 🔆 **AI Retroreflectivity Scoring**: Precise 0–100 index for road signs and markings.
- 🛰️ **Environmental Monitoring**: Detection of water-logging, dust, and debris.
- 📊 **Dynamic Dashboard**: Cyberpunk-themed telemetry HUD with animated gauges and metrics.
- 🔄 **Multi-Tiered Failover**: Auto-switches between 4 AI providers (Gemini → Claude → GPT-4o → OpenRouter) to ensure 100% uptime.

---

## 📦 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **API Key** (Anthropic, Google, or OpenAI)
- **Webcam/Camera** (for live testing)

### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/your-username/nhai-hackathon.git
cd nhai-hackathon

# Install heavy-duty dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root:
```env
GOOGLE_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 4. Launch
```powershell
# Launch the main Enterprise Dashboard
python app.py

# Launch the standalone high-speed Vision Engine
python vision_fast.py
```

---

## 🏗️ System Architecture

The platform is built as a hybrid edge-cloud system:
1. **Edge (Local PC):** Handles raw video frame extraction and YOLO-based object detection.
2. **Intelligence layer:** Cascades filtered frames to the highest available Vision API for depth analysis.
3. **Control Center:** A high-performance Python Tkinter GUI manages the telemetry and history logging.

---

## 📂 Repository Structure
```text
.
├── app.py              # Main Intelligence Hub (GUI)
├── vision_fast.py      # High-Speed Real-time CV Engine
├── yolov8n.pt          # Pre-trained Vision Model
├── .env                # API Configuration (Template)
├── requirements.txt    # Heavy-duty dependencies
├── README.html         # Enterprise Stakeholder Portal (Full Landing Page)
└── LICENSE             # MIT License
```

---

## ◈ Mission
**NHAI HACKATHON 2025**  
*Building safer Indian highways through automated 3D geometric intelligence and neural surface auditing.*

---
© 2026 RETROREFLECT·AI • MIT LICENSE • POWERED BY CLAUDE AI • v3.0.0
