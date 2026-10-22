// Manual source: ../../../../../kiro/specs/free-user-onboarding/tests.md T01,T06-T10,T16.
import { test, expect } from '@playwright/test';

test('T01: guide, connection address and complete beginner path', async ({ page, request }) => {
  const health = await request.get('/health'); expect(health.headers()['content-type']).toContain('json');
  expect((await health.json()).service).toBe('student-application-ai-helper');
  await page.goto('/'); await page.getByRole('link', { name: 'Start setup', exact: true }).first().click();
  await expect(page).toHaveURL(/\/start/);
  await expect(page.getByTestId('onboarding-steps').getByRole('link')).toHaveText(['Open one private folder','Paste the setup prompt','Connect, check and prepare']);
  await expect(page.getByRole('figure',{name:/From an empty folder/})).toBeVisible();
  await expect(page.locator('#connect-tools')).not.toHaveAttribute('open','');
  await page.getByRole('link', { name: 'Get the setup prompt' }).click();
  await expect(page.locator('#setup-prompt')).toBeInViewport();
  await expect(page.locator('#setup-prompt')).toContainText('handle connection and workspace setup for me');
  await page.getByRole('link', { name: 'Open one private folder', exact: true }).click();
  await expect(page.getByRole('heading', { name: '1. Open one private folder' })).toBeInViewport();
});

test('T06-T09,T16: alternatives, history, retained details and privacy', async ({ page }) => {
  await page.goto('/start');
  for (const [name,id] of [['ChatGPT in a browser','chatgpt-browser'],['I’m on my phone','phone-remote'],['Another AI app','other-client']]) {
    await page.getByRole('link',{name,exact:true}).click();
    await expect(page.locator('#'+id)).toHaveAttribute('open','');
    await page.reload(); await expect(page.locator('#'+id)).toHaveAttribute('open','');
  }
  await page.goBack();
  await page.locator('#materials > summary').click();
  await expect(page.getByText(/10 authentic achievement/)).toBeVisible();
  await page.locator('#dependencies > summary').click();
  await expect(page.getByText(/remains blocked or unverified/)).toBeVisible();
  await page.locator('#returning-user > summary').click();
  for(const name of ['Copy application prompt','Copy ATS prompt','Copy writing prompt']) await expect(page.getByRole('button',{name,exact:true})).toBeVisible();
  await page.getByRole('link',{name:'Read the full privacy boundary'}).click();
  await expect(page).toHaveURL(/\/privacy/);
});

for(const [width,height] of [[390,844],[430,932],[1366,768],[1920,1080]]) {
  test(`T10: readable ${width}x${height} entry and expanded help`, async ({ page }, info) => {
    await page.setViewportSize({width,height}); await page.goto('/start');
    const action=page.getByRole('link',{name:'Get the setup prompt'});
    const box=await action.boundingBox(); expect(box.y+box.height).toBeLessThanOrEqual(height);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({path:info.outputPath(`start-${width}.png`),fullPage:false});
    await page.locator('#dependencies > summary').click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    if(width===390) await page.screenshot({path:info.outputPath('start-full-mobile.png'),fullPage:true});
  });
}

test('T16: no JavaScript, direct disclosures and safe text remain usable', async ({ browser }) => {
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const page=await context.newPage(); await page.goto((process.env.BASE_URL||'http://127.0.0.1:5943')+'/start#phone-remote');
  await page.locator('#phone-remote > summary').click();
  await expect(page.getByText(/phone browser cannot create a folder/)).toBeVisible();
  await expect(page.locator('#mcp-address')).toHaveText('https://jobmcp.pmlecuong.com/mcp');
  await expect(page.locator('#setup-prompt')).toContainText('preserve existing files');
  await context.close();
});

test('T10,T16,T20: doubled text/layout zoom, no page errors or private telemetry',async({page})=>{
  const errors=[];const posts=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST')posts.push(r.url());});
  await page.setViewportSize({width:1366,height:768});await page.goto('/start');
  await page.evaluate(()=>{document.body.style.zoom='2';});
  await page.locator('#returning-user > summary').click();
  const action=page.getByRole('button',{name:'Copy setup prompt',exact:true});await expect(action).toBeVisible();
  expect(await action.evaluate(e=>e.getBoundingClientRect().right <= innerWidth)).toBe(true);
  await page.getByRole('link',{name:'See the technical diagrams and data boundaries'}).click();
  await expect(page).toHaveURL(/\/technical-flow/);expect(errors).toEqual([]);expect(posts).toEqual([]);
});
