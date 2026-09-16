#!/usr/bin/env bash
set -euo pipefail

target="${1:-cuong@100.83.8.41}"
kit_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing Mezzo traffic relay on ${target}"

scp "${kit_dir}/systemd/mezzo/mezzo-traffic-relay.service" "${target}:/tmp/mezzo-traffic-relay.service"

ssh "${target}" 'set -e
if command -v sudo >/dev/null 2>&1; then
  sudo install -m 0644 /tmp/mezzo-traffic-relay.service /etc/systemd/system/mezzo-traffic-relay.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now mezzo-traffic-relay.service
else
  install -m 0644 /tmp/mezzo-traffic-relay.service /etc/systemd/system/mezzo-traffic-relay.service
  systemctl daemon-reload
  systemctl enable --now mezzo-traffic-relay.service
fi
rm -f /tmp/mezzo-traffic-relay.service
if command -v tailscale >/dev/null 2>&1; then
  tailscale serve --bg --http=80 /traffic http://127.0.0.1:3031
fi
sleep 1
systemctl --no-pager --full status mezzo-traffic-relay.service | sed -n "1,18p"
curl -fsS http://127.0.0.1:3031/traffic/api/summary >/dev/null
'

echo "Mezzo traffic relay install complete."

