import { useState, useRef, useCallback } from "react";

const GRADES = [
  { min: 85, label: "EXCELLENT", color: "#00ff88", desc: "Fully compliant. Optimal night visibility." },
  { min: 65, label: "GOOD", color: "#aaff00", desc: "Meets standards. Minor degradation noted." },
  { min: 40, label: "FAIR", color: "#ffcc00", desc: "Below optimal. Maintenance recommended soon." },
  { min: 20, label: "POOR", color: "#ff8800", desc: "Fails standards. Immediate action required." },
  { min: 0,  label: "CRITICAL", color: "#ff2244", desc: "Dangerous. Replace immediately." },
];

function getGrade(score) {
  return GRADES.find(g => score >= g.min) || GRADES[GRADES.length - 1];
}

const SYSTEM_PROMPT = `You are an expert road safety engineer specializing in retroreflectivity measurement systems. When given an image of a road sign or road marking, analyze it for retroreflectivity and nighttime visibility.

Return ONLY a valid JSON object with these exact fields (no markdown, no extra text):
{
  "score": <integer 0-100 retroreflectivity score>,
  "surfaceType": "<Road Sign | Road Marking | Pavement | Other>",
  "material": "<estimated material e.g. Type III Sheeting, Glass Bead, Paint, etc.>",
  "colorDetected": "<primary color of sign/marking>",
  "degradationLevel": "<None | Low | Moderate | High | Severe>",
  "estimatedAge": "<estimated age range e.g. 0-2 years, 3-5 years, etc.>",
  "visibilityDistance": "<estimated visibility distance at night e.g. 150m, 80m, etc.>",
  "issues": ["<issue1>", "<issue2>"],
  "recommendations": ["<recommendation1>", "<recommendation2>"],
  "complianceStatus": "<Compliant | Non-Compliant | Borderline>",
  "urgency": "<Immediate | Within 3 months | Within 1 year | No action needed>",
  "summary": "<2-sentence expert analysis>"
}`;

