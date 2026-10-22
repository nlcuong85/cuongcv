import { test, expect } from '@playwright/test';

for (const viewport of [{ width: 390, height: 844 }, { width: 1366, height: 768 }]) {
  test(`docs cover current product updates and remain usable at ${viewport.width}px`, async ({ page }, testInfo) => {
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));
    await page.setViewportSize(viewport);
    await page.goto('/docs');

    await expect(page.getByRole('heading', { name: 'Job MCP by pmlecuong docs' })).toBeVisible();
    for (const heading of [
      'Latest product updates',
      'Start with your folder; the agent handles connection',
      'What you can do with Job MCP',
      'What the local application kit prepares',
      'Available MCP tools',
      'Review gates',
      'Local computer requirements',
      'Privacy contract',
      'Useful routes',
    ]) {
      await expect(page.getByRole('heading', { name: heading })).toBeVisible();
    }

    await expect(page.getByRole('main').getByText('2026.10.22-onboarding.2')).toBeVisible();
    const publicDocsCopy = await page.getByRole('main').innerText();
    expect(publicDocsCopy).not.toMatch(/optional Google sign-in|account\/dashboard path|Planned, not live|no account or Google login/i);
    expect(publicDocsCopy).not.toMatch(/homepage activity summary|one-minute bucket|salted visitor hashes|coarse country\/city headers|public usage\/analytics JSON route|counts are approximate and rounded/i);
    const diagramKeys = ['setup', 'privacy', 'package', 'ats', 'interview-prep'];
    for (const key of diagramKeys) {
      const diagram = page.getByTestId(`docs-diagram-${key}`);
      await expect(diagram).toBeVisible();
      await expect(diagram.locator('svg[role="img"]')).toHaveAttribute('aria-label', /.+/);
      const mobileSteps = diagram.locator('.docs-diagram-mobile-steps');
      if (viewport.width < 560) {
        await expect(mobileSteps).toBeVisible();
        await expect(mobileSteps.locator('li')).toHaveCount(3);
      } else {
        await expect(mobileSteps).toBeHidden();
      }
    }
    expect(await page.locator('[data-testid^="docs-diagram-"]').count()).toBe(5);
    await expect(page.getByText('check_ats_resume_fit', { exact: false })).toBeVisible();
    await expect(page.getByText('suggest_writing_revision', { exact: false })).toBeVisible();
    await page.getByRole('link', { name: 'Latest updates' }).click();
    await expect(page).toHaveURL(/#latest-updates$/);
    await page.getByRole('link', { name: 'Interview prep' }).click();
    await expect(page).toHaveURL(/#interview-prep$/);

    const dimensions = await page.evaluate(() => ({
      bodyWidth: document.body.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      pageHeight: document.body.scrollHeight,
      toolsVisible: document.querySelector('#tools').getBoundingClientRect().bottom <= document.body.scrollHeight,
      diagramsFit: [...document.querySelectorAll('[data-testid^="docs-diagram-"] svg')].every((svg) => svg.getBoundingClientRect().width <= document.documentElement.clientWidth),
    }));
    expect(dimensions.bodyWidth).toBeLessThanOrEqual(dimensions.viewportWidth);
    expect(dimensions.pageHeight).toBeGreaterThan(viewport.height);
    expect(dimensions.toolsVisible).toBe(true);
    expect(dimensions.diagramsFit).toBe(true);
    expect(pageErrors).toEqual([]);

    await page.goto('/docs');
    await page.screenshot({ path: testInfo.outputPath(`docs-${viewport.width}.png`), fullPage: true });
  });
}
