# CareerForge — 1CR Career OS

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rajanv3003/careerforge)

**One-click deploy:** click the button above (sign in with GitHub), paste your keys when
asked, and Render gives you a permanent `https://<name>.onrender.com` link.

An AI agent suite for job seekers targeting ₹1 Crore+ roles: Resume, LinkedIn
Positioning (banner + headline + About), Outreach, and Interview Prep.

Node (Express) + a vanilla-JS single-page UI. Banner images and designed PDFs are
rendered with headless Chromium driven by small Python (stdlib-only) scripts.

## Run locally

```bash
npm install
cp .env.example .env      # then fill in your keys
npm start                 # http://localhost:3080  (or the PORT you set)
```

Requires **Node 18+**, **Python 3**, and **Google Chrome / Chromium** on the machine.

## Deploy (permanent, always-on)

This repo ships a **Dockerfile** (bundles Node + Python + Chromium) and a
**render.yaml** Blueprint.

### Render (recommended, easiest)
1. Push this repo to GitHub (already done).
2. Create a free account at https://render.com and connect GitHub.
3. **New → Blueprint** → pick this repo. Render reads `render.yaml` and builds the Dockerfile.
4. Fill in the secret env vars when prompted (see the list below).
5. Deploy. You get a permanent `https://<name>.onrender.com` URL that never changes.

Any host that can build a Dockerfile (Railway, Fly.io, a VPS) works the same way.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `DEEPSEEK_API_KEY` | yes (primary brain) | DeepSeek `sk-...` key — powers all text agents |
| `DEEPSEEK_MODEL` | no | defaults to `deepseek-v4-flash` |
| `DEEPSEEK_BASE_URL` | no | defaults to `https://api.deepseek.com/v1` |
| `GEMINI_API_KEY` | optional | a real `AIza...` key — used only if DeepSeek is unset |
| `GEMINI_MODEL` | no | defaults to `gemini-2.5-flash` |
| `GATHOS_IMAGE_API_KEY` | optional | AI cover-image generation |
| `GATHOS_I2I_API_KEY` | optional | image-to-image |
| `GATHOS_TTS_API_KEY` | optional | voice for interview practice |
| `GATHOS_BASE_URL` | no | defaults to `https://gathos.com/api/v1` |
| `CHROME_PATH` | no | path to Chromium (Docker sets `/usr/bin/chromium`) |
| `PORT` | no | the host sets this automatically |

**Never commit real keys.** `.env` is gitignored; use `.env.example` as the template.
