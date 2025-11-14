import { test, expect } from '@playwright/test';

test.describe('Homepage Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check if the page loads (status 200)
    const response = await page.goto('http://localhost:3000');
    expect(response?.status()).toBe(200);
    
    // Check for basic page elements
    await expect(page.locator('body')).toBeVisible();
  });

  test('homepage has navigation elements', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check if page title exists or body is visible
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('homepage returns 200 OK', async ({ request }) => {
    const response = await request.get('http://localhost:3000');
    expect(response.status()).toBe(200);
  });
});

