# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: qoe-gates.spec.ts >> QoE quality gates (workshop demos) >> baseline: first frame within generous budget
- Location: e2e/qoe-gates.spec.ts:39:7

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: page.waitForFunction: Test timeout of 45000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - navigation [ref=e4]:
    - button "Go home" [ref=e5] [cursor=pointer]:
      - generic [ref=e6]: ▶
      - generic [ref=e7]: StreamApp
    - list [ref=e8]:
      - listitem [ref=e9]:
        - button "Home" [ref=e10] [cursor=pointer]
      - listitem [ref=e11]:
        - button "Pipeline" [ref=e12] [cursor=pointer]
      - listitem [ref=e13]:
        - button "Movies" [ref=e14] [cursor=pointer]
      - listitem [ref=e15]:
        - button "Shows" [ref=e16] [cursor=pointer]
      - listitem [ref=e17]:
        - button "Live" [ref=e18] [cursor=pointer]
    - generic [ref=e19]:
      - button "Search" [ref=e20] [cursor=pointer]:
        - img [ref=e21]
      - generic "Profile" [ref=e24]:
        - generic [ref=e25]: QE
  - generic [ref=e26]:
    - generic [ref=e27]:
      - button "Back" [ref=e28] [cursor=pointer]:
        - img [ref=e29]
        - text: Back
      - generic [ref=e31]:
        - generic [ref=e32]:
          - generic [ref=e33]: Sci-Fi
          - generic [ref=e34]: Adventure
          - generic [ref=e35]: Drama
        - heading "Cosmic Journey" [level=1] [ref=e36]
        - paragraph [ref=e37]: When mission commander Lena Vasquez discovers an anomalous signal at the edge of the solar system, she leads her crew into uncharted territory. What begins as a routine deep-space survey becomes humanity's most profound encounter with the unknown. A stunning visual odyssey that redefines the boundaries of science fiction.
        - generic [ref=e38]:
          - generic [ref=e39]: 97% Match
          - generic [ref=e40]: PG-13
          - generic [ref=e41]: "2024"
          - generic [ref=e42]: 2h 18m
        - generic [ref=e43]:
          - button "Play" [ref=e44] [cursor=pointer]:
            - img [ref=e45]
            - text: Play
          - button "Watchlist" [ref=e47] [cursor=pointer]:
            - img [ref=e48]
            - text: Watchlist
    - generic [ref=e50]:
      - heading "About Cosmic Journey" [level=3] [ref=e51]:
        - text: About
        - emphasis [ref=e52]: Cosmic Journey
      - generic [ref=e53]:
        - generic [ref=e54]:
          - term [ref=e55]: Genre
          - definition [ref=e56]: Sci-Fi, Adventure, Drama
        - generic [ref=e57]:
          - term [ref=e58]: Year
          - definition [ref=e59]: "2024"
        - generic [ref=e60]:
          - term [ref=e61]: Rating
          - definition [ref=e62]: PG-13
        - generic [ref=e63]:
          - term [ref=e64]: Duration
          - definition [ref=e65]: 2h 18m
    - button "Close player" [ref=e70] [cursor=pointer]:
      - img [ref=e71]
