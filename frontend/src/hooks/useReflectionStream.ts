import { useState, useEffect, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Convert http(s) to ws(s)
const getWsUrl = (url: string) => {
    if (url.startsWith('https')) {
        return url.replace('https://', 'wss://');
    }
    return url.replace('http://', 'ws://');
};

const WS_BASE_URL = getWsUrl(API_URL);

export interface ReflectionLog {
    id: number;
    content: string;
    isComplete: boolean;
    timestamp: string;
}

export function useReflectionStream(taskId: string | null) {
    const [logs, setLogs] = useState<ReflectionLog[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    
    // Buffer for the current streaming thought
    const currentThoughtRef = useRef<string>("");

    useEffect(() => {
        if (!taskId) return;

        // Reset logs on new task
        setLogs([]);
        currentThoughtRef.current = "";
        
        const wsUrl = `${WS_BASE_URL}/ws/task/${taskId}`;
        console.log(`Connecting to WS: ${wsUrl}`);
        
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log("WS Connected");
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'token') {
                    currentThoughtRef.current += data.content;
                    
                    // Update the last log entry or create new one if none exists
                    setLogs(prev => {
                        const newLogs = [...prev];
                        if (newLogs.length === 0 || newLogs[newLogs.length - 1].isComplete) {
                            // Start new log entry
                            newLogs.push({
                                id: Date.now(),
                                content: currentThoughtRef.current,
                                isComplete: false,
                                timestamp: new Date().toLocaleTimeString()
                            });
                        } else {
                            // Update existing
                            newLogs[newLogs.length - 1].content = currentThoughtRef.current;
                        }
                        return newLogs;
                    });
                } else if (data.type === 'end') {
                    // Mark last log as complete
                     setLogs(prev => {
                        if (prev.length === 0) return prev;
                        const newLogs = [...prev];
                        newLogs[newLogs.length - 1].isComplete = true;
                        return newLogs;
                    });
                    currentThoughtRef.current = ""; // Reset buffer for next thought
                }
            } catch (e) {
                console.error("WS Parse Error", e);
            }
        };

        ws.onerror = (err) => {
            console.error("WS Error", err);
            setIsConnected(false);
        };

        ws.onclose = () => {
            console.log("WS Closed");
            setIsConnected(false);
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [taskId]);

    return { logs, isConnected };
}
