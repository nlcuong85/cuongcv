#!/usr/bin/env bash
set -euo pipefail

target="${1:-root@100.124.166.95}"
kit_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backup_dir="${kit_dir}/backups"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="${backup_dir}/traffic-${stamp}.sqlite"

mkdir -p "${backup_dir}"

ssh "${target}" 'set -e
test -f /var/lib/mezzo-traffic/traffic.sqlite
python3 - <<'"'"'PY'"'"'
import sqlite3
con = sqlite3.connect("/var/lib/mezzo-traffic/traffic.sqlite")
result = con.execute("PRAGMA quick_check").fetchone()[0]
con.close()
raise SystemExit(0 if result == "ok" else 1)
PY
'

scp "${target}:/var/lib/mezzo-traffic/traffic.sqlite" "${out}"

python3 - "${out}" <<'PY'
import sqlite3
import sys
con = sqlite3.connect(sys.argv[1])
result = con.execute("PRAGMA quick_check").fetchone()[0]
con.close()
raise SystemExit(0 if result == "ok" else 1)
PY
du -h "${out}"
echo "Backup written: ${out}"
