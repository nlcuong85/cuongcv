#!/usr/bin/env bash
set -euo pipefail

echo "[cv-app] Installing deps (pnpm)"
if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm is not installed. Install with: npm i -g pnpm" >&2
  exit 1
fi

pnpm install --frozen-lockfile

echo "[cv-app] Building Next.js (production)"
pnpm build

echo "[cv-app] Starting with PM2"
if ! command -v pm2 >/dev/null 2>&1; then
  echo "pm2 is not installed. Install with: npm i -g pm2" >&2
  exit 1
fi

mkdir -p ./logs
pm2 start ecosystem.config.js --update-env
pm2 save
pm2 status

echo "[cv-app] Done. Listening on PORT=${PORT:-3000}"

