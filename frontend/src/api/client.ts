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
const API_KEY = import.meta.env.VITE_API_KEY || 'adeasy-secret-key';

const getHeaders = (isJson: boolean = true) => {
    const headers: Record<string, string> = {
        'X-API-Key': API_KEY,
    };
    if (isJson) {
        headers['Content-Type'] = 'application/json';
    }
    return headers;
};

export const api = {
    createTask: async (files: File[], prompt: string = ""): Promise<TaskResponse> => {
        const formData = new FormData();
        
        files.forEach((file) => {
            formData.append('files', file);
        });
        
        formData.append('prompt', prompt);

        const response = await fetch(`${API_URL}/api/v1/tasks/`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
            },
            body: formData,
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Error: ${response.statusText}`);
        }
        
        return response.json();
    },
    
    getTask: async (taskId: string): Promise<TaskResponse> => {
        const response = await fetch(`${API_URL}/api/v1/tasks/${taskId}`, {
            headers: getHeaders(false),
        });

    debugStep1Segmentation: async (file: File, numLayers: number, resolution: number): Promise<any> => {
        const formData = new FormData();
        formData.append('files', file);
        formData.append('num_layers', numLayers.toString());
        formData.append('resolution', resolution.toString());

        const response = await fetch(`${API_URL}/api/v1/debug/step1/segmentation`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Error: ${response.statusText}`);
        }
        return response.json();
    },

    debugStep2VideoGeneration: async (imagePath: string, prompt: string, numFrames: number): Promise<any> => {
        const formData = new FormData();
        formData.append('main_product_layer', imagePath);
        formData.append('prompt', prompt);
        formData.append('num_frames', numFrames.toString());

        const response = await fetch(`${API_URL}/api/v1/debug/step2/video_generation`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Error: ${response.statusText}`);
        }
        return response.json();
    },

    debugStep3Postprocess: async (videoPath: string, rifeEnabled: boolean, cuganEnabled: boolean): Promise<any> => {
        const formData = new FormData();
        formData.append('raw_video_path', videoPath);
        formData.append('rife_enabled', rifeEnabled.toString());
        formData.append('cugan_enabled', cuganEnabled.toString());

        const response = await fetch(`${API_URL}/api/v1/debug/step3/postprocess`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY,
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Error: ${response.statusText}`);
        }
        return response.json();
    },

    debugCleanup: async (): Promise<any> => {
        const response = await fetch(`${API_URL}/api/v1/debug/cleanup`, {
            method: 'POST',
            headers: getHeaders(false),
        });
        if (!response.ok) {
            throw new Error(`Error: ${response.statusText}`);
        }
        return response.json();
    }
};
