import { test, expect } from '@playwright/test';

test.describe('Agent Pipeline', () => {
    test('full agent flow with mock WS', async ({ page }) => {
        page.on('console', msg => console.log(`[Browser] ${msg.text()}`));
        await page.addInitScript(() => {
            class MockWebSocket {
                onopen: any;
                onmessage: any;
                onclose: any;
                onerror: any;
                url: string;
                
                constructor(url: string) {
                    this.url = url;
                    setTimeout(() => {
                        this.onopen && this.onopen();
                        this.emitSequence();
                    }, 100);
                }

                emitSequence() {
                     const send = (data: any) => {
                         if (this.onmessage) this.onmessage({ data: JSON.stringify(data) });
                     };
                     
                     setTimeout(() => send({ type: 'log', level: 'Agent', message: 'Analyzing image...' }), 200);
                     setTimeout(() => send({ 
                         type: 'status', 
                         status: 'vision_completed', 
                         data: { product_name: 'Hero Shoe', visual_characteristics: ['Red', 'Sporty'] } 
                     }), 1000);
                     
                     setTimeout(() => send({ 
                         type: 'status', 
                         status: 'step1_completed', 
                         data: { segmented_layers: ['/mock/layer0.png'] } 
                     }), 1500);
                     
                     setTimeout(() => send({ 
                         type: 'status', 
                         status: 'completed', 
                         data: { video_path: 'https://example.com/video.mp4', thumbnail_path: '' } 
                     }), 2000);
                }
                
                close() {}
                send() {}
            }
            (window as any).WebSocket = MockWebSocket;
        });

        // Mock API
        await page.route('*/**/api/v1/tasks/', async route => {
             await route.fulfill({ json: { task_id: 'mock-123' } });
        });

        await page.goto('/');

        // Navigate to Pipeline Lab view
        await page.click('text=Pipeline Lab');

        // Upload - use the file input directly
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles({
             name: 'shoe.png',
             mimeType: 'image/png',
             buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64')
        });

        // Wait for preview to appear (aspect-square is the preview container)
        await expect(page.locator('.aspect-square')).toHaveCount(1, { timeout: 5000 });

        // Wait for button to be enabled and click
        const startBtn = page.getByRole('button', { name: 'Start Agent Task' });
        await expect(startBtn).toBeEnabled({ timeout: 10000 });
        await startBtn.click();
        
        // Assertions - check logs tab content
        await expect(page.locator('text=Task Initialized: mock-123')).toBeVisible({ timeout: 5000 }); // From API
        await expect(page.locator('text=Analyzing image...')).toBeVisible({ timeout: 5000 }); // From WS

        // Wait for status to show completed
        await expect(page.locator('text=completed')).toBeVisible({ timeout: 5000 });

        // Click result tab to see final output
        await page.getByRole('button', { name: 'result' }).click();
        await expect(page.locator('text=Final Output')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('text=Task Completed Successfully')).toBeVisible();
    });
});
