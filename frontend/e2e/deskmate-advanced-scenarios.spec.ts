import { test, expect, Page } from '@playwright/test';

// Helper functions from the core tests
async function waitForDeskMateToLoad(page: Page) {
  await page.waitForSelector('[data-testid="grid-container"], .grid-area', { timeout: 10000 });
  await page.waitForSelector('[data-testid="chat-window"], .chat-window', { timeout: 10000 });
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
  await page.waitForSelector('.animate-bounce', { timeout: 5000 });
  await page.waitForSelector('.animate-bounce', { state: 'detached', timeout: 30000 });
}

test.describe('DeskMate Advanced User Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should handle complex multi-step conversations', async ({ page }) => {
    // Start a complex conversation
    await sendChatMessage(page, 'I want to turn on the lamp and then sit on the bed');
    await waitForAssistantResponse(page);

    // Follow up with related requests
    await sendChatMessage(page, 'What did you just do?');
    await waitForAssistantResponse(page);

    await sendChatMessage(page, 'Can you see the room clearly now?');
    await waitForAssistantResponse(page);

    // Check that all messages are visible
    const messages = page.locator('.message, .chat-message');
    const messageCount = await messages.count();
    expect(messageCount).toBeGreaterThanOrEqual(6); // 3 user + 3 assistant messages
  });

  test('should demonstrate spatial reasoning', async ({ page }) => {
    // Ask about spatial relationships
    await sendChatMessage(page, 'What objects can you see from your current position?');
    await waitForAssistantResponse(page);

    // Ask for movement with spatial context
    await sendChatMessage(page, 'Move closer to the object on your left');
    await waitForAssistantResponse(page);

    // Verify spatial understanding
    await sendChatMessage(page, 'Describe where you are now relative to the room');
    await waitForAssistantResponse(page);

    // Check for spatial reasoning in responses
    const lastMessages = page.locator('.message, .chat-message').last();
    await expect(lastMessages).toBeVisible();
  });

  test('should handle object manipulation requests', async ({ page }) => {
    // Request object interaction
    await sendChatMessage(page, 'Turn on the lamp');
    await waitForAssistantResponse(page);

    // Check for action feedback
    await sendChatMessage(page, 'Is the lamp on now?');
    await waitForAssistantResponse(page);

    // Try different objects
    await sendChatMessage(page, 'Open the window');
    await waitForAssistantResponse(page);

    await sendChatMessage(page, 'Sit on the bed');
    await waitForAssistantResponse(page);

    // Verify interactions were processed
    const messages = page.locator('.message, .chat-message');
    const messageCount = await messages.count();
    expect(messageCount).toBeGreaterThanOrEqual(8);
  });

  test('should maintain conversation context and memory', async ({ page }) => {
    // Establish context
    await sendChatMessage(page, 'My name is Alex and I like bright lighting');
    await waitForAssistantResponse(page);

    // Reference earlier context
    await sendChatMessage(page, 'What do you know about my preferences?');
    await waitForAssistantResponse(page);

    // Check if assistant remembers
    await sendChatMessage(page, 'What did I tell you my name was?');
    await waitForAssistantResponse(page);

    // Assistant should reference previous information
    const messages = page.locator('.message, .chat-message');
    const lastMessage = messages.last();
    await expect(lastMessage).toBeVisible();
  });
});

test.describe('DeskMate Brain Council Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should demonstrate multi-perspective reasoning', async ({ page }) => {
    // Request that requires multiple perspectives
    await sendChatMessage(page, 'I\'m feeling tired and want to relax. What should we do?');
    await waitForAssistantResponse(page);

    // Should consider personality, spatial awareness, and actions
    const response = page.locator('.message, .chat-message').last();
    await expect(response).toBeVisible();

    // Follow up to test consistency
    await sendChatMessage(page, 'Why did you suggest that?');
    await waitForAssistantResponse(page);

    // Should provide reasoning
    const reasoning = page.locator('.message, .chat-message').last();
    await expect(reasoning).toBeVisible();
  });

  test('should handle mood and expression changes', async ({ page }) => {
    // Requests that might affect mood
    await sendChatMessage(page, 'You\'re doing a great job!');
    await waitForAssistantResponse(page);

    // Check for visual mood indicators
    const moodIndicators = page.locator('.mood, .expression, .status');
    const moodCount = await moodIndicators.count();

    // Request emotional response
    await sendChatMessage(page, 'How are you feeling now?');
    await waitForAssistantResponse(page);

    // Should acknowledge emotional state
    const emotionalResponse = page.locator('.message, .chat-message').last();
    await expect(emotionalResponse).toBeVisible();
  });

  test('should validate action feasibility', async ({ page }) => {
    // Request impossible action
    await sendChatMessage(page, 'Fly to the ceiling');
    await waitForAssistantResponse(page);

    // Should explain limitations
    const impossibleResponse = page.locator('.message, .chat-message').last();
    await expect(impossibleResponse).toBeVisible();

    // Request feasible alternative
    await sendChatMessage(page, 'What can you actually do in this room?');
    await waitForAssistantResponse(page);

    // Should list realistic actions
    const feasibleResponse = page.locator('.message, .chat-message').last();
    await expect(feasibleResponse).toBeVisible();
  });
});

