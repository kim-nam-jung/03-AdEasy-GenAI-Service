import React from 'react';
import { ResultGallery } from '../ResultGallery';
import { ProgressBar } from '../ProgressBar';
import { TaskResponse } from '../../api/client';

interface ArtifactPaneProps {
  isOpen: boolean;
  onClose: () => void;
  taskData: TaskResponse | null;
  isLoading: boolean;
}

export const ArtifactPane: React.FC<ArtifactPaneProps> = ({ isOpen, onClose, taskData, isLoading }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full lg:w-[45%] bg-white border-l border-zinc-200 z-[60] shadow-2xl animate-fade-in-right overflow-y-auto">
      <div className="sticky top-0 bg-white/90 backdrop-blur-md z-10 px-8 py-5 border-b border-zinc-100 flex items-center justify-between">
         <h2 className="font-bold text-zinc-900 flex items-center gap-2.5 text-xs uppercase tracking-[0.2em]">
            <div className="w-2.5 h-2.5 rounded-full bg-zinc-900 shadow-[0_0_8px_rgba(0,0,0,0.2)]" />
            Vision Artifact
         </h2>
         <button onClick={onClose} className="p-2 hover:bg-zinc-100 rounded-full transition-all active:scale-90">
            <svg className="w-5 h-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
         </button>
      </div>

      <div className="p-8 pb-32">
        {taskData && taskData.status === 'completed' ? (
           <div className="animate-fade-in">
             <ResultGallery 
               taskId={taskData.task_id}
               videoPath={taskData.output_path}
               thumbnailPath={taskData.thumbnail_path}
             />
           </div>
        ) : (
          <div className="flex flex-col items-center justify-center min-h-[500px] text-center px-6">
            {isLoading ? (
               <div className="w-full max-w-sm space-y-8">
                  <div className="relative">
                    <div className="absolute inset-0 bg-zinc-900/5 blur-3xl rounded-full" />
                    {taskData && (
                      <ProgressBar 
                          progress={taskData.progress}
                          currentStep={taskData.current_step}
                          message={taskData.message}
                          status={taskData.status}
                      />
                    )}
                  </div>
                  {!taskData && (
                    <div className="space-y-6">
                       <div className="relative h-1 w-48 mx-auto bg-zinc-100 rounded-full overflow-hidden">
                          <div className="absolute inset-0 bg-zinc-900 animate-loading-bar" />
                       </div>
                       <p className="text-zinc-400 text-xs font-bold uppercase tracking-widest">Initializing Pipeline...</p>
                    </div>
                  )}
               </div>
            ) : (
              <div className="space-y-6 animate-fade-up">
                <div className="w-20 h-20 bg-zinc-50 rounded-3xl flex items-center justify-center mx-auto border border-zinc-100">
                  <svg className="w-8 h-8 text-zinc-200" fill="none" viewBox="0 0 24 24" stroke="currentColor font-light"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                </div>
                <p className="text-sm text-zinc-400 font-medium">현재 생성된 결과물이 없습니다.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
