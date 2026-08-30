import "dotenv/config";
import express from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import os from "os";
import { execFile } from "child_process";
import { fileURLToPath } from "url";
import { MODULES, FULL_KIT_ORDER } from "./skills.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

app.use(express.json({ limit: "2mb" }));
app.use(express.static(path.join(__dirname, "public")));

const API_KEY = process.env.GEMINI_API_KEY;
const MODEL = process.env.GEMINI_MODEL || "gemini-2.5-flash";
const PORT = process.env.PORT || 3080;

// DeepSeek (OpenAI-compatible) config — used as the primary brain when set.
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;
const DEEPSEEK_BASE = process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com/v1";
const DEEPSEEK_MODEL = process.env.DEEPSEEK_MODEL || "deepseek-v4-flash";

// ---------------- LLM call (DeepSeek primary, Gemini fallback) ----------------
// Named callGemini for backward-compatibility with existing callers.
// opts.json = true asks the model for guaranteed-valid JSON (used by all
// JSON-producing modules so a stray quote/newline can never break parsing).
async function callGemini(prompt, opts = {}) {
  if (DEEPSEEK_API_KEY) return callDeepSeek(prompt, opts);
  if (API_KEY) return callGeminiNative(prompt, opts);
  throw new Error("No DEEPSEEK_API_KEY or GEMINI_API_KEY set in .env");
}

