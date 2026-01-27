import { test, expect } from '@playwright/test';

test.describe('Agent Pipeline', () => {
    test('full agent flow with mock WS', async ({ page }) => {
        page.on('console', msg => console.log(`[Browser] ${msg.text()}`));
        
        // Mock WebSocket before page load
        await page.addInitScript(() => {
            const OriginalWebSocket = window.WebSocket;
            class MockWebSocket {
                onopen: any;
                onmessage: any;
                onclose: any;
                onerror: any;
                url: string;
                
                private listeners: Record<string, Function[]> = {};

                constructor(url: string) {
                    this.url = url;
                    // Only intercept task WS, let others (Vite HMR) pass through
                    if (url.includes('/ws/')) {
                        console.log(`[MockWS] Intercepting: ${url}`);
                        setTimeout(() => {
                            const ev = { type: 'open' };
                            if (this.onopen) this.onopen(ev);
                            this.dispatchEvent('open', ev);
                            this.emitSequence();
                        }, 100);
                    } else {
                        // Support for Vite HMR and other system WS
                        return new OriginalWebSocket(url) as any;
                    }
                }

                addEventListener(type: string, listener: Function) {
                    if (!this.listeners[type]) this.listeners[type] = [];
                    this.listeners[type].push(listener);
                }

                removeEventListener(type: string, listener: Function) {
                    if (!this.listeners[type]) return;
                    this.listeners[type] = this.listeners[type].filter(l => l !== listener);
                }

                private dispatchEvent(type: string, data: any) {
                    if (this.listeners[type]) {
                        this.listeners[type].forEach(l => l(data));
                    }
                }

                emitSequence() {
                     let seq = 0;
                     const send = (data: any) => {
                         seq++;
                         const envelope = { seq, data };
                         const ev = { data: JSON.stringify(envelope) };
                         if (this.onmessage) this.onmessage(ev);
                         this.dispatchEvent('message', ev);
                     };
                     
                     setTimeout(() => send({ type: 'log', level: 'Agent', message: 'Analyzing image...' }), 200);
                     setTimeout(() => send({ 
                         type: 'status', 
                         status: 'vision_completed', 
                         data: { product_name: 'Hero Shoe', visual_characteristics: ['Red', 'Sporty'] } 
                     }), 1000);
                     
                     // Mock planning_tool result to match new pipeline
                     setTimeout(() => send({
                         type: 'tool_result',
                         content: JSON.stringify({
                             steps: ["Analyze visuals", "Generate motion plan", "Execute video generation"],
                             rationale: "Highlighting sporty aesthetics"
                         })
                     }), 1200);
                     
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

        // Wait for preview to appear
        await expect(page.locator('.aspect-square')).toHaveCount(1, { timeout: 5000 });

        // Wait for button to be enabled and click
        const startBtn = page.getByRole('button', { name: 'Start Agent Task' });
        await expect(startBtn).toBeEnabled({ timeout: 10000 });
        await startBtn.click();
        
        // Assertions
        await expect(page.locator('text=Task Initialized: mock-123')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('text=Analyzing image...')).toBeVisible({ timeout: 5000 });

        // Wait a bit for connection to settle before emitting
        await page.waitForTimeout(1000);

        // --- Emit Planning Result (Seq 2) ---
        await page.evaluate(() => {
            if (window.wsMock) {
                window.wsMock.dispatchEvent(new MessageEvent('message', { 
                    data: JSON.stringify({ 
                        seq: 2, 
                        data: { 
                            type: 'status',
                            status: 'planning_proposed',
                            data: { 
                                steps: ['Analyze visuals', 'Segment product', 'Generate video'], 
                                rationale: 'I will analyze the visuals first...' 
                            } 
                        } 
                    }) 
                }));
            }
        });

        // Wait for planning result card - Increase timeout for CI stability
        await expect(page.locator('text=Strategy Plan')).toBeVisible({ timeout: 15000 });
        await expect(page.locator('text=Analyze visuals')).toBeVisible({ timeout: 15000 });
        
        // --- NEW: Handle Human-in-the-Loop Approval in Test ---
        const approveBtn = page.getByRole('button', { name: 'Approve & Start' });
        await expect(approveBtn).toBeVisible();
        
        // Mock feedback API
        await page.route('**/api/v1/tasks/**/feedback', async route => {
            await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: "received" }) });
        });

        await approveBtn.click();

        // Emit final completion event after approval
        await page.evaluate(() => {
            if (window.wsMock) {
                window.wsMock.dispatchEvent(new MessageEvent('message', { 
                    data: JSON.stringify({ seq: 3, data: { type: 'status', status: 'completed', data: { video_path: '/outputs/test.mp4', thumbnail_path: '/outputs/thumb.jpg' } } }) 
                }));
            }
        });

        // Wait for final completion indicators
        await expect(page.locator('text=Final Masterpiece')).toBeVisible({ timeout: 10000 });
        await expect(page.locator('text=Pipeline Completed Successfully!')).toBeVisible();
    });
});
