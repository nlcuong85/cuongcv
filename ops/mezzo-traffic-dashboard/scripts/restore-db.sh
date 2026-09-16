#!/usr/bin/env bash
set -euo pipefail

target="${1:-}"
backup="${2:-}"

if [[ -z "${target}" || -z "${backup}" ]]; then
  echo "Usage: $0 root@100.124.166.95 path/to/traffic-backup.sqlite" >&2
  exit 2
fi

if [[ ! -f "${backup}" ]]; then
  echo "Backup file not found: ${backup}" >&2
  exit 2
fi

python3 - "${backup}" <<'PY'
import sqlite3
import sys
con = sqlite3.connect(sys.argv[1])
result = con.execute("PRAGMA quick_check").fetchone()[0]
con.close()
raise SystemExit(0 if result == "ok" else 1)
PY

remote_tmp="/tmp/traffic-restore-$(date -u +%Y%m%dT%H%M%SZ).sqlite"
scp "${backup}" "${target}:${remote_tmp}"

ssh "${target}" "set -e
python3 - <<'PY'
import sqlite3
con = sqlite3.connect('${remote_tmp}')
result = con.execute('PRAGMA quick_check').fetchone()[0]
con.close()
raise SystemExit(0 if result == 'ok' else 1)
PY
systemctl stop traffic-collect.timer traffic-dashboard.service || true
if [ -f /var/lib/mezzo-traffic/traffic.sqlite ]; then
  cp -p /var/lib/mezzo-traffic/traffic.sqlite /var/lib/mezzo-traffic/traffic.sqlite.pre-restore-\$(date -u +%Y%m%dT%H%M%SZ)
fi
install -m 0644 '${remote_tmp}' /var/lib/mezzo-traffic/traffic.sqlite
rm -f '${remote_tmp}'
systemctl start traffic-dashboard.service
systemctl start traffic-collect.timer
sleep 1
curl -fsS http://100.124.166.95:3030/traffic/api/summary >/dev/null
"

echo "Restore complete."
