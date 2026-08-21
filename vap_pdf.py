#!/usr/bin/env python3
"""CareerForge — Value-Added Project (VAP) PDF. Authority-building, company-specific.
Usage: python3 vap_pdf.py <vap_json_path> <out_html_path> <name> <date>"""
import json, os, sys, base64, html

ROOT = os.path.dirname(os.path.abspath(__file__))
IN   = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "vap.json")
OUT  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "vap.html")
NAME = sys.argv[3] if len(sys.argv) > 3 else "Your Name"
DATE = sys.argv[4] if len(sys.argv) > 4 else "August 2026"
COVER = os.path.join(ROOT, "data", "brand_cover.png")

_raw = json.load(open(IN)); v = _raw.get("output", _raw)
def e(s): return html.escape(str(s or "").replace("`", "").replace("**", ""))
cover_b64 = base64.b64encode(open(COVER, "rb").read()).decode()

RED, EMBER, INK, MUT, LINE, BG2 = "#ED383B", "#FF6A3D", "#101218", "#6b7080", "#e7e9ef", "#f6f7fa"

opps = ""
for i, o in enumerate(v.get("opportunities", [])[:3], 1):
    owner = f'<div class="oppmeta"><b>Owned by:</b> {e(o.get("owner"))}</div>' if o.get("owner") else ""
    fmove = f'<div class="oppmeta"><b>First move:</b> {e(o.get("first_move"))}</div>' if o.get("first_move") else ""
    opps += f'''<div class="opp">
      <div class="oppn">{i:02d}</div>
      <div><div class="oppt">{e(o.get("title"))}</div>
        <div class="oppi">{e(o.get("insight"))}</div>
        <div class="oppimp"><b>Unlocks:</b> {e(o.get("impact"))}</div>
        {owner}{fmove}</div>
    </div>'''

# The insider "read" — 2-3 diagnosis bullets shown on the opportunity page.
read_items = v.get("read", []) or []
read_block = ""
if read_items:
    lis = "".join(f'<div class="readrow"><div class="readdot"></div><div>{e(r)}</div></div>' for r in read_items[:3])
    read_block = f'<div class="readwrap"><div class="readhd">What I see from the outside</div>{lis}</div>'

# The altitude reframe — the signature from/to positioning move.
rf = v.get("reframe") or {}
reframe_page = ""
if rf.get("from") or rf.get("to"):
    why = f'<div class="rfwhy">{e(rf.get("why"))}</div>' if rf.get("why") else ""
    reframe_page = f'''<section class="page">
  <div class="kicker"><div class="tab"></div><span>The Reframe</span></div>
  <h1 class="sec">Same experience, higher altitude</h1>
  <p class="lead">The work is real. This is how it should be positioned for {e(v.get("for_line","this company"))}.</p>
  <div class="rfgrid">
    <div class="rfcard rffrom"><div class="rftag">How it usually reads</div><div class="rftxt">{e(rf.get("from"))}</div></div>
    <div class="rfarrow">&#8594;</div>
    <div class="rfcard rfto"><div class="rftag rftagto">How it should read</div><div class="rftxt">{e(rf.get("to"))}</div></div>
  </div>
  {why}
  <div class="foot"><span>CareerForge · Value-Added Project</span><span>Positioning</span></div>
</section>'''

# 30/60/90 timeline
plan = v.get("plan", [])[:3]
cols = ""
for i, p in enumerate(plan):
    acts = "".join(f"<li>{e(a)}</li>" for a in p.get("actions", []))
    cols += f'''<div class="pcol">
      <div class="pdot"></div>
      <div class="pphase">{e(p.get("phase"))}</div>
      <div class="pfocus">{e(p.get("focus"))}</div>
      <ul>{acts}</ul>
    </div>'''

