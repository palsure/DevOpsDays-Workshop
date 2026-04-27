import { describe, expect, it } from 'vitest';
import { DEMO_SCENARIO_IDS } from '../demo/scenarios';
import { ALL_VIDEOS, CATALOG, HERO_VIDEO, findVideo } from './catalog';

// ── CATALOG structure ───────────────────────────────────────────────────────

describe('CATALOG', () => {
  it('contains at least one row', () => {
    expect(CATALOG.length).toBeGreaterThan(0);
  });

  it('every row has a non-empty id and label', () => {
    for (const row of CATALOG) {
      expect(row.id).toBeTruthy();
      expect(row.label).toBeTruthy();
    }
  });

  it('every row contains at least one video', () => {
    for (const row of CATALOG) {
      expect(row.videos.length).toBeGreaterThan(0);
    }
  });

  it('contains a "featured" row', () => {
    expect(CATALOG.find(r => r.id === 'featured')).toBeDefined();
  });

  it('contains a "qoe-scenarios" row', () => {
    expect(CATALOG.find(r => r.id === 'qoe-scenarios')).toBeDefined();
  });

  it('the qoe-scenarios row covers all 5 DemoScenarioIds', () => {
    const qoeRow = CATALOG.find(r => r.id === 'qoe-scenarios')!;
    const scenariosUsed = qoeRow.videos.map(v => v.scenario);
    for (const id of DEMO_SCENARIO_IDS) {
      expect(scenariosUsed).toContain(id);
    }
  });
});

// ── ALL_VIDEOS ──────────────────────────────────────────────────────────────

describe('ALL_VIDEOS', () => {
  it('is the flat union of all CATALOG rows', () => {
    expect(ALL_VIDEOS).toEqual(CATALOG.flatMap(r => r.videos));
  });

  it('contains more than 5 videos', () => {
    expect(ALL_VIDEOS.length).toBeGreaterThan(5);
  });

  it('all video IDs are unique', () => {
    const ids = ALL_VIDEOS.map(v => v.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('all videos have non-empty id, title, and description', () => {
    for (const video of ALL_VIDEOS) {
      expect(video.id, `video.id for "${video.title}"`).toBeTruthy();
      expect(video.title, `video.title for id "${video.id}"`).toBeTruthy();
      expect(video.description, `video.description for id "${video.id}"`).toBeTruthy();
    }
  });

  it('all hlsUrl values are valid http(s) URLs', () => {
    for (const video of ALL_VIDEOS) {
      expect(video.hlsUrl, `hlsUrl for "${video.id}"`).toMatch(/^https?:\/\/.+\.m3u8$/);
    }
  });

  it('all matchScore values are in the range 0–100', () => {
    for (const video of ALL_VIDEOS) {
      expect(video.matchScore, `matchScore for "${video.id}"`).toBeGreaterThanOrEqual(0);
      expect(video.matchScore, `matchScore for "${video.id}"`).toBeLessThanOrEqual(100);
    }
  });

  it('all scenario values are valid DemoScenarioIds', () => {
    for (const video of ALL_VIDEOS) {
      expect(
        DEMO_SCENARIO_IDS as readonly string[],
        `scenario for "${video.id}"`,
      ).toContain(video.scenario);
    }
  });

  it('all year values are plausible (≥ 2000)', () => {
    for (const video of ALL_VIDEOS) {
      expect(video.year).toBeGreaterThanOrEqual(2000);
    }
  });
});

// ── findVideo ───────────────────────────────────────────────────────────────

describe('findVideo', () => {
  it('returns undefined for an unknown id', () => {
    expect(findVideo('does-not-exist')).toBeUndefined();
  });

  it('returns undefined for an empty string', () => {
    expect(findVideo('')).toBeUndefined();
  });

  it('finds every video present in ALL_VIDEOS by its id', () => {
    for (const video of ALL_VIDEOS) {
      expect(findVideo(video.id)).toBe(video);
    }
  });

  it('returns the exact same object reference (no clone)', () => {
    const video = ALL_VIDEOS[0];
    expect(findVideo(video.id)).toBe(video);
  });
});

// ── HERO_VIDEO ──────────────────────────────────────────────────────────────

describe('HERO_VIDEO', () => {
  it('is the first video in the "featured" row', () => {
    const featured = CATALOG.find(r => r.id === 'featured')!;
    expect(HERO_VIDEO).toBe(featured.videos[0]);
  });

  it('is findable by its id', () => {
    expect(findVideo(HERO_VIDEO.id)).toBe(HERO_VIDEO);
  });

  it('has a baseline scenario', () => {
    expect(HERO_VIDEO.scenario).toBe('baseline');
  });
});
