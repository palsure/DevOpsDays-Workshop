import { describe, expect, it } from 'vitest';
import { DEMO_SCENARIO_IDS, parseDemoScenario } from './scenarios';

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
});
