import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_BASE_URL } from '../api/config';
import { WSEnvelope } from '../types/websocket';

type MessageHandler = (data: any) => void;

interface UseWebSocketManagerOptions {
    baseUrl?: string;
    onOpen?: () => void;
    onClose?: () => void;
    onError?: (error: Event) => void;
}

export function useWebSocketManager(
    endpoint: string | null, 
    onMessage: MessageHandler,
    options: UseWebSocketManagerOptions = {}
) {
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    
    // Sequencing State
    const nextSeqRef = useRef<number>(1);
    const bufferRef = useRef<Map<number, any>>(new Map());

    // Reset sequence state
    const resetSequence = useCallback(() => {
        nextSeqRef.current = 1;
        bufferRef.current.clear();
    }, []);

    const processMessage = useCallback((data: any) => {
        onMessage(data);
    }, [onMessage]);

    const drainBuffer = useCallback(() => {
        while (bufferRef.current.has(nextSeqRef.current)) {
            const data = bufferRef.current.get(nextSeqRef.current);
            bufferRef.current.delete(nextSeqRef.current);
            processMessage(data);
            nextSeqRef.current++;
        }
    }, [processMessage]);

    useEffect(() => {
        if (!endpoint) return;

        resetSequence();
        
        const baseUrl = options.baseUrl || WS_BASE_URL;
        const wsUrl = `${baseUrl}${endpoint}`;
        
        console.log(`[WS Manager] Connecting to: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log(`[WS Manager] Connected: ${endpoint}`);
            setIsConnected(true);
            options.onOpen?.();
        };

        ws.onmessage = (event) => {
            try {
                const envelope: WSEnvelope = JSON.parse(event.data);
                
                if (envelope.type === 'ping') return;

                // Handle Sequence
                if (envelope.seq !== undefined) {
                    bufferRef.current.set(envelope.seq, envelope.data);
                    drainBuffer();
                } else {
                    // Legacy or direct message
                    processMessage(envelope);
                }
            } catch (e) {
                console.error("[WS Manager] Parse Error", e);
            }
        };

        ws.onclose = () => {
             console.log(`[WS Manager] Disconnected: ${endpoint}`);
             setIsConnected(false);
             options.onClose?.();
        };

        ws.onerror = (e) => {
            console.error(`[WS Manager] Error`, e);
            options.onError?.(e);
        };

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
            wsRef.current = null;
        };
    }, [endpoint, options.baseUrl, resetSequence, drainBuffer, processMessage]);

    return { isConnected, ws: wsRef.current };
}
