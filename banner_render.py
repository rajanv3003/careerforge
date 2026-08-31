#!/usr/bin/env python3
"""CareerForge — PREMIUM multi-layout LinkedIn banner renderer (1584x396).
Locked premium aesthetic (2026-08-19, approved by Rajan) BUT the DESIGN VARIES per
person so no two banners look the same. The AI picks a "layout" that fits the
individual's field/perspective; each layout renders a distinct right-side visual:

  network   — constellation data-mesh (systems / data / infra / product)
  authority — a "WORKED WITH" brand-credibility strip (big-brand employers)
  metric    — one giant focal number/timeframe (a standout result)
  bars      — a rising bar-chart of impact measures (growth trends)

All share the dark-executive base (charcoal gradient + warm brand glow) and crisp
overlaid text. Graphics are seeded from the person's name so each render is unique
but stable. Any missing layout data falls back gracefully to 'network'.

Usage: python3 banner_render.py <banner_json> <out_html> <theme> [ai_bg.png]
theme = noir (amber) | red (ember) | emerald (teal-green)"""
import json, os, sys, html, base64, re

ROOT = os.path.dirname(os.path.abspath(__file__))
IN    = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "banner.json")
OUT   = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "banner.html")
THEME = (sys.argv[3] if len(sys.argv) > 3 else "noir").lower()
BG    = sys.argv[4] if len(sys.argv) > 4 else ""
COLOR = sys.argv[5] if len(sys.argv) > 5 else ""   # swatch hex or free-text colour name

_raw = json.load(open(IN))
b = _raw.get("output", _raw)
b = b.get("banner", b)
def e(s): return html.escape(str(s or "").replace("`", "").replace("**", ""))

tagline = str(b.get("tagline", "") or "").strip().rstrip(".")
accent  = str(b.get("accent_word", "") or "").strip()
pillars_list = [e(p) for p in (b.get("pillars") or [])[:3] if str(p or "").strip()]
name    = e(b.get("name"))
name_raw = str(b.get("name", "") or "")
email   = str(b.get("email", "") or "").strip()
stat    = str(b.get("stat", "") or "").strip()
layout  = str(b.get("layout", "") or "network").strip().lower()
companies = [str(c).strip() for c in (b.get("companies") or []) if str(c or "").strip()][:4]
big_metric = b.get("big_metric") or {}
bars = [x for x in (b.get("bars") or []) if isinstance(x, dict)][:4]

pillars = '<span class="bar">|</span>'.join(f'<span>{p}</span>' for p in pillars_list)

tag_html = e(tagline)
if accent and accent.lower() in tagline.lower():
    tag_html = re.sub("(" + re.escape(accent) + ")", r'<span class="acc">\1</span>',
                      e(tagline), count=1, flags=re.I)

# ---------------- Premium themes ----------------
THEMES = {
    "noir":    {"glow": "255,150,64",  "acc": "#FF7A2F", "net": "255,181,120"},
    "red":     {"glow": "237,56,59",   "acc": "#FF5E60", "net": "255,120,122"},
    "emerald": {"glow": "22,196,138",  "acc": "#2FE6A6", "net": "120,232,190"},
}
t = THEMES.get(THEME, THEMES["noir"])
GLOW, ACC, NET = t["glow"], t["acc"], t["net"]

