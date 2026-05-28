// base.spec.js
// ============
// BASE REGRESSION TESTS — always run, regardless of what changed in Git.
// These are the business rules that must NEVER break.

// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('🔒 Base — Invariants that must NEVER change', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test('"Join Now" button must always exist and display "Join Now"', async ({ page }) => {
    const btn = page.locator('#btn-participar');
    await expect(btn).toBeVisible();
    await expect(btn).toHaveText('Join Now');
  });

  test('page must always have a main heading (#main-title)', async ({ page }) => {
    const title = page.locator('#main-title');
    await expect(title).toBeVisible();
  });

  test('event text (#event-text) must always be visible', async ({ page }) => {
    const eventText = page.locator('#event-text');
    await expect(eventText).toBeVisible();
  });

  test('Intel logo must always be visible', async ({ page }) => {
    const logo = page.locator('#logo');
    await expect(logo).toBeVisible();
  });

  test('footer must always be present', async ({ page }) => {
    const footer = page.locator('#footer-text');
    await expect(footer).toBeVisible();
  });

  test('button click must change text to "Registered! 🎉"', async ({ page }) => {
    const btn = page.locator('#btn-participar');
    await btn.click();
    await expect(btn).toHaveText('Registered! 🎉');
    await expect(btn).toBeDisabled();
  });

});
