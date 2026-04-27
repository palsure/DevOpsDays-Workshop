# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: player-controls.spec.ts >> ABR & Bitrate (HLS.js level management) >> multiple quality levels are available after manifest parse
- Location: e2e/player-controls.spec.ts:239:7

# Error details

```
Test timeout of 45000ms exceeded while running "beforeEach" hook.
```

```
Error: page.waitForFunction: Test timeout of 45000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - heading "Welcome to nginx!" [level=1] [ref=e2]
  - paragraph [ref=e3]: If you see this page, nginx is successfully installed and working. Further configuration is required for the web server, reverse proxy, API gateway, load balancer, content cache, or other features.
  - paragraph [ref=e4]:
    - text: For online documentation and support please refer to
    - link "nginx.org" [ref=e5] [cursor=pointer]:
      - /url: https://nginx.org/
    - text: .
    - text: To engage with the community please visit
    - link "community.nginx.org" [ref=e6] [cursor=pointer]:
      - /url: https://community.nginx.org/
    - text: .
    - text: For enterprise grade support, professional services, additional security features and capabilities please refer to
    - link "f5.com/nginx" [ref=e7] [cursor=pointer]:
      - /url: https://f5.com/nginx
    - text: .
  - paragraph [ref=e8]:
    - emphasis [ref=e9]: Thank you for using nginx.
```

# Test source

