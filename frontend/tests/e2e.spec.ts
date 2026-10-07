import { test, expect } from '@playwright/test';

test.describe('Animal Guardian 360° Core Flows', () => {
  test('Landing page loads and displays core rescue modules', async ({ page }) => {
    await page.goto('/en');
    await expect(page).toHaveTitle(/Animal Guardian 360°/);
    await expect(page.locator('text=Animal Guardian 360°')).toBeVisible();
    await expect(page.locator('text=Nearby Vets & SOS')).toBeVisible();
    await expect(page.locator('text=Report Cruelty')).toBeVisible();
    await expect(page.locator('text=Lost & Found Pets')).toBeVisible();
    await expect(page.locator('text=Donate (80G)')).toBeVisible();
  });

  test('Vet Emergency & SOS modal flow', async ({ page }) => {
    await page.goto('/en/vets');
    await expect(page.locator('text=Emergency Road Accident SOS')).toBeVisible();
    
    // Tap SOS button
    await page.click('button:has-text("SOS EMERGENCY")');
    await expect(page.locator('text=Road Accident Animal SOS')).toBeVisible();
  });

  test('Cruelty complaint preparation and disclaimer', async ({ page }) => {
    await page.goto('/en/cruelty-report');
    await expect(page.locator('text=Report Cruelty & Illegal Wildlife Trade')).toBeVisible();
    // Verify citizen disclaimer is present
    await expect(page.locator('text=prepares a formal complaint summary')).toBeVisible();
  });

  test('Lost and Found Pet listing and filters', async ({ page }) => {
    await page.goto('/en/lost-and-found');
    await expect(page.locator('text=AI Lost & Found Pet Recovery')).toBeVisible();
    await expect(page.locator('text=Report Lost Pet')).toBeVisible();
    await expect(page.locator('text=Report Sighting')).toBeVisible();
  });

  test('Donation page and 80G tax benefit information', async ({ page }) => {
    await page.goto('/en/donate');
    await expect(page.locator('text=Empower Rescues, Heal Lives')).toBeVisible();
    await expect(page.locator('text=Section 80G')).toBeVisible();
    await expect(page.locator('text=Public Transparency Ledger')).toBeVisible();
  });

  test('Public Transparency Ledger renders audit metrics', async ({ page }) => {
    await page.goto('/en/donate/transparency');
    await expect(page.locator('text=Public Financial Transparency Ledger')).toBeVisible();
    await expect(page.locator('text=Total Funds Raised')).toBeVisible();
    await expect(page.locator('text=Audited Efficiency')).toBeVisible();
  });

  test('Admin dashboard renders tabs and KPI cards', async ({ page }) => {
    await page.goto('/en/admin/dashboard');
    await expect(page.locator('text=Animal Guardian 360° Admin Console')).toBeVisible();
    await expect(page.locator('text=Overview & KPIs')).toBeVisible();
    await expect(page.locator('text=Cruelty Review Queue')).toBeVisible();
  });
});
