// T03/T04/T17/T18: SDK-to-local-kit integration. Not a desktop UI/account test.
import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const endpoint = process.env.MCP_URL || 'http://127.0.0.1:5943/mcp';
const root = await mkdtemp(path.join(tmpdir(),'jobmcp-clean-workspace-'));
const client = new Client({ name:'onboarding-workspace-fixture', version:'1.0' });
await client.connect(new StreamableHTTPClientTransport(new URL(endpoint)));
try {
  const tools = await client.listTools();
  if (!tools.tools.some(x=>x.name==='get_complete_bootstrap')) throw new Error('Complete bootstrap tool missing');
  const bootstrap=JSON.parse((await client.callTool({name:'get_complete_bootstrap',arguments:{}})).content[0].text);
  const baseUrl=new URL(endpoint); baseUrl.pathname='/';
  const install=spawnSync('python3',[path.resolve('resources/bootstrap_workspace.py'),'--root',root,'--base-url',baseUrl.href,'--expected-sha256',bootstrap.archive_sha256,'--approve-workspace'],{encoding:'utf8'});
  if(install.status!==0) throw new Error(`Complete bootstrap failed: ${install.stderr}\n${install.stdout}`);
  const run=(args)=>{
    const r=spawnSync('python3',args,{cwd:root,encoding:'utf8'});
    if(r.status!==0) throw new Error(`${args.join(' ')} failed: ${r.stderr}\n${r.stdout}`);
    return r.stdout;
  };
  run(['application-kit/scripts/check_capabilities.py','--operation','bootstrap','--root','.']);
  run(['scripts/migrate_legacy_workspace.py','.']);
  run(['application-kit/scripts/workspace_audit.py','--root','.']);
  run(['application-kit/scripts/application_sop.py','--root','.','boot','--strict']);
  const manifest=JSON.parse(await readFile(path.join(root,'.mcp/workspace-manifest.json'),'utf8'));
  const auditResult=await client.callTool({name:'audit_workspace_manifest',arguments:manifest});
  if(auditResult.isError) throw new Error(auditResult.content[0].text);
  const audit=JSON.parse(auditResult.content[0].text);
  if(audit.status!=='workspace_current') throw new Error(`Incomplete kit after bootstrap: ${JSON.stringify({missing:audit.missing_paths, mismatches:audit.managed_hash_mismatches})}`);
  // Fresh generic setup need not have candidate decisions answered yet.
  console.log(JSON.stringify({ok:true,endpoint,workspace:root,proof:'SDK connection, generic scaffold, local strict boot and safe manifest audit',auditStatus:audit.status,limitation:'Does not prove client UI registration, user account eligibility or physical phone access.'},null,2));
} finally { await client.close(); }
