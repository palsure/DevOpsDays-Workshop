# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: player-controls.spec.ts >> ABR & Bitrate (HLS.js level management) >> ABR selects a valid quality level after first frame
- Location: e2e/player-controls.spec.ts:294:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/?scenario=baseline&e2e_autoplay=1
Call log:
  - navigating to "http://localhost:3000/?scenario=baseline&e2e_autoplay=1", waiting until "load"

```

# Test source

```ts
  133 |         .toBeGreaterThan(frozenTime + 0.3);
  134 | 
  135 |       const snapAfter = await bridge.snapshot(page) as QoeDemoSnapshot;
  136 |       await allure.parameter('isPaused',         String(snapAfter.isPaused));
  137 |       await allure.parameter('frozenTime_s',     String(frozenTime));
  138 |       await allure.parameter('resumedTime_s',    String(snapAfter.currentTime));
  139 |       expect(snapAfter.isPaused).toBe(false);
  140 |     });
  141 |   });
  142 | 
  143 |   // ── Seek forward ──────────────────────────────────────────────────────────
  144 | 
  145 |   test('seek forward: currentTime jumps to target position', { tag: ['@Smoke'] }, async ({ page }) => {
  146 |     await allure.feature('Player Controls');
  147 |     await allure.story('Seek Forward');
  148 |     await allure.severity('normal');
  149 |     await allure.description(`
  150 | Seeks the playhead forward to 20 s and verifies the video element reports
  151 | the new position within ±2 s.
  152 | 
  153 | **Pass condition:** \`currentTime ≥ 18 s\`
  154 |     `.trim());
  155 | 
  156 |     const TARGET = 20;
  157 | 
  158 |     await allure.step(`Seek to ${TARGET}s`, () => bridge.seek(page, TARGET));
  159 | 
  160 |     await allure.step('Wait for playhead to reach target', () =>
  161 |       waitForPlayhead(page, TARGET - 2));
  162 | 
  163 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  164 | 
  165 |     await allure.step('Assert currentTime is at target', async () => {
  166 |       await allure.parameter('seekTarget_s',   String(TARGET));
  167 |       await allure.parameter('currentTime_s',  String(snap.currentTime));
  168 |       expect(snap.currentTime).toBeGreaterThanOrEqual(TARGET - 2);
  169 |     });
  170 |   });
  171 | 
  172 |   // ── Seek backward ─────────────────────────────────────────────────────────
  173 | 
  174 |   test('seek backward: currentTime rewinds to earlier position', { tag: ['@Smoke'] }, async ({ page }) => {
  175 |     await allure.feature('Player Controls');
  176 |     await allure.story('Seek Backward');
  177 |     await allure.severity('normal');
  178 |     await allure.description(`
  179 | Seeks the playhead forward to 30 s, then rewinds back to 5 s. Verifies that
  180 | the player correctly handles backward seeking in an HLS VOD stream.
  181 | 
  182 | **Pass condition:** currentTime ≤ 8 s after the backward seek.
  183 |     `.trim());
  184 | 
  185 |     await allure.step('Seek forward to 30s', () => bridge.seek(page, 30));
  186 |     await waitForPlayhead(page, 28);
  187 | 
  188 |     const snapMid = await bridge.snapshot(page) as QoeDemoSnapshot;
  189 |     await allure.parameter('midpoint_s',  String(snapMid.currentTime));
  190 | 
  191 |     await allure.step('Seek backward to 5s', () => bridge.seek(page, 5));
  192 |     await page.waitForTimeout(800);
  193 | 
  194 |     const snapAfter = await bridge.snapshot(page) as QoeDemoSnapshot;
  195 | 
  196 |     await allure.step('Assert currentTime is at the rewound position', async () => {
  197 |       await allure.parameter('rewindTarget_s',  String(5));
  198 |       await allure.parameter('currentTime_s',   String(snapAfter.currentTime));
  199 |       expect(snapAfter.currentTime).toBeLessThanOrEqual(8);
  200 |     });
  201 |   });
  202 | 
  203 |   // ── Seek boundary ─────────────────────────────────────────────────────────
  204 | 
  205 |   test('seek to 0 resets playhead to beginning', { tag: ['@Smoke'] }, async ({ page }) => {
  206 |     await allure.feature('Player Controls');
  207 |     await allure.story('Seek Boundary');
  208 |     await allure.severity('minor');
  209 |     await allure.description('Seeking to 0 resets the playhead to the beginning of the stream.');
  210 | 
  211 |     await allure.step('Seek forward to 15s', () => bridge.seek(page, 15));
  212 |     await waitForPlayhead(page, 13);
  213 | 
  214 |     await allure.step('Seek back to 0', () => bridge.seek(page, 0));
  215 |     await page.waitForTimeout(600);
  216 | 
  217 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  218 | 
  219 |     await allure.step('Assert currentTime ≤ 2 s', async () => {
  220 |       await allure.parameter('currentTime_s',  String(snap.currentTime));
  221 |       expect(snap.currentTime).toBeLessThanOrEqual(2);
  222 |     });
  223 |   });
  224 | });
  225 | 
  226 | // ─────────────────────────────────────────────────────────────────────────────
  227 | // Suite 2 — ABR & Bitrate
  228 | // ─────────────────────────────────────────────────────────────────────────────
  229 | 
  230 | test.describe('ABR & Bitrate (HLS.js level management)', () => {
  231 | 
  232 |   test.beforeEach(async ({ page }) => {
> 233 |     await page.goto('/?scenario=baseline&e2e_autoplay=1');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/?scenario=baseline&e2e_autoplay=1
  234 |     await waitForManifest(page);
  235 |   });
  236 | 
  237 |   // ── Quality levels ─────────────────────────────────────────────────────────
  238 | 
  239 |   test('multiple quality levels are available after manifest parse', { tag: ['@BAT'] }, async ({ page }) => {
  240 |     await allure.feature('ABR');
  241 |     await allure.story('Quality Levels');
  242 |     await allure.severity('critical');
  243 |     await allure.description(`
  244 | Verifies that the HLS manifest exposes more than one quality rendition.
  245 | ABR requires at least 2 levels to be meaningful.
  246 | 
  247 | **Pass condition:** \`hlsLevels.length > 1\`
  248 |     `.trim());
  249 | 
  250 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  251 | 
  252 |     await allure.step('Assert multiple quality levels', async () => {
  253 |       await allure.parameter('levelCount',  String(snap.hlsLevels.length));
  254 |       for (const l of snap.hlsLevels) {
  255 |         await allure.parameter(`level_${l.index}`,  String(l.name));
  256 |       }
  257 |       expect(snap.hlsLevels.length).toBeGreaterThan(1);
  258 |     });
  259 |   });
  260 | 
  261 |   // ── Bandwidth estimate ─────────────────────────────────────────────────────
  262 | 
  263 |   test('bandwidth estimate is non-zero after first segment download', { tag: ['@BAT'] }, async ({ page }) => {
  264 |     await allure.feature('ABR');
  265 |     await allure.story('Bandwidth Estimation');
  266 |     await allure.severity('normal');
  267 |     await allure.description(`
  268 | HLS.js estimates the available bandwidth after downloading the first segment.
  269 | This is the foundation of adaptive bitrate selection.
  270 | 
  271 | **Pass condition:** \`bandwidthEstimate > 0\` within 30 s.
  272 |     `.trim());
  273 | 
  274 |     await allure.step('Wait for bandwidth estimate to be non-zero', async () => {
  275 |       await expect
  276 |         .poll(() => bridge.snapshot(page).then(s => s?.bandwidthEstimate ?? 0), { timeout: 30_000 })
  277 |         .toBeGreaterThan(0);
  278 |     });
  279 | 
  280 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  281 | 
  282 |     await allure.step('Assert bandwidth estimate is reasonable', async () => {
  283 |       const estimateMbps = Math.round(snap.bandwidthEstimate / 1_000) / 1_000;
  284 |       await allure.parameter('bandwidthEstimate_bps',   String(snap.bandwidthEstimate));
  285 |       await allure.parameter('bandwidthEstimate_Mbps',  String(estimateMbps));
  286 |       // Estimate should be > 0 and below 1 Gbps (sanity check)
  287 |       expect(snap.bandwidthEstimate).toBeGreaterThan(0);
  288 |       expect(snap.bandwidthEstimate).toBeLessThan(1_000_000_000);
  289 |     });
  290 |   });
  291 | 
  292 |   // ── ABR current level ─────────────────────────────────────────────────────
  293 | 
  294 |   test('ABR selects a valid quality level after first frame', { tag: ['@Smoke'] }, async ({ page }) => {
  295 |     await allure.feature('ABR');
  296 |     await allure.story('Automatic Level Selection');
  297 |     await allure.severity('normal');
  298 |     await allure.description(`
  299 | After the first frame is rendered, HLS.js should have locked into a specific
  300 | quality level (currentLevelIndex ≥ 0).
  301 | 
  302 | **Pass condition:** \`currentLevelIndex ≥ 0\`
  303 |     `.trim());
  304 | 
  305 |     await waitForFirstFrame(page);
  306 |     await page.waitForTimeout(500);
  307 | 
  308 |     const snap = await bridge.snapshot(page) as QoeDemoSnapshot;
  309 | 
  310 |     await allure.step('Assert ABR has selected a level', async () => {
  311 |       await allure.parameter('currentLevelIndex',  String(snap.currentLevelIndex));
  312 |       await allure.parameter('currentLevel',
  313 |          String(snap.hlsLevels[snap.currentLevelIndex]?.name ?? 'auto'));
  314 |       await allure.parameter('bandwidthEstimate_bps',  String(snap.bandwidthEstimate));
  315 |       expect(snap.currentLevelIndex).toBeGreaterThanOrEqual(0);
  316 |     });
  317 |   });
  318 | 
  319 |   // ── Manual level override ──────────────────────────────────────────────────
  320 | 
  321 |   test('manual level override forces lowest quality', { tag: ['@Smoke'] }, async ({ page }) => {
  322 |     await allure.feature('ABR');
  323 |     await allure.story('Manual Level Override');
  324 |     await allure.severity('normal');
  325 |     await allure.description(`
  326 | Calling setLevel(0) forces HLS.js to lock to the lowest quality rendition
  327 | regardless of available bandwidth. This is useful for testing degraded
  328 | network conditions without actual throttling.
  329 | 
  330 | **Pass condition:** \`currentLevelIndex === 0\` within 10 s.
  331 |     `.trim());
  332 | 
  333 |     await waitForFirstFrame(page);
```