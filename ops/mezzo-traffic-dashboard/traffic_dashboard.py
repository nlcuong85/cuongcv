#!/usr/bin/env python3
"""Private, low-overhead traffic dashboard for the Mezzo control plane."""
from __future__ import annotations

import argparse, json, re, sqlite3, subprocess, time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DB = Path('/var/lib/mezzo-traffic/traffic.sqlite')
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

def payload():
    c=db(); now=int(time.time()); hour=now-3600; day=now-86400
    sites=[]
    for site in LOGS:
        r=c.execute('select coalesce(sum(requests),0),coalesce(sum(bytes),0),coalesce(sum(errors),0) from web where site=? and bucket>=?',(site,hour)).fetchone()
        d=c.execute('select coalesce(sum(requests),0),coalesce(sum(bytes),0) from web where site=? and bucket>=?',(site,day)).fetchone()
        sites.append({'site':site,'requestsHour':r[0],'bytesHour':r[1],'errorsHour':r[2],'requestsDay':d[0],'bytesDay':d[1]})
    inv=[]
    for name in ('invidious','invidious-companion'):
        r=c.execute('select coalesce(sum(rx),0),coalesce(sum(tx),0) from containers where name=? and bucket>=?',(name,hour)).fetchone()
        total=c.execute('select rx,tx from counters where name=?',(name,)).fetchone() or (0,0)
        inv.append({'name':name,'receivedHour':r[0],'sentHour':r[1],'receivedTotal':total[0],'sentTotal':total[1]})
    mcp_hour=c.execute('select coalesce(sum(calls),0),coalesce(sum(initializations),0),coalesce(sum(errors),0),coalesce(sum(latency_ms),0) from mcp where bucket>=?',(hour,)).fetchone()
    mcp_day=c.execute('select coalesce(sum(calls),0),coalesce(sum(initializations),0),coalesce(sum(errors),0),coalesce(sum(latency_ms),0) from mcp where bucket>=?',(day,)).fetchone()
    mcp_all=c.execute('select min(bucket),coalesce(sum(calls),0),coalesce(sum(initializations),0),coalesce(sum(errors),0) from mcp').fetchone()
    human_where = "route_group not in ('health','asset') and client != 'bot_or_monitor'"
    unique_hour=c.execute(f"select count(distinct visitor_hash) from mcp_visits where bucket>=? and {human_where}",(hour,)).fetchone()[0]
    unique_day=c.execute(f"select count(distinct visitor_hash) from mcp_visits where bucket>=? and {human_where}",(day,)).fetchone()[0]
    unique_all=c.execute(f"select count(distinct visitor_hash) from mcp_visits where {human_where}").fetchone()[0]
    visits_hour=c.execute(f"select coalesce(sum(hits),0) from mcp_visits where bucket>=? and {human_where}",(hour,)).fetchone()[0]
    visits_day=c.execute(f"select coalesce(sum(hits),0) from mcp_visits where bucket>=? and {human_where}",(day,)).fetchone()[0]
    tools=[]
    for tool, calls_hour, errors_hour, calls_day in c.execute('select mt.tool,(select coalesce(sum(h.calls),0) from mcp_tools h where h.tool=mt.tool and h.bucket>=?),(select coalesce(sum(h.errors),0) from mcp_tools h where h.tool=mt.tool and h.bucket>=?),coalesce(sum(mt.calls),0) from mcp_tools mt where mt.bucket>=? group by mt.tool order by 4 desc,1',(hour,hour,day)):
        tools.append({'tool':tool,'callsHour':calls_hour,'errorsHour':errors_hour,'callsDay':calls_day})
    countries=[]
    for country, uniques, hits in c.execute(f"select country,count(distinct visitor_hash),sum(hits) from mcp_visits where bucket>=? and {human_where} group by country order by 2 desc,3 desc limit 12",(day,)):
        countries.append({'country':country,'uniqueDay':uniques,'hitsDay':hits})
    cities=[]
    for city, region, country, uniques, hits in c.execute(f"select city,region,country,count(distinct visitor_hash),sum(hits) from mcp_visits where bucket>=? and {human_where} group by city,region,country order by 4 desc,5 desc limit 15",(day,)):
        cities.append({'city':city,'region':region,'country':country,'uniqueDay':uniques,'hitsDay':hits})
    routes=[]
    for route_group, uniques, hits in c.execute(f"select route_group,count(distinct visitor_hash),sum(hits) from mcp_visits where bucket>=? and {human_where} group by route_group order by 3 desc limit 12",(day,)):
        routes.append({'routeGroup':route_group,'uniqueDay':uniques,'hitsDay':hits})
    clients=[]
    for client, uniques, hits in c.execute(f"select client,count(distinct visitor_hash),sum(hits) from mcp_visits where bucket>=? and {human_where} group by client order by 3 desc limit 8",(day,)):
        clients.append({'client':client,'uniqueDay':uniques,'hitsDay':hits})
    c.close(); return {'updatedAt':datetime.now(timezone.utc).isoformat(),'sites':sites,'invidious':inv,'mcp':{'healthy':mcp_healthy(),'callsHour':mcp_hour[0],'initializationsHour':mcp_hour[1],'errorsHour':mcp_hour[2],'avgLatencyHour':round(mcp_hour[3]/mcp_hour[0]) if mcp_hour[0] else 0,'callsDay':mcp_day[0],'initializationsDay':mcp_day[1],'errorsDay':mcp_day[2],'callsAll':mcp_all[1],'initializationsAll':mcp_all[2],'errorsAll':mcp_all[3],'metricsSince':datetime.fromtimestamp(mcp_all[0], timezone.utc).isoformat() if mcp_all[0] else None,'uniqueHour':unique_hour,'uniqueDay':unique_day,'uniqueAll':unique_all,'visitsHour':visits_hour,'visitsDay':visits_day,'countries':countries,'cities':cities,'routes':routes,'clients':clients,'tools':tools}}