metrics = "".join(f'<span class="chip">{e(m)}</span>' for m in v.get("metrics", []))

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ margin:0; font-family:'Inter',sans-serif; color:{INK}; }}
.page {{ width:210mm; min-height:297mm; page-break-after:always; position:relative; padding:22mm 20mm; }}
.page:last-child {{ page-break-after:auto; }}
.kicker {{ display:flex; align-items:center; gap:11px; margin-bottom:6px; }}
.kicker .tab {{ width:26px; height:5px; border-radius:3px; background:linear-gradient(90deg,{RED},{EMBER}); }}
.kicker span {{ font-family:'Archivo'; font-weight:700; font-size:11px; letter-spacing:.24em; text-transform:uppercase; color:{RED}; }}
h1.sec {{ font-family:'Archivo'; font-weight:800; font-size:26px; letter-spacing:-.5px; margin:0 0 4px; }}
.lead {{ font-family:'Source Serif 4'; font-size:13px; color:{MUT}; margin:0 0 18px; }}
hr {{ border:none; border-top:1px solid {LINE}; margin:16px 0; }}
.foot {{ position:absolute; bottom:12mm; left:20mm; right:20mm; display:flex; justify-content:space-between; font-size:9px; color:#9aa0b0; border-top:1px solid {LINE}; padding-top:7px; }}
.foot b {{ color:{RED}; font-family:Archivo; }}

/* cover */
.cover {{ background:#08080A; color:#fff; padding:0; overflow:hidden; }}
.cover .bg {{ position:absolute; inset:0; }} .cover .bg img {{ width:100%; height:100%; object-fit:cover; opacity:.85; }}
.cover .veil {{ position:absolute; inset:0; background:linear-gradient(180deg,rgba(8,8,10,.45),rgba(8,8,10,.72) 60%,rgba(8,8,10,.97)); }}
.cover .in {{ position:absolute; inset:0; padding:24mm 20mm; display:flex; flex-direction:column; justify-content:flex-end; }}
.cover .brand {{ position:absolute; top:20mm; left:20mm; display:flex; align-items:center; gap:10px; }}
.cover .brand .m {{ width:32px; height:32px; border-radius:9px; background:linear-gradient(135deg,{RED},{EMBER}); }}
.cover .brand .t {{ font-family:'Archivo'; font-weight:800; font-size:15px; }}
.cover .eb {{ font-family:'Archivo'; font-weight:700; font-size:12px; letter-spacing:.28em; text-transform:uppercase; color:{EMBER}; margin-bottom:14px; }}
.cover h1 {{ font-family:'Archivo'; font-weight:800; font-size:38px; line-height:1.06; margin:0 0 14px; letter-spacing:-1px; }}
.cover .thesis {{ font-family:'Source Serif 4'; font-style:italic; font-size:18px; color:#e7c6b6; margin-bottom:22px; line-height:1.4; border-left:3px solid {RED}; padding-left:16px; }}
.cover .meta {{ display:flex; gap:30px; border-top:1px solid rgba(255,255,255,.16); padding-top:14px; }}
.cover .meta span {{ display:block; font-size:9px; letter-spacing:.2em; text-transform:uppercase; color:rgba(255,255,255,.5); margin-bottom:3px; }}
.cover .meta b {{ font-family:'Archivo'; font-weight:600; font-size:13px; }}

/* opportunities */
.whynow {{ font-family:'Source Serif 4'; font-size:15px; line-height:1.55; color:#2a2d38; background:{BG2}; border-left:3px solid {EMBER}; padding:14px 18px; border-radius:8px; margin-bottom:18px; }}
.opp {{ display:flex; gap:16px; padding:14px 0; border-bottom:1px solid {LINE}; }}
.oppn {{ font-family:'Archivo'; font-weight:800; font-size:24px; color:{RED}; width:44px; flex-shrink:0; }}
.oppt {{ font-family:'Archivo'; font-weight:700; font-size:15px; margin-bottom:4px; }}
.oppi {{ font-size:12.5px; color:#33363f; line-height:1.5; }}
.oppimp {{ font-size:12px; color:{INK}; margin-top:5px; }} .oppimp b {{ color:{RED}; }}
.oppmeta {{ font-size:11px; color:{MUT}; margin-top:3px; }} .oppmeta b {{ color:{INK}; font-weight:600; }}

/* insider read */
.readwrap {{ background:{BG2}; border:1px solid {LINE}; border-radius:12px; padding:16px 18px; margin-bottom:18px; }}
.readhd {{ font-family:'Archivo'; font-weight:700; font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:{RED}; margin-bottom:10px; }}
.readrow {{ display:flex; gap:10px; align-items:flex-start; margin:7px 0; font-size:12.5px; line-height:1.5; color:#2a2d38; }}
.readdot {{ width:7px; height:7px; border-radius:50%; background:{RED}; margin-top:5px; flex-shrink:0; }}

/* reframe */
.rfgrid {{ display:flex; align-items:stretch; gap:14px; margin-top:8px; }}
.rfcard {{ flex:1; border-radius:14px; padding:20px; border:1px solid {LINE}; }}
.rffrom {{ background:{BG2}; }}
.rfto {{ background:linear-gradient(135deg,rgba(237,56,59,.06),rgba(255,106,61,.06)); border-color:{RED}; }}
.rftag {{ font-family:'Archivo'; font-weight:700; font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:{MUT}; margin-bottom:10px; }}
.rftagto {{ color:{RED}; }}
.rftxt {{ font-family:'Source Serif 4'; font-size:15px; line-height:1.5; color:{INK}; }}
.rfarrow {{ display:flex; align-items:center; font-size:26px; color:{RED}; font-weight:700; }}
.rfwhy {{ font-family:'Source Serif 4'; font-style:italic; font-size:14px; color:{MUT}; margin-top:18px; border-left:3px solid {EMBER}; padding-left:14px; }}

/* timeline */
.timeline {{ display:flex; gap:16px; margin-top:8px; }}
.pcol {{ flex:1; border:1px solid {LINE}; border-radius:12px; padding:16px; position:relative; }}
.pcol .pdot {{ width:12px; height:12px; border-radius:50%; background:{RED}; margin-bottom:10px; }}
.pphase {{ font-family:'Archivo'; font-weight:800; font-size:14px; color:{INK}; }}
.pfocus {{ font-size:11.5px; color:{MUT}; margin:4px 0 8px; font-style:italic; }}
.pcol ul {{ margin:0; padding-left:16px; }} .pcol li {{ font-size:11.5px; margin:5px 0; color:#2a2d38; }}
.whyme {{ font-family:'Source Serif 4'; font-size:14px; line-height:1.55; color:#2a2d38; margin-top:6px; }}
.chip {{ display:inline-block; background:{BG2}; border:1px solid {LINE}; border-radius:100px; padding:5px 13px; font-size:11.5px; margin:4px 5px 0 0; font-weight:500; }}

/* outreach note */
.note {{ background:#fff; border:1px solid {LINE}; border-radius:14px; padding:22px 24px; box-shadow:0 10px 30px -18px rgba(0,0,0,.25); }}
.note .nh {{ font-size:11px; color:{MUT}; text-transform:uppercase; letter-spacing:.14em; margin-bottom:10px; }}
.note .nb {{ font-size:13.5px; line-height:1.65; color:{INK}; white-space:pre-wrap; }}
.sign {{ margin-top:16px; font-family:'Archivo'; font-weight:700; }}
</style></head><body>

<section class="page cover">
  <div class="bg"><img src="data:image/png;base64,{cover_b64}"></div><div class="veil"></div>
  <div class="brand"><div class="m"></div><div class="t">CareerForge</div></div>
  <div class="in">
    <div class="eb">Value-Added Project</div>
    <h1>{e(v.get("project_title"))}</h1>
    <div class="thesis">{e(v.get("thesis"))}</div>
    <div class="meta">
      <div><span>{e(v.get("for_line"))}</span><b>By {e(NAME)}</b></div>
      <div><span>Date</span><b>{e(DATE)}</b></div>
    </div>
  </div>
</section>

<section class="page">
  <div class="kicker"><div class="tab"></div><span>The Opportunity</span></div>
  <h1 class="sec">Why this, why now</h1>
  <p class="lead">Three things I'd move first — grounded in your business, not a template.</p>
  <div class="whynow">{e(v.get("why_now"))}</div>
  {read_block}
  {opps}
  <div class="foot"><span>CareerForge · Value-Added Project</span><span>{e(v.get("for_line"))}</span></div>
</section>

{reframe_page}

<section class="page">
  <div class="kicker"><div class="tab"></div><span>The Plan</span></div>
  <h1 class="sec">My first 90 days</h1>
  <p class="lead">Not a promise — a sequence, with what I'd ship at each stage.</p>
  <div class="timeline">{cols}</div>
  <hr>
  <div class="kicker"><div class="tab"></div><span>Why me</span></div>
  <div class="whyme">{e(v.get("why_me"))}</div>
  <div style="margin-top:12px">{metrics}</div>
  <div class="foot"><span>CareerForge · Value-Added Project</span><span>90-day plan</span></div>
</section>

<section class="page">
  <div class="kicker"><div class="tab"></div><span>Send this with it</span></div>
  <h1 class="sec">Your outreach note</h1>
  <p class="lead">Copy this into your email or LinkedIn message, attach the project, hit send.</p>
  <div class="note">
    <div class="nh">Message</div>
    <div class="nb">{e(v.get("outreach_note"))}</div>
    <div class="sign">— {e(NAME)}</div>
  </div>
  <div class="foot"><span>CareerForge · Value-Added Project</span><span>Prepared by CareerForge · Career OS</span></div>
</section>

</body></html>"""
open(OUT, "w").write(HTML)
print(json.dumps({"html": OUT, "title": v.get("project_title")}))
