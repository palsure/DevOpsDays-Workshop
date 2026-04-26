import { defineConfig, devices } from '@playwright/test';

const BASE_URL          = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:4173';
const USE_EXTERNAL_SERVER = !!process.env.PLAYWRIGHT_BASE_URL;

export default defineConfig({
  testDir: 'e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: [
    // Always: human-readable terminal output
    ['list'],
    // Always: Playwright HTML report (open with `npm run report`)
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    // Always: Allure raw results (process with `npm run allure:generate`)
    ['allure-playwright', {
      detail: true,
      outputFolder: 'allure-results',
      suiteTitle: true,
      environmentInfo: {
        Framework:  'Playwright',
        Language:   'TypeScript',
        App:        'QoE Web Player',
        BaseURL:    BASE_URL,
      },
    }],
    // CI only: JSON (for the parse-playwright-results.js quality gate)
    ...(process.env.CI ? [['json', { outputFile: 'playwright-results.json' }] as const] : []),
    // CI only: GitHub annotations in the Actions log
    ...(process.env.CI ? [['github'] as const] : []),
  ],

  use: {
    ...devices['Desktop Chrome'],
    // Always record — allure-playwright picks these up automatically in onTestEnd
    video:      'on',
    screenshot: 'on',
    // Trace only on retry (traces are large; video + screenshot cover the normal case)
    trace:      'on-first-retry',
    baseURL:    BASE_URL,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      // Throttle tests run sequentially (1 worker) to avoid bandwidth contention.
      // Activate with: PLAYWRIGHT_PROJECT=throttle npx playwright test
      name:  'chromium-throttle',
      use:   { ...devices['Desktop Chrome'] },
      testMatch: '**/network-throttle.spec.ts',
      fullyParallel: false,
    },
  ],

  ...(USE_EXTERNAL_SERVER
    ? {}
    : {
        webServer: {
          command:             'npm run preview -- --host 127.0.0.1 --port 4173',
          url:                 'http://127.0.0.1:4173',
          reuseExistingServer: !process.env.CI,
          timeout:             120_000,
        },
      }),
});