```ts
  1   | /**
  2   |  * player-controls.spec.ts
  3   |  *
  4   |  * Tests for:
  5   |  *   1. Player Controls   — pause, resume, seek forward/backward via the QoE
  6   |  *                          demo bridge (window.__QOE_DEMO__)
  7   |  *   2. ABR & Bitrate     — quality level enumeration, bandwidth estimation,
  8   |  *                          forced level override, and the built-in
  9   |  *                          bitrate_step_down fault scenario
  10  |  *
  11  |  * All commands are issued through the QoE bridge so the tests remain
  12  |  * framework-agnostic (no CSS selector hacks; just the JS player API).
  13  |  */
  14  | 
  15  | import { test, expect } from './fixtures';
  16  | import { allure }       from 'allure-playwright';
  17  | import type { QoeDemoSnapshot } from '../src/demo/qoeDemoBridge';
  18  | 
  19  | // ── Bridge helpers ─────────────────────────────────────────────────────────────
  20  | 
  21  | const bridge = {
  22  |   snapshot: (page: import('@playwright/test').Page) =>
  23  |     page.evaluate(() => window.__QOE_DEMO__?.getSnapshot() ?? null),
  24  | 
  25  |   play: (page: import('@playwright/test').Page) =>
  26  |     page.evaluate(() => window.__QOE_DEMO__?.play()),
  27  | 
  28  |   pause: (page: import('@playwright/test').Page) =>
  29  |     page.evaluate(() => window.__QOE_DEMO__?.pause()),
  30  | 
  31  |   seek: (page: import('@playwright/test').Page, seconds: number) =>
  32  |     page.evaluate((s) => window.__QOE_DEMO__?.seek(s), seconds),
  33  | 
  34  |   setLevel: (page: import('@playwright/test').Page, level: number) =>
  35  |     page.evaluate((l) => window.__QOE_DEMO__?.setLevel(l), level),
  36  | };
  37  | 
  38  | /** Wait until the bridge is registered and the manifest is parsed.
  39  |  *  Uses page.waitForFunction() so intermediate retries are silent in Allure. */
  40  | async function waitForManifest(page: import('@playwright/test').Page, timeout = 30_000) {
> 41  |   await page.waitForFunction(
      |              ^ Error: page.waitForFunction: Test timeout of 45000ms exceeded.
  42  |     () => ((window as any).__QOE_DEMO__?.getSnapshot()?.hlsLevels?.length ?? 0) > 0,
  43  |     { timeout },
  44  |   );
  45  | }
  46  | 
  47  | /** Wait until the QoE collector records the first decoded frame.
  48  |  *  Uses page.waitForFunction() so intermediate retries are silent in Allure. */
  49  | async function waitForFirstFrame(page: import('@playwright/test').Page, timeout = 60_000) {
  50  |   await page.waitForFunction(
  51  |     () => (window as any).__QOE_DEMO__?.getSnapshot()?.timeToFirstFrameMs != null,
  52  |     { timeout },
  53  |   );
  54  | }
  55  | 
  56  | /** Wait until the video's currentTime passes the given threshold.
  57  |  *  Uses page.waitForFunction() so intermediate retries are silent in Allure. */
  58  | async function waitForPlayhead(
  59  |   page: import('@playwright/test').Page,
  60  |   minSeconds: number,
  61  |   timeout = 30_000,
  62  | ) {
  63  |   await page.waitForFunction(
  64  |     (min: number) => ((window as any).__QOE_DEMO__?.getSnapshot()?.currentTime ?? 0) >= min,
  65  |     minSeconds,
  66  |     { timeout },
  67  |   );
  68  | }
  69  | 
  70  | // ─────────────────────────────────────────────────────────────────────────────
  71  | // Suite 1 — Player Controls
  72  | // ─────────────────────────────────────────────────────────────────────────────
  73  | 
  74  | test.describe('Player Controls (pause / play / seek)', () => {
  75  | 
  76  |   test.beforeEach(async ({ page }) => {
  77  |     await page.goto('/?scenario=baseline&e2e_autoplay=1');
  78  |     await waitForFirstFrame(page);
  79  |   });
  80  | 
  81  |   // ── Pause ──────────────────────────────────────────────────────────────────
  82  | 
  83  |   test('pause stops playback and isPaused is true', { tag: ['@BAT'] }, async ({ page }) => {
  84  |     await allure.feature('Player Controls');
  85  |     await allure.story('Pause');
  86  |     await allure.severity('critical');
  87  |     await allure.description(`
  88  | Verifies that calling pause() via the QoE bridge halts playback.
  89  | 
  90  | **Steps:**
  91  | 1. Autoplay baseline stream, wait for first frame.
  92  | 2. Call bridge.pause() — equivalent to video.pause().
  93  | 3. Assert isPaused = true and currentTime is frozen.
  94  | 
  95  | **Pass condition:** \`isPaused === true\`
  96  |     `.trim());
  97  | 
  98  |     await allure.step('Pause playback via bridge', () => bridge.pause(page));
  99  |     await page.waitForTimeout(300);
  100 | 
  101 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  102 | 
  103 |     await allure.step('Assert player reports isPaused = true', async () => {
  104 |       await allure.parameter('isPaused',     String(snap.isPaused));
  105 |       await allure.parameter('currentTime',  String(snap.currentTime));
  106 |       expect(snap.isPaused).toBe(true);
  107 |     });
  108 |   });
  109 | 
  110 |   // ── Resume ─────────────────────────────────────────────────────────────────
  111 | 
  112 |   test('resume after pause restarts playback', { tag: ['@Smoke'] }, async ({ page }) => {
  113 |     await allure.feature('Player Controls');
  114 |     await allure.story('Resume');
  115 |     await allure.severity('critical');
  116 |     await allure.description(`
  117 | Verifies that calling play() after pause() resumes advancement of currentTime.
  118 | 
  119 | **Pass condition:** currentTime advances > 0.5 s within 5 s of resume.
  120 |     `.trim());
  121 | 
  122 |     await allure.step('Pause playback', () => bridge.pause(page));
  123 |     await page.waitForTimeout(200);
  124 | 
  125 |     const snapBefore = await bridge.snapshot(page) as QoeDemoSnapshot;
  126 |     const frozenTime = snapBefore.currentTime;
  127 | 
  128 |     await allure.step('Resume playback via bridge', () => bridge.play(page));
  129 | 
  130 |     await allure.step('Assert currentTime advances after resume', async () => {
  131 |       await expect
  132 |         .poll(() => bridge.snapshot(page).then(s => s?.currentTime ?? 0), { timeout: 5_000 })
  133 |         .toBeGreaterThan(frozenTime + 0.3);
  134 | 
  135 |       const snapAfter = await bridge.snapshot(page) as QoeDemoSnapshot;
  136 |       await allure.parameter('isPaused',         String(snapAfter.isPaused));
  137 |       await allure.parameter('frozenTime_s',     String(frozenTime));
  138 |       await allure.parameter('resumedTime_s',    String(snapAfter.currentTime));
  139 |       expect(snapAfter.isPaused).toBe(false);
  140 |     });
  141 |   });
```