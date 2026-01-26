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
    type: 'thought' | 'tool_call' | 'tool_result';
    content: string;
    isComplete: boolean;
    timestamp: string;
    metadata?: any;
}

export function useReflectionStream(taskId: string | null) {
    const [logs, setLogs] = useState<ReflectionLog[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const nextSeqRef = useRef<number>(1);
    const bufferRef = useRef<Map<number, any>>(new Map());
    
    // Buffer for the current streaming thought/token stream
    const currentThoughtRef = useRef<string>("");

    useEffect(() => {
        if (!taskId) return;

        // Reset state on new task
        setLogs([]);
        currentThoughtRef.current = "";
        nextSeqRef.current = 1;
        bufferRef.current.clear();
        
        const wsUrl = `${WS_BASE_URL}/ws/${taskId}`;
        console.log(`Connecting to Reflection Stream: ${wsUrl}`);
        
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        const processMessage = (msgData: any) => {
            if (msgData.type === 'token') {
                currentThoughtRef.current += msgData.content;
                
                setLogs(prev => {
                    const newLogs = [...prev];
                    if (newLogs.length > 0 && newLogs[newLogs.length - 1].type === 'thought' && !newLogs[newLogs.length - 1].isComplete) {
                        newLogs[newLogs.length - 1].content = currentThoughtRef.current;
                    } else {
                        newLogs.push({
                            id: Date.now(),
                            type: 'thought',
                            content: currentThoughtRef.current,
                            isComplete: false,
                            timestamp: new Date().toLocaleTimeString()
                        });
                    }
                    return newLogs;
                });
            } else if (msgData.type === 'end') {
                 setLogs(prev => {
                    if (prev.length === 0) return prev;
                    const newLogs = [...prev];
                    if (newLogs[newLogs.length - 1].type === 'thought') {
                        newLogs[newLogs.length - 1].isComplete = true;
                    }
                    return newLogs;
                });
                currentThoughtRef.current = ""; 
            } else if (msgData.type === 'thought') {
                setLogs(prev => [...prev, {
                    id: Date.now(),
                    type: 'thought',
                    content: msgData.message,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString()
                }]);
            } else if (msgData.type === 'tool_call') {
                setLogs(prev => [...prev, {
                    id: Date.now(),
                    type: 'tool_call',
                    content: msgData.log || `Calling ${msgData.tool}...`,
                    metadata: { tool: msgData.tool, input: msgData.tool_input },
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString()
                }]);
            } else if (msgData.type === 'tool_result') {
                setLogs(prev => [...prev, {
                    id: Date.now(),
                    type: 'tool_result',
                    content: msgData.output,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString()
                }]);
            } else if (msgData.type === 'log') {
                setLogs(prev => [...prev, {
                    id: Date.now(),
                    type: 'thought',
                    content: msgData.message,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString()
                }]);
            }
        };

        const handleSequencedMessages = () => {
            while (bufferRef.current.has(nextSeqRef.current)) {
                const data = bufferRef.current.get(nextSeqRef.current);
                bufferRef.current.delete(nextSeqRef.current);
                processMessage(data);
                nextSeqRef.current++;
            }
        };

        ws.onopen = () => {
            console.log("Reflection WS Connected");
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const envelope = JSON.parse(event.data);
                
                // Handle Heartbeat
                if (envelope.type === 'ping') return;

                // Handle legacy or non-sequenced messages
                if (envelope.seq === undefined) {
                    processMessage(envelope);
                    return;
                }

                // Buffer sequenced messages
                bufferRef.current.set(envelope.seq, envelope.data);
                handleSequencedMessages();
                
            } catch (e) {
                console.error("WS Message Error", e);
            }
        };

        ws.onerror = (err) => {
            console.error("Reflection WS Error", err);
            setIsConnected(false);
        };

        ws.onclose = () => {
            console.log("Reflection WS Closed");
            setIsConnected(false);
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
            wsRef.current = null;
        };
    }, [taskId]);

    return { logs, isConnected };
}
