import { useState, useRef, useCallback } from 'react';
import { useWebSocketManager } from './useWebSocketManager';
import { TaskEvent } from '../types/websocket';

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
    const logIdRef = useRef<number>(0);
    const currentThoughtRef = useRef<string>("");
    const [awaitingInput, setAwaitingInput] = useState(false);
    const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);

    const handleMessage = useCallback((msgData: TaskEvent) => {
        // Handle token streaming
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
                        taskId: taskId || undefined
                    });
                }
                return newLogs;
            });
            return;
        }

        // Handle other structured events
        if (msgData.type === 'end') {
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
                taskId: taskId || undefined
            }]);
        } else if (msgData.type === 'tool_call') {
            // If there's a log message, show it as a thought bubble first
            if (msgData.log && msgData.log.trim()) {
                setLogs(prev => [...prev, {
                    id: ++logIdRef.current,
                    type: 'thought',
                    content: msgData.log,
                    isComplete: true,
                    timestamp: new Date().toLocaleTimeString(),
                    taskId: taskId || undefined
                }]);
            }
            
            setLogs(prev => [...prev, {
                id: ++logIdRef.current,
                type: 'tool_call',
                content: msgData.log || `Calling ${msgData.tool}...`,
                metadata: { tool: msgData.tool, input: msgData.tool_input },
                isComplete: true,
                timestamp: new Date().toLocaleTimeString(),
                taskId: taskId || undefined
            }]);
        } else if (msgData.type === 'tool_result') {
            setLogs(prev => [...prev, {
                id: ++logIdRef.current,
                type: 'tool_result',
                content: msgData.output,
                isComplete: true,
                timestamp: new Date().toLocaleTimeString(),
                taskId: taskId || undefined
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
                    taskId: taskId || undefined,
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
                taskId: taskId || undefined
            }]);
        } else if (msgData.type === 'human_input_request') {
            setAwaitingInput(true);
            setPendingQuestion(msgData.question || "추가 지침이 필요합니다");
            
            // Inject a visible log for the chat
            setLogs(prev => [...prev, {
                id: ++logIdRef.current,
                type: 'thought',
                content: msgData.question || "작업을 중단하고 사용자의 승인을 기다립니다.",
                isComplete: true,
                timestamp: new Date().toLocaleTimeString(),
                taskId: taskId || undefined,
                metadata: { is_human_request: true }
            }]);
        } else if (msgData.type === 'human_input_received') {
            setAwaitingInput(false);
            setPendingQuestion(null);
            setLogs(prev => {
                const newLogs = [...prev];
                const lastPlan = [...newLogs].reverse().find(l => l.status === 'planning_proposed');
                if (lastPlan) {
                    lastPlan.status = 'planning_completed';
                }
                return newLogs;
            });
        }
    }, [taskId]);

    const { isConnected } = useWebSocketManager(
        taskId ? `/ws/${taskId}` : null,
        handleMessage
    );

    return { logs, isConnected, awaitingInput, pendingQuestion };
}
