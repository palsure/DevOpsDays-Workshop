import { describe, expect, it } from 'vitest';
import { DEMO_SCENARIO_IDS, DEMO_SCENARIO_LABELS, parseDemoScenario } from './scenarios';

describe('parseDemoScenario', () => {
  it('defaults invalid values to baseline', () => {
    expect(parseDemoScenario(null)).toBe('baseline');
    expect(parseDemoScenario('')).toBe('baseline');
    expect(parseDemoScenario('unknown')).toBe('baseline');
  });

  it('accepts every known scenario id', () => {
    for (const id of DEMO_SCENARIO_IDS) {
      expect(parseDemoScenario(id)).toBe(id);
    }
  });

  it('returns "baseline" for a string that is a prefix of a valid id', () => {
    expect(parseDemoScenario('base')).toBe('baseline');
    expect(parseDemoScenario('startup')).toBe('baseline');
  });

  it('is case-sensitive — mixed-case ids fall back to baseline', () => {
    expect(parseDemoScenario('Baseline')).toBe('baseline');
    expect(parseDemoScenario('BASELINE')).toBe('baseline');
  });
});

describe('DEMO_SCENARIO_IDS', () => {
  it('contains exactly 5 scenario ids', () => {
    expect(DEMO_SCENARIO_IDS.length).toBe(5);
  });

  it('always includes "baseline" as the first entry', () => {
    expect(DEMO_SCENARIO_IDS[0]).toBe('baseline');
  });
});

describe('DEMO_SCENARIO_LABELS', () => {
  it('has a label entry for every known scenario id', () => {
    for (const id of DEMO_SCENARIO_IDS) {
      expect(DEMO_SCENARIO_LABELS[id], `label missing for "${id}"`).toBeTruthy();
    }
  });

  it('all labels are non-empty strings', () => {
    for (const [id, label] of Object.entries(DEMO_SCENARIO_LABELS)) {
      expect(typeof label, `label for "${id}" is not a string`).toBe('string');
      expect(label.length, `label for "${id}" is empty`).toBeGreaterThan(0);
    }
  });

  it('has no extra entries beyond the known scenario ids', () => {
    const labelKeys = Object.keys(DEMO_SCENARIO_LABELS);
    expect(labelKeys.length).toBe(DEMO_SCENARIO_IDS.length);
  });
});
