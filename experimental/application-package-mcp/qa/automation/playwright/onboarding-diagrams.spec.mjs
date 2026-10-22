// Manual source: kiro/specs/free-user-onboarding/tests.md T21,T16.
import {test,expect} from '@playwright/test';
test('T21: public diagrams decode, sources and render carry corrected boundary',async({page,request},info)=>{
  for(const name of ['bootstrap-scaffolding-flow','private-checker-flow','local-first-human-flow']){
    const source=await request.get(`/assets/${name}.puml`);expect(source.ok()).toBe(true);expect(await source.text()).toContain('@startuml');
    const svg=await request.get(`/assets/${name}.svg`);expect(svg.headers()['content-type']).toContain('svg');expect(await svg.text()).toContain('<svg');
  }
  await page.goto('/technical-flow');
  for(const img of await page.locator('.tech-card img').all()){expect(await img.evaluate(e=>e.complete&&e.naturalWidth>0)).toBe(true);}
  await page.screenshot({path:info.outputPath('technical-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.reload();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const region=page.getByRole('region',{name:'Bootstrap diagram, horizontally scrollable'});
  await expect(region).toBeVisible();
  expect(await region.evaluate(e=>e.getBoundingClientRect().right<=innerWidth)).toBe(true);
  await region.evaluate(e=>{e.scrollLeft=e.scrollWidth;});expect(await region.evaluate(e=>e.scrollLeft)).toBeGreaterThan(0);
  await expect(page.getByRole('link',{name:'Open bootstrap diagram full size ↗'})).toHaveAttribute('target','_blank');
  await page.screenshot({path:info.outputPath('technical-mobile.png'),fullPage:true});
  await page.goto('/start');
  const map=page.getByRole('figure',{name:/From an empty folder/});
  await expect(map.getByRole('link')).toHaveCount(3);
  await map.screenshot({path:info.outputPath('agent-map-mobile.png')});
  await page.setViewportSize({width:1366,height:900});
  await map.screenshot({path:info.outputPath('agent-map-desktop.png')});
});
