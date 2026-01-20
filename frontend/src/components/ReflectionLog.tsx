import React, { useEffect, useRef } from 'react';
import { useReflectionStream } from '../hooks/useReflectionStream';

interface ReflectionLogProps {
    taskId: string;
}

export const ReflectionLog: React.FC<ReflectionLogProps> = ({ taskId }) => {
    const { logs, isConnected } = useReflectionStream(taskId);
    const endRef = useRef<HTMLDivElement>(null);
    const [isExpanded, setIsExpanded] = React.useState(true);

    // Auto-scroll to bottom
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    if (!taskId) return null;

    return (
        <div className="w-full border-t border-zinc-100 mt-4 pt-4">
            <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 text-xs font-semibold text-zinc-500 hover:text-zinc-800 transition-colors mb-2 w-full"
            >
                <svg className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/></svg>
                SUPERVISOR LOGS
                <span className={`w-1.5 h-1.5 rounded-full ml-auto ${isConnected ? 'bg-green-500' : 'bg-zinc-300'}`} />
            </button>

            {isExpanded && (
                <div className="w-full bg-zinc-50 rounded-md p-4 font-mono text-xs text-zinc-600 h-48 overflow-y-auto custom-scrollbar border border-zinc-200/50 shadow-inner">
                    {logs.length === 0 && (
                        <div className="text-zinc-400 italic">No logs yet...</div>
                    )}
                    
                    {logs.map((log) => (
                        <div key={log.id} className="mb-2 last:mb-0">
                            <span className="text-zinc-400 mr-2 select-none">[{log.timestamp.split(' ')[1]}]</span>
                            <span className="whitespace-pre-wrap">{log.content}</span>
                        </div>
                    ))}
                    <div ref={endRef} />
                </div>
            )}
        </div>
    );
};