async function callDeepSeek(prompt, opts = {}) {
  const messages = [];
  if (opts.json) messages.push({ role: "system", content: "Output valid JSON only." });
  messages.push({ role: "user", content: prompt });
  const payload = {
    model: DEEPSEEK_MODEL,
    messages,
    temperature: 0.7,
    // deepseek-v4 is a reasoning model. By default we DISABLE thinking so the
    // whole token budget goes to the answer (otherwise it returns empty).
    // For opts.think=true (nuanced tasks that need instruction-following, e.g.
    // personalized outreach) we ENABLE thinking and give extra headroom.
    max_tokens: opts.think ? 20000 : 8192,
    thinking: { type: opts.think ? "enabled" : "disabled" },
  };
  if (opts.json) payload.response_format = { type: "json_object" };
  const res = await fetch(`${DEEPSEEK_BASE}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`DeepSeek ${res.status}: ${body.slice(0, 400)}`);
  }
  const data = await res.json();
  const msg = data?.choices?.[0]?.message || {};
  // Fall back to reasoning_content in case a model ignores the thinking toggle.
  const text = msg.content || msg.reasoning_content || "";
  if (!text) throw new Error("DeepSeek returned no text: " + JSON.stringify(data).slice(0, 400));
  return text;
}

async function callGeminiNative(prompt, opts = {}) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${API_KEY}`;
  const generationConfig = { temperature: 0.7, maxOutputTokens: 8192 };
  if (opts.json) generationConfig.responseMimeType = "application/json";
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      generationConfig,
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Gemini ${res.status}: ${body.slice(0, 400)}`);
  }
  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.map((p) => p.text).join("") || "";
  if (!text) throw new Error("Gemini returned no text: " + JSON.stringify(data).slice(0, 400));
  return text;
}

// ---------------- File -> text ----------------
async function extractText(file) {
  const name = (file.originalname || "").toLowerCase();
  if (name.endsWith(".pdf")) {
    const pdfParse = (await import("pdf-parse")).default;
    const out = await pdfParse(file.buffer);
    return out.text;
  }
  if (name.endsWith(".docx")) {
    const mammoth = await import("mammoth");
    const out = await mammoth.extractRawText({ buffer: file.buffer });
    return out.value;
  }
  // txt / md / anything else -> raw
  return file.buffer.toString("utf8");
}

app.post("/api/parse-resume", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No file uploaded" });
    const text = await extractText(req.file);
    res.json({ text: (text || "").trim() });
  } catch (e) {
    res.status(500).json({ error: "Could not read that file. Please paste your resume text instead. (" + e.message + ")" });
  }
});

// ---------------- Run one module ----------------
app.post("/api/run", async (req, res) => {
  try {
    const { module, resume, job, profile } = req.body || {};
    const mod = MODULES[module];
    if (!mod) return res.status(400).json({ error: "Unknown module: " + module });
    let raw = await callGemini(mod.prompt({ resume, job, profile, o: req.body.o }), { json: !!mod.json, think: !!mod.think });
    // Outreach system prompt bans the em dash (the loudest AI tell). Safety net:
    // scrub any em/en dash the model still slips in before it reaches the user.
    if (module === "outreach") {
      raw = raw.replace(/\s*—\s*/g, ", ").replace(/\s*–\s*/g, "-").replace(/\s*;\s*/g, ", ");
    }
    let output = raw;
    if (mod.json) {
      const cleaned = raw.replace(/```json/gi, "").replace(/```/g, "").trim();
      try { output = JSON.parse(cleaned); } catch { output = { raw: cleaned }; }
    }
    res.json({ module, title: mod.title, group: mod.group, json: !!mod.json, output });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ---------------- Generate the graphical Intelligence Report PDF ----------------
const CHROME_PATHS = [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
];
function findChrome() { return CHROME_PATHS.find((p) => fs.existsSync(p)); }
function run(cmd, args) {
  return new Promise((res, rej) =>
    execFile(cmd, args, { maxBuffer: 1024 * 1024 * 64 }, (e, so, se) => (e ? rej(new Error(se || e.message)) : res(so)))
  );
}

const REPORTS_DIR = path.join(__dirname, "public", "reports");
fs.mkdirSync(REPORTS_DIR, { recursive: true });

// Forgiving JSON extraction: strip fences, then take the outermost {...}
function safeJson(raw) {
  let s = String(raw || "").replace(/```json/gi, "").replace(/```/g, "").trim();
  try { return JSON.parse(s); } catch {}
  const a = s.indexOf("{"), b = s.lastIndexOf("}");
  if (a >= 0 && b > a) { try { return JSON.parse(s.slice(a, b + 1)); } catch {} }
  return null;
}

app.post("/api/report", async (req, res) => {
  try {
    const { resume, job, profile } = req.body || {};
    const chrome = findChrome();
    if (!chrome) return res.status(500).json({ error: "No Chrome/Chromium found to render the PDF." });

    // 1. Run the intelligence diagnostic (grounded in our benchmark)
    const raw = await callGemini(MODULES.intel.prompt({ resume, job, profile }), { json: true });
    const intel = safeJson(raw);
    if (!intel) return res.status(500).json({ error: "Could not parse the diagnostic. Try again." });

    // 2. Write intel to a temp file and build the report HTML
    const id = "rpt_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    const tmp = path.join(os.tmpdir(), id + ".json");
    fs.writeFileSync(tmp, JSON.stringify({ output: intel }));
    const htmlPath = path.join(REPORTS_DIR, id + ".html");
    const pdfPath = path.join(REPORTS_DIR, id + ".pdf");
    const name = (profile && profile.name) || "Your Name";
    const date = new Date().toLocaleString("en-US", { month: "long", year: "numeric" });
    await run("python3", [path.join(__dirname, "report_gen.py"), tmp, htmlPath, name, date]);

    // 3. Print to PDF with headless Chrome
    await run(chrome, [
      "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
      "--print-to-pdf=" + pdfPath, "--virtual-time-budget=8000",
      "file://" + encodeURI(htmlPath),
    ]);
    fs.unlinkSync(tmp);
    if (!fs.existsSync(pdfPath)) return res.status(500).json({ error: "PDF render failed." });

    res.json({ url: "/reports/" + id + ".pdf", intel, overall: weightedScore(intel) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ---------------- Generate the designed Resume PDF ----------------
app.post("/api/resume-pdf", async (req, res) => {
  try {
    const { resume, job, profile } = req.body || {};
    const chrome = findChrome();
    if (!chrome) return res.status(500).json({ error: "No Chrome/Chromium found to render the PDF." });

    const raw = await callGemini(MODULES.resume_struct.prompt({ resume, job, profile }), { json: true });
    const data = safeJson(raw);
    if (!data) return res.status(500).json({ error: "Could not parse the resume. Try again." });

    const id = "cv_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    const tmp = path.join(os.tmpdir(), id + ".json");
    fs.writeFileSync(tmp, JSON.stringify({ output: data }));
    const htmlPath = path.join(REPORTS_DIR, id + ".html");
    const pdfPath = path.join(REPORTS_DIR, id + ".pdf");
    await run("python3", [path.join(__dirname, "resume_pdf.py"), tmp, htmlPath]);
    await run(chrome, [
      "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
      "--print-to-pdf=" + pdfPath, "--virtual-time-budget=6000",
      "file://" + encodeURI(htmlPath),
    ]);
    fs.unlinkSync(tmp);
    if (!fs.existsSync(pdfPath)) return res.status(500).json({ error: "PDF render failed." });
    res.json({ url: "/reports/" + id + ".pdf", data });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ---------------- Generate the Value-Added Project PDF ----------------
app.post("/api/vap-pdf", async (req, res) => {
  try {
    const { resume, job, profile, vap } = req.body || {};
    const chrome = findChrome();
    if (!chrome) return res.status(500).json({ error: "No Chrome/Chromium found to render the PDF." });
    if (!vap || !vap.company) return res.status(400).json({ error: "Tell me the target company first." });

    const raw = await callGemini(MODULES.vap.prompt({ resume, job, profile, vap }), { json: true });
    const data = safeJson(raw);
    if (!data) return res.status(500).json({ error: "Could not parse the project. Try again." });

    const id = "vap_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    const tmp = path.join(os.tmpdir(), id + ".json");
    fs.writeFileSync(tmp, JSON.stringify({ output: data }));
    const htmlPath = path.join(REPORTS_DIR, id + ".html");
    const pdfPath = path.join(REPORTS_DIR, id + ".pdf");
    const name = (profile && profile.name) || "Your Name";
    const date = new Date().toLocaleString("en-US", { month: "long", year: "numeric" });
    await run("python3", [path.join(__dirname, "vap_pdf.py"), tmp, htmlPath, name, date]);
    await run(chrome, [
      "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
      "--print-to-pdf=" + pdfPath, "--virtual-time-budget=8000",
      "file://" + encodeURI(htmlPath),
    ]);
    fs.unlinkSync(tmp);
    if (!fs.existsSync(pdfPath)) return res.status(500).json({ error: "PDF render failed." });
    res.json({ url: "/reports/" + id + ".pdf", data });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ---------------- Gathos text-to-image (for AI banner backgrounds) ----------------
const GATHOS_IMG_KEY = process.env.GATHOS_IMAGE_API_KEY;
const GATHOS_BASE = process.env.GATHOS_BASE_URL || "https://gathos.com/api/v1";

async function gathosImage(prompt, width = 2048, height = 512, onTick) {
  if (!GATHOS_IMG_KEY) throw new Error("No Gathos image key set.");
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${GATHOS_IMG_KEY}`, "User-Agent": "Mozilla/5.0" };
  // Gathos: dims 512–2048, divisible by 16
  const clamp = (n) => Math.min(2048, Math.max(512, Math.round(n / 16) * 16));
  width = clamp(width); height = clamp(height);
  const submit = await fetch(`${GATHOS_BASE}/image-generation`, {
    method: "POST", headers,
    body: JSON.stringify({
      prompt, width, height, prevent_text: true,
      negative_prompt: "text, words, letters, typography, watermark, logo, faces, people, ui, buttons, clutter, low quality, blurry",
    }),
  });
  if (!submit.ok) throw new Error(`Gathos submit ${submit.status}: ${(await submit.text()).slice(0, 200)}`);
  const { job_id } = await submit.json();
  if (!job_id) throw new Error("Gathos: no job_id");
  // poll (image ~3s interval, generous timeout — GPU + queue)
  for (let i = 0; i < 120; i++) {
    await new Promise((r) => setTimeout(r, 5000));
    const pr = await fetch(`${GATHOS_BASE}/image-generation/jobs/${job_id}`, { headers });
    if (!pr.ok) continue;
    const d = await pr.json();
    if (onTick) onTick(d.status, d.queue_position);
    if (d.status === "completed" || d.status === "done") {
      const b64 = d.result && d.result.image_base64;
      if (!b64) throw new Error("Gathos: completed but no image");
      return Buffer.from(b64, "base64");
    }
    if (d.status === "failed") throw new Error("Gathos image failed: " + (d.error || ""));
  }
  throw new Error("Gathos image timed out (queue too deep). Try again shortly.");
}

