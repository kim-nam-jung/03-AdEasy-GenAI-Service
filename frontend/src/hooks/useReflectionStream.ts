import { useState, useEffect, useRef } from 'react';

import { WS_BASE_URL } from '../api/config';

export interface ReflectionLog {
    id: number;
    type: 'thought' | 'tool_call' | 'tool_result';
    content: string;
    isComplete: boolean;
    timestamp: string;
    metadata?: any;
    status?: string;
    taskId?: string;
}

export function useReflectionStream(taskId: string | null) {
    const [logs, setLogs] = useState<ReflectionLog[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const nextSeqRef = useRef<number>(1);
    const bufferRef = useRef<Map<number, any>>(new Map());
    const logIdRef = useRef<number>(0);
    
    // Buffer for the current streaming thought/token stream
    const currentThoughtRef = useRef<string>("");

    useEffect(() => {
        if (!taskId) return;

        // Reset state on new task
        setLogs([]);
        currentThoughtRef.current = "";
        nextSeqRef.current = 1;
        bufferRef.current.clear();
        logIdRef.current = 0;
        
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
                            id: ++logIdRef.current,
                            type: 'thought',
                            content: currentThoughtRef.current,
                            isComplete: false,
                            timestamp: new Date().toLocaleTimeString(),
                            taskId
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
                    id: ++logIdRef.current,
                    type: 'thought',
                    content: msgData.message,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString(),
                    taskId
                }]);
            } else if (msgData.type === 'tool_call') {
                setLogs(prev => [...prev, {
                    id: ++logIdRef.current,
                    type: 'tool_call',
                    content: msgData.log || `Calling ${msgData.tool}...`,
                    metadata: { tool: msgData.tool, input: msgData.tool_input },
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString(),
                    taskId
                }]);
            } else if (msgData.type === 'tool_result') {
                setLogs(prev => [...prev, {
                    id: ++logIdRef.current,
                    type: 'tool_result',
                    content: msgData.output,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString(),
                    taskId
                }]);
            } else if (msgData.type === 'status') {
                // Treat status updates with data as tool results so they appear in chat
                if (msgData.data) {
                    setLogs(prev => [...prev, {
                        id: ++logIdRef.current,
                        type: 'tool_result',
                        content: typeof msgData.data === 'string' ? msgData.data : JSON.stringify(msgData.data),
                        isComplete: true,
                        timestamp: new Date().toLocaleTimeString(),
                        status: msgData.status,
                        taskId,
                        metadata: { status: msgData.status, is_final: msgData.status === 'completed' }
                    }]);
                }
            } else if (msgData.type === 'log') {
                setLogs(prev => [...prev, {
                    id: ++logIdRef.current,
                    type: 'thought',
                    content: msgData.message,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString(),
                    taskId
                }]);
            } else if (msgData.type === 'human_input_received') {
                // If the user submits feedback, we might want to update the last 'planning_proposed' entry's status
                setLogs(prev => {
                    const newLogs = [...prev];
                    const lastPlan = [...newLogs].reverse().find(l => l.status === 'planning_proposed');
                    if (lastPlan) {
                        lastPlan.status = 'planning_completed';
                    }
                    return newLogs;
                });
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
