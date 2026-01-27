import React, { useEffect, useRef, useState } from 'react';
import { useReflectionStream, ReflectionLog as IReflectionLog } from '../hooks/useReflectionStream';

interface ReflectionLogProps {
    taskId: string;
}

export const ReflectionLog: React.FC<ReflectionLogProps> = ({ taskId }) => {
    const { logs, isConnected } = useReflectionStream(taskId);
    const endRef = useRef<HTMLDivElement>(null);
    const [isExpanded, setIsExpanded] = useState(true);

    // Auto-scroll to bottom
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    if (!taskId) return null;

    return (
        <div className="w-full flex flex-col h-full">
            <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 text-xs font-semibold text-zinc-500 hover:text-zinc-800 transition-colors mb-3 px-1 w-full"
            >
                <div 
                    className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium transition-colors ${
                        isConnected 
                        ? 'bg-green-100 text-green-700 border border-green-200' 
                        : 'bg-red-100 text-red-700 border border-red-200 animate-pulse'
                    }`}
                    title={isConnected ? "Real-time logs connected" : "Connection lost. Reconnecting..."}
                >
                    <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                    {isConnected ? 'LIVE' : 'OFFLINE'}
                </div>
                AGENT CHAIN-OF-THOUGHT
                <svg className={`w-3 h-3 ml-auto transition-transform ${isExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"/></svg>
            </button>

            {isExpanded && (
                <div className="flex-1 bg-zinc-50/50 rounded-xl p-4 font-mono text-xs text-zinc-600 overflow-y-auto custom-scrollbar border border-zinc-200/60 shadow-inner min-h-0">
                    {logs.length === 0 && (
                        <div className="text-zinc-400 italic flex items-center gap-2">
                             <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                             Waiting for agent to start thinking...
                        </div>
                    )}
                    
                    {logs.map((log) => (
                        <LogEntry key={log.id} log={log} />
                    ))}
                    <div ref={endRef} />
                </div>
            )}
        </div>
    );
};

const LogEntry: React.FC<{ log: IReflectionLog }> = ({ log }) => {
    const [isCollapsed, setIsCollapsed] = useState(log.type === 'tool_result');

    const getIcon = () => {
        switch (log.type) {
            case 'tool_call': return '🛠️';
            case 'tool_result': return '📦';
            case 'thought': return '💡';
            default: return '•';
        }
    };

    const getBgColor = () => {
        switch (log.type) {
            case 'tool_call': return 'bg-blue-50/80 border-blue-100 text-blue-800';
            case 'tool_result': return 'bg-zinc-100/80 border-zinc-200 text-zinc-600';
            default: return 'bg-transparent border-transparent';
        }
    };

    return (
        <div className={`mb-3 p-2 rounded-lg border transition-all ${getBgColor()}`}>
            <div className="flex items-start gap-2">
                <span className="text-sm shrink-0 select-none" role="img" aria-label={log.type}>
                    {getIcon()}
                </span>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">
                            {log.type.replace('_', ' ')}
                        </span>
                        <span className="text-[10px] text-zinc-300">{log.timestamp}</span>
                    </div>
                    
                    {log.type === 'tool_result' ? (() => {
                        let parsed = null;
                        try {
                            if (log.content.trim().startsWith('{')) {
                                parsed = JSON.parse(log.content);
                            }
                        } catch (e) { /* ignore */ }

                        if (parsed && parsed.reflection) {
                            return (
                                <div className="mt-2 text-[12px] text-zinc-900 leading-relaxed bg-white/40 p-3 rounded-lg border border-zinc-200/50">
                                    {parsed.reflection}
                                </div>
                            );
                        }

                        return (
                            <div>
                                <button 
                                    onClick={() => setIsCollapsed(!isCollapsed)}
                                    className="text-[11px] underline hover:text-zinc-900 flex items-center gap-1"
                                >
                                    {isCollapsed ? 'Show data' : 'Hide data'}
                                </button>
                                {!isCollapsed && (
                                    <div className="mt-2 text-[10px] overflow-x-auto whitespace-pre p-2 bg-white/50 rounded border border-zinc-200/50 max-h-60 custom-scrollbar mt-2">
                                        {parsed ? JSON.stringify(parsed, null, 2) : log.content}
                                    </div>
                                )}
                            </div>
                        );
                    })() : (
                        <div className={`whitespace-pre-wrap leading-relaxed ${log.type === 'thought' ? 'text-zinc-700' : 'font-bold'}`}>
                            {log.content}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
