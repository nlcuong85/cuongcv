# Mezzo Traffic Dashboard Disaster Recovery Kit

This folder is the repo-backed rebuild kit for the private traffic dashboard at:

- `http://mezzo.phoenix-scala.ts.net/traffic`

The dashboard is intentionally private and tailnet-only. It is not the public Job MCP app.

## Architecture

```text
Visitor / investor-facing owner view
        |
        v
Mezzo Tailscale Serve
  http://mezzo.phoenix-scala.ts.net/traffic
        |
        v
Mezzo local relay
  mezzo-traffic-relay.service
  127.0.0.1:3031 -> 100.124.166.95:3030
        |
        v
Franklee dashboard service
  traffic-dashboard.service
  /usr/local/lib/mezzo-traffic/traffic_dashboard.py --serve --host 100.124.166.95
        |
        v
Franklee SQLite DB
  /var/lib/mezzo-traffic/traffic.sqlite
```

The collector runs on Franklee every minute:

- `traffic-collect.timer`
- `traffic-collect.service`
- `/usr/local/lib/mezzo-traffic/traffic_dashboard.py`

It aggregates:

- Nginx Proxy Manager access logs for selected WordPress sites.
- Docker network counters for Invidious containers.
- Job MCP `MCP_METRIC` and `MCP_VISIT` container log lines.

## Privacy boundary

Preserve this boundary when changing the dashboard:

- Do not log raw IP addresses.
- Do not log request bodies or response bodies.
- Do not log CVs, job descriptions, writing text, prompts, cookies, auth headers, or MCP session IDs.
- Unique visitors are salted hashes emitted by Job MCP.
- Location analytics use coarse Cloudflare headers such as `cf-ipcity`, `cf-ipcountry`, and `cf-timezone`.

Cloudflare Managed Transform status:

- `pmlecuong.com > Rules > Transform Rules > Managed Transforms > Add visitor location headers`
- Enabled on 2026-09-16.
- Verified through `https://jobmcp.pmlecuong.com/start`: Franklee received city `Heilbronn`, country `DE`, timezone `Europe/Berlin`.

Older DB rows from before the transform was enabled may still show city as `unknown`.

## Files in this kit

- `traffic_dashboard.py` — canonical dashboard/collector script.
- `systemd/franklee/traffic-dashboard.service` — serves the dashboard on Franklee tailnet IP.
- `systemd/franklee/traffic-collect.service` — one-shot collector.
- `systemd/franklee/traffic-collect.timer` — every-minute collector timer.
- `systemd/mezzo/mezzo-traffic-relay.service` — optional local relay on Mezzo.
- `scripts/install-franklee.sh` — install/update dashboard service on Franklee.
- `scripts/install-mezzo.sh` — install/update relay and Tailscale Serve route on Mezzo.
- `scripts/backup-db.sh` — copy Franklee SQLite DB into a timestamped local backup.
- `scripts/restore-db.sh` — restore a selected backup to Franklee.

## Current live hosts

- Franklee SSH: `root@100.124.166.95`
- Mezzo SSH: `cuong@100.83.8.41`
- Franklee dashboard bind: `100.124.166.95:3030`
- Mezzo relay bind: `127.0.0.1:3031`
- Public tailnet URL: `http://mezzo.phoenix-scala.ts.net/traffic`

## Cold rebuild: Franklee side

From the repo root on this Mac:

```bash
ops/mezzo-traffic-dashboard/scripts/install-franklee.sh root@100.124.166.95
```

Then verify:

```bash
ssh root@100.124.166.95 'systemctl status traffic-dashboard.service --no-pager'
ssh root@100.124.166.95 'systemctl status traffic-collect.timer --no-pager'
ssh root@100.124.166.95 'curl -fsS http://100.124.166.95:3030/traffic/api/summary | python3 -m json.tool | head'
```

## Cold rebuild: Mezzo side

From the repo root on this Mac:

```bash
ops/mezzo-traffic-dashboard/scripts/install-mezzo.sh cuong@100.83.8.41
```

Then verify:

```bash
ssh cuong@100.83.8.41 'systemctl status mezzo-traffic-relay.service --no-pager'
ssh cuong@100.83.8.41 'curl -fsS http://127.0.0.1:3031/traffic/api/summary | python3 -m json.tool | head'
curl -fsS http://mezzo.phoenix-scala.ts.net/traffic/api/summary | python3 -m json.tool | head
```

## Tailscale Serve contract

Current observed state on Mezzo:

```text
https://mezzo.phoenix-scala.ts.net (tailnet only)
|-- /traffic proxy http://100.124.166.95:3030

http://mezzo (tailnet only)
http://mezzo.phoenix-scala.ts.net (tailnet only)
|-- /        proxy http://127.0.0.1:3001
|-- /traffic proxy http://127.0.0.1:3031
```

The install script preserves the normal HTTP route:

```bash
tailscale serve --bg --http=80 /traffic http://127.0.0.1:3031
```

If Tailscale Serve syntax changes, inspect with:

```bash
tailscale serve status
```

## DB backup and restore

Back up the current Franklee DB to the local repo workspace:

```bash
ops/mezzo-traffic-dashboard/scripts/backup-db.sh root@100.124.166.95
```

Backups are written under:

- `ops/mezzo-traffic-dashboard/backups/`

That folder is gitignored except `.gitkeep`; do not commit live analytics history unless the user explicitly asks.

Restore a chosen backup:

```bash
ops/mezzo-traffic-dashboard/scripts/restore-db.sh root@100.124.166.95 ops/mezzo-traffic-dashboard/backups/traffic-YYYYmmddTHHMMSSZ.sqlite
```

The restore script stops the collector/dashboard services, saves a remote pre-restore DB copy, uploads the selected DB, then restarts services.

## Verification checklist

After rebuild:

1. `python3 -m py_compile /usr/local/lib/mezzo-traffic/traffic_dashboard.py` passes on Franklee.
2. `traffic-dashboard.service` is running.
3. `traffic-collect.timer` is active.
4. `curl http://100.124.166.95:3030/traffic/api/summary` returns JSON.
5. `mezzo-traffic-relay.service` is running on Mezzo.
6. `curl http://127.0.0.1:3031/traffic/api/summary` works on Mezzo.
7. `curl http://mezzo.phoenix-scala.ts.net/traffic/api/summary` works from this Mac.
8. Browser dashboard shows `Job MCP`, `Countries today`, and `Cities today`.

