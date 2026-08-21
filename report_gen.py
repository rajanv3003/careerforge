#!/usr/bin/env python3
"""CareerForge — ₹1 Cr Career Intelligence Report. Graphical, consulting-grade PDF.
Usage: python3 report_gen.py <intel_json_path> <out_html_path> <name> <date>
The intel_json_path file is {"output": {...intel...}} OR the intel object directly."""
import json, base64, os, math, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
bench = json.load(open(os.path.join(ROOT, "data", "benchmarks.json")))

INTEL_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "intel.json")
OUT_HTML   = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "report.html")
NAME       = sys.argv[3] if len(sys.argv) > 3 else "Rajat Sharma"
DATE       = sys.argv[4] if len(sys.argv) > 4 else "August 2026"
COVER_PATH = os.path.join(ROOT, "data", "brand_cover.png")

_raw = json.load(open(INTEL_PATH))
intel = _raw.get("output", _raw)

# ---------- helpers ----------
def inr(n):
    n = int(n or 0)
    if n >= 10000000: return f"₹{n/10000000:.2f} Cr"
    if n >= 100000:   return f"₹{n/100000:.0f} L"
    return f"₹{n:,}"

W = {d["key"]: d["weight"] for d in bench["competency_dimensions"]}
LAB = {d["key"]: d["label"] for d in bench["competency_dimensions"]}
dims = intel["dimensions"]
overall = round(sum(d["score"] * W.get(d["key"], 0) for d in dims))
band = next(b for b in bench["readiness_bands"] if overall >= b["min"])

RED, EMBER, INK, MUT, LINE, BG2 = "#ED383B", "#FF6A3D", "#101218", "#6b7080", "#e7e9ef", "#f5f6fa"
def sc(v): return "#12b76a" if v>=80 else ("#f59e0b" if v>=60 else RED)  # score color

# ---------- gauge (270° arc) ----------
def gauge(score, cx=110, cy=110, r=88):
    start, sweep = 135, 270
    def pt(ang, rr):
        a = math.radians(ang); return cx + rr*math.cos(a), cy + rr*math.sin(a)
    def arc(frac, color, w):
        a0 = start; a1 = start + sweep*frac
        x0,y0 = pt(a0, r); x1,y1 = pt(a1, r)
        large = 1 if (a1-a0) > 180 else 0
        return f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {large} 1 {x1:.1f} {y1:.1f}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
    col = sc(score)
    return f'''<svg width="220" height="200" viewBox="0 0 220 210">
      {arc(1, "#edeff4", 16)}
      {arc(score/100, col, 16)}
      <text x="{cx}" y="{cy+6}" text-anchor="middle" font-family="Archivo" font-weight="800" font-size="52" fill="{INK}">{score}</text>
      <text x="{cx}" y="{cy+30}" text-anchor="middle" font-family="Inter" font-size="12" fill="{MUT}" letter-spacing="1">/ 100</text>
    </svg>'''

# ---------- radar (hexagon) ----------
def radar(dims, cx=165, cy=150, r=105):
    n = len(dims); pts_out=[]; pts_val=[]; labels=""
    for i,d in enumerate(dims):
        ang = math.radians(-90 + i*360/n)
        ox, oy = cx+r*math.cos(ang), cy+r*math.sin(ang)
        vr = r*d["score"]/100
        vx, vy = cx+vr*math.cos(ang), cy+vr*math.sin(ang)
        pts_out.append((ox,oy)); pts_val.append((vx,vy))
        lx, ly = cx+(r+22)*math.cos(ang), cy+(r+22)*math.sin(ang)
        anc = "middle" if abs(math.cos(ang))<0.3 else ("start" if math.cos(ang)>0 else "end")
        short = {"impact_scale":"Impact","leadership":"Leadership","domain_depth":"Domain","strategic":"Strategic","brand_visibility":"Brand","communication":"Comms"}.get(d["key"], LAB[d["key"]])
        labels += f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="{anc}" font-family="Archivo" font-weight="600" font-size="12" fill="{INK}">{short}</text>'
        labels += f'<text x="{lx:.0f}" y="{ly+13:.0f}" text-anchor="{anc}" font-family="Inter" font-size="10" fill="{sc(d["score"])}" font-weight="700">{d["score"]}</text>'
    rings=""
    for f in (0.25,0.5,0.75,1.0):
        rp = " ".join(f"{cx+r*f*math.cos(math.radians(-90+i*360/n)):.0f},{cy+r*f*math.sin(math.radians(-90+i*360/n)):.0f}" for i in range(n))
        rings += f'<polygon points="{rp}" fill="none" stroke="{LINE}" stroke-width="1"/>'
    spokes = "".join(f'<line x1="{cx}" y1="{cy}" x2="{o[0]:.0f}" y2="{o[1]:.0f}" stroke="{LINE}" stroke-width="1"/>' for o in pts_out)
    val = " ".join(f"{p[0]:.0f},{p[1]:.0f}" for p in pts_val)
    dots = "".join(f'<circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="3.5" fill="{RED}"/>' for p in pts_val)
    return f'''<svg width="330" height="300" viewBox="-60 -5 400 310">{rings}{spokes}
      <polygon points="{val}" fill="{RED}" fill-opacity="0.16" stroke="{RED}" stroke-width="2.5"/>{dots}{labels}</svg>'''

