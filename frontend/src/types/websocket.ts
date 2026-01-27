export interface StatusUpdate {
    status: string;
    progress?: number;
    message?: string;
    result?: {
        segmented_layers?: string[];
        main_product_layer?: string;
        video_path?: string;
        thumbnail_path?: string;
    };
}

// WebSocket Envelope (the raw message from server)
export interface WSEnvelope {
    seq?: number;
    type?: string; 
    data?: any;
    // Legacy support (non-enveloped messages)
    [key: string]: any;
}

// Task Event (the 'data' inside the envelope)
export type TaskEvent = 
    | { type: 'log'; level: string; message: string }
    | { type: 'progress'; value: number; status?: string }
    | { type: 'status'; status: string; data?: any }
    | { type: 'human_input_request'; question?: string; context?: string }
    | { type: 'human_input_received'; feedback?: string }
    | { type: 'error'; message: string }
    | { type: 'ping'; timestamp: number };
