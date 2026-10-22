// T03/T04/T17/T18: SDK-to-local-kit integration. Not a desktop UI/account test.
import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';
import { mkdtemp, mkdir, writeFile, access, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const endpoint = process.env.MCP_URL || 'http://127.0.0.1:5943/mcp';
const root = await mkdtemp(path.join(tmpdir(),'jobmcp-clean-workspace-'));
const client = new Client({ name:'onboarding-workspace-fixture', version:'1.0' });
await client.connect(new StreamableHTTPClientTransport(new URL(endpoint)));
try {
  const tools = await client.listTools();
  if (!tools.tools.some(x=>x.name==='get_workspace_template')) throw new Error('Expected tools missing');
  for(const [tool,prefix] of [['get_workspace_template',''],['get_application_kit_bundle','application-kit']]){
    const result=JSON.parse((await client.callTool({name:tool,arguments:{}})).content[0].text);
    for(const file of result.files){
      const target=path.resolve(root,prefix,file.path);
      if(!target.startsWith(root+path.sep)||path.isAbsolute(file.path)||file.path.includes('..')||file.path.includes('\\')) throw new Error('Unsafe kit path');
      await mkdir(path.dirname(target),{recursive:true});
      try{await access(target);}catch{await writeFile(target,file.content,{flag:'wx'});}
    }
  }
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
  // Fresh generic setup need not have candidate decisions answered yet.
  console.log(JSON.stringify({ok:true,endpoint,workspace:root,proof:'SDK connection, generic scaffold, local strict boot and safe manifest audit',auditStatus:audit.status,limitation:'Does not prove client UI registration, user account eligibility or physical phone access.'},null,2));
} finally { await client.close(); }