// Build a background prompt from the person's positioning, per the cover principles
function bannerBgPrompt(banner, positioning) {
  const pillars = (banner.pillars || []).join(", ");
  return `A minimalist, premium LinkedIn banner background for a senior executive. Deep dark charcoal (#0A0A0C) base with a subtle warm ember-to-transparent gradient bloom in the far top-right corner. Very subtle abstract infographic motifs suggesting ${pillars || "leadership, growth, strategy"} — faint thin line-art: an upward growth curve, a light geometric grid, delicate connected nodes — extremely low contrast, elegant, lots of clean negative space especially on the left third. Professional, authoritative, understated, cinematic soft lighting, high-end corporate aesthetic. Flat, no photography of people.`;
}

// ---------------- Gathos TTS (voice for the mock interview) ----------------
const GATHOS_TTS_KEY = process.env.GATHOS_TTS_API_KEY;
app.post("/api/tts", async (req, res) => {
  try {
    const { text, voice } = req.body || {};
    if (!GATHOS_TTS_KEY) return res.status(500).json({ error: "No Gathos TTS key set." });
    if (!text) return res.status(400).json({ error: "No text." });
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${GATHOS_TTS_KEY}`, "User-Agent": "Mozilla/5.0" };
    const submit = await fetch(`${GATHOS_BASE}/tts`, {
      method: "POST", headers,
      body: JSON.stringify({ text: String(text).slice(0, 500), voice: voice || "prof" }),
    });
    if (!submit.ok) return res.status(502).json({ error: `Gathos TTS ${submit.status}` });
    const { job_id } = await submit.json();
    if (!job_id) return res.status(502).json({ error: "TTS: no job_id" });
    for (let i = 0; i < 40; i++) {
      await new Promise((r) => setTimeout(r, 3000));
      const pr = await fetch(`${GATHOS_BASE}/tts/jobs/${job_id}`, { headers });
      if (!pr.ok) continue;
      const d = await pr.json();
      if (d.status === "completed" || d.status === "done") {
        const b64 = d.result && d.result.audio_base64;
        if (!b64) return res.status(502).json({ error: "TTS completed but no audio" });
        const ext = (d.result.content_type || "").includes("mp3") ? "mp3" : "wav";
        const fn = "tts_" + Date.now().toString(36) + "." + ext;
        fs.writeFileSync(path.join(REPORTS_DIR, fn), Buffer.from(b64, "base64"));
        return res.json({ url: "/reports/" + fn });
      }
      if (d.status === "failed") return res.status(502).json({ error: "TTS failed" });
    }
    return res.status(504).json({ error: "TTS timed out (queue busy). Try again." });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ---------------- LinkedIn Kit (banner image + headline + about) ----------------
async function renderBanner(bannerObj, theme, bgPath) {
  const chrome = findChrome();
  if (!chrome) throw new Error("No Chrome/Chromium found to render the banner.");
  const id = "ban_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const tmp = path.join(os.tmpdir(), id + ".json");
  fs.writeFileSync(tmp, JSON.stringify({ output: { banner: bannerObj } }));
  const htmlPath = path.join(REPORTS_DIR, id + ".html");
  const pngPath = path.join(REPORTS_DIR, id + ".png");
  const args = [path.join(__dirname, "banner_render.py"), tmp, htmlPath, theme || "noir"];
  if (bgPath) args.push(bgPath);
  await run("python3", args);
  await run(chrome, [
    "--headless=new", "--disable-gpu", "--force-device-scale-factor=1", "--hide-scrollbars",
    "--window-size=1584,396", "--screenshot=" + pngPath, "--virtual-time-budget=4000",
    "file://" + encodeURI(htmlPath),
  ]);
  fs.unlinkSync(tmp);
  if (!fs.existsSync(pngPath)) throw new Error("Banner render failed.");
  return "/reports/" + id + ".png";
}

app.post("/api/linkedin-kit", async (req, res) => {
  try {
    const { resume, job, profile, li } = req.body || {};
    const raw = await callGemini(MODULES.linkedin_kit.prompt({ resume, job, profile, li }), { json: true });
    const assets = safeJson(raw);
    if (!assets || !assets.banner) return res.status(500).json({ error: "Could not build the kit. Try again." });
    const theme = (li && li.theme) || "noir";
    const banner_url = await renderBanner(assets.banner, theme);
    res.json({ assets, banner_url, theme });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post("/api/banner-render", async (req, res) => {
  try {
    const { banner, theme } = req.body || {};
    if (!banner) return res.status(400).json({ error: "No banner data." });
    const banner_url = await renderBanner(banner, theme || "noir");
    res.json({ banner_url, theme: theme || "noir" });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// AI cover: Gathos generates a premium background, our engine keeps the crisp text on top
app.post("/api/banner-ai", async (req, res) => {
  try {
    const { banner, positioning } = req.body || {};
    if (!banner) return res.status(400).json({ error: "No banner data." });
    const prompt = bannerBgPrompt(banner, positioning);
    const buf = await gathosImage(prompt, 2048, 512);
    const bgPath = path.join(REPORTS_DIR, "bg_" + Date.now().toString(36) + ".png");
    fs.writeFileSync(bgPath, buf);
    const banner_url = await renderBanner(banner, "ai", bgPath);
    res.json({ banner_url, theme: "ai", bg: "/reports/" + path.basename(bgPath) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

function weightedScore(intel) {
  try {
    const W = { impact_scale:0.22, leadership:0.2, domain_depth:0.2, strategic:0.15, brand_visibility:0.12, communication:0.11 };
    return Math.round((intel.dimensions || []).reduce((s, d) => s + (d.score || 0) * (W[d.key] || 0), 0));
  } catch { return null; }
}

// ---------------- List modules ----------------
app.get("/api/modules", (_req, res) => {
  res.json({
    order: FULL_KIT_ORDER,
    modules: Object.fromEntries(
      Object.entries(MODULES).map(([k, v]) => [k, { title: v.title, group: v.group, json: !!v.json }])
    ),
  });
});

app.listen(PORT, () => {
  console.log(`\n  🚀 One-Room Career Suite running`);
  console.log(`  → Open http://localhost:${PORT} in your browser`);
  console.log(`  → Model: ${MODEL}\n`);
});
