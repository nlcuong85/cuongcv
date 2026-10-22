import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: '.', testMatch: '*.spec.mjs', workers: 1, timeout: 30000,
  outputDir: '../../../output/playwright/free-user-onboarding/artifacts',
  reporter: [['list'], ['html', { outputFolder: '../../../output/playwright/free-user-onboarding/report', open: 'never' }]],
  use: { channel: 'chromium', baseURL: process.env.BASE_URL || 'http://127.0.0.1:5943', trace: 'retain-on-failure', screenshot: 'only-on-failure', reducedMotion: 'reduce' },
});
