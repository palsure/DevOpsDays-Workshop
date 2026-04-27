# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: qoe-gates.spec.ts >> QoE quality gates (workshop demos) >> startup_delay: time-to-first-frame reflects injected delay
- Location: e2e/qoe-gates.spec.ts:92:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/?scenario=startup_delay&e2e_autoplay=1
Call log:
  - navigating to "http://localhost:3000/?scenario=startup_delay&e2e_autoplay=1", waiting until "load"

```

# Test source

```ts
  9   | 
  10  | /** Wait until the QoE probe bridge has recorded a first frame.
  11  |  *  Uses page.waitForFunction() so intermediate retries are silent in Allure. */
  12  | async function waitForFirstFrame(page: import('@playwright/test').Page, timeout = 60_000) {
  13  |   await page.waitForFunction(
  14  |     () => (window as any).__QOE_DEMO__?.getSnapshot()?.timeToFirstFrameMs != null,
  15  |     { timeout },
  16  |   );
  17  | }
  18  | 
  19  | /**
  20  |  * Snapshot the request log and assert no critical network issues exist.
  21  |  * Called at the end of each test after the scenario has played out.
  22  |  *
  23  |  * HLS manifest failures are hard-blocked — they directly prevent video playback.
  24  |  * QoE API failures are recorded as Allure parameters but do NOT fail the test:
  25  |  * these E2E tests run against a static file server (no backend), so 404s on
  26  |  * /api/v1/metrics are expected and do not affect visual playback behaviour.
  27  |  */
  28  | async function assertNoNetworkIssues(
  29  |   entries: import('./fixtures').NetworkFixtures['networkCapture']['entries'],
  30  | ) {
  31  |   const failed         = entries.filter(e => e.failed);
  32  |   const manifestErrors = failed.filter(e => e.category === 'hls-manifest');
  33  |   const apiErrors      = failed.filter(e => e.category === 'qoe-api');
  34  |   const apiTotal       = entries.filter(e => e.category === 'qoe-api').length;
  35  | 
  36  |   // HLS manifest errors block playback — always assert
  37  |   expect.soft(manifestErrors, `HLS manifest errors: ${manifestErrors.map(e => e.url).join(', ')}`).toHaveLength(0);
  38  | 
  39  |   // QoE API availability is tested by the API pipeline; record here for visibility only
  40  |   if (apiTotal > 0) {
  41  |     await allure.parameter(
  42  |       'qoe_api_failures',
  43  |       `${apiErrors.length}/${apiTotal} (backend not co-deployed — informational only)`,
  44  |     );
  45  |   }
  46  | }
  47  | 
  48  | // ── Test suite ────────────────────────────────────────────────────────────────
  49  | 
  50  | test.describe('QoE quality gates (workshop demos)', () => {
  51  | 
  52  |   test('baseline: first frame within generous budget', { tag: ['@BAT'] }, async ({ page, networkCapture }) => {
  53  |     await allure.feature('Time to First Frame');
  54  |     await allure.story('Baseline (reference stream)');
  55  |     await allure.severity('critical');
  56  |     await allure.description(`
  57  | **Scenario:** Baseline — no faults injected.
  58  | 
  59  | The player loads the HLS manifest immediately and begins buffering segments.
  60  | This test asserts that the first decoded video frame is delivered within a
  61  | generous 60-second budget (cloud CI networks serving external HLS streams
  62  | can be slow; the budget is intentionally wide to distinguish real regressions
  63  | from transient network latency).
  64  | 
  65  | **Pass condition:** \`timeToFirstFrameMs < 60 000\`
  66  |     `.trim());
  67  |     await allure.label('layer', 'e2e');
  68  |     await allure.label('testType', 'automated');
  69  |     await allure.tag('qoe', 'ttff', 'baseline');
  70  |     await allure.link('https://www.w3.org/TR/media-source/', 'MSE spec', 'reference');
  71  | 
  72  |     await page.goto('/?scenario=baseline&e2e_autoplay=1');
  73  | 
  74  |     await allure.step('Wait for first frame', () => waitForFirstFrame(page));
  75  | 
  76  |     const snap = await snapshot(page);
  77  |     const ttff = snap!.timeToFirstFrameMs!;
  78  | 
  79  |     await allure.step('Assert time-to-first-frame < 60 s', async () => {
  80  |       await allure.parameter('timeToFirstFrameMs',  String(ttff));
  81  |       await allure.parameter('threshold_ms',  String(60_000));
  82  |       expect(ttff).toBeLessThan(60_000);
  83  |     });
  84  | 
  85  |     await allure.step('Assert no critical network issues', async () => {
  86  |       await assertNoNetworkIssues(networkCapture.entries);
  87  |     });
  88  |   });
  89  | 
  90  |   // ──────────────────────────────────────────────────────────────────────────
  91  | 
  92  |   test('startup_delay: time-to-first-frame reflects injected delay', { tag: ['@Smoke'] }, async ({ page, networkCapture }) => {
  93  |     await allure.feature('Startup Latency');
  94  |     await allure.story('Startup delay (late manifest attach)');
  95  |     await allure.severity('normal');
  96  |     await allure.description(`
  97  | **Scenario:** Startup delay — HLS manifest attach is intentionally delayed by 2 800 ms.
  98  | 
  99  | Validates that the QoE probe correctly measures the injected startup penalty.
  100 | 47 % of viewers abandon a stream that takes > 3 s to start; early detection
  101 | in CI prevents regressions landing in production.
  102 | 
  103 | **Pass condition:** \`timeToFirstFrameMs > 2 000\`
  104 |     `.trim());
  105 |     await allure.label('layer', 'e2e');
  106 |     await allure.label('testType', 'automated');
  107 |     await allure.tag('qoe', 'ttff', 'startup-delay');
  108 | 
> 109 |     await page.goto('/?scenario=startup_delay&e2e_autoplay=1');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/?scenario=startup_delay&e2e_autoplay=1
  110 | 
  111 |     await allure.step('Wait for first frame (with injected delay)', () => waitForFirstFrame(page));
  112 | 
  113 |     const snap = await snapshot(page);
  114 |     const ttff = snap!.timeToFirstFrameMs!;
  115 | 
  116 |     await allure.step('Assert startup delay was measured (ttff > 2 000 ms)', async () => {
  117 |       await allure.parameter('timeToFirstFrameMs',  String(ttff));
  118 |       await allure.parameter('injected_delay_ms',  String(2_800));
  119 |       expect(ttff).toBeGreaterThan(2_000);
  120 |     });
  121 | 
  122 |     await allure.step('Assert no critical network issues', async () => {
  123 |       await assertNoNetworkIssues(networkCapture.entries);
  124 |     });
  125 |   });
  126 | 
  127 |   // ──────────────────────────────────────────────────────────────────────────
  128 | 
  129 |   test('black_screen_pulse: blackout overlay appears for CV-style probes', { tag: ['@BAT'] }, async ({ page, networkCapture }) => {
  130 |     await allure.feature('Visual Fault Detection');
  131 |     await allure.story('Black screen pulse (decoder freeze simulation)');
  132 |     await allure.severity('critical');
  133 |     await allure.description(`
  134 | **Scenario:** Visual fault — a black overlay covers the video at 3 500 ms
  135 | for 1 600 ms, simulating a GPU decoder stall or frame corruption event.
  136 | 
  137 | This fault is *invisible to server-side logs* — only a client-side visual
  138 | probe (or computer-vision CI check) can catch it. The test asserts that the
  139 | \`data-testid="visual-blackout-overlay"\` element appears and then clears.
  140 | 
  141 | **Pass conditions:**
  142 | - Overlay becomes visible within 15 s
  143 | - Overlay clears within 15 s of appearing
  144 |     `.trim());
  145 |     await allure.label('layer', 'e2e');
  146 |     await allure.label('testType', 'automated');
  147 |     await allure.tag('qoe', 'visual-fault', 'black-screen');
  148 | 
  149 |     await page.goto('/?scenario=black_screen_pulse&e2e_autoplay=1');
  150 | 
  151 |     const overlay = page.getByTestId('visual-blackout-overlay');
  152 | 
  153 |     await allure.step('Assert blackout overlay becomes visible', async () => {
  154 |       await expect(overlay).toBeVisible({ timeout: 15_000 });
  155 |     });
  156 | 
  157 |     await allure.step('Assert blackout overlay clears automatically', async () => {
  158 |       await expect(overlay).toBeHidden({ timeout: 15_000 });
  159 |     });
  160 | 
  161 |     await allure.step('Assert no critical network issues', async () => {
  162 |       await assertNoNetworkIssues(networkCapture.entries);
  163 |     });
  164 |   });
  165 | 
  166 |   // ──────────────────────────────────────────────────────────────────────────
  167 | 
  168 |   test('forced_mid_play_rebuffer: records at least one buffering span', { tag: ['@Smoke'] }, async ({ page, networkCapture }) => {
  169 |     await allure.feature('Rebuffering Detection');
  170 |     await allure.story('Mid-play stall (HLS stop/start)');
  171 |     await allure.severity('critical');
  172 |     await allure.description(`
  173 | **Scenario:** Mid-play rebuffering — HLS segment loading is halted at 4 500 ms
  174 | for 2 200 ms, then resumed.
  175 | 
  176 | Rebuffering mid-play is the primary driver of viewer churn. The QoE collector
  177 | must detect the stall via the \`waiting\` media event, measure its duration,
  178 | and accumulate it in \`totalBufferingTime\`.
  179 | 
  180 | **Pass condition:** \`bufferingEventsCount > 0\` OR \`totalBufferingTime > 0.05 s\`
  181 |     `.trim());
  182 |     await allure.label('layer', 'e2e');
  183 |     await allure.label('testType', 'automated');
  184 |     await allure.tag('qoe', 'rebuffering', 'stall');
  185 | 
  186 |     await page.goto('/?scenario=forced_mid_play_rebuffer&e2e_autoplay=1');
  187 | 
  188 |     await allure.step('Wait for first frame', () => waitForFirstFrame(page));
  189 | 
  190 |     await allure.step('Assert at least one buffering event was recorded', async () => {
  191 |       await expect
  192 |         .poll(async () => {
  193 |           const s = await snapshot(page);
  194 |           return (s?.bufferingEventsCount ?? 0) > 0 || (s?.totalBufferingTime ?? 0) > 0.05;
  195 |         }, { timeout: 60_000 })
  196 |         .toBe(true);
  197 | 
  198 |       const snap = await snapshot(page);
  199 |       await allure.parameter('bufferingEventsCount',   String(snap?.bufferingEventsCount ?? 0));
  200 |       await allure.parameter('totalBufferingTime_s',   String(snap?.totalBufferingTime   ?? 0));
  201 |     });
  202 | 
  203 |     await allure.step('Assert HLS segment continuity (no prolonged network error)', async () => {
  204 |       const segErrors     = networkCapture.entries.filter(e => e.category === 'hls-segment' && e.failed);
  205 |       const totalSegs     = networkCapture.entries.filter(e => e.category === 'hls-segment').length;
  206 |       const segErrorRate  = totalSegs > 0 ? Math.round((segErrors.length / totalSegs) * 100) : 0;
  207 |       await allure.parameter('seg_total',       String(totalSegs));
  208 |       await allure.parameter('seg_errors',      String(segErrors.length));
  209 |       await allure.parameter('seg_error_rate', `${segErrorRate}%`);
```