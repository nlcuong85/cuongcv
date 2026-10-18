#!/usr/bin/env python3
"""Private, low-overhead traffic dashboard for the Mezzo control plane."""
from __future__ import annotations

import argparse, json, os, re, sqlite3, subprocess, time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DB = Path(os.environ.get('MEZZO_TRAFFIC_DB', '/var/lib/mezzo-traffic/traffic.sqlite'))
LOGS = {
    'pmlecuong.com': Path('/DATA/AppData/nginxproxymanager/data/logs/proxy-host-2_access.log'),
    'maytrevannguyen.com': Path('/DATA/AppData/nginxproxymanager/data/logs/proxy-host-3_access.log'),
    'trangluc.com': Path('/DATA/AppData/nginxproxymanager/data/logs/proxy-host-4_access.log'),
    'productvn.com': Path('/DATA/AppData/nginxproxymanager/data/logs/proxy-host-5_access.log'),
    'tranjstudio.com': Path('/DATA/AppData/nginxproxymanager/data/logs/proxy-host-6_access.log'),
    'sinewiz.me': Path('/DATA/AppData/nginxproxymanager/data/logs/proxy-host-7_access.log'),
}
MCP_CONTAINER = 'application-package-mcp'
LINE = re.compile(r'^\[([^]]+)\].*? - (\d{3}) \d{3} - .*? \[Length (\d+)\]')
UNITS = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}

def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute('create table if not exists offsets (path text primary key, pos integer not null)')
    c.execute('create table if not exists web (bucket integer, site text, requests integer, bytes integer, errors integer, primary key(bucket,site))')
    c.execute('create table if not exists counters (name text primary key, rx integer, tx integer)')
    c.execute('create table if not exists containers (bucket integer, name text, rx integer, tx integer, primary key(bucket,name))')
    c.execute('create table if not exists mcp (bucket integer primary key, calls integer, initializations integer, errors integer, latency_ms integer)')
    c.execute('create table if not exists mcp_tools (bucket integer, tool text, calls integer, errors integer, primary key(bucket,tool))')
    c.execute('create table if not exists mcp_visits (bucket integer, visitor_hash text, country text, region text, city text, timezone text, colo text, client text, route_group text, method text, status integer, hits integer, primary key(bucket,visitor_hash,route_group,method,status))')
    return c

def collect_web(c):
    for site, path in LOGS.items():
        if not path.exists(): continue
        size = path.stat().st_size
        old = c.execute('select pos from offsets where path=?', (str(path),)).fetchone()
        pos = old[0] if old else 0
        if pos > size: pos = 0
        with path.open('r', errors='replace') as f:
            f.seek(pos)
            for line in f:
                m = LINE.match(line)
                if not m: continue
                try: bucket = int(datetime.strptime(m.group(1), '%d/%b/%Y:%H:%M:%S %z').timestamp()) // 60 * 60
                except ValueError: continue
                status, length = int(m.group(2)), int(m.group(3))
                c.execute('insert into web values(?,?,?,?,?) on conflict(bucket,site) do update set requests=requests+1, bytes=bytes+excluded.bytes, errors=errors+excluded.errors', (bucket,site,1,length,int(status >= 400)))
            pos = f.tell()
        c.execute('insert into offsets values(?,?) on conflict(path) do update set pos=excluded.pos', (str(path),pos))

def as_bytes(value):
    m = re.match(r'([0-9.]+)\s*([KMGT]?B)', value.strip())
    return int(float(m.group(1)) * UNITS[m.group(2)]) if m else 0

def collect_containers(c):
    out = subprocess.run(['docker','stats','--no-stream','--format','{{.Name}}\t{{.NetIO}}'], capture_output=True, text=True, check=False).stdout
    bucket = int(time.time()) // 60 * 60
    for line in out.splitlines():
        if '\t' not in line: continue
        name, net = line.split('\t', 1)
        if name not in ('invidious','invidious-companion'): continue
        parts = net.split(' / ')
        if len(parts) != 2: continue
        rx, tx = as_bytes(parts[0]), as_bytes(parts[1])
        previous = c.execute('select rx,tx from counters where name=?',(name,)).fetchone()
        drx, dtx = (0,0) if not previous else (max(0,rx-previous[0]),max(0,tx-previous[1]))
        c.execute('insert into containers values(?,?,?,?) on conflict(bucket,name) do update set rx=rx+excluded.rx,tx=tx+excluded.tx',(bucket,name,drx,dtx))
        c.execute('insert into counters values(?,?,?) on conflict(name) do update set rx=excluded.rx,tx=excluded.tx',(name,rx,tx))

