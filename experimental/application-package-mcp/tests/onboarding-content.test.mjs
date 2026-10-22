// Manual intent: free-user-onboarding/tests.md T14,T15,T17,T19,T21.
import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile, mkdtemp, writeFile, mkdir, symlink, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { SETUP_PROMPT, onboardingBody } from '../dist/onboarding.js';

test('public first-run prompt and managed instructions preserve prerequisites and safeguards',async()=>{
  const prompts=await readFile('resources/sample-prompts.md','utf8');assert.ok(prompts.includes(SETUP_PROMPT));
  for(const name of ['resources/onboarding.md','resources/client-skill/SKILL.md',...['AGENTS','CLAUDE','COPILOT','GEMINI'].map(x=>`resources/workspace-template/${x}.md`)]){
    const source=await readFile(name,'utf8');
    for(const phrase of ['selected writable','symlink','check_capabilities.py','strict','manifest'])assert.ok(source.includes(phrase),`${name}: ${phrase}`);
  }
  const html=onboardingBody();assert.ok(html.includes('Streamable HTTP'));assert.ok(html.includes('OneDrive'));assert.ok(html.includes('own policy'));
});

test('capability checks distinguish native connection, missing PDF/DOCX, and retry',()=>{
  const code=`import importlib.util,unittest.mock as m\ns=importlib.util.spec_from_file_location('cap','resources/application-kit/scripts/check_capabilities.py'); c=importlib.util.module_from_spec(s);s.loader.exec_module(c)\nwith m.patch.object(c.shutil,'which',return_value=None):\n assert c.check('native-mcp')['status']=='available'\n assert c.check('bootstrap')['status']=='available'\n assert c.check('pdf-text')['missing']==['pdftotext']\n assert c.check('mcp-wrapper')['missing']==['node']\nwith m.patch.object(c.importlib.util,'find_spec',return_value=None):\n assert c.check('docx-ats')['status']=='blocked'\nwith m.patch.object(c.shutil,'which',return_value='/test/bin/tool'):\n assert c.check('pdf-text')['status']=='available'\n`;
  const r=spawnSync('python3',['-c',code],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
});

test('CV ingestion preserves originals on conflict and rejects output symlink escapes',async()=>{
  const root=await mkdtemp(path.join(tmpdir(),'jobmcp-source-'));const src=path.join(root,'input.html');await writeFile(src,'<h1>Synthetic Candidate</h1><p>Confirmed experience</p>');
  const args=['resources/application-kit/scripts/ingest_cv.py',src,'--root',root];
  let r=spawnSync('python3',args,{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  r=spawnSync('python3',args,{encoding:'utf8'});assert.equal(r.status,0,r.stderr);
  await writeFile(src,'<h1>A different original</h1>');r=spawnSync('python3',args,{encoding:'utf8'});assert.notEqual(r.status,0);assert.match(r.stderr,/already exists/);
  assert.match(await readFile(path.join(root,'candidate/source/cv-original.html'),'utf8'),/Synthetic Candidate/);
  const linked=await mkdtemp(path.join(tmpdir(),'jobmcp-symlink-'));await mkdir(path.join(linked,'candidate'));await symlink(root,path.join(linked,'candidate/source'));
  r=spawnSync('python3',['resources/application-kit/scripts/ingest_cv.py',src,'--root',linked],{encoding:'utf8'});assert.notEqual(r.status,0);assert.match(r.stderr,/outside the selected workspace/);
});

test('technical diagram sources encode connection and selected-text boundaries',async()=>{
  const boot=await readFile('resources/diagrams/bootstrap-scaffolding-flow.puml','utf8');
  for(const phrase of ['server/discover','initialize + tools/list','selected writable folder','Tools missing','configuration approval','/agent-setup.md'])assert.ok(boot.includes(phrase));
  for(const name of ['bootstrap-scaffolding-flow','private-checker-flow','local-first-human-flow']){
    const svg=await readFile(`resources/diagrams/${name}.svg`,'utf8');assert.ok(svg.includes('<svg'));assert.ok(!svg.includes('Syntax Error'));
  }
});

test('missing PDF converter leaves original and workspace untouched; text alternative still works',async()=>{
  const root=await mkdtemp(path.join(tmpdir(),'jobmcp-no-converter-'));
  const source=path.join(root,'source.pdf');await writeFile(source,'synthetic PDF placeholder; no external tool should run');
  const python=spawnSync('python3',['-c','import sys;print(sys.executable)'],{encoding:'utf8'}).stdout.trim();
  const r=spawnSync(python,['resources/application-kit/scripts/ingest_cv.py',source,'--root',root],{encoding:'utf8',env:{...process.env,PATH:root}});
  assert.notEqual(r.status,0);assert.match(r.stderr,/pdftotext/);
  assert.equal(await readFile(source,'utf8'),'synthetic PDF placeholder; no external tool should run');
  await assert.rejects(access(path.join(root,'candidate/source/cv-original.pdf')));
  const code=`import importlib.util,unittest.mock as m\ns=importlib.util.spec_from_file_location('ats','resources/application-kit/scripts/ats_text_extract.py'); a=importlib.util.module_from_spec(s);s.loader.exec_module(a)\nfrom pathlib import Path\nwith m.patch.object(a.shutil,'which',return_value=None):\n try:a.extract_pdf(Path('unused.pdf'))\n except SystemExit as e:assert 'blocked' in str(e) and 'unchanged' in str(e)\nassert a.extract_source(Path('${source.replaceAll('\\','\\\\')}'.replace('source.pdf','source.txt'))) == 'Confirmed synthetic facts'\n`;
  await writeFile(path.join(root,'source.txt'),'Confirmed synthetic facts');
  const text=spawnSync(python,['-c',code],{encoding:'utf8'});assert.equal(text.status,0,text.stderr);
});