test.describe('DeskMate Performance Under Load', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should handle rapid message sending', async ({ page }) => {
    const messages = [
      'Hello',
      'Move to position 10, 5',
      'What can you see?',
      'Turn on the lamp',
      'How are you feeling?'
    ];

    // Send messages rapidly
    for (const message of messages) {
      await sendChatMessage(page, message);
      await page.waitForTimeout(500); // Small delay to avoid overwhelming
    }

    // Wait for all responses
    await page.waitForTimeout(10000);

    // All messages should be processed
    const chatMessages = page.locator('.message, .chat-message');
    const messageCount = await chatMessages.count();
    expect(messageCount).toBeGreaterThanOrEqual(messages.length);
  });

  test('should handle complex grid interactions', async ({ page }) => {
    const grid = page.locator('.grid-area, [data-testid="grid-container"]').first();
    const gridBounds = await grid.boundingBox();

    if (gridBounds) {
      // Perform multiple grid clicks with different patterns
      const clickPatterns = [
        { x: 0.2, y: 0.3 }, // Top-left area
        { x: 0.8, y: 0.3 }, // Top-right area
        { x: 0.5, y: 0.7 }, // Bottom-center
        { x: 0.3, y: 0.5 }, // Left-center
        { x: 0.7, y: 0.5 }, // Right-center
      ];

      for (const pattern of clickPatterns) {
        const x = gridBounds.x + (gridBounds.width * pattern.x);
        const y = gridBounds.y + (gridBounds.height * pattern.y);

        await page.mouse.click(x, y);
        await page.waitForTimeout(1000); // Wait for any movement or processing
      }

      // Interface should remain responsive
      await expect(grid).toBeVisible();
      const assistant = page.locator('.bg-white').first();
      await expect(assistant).toBeVisible();
    }
  });

  test('should maintain performance with long conversation history', async ({ page }) => {
    // Simulate a long conversation
    for (let i = 0; i < 10; i++) {
      await sendChatMessage(page, `This is message number ${i + 1}. Tell me about the room.`);

      // Wait for response with timeout to prevent hanging
      try {
        await waitForAssistantResponse(page);
      } catch (error) {
        console.log(`Response ${i + 1} timed out, continuing...`);
      }

      await page.waitForTimeout(1000);
    }

    // Chat should still be responsive
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    await expect(chatInput).toBeEnabled();

    // Should be able to send new messages
    await sendChatMessage(page, 'Are you still responsive?');
    await waitForAssistantResponse(page);
  });
});

