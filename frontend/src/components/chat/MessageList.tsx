import { API_URL } from '../../api/config';
import { ReflectionLog as ReflectionLogType } from '../../hooks/useReflectionStream';

interface MessageListProps {
  logs: ReflectionLogType[];
  userPrompt?: string;
  userImages: string[];
}

export const MessageList: React.FC<MessageListProps> = ({ logs, userPrompt, userImages }) => {
  const ensureUrl = (path: string) => {
    if (!path) return '';
    if (path.startsWith('http') || path.startsWith('data:') || path.startsWith('blob:')) return path;
    const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
    const p = path.startsWith('/') ? path : `/${path}`;
    return `${base}${p}`;
  };

  // Helper to hide purely technical JSON content from thoughts
  const formatContent = (content: string) => {
    const trimmed = content.trim();
    // If it's a raw JSON object or contains a JSON code block, hide it
    if (
      (trimmed.startsWith('{') && trimmed.endsWith('}')) || 
      trimmed.includes('```json') ||
      (trimmed.includes('{') && trimmed.includes('}') && trimmed.includes('"'))
    ) {
      return null;
    }
    
    // Standard text
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
            {userPrompt && <p className="text-white text-[15px] leading-relaxed font-medium">{userPrompt}</p>}
          </div>
        </div>
      )}

      {/* Agent Response Stream */}
      <div className="space-y-8">
        {logs.filter(log => log.content && log.content.trim() !== "").map((log) => {
          const content = formatContent(log.content);
          if (log.type === 'thought' && !content) return null;

          return (
            <div key={log.id} className="animate-fade-up">
              {log.type === 'thought' && (
                <div className="flex gap-4 items-start">
                  <div className="w-8 h-8 rounded-full bg-zinc-100 border border-zinc-200 flex items-center justify-center shrink-0 mt-1">
                    <div className="w-2 h-2 rounded-full bg-zinc-400" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest ml-3">AI Producer</span>
                    <div className="bg-white border border-zinc-100 rounded-2xl rounded-tl-none px-5 py-3.5 shadow-sm inline-block max-w-full">
                      {content}
                    </div>
                  </div>
                </div>
              )}

              {log.type === 'tool_call' && (
                <div className="my-4 ml-12">
                  <div className="inline-flex items-center gap-2.5 px-3 py-1.5 bg-zinc-50 border border-zinc-200 rounded-full text-[10px] font-bold text-zinc-400 uppercase tracking-tight">
                     <div className="w-1.5 h-1.5 rounded-full bg-zinc-300 animate-pulse" />
                     {log.content}...
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
                             src={ensureUrl(parsed.video_path)} 
                             poster={ensureUrl(parsed.thumbnail_path)} 
                             className="w-full h-full object-contain" 
                           />
                         </div>
                         <div className="p-4 bg-zinc-50 border-t border-zinc-100 italic text-center">
                           <p className="text-[13px] text-zinc-500">영상이 완성되었습니다. 최상의 품질로 감상해 보세요!</p>
                         </div>
                       </div>
                     </div>
                   );
                 }

                 // Handle Strategy Plan
                 if (parsed && parsed.steps && Array.isArray(parsed.steps)) {
                   return (
                     <div className="my-8 animate-fade-up ml-12">
                       <div className="bg-zinc-900 border border-zinc-700 rounded-3xl overflow-hidden shadow-2xl">
                         <div className="px-6 py-4 bg-zinc-800/50 border-b border-zinc-700 flex items-center gap-3">
                           <div className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]" />
                           <span className="text-[11px] font-black text-amber-400 uppercase tracking-[0.2em]">Strategy Plan</span>
                         </div>
                         <div className="p-7 space-y-6">
                           <div className="space-y-4">
                             {parsed.steps.map((step: string, idx: number) => (
                               <div key={idx} className="flex gap-4 items-start">
                                 <span className="flex-shrink-0 w-6 h-6 rounded-full bg-zinc-800 border border-zinc-700 text-[10px] font-bold text-zinc-400 flex items-center justify-center">
                                   {idx + 1}
                                 </span>
                                 <p className="text-[14px] text-zinc-300 leading-snug pt-0.5">{step}</p>
                               </div>
                             ))}
                           </div>
                           {parsed.rationale && (
                             <div className="pt-6 border-t border-zinc-800">
                               <p className="text-[12px] text-zinc-500 italic leading-relaxed">
                                 <span className="text-zinc-400 font-bold not-italic mr-2">Rationale:</span>
                                 {parsed.rationale}
                               </p>
                             </div>
                           )}

                           {/* Human Interaction: Approval Input & Button */}
                           {log.status === 'planning_proposed' && (
                              <div className="mt-8 space-y-4">
                                <div className="relative">
                                  <textarea
                                    id={`feedback-${log.id}`}
                                    placeholder="Add feedback or adjustments (optional)..."
                                    className="w-full bg-zinc-800/50 border border-zinc-700 rounded-2xl px-5 py-4 text-[14px] text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 min-h-[100px] resize-none transition-all"
                                  />
                                </div>
                                <div className="flex justify-end">
                                  <button 
                                    onClick={async (e) => {
                                      const btn = e.currentTarget;
                                      const textarea = document.getElementById(`feedback-${log.id}`) as HTMLTextAreaElement;
                                      const feedbackText = textarea?.value?.trim() || 'Approved';
                                      
                                      btn.disabled = true;
                                      if (textarea) textarea.disabled = true;
                                      
                                      try {
                                        const formData = new FormData();
                                        formData.append('feedback', feedbackText);
                                        await fetch(`${API_URL}/api/v1/tasks/${log.taskId}/feedback`, {
                                          method: 'POST',
                                          headers: { 'X-API-Key': 'adeasy-secret-key' },
                                          body: formData
                                        });
                                      } catch (err) {
                                        console.error("Plan approval failed:", err);
                                        btn.disabled = false;
                                        if (textarea) textarea.disabled = false;
                                      }
                                    }}
                                    className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl text-[14px] font-bold transition-all active:scale-95 flex items-center gap-2 shadow-xl shadow-blue-500/20"
                                  >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                                    Approve & Start
                                  </button>
                                </div>
                              </div>
                            )}

                            {(log.status === 'planning_completed' || log.status === 'feedback_received') && (
                              <div className="mt-6 flex items-center gap-2 text-green-400 text-[11px] font-bold uppercase tracking-wider">
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                Plan Approved
                              </div>
                            )}
                         </div>
                       </div>
                     </div>
                   );
                 }

                 // Handle Reflection (Clean Sentence - Stylized)
                 if (parsed && parsed.reflection) {
                   return (
                    <div className="my-6 flex gap-4 items-start">
                      <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0 mt-1">
                        <div className="w-2 h-2 rounded-full bg-blue-400" />
                      </div>
                      <div className="flex-1 space-y-1">
                        <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest ml-3">Supervisor Feedback</span>
                        <div className="bg-blue-50/50 border border-blue-100 rounded-2xl rounded-tl-none px-5 py-3.5 shadow-sm inline-block">
                          <p className="text-zinc-700 text-[15px] leading-relaxed italic font-medium">
                            {parsed.reflection}
                          </p>
                          {parsed.decision === 'retry' && (
                            <div className="mt-3 flex items-center gap-2 text-[11px] text-amber-600 font-bold uppercase tracking-wider">
                              <span className="animate-spin">↺</span> Retrying with adjustments
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                   );
                 }

                 // Handle Intermediate data (Segmentation etc)
                 if (parsed && !parsed.error) {
                   const isSegmentation = parsed.segmented_layers && Array.isArray(parsed.segmented_layers);
                   
                   // HIDE technical results like vision analysis tables
                   // ONLY show visual results like segmentation layers
                   if (!isSegmentation) return null;
                   
                   return (
                     <div className="my-6 ml-12">
                       <div className="bg-white border border-zinc-200 rounded-2xl overflow-hidden shadow-sm max-w-lg">
                         <div className="px-4 py-2 bg-zinc-50 border-b border-zinc-100 flex items-center justify-between">
                           <span className="text-[9px] font-black text-zinc-400 uppercase tracking-[0.2em]">
                             {log.metadata?.status?.replace(/_/g, ' ') || 'Process Insight'}
                           </span>
                         </div>
                         <div className="p-4">
                            <div className="grid grid-cols-3 gap-2">
                              {parsed.segmented_layers.map((layer: string, idx: number) => (
                                <img key={idx} src={ensureUrl(layer)} className="w-full aspect-square object-cover rounded-lg border border-zinc-100 hover:scale-105 transition-transform" alt="layer" />
                              ))}
                            </div>
                         </div>
                       </div>
                     </div>
                   );
                 }

                 return null; // Don't show raw text results - rely on agent reflection
              })()}
            </div>
          );
        })}
      </div>
    </div>
  );
};
