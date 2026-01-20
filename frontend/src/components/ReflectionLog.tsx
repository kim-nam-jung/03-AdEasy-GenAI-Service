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
        <div className="w-full bg-slate-900 rounded-2xl shadow-2xl overflow-hidden border border-slate-700/50 font-mono text-sm ring-1 ring-white/10">
            {/* Header */}
            <div className="bg-slate-950/50 px-5 py-3 flex items-center justify-between border-b border-white/5 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500/80"></span>
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></span>
                        <span className="w-2.5 h-2.5 rounded-full bg-green-500/80"></span>
                    </div>
                    <span className="text-slate-400 font-medium text-xs ml-2">SUPERVISOR.LOG</span>
                </div>
                <div className="flex items-center gap-2 bg-black/20 px-2 py-1 rounded-md">
                     <span className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'}`}></span>
                    <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">
                        {isConnected ? 'Live' : 'Offline'}
                    </span>
                </div>
            </div>

            {/* Logs Area */}
            <div className="p-6 h-64 overflow-y-auto space-y-3 custom-scrollbar bg-slate-900/50">
                {logs.length === 0 && isConnected && (
                    <div className="text-slate-600 italic">Initializing agent process...</div>
                )}
                
                {logs.map((log) => (
                    <div key={log.id} className="animate-fade-in group">
                        <div className="flex items-start gap-3">
                            <span className="text-indigo-400/50 text-xs mt-0.5 select-none font-light min-w-[60px]">{log.timestamp}</span>
                            <div className="text-slate-300 whitespace-pre-wrap leading-relaxed group-hover:text-white transition-colors">
                                {log.content}
                                {!log.isComplete && (
                                    <span className="inline-block w-2 h-4 ml-1 bg-indigo-500 align-middle animate-ping"></span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                
                <div ref={endRef} />
            </div>
            
            {/* Status Footer */}
            {!isConnected && logs.length > 0 && (
                 <div className="bg-red-500/10 px-4 py-1.5 text-xs text-red-400 text-center border-t border-red-500/20">
                    Connection Closed
                </div>
            )}
        </div>
    );
};
