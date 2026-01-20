import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../api/client';

describe('API Client', () => {
    beforeEach(() => {
        vi.stubGlobal('fetch', vi.fn());
    });

    it('createTask sends FormData and returns JSON', async () => {
        const mockResponse = { task_id: '123', status: 'queued', progress: 0, current_step: 0 };
        (fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockResponse
        });

        const files = [new File([''], 'test.jpg', { type: 'image/jpeg' })];
        const result = await api.createTask(files, 'test prompt');

        expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/tasks/'), expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData)
        }));
        expect(result).toEqual(mockResponse);
    });

    it('getTask fetches task status', async () => {
        const mockResponse = { task_id: '123', status: 'processing', progress: 50, current_step: 1 };
        (fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockResponse
        });

        const result = await api.getTask('123');
        expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/tasks/123'));
        expect(result).toEqual(mockResponse);
    });

    it('throws error when response is not ok', async () => {
        (fetch as any).mockResolvedValue({
            ok: false,
            statusText: 'Internal Server Error',
            json: async () => ({ detail: 'Something went wrong' })
        });

        await expect(api.getTask('fail')).rejects.toThrow('Error: Internal Server Error');
    });

    it('debugAnalyzeStep1 sends file and prompt', async () => {
        const mockResponse = { result: 'ok' };
        (fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockResponse
        });

        const file = new File([''], 'test.jpg');
        const result = await api.debugAnalyzeStep1(file, 'test prompt');

        expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/debug/step1/analyze'), expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData)
        }));
        expect(result).toEqual(mockResponse);
    });

    it('debugPlanStep2 sends file, data and prompt', async () => {
        const mockResponse = { result: 'ok' };
        (fetch as any).mockResolvedValue({
            ok: true,
            json: async () => mockResponse
        });

        const file = new File([''], 'test.jpg');
        const result = await api.debugPlanStep2(file, { info: 'test' }, 'test prompt');

        expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/debug/step2/plan'), expect.objectContaining({
            method: 'POST',
            body: expect.any(FormData)
        }));
        expect(result).toEqual(mockResponse);
    });
});
