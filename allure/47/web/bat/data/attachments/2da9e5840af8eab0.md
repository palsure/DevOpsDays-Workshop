# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: player-controls.spec.ts >> Player Controls (pause / play / seek) >> pause stops playback and isPaused is true
- Location: e2e/player-controls.spec.ts:86:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4173/
Call log:
  - navigating to "http://127.0.0.1:4173/", waiting until "load"

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
  41  |   await page.waitForFunction(
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
  77  |     // Navigate to home page first — visible in video recording as full navigation flow
> 78  |     await page.goto('/');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4173/
  79  |     await page.waitForLoadState('domcontentloaded');
  80  |     await page.goto('/?scenario=baseline&e2e_autoplay=1');
  81  |     await waitForFirstFrame(page);
  82  |   });
  83  | 
  84  |   // ── Pause ──────────────────────────────────────────────────────────────────
  85  | 
  86  |   test('pause stops playback and isPaused is true', { tag: ['@BAT'] }, async ({ page }) => {
  87  |     await allure.feature('Player Controls');
  88  |     await allure.story('Pause');
  89  |     await allure.severity('critical');
  90  |     await allure.description(`
  91  | Verifies that calling pause() via the QoE bridge halts playback.
  92  | 
  93  | **Steps:**
  94  | 1. Autoplay baseline stream, wait for first frame.
  95  | 2. Call bridge.pause() — equivalent to video.pause().
  96  | 3. Assert isPaused = true and currentTime is frozen.
  97  | 
  98  | **Pass condition:** \`isPaused === true\`
  99  |     `.trim());
  100 | 
  101 |     await allure.step('Pause playback via bridge', () => bridge.pause(page));
  102 |     await page.waitForTimeout(300);
  103 | 
  104 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  105 | 
  106 |     await allure.step('Assert player reports isPaused = true', async () => {
  107 |       await allure.parameter('isPaused',     String(snap.isPaused));
  108 |       await allure.parameter('currentTime',  String(snap.currentTime));
  109 |       expect(snap.isPaused).toBe(true);
  110 |     });
  111 |   });
  112 | 
  113 |   // ── Resume ─────────────────────────────────────────────────────────────────
  114 | 
  115 |   test('resume after pause restarts playback', { tag: ['@Smoke'] }, async ({ page }) => {
  116 |     await allure.feature('Player Controls');
  117 |     await allure.story('Resume');
  118 |     await allure.severity('critical');
  119 |     await allure.description(`
  120 | Verifies that calling play() after pause() resumes advancement of currentTime.
  121 | 
  122 | **Pass condition:** currentTime advances > 0.5 s within 5 s of resume.
  123 |     `.trim());
  124 | 
  125 |     await allure.step('Pause playback', () => bridge.pause(page));
  126 |     await page.waitForTimeout(200);
  127 | 
  128 |     const snapBefore = await bridge.snapshot(page) as QoeDemoSnapshot;
  129 |     const frozenTime = snapBefore.currentTime;
  130 | 
  131 |     await allure.step('Resume playback via bridge', () => bridge.play(page));
  132 | 
  133 |     await allure.step('Assert currentTime advances after resume', async () => {
  134 |       await expect
  135 |         .poll(() => bridge.snapshot(page).then(s => s?.currentTime ?? 0), { timeout: 5_000 })
  136 |         .toBeGreaterThan(frozenTime + 0.3);
  137 | 
  138 |       const snapAfter = await bridge.snapshot(page) as QoeDemoSnapshot;
  139 |       await allure.parameter('isPaused',         String(snapAfter.isPaused));
  140 |       await allure.parameter('frozenTime_s',     String(frozenTime));
  141 |       await allure.parameter('resumedTime_s',    String(snapAfter.currentTime));
  142 |       expect(snapAfter.isPaused).toBe(false);
  143 |     });
  144 |   });
  145 | 
  146 |   // ── Seek forward ──────────────────────────────────────────────────────────
  147 | 
  148 |   test('seek forward: currentTime jumps to target position', { tag: ['@Smoke'] }, async ({ page }) => {
  149 |     await allure.feature('Player Controls');
  150 |     await allure.story('Seek Forward');
  151 |     await allure.severity('normal');
  152 |     await allure.description(`
  153 | Seeks the playhead forward to 20 s and verifies the video element reports
  154 | the new position within ±2 s.
  155 | 
  156 | **Pass condition:** \`currentTime ≥ 18 s\`
  157 |     `.trim());
  158 | 
  159 |     const TARGET = 20;
  160 | 
  161 |     await allure.step(`Seek to ${TARGET}s`, () => bridge.seek(page, TARGET));
  162 | 
  163 |     await allure.step('Wait for playhead to reach target', () =>
  164 |       waitForPlayhead(page, TARGET - 2));
  165 | 
  166 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  167 | 
  168 |     await allure.step('Assert currentTime is at target', async () => {
  169 |       await allure.parameter('seekTarget_s',   String(TARGET));
  170 |       await allure.parameter('currentTime_s',  String(snap.currentTime));
  171 |       expect(snap.currentTime).toBeGreaterThanOrEqual(TARGET - 2);
  172 |     });
  173 |   });
  174 | 
  175 |   // ── Seek backward ─────────────────────────────────────────────────────────
  176 | 
  177 |   test('seek backward: currentTime rewinds to earlier position', { tag: ['@Smoke'] }, async ({ page }) => {
  178 |     await allure.feature('Player Controls');
```