# ---------- score bar ----------
def bar(score, w=150):
    return f'<div style="height:8px;width:{w}px;background:#edeff4;border-radius:5px;overflow:hidden;display:inline-block;vertical-align:middle"><div style="height:100%;width:{score*w/100:.0f}px;background:{sc(score)}"></div></div>'

# ---------- compensation chart ----------
def comp_chart(c):
    lo, hi = c["market_low_inr"], c["market_high_inr"]
    cur, tgt = c["current_estimate_inr"], c["target_estimate_inr"]
    thr = bench["salary_bands_inr"]["cr_threshold"]
    span = max(hi, tgt, thr)*1.08; x0=70; W=430
    def X(v): return x0 + (v/span)*W
    def marker(v,color,label,dy):
        x=X(v)
        return (f'<line x1="{x:.0f}" y1="34" x2="{x:.0f}" y2="86" stroke="{color}" stroke-width="2.5"/>'
                f'<circle cx="{x:.0f}" cy="60" r="5" fill="{color}"/>'
                f'<text x="{x:.0f}" y="{dy}" text-anchor="middle" font-family="Archivo" font-weight="700" font-size="11" fill="{color}">{label}</text>')
    thx=X(thr)
    return f'''<svg width="530" height="120" viewBox="0 0 530 120">
      <rect x="{X(lo):.0f}" y="50" width="{X(hi)-X(lo):.0f}" height="20" rx="10" fill="#e9ebf1"/>
      <text x="{X(lo):.0f}" y="86" font-family="Inter" font-size="10" fill="{MUT}">{inr(lo)}</text>
      <text x="{X(hi):.0f}" y="86" text-anchor="end" font-family="Inter" font-size="10" fill="{MUT}">{inr(hi)}</text>
      <line x1="{thx:.0f}" y1="20" x2="{thx:.0f}" y2="92" stroke="{EMBER}" stroke-width="1.5" stroke-dasharray="4 3"/>
      <text x="{thx:.0f}" y="16" text-anchor="middle" font-family="Archivo" font-weight="800" font-size="10" fill="{EMBER}">₹1 Cr line</text>
      {marker(cur, MUT, "Today "+inr(cur), 30)}
      {marker(tgt, RED, "Target "+inr(tgt), 108)}
      <text x="10" y="63" font-family="Inter" font-size="10" fill="{MUT}">Market</text>
    </svg>'''

cover_b64 = base64.b64encode(open(COVER_PATH,"rb").read()).decode()

# dimension rows
dim_rows = ""
for d in sorted(dims, key=lambda x:-x["score"]):
    dim_rows += f'''<tr>
      <td style="font-family:Archivo;font-weight:600;color:{INK};width:112px">{LAB[d["key"]]}<br>{bar(d["score"],86)} <b style="color:{sc(d["score"])};font-family:Archivo">{d["score"]}</b></td>
      <td style="color:#3a3d48;font-size:10.5px">{d["evidence"]}<div style="color:{RED};font-size:10px;margin-top:2px">▲ {d["gap"]}</div></td>
    </tr>'''

