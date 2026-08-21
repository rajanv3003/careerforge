#!/usr/bin/env python3
"""CareerForge — professional designed resume PDF (clean, simple, ATS-safe).
Usage: python3 resume_pdf.py <resume_json_path> <out_html_path>
The JSON file is {"output": {...resume...}} OR the resume object directly."""
import json, os, sys, html

ROOT = os.path.dirname(os.path.abspath(__file__))
IN  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "resume_struct.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "out", "resume.html")

_raw = json.load(open(IN))
r = _raw.get("output", _raw)
def e(s): return html.escape(str(s or "").replace("`", "").replace("**", ""))

ACCENT, INK, MUT, LINE = "#ED383B", "#15171c", "#5b6070", "#e6e8ee"

# contact line
contact = " &nbsp;·&nbsp; ".join(filter(None, [
    e(r.get("location")), e(r.get("email")), e(r.get("phone")), e(r.get("linkedin"))
]))

# highlights strip
hi = r.get("highlights") or []
hi_html = ""
if hi:
    cells = "".join(f'<div class="hl"><div class="hlt">{e(h)}</div></div>' for h in hi[:3])
    hi_html = f'<div class="hlrow">{cells}</div>'

# skills
sk = r.get("skills") or []
sk_rows = ""
for grp in sk:
    if isinstance(grp, dict):
        items = ", ".join(e(x) for x in grp.get("items", []))
        sk_rows += f'<div class="skrow"><span class="skc">{e(grp.get("category"))}</span><span class="ski">{items}</span></div>'
    else:
        sk_rows += f'<div class="skrow"><span class="ski">{e(grp)}</span></div>'

# experience
exp = r.get("experience") or []
exp_html = ""
for x in exp:
    bullets = "".join(f"<li>{e(b)}</li>" for b in (x.get("bullets") or []))
    dates = " – ".join(filter(None, [e(x.get("start")), e(x.get("end"))]))
    loc = f' · {e(x.get("location"))}' if x.get("location") else ""
    exp_html += f'''<div class="job">
      <div class="jobhead">
        <div><span class="role">{e(x.get("role"))}</span> <span class="at">at</span> <span class="company">{e(x.get("company"))}</span><span class="jloc">{loc}</span></div>
        <div class="dates">{dates}</div>
      </div>
      <ul>{bullets}</ul>
    </div>'''

# education
edu = r.get("education") or []
edu_html = ""
for x in edu:
    detail = f' · {e(x.get("detail"))}' if x.get("detail") else ""
    edu_html += f'''<div class="edu">
      <div><span class="deg">{e(x.get("degree"))}</span> <span class="at">—</span> <span class="school">{e(x.get("school"))}</span><span class="edet">{detail}</span></div>
      <div class="dates">{e(x.get("year"))}</div>
    </div>'''

# certifications
certs = r.get("certifications") or []
cert_html = ""
if certs:
    cert_html = f'''<div class="section"><h2>Certifications</h2>
      <div class="certs">{" &nbsp;·&nbsp; ".join(e(c) for c in certs)}</div></div>'''

def section(title, inner):
    return f'<div class="section"><h2>{title}</h2>{inner}</div>' if inner.strip() else ""

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@page {{ size:A4; margin:0; }}
* {{ box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ margin:0; font-family:'Inter',sans-serif; color:{INK}; font-size:10.3pt; line-height:1.42; }}
.page {{ width:210mm; min-height:297mm; padding:15mm 18mm; }}

/* header */
.head {{ border-bottom:2px solid {ACCENT}; padding-bottom:14px; margin-bottom:16px; }}
.name {{ font-family:'Archivo'; font-weight:800; font-size:27pt; letter-spacing:-.6px; line-height:1; }}
.title {{ font-family:'Archivo'; font-weight:600; font-size:12.5pt; color:{ACCENT}; margin-top:5px; letter-spacing:.2px; }}
.contact {{ font-size:9.3pt; color:{MUT}; margin-top:9px; }}

/* highlights */
.hlrow {{ display:flex; gap:10px; margin:0 0 16px; }}
.hl {{ flex:1; background:#f7f8fb; border:1px solid {LINE}; border-left:3px solid {ACCENT}; border-radius:7px; padding:9px 11px; }}
.hlt {{ font-size:9pt; color:{INK}; font-weight:500; line-height:1.35; }}

/* sections */
.section {{ margin-bottom:15px; }}
h2 {{ font-family:'Archivo'; font-weight:700; font-size:11pt; text-transform:uppercase; letter-spacing:1.4px;
     color:{INK}; margin:0 0 9px; padding-bottom:4px; border-bottom:1px solid {LINE}; }}
.summary {{ font-size:10.5pt; color:#2c2f38; }}

/* skills */
.skrow {{ display:flex; margin:4px 0; font-size:9.8pt; }}
.skc {{ font-weight:700; color:{INK}; width:135px; flex-shrink:0; }}
.ski {{ color:#33363f; }}

/* experience */
.job {{ margin-bottom:13px; page-break-inside:avoid; }}
.jobhead {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; }}
.role {{ font-family:'Archivo'; font-weight:700; font-size:11pt; color:{INK}; }}
.at {{ color:{MUT}; font-size:9.5pt; }}
.company {{ font-weight:600; color:{ACCENT}; font-size:10.5pt; }}
.jloc {{ color:{MUT}; font-size:9.3pt; }}
.dates {{ font-size:9pt; color:{MUT}; white-space:nowrap; font-weight:500; }}
.job ul {{ margin:6px 0 0; padding-left:16px; }}
.job li {{ margin:3px 0; font-size:9.9pt; color:#2c2f38; }}

/* education */
.edu {{ display:flex; justify-content:space-between; align-items:baseline; margin:5px 0; font-size:10pt; }}
.deg {{ font-weight:700; }} .school {{ color:#33363f; }} .edet {{ color:{MUT}; font-size:9.3pt; }}
.certs {{ font-size:9.8pt; color:#33363f; }}
</style></head><body>
<div class="page">
  <div class="head">
    <div class="name">{e(r.get("name"))}</div>
    <div class="title">{e(r.get("title"))}</div>
    <div class="contact">{contact}</div>
  </div>
  {hi_html}
  {section("Summary", f'<div class="summary">{e(r.get("summary"))}</div>') if r.get("summary") else ""}
  {section("Skills", sk_rows)}
  {section("Experience", exp_html)}
  {section("Education", edu_html)}
  {cert_html}
</div>
</body></html>"""
open(OUT, "w").write(HTML)
print(json.dumps({"html": OUT, "name": r.get("name")}))
