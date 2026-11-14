// T03/T04/T17/T18: SDK-to-local-kit integration. Not a desktop UI/account test.
import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';
import { mkdtemp, readFile, writeFile } from 'node:fs/promises';
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
  const installerResponse=await fetch(new URL('/bootstrap-workspace.py',baseUrl));
  if(!installerResponse.ok) throw new Error(`Public installer download failed: ${installerResponse.status}`);
  const installer=path.join(root,'bootstrap-workspace.py');
  await writeFile(installer,await installerResponse.text());
  const install=spawnSync('python3',[installer,'--root',root,'--base-url',baseUrl.href,'--expected-sha256',bootstrap.archive_sha256,'--approve-workspace'],{encoding:'utf8'});
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
  const agentsPath=path.join(root,'AGENTS.md');
  await writeFile(agentsPath,`${await readFile(agentsPath,'utf8')}\n## Candidate-owned note\nPlease keep my draft files local.\n`);
  const reinstall=spawnSync('python3',[installer,'--root',root,'--base-url',baseUrl.href,'--expected-sha256',bootstrap.archive_sha256,'--approve-workspace'],{encoding:'utf8'});
  if(reinstall.status!==0) throw new Error(`Safe kit reinstall failed: ${reinstall.stderr}\n${reinstall.stdout}`);
  if(!(await readFile(agentsPath,'utf8')).includes('Candidate-owned note')) throw new Error('Safe kit reinstall removed candidate-owned agent guidance');
  run(['application-kit/scripts/workspace_audit.py','--root','.']);
  const customizedManifest=JSON.parse(await readFile(path.join(root,'.mcp/workspace-manifest.json'),'utf8'));
  const customizedAudit=JSON.parse((await client.callTool({name:'audit_workspace_manifest',arguments:customizedManifest})).content[0].text);
  if(customizedAudit.status!=='workspace_current') throw new Error(`Candidate-owned agent note caused false managed drift: ${JSON.stringify(customizedAudit.managed_hash_mismatches)}`);
  await writeFile(agentsPath,(await readFile(agentsPath,'utf8')).replace('<!-- JOB-MCP-MANDATORY-POLICY:START -->','<!-- JOB-MCP-MANDATORY-POLICY:STALE -->'));
  run(['application-kit/scripts/workspace_audit.py','--root','.']);
  const tamperedManifest=JSON.parse(await readFile(path.join(root,'.mcp/workspace-manifest.json'),'utf8'));
  const tamperedAudit=JSON.parse((await client.callTool({name:'audit_workspace_manifest',arguments:tamperedManifest})).content[0].text);
  if(tamperedAudit.status!=='action_required'||!tamperedAudit.managed_hash_mismatches.includes('AGENTS.md')) throw new Error('Changed mandatory agent policy was not rejected');
  // Fresh generic setup need not have candidate decisions answered yet.
  console.log(JSON.stringify({ok:true,endpoint,workspace:root,proof:'SDK connection, generic scaffold, local strict boot and safe manifest audit',auditStatus:audit.status,candidateAgentNotePreserved:true,tamperedPolicyRejected:true,limitation:'Does not prove client UI registration, user account eligibility or physical phone access.'},null,2));
} finally { await client.close(); }
