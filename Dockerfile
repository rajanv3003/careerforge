# CareerForge — Node app that shells out to headless Chromium + Python (stdlib only)
# for the banner images and designed PDFs. This image bundles all three.
FROM node:20-slim

ENV NODE_ENV=production \
    CHROME_PATH=/usr/bin/chromium \
    PORT=3080

# Chromium (for banner/PDF rendering), Python 3 (the render scripts), and fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium \
      python3 \
      ca-certificates \
      fontconfig \
      fonts-liberation \
      fonts-dejavu-core \
      fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install node deps first (better build caching)
COPY package*.json ./
RUN npm ci --omit=dev

# App source
COPY . .

EXPOSE 3080
CMD ["node", "server.js"]
