import { afterEach, describe, expect, it, vi } from 'vitest';
import { registerQoeDemoBridge, unregisterQoeDemoBridge } from './qoeDemoBridge';
import type { QoeDemoBridge } from './qoeDemoBridge';

// Minimal stub bridge for testing registration
function makeBridge(scenario: QoeDemoBridge['scenario'] = 'baseline'): QoeDemoBridge {
  return {
    scenario,
    getSnapshot: vi.fn(),
    play: vi.fn(),
    pause: vi.fn(),
    seek: vi.fn(),
    setLevel: vi.fn(),
  };
}

afterEach(() => {
  // Always clean up the global after each test
  unregisterQoeDemoBridge();
});

describe('registerQoeDemoBridge', () => {
  it('attaches the bridge to window.__QOE_DEMO__', () => {
    const bridge = makeBridge();
    registerQoeDemoBridge(bridge);
    expect(window.__QOE_DEMO__).toBe(bridge);
  });

  it('overrides a previously registered bridge', () => {
    const first = makeBridge('baseline');
    const second = makeBridge('startup_delay');
    registerQoeDemoBridge(first);
    registerQoeDemoBridge(second);
    expect(window.__QOE_DEMO__).toBe(second);
  });

  it('preserves the scenario value on the registered bridge', () => {
    const bridge = makeBridge('black_screen_pulse');
    registerQoeDemoBridge(bridge);
    expect(window.__QOE_DEMO__?.scenario).toBe('black_screen_pulse');
  });
});

describe('unregisterQoeDemoBridge', () => {
  it('removes window.__QOE_DEMO__ when a bridge is registered', () => {
    registerQoeDemoBridge(makeBridge());
    unregisterQoeDemoBridge();
    expect(window.__QOE_DEMO__).toBeUndefined();
  });

  it('is safe to call when no bridge is registered (idempotent)', () => {
    expect(() => unregisterQoeDemoBridge()).not.toThrow();
    expect(window.__QOE_DEMO__).toBeUndefined();
  });
});
