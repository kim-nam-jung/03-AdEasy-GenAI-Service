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

            {log.type === 'tool_result' && (() => {
               let parsed: any = null;
               try {
                 if (log.content.trim().startsWith('{')) {
                   parsed = JSON.parse(log.content.replace(/```json|```/g, '').trim());
                 }
               } catch (e) { /* ignore */ }

               // Handle Final Output
               if (log.metadata?.is_final && parsed?.video_path) {
                 return (
                   <div className="my-10 animate-scale-in">
                     <div className="bg-white border-2 border-green-500/20 rounded-3xl overflow-hidden shadow-2xl">
                       <div className="px-6 py-3 bg-green-50 border-b border-green-100 flex items-center justify-between">
                         <div className="flex items-center gap-2">
                           <span className="flex h-2 w-2 rounded-full bg-green-500" />
                           <span className="text-[12px] font-black text-green-700 uppercase tracking-widest">Final Masterpiece</span>
                         </div>
                         <span className="text-[10px] text-green-600/60 font-mono">COMPLETE</span>
                       </div>
                       <div className="aspect-video relative bg-black">
                         <video 
                           controls 
                           autoPlay
                           loop
                           src={parsed.video_path} 
                           poster={parsed.thumbnail_path} 
                           className="w-full h-full object-contain" 
                         />
                       </div>
                       <div className="p-4 bg-zinc-50 border-t border-zinc-100 italic text-center">
                         <p className="text-[13px] text-zinc-500">Pipeline completed successfully. Your video is ready!</p>
                       </div>
                     </div>
                   </div>
                 );
               }

               // Handle Reflection (Clean Sentence)
               if (parsed && parsed.reflection) {
                 return (
                   <div className="my-8 flex justify-start">
                     <div className="bg-blue-50/50 border border-blue-100 rounded-2xl px-6 py-4 max-w-[90%] shadow-sm">
                       <div className="flex items-center gap-2 mb-2">
                          <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Supervisor Reflection</span>
                       </div>
                       <p className="text-zinc-700 text-[15px] leading-relaxed italic">
                         {parsed.reflection}
                       </p>
                       {parsed.decision === 'retry' && (
                         <div className="mt-3 flex items-center gap-2 text-[12px] text-amber-600 font-bold">
                           <span className="animate-spin text-lg">↺</span> Retrying with adjusted parameters...
                         </div>
                       )}
                     </div>
                   </div>
                 );
               }

               // Handle Intermediate data (Segmentation etc)
               if (parsed && !parsed.error) {
                 const isSegmentation = parsed.segmented_layers && Array.isArray(parsed.segmented_layers);
                 
                 return (
                   <div className="my-6">
                     <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden shadow-sm">
                       <div className="px-4 py-2 bg-zinc-50 border-b border-zinc-100 flex items-center justify-between">
                         <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                           {log.metadata?.status?.replace(/_/g, ' ') || 'Tool Insight'}
                         </span>
                         <div className="w-1 h-1 rounded-full bg-blue-400" />
                       </div>
                       <div className="p-4">
                         {isSegmentation ? (
                           <div className="grid grid-cols-3 gap-2">
                             {parsed.segmented_layers.map((layer: string, idx: number) => (
                               <img key={idx} src={layer} className="w-full aspect-square object-cover rounded-lg border border-zinc-100" alt="layer" />
                             ))}
                           </div>
                         ) : (
                           <div className="space-y-2">
                             {Object.entries(parsed).map(([key, value]: [string, any]) => {
                               if (typeof value === 'object' || key.includes('path')) return null;
                               return (
                                 <div key={key} className="flex items-baseline gap-2">
                                   <span className="text-[10px] font-bold text-zinc-400 uppercase shrink-0 w-24">{key.replace(/_/g, ' ')}</span>
                                   <p className="text-[13px] text-zinc-600">{String(value)}</p>
                                 </div>
                               )
                             })}
                           </div>
                         )}
                       </div>
                     </div>
                   </div>
                 );
               }

               return (
                 <div className="my-6 flex justify-start">
                    <div className="bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-3 max-w-[80%]">
                       <p className="text-[13px] text-zinc-500 leading-relaxed font-medium">{log.content}</p>
                    </div>
                 </div>
               );
            })()}
          </div>
        ))}
      </div>
    </div>
  );
};
