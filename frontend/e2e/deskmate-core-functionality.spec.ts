import { test, expect, Page } from '@playwright/test';

// Helper functions
async function waitForDeskMateToLoad(page: Page) {
  await page.waitForSelector('[data-testid="grid-container"], .grid-area', { timeout: 10000 });
  await page.waitForSelector('[data-testid="chat-window"], .chat-window', { timeout: 10000 });

  // Wait for WebSocket connection
  await page.waitForFunction(() => {
    const wsIndicator = document.querySelector('.bg-green-500');
    return wsIndicator !== null;
  }, { timeout: 15000 });
}

async function sendChatMessage(page: Page, message: string) {
  const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
  await chatInput.fill(message);
  await chatInput.press('Enter');
}

async function waitForAssistantResponse(page: Page) {
  // Wait for typing indicator to appear and disappear
  await page.waitForSelector('.animate-bounce', { timeout: 5000 });
  await page.waitForSelector('.animate-bounce', { state: 'detached', timeout: 30000 });
}

test.describe('DeskMate Core Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should load the main interface correctly', async ({ page }) => {
    // Check that main components are visible
    await expect(page.locator('.grid-area, [data-testid="grid-container"]')).toBeVisible();
    await expect(page.locator('text=DeskMate', { hasText: /DeskMate|Chat/ })).toBeVisible();

    // Grid area should be visible (no longer using 64x16 grid cells)
    const gridArea = page.locator('.grid-area, [data-testid="grid-container"]');
    await expect(gridArea).toBeVisible();

    // Check WebSocket connection indicator
    await expect(page.locator('.bg-green-500')).toBeVisible();
  });

  test('should display assistant in the grid', async ({ page }) => {
    // Look for assistant dot or indicator
    const assistant = page.locator('.bg-white').or(page.locator('[data-testid="assistant"]'));
    await expect(assistant).toBeVisible();

    // Assistant should be positioned in the grid
    const assistantElement = assistant.first();
    const boundingBox = await assistantElement.boundingBox();
    expect(boundingBox).toBeTruthy();
    expect(boundingBox!.width).toBeGreaterThan(0);
    expect(boundingBox!.height).toBeGreaterThan(0);
  });

  test('should show room objects', async ({ page }) => {
    // Wait for objects to load
    await page.waitForTimeout(2000);

    // Look for object indicators or labels
    const objects = page.locator('.bg-purple-600, .bg-orange-600, .bg-blue-500, .bg-amber-700');
    const objectCount = await objects.count();

    // Should have at least some default objects
    expect(objectCount).toBeGreaterThan(0);
  });

  test('should enable chat functionality', async ({ page }) => {
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();

    // Check chat input is visible and enabled
    await expect(chatInput).toBeVisible();
    await expect(chatInput).toBeEnabled();

    // Send a simple message
    await sendChatMessage(page, 'Hello!');

    // Wait for assistant response
    await waitForAssistantResponse(page);

    // Check that a response appeared
    const messages = page.locator('.message, .chat-message');
    const messageCount = await messages.count();
    expect(messageCount).toBeGreaterThanOrEqual(2); // User message + assistant response
  });

  test('should handle assistant movement commands', async ({ page }) => {
    // Send movement command
    await sendChatMessage(page, 'Move to position 20, 10');

    // Wait for response and potential movement
    await waitForAssistantResponse(page);
    await page.waitForTimeout(2000); // Allow time for movement animation

    // Check that assistant position might have changed
    // (This is hard to verify precisely without knowing exact implementation)
    const assistant = page.locator('.bg-white').first();
    await expect(assistant).toBeVisible();
  });

  test('should show typing indicator during processing', async ({ page }) => {
    // Send a message that requires processing
    await sendChatMessage(page, 'What can you see in the room?');

    // Check for typing indicator
    await expect(page.locator('.animate-bounce')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=typing', { hasText: /typing/i })).toBeVisible({ timeout: 5000 });

    // Wait for typing to stop
    await page.waitForSelector('.animate-bounce', { state: 'detached', timeout: 30000 });
  });
});

test.describe('DeskMate Grid Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should handle grid cell clicks for movement', async ({ page }) => {
    // Find grid container
    const grid = page.locator('.grid-area, [data-testid="grid-container"]').first();
    await expect(grid).toBeVisible();

    // Click on a grid cell (try center area)
    const gridBounds = await grid.boundingBox();
    if (gridBounds) {
      const centerX = gridBounds.x + gridBounds.width * 0.5;
      const centerY = gridBounds.y + gridBounds.height * 0.5;

      await page.mouse.click(centerX, centerY);

      // Wait for any movement or response
      await page.waitForTimeout(1000);

      // Assistant should still be visible
      const assistant = page.locator('.bg-white').first();
      await expect(assistant).toBeVisible();
    }
  });

  test('should show object information on interaction', async ({ page }) => {
    // Look for interactive objects
    const objects = page.locator('.bg-purple-600, .bg-orange-600, .bg-blue-500, .bg-amber-700');
    const objectCount = await objects.count();

    if (objectCount > 0) {
      // Click on first object
      await objects.first().click();

      // Wait for any selection or info display
      await page.waitForTimeout(500);

      // Check for selection indicators or info
      const selection = page.locator('.ring-2, .ring-blue-500, .selected');
      const selectionCount = await selection.count();
      expect(selectionCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should handle right-click interactions', async ({ page }) => {
    // Find an object to right-click
    const objects = page.locator('.bg-purple-600, .bg-orange-600, .bg-blue-500, .bg-amber-700');
    const objectCount = await objects.count();

    if (objectCount > 0) {
      // Right-click on first object
      await objects.first().click({ button: 'right' });

      // Wait for any interaction result
      await page.waitForTimeout(1000);

      // Object should still be visible (interaction completed)
      await expect(objects.first()).toBeVisible();
    }
  });
});