export default function RetroApp() {
  const [image, setImage] = useState(null);
  const [imageBase64, setImageBase64] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [scanLine, setScanLine] = useState(0);
  const fileRef = useRef();
  const scanRef = useRef(null);

  const startScan = () => {
    let pos = 0;
    if (scanRef.current) clearInterval(scanRef.current);
    scanRef.current = setInterval(() => {
      pos = (pos + 1) % 101;
      setScanLine(pos);
    }, 30);
  };

  const stopScan = () => {
    if (scanRef.current) clearInterval(scanRef.current);
    setScanLine(0);
  };

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith("image/")) return;
    setResult(null);
    setError(null);
    const url = URL.createObjectURL(file);
    setImage(url);
    const reader = new FileReader();
    reader.onload = (e) => setImageBase64(e.target.result.split(",")[1]);
    reader.readAsDataURL(file);
  }, []);

  const analyze = async () => {
    if (!imageBase64) return;
    setLoading(true);
    setError(null);
    setResult(null);
    startScan();

    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: SYSTEM_PROMPT,
          messages: [{
            role: "user",
            content: [
              { type: "image", source: { type: "base64", media_type: "image/jpeg", data: imageBase64 } },
              { type: "text", text: "Analyze this road sign or marking for retroreflectivity. Respond only with the JSON object." }
            ]
          }]
        })
      });

      const data = await response.json();
      const text = data.content?.map(i => i.text || "").join("") || "";
      const clean = text.replace(/```json|```/g, "").trim();
      const parsed = JSON.parse(clean);
      setResult(parsed);
    } catch (err) {
      setError("Analysis failed. Please try a clearer image of a road sign or marking.");
    } finally {
      setLoading(false);
      stopScan();
    }
  };

  const grade = result ? getGrade(result.score) : null;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#050a12",
      fontFamily: "'Courier New', monospace",
      color: "#c8d8e8",
      padding: "0",
      overflow: "hidden auto",
      position: "relative"
    }}>
      {/* Grid background */}
      <div style={{
        position: "fixed", inset: 0, zIndex: 0,
        backgroundImage: `
          linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px)
        `,
        backgroundSize: "40px 40px",
        pointerEvents: "none"
      }} />

      {/* Glow orbs */}
      <div style={{ position: "fixed", top: "-100px", left: "-100px", width: "400px", height: "400px", borderRadius: "50%", background: "radial-gradient(circle, rgba(255,220,0,0.06) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "fixed", bottom: "-100px", right: "-100px", width: "500px", height: "500px", borderRadius: "50%", background: "radial-gradient(circle, rgba(0,180,255,0.05) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />

      <div style={{ position: "relative", zIndex: 1, maxWidth: "900px", margin: "0 auto", padding: "24px 16px" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px", marginBottom: "8px" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#ffdd00", boxShadow: "0 0 12px #ffdd00", animation: "pulse 2s infinite" }} />
            <span style={{ fontSize: "11px", letterSpacing: "4px", color: "#ffdd00", textTransform: "uppercase" }}>AI-POWERED SYSTEM</span>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#ffdd00", boxShadow: "0 0 12px #ffdd00", animation: "pulse 2s infinite" }} />
          </div>
          <h1 style={{ fontSize: "clamp(22px,5vw,36px)", fontWeight: "900", letterSpacing: "3px", color: "#fff", margin: "0 0 6px", textTransform: "uppercase" }}>
            RETRO<span style={{ color: "#ffdd00" }}>REFLECT</span>·AI
          </h1>
          <p style={{ fontSize: "13px", color: "#6a8aaa", letterSpacing: "2px", margin: 0 }}>
            SMART RETROREFLECTIVITY MEASUREMENT SYSTEM
          </p>
          <div style={{ width: "200px", height: "1px", background: "linear-gradient(90deg, transparent, #ffdd00, transparent)", margin: "16px auto 0" }} />
        </div>

        {/* Upload Zone */}
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
          style={{
            border: `2px dashed ${dragOver ? "#ffdd00" : image ? "#00ccff" : "#1e3050"}`,
            borderRadius: "12px",
            padding: image ? "12px" : "40px 20px",
            cursor: "pointer",
            transition: "all 0.3s",
            background: dragOver ? "rgba(255,220,0,0.04)" : "rgba(5,15,30,0.8)",
            position: "relative",
            overflow: "hidden",
            textAlign: "center",
            marginBottom: "20px"
          }}
        >
          <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={e => handleFile(e.target.files[0])} />

          {image ? (
            <div style={{ position: "relative", display: "inline-block", maxWidth: "100%" }}>
              <img src={image} alt="Upload" style={{ maxHeight: "280px", maxWidth: "100%", borderRadius: "8px", display: "block" }} />
              {/* Scan line */}
              {loading && (
                <div style={{
                  position: "absolute", left: 0, right: 0,
                  top: `${scanLine}%`,
                  height: "3px",
                  background: "linear-gradient(90deg, transparent, #00ffcc, #ffdd00, #00ffcc, transparent)",
                  boxShadow: "0 0 20px #00ffcc",
                  transition: "top 0.03s linear",
                  pointerEvents: "none"
                }} />
              )}
              {/* Corner markers */}
              {["0,0", "0,auto", "auto,0", "auto,auto"].map((pos, i) => {
                const [t, b] = pos.split(",");
                return (
                  <div key={i} style={{
                    position: "absolute", width: "16px", height: "16px",
                    top: t !== "auto" ? t : undefined,
                    bottom: b !== "auto" ? b : undefined,
                    left: i % 2 === 0 ? "0" : undefined,
                    right: i % 2 === 1 ? "0" : undefined,
                    borderTop: i < 2 ? "2px solid #ffdd00" : undefined,
                    borderBottom: i >= 2 ? "2px solid #ffdd00" : undefined,
                    borderLeft: i % 2 === 0 ? "2px solid #ffdd00" : undefined,
                    borderRight: i % 2 === 1 ? "2px solid #ffdd00" : undefined,
                  }} />
                );
              })}
              <div style={{ marginTop: "10px", fontSize: "11px", color: "#4a7090", letterSpacing: "2px" }}>CLICK TO CHANGE IMAGE</div>
            </div>
          ) : (
            <>
              <div style={{ fontSize: "48px", marginBottom: "12px" }}>🔆</div>
              <div style={{ fontSize: "15px", color: "#aac0d8", marginBottom: "6px", fontWeight: "bold" }}>DROP ROAD SIGN / MARKING IMAGE</div>
              <div style={{ fontSize: "12px", color: "#3a5a78", letterSpacing: "2px" }}>OR CLICK TO UPLOAD • JPG / PNG / WEBP</div>
            </>
          )}
        </div>

        {/* Analyze Button */}
        <button
          onClick={analyze}
          disabled={!image || loading}
          style={{
            width: "100%",
            padding: "16px",
            background: !image || loading ? "#0d1f30" : "linear-gradient(135deg, #ffdd00, #ffaa00)",
            border: "none",
            borderRadius: "10px",
            color: !image || loading ? "#3a5a78" : "#0a0a0a",
            fontSize: "14px",
            fontWeight: "900",
            letterSpacing: "4px",
            cursor: !image || loading ? "not-allowed" : "pointer",
            textTransform: "uppercase",
            marginBottom: "28px",
            transition: "all 0.3s",
            boxShadow: !image || loading ? "none" : "0 0 30px rgba(255,220,0,0.3)",
            fontFamily: "'Courier New', monospace"
          }}
        >
          {loading ? "⟳  ANALYZING RETROREFLECTIVITY..." : "▶  ANALYZE WITH AI"}
        </button>

        {error && (
          <div style={{ background: "rgba(255,30,60,0.08)", border: "1px solid rgba(255,30,60,0.3)", borderRadius: "8px", padding: "14px 16px", marginBottom: "20px", fontSize: "13px", color: "#ff6680" }}>
            ⚠ {error}
          </div>
        )}

        {/* Results */}
        {result && grade && (
          <div style={{ animation: "fadeIn 0.5s ease" }}>

            {/* Score Hero */}
            <div style={{
              background: "rgba(5,15,28,0.9)",
              border: `1px solid ${grade.color}44`,
              borderRadius: "14px",
              padding: "28px 24px",
              marginBottom: "16px",
              textAlign: "center",
              position: "relative",
              overflow: "hidden"
            }}>
              <div style={{ position: "absolute", inset: 0, background: `radial-gradient(circle at 50% 50%, ${grade.color}08, transparent 70%)`, pointerEvents: "none" }} />
              <div style={{ fontSize: "11px", letterSpacing: "4px", color: "#6a8aaa", marginBottom: "12px" }}>RETROREFLECTIVITY INDEX</div>

              {/* Score ring */}
              <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: "12px" }}>
                <svg width="140" height="140" viewBox="0 0 140 140">
                  <circle cx="70" cy="70" r="60" fill="none" stroke="#0d1f30" strokeWidth="10" />
                  <circle cx="70" cy="70" r="60" fill="none" stroke={grade.color}
                    strokeWidth="10"
                    strokeDasharray={`${2 * Math.PI * 60 * result.score / 100} ${2 * Math.PI * 60}`}
                    strokeLinecap="round"
                    strokeDashoffset={2 * Math.PI * 60 * 0.25}
                    style={{ filter: `drop-shadow(0 0 8px ${grade.color})`, transition: "stroke-dasharray 1s ease" }}
                  />
                </svg>
                <div style={{ position: "absolute", textAlign: "center" }}>
                  <div style={{ fontSize: "38px", fontWeight: "900", color: grade.color, lineHeight: 1 }}>{result.score}</div>
                  <div style={{ fontSize: "10px", color: "#4a6a88", letterSpacing: "2px" }}>/ 100</div>
                </div>
              </div>

              <div style={{ fontSize: "22px", fontWeight: "900", letterSpacing: "6px", color: grade.color, marginBottom: "6px" }}>{grade.label}</div>
              <div style={{ fontSize: "13px", color: "#7a9ab8" }}>{grade.desc}</div>

              {/* Status badge */}
              <div style={{
                display: "inline-block", marginTop: "14px", padding: "6px 18px",
                background: result.complianceStatus === "Compliant" ? "rgba(0,255,136,0.1)" : result.complianceStatus === "Non-Compliant" ? "rgba(255,34,68,0.1)" : "rgba(255,200,0,0.1)",
                border: `1px solid ${result.complianceStatus === "Compliant" ? "#00ff88" : result.complianceStatus === "Non-Compliant" ? "#ff2244" : "#ffcc00"}`,
                borderRadius: "20px", fontSize: "11px", letterSpacing: "3px", fontWeight: "bold",
                color: result.complianceStatus === "Compliant" ? "#00ff88" : result.complianceStatus === "Non-Compliant" ? "#ff4466" : "#ffcc00"
              }}>
                {result.complianceStatus === "Compliant" ? "✓" : "✗"} {result.complianceStatus?.toUpperCase()}
              </div>
            </div>

            {/* Metrics Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
              {[
                { icon: "🪟", label: "Surface Type", value: result.surfaceType },
                { icon: "🧪", label: "Material", value: result.material },
                { icon: "🎨", label: "Color Detected", value: result.colorDetected },
                { icon: "📉", label: "Degradation", value: result.degradationLevel },
                { icon: "📅", label: "Est. Age", value: result.estimatedAge },
                { icon: "🔦", label: "Night Visibility", value: result.visibilityDistance },
              ].map(m => (
                <div key={m.label} style={{
                  background: "rgba(8,20,38,0.9)",
                  border: "1px solid #0d2040",
                  borderRadius: "10px",
                  padding: "14px"
                }}>
                  <div style={{ fontSize: "10px", color: "#4a6888", letterSpacing: "2px", marginBottom: "6px" }}>{m.icon} {m.label.toUpperCase()}</div>
                  <div style={{ fontSize: "14px", color: "#d0e8ff", fontWeight: "bold" }}>{m.value || "—"}</div>
                </div>
              ))}
            </div>

            {/* Urgency Banner */}
            <div style={{
              background: result.urgency === "Immediate" ? "rgba(255,30,60,0.08)" : result.urgency === "Within 3 months" ? "rgba(255,136,0,0.08)" : "rgba(0,255,136,0.05)",
              border: `1px solid ${result.urgency === "Immediate" ? "#ff2244" : result.urgency === "Within 3 months" ? "#ff8800" : "#00ff88"}44`,
              borderRadius: "10px",
              padding: "14px 18px",
              marginBottom: "16px",
              display: "flex",
              alignItems: "center",
              gap: "12px"
            }}>
              <div style={{ fontSize: "22px" }}>{result.urgency === "Immediate" ? "🚨" : result.urgency === "Within 3 months" ? "⚠️" : "✅"}</div>
              <div>
                <div style={{ fontSize: "10px", color: "#6a8aaa", letterSpacing: "3px", marginBottom: "3px" }}>ACTION URGENCY</div>
                <div style={{ fontSize: "15px", fontWeight: "bold", color: result.urgency === "Immediate" ? "#ff4466" : result.urgency === "Within 3 months" ? "#ffaa44" : "#00ff88" }}>
                  {result.urgency}
                </div>
              </div>
            </div>

            {/* Issues & Recommendations */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
              <div style={{ background: "rgba(8,20,38,0.9)", border: "1px solid #1a0010", borderRadius: "10px", padding: "16px" }}>
                <div style={{ fontSize: "10px", color: "#ff4466", letterSpacing: "3px", marginBottom: "12px" }}>⚠ ISSUES DETECTED</div>
                {(result.issues || []).map((iss, i) => (
                  <div key={i} style={{ fontSize: "12px", color: "#c0a8b0", marginBottom: "8px", paddingLeft: "10px", borderLeft: "2px solid #ff224440" }}>
                    {iss}
                  </div>
                ))}
              </div>
              <div style={{ background: "rgba(8,20,38,0.9)", border: "1px solid #001a10", borderRadius: "10px", padding: "16px" }}>
                <div style={{ fontSize: "10px", color: "#00ff88", letterSpacing: "3px", marginBottom: "12px" }}>✦ RECOMMENDATIONS</div>
                {(result.recommendations || []).map((rec, i) => (
                  <div key={i} style={{ fontSize: "12px", color: "#a8c0b0", marginBottom: "8px", paddingLeft: "10px", borderLeft: "2px solid #00ff8840" }}>
                    {rec}
                  </div>
                ))}
              </div>
            </div>

            {/* AI Summary */}
            <div style={{
              background: "rgba(8,20,38,0.9)",
              border: "1px solid #0d2040",
              borderRadius: "10px",
              padding: "18px",
              marginBottom: "28px"
            }}>
              <div style={{ fontSize: "10px", color: "#ffdd00", letterSpacing: "3px", marginBottom: "10px" }}>◈ AI EXPERT ANALYSIS</div>
              <p style={{ fontSize: "13px", color: "#9ab8d0", lineHeight: "1.7", margin: 0 }}>{result.summary}</p>
            </div>

          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: "center", fontSize: "10px", color: "#1e3050", letterSpacing: "3px", paddingBottom: "20px" }}>
          RETROREFLECT·AI • SMART ROAD SAFETY SYSTEM • POWERED BY CLAUDE AI
        </div>
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
      `}</style>
    </div>
  );
}
