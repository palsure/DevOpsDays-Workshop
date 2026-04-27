import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { QoECollector } from './qoeCollector';

describe('QoECollector', () => {
  let collector: QoECollector;

  beforeEach(() => {
    collector = new QoECollector('test-video', { silent: true });
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  // ── construction ────────────────────────────────────────────────────────────

  describe('initial state', () => {
    it('starts with zero buffering count and time', () => {
      expect(collector.getBufferingEventsCount()).toBe(0);
      expect(collector.totalBufferingTime).toBe(0);
    });

    it('starts with zero bitrate switches and null lastBitrate', () => {
      expect(collector.getBitrateSwitches()).toBe(0);
      expect(collector.lastBitrate).toBeNull();
    });

    it('starts with zero errors', () => {
      expect(collector.getErrorCount()).toBe(0);
    });

    it('generates a unique sessionId for each instance', () => {
      const a = new QoECollector('v', { silent: true });
      const b = new QoECollector('v', { silent: true });
      expect((a as any).sessionId).not.toBe((b as any).sessionId);
    });
  });

  // ── time-to-first-frame ─────────────────────────────────────────────────────

  describe('getTimeToFirstFrameMs', () => {
    it('returns null before markPlaybackRequested is called', () => {
      expect(collector.getTimeToFirstFrameMs()).toBeNull();
    });

    it('returns null when only markFirstFrameRendered has been called', () => {
      collector.markFirstFrameRendered();
      expect(collector.getTimeToFirstFrameMs()).toBeNull();
    });

    it('returns null when only markPlaybackRequested has been called', () => {
      collector.markPlaybackRequested();
      expect(collector.getTimeToFirstFrameMs()).toBeNull();
    });

    it('returns the elapsed ms between request and first frame', () => {
      let now = 1000;
      vi.spyOn(performance, 'now').mockImplementation(() => now);

      collector.markPlaybackRequested();
      now = 1750;
      collector.markFirstFrameRendered();

      expect(collector.getTimeToFirstFrameMs()).toBe(750);
    });

    it('markPlaybackRequested is idempotent — subsequent calls are ignored', () => {
      let now = 1000;
      vi.spyOn(performance, 'now').mockImplementation(() => now);

      collector.markPlaybackRequested();
      now = 9000; // second call should be ignored
      collector.markPlaybackRequested();
      now = 9500;
      collector.markFirstFrameRendered();

      // measured from the first call (1000), not the second (9000)
      expect(collector.getTimeToFirstFrameMs()).toBe(8500);
    });

    it('markFirstFrameRendered is idempotent — subsequent calls are ignored', () => {
      let now = 1000;
      vi.spyOn(performance, 'now').mockImplementation(() => now);

      collector.markPlaybackRequested();
      now = 1300;
      collector.markFirstFrameRendered();
      now = 5000; // second call should be ignored
      collector.markFirstFrameRendered();

      expect(collector.getTimeToFirstFrameMs()).toBe(300);
    });
  });

  // ── buffering tracking ──────────────────────────────────────────────────────

  describe('buffering tracking', () => {
    it('records a buffering event and accumulates duration', () => {
      vi.setSystemTime(0);
      collector.recordBufferingStart();
      vi.setSystemTime(2000); // 2 seconds later
      collector.recordBufferingEnd();

      expect(collector.getBufferingEventsCount()).toBe(1);
      expect(collector.totalBufferingTime).toBeCloseTo(2, 5);
    });

    it('ignores recordBufferingEnd when no start has been recorded', () => {
      collector.recordBufferingEnd();

      expect(collector.getBufferingEventsCount()).toBe(0);
      expect(collector.totalBufferingTime).toBe(0);
    });

    it('recordBufferingStart is idempotent while a buffering event is open', () => {
      vi.setSystemTime(0);
      collector.recordBufferingStart();
      vi.setSystemTime(1000);
      collector.recordBufferingStart(); // ignored — use the original start time
      vi.setSystemTime(3000);
      collector.recordBufferingEnd();

      expect(collector.getBufferingEventsCount()).toBe(1);
      expect(collector.totalBufferingTime).toBeCloseTo(3, 5);
    });

    it('accumulates multiple buffering events', () => {
      vi.setSystemTime(0);
      collector.recordBufferingStart();
      vi.setSystemTime(1000);
      collector.recordBufferingEnd(); // 1 second

      vi.setSystemTime(5000);
      collector.recordBufferingStart();
      vi.setSystemTime(7000);
      collector.recordBufferingEnd(); // 2 seconds

      expect(collector.getBufferingEventsCount()).toBe(2);
      expect(collector.totalBufferingTime).toBeCloseTo(3, 5);
    });

    it('does not double-count if recordBufferingEnd is called twice', () => {
      vi.setSystemTime(0);
      collector.recordBufferingStart();
      vi.setSystemTime(1000);
      collector.recordBufferingEnd();
      collector.recordBufferingEnd(); // second call with no open event

      expect(collector.getBufferingEventsCount()).toBe(1);
    });
  });

  // ── error tracking ──────────────────────────────────────────────────────────

  describe('error tracking', () => {
    it('increments the error count for each recorded error', () => {
      collector.recordError('NET_ERR', 'Network error');
      expect(collector.getErrorCount()).toBe(1);

      collector.recordError('DECODE_ERR', 'Decode failed');
      expect(collector.getErrorCount()).toBe(2);
    });

    it('stores distinct error codes', () => {
      collector.recordError('A', 'first');
      collector.recordError('B', 'second');
      const errors = (collector as any).errors as Array<{ code: string }>;
      expect(errors.map(e => e.code)).toEqual(['A', 'B']);
    });
  });

  // ── bitrate tracking ────────────────────────────────────────────────────────

  describe('bitrate tracking', () => {
    it('does not count the first bitrate set as a switch', () => {
      collector.recordBitrateChange(1_000_000);

      expect(collector.getBitrateSwitches()).toBe(0);
      expect(collector.lastBitrate).toBe(1_000_000);
    });

    it('counts a switch when the bitrate changes', () => {
      collector.recordBitrateChange(1_000_000);
      collector.recordBitrateChange(500_000);

      expect(collector.getBitrateSwitches()).toBe(1);
    });

    it('does not count as a switch when the bitrate stays the same', () => {
      collector.recordBitrateChange(1_000_000);
      collector.recordBitrateChange(1_000_000);

      expect(collector.getBitrateSwitches()).toBe(0);
    });

    it('counts multiple switches correctly', () => {
      [1_000_000, 500_000, 1_000_000, 250_000].forEach(b =>
        collector.recordBitrateChange(b),
      );

      expect(collector.getBitrateSwitches()).toBe(3);
    });

    it('tracks the last observed bitrate', () => {
      collector.recordBitrateChange(1_000_000);
      collector.recordBitrateChange(250_000);

      expect(collector.lastBitrate).toBe(250_000);
    });
  });

  // ── sendMetrics (silent) ────────────────────────────────────────────────────

  describe('sendMetrics in silent mode', () => {
    it('resolves without throwing', async () => {
      collector.markPlaybackRequested();
      collector.markFirstFrameRendered();

      await expect(
        collector.sendMetrics({ playbackState: 'playing', currentTime: 5, duration: 120 }),
      ).resolves.toBeUndefined();
    });
  });
});