# ---------------- Colour picker: swatch hex OR free-text name ----------------
NAMED = {
    "amber": "#FF7A2F", "gold": "#FFB020", "orange": "#FF7A2F", "sunset": "#FF6A3D",
    "red": "#ED383B", "crimson": "#E5484D", "ember": "#FF5E60", "ruby": "#E5484D",
    "emerald": "#20C08A", "green": "#22B473", "teal": "#14B8A6", "mint": "#2FE6A6",
    "blue": "#3B82F6", "deep blue": "#2F5BFF", "navy": "#3457D5", "royal blue": "#2F5BFF",
    "sky": "#38BDF8", "cyan": "#22D3EE", "azure": "#2F80FF",
    "indigo": "#6366F1", "violet": "#8B5CF6", "purple": "#A855F7", "lavender": "#B39DFF",
    "magenta": "#E24B9E", "pink": "#EC4899", "rose": "#FB7185",
    "slate": "#94A3B8", "steel": "#7C93B0", "graphite": "#9AA0AA", "silver": "#C4C9D4",
    "bronze": "#C08457", "copper": "#C0714A", "champagne": "#D9C08A", "white": "#E8E8EC",
}
def _hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def resolve_color(s):
    s = (s or "").strip().lower()
    if not s:
        return None
    hexv = None
    if re.fullmatch(r"#?[0-9a-f]{6}", s) or re.fullmatch(r"#?[0-9a-f]{3}", s):
        hexv = s if s.startswith("#") else "#" + s
    elif s in NAMED:
        hexv = NAMED[s]
    else:
        for k, v in NAMED.items():          # match "deep blue" inside "a deep blue please"
            if k in s:
                hexv = v
                break
    if not hexv:
        return None
    r, g, b = _hex_to_rgb(hexv)
    lr, lg, lb = [int(c + (255 - c) * 0.45) for c in (r, g, b)]   # lighter tint for the network/lines
    return {"glow": f"{r},{g},{b}", "acc": hexv, "net": f"{lr},{lg},{lb}"}
_col = resolve_color(COLOR)
if _col:
    GLOW, ACC, NET = _col["glow"], _col["acc"], _col["net"]

# Per-person deterministic seed → unique-but-stable graphics
def _seed_from(s):
    v = 20260819
    for ch in (s or "x"):
        v = (v * 1103515245 + ord(ch) + 12345) & 0x7fffffff
    return v or 1

# ---------------- Right-side visuals (one per layout) ----------------
def viz_network():
    seed = _seed_from(name_raw)
    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        return seed / 0x7fffffff
    x0, x1, y0, y1 = 990, 1548, 46, 356
    n = 26 + int(rnd() * 8)
    nodes = [(x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)) for _ in range(n)]
    D = 168
    edges = [(i, j) for i in range(len(nodes)) for j in range(i + 1, len(nodes))
             if (nodes[i][0]-nodes[j][0])**2 + (nodes[i][1]-nodes[j][1])**2 < D*D]
    lines = "".join(f'<line x1="{nodes[i][0]:.0f}" y1="{nodes[i][1]:.0f}" x2="{nodes[j][0]:.0f}" y2="{nodes[j][1]:.0f}" stroke="rgba({NET},0.22)" stroke-width="1"/>' for i, j in edges)
    dots = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{2.0+(i%3):.1f}" fill="rgba({NET},{0.55 if i%4 else 0.85})"/>' for i, (x, y) in enumerate(nodes))
    return f'<svg class="viz" width="1584" height="396" viewBox="0 0 1584 396">{lines}{dots}</svg>'

def viz_curves():
    seed = _seed_from(name_raw + "c")
    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        return seed / 0x7fffffff
    paths = ""
    base = 300 + int(rnd() * 30)
    for k in range(6):
        o = k * 15
        paths += f'<path d="M 690 {base-o*0.35:.0f} C 980 {316-o:.0f}, 1200 {188-o:.0f}, 1560 {104-o:.0f}" stroke="rgba(255,255,255,{0.05+0.028*k:.3f})" stroke-width="1.4" fill="none"/>'
    return f'<svg class="viz" width="1584" height="396" viewBox="0 0 1584 396">{paths}</svg>'

