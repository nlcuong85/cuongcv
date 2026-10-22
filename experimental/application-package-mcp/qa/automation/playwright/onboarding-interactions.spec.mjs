// Manual source: kiro/specs/free-user-onboarding/tests.md T11,T12,T16.
import { test, expect } from '@playwright/test';

test('T12: every copy control copies only its own prompt/address',async({page,context})=>{
  await context.grantPermissions(['clipboard-read','clipboard-write']); await page.goto('/start');
  await page.locator('#connect-tools > summary').click();
  await page.locator('#returning-user > summary').click();
  for(const [label,id] of [['Copy MCP address','mcp-address'],['Copy setup prompt','setup-prompt'],['Copy application prompt','application-prompt'],['Copy ATS prompt','ats-prompt'],['Copy writing prompt','writing-prompt']]){
    const expected=await page.locator('#'+id).textContent(); await page.getByRole('button',{name:label,exact:true}).click();
    await expect.poll(()=>page.evaluate(()=>navigator.clipboard.readText())).toBe(expected.trim());
    await expect(page.getByRole('button',{name:label,exact:true})).toBeEnabled();
  }
});

for(const fallback of ['false','throw','success']){
  test(`T12: clipboard denied and legacy ${fallback}`,async({page})=>{
    await page.addInitScript((mode)=>{
      Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('denied');}}});
      document.execCommand=()=>{if(mode==='throw') throw new Error('denied');return mode==='success';};
    },fallback);
    await page.goto('/start'); const button=page.getByRole('button',{name:'Copy setup prompt',exact:true});
    await button.click();
    await expect(page.locator('#setup-prompt').locator('..').getByRole('status')).toContainText(fallback==='success'?'Copied.':'Could not copy.');
    await expect(button).toHaveText('Copy setup prompt');
    if(fallback!=='success') await expect(page.locator('#setup-prompt')).toBeFocused();
  });
}

test('T11: keyboard and focus, hidden details, mobile target sizes',async({page})=>{
  await page.setViewportSize({width:390,height:844}); await page.goto('/start');
  await expect(page.getByRole('button',{name:'Copy ATS prompt'})).toBeHidden();
  await page.locator('#returning-user > summary').focus(); await page.keyboard.press('Enter');
  await expect(page.getByRole('button',{name:'Copy ATS prompt'})).toBeVisible();
  for(const button of await page.getByRole('button').all()){
    if(await button.isVisible()){const b=await button.boundingBox();expect(b.width).toBeGreaterThanOrEqual(44);expect(b.height).toBeGreaterThanOrEqual(44);}
  }
  await page.getByRole('button',{name:'Copy setup prompt',exact:true}).focus();
  expect(await page.evaluate(()=>getComputedStyle(document.activeElement).outlineStyle)).not.toBe('none');
});
