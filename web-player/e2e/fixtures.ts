/**
 * fixtures.ts
 *
 * Extends the base Playwright test with three fixtures:
 *
 *   networkCapture  – intercepts every request/response/failure + console
 *                     messages + uncaught JS errors for the entire test.
 *                     After the test body completes, runs the network
 *                     analyzer and attaches rich Allure artifacts.
 *
 *   networkReport   – convenience accessor; holds the NetworkReport produced
 *                     by networkCapture after the test body resolves.
 *
 *   throttle        – CDP-based network condition emulation. Call
 *                     throttle.apply('3G') to simulate throttled networks
 *                     and throttle.reset() to restore full speed.
 *
 * Usage:
 *   import { test, expect, NETWORK_PRESETS } from './fixtures';
 *   // same API as @playwright/test but with automatic network analysis
 *   // and optional network throttling.
 */

import { test as base, expect } from '@playwright/test';
import { allure }               from 'allure-playwright';

// ── Network throttle types & presets ──────────────────────────────────────────

export type NetworkPresetName = '4G' | '3G' | 'Slow3G' | '2G' | 'Offline' | 'None';

export interface ThrottleCondition {
  /** Maximum download bandwidth in kbps. Use -1 for unlimited. */
  downloadKbps: number;
  /** Maximum upload bandwidth in kbps. Use -1 for unlimited. */
  uploadKbps:   number;
  /** Additional round-trip latency in ms. */
  latencyMs:    number;
  offline?:     boolean;
}

/** Named network condition presets. Values match Chrome DevTools presets. */
export const NETWORK_PRESETS: Record<NetworkPresetName, ThrottleCondition> = {
  '4G':     { downloadKbps: 20_000, uploadKbps: 10_000, latencyMs: 20  },
  '3G':     { downloadKbps:  1_500, uploadKbps:    750, latencyMs: 100 },
  'Slow3G': { downloadKbps:    400, uploadKbps:    400, latencyMs: 300 },
  '2G':     { downloadKbps:    250, uploadKbps:     50, latencyMs: 500 },
  'Offline':{ downloadKbps:      0, uploadKbps:      0, latencyMs:   0, offline: true },
  'None':   { downloadKbps:     -1, uploadKbps:     -1, latencyMs:   0 },
};
import {
  analyze,
  categorize,
  isSlowRequest,
  toHAR,
  toTimeline,
  type NetworkEntry,
  type ConsoleEntry,
  type PageError,
  type NetworkReport,
} from './network-analyzer';

// ── Fixture types ─────────────────────────────────────────────────────────────

export type ThrottleControl = {
  /** Apply a named preset or custom condition. */
  apply: (preset: NetworkPresetName | ThrottleCondition) => Promise<void>;
  /** Restore unlimited network speed. */
  reset: () => Promise<void>;
  /** The currently active condition (undefined until apply() is called). */
  current: ThrottleCondition | undefined;
};

export type NetworkFixtures = {
  /** Call inside a test to get the live capture arrays. */
  networkCapture: {
    entries:     NetworkEntry[];
    consoleLogs: ConsoleEntry[];
    pageErrors:  PageError[];
  };
  /** Available after the test body resolves; holds the full analysis. */
  networkReport: NetworkReport | null;
  /** CDP network throttle control. Always available; starts at unlimited speed. */
  throttle: ThrottleControl;
};

// ── Extended test ─────────────────────────────────────────────────────────────

