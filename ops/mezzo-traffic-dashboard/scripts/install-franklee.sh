#!/usr/bin/env bash
set -euo pipefail

target="${1:-root@100.124.166.95}"
kit_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing Mezzo traffic dashboard on ${target}"

ssh "${target}" 'set -e
install -d -m 0755 /usr/local/lib/mezzo-traffic
install -d -m 0755 /var/lib/mezzo-traffic
install -d -m 0755 /etc/systemd/system
'

scp "${kit_dir}/traffic_dashboard.py" "${target}:/usr/local/lib/mezzo-traffic/traffic_dashboard.py"
scp "${kit_dir}/systemd/franklee/traffic-dashboard.service" "${target}:/etc/systemd/system/traffic-dashboard.service"
scp "${kit_dir}/systemd/franklee/traffic-collect.service" "${target}:/etc/systemd/system/traffic-collect.service"
scp "${kit_dir}/systemd/franklee/traffic-collect.timer" "${target}:/etc/systemd/system/traffic-collect.timer"

ssh "${target}" 'set -e
chmod 0755 /usr/local/lib/mezzo-traffic/traffic_dashboard.py
python3 -m py_compile /usr/local/lib/mezzo-traffic/traffic_dashboard.py
systemctl daemon-reload
systemctl restart traffic-dashboard.service
systemctl enable --now traffic-collect.timer
systemctl start traffic-collect.service || true
sleep 1
systemctl --no-pager --full status traffic-dashboard.service | sed -n "1,18p"
systemctl --no-pager --full status traffic-collect.timer | sed -n "1,18p"
curl -fsS http://100.124.166.95:3030/traffic/api/summary >/dev/null
'

echo "Franklee traffic dashboard install complete."