def viz_bars():
    data = bars if bars else [{"label": p, "value": 55 + i*15} for i, p in enumerate(pillars_list)]
    if not data:
        return viz_network()
    data = data[:4]
    x0, w, gap, base_y, maxh = 1050, 96, 40, 330, 250
    out = ""
    for i, d in enumerate(data):
        try: val = max(8, min(100, float(str(d.get("value", 60)).replace('%',''))))
        except Exception: val = 60
        h = maxh * val / 100.0
        x = x0 + i * (w + gap)
        y = base_y - h
        out += (f'<defs><linearGradient id="bg{i}" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="rgba({GLOW},0.95)"/><stop offset="1" stop-color="rgba({GLOW},0.30)"/></linearGradient></defs>'
                f'<rect x="{x}" y="{y:.0f}" width="{w}" height="{h:.0f}" rx="10" fill="url(#bg{i})"/>'
                f'<text x="{x+w/2:.0f}" y="{base_y+26}" fill="rgba(255,255,255,.68)" font-family="Inter" font-weight="700" font-size="17" text-anchor="middle">{e(d.get("label",""))}</text>')
    return f'<svg class="viz" width="1584" height="396" viewBox="0 0 1584 396"><line x1="1030" y1="330" x2="1552" y2="330" stroke="rgba(255,255,255,.14)" stroke-width="1.5"/>{out}</svg>'

def viz_metric():
    val = str(big_metric.get("value", "") or stat or "").strip()
    lab = str(big_metric.get("label", "") or "").strip()
    if not val:
        return viz_network()
    rings = ''.join(f'<circle cx="1194" cy="198" r="{r}" fill="none" stroke="rgba({NET},{0.14-0.03*i:.2f})" stroke-width="1.5"/>' for i, r in enumerate((110, 150, 190)))
    lab_html = f'<div class="mlabel">{e(lab)}</div>' if lab else ""
    return (f'<svg class="viz" width="1584" height="396" viewBox="0 0 1584 396">{rings}</svg>'
            f'<div class="metric"><div class="mval">{e(val)}</div>{lab_html}</div>')

def viz_authority():
    if not companies:
        return viz_network()
    chips = ''.join(f'<span class="chip">{e(c)}</span>' for c in companies)
    return (viz_curves() +
            f'<div class="creds"><div class="credlabel">WORKED WITH</div><div class="chips">{chips}</div></div>')

def viz_wave():
    return viz_curves()

def viz_minimal():
    # elegant executive: a giant faint initial on the right, nothing else
    initial = e((name_raw.strip()[:1] or "").upper())
    return f'<div class="mono">{initial}</div>'

def viz_spotlight():
    rings = ''.join(f'<circle cx="1240" cy="198" r="{r}" fill="none" stroke="rgba({NET},{max(0.03,0.12-0.02*i):.2f})" stroke-width="1.5"/>'
                    for i, r in enumerate((90, 140, 190, 240)))
    return f'<svg class="viz" width="1584" height="396">{rings}</svg>'

VIZ = {"network": lambda: viz_network()+viz_curves(),
       "wave": viz_wave, "minimal": viz_minimal, "spotlight": viz_spotlight,
       "bars": viz_bars, "metric": viz_metric, "authority": viz_authority}

# ---------------- Background ----------------
if BG and os.path.exists(BG):
    b64 = base64.b64encode(open(BG, "rb").read()).decode()
    bg_css = "#0A0A0C"
    bg_layer = f'<div class="bglayer"><img src="data:image/png;base64,{b64}"/><div class="scrim"></div></div>'
    infographic = ""
else:
    bg_css = (f"radial-gradient(58% 130% at 63% 42%, rgba({GLOW},0.30) 0%, rgba({GLOW},0.08) 38%, rgba(0,0,0,0) 66%),"
              f"linear-gradient(106deg, #090909 0%, #141417 46%, #0B0B0D 100%)")
    bg_layer = ""
    infographic = VIZ.get(layout, VIZ["network"])()

