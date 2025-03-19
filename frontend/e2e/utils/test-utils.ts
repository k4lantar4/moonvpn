import { Page, expect } from '@playwright/test';

export async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', process.env.ADMIN_EMAIL || 'admin@example.com');
  await page.fill('[data-testid="password"]', process.env.ADMIN_PASSWORD || 'admin123');
  await page.click('[data-testid="login-button"]');
  await expect(page.locator('[data-testid="admin-dashboard"]')).toBeVisible();
}

export async function loginAsUser(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', process.env.USER_EMAIL || 'user@example.com');
  await page.fill('[data-testid="password"]', process.env.USER_PASSWORD || 'user123');
  await page.click('[data-testid="login-button"]');
  await expect(page.locator('[data-testid="user-dashboard"]')).toBeVisible();
}

export async function setLanguage(page: Page, language: 'en' | 'fa') {
  await page.click('[data-testid="language-selector"]');
  await page.click(`[data-testid="language-${language}"]`);
  await expect(page.locator(`[data-testid="current-language-${language}"]`)).toBeVisible();
}

export async function toggleTheme(page: Page) {
  await page.click('[data-testid="theme-toggle"]');
}

export async function toggleAccessibilityFeature(page: Page, feature: 'contrast' | 'motion' | 'font-size') {
  await page.click('[data-testid="accessibility-menu"]');
  await page.click(`[data-testid="${feature}-toggle"]`);
}

export async function checkAccessibility(page: Page) {
  // Add axe-core accessibility checks
  await page.evaluate(() => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js';
      script.onload = resolve;
      document.head.appendChild(script);
    });
  });

  const violations = await page.evaluate(() => {
    return new Promise((resolve) => {
      // @ts-ignore
      window.axe.run((err: any, results: any) => {
        if (err) throw err;
        resolve(results.violations);
      });
    });
  });

  return violations;
}

export async function waitForLoadingToComplete(page: Page) {
  await page.waitForSelector('[data-testid="loading-indicator"]', { state: 'hidden' });
}

export async function interceptAPIRequests(page: Page) {
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    // Log API requests for debugging
    console.log(`${request.method()} ${request.url()}`);
    await route.continue();
  });
}

export async function mockAPIResponse(page: Page, url: string, data: any) {
  await page.route(url, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data),
    });
  });
}

export async function checkForConsoleErrors(page: Page) {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  return errors;
}

export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({
    path: `./test-results/screenshots/${name}.png`,
    fullPage: true,
  });
}

export async function checkPerformance(page: Page) {
  const metrics = await page.evaluate(() => {
    const timing = performance.timing;
    return {
      loadTime: timing.loadEventEnd - timing.navigationStart,
      domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
      firstPaint: performance.getEntriesByType('paint')[0]?.startTime,
      firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime,
    };
  });
  return metrics;
} 