kw = intel["keyword_coverage"]
present = "".join(f'<span class="chip good">{k}</span>' for k in kw.get("present",[]))
missing = "".join(f'<span class="chip bad">{k}</span>' for k in kw.get("missing",[]))
cov = round(100*len(kw.get("present",[]))/max(1,len(kw.get("present",[]))+len(kw.get("missing",[]))))
sig = "".join(f'<li>{s}</li>' for s in intel.get("missing_cr_signals",[]))
rec = "".join(f'<div class="reccard">{r}</div>' for r in intel.get("recruiter_view",[]))
road = ""
for r in intel.get("roadmap",[]):
    acts = "".join(f'<li>{a}</li>' for a in r["actions"])
    road += f'<div class="rd"><div class="rdh">{r["horizon"]}</div><ul>{acts}</ul></div>'

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ margin:0; font-family:'Inter',sans-serif; color:{INK}; }}
.page {{ width:210mm; min-height:297mm; page-break-after:always; position:relative; padding:22mm 20mm; }}
.page:last-child {{ page-break-after:auto; }}
.kicker {{ display:flex; align-items:center; gap:11px; margin-bottom:5px; }}
.kicker .tab {{ width:26px; height:5px; border-radius:3px; background:linear-gradient(90deg,{RED},{EMBER}); }}
.kicker span {{ font-family:'Archivo'; font-weight:700; font-size:11px; letter-spacing:.24em; text-transform:uppercase; color:{RED}; }}
h1.sec {{ font-family:'Archivo'; font-weight:800; font-size:27px; letter-spacing:-.5px; margin:0 0 3px; }}
.lead {{ font-family:'Source Serif 4'; font-size:13px; color:{MUT}; margin:0 0 16px; }}
hr {{ border:none; border-top:1px solid {LINE}; margin:14px 0; }}
.foot {{ position:absolute; bottom:12mm; left:20mm; right:20mm; display:flex; justify-content:space-between; font-size:9px; color:#9aa0b0; border-top:1px solid {LINE}; padding-top:7px; }}
.foot b {{ color:{RED}; font-family:Archivo; }}
.chip {{ display:inline-block; border-radius:100px; padding:4px 11px; font-size:11px; margin:3px 4px 0 0; }}
.chip.good {{ background:rgba(18,183,106,.1); color:#0f9257; }}
.chip.bad {{ background:rgba(237,56,59,.08); color:{RED}; border:1px solid rgba(237,56,59,.25); }}
table {{ border-collapse:collapse; width:100%; }}
td {{ padding:6px 7px; border-bottom:1px solid #eef0f4; vertical-align:top; font-size:11px; }}

/* cover */
.cover {{ background:#08080A; color:#fff; padding:0; overflow:hidden; }}
.cover .bg {{ position:absolute; inset:0; }} .cover .bg img {{ width:100%; height:100%; object-fit:cover; opacity:.88; }}
.cover .veil {{ position:absolute; inset:0; background:linear-gradient(180deg,rgba(8,8,10,.4),rgba(8,8,10,.7) 60%,rgba(8,8,10,.96)); }}
.cover .in {{ position:absolute; inset:0; padding:24mm 20mm; display:flex; flex-direction:column; justify-content:flex-end; }}
.cover .brand {{ position:absolute; top:20mm; left:20mm; display:flex; align-items:center; gap:10px; }}
.cover .brand .m {{ width:32px; height:32px; border-radius:9px; background:linear-gradient(135deg,{RED},{EMBER}); }}
.cover .brand .t {{ font-family:'Archivo'; font-weight:800; font-size:15px; }}
.cover .eb {{ font-family:'Archivo'; font-weight:700; font-size:12px; letter-spacing:.3em; text-transform:uppercase; color:{EMBER}; margin-bottom:12px; }}
.cover h1 {{ font-family:'Archivo'; font-weight:800; font-size:44px; line-height:1.03; margin:0 0 8px; letter-spacing:-1px; }}
.cover .role {{ font-family:'Source Serif 4'; font-style:italic; font-size:19px; color:#e7c6b6; margin-bottom:22px; }}
.cover .meta {{ display:flex; gap:30px; border-top:1px solid rgba(255,255,255,.16); padding-top:14px; }}
.cover .meta span {{ display:block; font-size:9px; letter-spacing:.2em; text-transform:uppercase; color:rgba(255,255,255,.5); margin-bottom:3px; }}
.cover .meta b {{ font-family:'Archivo'; font-weight:600; font-size:13px; }}

/* exec */
.exec {{ display:flex; gap:24px; align-items:center; }}
.gaugebox {{ text-align:center; flex-shrink:0; }}
.bandlbl {{ font-family:'Archivo'; font-weight:800; font-size:16px; color:{sc(overall)}; margin-top:-6px; }}
.verdict {{ font-family:'Source Serif 4'; font-size:14px; line-height:1.5; color:#2a2d38; }}
.tiles {{ display:flex; gap:12px; margin:16px 0; }}
.tile {{ flex:1; border:1px solid {LINE}; border-radius:12px; padding:13px 15px; background:{BG2}; }}
.tile span {{ font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; color:{MUT}; }}
.tile b {{ display:block; font-family:'Archivo'; font-weight:700; font-size:16px; margin-top:4px; color:{INK}; }}
.quote {{ border-left:3px solid {RED}; padding:8px 16px; font-family:'Source Serif 4'; font-style:italic; font-size:15px; color:{INK}; margin:14px 0; }}
.reccard {{ background:{BG2}; border:1px solid {LINE}; border-left:3px solid {EMBER}; border-radius:8px; padding:10px 13px; font-size:12px; margin-bottom:8px; color:#2a2d38; }}
.rd {{ border:1px solid {LINE}; border-radius:12px; padding:14px 16px; margin-bottom:11px; }}
.rd .rdh {{ font-family:'Archivo'; font-weight:800; font-size:14px; color:{RED}; margin-bottom:5px; }}
.rd ul {{ margin:0; padding-left:17px; }} .rd li {{ font-size:12px; margin:4px 0; color:#2a2d38; }}
ul.sig {{ padding-left:17px; }} ul.sig li {{ font-size:12px; margin:5px 0; }}
.two {{ display:flex; gap:26px; }}
</style></head><body>

<section class="page cover">
  <div class="bg"><img src="data:image/png;base64,{cover_b64}"></div><div class="veil"></div>
  <div class="brand"><div class="m"></div><div class="t">CareerForge</div></div>
  <div class="in">
    <div class="eb">₹1 Crore Career Intelligence</div>
    <h1>{NAME}</h1>
    <div class="role">{intel['role_family']} — readiness assessment & path to ₹1 Cr</div>
    <div class="meta">
      <div><span>Report date</span><b>{DATE}</b></div>
      <div><span>Readiness</span><b>{overall}/100 · {band['label']}</b></div>
      <div><span>Target CTC</span><b>{inr(intel['compensation']['target_estimate_inr'])}</b></div>
    </div>
  </div>
</section>

<section class="page">
  <div class="kicker"><div class="tab"></div><span>Executive Summary</span></div>
  <h1 class="sec">Your ₹1 Cr Readiness</h1>
  <p class="lead">A single, honest score of how you read against the ₹1 Cr bar today — and exactly where the points are.</p>
  <div class="exec">
    <div class="gaugebox">{gauge(overall)}<div class="bandlbl">{band['label']}</div></div>
    <div><div class="verdict">{band['verdict']}</div>
      <div class="quote">{intel['headline']}</div></div>
  </div>
  <div class="tiles">
    <div class="tile"><span>Reads at today</span><b>{intel['current_tier']}</b></div>
    <div class="tile"><span>Target level</span><b>{intel['target_tier']}</b></div>
    <div class="tile"><span>Comp potential</span><b>{inr(intel['compensation']['current_estimate_inr'])} → {inr(intel['compensation']['target_estimate_inr'])}</b></div>
  </div>
  <hr>
  <div class="kicker"><div class="tab"></div><span>First 10 seconds</span></div>
  <p class="lead" style="margin-bottom:10px">What a top recruiter notices before they decide to read on.</p>
  {rec}
  <div class="foot"><span>CareerForge · ₹1 Cr Career Intelligence</span><span>Confidential — <b>{NAME}</b></span></div>
</section>

<section class="page">
  <div class="kicker"><div class="tab"></div><span>Competency Diagnostic</span></div>
  <h1 class="sec">The Six Dimensions</h1>
  <p class="lead">Scored against our ₹1 Cr benchmark. The shape shows where you're strong — and where the story thins out.</p>
  <div class="two">
    <div style="flex-shrink:0">{radar(dims)}</div>
    <div style="flex:1;padding-top:10px"><table>{dim_rows}</table></div>
  </div>
  <div class="foot"><span>CareerForge · ₹1 Cr Career Intelligence</span><span>Competency Diagnostic</span></div>
</section>

<section class="page">
  <div class="kicker"><div class="tab"></div><span>Positioning & Compensation</span></div>
  <h1 class="sec">Keywords, Signals & Money</h1>
  <p class="lead">Where you sit in the market — and the levers that move your number.</p>
  <b style="font-family:Archivo;font-size:13px">Job-match keyword coverage — {cov}%</b>
  <div style="margin:8px 0 4px">{present}{missing}</div>
  <hr>
  <b style="font-family:Archivo;font-size:13px">Compensation intelligence</b>
  <div style="margin:6px 0">{comp_chart(intel['compensation'])}</div>
  <div class="reccard" style="border-left-color:{RED}"><b>Your biggest lever:</b> {intel['compensation']['leverage']}</div>
  <hr>
  <b style="font-family:Archivo;font-size:13px;color:{RED}">Missing ₹1 Cr signals</b>
  <ul class="sig">{sig}</ul>
  <div class="foot"><span>CareerForge · ₹1 Cr Career Intelligence</span><span>Positioning & Compensation</span></div>
</section>

<section class="page">
  <div class="kicker"><div class="tab"></div><span>The Path</span></div>
  <h1 class="sec">Your ₹1 Cr Roadmap</h1>
  <p class="lead">Not advice — a sequence. Do these, in this order, and the score above moves.</p>
  {road}
  <div class="foot"><span>CareerForge · ₹1 Cr Career Intelligence</span><span>Prepared by CareerForge · Career OS</span></div>
</section>

</body></html>"""
open(OUT_HTML,"w").write(HTML)
print(json.dumps({"overall":overall,"band":band["label"],"html":OUT_HTML}))
