import { test, expect } from '@playwright/test';

for (const viewport of [{ width: 390, height: 844 }, { width: 1366, height: 768 }]) {
  test(`homepage activity is readable above the fold at ${viewport.width}px`, async ({ page }) => {
    const unexpectedAnalyticsRequests = [];
    page.on('request', (request) => {
      if (/\/api\/(?:public-usage|analytics)|usage\.json/.test(request.url())) {
        unexpectedAnalyticsRequests.push(request.url());
      }
    });
    await page.setViewportSize(viewport);
    await page.goto('/');

    const activity = page.getByTestId('public-activity');
    const heading = page.getByRole('heading', { name: 'Real evidence. Stronger applications.' });
    await expect(activity).toBeVisible();
    await expect(activity.getByText('Job MCP activity')).toBeVisible();
    await expect(heading).toBeVisible();

    const unavailable = await activity.getByText('Numbers are temporarily unavailable.').count();
    expect(unavailable).toBeLessThanOrEqual(1);
    if (!unavailable) {
      await expect(activity.getByText('LAST 30 DAYS')).toBeVisible();
      const lastCall = activity.getByRole('status', { name: /Last MCP call:/ });
      await expect(lastCall).toBeVisible();
      await expect(lastCall).toContainText(/Last MCP call · (?:No calls recorded|just now|\d+ min ago|\d+ hr ago|\d+ days ago)/);
      await expect(lastCall).toHaveClass(/has-recorded-call/);
      const lastCallText = await lastCall.innerText();
      if (/just now|(?:[0-9]|1[0-4]) min ago/.test(lastCallText)) await expect(lastCall).toHaveClass(/is-recent/);
      if (/No calls recorded|(?:1[6-9]|[2-9][0-9]) min ago|\d+ hr ago|\d+ days ago/.test(lastCallText)) {
        await expect(lastCall).not.toHaveClass(/is-recent/);
      }
      await expect(activity.getByText(/Heilbronn/)).toBeVisible();
      await expect(activity.getByRole('img', { name: 'Approximate visits by city' })).toBeVisible();
    }

    const activityBox = await activity.boundingBox();
    const headingBox = await heading.boundingBox();
    const visualContract = await activity.evaluate((element) => ({
      background: getComputedStyle(element).backgroundColor,
      valueSize: Number.parseFloat(getComputedStyle(element.querySelector('.activity-number strong') ?? element.querySelector('strong')).fontSize),
      legendSize: element.querySelector('.activity-legend li') ? Number.parseFloat(getComputedStyle(element.querySelector('.activity-legend li')).fontSize) : 0,
      pieWidth: element.querySelector('.activity-pie') ? Number.parseFloat(getComputedStyle(element.querySelector('.activity-pie')).width) : 0,
      legendColor: element.querySelector('.activity-legend li') ? getComputedStyle(element.querySelector('.activity-legend li')).color : '',
      pulse: element.querySelector('.activity-last-call i') ? getComputedStyle(element.querySelector('.activity-last-call i')).animationName : 'none',
      markerWidth: element.querySelector('.activity-last-call i') ? Number.parseFloat(getComputedStyle(element.querySelector('.activity-last-call i')).width) : 0,
      markerHeight: element.querySelector('.activity-last-call i') ? Number.parseFloat(getComputedStyle(element.querySelector('.activity-last-call i')).height) : 0,
      markerColor: element.querySelector('.activity-last-call i') ? getComputedStyle(element.querySelector('.activity-last-call i')).backgroundColor : '',
      statusSize: element.querySelector('.activity-last-call') ? Number.parseFloat(getComputedStyle(element.querySelector('.activity-last-call')).fontSize) : 0,
      recent: element.querySelector('.activity-last-call')?.classList.contains('is-recent') ?? false,
    }));
    const bodyWidth = await page.locator('body').evaluate((element) => element.scrollWidth);
    expect(activityBox.y + activityBox.height).toBeLessThanOrEqual(viewport.height);
    expect(headingBox.y + headingBox.height).toBeLessThanOrEqual(viewport.height);
    expect(bodyWidth).toBeLessThanOrEqual(viewport.width);
    expect(visualContract.background).toBe('rgb(9, 22, 77)');
    if (!unavailable) {
      expect(visualContract.valueSize).toBeGreaterThanOrEqual(viewport.width < 560 ? 38 : 42);
      expect(visualContract.legendSize).toBeGreaterThanOrEqual(12);
      expect(visualContract.pieWidth).toBeGreaterThanOrEqual(viewport.width < 560 ? 70 : 88);
      expect(visualContract.legendColor).toBe('rgb(226, 232, 255)');
      expect(visualContract.markerWidth).toBeGreaterThanOrEqual(14);
      expect(visualContract.markerHeight).toBeGreaterThanOrEqual(14);
      expect(visualContract.statusSize).toBeGreaterThanOrEqual(viewport.width < 560 ? 11 : 13);
      expect(visualContract.markerColor).toBe('rgb(83, 226, 140)');
      expect(visualContract.pulse).toBe('none');
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      const lastCall = activity.getByRole('status', { name: /Last MCP call:/ });
      const livePulse = await lastCall.locator('i').evaluate((element) => getComputedStyle(element).animationName);
      expect(livePulse).toBe('activity-last-call-breathe');
      await page.emulateMedia({ reducedMotion: 'reduce' });
      const reducedPulse = await lastCall.locator('i').evaluate((element) => getComputedStyle(element).animationName);
      expect(reducedPulse).toBe('none');
    }
    expect(unexpectedAnalyticsRequests).toEqual([]);
  });
}