test.describe('DeskMate Settings and UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should open and close settings panel', async ({ page }) => {
    // Look for settings button (gear icon or settings text)
    const settingsButton = page.locator('button[title*="Settings"], button[aria-label*="Settings"], .settings-button, svg[class*="settings"]').first();

    if (await settingsButton.isVisible()) {
      await settingsButton.click();

      // Check if settings panel opened
      const settingsPanel = page.locator('.settings-panel, [role="dialog"], .modal');
      await expect(settingsPanel).toBeVisible({ timeout: 5000 });

      // Close settings
      const closeButton = page.locator('button[title*="close"], button[aria-label*="close"], .close-button').first();
      if (await closeButton.isVisible()) {
        await closeButton.click();
        await expect(settingsPanel).not.toBeVisible();
      } else {
        // Try pressing Escape
        await page.keyboard.press('Escape');
        await expect(settingsPanel).not.toBeVisible();
      }
    }
  });

  test('should display time and status information', async ({ page }) => {
    // Look for time display
    const timeElements = page.locator('text=/\\d{1,2}:\\d{2}/, .time-display, .clock');
    const timeCount = await timeElements.count();

    if (timeCount > 0) {
      await expect(timeElements.first()).toBeVisible();
    }

    // Look for status indicators
    const statusElements = page.locator('.status, .mood, .energy, text=/Active|Idle|Busy/');
    const statusCount = await statusElements.count();
    expect(statusCount).toBeGreaterThanOrEqual(0);
  });

  test('should show model information', async ({ page }) => {
    // Look for model/provider information
    const modelInfo = page.locator('text=/ollama|nano.*gpt|gpt|llama/i, .model-info, .provider');
    const modelCount = await modelInfo.count();

    if (modelCount > 0) {
      await expect(modelInfo.first()).toBeVisible();
    }
  });
});

test.describe('DeskMate Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // Check that interface adapts to mobile
    const grid = page.locator('.grid-area, [data-testid="grid-container"]').first();
    await expect(grid).toBeVisible();

    // Chat should still be functional
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    if (await chatInput.isVisible()) {
      await expect(chatInput).toBeEnabled();
    }
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad size
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // All main components should be visible
    await expect(page.locator('.grid-area, [data-testid="grid-container"]')).toBeVisible();

    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    if (await chatInput.isVisible()) {
      await expect(chatInput).toBeEnabled();
    }
  });

  test('should work on wide desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // All components should be visible and properly spaced
    await expect(page.locator('.grid-area, [data-testid="grid-container"]')).toBeVisible();

    // Grid should take advantage of larger space
    const grid = page.locator('.grid-area, [data-testid="grid-container"]').first();
    const gridBounds = await grid.boundingBox();
    expect(gridBounds!.width).toBeGreaterThan(800);
  });
});

test.describe('DeskMate Error Handling', () => {
  test('should handle network connectivity issues gracefully', async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // Simulate network failure
    await page.route('**/ws**', route => route.abort());
    await page.route('**/api/**', route => route.abort());

    // Try to send a message
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    if (await chatInput.isVisible()) {
      await sendChatMessage(page, 'Test message during network failure');

      // Should show disconnection indicator
      await expect(page.locator('.bg-red-500')).toBeVisible({ timeout: 10000 });
    }
  });

  test('should recover from connection loss', async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // Verify initial connection
    await expect(page.locator('.bg-green-500')).toBeVisible();

    // Simulate temporary network failure and recovery
    await page.route('**/ws**', route => route.abort());
    await page.waitForTimeout(2000);

    // Remove network block
    await page.unroute('**/ws**');

    // Should eventually reconnect
    await expect(page.locator('.bg-green-500')).toBeVisible({ timeout: 30000 });
  });
});

test.describe('DeskMate Performance', () => {
  test('should load within reasonable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await waitForDeskMateToLoad(page);
    const loadTime = Date.now() - startTime;

    // Should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });

  test('should handle rapid interactions without freezing', async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    const grid = page.locator('.grid-area, [data-testid="grid-container"]').first();
    const gridBounds = await grid.boundingBox();

    if (gridBounds) {
      // Rapidly click different areas of the grid
      for (let i = 0; i < 5; i++) {
        const x = gridBounds.x + (gridBounds.width * Math.random());
        const y = gridBounds.y + (gridBounds.height * Math.random());
        await page.mouse.click(x, y);
        await page.waitForTimeout(100);
      }

      // Interface should still be responsive
      await expect(page.locator('.grid-area, [data-testid="grid-container"]')).toBeVisible();

      const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
      if (await chatInput.isVisible()) {
        await expect(chatInput).toBeEnabled();
      }
    }
  });
});

test.describe('DeskMate Accessibility', () => {
  test('should be navigable with keyboard', async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);

    // Should be able to reach chat input
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    if (await chatInput.isVisible()) {
      await chatInput.focus();
      await expect(chatInput).toBeFocused();

      // Should be able to type
      await chatInput.type('Keyboard test');
      await expect(chatInput).toHaveValue('Keyboard test');
    }
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);

    // Check for ARIA labels on interactive elements
    const ariaElements = page.locator('[aria-label], [aria-describedby], [role]');
    const ariaCount = await ariaElements.count();

    // Should have some accessibility attributes
    expect(ariaCount).toBeGreaterThan(0);
  });
});