export const test = base.extend<NetworkFixtures>({

  // eslint-disable-next-line no-empty-pattern
  networkReport: [async ({}, use) => {
    // placeholder; populated by networkCapture fixture via closure
    await use(null);
  }, { scope: 'test' }],

  // ── Network throttle fixture ───────────────────────────────────────────────
  throttle: [async ({ page }, use, testInfo) => {
    // CDP session is Chromium-only (matches our project config).
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Network.enable');

    let current: ThrottleCondition | undefined;

    const applyCondition = async (cond: ThrottleCondition) => {
      current = cond;
      await cdp.send('Network.emulateNetworkConditions', {
        offline:             cond.offline ?? false,
        latency:             cond.latencyMs,
        // CDP expects bytes/s; -1 means unlimited
        downloadThroughput:  cond.downloadKbps < 0 ? -1 : (cond.downloadKbps * 1_000) / 8,
        uploadThroughput:    cond.uploadKbps   < 0 ? -1 : (cond.uploadKbps   * 1_000) / 8,
      });
    };

    const control: ThrottleControl = {
      apply: (preset) =>
        applyCondition(typeof preset === 'string' ? NETWORK_PRESETS[preset] : preset),
      reset: () => applyCondition(NETWORK_PRESETS['None']),
      get current() { return current; },
    };

    await use(control);

    // Teardown: restore unlimited speed, then detach
    await applyCondition(NETWORK_PRESETS['None']).catch(() => {});
    await cdp.detach().catch(() => {});

    // Attach throttle info to Allure if a preset was used
    if (current && current !== NETWORK_PRESETS['None']) {
      testInfo.annotations.push({
        type:        '🌐 Network Throttle',
        description: `${current.downloadKbps} kbps down / ${current.latencyMs} ms RTT`,
      });
      await allure.parameter('throttle:download_kbps', String(current.downloadKbps));
      await allure.parameter('throttle:latency_ms',    String(current.latencyMs));
    }
  }, { scope: 'test' }],

  networkCapture: [async ({ page }, use, testInfo) => {
    const entries:     NetworkEntry[]  = [];
    const consoleLogs: ConsoleEntry[]  = [];
    const pageErrors:  PageError[]     = [];
    const startTimes   = new Map<string, number>();
    const testStartMs  = Date.now();
    let   idCounter    = 0;

    // ── Request starts ──────────────────────────────────────────────
    page.on('request', req => {
      startTimes.set(req.guid, Date.now());
    });

    // ── Successful responses ────────────────────────────────────────
    page.on('response', res => {
      const req         = res.request();
      const start       = startTimes.get(req.guid) ?? Date.now();
      const durationMs  = Date.now() - start;
      const url         = res.url();
      const status      = res.status();
      const category    = categorize(url);
      const failed      = status >= 400;
      const entry: NetworkEntry = {
        id:        ++idCounter,
        url,
        method:    req.method(),
        status,
        durationMs,
        category,
        failed,
        slow:      isSlowRequest({ durationMs, category }),
        startedAt: Date.now() - testStartMs,
      };
      entries.push(entry);
    });

    // ── Network-level failures ──────────────────────────────────────
    page.on('requestfailed', req => {
      const start      = startTimes.get(req.guid) ?? Date.now();
      const durationMs = Date.now() - start;
      const url        = req.url();
      const category   = categorize(url);
      const entry: NetworkEntry = {
        id:        ++idCounter,
        url,
        method:    req.method(),
        status:    null,
        durationMs,
        category,
        failed:    true,
        slow:      false,
        errorText: req.failure()?.errorText ?? 'Unknown network error',
        startedAt: Date.now() - testStartMs,
      };
      entries.push(entry);
    });

    // ── Browser console ─────────────────────────────────────────────
    page.on('console', msg => {
      const type = msg.type() as ConsoleEntry['type'];
      consoleLogs.push({
        type,
        text:      msg.text(),
        startedAt: Date.now() - testStartMs,
      });
    });

    // ── Uncaught page-level JS errors ───────────────────────────────
    page.on('pageerror', err => {
      pageErrors.push({
        message:   err.message,
        startedAt: Date.now() - testStartMs,
      });
    });

    // ── Run the test ────────────────────────────────────────────────
    await use({ entries, consoleLogs, pageErrors });

    // ── Post-test teardown (page is still open here) ─────────────────

    // 0a. Final page screenshot — captures the player state at test end.
    //     We take this manually so Allure always gets a named "End State"
    //     screenshot regardless of pass/fail, in addition to Playwright's
    //     automatic screenshot added by the config.
    try {
      const screenshotBuf = await page.screenshot({ fullPage: false, type: 'png' });
      await allure.attachment('End State Screenshot', screenshotBuf, 'image/png');
    } catch {
      // Page may already be closing — safe to ignore
    }

    // 0b. Video is recorded by Playwright (video:'on' in config) and
    //     allure-playwright's onTestEnd hook automatically attaches
    //     testResult.attachments (video/webm) to the Allure report.
    //     Nothing extra needed here.

    // ── Post-test: analyse and attach to Allure ─────────────────────
    const report = analyze(entries, consoleLogs, pageErrors);

    // allure.parameter() requires string values — numbers cause a localeCompare crash
    // in allure-js-commons getTestResultHistoryId. Always use String().
    const p = (name: string, v: unknown) => allure.parameter(name, String(v ?? ''));

    // 1. Key metrics as Allure parameters (visible in the test detail header)
    await p('net:total_requests',   report.summary.total);
    await p('net:failed_requests',  report.summary.failed);
    await p('net:slow_requests',    report.summary.slow);
    await p('net:health',           report.summary.overallHealth);
    await p('net:issues_found',     report.issues.length);

    const segStats = report.summary.byCategory['hls-segment'];
    if (segStats.count > 0) {
      await p('hls:segments',       segStats.count);
      await p('hls:seg_errors',     segStats.failed);
      await p('hls:avg_segment_ms', segStats.avgMs);
      await p('hls:p95_segment_ms', segStats.p95Ms);
    }

    const apiStats = report.summary.byCategory['qoe-api'];
    if (apiStats.count > 0) {
      await p('api:qoe_calls',  apiStats.count);
      await p('api:qoe_errors', apiStats.failed);
      await p('api:avg_ms',     apiStats.avgMs);
    }

    // 2. Human-readable Markdown analysis (shown as an attachment in Allure)
    await allure.attachment('Network Analysis Report', report.markdownReport, 'text/markdown');

    // 3. Chronological request + console timeline (plain text, easy to scan)
    await allure.attachment(
      'Network & Console Timeline',
      toTimeline(entries, consoleLogs, pageErrors),
      'text/plain',
    );

    // 4. Standard HAR 1.2 file — importable into Chrome DevTools / Charles / Fiddler
    await allure.attachment(
      'Network HAR',
      toHAR(entries, testInfo.title),
      'application/json',
    );

    // 5. Full request log as JSON (raw captured data)
    await allure.attachment('All Network Requests (JSON)', JSON.stringify(entries, null, 2), 'application/json');

    // 6. Issues-only summary (quick triage)
    if (report.issues.length > 0) {
      await allure.attachment('Network Issues', JSON.stringify(report.issues, null, 2), 'application/json');
    }

    // 7. Console errors (separate attachment for easy scanning)
    if (report.consoleErrors.length > 0) {
      const consoleText = report.consoleErrors
        .map(e => `[+${e.startedAt}ms] ${e.text}`)
        .join('\n');
      await allure.attachment('Browser Console Errors', consoleText, 'text/plain');
    }

    // 8. Page errors
    if (report.pageErrors.length > 0) {
      await allure.attachment(
        'Uncaught Page Errors',
        report.pageErrors.map(e => `[+${e.startedAt}ms] ${e.message}`).join('\n'),
        'text/plain',
      );
    }

    // 7. Annotate the test with critical issues so they surface in the list view
    const criticalIssues = report.issues.filter(i => i.severity === 'critical');
    for (const issue of criticalIssues) {
      testInfo.annotations.push({
        type:        `🔴 ${issue.type}`,
        description: issue.url ? `${issue.message} — ${issue.url}` : issue.message,
      });
    }
    const warningIssues = report.issues.filter(i => i.severity === 'warning');
    for (const issue of warningIssues.slice(0, 3)) {
      testInfo.annotations.push({
        type:        `⚠️ ${issue.type}`,
        description: issue.message,
      });
    }
  }, { scope: 'test', auto: true }],   // auto:true — active for every test without explicit use
});

export { expect };
