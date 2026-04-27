# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: player-controls.spec.ts >> ABR & Bitrate (HLS.js level management) >> multiple quality levels are available after manifest parse
- Location: e2e/player-controls.spec.ts:245:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4173/
Call log:
  - navigating to "http://127.0.0.1:4173/", waiting until "load"

```

# Test source

```ts
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
  179 |     await allure.story('Seek Backward');
  180 |     await allure.severity('normal');
  181 |     await allure.description(`
  182 | Seeks the playhead forward to 30 s, then rewinds back to 5 s. Verifies that
  183 | the player correctly handles backward seeking in an HLS VOD stream.
  184 | 
  185 | **Pass condition:** currentTime ≤ 8 s after the backward seek.
  186 |     `.trim());
  187 | 
  188 |     await allure.step('Seek forward to 30s', () => bridge.seek(page, 30));
  189 |     await waitForPlayhead(page, 28);
  190 | 
  191 |     const snapMid = await bridge.snapshot(page) as QoeDemoSnapshot;
  192 |     await allure.parameter('midpoint_s',  String(snapMid.currentTime));
  193 | 
  194 |     await allure.step('Seek backward to 5s', () => bridge.seek(page, 5));
  195 |     await page.waitForTimeout(800);
  196 | 
  197 |     const snapAfter = await bridge.snapshot(page) as QoeDemoSnapshot;
  198 | 
  199 |     await allure.step('Assert currentTime is at the rewound position', async () => {
  200 |       await allure.parameter('rewindTarget_s',  String(5));
  201 |       await allure.parameter('currentTime_s',   String(snapAfter.currentTime));
  202 |       expect(snapAfter.currentTime).toBeLessThanOrEqual(8);
  203 |     });
  204 |   });
  205 | 
  206 |   // ── Seek boundary ─────────────────────────────────────────────────────────
  207 | 
  208 |   test('seek to 0 resets playhead to beginning', { tag: ['@Smoke'] }, async ({ page }) => {
  209 |     await allure.feature('Player Controls');
  210 |     await allure.story('Seek Boundary');
  211 |     await allure.severity('minor');
  212 |     await allure.description('Seeking to 0 resets the playhead to the beginning of the stream.');
  213 | 
  214 |     await allure.step('Seek forward to 15s', () => bridge.seek(page, 15));
  215 |     await waitForPlayhead(page, 13);
  216 | 
  217 |     await allure.step('Seek back to 0', () => bridge.seek(page, 0));
  218 |     await page.waitForTimeout(600);
  219 | 
  220 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  221 | 
  222 |     await allure.step('Assert currentTime ≤ 2 s', async () => {
  223 |       await allure.parameter('currentTime_s',  String(snap.currentTime));
  224 |       expect(snap.currentTime).toBeLessThanOrEqual(2);
  225 |     });
  226 |   });
  227 | });
  228 | 
  229 | // ─────────────────────────────────────────────────────────────────────────────
  230 | // Suite 2 — ABR & Bitrate
  231 | // ─────────────────────────────────────────────────────────────────────────────
  232 | 
  233 | test.describe('ABR & Bitrate (HLS.js level management)', () => {
  234 | 
  235 |   test.beforeEach(async ({ page }) => {
  236 |     // Navigate to home page first — visible in video recording as full navigation flow
> 237 |     await page.goto('/');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4173/
  238 |     await page.waitForLoadState('domcontentloaded');
  239 |     await page.goto('/?scenario=baseline&e2e_autoplay=1');
  240 |     await waitForManifest(page);
  241 |   });
  242 | 
  243 |   // ── Quality levels ─────────────────────────────────────────────────────────
  244 | 
  245 |   test('multiple quality levels are available after manifest parse', { tag: ['@BAT'] }, async ({ page }) => {
  246 |     await allure.feature('ABR');
  247 |     await allure.story('Quality Levels');
  248 |     await allure.severity('critical');
  249 |     await allure.description(`
  250 | Verifies that the HLS manifest exposes more than one quality rendition.
  251 | ABR requires at least 2 levels to be meaningful.
  252 | 
  253 | **Pass condition:** \`hlsLevels.length > 1\`
  254 |     `.trim());
  255 | 
  256 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  257 | 
  258 |     await allure.step('Assert multiple quality levels', async () => {
  259 |       await allure.parameter('levelCount',  String(snap.hlsLevels.length));
  260 |       for (const l of snap.hlsLevels) {
  261 |         await allure.parameter(`level_${l.index}`,  String(l.name));
  262 |       }
  263 |       expect(snap.hlsLevels.length).toBeGreaterThan(1);
  264 |     });
  265 |   });
  266 | 
  267 |   // ── Bandwidth estimate ─────────────────────────────────────────────────────
  268 | 
  269 |   test('bandwidth estimate is non-zero after first segment download', { tag: ['@BAT'] }, async ({ page }) => {
  270 |     await allure.feature('ABR');
  271 |     await allure.story('Bandwidth Estimation');
  272 |     await allure.severity('normal');
  273 |     await allure.description(`
  274 | HLS.js estimates the available bandwidth after downloading the first segment.
  275 | This is the foundation of adaptive bitrate selection.
  276 | 
  277 | **Pass condition:** \`bandwidthEstimate > 0\` within 30 s.
  278 |     `.trim());
  279 | 
  280 |     await allure.step('Wait for bandwidth estimate to be non-zero', async () => {
  281 |       await expect
  282 |         .poll(() => bridge.snapshot(page).then(s => s?.bandwidthEstimate ?? 0), { timeout: 30_000 })
  283 |         .toBeGreaterThan(0);
  284 |     });
  285 | 
  286 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  287 | 
  288 |     await allure.step('Assert bandwidth estimate is reasonable', async () => {
  289 |       const estimateMbps = Math.round(snap.bandwidthEstimate / 1_000) / 1_000;
  290 |       await allure.parameter('bandwidthEstimate_bps',   String(snap.bandwidthEstimate));
  291 |       await allure.parameter('bandwidthEstimate_Mbps',  String(estimateMbps));
  292 |       // Estimate should be > 0 and below 1 Gbps (sanity check)
  293 |       expect(snap.bandwidthEstimate).toBeGreaterThan(0);
  294 |       expect(snap.bandwidthEstimate).toBeLessThan(1_000_000_000);
  295 |     });
  296 |   });
  297 | 
  298 |   // ── ABR current level ─────────────────────────────────────────────────────
  299 | 
  300 |   test('ABR selects a valid quality level after first frame', { tag: ['@Smoke'] }, async ({ page }) => {
  301 |     await allure.feature('ABR');
  302 |     await allure.story('Automatic Level Selection');
  303 |     await allure.severity('normal');
  304 |     await allure.description(`
  305 | After the first frame is rendered, HLS.js should have locked into a specific
  306 | quality level (currentLevelIndex ≥ 0).
  307 | 
  308 | **Pass condition:** \`currentLevelIndex ≥ 0\`
  309 |     `.trim());
  310 | 
  311 |     await waitForFirstFrame(page);
  312 |     await page.waitForTimeout(500);
  313 | 
  314 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  315 | 
  316 |     await allure.step('Assert ABR has selected a level', async () => {
  317 |       await allure.parameter('currentLevelIndex',  String(snap.currentLevelIndex));
  318 |       await allure.parameter('currentLevel',
  319 |          String(snap.hlsLevels[snap.currentLevelIndex]?.name ?? 'auto'));
  320 |       await allure.parameter('bandwidthEstimate_bps',  String(snap.bandwidthEstimate));
  321 |       expect(snap.currentLevelIndex).toBeGreaterThanOrEqual(0);
  322 |     });
  323 |   });
  324 | 
  325 |   // ── Manual level override ──────────────────────────────────────────────────
  326 | 
  327 |   test('manual level override forces lowest quality', { tag: ['@Smoke'] }, async ({ page }) => {
  328 |     await allure.feature('ABR');
  329 |     await allure.story('Manual Level Override');
  330 |     await allure.severity('normal');
  331 |     await allure.description(`
  332 | Calling setLevel(0) forces HLS.js to lock to the lowest quality rendition
  333 | regardless of available bandwidth. This is useful for testing degraded
  334 | network conditions without actual throttling.
  335 | 
  336 | **Pass condition:** \`currentLevelIndex === 0\` within 10 s.
  337 |     `.trim());
```