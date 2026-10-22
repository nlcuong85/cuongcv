// Manual intent: free-user-onboarding/tests.md T22, agent-led correction.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

test('agent helper plans without writes; approved project config preserves existing settings',()=>{
  const code=`import importlib.util,tempfile,tomllib\nfrom pathlib import Path\ns=importlib.util.spec_from_file_location('setup','resources/bootstrap/configure_codex_mcp.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nr=Path(tempfile.mkdtemp(prefix='jobmcp-agent-config-'))\nassert m.configure(r,False)['status']=='approval_required'\nassert not (r/'.codex').exists()\n(r/'.codex').mkdir();p=r/'.codex/config.toml';original='# user comment\\nmodel = "test-model"\\n[mcp_servers.existing]\\nurl = "https://example.test/mcp"\\n';p.write_text(original)\nassert m.configure(r,True)['status']=='configured_awaiting_client_reload'\nafter=p.read_text();assert after.startswith(original);d=tomllib.loads(after);assert d['model']=='test-model';assert d['mcp_servers']['existing']['url']=='https://example.test/mcp';assert d['mcp_servers']['jobmcp']['url']==m.ENDPOINT\nassert 'approval_policy' not in d and 'sandbox_mode' not in d\nassert len(list((r/'.codex').glob('config.toml.jobmcp-backup-*')))==1\nassert m.configure(r,True)['status']=='already_configured' and p.read_text()==after\n`;
  const r=spawnSync('python3',['-c',code],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
});

test('agent helper rejects conflicts, disabled entries, malformed config and symlink escapes',()=>{
  const code=`import importlib.util,tempfile\nfrom pathlib import Path\ns=importlib.util.spec_from_file_location('setup','resources/bootstrap/configure_codex_mcp.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nfor original in ['[mcp_servers.jobmcp]\\nurl="https://different.test/mcp"\\n','[mcp_servers.jobmcp]\\nurl="'+m.ENDPOINT+'"\\nenabled=false\\n','broken [ TOML']:\n r=Path(tempfile.mkdtemp(prefix='jobmcp-conflict-'));(r/'.codex').mkdir();p=r/'.codex/config.toml';p.write_text(original)\n try:m.configure(r,True);raise AssertionError('must reject')\n except ValueError:pass\n assert p.read_text()==original\nr=Path(tempfile.mkdtemp(prefix='jobmcp-link-'));outside=Path(tempfile.mkdtemp(prefix='jobmcp-outside-'));(r/'.codex').symlink_to(outside,target_is_directory=True)\ntry:m.configure(r,True);raise AssertionError('must reject link')\nexcept ValueError:pass\nassert not list(outside.iterdir())\n`;
  const r=spawnSync('python3',['-c',code],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
});
