import { test, expect } from '@playwright/test';

test('basic navigation test', async ({ page }) => {
  // Navigate to the application
  await page.goto('http://localhost:3000');

  // Check if the page loads
  await expect(page).toHaveTitle(/Social Media Automation/);

  // Check for main navigation elements
  await expect(page.locator('text=Upload')).toBeVisible();
  await expect(page.locator('text=Schedule')).toBeVisible();
  await expect(page.locator('text=Insights')).toBeVisible();
});

test('upload page test', async ({ page }) => {
  await page.goto('http://localhost:3000/upload');

  // Check if upload form is present
  await expect(page.locator('input[type="file"]')).toBeVisible();
  await expect(page.locator('button[type="submit"]')).toBeVisible();
});

test('schedule page test', async ({ page }) => {
  await page.goto('http://localhost:3000/schedule');

  // Check if schedule form is present
  await expect(page.locator('form')).toBeVisible();
});
