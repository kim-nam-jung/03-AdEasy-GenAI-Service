import React from 'react';
import { ReflectionLog as ReflectionLogType } from '../../hooks/useReflectionStream';

interface MessageListProps {
  logs: ReflectionLogType[];
  userPrompt?: string;
  userImages: string[];
}

export const MessageList: React.FC<MessageListProps> = ({ logs, userPrompt, userImages }) => {
  // Helper to detect and format JSON or code-like thought content
  const formatContent = (content: string) => {
    if (content.trim().startsWith('{') || content.trim().startsWith('```')) {
      return (
        <pre className="bg-zinc-50 border border-zinc-200 rounded-xl p-4 text-[12px] font-mono text-zinc-600 overflow-x-auto my-2">
          {content.replace(/```json|```/g, '').trim()}
        </pre>
      );
    }
    return <p className="text-zinc-800 text-[15px] leading-relaxed whitespace-pre-wrap">{content}</p>;
  };

  return (
    <div className="flex flex-col gap-10 pb-40 max-w-2xl mx-auto w-full px-6 pt-16">
      {/* User Message */}
      {(userPrompt || userImages.length > 0) && (
        <div className="flex flex-col gap-4 items-end animate-fade-in">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 max-w-[85%] shadow-lg shadow-zinc-200/20">
            <div className="flex gap-2.5 mb-3">
              {userImages.map((img, i) => (
                <img key={i} src={img} alt="upload" className="w-20 h-20 object-cover rounded-xl border border-white/10" />
              ))}
            </div>
            {userPrompt && <p className="text-white text-[15px] leading-relaxed">{userPrompt}</p>}
          </div>
        </div>
      )}

      {/* Agent Response Stream */}
      <div className="space-y-8">
        {logs.filter(log => log.content && log.content.trim() !== "").map((log) => (
          <div key={log.id} className="animate-fade-up">
            {log.type === 'thought' && (
              <div className="flex gap-5 group">
                <div className="flex-1">
                  {formatContent(log.content)}
                </div>
              </div>
            )}

            {log.type === 'tool_call' && (
              <div className="my-4">
                <div className="inline-flex items-center gap-2.5 px-3 py-1.5 bg-zinc-50 border border-zinc-200 rounded-full text-[11px] font-bold text-zinc-500 uppercase tracking-tight">
                   <div className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse" />
                   Running {log.content}...
                </div>
              </div>
            )}

            {log.type === 'tool_result' && (
              <div className="my-6">
                <div className="bg-zinc-50/50 border border-zinc-200/60 rounded-2xl overflow-hidden">
                   <div className="px-4 py-2 border-b border-zinc-100 flex items-center justify-between">
                      <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Reflection Insight</span>
                      <div className="w-1 h-1 rounded-full bg-green-400" />
                   </div>
                   <div className="p-4">
                      {log.content.trim().startsWith('{') || log.content.trim().startsWith('```') ? (
                        <pre className="bg-zinc-100 border border-zinc-200 rounded-lg p-3 text-[12px] font-mono text-zinc-600 overflow-x-auto">
                          {log.content.replace(/```json|```/g, '').trim()}
                        </pre>
                      ) : (
                        <p className="text-[13px] text-zinc-500 leading-relaxed font-medium whitespace-pre-wrap">{log.content}</p>
                      )}
                   </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