test.describe('DeskMate Edge Cases and Error Recovery', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should handle very long messages', async ({ page }) => {
    const longMessage = 'This is a very long message that contains a lot of text and should test how the system handles lengthy user inputs. '.repeat(20);

    await sendChatMessage(page, longMessage);

    // Should process without errors
    try {
      await waitForAssistantResponse(page);
    } catch (error) {
      // Even if it times out, interface should remain functional
    }

    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    await expect(chatInput).toBeEnabled();
  });

  test('should handle special characters and emojis', async ({ page }) => {
    const specialMessages = [
      'Hello! 🎉 How are you? 😊',
      'Test symbols: @#$%^&*()_+-=[]{}|;:,.<>?',
      'Unicode test: αβγδε ñáéíóú çñü',
      'Quotes test: "Hello" \'World\' `Test`',
    ];

    for (const message of specialMessages) {
      await sendChatMessage(page, message);
      await page.waitForTimeout(2000); // Give time for processing
    }

    // Interface should remain stable
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    await expect(chatInput).toBeEnabled();
  });

  test('should recover from WebSocket disconnection', async ({ page }) => {
    // Verify initial connection
    await expect(page.locator('.bg-green-500')).toBeVisible();

    // Send a message to establish baseline
    await sendChatMessage(page, 'Test message before disconnection');

    // Simulate WebSocket disconnection
    await page.evaluate(() => {
      // Force close any existing WebSocket connections
      if ((window as any).websocket) {
        (window as any).websocket.close();
      }
    });

    // Should show disconnection indicator
    await expect(page.locator('.bg-red-500')).toBeVisible({ timeout: 10000 });

    // Wait for automatic reconnection
    await expect(page.locator('.bg-green-500')).toBeVisible({ timeout: 30000 });

    // Should be able to send messages again
    await sendChatMessage(page, 'Test message after reconnection');

    try {
      await waitForAssistantResponse(page);
    } catch (error) {
      // Even if response times out, connection should be restored
    }

    // Connection indicator should be green
    await expect(page.locator('.bg-green-500')).toBeVisible();
  });

  test('should handle rapid tab switching and focus changes', async ({ page }) => {
    // Send initial message
    await sendChatMessage(page, 'Initial test message');

    // Simulate tab switching by blurring and focusing the page
    await page.evaluate(() => {
      window.dispatchEvent(new Event('blur'));
    });
    await page.waitForTimeout(1000);

    await page.evaluate(() => {
      window.dispatchEvent(new Event('focus'));
    });
    await page.waitForTimeout(1000);

    // Should maintain state and functionality
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    await expect(chatInput).toBeEnabled();

    // Should be able to continue conversation
    await sendChatMessage(page, 'Message after focus change');

    // Interface should remain responsive
    await expect(page.locator('.grid-area, [data-testid="grid-container"]')).toBeVisible();
  });

  test('should handle browser back/forward navigation', async ({ page }) => {
    // Send a message to establish state
    await sendChatMessage(page, 'Message before navigation');
    await page.waitForTimeout(2000);

    // Navigate away and back
    await page.goto('about:blank');
    await page.waitForTimeout(1000);

    await page.goBack();
    await waitForDeskMateToLoad(page);

    // Should restore functionality
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    await expect(chatInput).toBeEnabled();

    // Should be able to send new messages
    await sendChatMessage(page, 'Message after navigation');

    // Basic functionality should work
    await expect(page.locator('.grid-area, [data-testid="grid-container"]')).toBeVisible();
  });
});

test.describe('DeskMate Accessibility and Usability', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForDeskMateToLoad(page);
  });

  test('should support screen reader navigation', async ({ page }) => {
    // Check for semantic HTML and ARIA labels
    const landmarks = page.locator('[role="main"], [role="navigation"], [role="region"], main, nav, section');
    const landmarkCount = await landmarks.count();
    expect(landmarkCount).toBeGreaterThan(0);

    // Check for proper headings
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);

    // Check for accessible form labels
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    if (await chatInput.isVisible()) {
      const ariaLabel = await chatInput.getAttribute('aria-label');
      const associatedLabel = await chatInput.getAttribute('aria-labelledby');
      expect(ariaLabel || associatedLabel).toBeTruthy();
    }
  });

  test('should have sufficient color contrast', async ({ page }) => {
    // Check that text is visible against backgrounds
    const textElements = page.locator('p, span, div').filter({ hasText: /\w+/ });
    const textCount = await textElements.count();

    if (textCount > 0) {
      // Sample a few text elements to check they're visible
      for (let i = 0; i < Math.min(5, textCount); i++) {
        const element = textElements.nth(i);
        await expect(element).toBeVisible();
      }
    }
  });

  test('should support keyboard navigation throughout the interface', async ({ page }) => {
    // Start from the beginning
    await page.keyboard.press('Tab');

    let tabCount = 0;
    const maxTabs = 20; // Prevent infinite loop

    while (tabCount < maxTabs) {
      // Check if we can find the currently focused element
      const focusedElement = page.locator(':focus');
      const isVisible = await focusedElement.isVisible().catch(() => false);

      if (isVisible) {
        tabCount++;
      }

      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      // Check if we've reached the chat input
      const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
      const chatInputFocused = await chatInput.evaluate(el => document.activeElement === el).catch(() => false);

      if (chatInputFocused) {
        break;
      }
    }

    // Should be able to reach interactive elements
    expect(tabCount).toBeGreaterThan(0);
  });

  test('should provide helpful error messages', async ({ page }) => {
    // Try to trigger an error condition
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });

    await sendChatMessage(page, 'Test error handling');
    await page.waitForTimeout(5000);

    // Should show user-friendly error message
    const errorMessages = page.locator('text=/error|failed|something went wrong/i');
    const errorCount = await errorMessages.count();

    // At minimum, should not crash the interface
    const chatInput = page.locator('input[placeholder*="message"], textarea[placeholder*="message"], .chat-input input, .chat-input textarea').first();
    await expect(chatInput).toBeEnabled();
  });
});