email_html = f'<div class="email"><span>EMAIL&nbsp;ID:</span> <b>{e(email.upper())}</b></div>' if email else ""
stat_html  = f'<div class="stat">{e(stat)}</div>' if (stat and layout not in ("metric", "bars")) else ""

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800;900&family=Inter:wght@500;600;700&display=swap" rel="stylesheet">
<style>
* {{ margin:0; box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
html,body {{ width:1584px; height:396px; overflow:hidden; }}
.banner {{ width:1584px; height:396px; background:{bg_css}; position:relative; font-family:'Inter',sans-serif; color:#FFFFFF; overflow:hidden; }}
.bglayer {{ position:absolute; inset:0; }}
.bglayer img {{ width:100%; height:100%; object-fit:cover; }}
.scrim {{ position:absolute; inset:0; background:linear-gradient(90deg,rgba(9,9,11,.78),rgba(9,9,11,.52) 34%,rgba(9,9,11,.55) 66%,rgba(9,9,11,.80)); }}
.viz {{ position:absolute; inset:0; pointer-events:none; }}
.banner::after {{ content:""; position:absolute; inset:0; pointer-events:none; background:linear-gradient(90deg, rgba(9,9,11,.55) 0%, rgba(9,9,11,0) 30%); }}
/* SAFE ZONE: LinkedIn overlays the profile photo on the lower-left and crops the
   sides on mobile. Keep all copy inside left:392..right:88 and vertically centred. */
.copy {{ position:absolute; left:392px; right:88px; top:0; bottom:0; z-index:3; display:flex; flex-direction:column; justify-content:center; }}
.mono {{ position:absolute; right:120px; top:50%; transform:translateY(-52%); z-index:1; font-family:'Archivo'; font-weight:900; font-size:340px; line-height:1; color:rgba(255,255,255,.05); pointer-events:none; }}
.tagline {{ font-family:'Archivo'; font-weight:800; font-size:41px; letter-spacing:-.6px; line-height:1.12; color:#FFF; max-width:900px; text-shadow:0 2px 22px rgba(0,0,0,.45); }}
.lay-authority .tagline {{ max-width:560px; }}
.lay-metric .tagline, .lay-bars .tagline {{ max-width:520px; }}
.lay-metric .name {{ font-size:62px; }}
.tagline .acc {{ color:{ACC}; }}
.pillars {{ font-family:'Inter'; font-weight:700; font-size:22px; color:rgba(255,255,255,.82); margin-top:16px; letter-spacing:.2px; }}
.pillars .bar {{ color:rgba(255,255,255,.30); margin:0 12px; font-weight:400; }}
.name {{ font-family:'Archivo'; font-weight:900; font-size:74px; letter-spacing:-1.6px; line-height:1; margin-top:22px; color:#FFF; text-shadow:0 2px 26px rgba(0,0,0,.5); }}
.email {{ margin-top:22px; font-size:19px; color:rgba(255,255,255,.66); letter-spacing:.5px; }}
.email b {{ color:#FFF; font-weight:700; }}
.stat {{ position:absolute; right:64px; bottom:40px; z-index:4; font-family:'Archivo'; font-weight:900; font-size:25px; color:#FFF; background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); padding:11px 24px; border-radius:100px; box-shadow:0 6px 24px rgba(0,0,0,.35); }}
/* metric layout */
.metric {{ position:absolute; right:90px; top:0; bottom:0; width:600px; z-index:2; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }}
.metric .mval {{ font-family:'Archivo'; font-weight:900; font-size:84px; line-height:.92; letter-spacing:-2px; color:{ACC}; text-shadow:0 4px 40px rgba({GLOW},.35); }}
.metric .mlabel {{ font-family:'Inter'; font-weight:700; font-size:21px; color:rgba(255,255,255,.80); margin-top:14px; max-width:440px; }}
/* authority layout */
.creds {{ position:absolute; right:70px; top:58px; z-index:3; text-align:right; }}
.credlabel {{ font-family:'Inter'; font-weight:700; font-size:15px; letter-spacing:3px; color:rgba(255,255,255,.55); margin-bottom:14px; }}
.chips {{ display:flex; flex-wrap:wrap; gap:12px; justify-content:flex-end; max-width:640px; }}
.chip {{ font-family:'Archivo'; font-weight:800; font-size:24px; color:#FFF; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.16); padding:8px 20px; border-radius:12px; }}
</style></head><body>
<div class="banner lay-{layout}">
  {bg_layer}
  {infographic}
  {stat_html}
  <div class="copy">
    <div class="tagline">{tag_html}</div>
    <div class="pillars">{pillars}</div>
    <div class="name">{name}</div>
    {email_html}
  </div>
</div>
</body></html>"""
open(OUT, "w").write(HTML)
print(json.dumps({"html": OUT, "theme": THEME, "layout": layout}))
