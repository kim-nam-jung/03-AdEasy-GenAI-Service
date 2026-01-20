export interface TaskResponse {
    task_id: string;
    status: string; // queued | processing | completed | failed
    message?: string;
    progress: number;
    current_step: number;
    output_path?: string;
    thumbnail_path?: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
    createTask: async (files: File[], prompt: string = ""): Promise<TaskResponse> => {
        const formData = new FormData();
        
        files.forEach((file) => {
            formData.append('files', file);
        });
        
        formData.append('prompt', prompt);

        const response = await fetch(`${API_URL}/api/v1/tasks/`, {
            method: 'POST',
            body: formData, // Content-Type header excluded (browser sets multipart/form-data boundary)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Error: ${response.statusText}`);
        }
        
        return response.json();
    },
    
    getTask: async (taskId: string): Promise<TaskResponse> => {
        const response = await fetch(`${API_URL}/api/v1/tasks/${taskId}`);
        if (!response.ok) {
            throw new Error(`Error: ${response.statusText}`);
        }
        return response.json();
    },

    debugAnalyzeStep1: async (file: File, prompt: string): Promise<any> => {
        const formData = new FormData();
        formData.append('files', file);
        formData.append('prompt', prompt);

        const response = await fetch(`${API_URL}/api/v1/debug/step1/analyze`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Error: ${response.statusText}`);
        }
        return response.json();
    },

    debugPlanStep2: async (file: File, analysisResult: any, prompt: string): Promise<any> => {
        const formData = new FormData();
        formData.append('files', file);
        formData.append('analysis_data', JSON.stringify(analysisResult));
        formData.append('prompt', prompt);

        const response = await fetch(`${API_URL}/api/v1/debug/step2/plan`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Error: ${response.statusText}`);
        }
        return response.json();
    }
};