HTML = '''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mezzo Traffic</title><style>body{font:16px system-ui;background:#101828;color:#eef2f7;margin:0;padding:28px}h1{margin:0 0 8px}p{color:#aeb9c7}section{background:#182435;border-radius:12px;padding:18px;margin:18px 0}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #2a3a4e}.ok{color:#53d58b}.bad{color:#ff6b6b}.muted{color:#aeb9c7}.stats{display:flex;flex-wrap:wrap;gap:18px}.stats div{min-width:130px}.stats b{display:block;font-size:24px;color:#eef2f7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px}.panel{background:#111b2b;border:1px solid #26374c;border-radius:10px;padding:14px}small{color:#93a4b8}</style><h1>Mezzo Traffic</h1><p>Private traffic view. Refreshes every minute.</p><section><h2>Job MCP</h2><div id="mcp"></div><div class="grid"><div class="panel"><h3>Countries today</h3><table><thead><tr><th>Country</th><th>Unique</th><th>Hits</th></tr></thead><tbody id="countries"></tbody></table></div><div class="panel"><h3>Cities today</h3><table><thead><tr><th>City</th><th>Country</th><th>Unique</th><th>Hits</th></tr></thead><tbody id="cities"></tbody></table><small>City appears only when Cloudflare visitor-location headers are enabled.</small></div></div><div class="grid"><div class="panel"><h3>Routes today</h3><table><thead><tr><th>Route</th><th>Unique</th><th>Hits</th></tr></thead><tbody id="routes"></tbody></table></div><div class="panel"><h3>Client mix today</h3><table><thead><tr><th>Client</th><th>Unique</th><th>Hits</th></tr></thead><tbody id="clients"></tbody></table></div></div><table><thead><tr><th>Tool / protocol operation</th><th>Calls (1h)</th><th>Errors (1h)</th><th>Calls (24h)</th></tr></thead><tbody id="mcpTools"></tbody></table><p class="muted">Unique visitors are salted hashes from request metadata. No raw IPs, request bodies, response bodies, CVs, or writing text are stored. City/country are coarse edge headers when available.</p></section><section><h2>YouTube / Invidious</h2><div id="inv"></div></section><section><h2>WordPress traffic</h2><table><thead><tr><th>Site</th><th>Requests (1h)</th><th>Data (1h)</th><th>Errors (1h)</th><th>Requests (24h)</th><th>Data (24h)</th></tr></thead><tbody id="sites"></tbody></table></section><p class="muted" id="updated"></p><script>const b=n=>{for(const u of['B','KB','MB','GB','TB']){if(n<1024)return n.toFixed(n<10&&u!='B'?1:0)+' '+u;n/=1024}return n.toFixed(1)+' PB'};const rows=(arr,cols,empty)=>arr&&arr.length?arr.map(x=>`<tr>${cols.map(c=>`<td>${c(x)}</td>`).join('')}</tr>`).join(''):`<tr><td colspan="9" class="muted">${empty}</td></tr>`;async function load(){let d=await fetch(location.pathname.replace(/\\/$/,'')+'/api/summary').then(r=>r.json());let m=d.mcp;mcp.innerHTML=`<p class="${m.healthy?'ok':'bad'}"><b>${m.healthy?'Healthy':'Unavailable'}</b></p><div class="stats"><div><span>Unique visitors (1h)</span><b>${m.uniqueHour}</b></div><div><span>Unique visitors (24h)</span><b>${m.uniqueDay}</b></div><div><span>Unique since tracking</span><b>${m.uniqueAll}</b></div><div><span>Visits (24h)</span><b>${m.visitsDay}</b></div><div><span>MCP calls (24h)</span><b>${m.callsDay}</b></div><div><span>Sessions started (24h)</span><b>${m.initializationsDay}</b></div><div><span>Failures (24h)</span><b>${m.errorsDay}</b></div><div><span>Avg response</span><b>${m.avgLatencyHour} ms</b></div></div><p class="muted">Metric history since ${m.metricsSince?new Date(m.metricsSince).toLocaleString():'now'} · ${m.callsAll} total MCP events</p>`;countries.innerHTML=rows(m.countries,[x=>x.country,x=>x.uniqueDay,x=>x.hitsDay],'No country data yet.');cities.innerHTML=rows(m.cities,[x=>x.city,x=>[x.region,x.country].filter(v=>v&&v!='unknown').join(', ')||x.country,x=>x.uniqueDay,x=>x.hitsDay],'No city data yet. Enable Cloudflare visitor-location headers.');routes.innerHTML=rows(m.routes,[x=>x.routeGroup,x=>x.uniqueDay,x=>x.hitsDay],'No route visits yet.');clients.innerHTML=rows(m.clients,[x=>x.client,x=>x.uniqueDay,x=>x.hitsDay],'No client data yet.');mcpTools.innerHTML=m.tools.map(x=>`<tr><td>${x.tool}</td><td>${x.callsHour}</td><td class="${x.errorsHour?'bad':'ok'}">${x.errorsHour}</td><td>${x.callsDay}</td></tr>`).join('')||'<tr><td colspan="4" class="muted">No tool metrics yet.</td></tr>';inv.innerHTML=d.invidious.map(x=>`<p><b>${x.name}</b>: last hour ↓ ${b(x.receivedHour)} ↑ ${b(x.sentHour)} <span class=muted>· cumulative ↓ ${b(x.receivedTotal)} ↑ ${b(x.sentTotal)}</span></p>`).join('');sites.innerHTML=d.sites.map(x=>`<tr><td class=ok>${x.site}</td><td>${x.requestsHour}</td><td>${b(x.bytesHour)}</td><td>${x.errorsHour}</td><td>${x.requestsDay}</td><td>${b(x.bytesDay)}</td></tr>`).join('');updated.textContent='Updated '+new Date(d.updatedAt).toLocaleString()}load();setInterval(load,60000)</script>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip('/').endswith('/api/summary'):
            body=json.dumps(payload()).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        body=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--serve',action='store_true'); p.add_argument('--host',default='127.0.0.1'); a=p.parse_args()
    if a.serve: ThreadingHTTPServer((a.host,3030),Handler).serve_forever()
    else: collect()
