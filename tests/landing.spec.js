// @ts-check
const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('Intel Costa Rica – Landing Page', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  test('should display the correct page title', async ({ page }) => {
    await expect(page).toHaveTitle('Intel Costa Rica');
  });

  test('should display main heading "Intel Costa Rica"', async ({ page }) => {
    const title = page.locator('#main-title');
    await expect(title).toBeVisible();
    await expect(title).toHaveText('Intel Costa Rica');
  });

  test('should display event text "Hackathon CR 2026"', async ({ page }) => {
    const eventText = page.locator('#event-text');
    await expect(eventText).toBeVisible();
    await expect(eventText).toHaveText('Hackathon CR 2026');
  });

  test('should display the "Participar" button', async ({ page }) => {
    const btn = page.locator('#btn-participar');
    await expect(btn).toBeVisible();
    await expect(btn).toHaveText('Participar');
  });

  test('button click changes text to "¡Registrado! 🎉"', async ({ page }) => {
    const btn = page.locator('#btn-participar');
    await btn.click();
    await expect(btn).toHaveText('¡Registrado! 🎉');
    await expect(btn).toBeDisabled();
  });

  test('should display the Intel logo', async ({ page }) => {
    const logo = page.locator('#logo');
    await expect(logo).toBeVisible();
  });

  test('should display footer text', async ({ page }) => {
    const footer = page.locator('#footer-text');
    await expect(footer).toBeVisible();
  });

});
