import React, { useEffect, useRef } from 'react';
import { useReflectionStream } from '../hooks/useReflectionStream';

interface ReflectionLogProps {
    taskId: string;
}

export const ReflectionLog: React.FC<ReflectionLogProps> = ({ taskId }) => {
    const { logs, isConnected } = useReflectionStream(taskId);
    const endRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    if (!taskId) return null;

    return (
        <div className="w-full bg-gray-900 rounded-lg shadow-xl overflow-hidden border border-gray-700 font-mono text-sm">
            {/* Header */}
            <div className="bg-gray-800 px-4 py-2 flex items-center justify-between border-b border-gray-700">
                <div className="flex items-center gap-2">
                    <span className="text-blue-400 font-bold">🤖 Supervisor Agent</span>
                    <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                </div>
                <span className="text-gray-500 text-xs">Real-time Reflection</span>
            </div>

            {/* Logs Area */}
            <div className="p-4 h-64 overflow-y-auto space-y-3 custom-scrollbar">
                {logs.length === 0 && isConnected && (
                    <div className="text-gray-500 italic">Waiting for thoughts...</div>
                )}
                
                {logs.map((log) => (
                    <div key={log.id} className="animate-fade-in">
                        <div className="flex items-start gap-2">
                            <span className="text-gray-600 text-xs mt-1">[{log.timestamp}]</span>
                            <div className="text-gray-300 whitespace-pre-wrap">
                                {log.content}
                                {!log.isComplete && (
                                    <span className="inline-block w-2 h-4 ml-1 bg-blue-500 align-middle animate-blink"></span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                
                <div ref={endRef} />
            </div>
            
            {/* Status Footer */}
            {!isConnected && logs.length > 0 && (
                 <div className="bg-gray-800 px-4 py-1 text-xs text-gray-500 text-center">
                    Session Disconnected
                </div>
            )}
        </div>
    );
};
