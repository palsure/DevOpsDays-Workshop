import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import * as allure from 'allure-js-commons';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Navbar } from './Navbar';

// Tell React 18 we're in a test environment so it accepts act() wrapping.
// Must be set BEFORE the first render — see
// https://react.dev/reference/react/act#error-the-current-testing-environment-is-not-configured-to-support-act
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Lightweight component rendering helper — avoids pulling in
// @testing-library/react just for these few assertions. JSDOM is provided by
// vitest's `environment: 'jsdom'` setting (see vite.config.ts).
function render(ui: React.ReactElement): { container: HTMLDivElement; root: Root } {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => { root.render(ui); });
  return { container, root };
}

describe('Navbar', () => {
  let cleanup: Array<() => void> = [];

  beforeEach(() => {
    cleanup = [];
  });

  afterEach(() => {
    for (const fn of cleanup) fn();
    document.body.innerHTML = '';
  });

  function mountNavbar(onHome = vi.fn()) {
    const { container, root } = render(<Navbar onHome={onHome} />);
    cleanup.push(() => act(() => root.unmount()));
    return { container, onHome };
  }

  it('renders the StreamApp brand', async () => {
    await allure.feature('Navbar');
    await allure.story('Branding');
    await allure.description('The navbar must render the StreamApp brand with its triangle play icon so users always have a visible "back to home" affordance.');

    const { container } = mountNavbar();

    await allure.step('contains "StreamApp" brand text', () => {
      expect(container.textContent).toContain('StreamApp');
    });
    await allure.step('renders the play-icon glyph', () => {
      expect(container.querySelector('.navbar-logo-icon')?.textContent).toBe('▶');
    });
  });

  it('renders exactly the expected nav items in order', async () => {
    await allure.feature('Navbar');
    await allure.story('Nav items');
    await allure.description('After removing the Pipeline link, the navbar must show *only* Home / Movies / Shows / Live, in that order. Adding or removing items here should be a deliberate UX decision and trip this test.');

    const { container } = mountNavbar();

    const labels = Array.from(container.querySelectorAll('.navbar-links button'))
      .map(el => el.textContent?.trim());

    await allure.step('exact list = [Home, Movies, Shows, Live]', () => {
      expect(labels).toEqual(['Home', 'Movies', 'Shows', 'Live']);
    });
  });

  it('does NOT render a Pipeline link', async () => {
    await allure.feature('Navbar');
    await allure.story('Nav items');
    await allure.description('Regression guard: the Pipeline page was removed; if any code path re-introduces a Pipeline link this test fails before users see it.');

    const { container } = mountNavbar();

    await allure.step('no button labelled "Pipeline"', () => {
      const buttons = Array.from(container.querySelectorAll('button'));
      expect(buttons.find(b => b.textContent?.trim() === 'Pipeline')).toBeUndefined();
    });
  });

  it('invokes onHome when the brand is clicked', async () => {
    await allure.feature('Navbar');
    await allure.story('Interactions');
    await allure.description('Clicking the StreamApp brand must navigate the user back to the home page — the brand button is the primary "escape hatch" out of any sub-page.');

    const { container, onHome } = mountNavbar();
    const brand = container.querySelector('.navbar-logo') as HTMLButtonElement;

    await allure.step('click .navbar-logo', () => {
      act(() => { brand.click(); });
    });
    await allure.step('onHome called exactly once', () => {
      expect(onHome).toHaveBeenCalledTimes(1);
    });
  });

  it('invokes onHome when the Home nav link is clicked', async () => {
    await allure.feature('Navbar');
    await allure.story('Interactions');
    await allure.description('The Home nav link must call the onHome handler so users can return to the catalog from any page.');

    const { container, onHome } = mountNavbar();
    const homeLink = Array.from(container.querySelectorAll('.navbar-links button'))
      .find(el => el.textContent?.trim() === 'Home') as HTMLButtonElement;

    await allure.step('click Home link', () => {
      act(() => { homeLink.click(); });
    });
    await allure.step('onHome called exactly once', () => {
      expect(onHome).toHaveBeenCalledTimes(1);
    });
  });

  it('exposes Search and Profile affordances', async () => {
    await allure.feature('Navbar');
    await allure.story('Affordances');
    await allure.description('The right-hand side of the nav must expose accessible Search and Profile controls — both have aria-labels so assistive tech can target them.');

    const { container } = mountNavbar();

    await allure.step('search button has aria-label="Search"', () => {
      expect(container.querySelector('button[aria-label="Search"]')).not.toBeNull();
    });
    await allure.step('profile element has aria-label="Profile"', () => {
      expect(container.querySelector('[aria-label="Profile"]')).not.toBeNull();
    });
  });
});
