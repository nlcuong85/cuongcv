import { expect, test } from '@playwright/test';

test('pink suitcase favicon is linked and served on site routes', async ({ page, request }) => {
  for (const route of ['/', '/docs']) {
    await page.goto(route);
    const icon = page.locator('link[rel="icon"]');
    await expect(icon).toHaveAttribute('type', 'image/svg+xml');
    await expect(icon).toHaveAttribute('href', '/favicon.svg');

    const response = await request.get(new URL('/favicon.svg', page.url()).toString());
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('image/svg+xml');
    const svg = await response.text();
    expect(svg).toContain('Job MCP pink suitcase');
    expect(svg).toContain('#ff79b5');
  }
});
