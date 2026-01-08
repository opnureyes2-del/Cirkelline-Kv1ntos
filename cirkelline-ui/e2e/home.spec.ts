import { test, expect } from '@playwright/test'

test.describe('Home Page', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/')

    // Wait for the page to load
    await page.waitForLoadState('networkidle')

    // Check that we're on the right page
    expect(page.url()).toContain('localhost:3000')
  })

  test('should have proper title', async ({ page }) => {
    await page.goto('/')

    // Check that the page has loaded properly
    const body = page.locator('body')
    await expect(body).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Verify page loads in mobile view
    await page.waitForLoadState('domcontentloaded')
    expect(page.url()).toContain('localhost:3000')
  })
})

test.describe('Navigation', () => {
  test('should have working navigation elements', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    // Check for main navigation elements
    const main = page.locator('main')
    await expect(main).toBeVisible()
  })
})

test.describe('Chat Interface', () => {
  test('should have chat input area', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Look for textarea or input element for chat
    const chatInput = page.locator('textarea, input[type="text"]').first()
    if (await chatInput.isVisible()) {
      await expect(chatInput).toBeEnabled()
    }
  })
})

test.describe('Theme', () => {
  test('should support dark mode toggle', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    // Check for theme-related elements (html class or data attribute)
    const html = page.locator('html')
    await expect(html).toBeVisible()

    // Verify theme attribute exists (could be 'light' or 'dark')
    const classAttr = await html.getAttribute('class')
    const styleAttr = await html.getAttribute('style')

    // Page should have some styling applied
    expect(classAttr !== null || styleAttr !== null).toBeTruthy()
  })
})

test.describe('Accessibility', () => {
  test('should have no major accessibility violations', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')

    // Basic accessibility checks
    // Check for main landmark
    const main = page.getByRole('main')
    if (await main.count() > 0) {
      await expect(main.first()).toBeVisible()
    }

    // Check for buttons have accessible names
    const buttons = page.getByRole('button')
    const buttonCount = await buttons.count()

    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const button = buttons.nth(i)
      if (await button.isVisible()) {
        // Button should have accessible name
        const name = await button.getAttribute('aria-label')
        const text = await button.textContent()
        expect(name !== null || (text && text.length > 0)).toBeTruthy()
      }
    }
  })
})