def collect_mcp(c):
    path_text = subprocess.run(['docker', 'inspect', MCP_CONTAINER, '--format', '{{.LogPath}}'], capture_output=True, text=True, check=False).stdout.strip()
    if not path_text: return
    path = Path(path_text)
    if not path.exists(): return
    size = path.stat().st_size
    old = c.execute('select pos from offsets where path=?', (str(path),)).fetchone()
    pos = old[0] if old else 0
    if pos > size: pos = 0
    with path.open('r', errors='replace') as f:
        f.seek(pos)
        for line in f:
            try:
                entry = json.loads(line)
                message = entry.get('log', '').strip()
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
            if message.startswith('MCP_METRIC '):
                try:
                    metric = json.loads(message[len('MCP_METRIC '):])
                    bucket = int(datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00')).timestamp()) // 60 * 60
                    method = str(metric.get('rpcMethod', 'invalid'))[:120]
                    tool = str(metric.get('tool') or method)[:120]
                    status = int(metric.get('status', 500))
                    duration = max(0, int(metric.get('durationMs', 0)))
                except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                    continue
                is_error = int(status >= 400)
                is_initialization = int(method == 'initialize' and status < 400)
                c.execute('insert into mcp values(?,?,?,?,?) on conflict(bucket) do update set calls=calls+1,initializations=initializations+excluded.initializations,errors=errors+excluded.errors,latency_ms=latency_ms+excluded.latency_ms', (bucket, 1, is_initialization, is_error, duration))
                c.execute('insert into mcp_tools values(?,?,?,?) on conflict(bucket,tool) do update set calls=calls+1,errors=errors+excluded.errors', (bucket, tool, 1, is_error))
            elif message.startswith('MCP_VISIT '):
                try:
                    visit = json.loads(message[len('MCP_VISIT '):])
                    bucket = int(datetime.fromisoformat(visit['timestamp'].replace('Z', '+00:00')).timestamp()) // 60 * 60
                    visitor_hash = str(visit.get('visitorHash') or 'unknown')[:64]
                    country = str(visit.get('country') or 'unknown')[:80]
                    region = str(visit.get('region') or 'unknown')[:80]
                    city = str(visit.get('city') or 'unknown')[:80]
                    timezone = str(visit.get('timezone') or 'unknown')[:80]
                    colo = str(visit.get('colo') or 'unknown')[:40]
                    client = str(visit.get('client') or 'unknown')[:40]
                    route_group = str(visit.get('routeGroup') or 'other')[:80]
                    method = str(visit.get('method') or 'UNKNOWN')[:16]
                    status = int(visit.get('status', 0))
                except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                    continue
                c.execute('insert into mcp_visits values(?,?,?,?,?,?,?,?,?,?,?,?) on conflict(bucket,visitor_hash,route_group,method,status) do update set hits=hits+1,country=excluded.country,region=excluded.region,city=excluded.city,timezone=excluded.timezone,colo=excluded.colo,client=excluded.client', (bucket, visitor_hash, country, region, city, timezone, colo, client, route_group, method, status, 1))
        pos = f.tell()
    c.execute('insert into offsets values(?,?) on conflict(path) do update set pos=excluded.pos', (str(path), pos))

def mcp_healthy():
    result = subprocess.run(['curl', '-fsS', '--max-time', '5', 'http://127.0.0.1:5920/health'], capture_output=True, text=True, check=False)
    return result.returncode == 0

def collect():
    c=db(); collect_web(c); collect_containers(c); collect_mcp(c); c.commit(); c.close()

def bounded_where(start, end, expression='bucket'):
    clauses, values = [], []
    if start is not None:
        clauses.append(f'{expression} >= ?')
        values.append(start)
    if end is not None:
        clauses.append(f'{expression} < ?')
        values.append(end)
    return (' where ' + ' and '.join(clauses) if clauses else ''), values


def payload(start=None, end=None):
    where, bounds = bounded_where(start, end)
    range_clause = where.strip()[6:] if where else ''
    human_where = "route_group not in ('health','asset') and client != 'bot_or_monitor'"
    visit_where = f' where {human_where}' + (f' and {range_clause}' if range_clause else '')
    c = db()

    sites = []
    for site in LOGS:
        row = c.execute(
            'select coalesce(sum(requests),0),coalesce(sum(bytes),0),coalesce(sum(errors),0) '
            'from web where site=?' + (f' and {range_clause}' if range_clause else ''),
            [site, *bounds],
        ).fetchone()
        sites.append({'site': site, 'requests': row[0], 'bytes': row[1], 'errors': row[2]})

    invidious = []
    for name in ('invidious', 'invidious-companion'):
        row = c.execute(
            'select coalesce(sum(rx),0),coalesce(sum(tx),0) from containers where name=?'
            + (f' and {range_clause}' if range_clause else ''),
            [name, *bounds],
        ).fetchone()
        invidious.append({'name': name, 'received': row[0], 'sent': row[1]})

    metrics = c.execute(
        'select coalesce(sum(calls),0),coalesce(sum(initializations),0),'
        'coalesce(sum(errors),0),coalesce(sum(latency_ms),0) from mcp' + where,
        bounds,
    ).fetchone()
    metrics_since = c.execute('select min(bucket) from mcp' + where, bounds).fetchone()[0]
    visit_totals = c.execute(
        f'select count(distinct visitor_hash),coalesce(sum(hits),0) from mcp_visits{visit_where}',
        bounds,
    ).fetchone()
    tools = [
        {'tool': tool, 'calls': calls, 'errors': errors}
        for tool, calls, errors in c.execute(
            'select tool,coalesce(sum(calls),0),coalesce(sum(errors),0) from mcp_tools'
            + where + ' group by tool order by 2 desc,1', bounds,
        )
    ]
    countries = [
        {'country': country, 'uniqueVisitors': unique_visitors, 'visits': hits}
        for country, unique_visitors, hits in c.execute(
            f'select country,count(distinct visitor_hash),sum(hits) from mcp_visits{visit_where} '
            'group by country order by 3 desc,2 desc', bounds,
        )
    ]
    cities = [
        {'city': city, 'region': region, 'country': country,
         'uniqueVisitors': unique_visitors, 'visits': hits}
        for city, region, country, unique_visitors, hits in c.execute(
            f'select city,region,country,count(distinct visitor_hash),sum(hits) '
            f'from mcp_visits{visit_where} group by city,region,country order by 5 desc,4 desc', bounds,
        )
    ]
    routes = [
        {'routeGroup': route, 'uniqueVisitors': unique_visitors, 'visits': hits}
        for route, unique_visitors, hits in c.execute(
            f'select route_group,count(distinct visitor_hash),sum(hits) from mcp_visits{visit_where} '
            'group by route_group order by 3 desc', bounds,
        )
    ]
    clients = [
        {'client': client, 'uniqueVisitors': unique_visitors, 'visits': hits}
        for client, unique_visitors, hits in c.execute(
            f'select client,count(distinct visitor_hash),sum(hits) from mcp_visits{visit_where} '
            'group by client order by 3 desc', bounds,
        )
    ]
    c.close()
    return {
        'updatedAt': datetime.now(timezone.utc).isoformat(),
        'range': {'from': start, 'to': end}, 'sites': sites, 'invidious': invidious,
        'mcp': {
            'healthy': mcp_healthy(), 'calls': metrics[0], 'sessionsStarted': metrics[1],
            'failures': metrics[2], 'averageResponseMs': round(metrics[3] / metrics[0]) if metrics[0] else 0,
            'uniqueVisitorHashes': visit_totals[0], 'visits': visit_totals[1],
            'metricsSince': datetime.fromtimestamp(metrics_since, timezone.utc).isoformat() if metrics_since else None,
            'countries': countries, 'cities': cities, 'routes': routes, 'clients': clients, 'tools': tools,
        },
    }

HTML = Path(__file__).with_name('traffic_dashboard.html').read_text()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path.rstrip('/').endswith('/api/summary'):
            query = parse_qs(parsed.query)
            try:
                start = int(query['from'][0]) if query.get('from') else None
                end = int(query['to'][0]) if query.get('to') else None
                if start is not None and end is not None and start >= end:
                    raise ValueError('The start date must be before the end date.')
                body = json.dumps(payload(start, end)).encode()
                self.send_response(200)
            except ValueError as error:
                body = json.dumps({'error': str(error) or 'Dates must be Unix timestamps in seconds.'}).encode()
                self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = HTML.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args): pass

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--serve',action='store_true'); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=3030); a=p.parse_args()
    if a.serve: ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
    else: collect()