```

# Test source

```ts
  1   | import { test, expect } from './fixtures';
  2   | import { allure }        from 'allure-playwright';
  3   | 
  4   | // ── Shared helpers ────────────────────────────────────────────────────────────
  5   | 
  6   | async function snapshot(page: import('@playwright/test').Page) {
  7   |   return page.evaluate(() => window.__QOE_DEMO__?.getSnapshot() ?? null);
  8   | }
  9   | 
  10  | /** Wait until the QoE probe bridge has recorded a first frame.
  11  |  *  Uses page.waitForFunction() so intermediate retries are silent in Allure. */
  12  | async function waitForFirstFrame(page: import('@playwright/test').Page, timeout = 60_000) {
> 13  |   await page.waitForFunction(
      |              ^ Error: page.waitForFunction: Test timeout of 45000ms exceeded.
  14  |     () => (window as any).__QOE_DEMO__?.getSnapshot()?.timeToFirstFrameMs != null,
  15  |     { timeout },
  16  |   );
  17  | }
  18  | 
  19  | /**
  20  |  * Snapshot the request log and assert no critical network issues exist.
  21  |  * Called at the end of each test after the scenario has played out.
  22  |  */
  23  | async function assertNoNetworkIssues(
  24  |   entries: import('./fixtures').NetworkFixtures['networkCapture']['entries'],
  25  | ) {
  26  |   const failed = entries.filter(e => e.failed);
  27  |   const manifestErrors = failed.filter(e => e.category === 'hls-manifest');
  28  |   const apiErrors      = failed.filter(e => e.category === 'qoe-api');
  29  | 
  30  |   // Soft-assert so all issues are visible in one report
  31  |   expect.soft(manifestErrors, `HLS manifest errors: ${manifestErrors.map(e => e.url).join(', ')}`).toHaveLength(0);
  32  |   expect.soft(apiErrors.length, `QoE API failures: ${apiErrors.length}/${entries.filter(e=>e.category==='qoe-api').length}`).toBe(0);
  33  | }
  34  | 
  35  | // ── Test suite ────────────────────────────────────────────────────────────────
  36  | 
  37  | test.describe('QoE quality gates (workshop demos)', () => {
  38  | 
  39  |   test('baseline: first frame within generous budget', { tag: ['@BAT'] }, async ({ page, networkCapture }) => {
  40  |     await allure.feature('Time to First Frame');
  41  |     await allure.story('Baseline (reference stream)');
  42  |     await allure.severity('critical');
  43  |     await allure.description(`
  44  | **Scenario:** Baseline — no faults injected.
  45  | 
  46  | The player loads the HLS manifest immediately and begins buffering segments.
  47  | This test asserts that the first decoded video frame is delivered within a
  48  | generous 45-second budget (cloud CI networks can be slow).
  49  | 
  50  | **Pass condition:** \`timeToFirstFrameMs < 45 000\`
  51  |     `.trim());
  52  |     await allure.label('layer', 'e2e');
  53  |     await allure.label('testType', 'automated');
  54  |     await allure.tag('qoe', 'ttff', 'baseline');
  55  |     await allure.link('https://www.w3.org/TR/media-source/', 'MSE spec', 'reference');
  56  | 
  57  |     await page.goto('/?scenario=baseline&e2e_autoplay=1');
  58  | 
  59  |     await allure.step('Wait for first frame', () => waitForFirstFrame(page));
  60  | 
  61  |     const snap = await snapshot(page);
  62  |     const ttff = snap!.timeToFirstFrameMs!;
  63  | 
  64  |     await allure.step('Assert time-to-first-frame < 45 s', async () => {
  65  |       await allure.parameter('timeToFirstFrameMs',  String(ttff));
  66  |       await allure.parameter('threshold_ms',  String(45_000));
  67  |       expect(ttff).toBeLessThan(45_000);
  68  |     });
  69  | 
  70  |     await allure.step('Assert no critical network issues', async () => {
  71  |       await assertNoNetworkIssues(networkCapture.entries);
  72  |     });
  73  |   });
  74  | 
  75  |   // ──────────────────────────────────────────────────────────────────────────
  76  | 
  77  |   test('startup_delay: time-to-first-frame reflects injected delay', { tag: ['@Smoke'] }, async ({ page, networkCapture }) => {
  78  |     await allure.feature('Startup Latency');
  79  |     await allure.story('Startup delay (late manifest attach)');
  80  |     await allure.severity('normal');
  81  |     await allure.description(`
  82  | **Scenario:** Startup delay — HLS manifest attach is intentionally delayed by 2 800 ms.
  83  | 
  84  | Validates that the QoE probe correctly measures the injected startup penalty.
  85  | 47 % of viewers abandon a stream that takes > 3 s to start; early detection
  86  | in CI prevents regressions landing in production.
  87  | 
  88  | **Pass condition:** \`timeToFirstFrameMs > 2 000\`
  89  |     `.trim());
  90  |     await allure.label('layer', 'e2e');
  91  |     await allure.label('testType', 'automated');
  92  |     await allure.tag('qoe', 'ttff', 'startup-delay');
  93  | 
  94  |     await page.goto('/?scenario=startup_delay&e2e_autoplay=1');
  95  | 
  96  |     await allure.step('Wait for first frame (with injected delay)', () => waitForFirstFrame(page));
  97  | 
  98  |     const snap = await snapshot(page);
  99  |     const ttff = snap!.timeToFirstFrameMs!;
  100 | 
  101 |     await allure.step('Assert startup delay was measured (ttff > 2 000 ms)', async () => {
  102 |       await allure.parameter('timeToFirstFrameMs',  String(ttff));
  103 |       await allure.parameter('injected_delay_ms',  String(2_800));
  104 |       expect(ttff).toBeGreaterThan(2_000);
  105 |     });
  106 | 
  107 |     await allure.step('Assert no critical network issues', async () => {
  108 |       await assertNoNetworkIssues(networkCapture.entries);
  109 |     });
  110 |   });
  111 | 
  112 |   // ──────────────────────────────────────────────────────────────────────────
  113 | 
```