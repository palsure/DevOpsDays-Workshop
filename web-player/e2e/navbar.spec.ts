import { test, expect } from './fixtures';
import { allure }       from 'allure-playwright';

/**
 * navbar.spec.ts
 *
 * Tagged @BAT so it runs as part of the build-acceptance gate — the navbar is
 * on every page, so a regression here breaks every user flow downstream.
 *
 * The "Pipeline" link was removed from the navbar; this spec is the regression
 * guard that fails if any future change re-introduces it.
 */

test.describe('Navbar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const testedUrl = page.url();
    await allure.parameter('tested_url', testedUrl);
    await allure.link(testedUrl, 'Tested App URL');
  });

  test('renders the StreamApp brand and the four nav items', { tag: ['@BAT'] }, async ({ page }) => {
    await allure.feature('Navbar');
    await allure.story('Branding + nav items');
    await allure.severity('blocker');
    await allure.description(`
The navbar is the global chrome on every page. This BAT-gated test asserts:

- The **StreamApp** brand is visible.
- The nav exposes exactly **Home / Movies / Shows / Live** in that order.
- The right-hand affordances (**Search** + **Profile**) are reachable by their
  ARIA labels.

Any rebrand or nav restructure should be a deliberate UX decision and will trip
this test, prompting the change to be reviewed before it ships to users.
    `.trim());
    await allure.label('layer', 'e2e');
    await allure.tag('qoe', 'navbar', 'bat');

    const navbar = page.locator('nav.navbar');

    await allure.step('navbar is visible', async () => {
      await expect(navbar).toBeVisible();
    });

    await allure.step('StreamApp brand visible', async () => {
      await expect(navbar.locator('.navbar-logo-text')).toHaveText('StreamApp');
    });

    await allure.step('nav items = [Home, Movies, Shows, Live]', async () => {
      const labels = await navbar
        .locator('.navbar-links button')
        .allTextContents();
      expect(labels.map(l => l.trim())).toEqual(['Home', 'Movies', 'Shows', 'Live']);
    });

    await allure.step('Search and Profile affordances are present', async () => {
      await expect(navbar.locator('button[aria-label="Search"]')).toBeVisible();
      await expect(navbar.locator('[aria-label="Profile"]')).toBeVisible();
    });
  });

  test('does not show the removed Pipeline link', { tag: ['@BAT'] }, async ({ page }) => {
    await allure.feature('Navbar');
    await allure.story('Pipeline link removed');
    await allure.severity('normal');
    await allure.description(`
Regression guard. The Pipeline page was removed from the web player; the navbar
must not surface a link to it. If a future PR re-adds an "onPipeline" prop or a
list item labelled "Pipeline", this test fails before merge.
    `.trim());
    await allure.tag('qoe', 'navbar', 'regression');

    const navbar = page.locator('nav.navbar');

    await allure.step('no nav button labelled "Pipeline"', async () => {
      await expect(
        navbar.locator('.navbar-links button', { hasText: /^Pipeline$/ }),
      ).toHaveCount(0);
    });
  });

  test('clicking Home returns to the catalog from a detail page', { tag: ['@BAT'] }, async ({ page }) => {
    await allure.feature('Navbar');
    await allure.story('Home navigation');
    await allure.severity('critical');
    await allure.description(`
The Home link is the primary "escape hatch" out of any sub-page. This test
navigates into a detail page via the home carousel, then asserts that clicking
the Home nav link returns to the catalog (the QoE Demo Scenarios row is the
canonical landmark — only present on the home page).
    `.trim());
    await allure.tag('qoe', 'navbar', 'navigation');

    // Open any catalog tile to leave the home page.
    // Tiles render with className "video-tile" and data-testid="tile-<id>".
    const firstTile = page.locator('.video-tile').first();
    await firstTile.scrollIntoViewIfNeeded();
    await firstTile.click();

    // Sanity check: we navigated away from home.
    await expect(page.locator('text=QoE Demo Scenarios')).toHaveCount(0, { timeout: 5_000 });

    await allure.step('click Home in the navbar', async () => {
      await page
        .locator('nav.navbar .navbar-links button', { hasText: /^Home$/ })
        .click();
    });

    await allure.step('home landmark "QoE Demo Scenarios" is visible again', async () => {
      await expect(page.locator('text=QoE Demo Scenarios')).toBeVisible({ timeout: 10_000 });
    });
  });
});
