import { useState, useEffect, useRef } from 'react'
import { api, TaskResponse } from './api/client'
import { Layout } from './components/Layout'
import { ImageUploader } from './components/ImageUploader'
import { ProgressBar } from './components/ProgressBar'
import { ResultGallery } from './components/ResultGallery'
import { ReflectionLog } from './components/ReflectionLog'
import { PipelineLab } from './components/PipelineLab'
import { ToastContainer } from './components/ToastContainer';

function App() {
  const [currentView, setCurrentView] = useState<'create' | 'lab'>('create');

  // --- CREATE VIEW STATE ---
  const [status, setStatus] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [files, setFiles] = useState<File[]>([]);
  const [prompt, setPrompt] = useState<string>("");
  
  // Polling State
  const [taskData, setTaskData] = useState<TaskResponse | null>(null);
  const pollTimer = useRef<number | null>(null);

  const handleCreateTask = async () => {
    if (files.length === 0) {
        alert("Please select images first.");
        return;
    }

    try {
      setIsLoading(true);
      setStatus('Starting...');
      setTaskData(null); // Reset previous task data
      
      const res = await api.createTask(files, prompt);
      
      setStatus(`Processing ID: ${res.task_id}`);
      
      // Start Polling immediately
      startPolling(res.task_id);
      
    } catch (err) {
        if (err instanceof Error) {
            setStatus(`Error: ${err.message}`);
        } else {
            setStatus(`Error: Unknown error`);
        }
        setIsLoading(false);
    }
  };
  
  const startPolling = (tid: string) => {
    if (pollTimer.current) window.clearInterval(pollTimer.current);
    
    pollTimer.current = window.setInterval(async () => {
        try {
            const res = await api.getTask(tid);
            setTaskData(res);
            
            if (res.status === 'completed' || res.status === 'failed') {
                if (pollTimer.current) window.clearInterval(pollTimer.current);
                setIsLoading(false);
                setStatus(res.status === 'completed' ? 'Done' : 'Failed');
            }
        } catch (err) {
            console.error("Polling error", err);
        }
    }, 2000); // Poll every 2 seconds
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
        if (pollTimer.current) window.clearInterval(pollTimer.current);
    };
  }, []);

  return (
    <Layout currentView={currentView} onNavigate={setCurrentView}>
      {currentView === 'lab' ? (
        <PipelineLab />
      ) : (
        <div className="flex flex-col lg:flex-row gap-8 h-full">
            {/* LEFT COLUMN: Controls & Input currently max-w-lg for readability */}
            <div className="flex-1 max-w-xl flex flex-col gap-8 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Create Video</h1>
                <p className="text-zinc-500 text-sm mt-1">Generate social media shorts from static product images.</p>
            </div>
            
            <div className="space-y-6">
                    {/* Image Uploader */}
                <ImageUploader 
                    onImagesSelected={setFiles} 
                    isLoading={isLoading}
                />
                
                {/* Prompt Input */}
                <div>
                    <label className="block text-sm font-semibold text-zinc-900 mb-2">Description</label>
                    <textarea 
                            className="w-full p-4 bg-zinc-50 border border-zinc-200 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none text-zinc-700 placeholder:text-zinc-400 text-sm min-h-[120px] shadow-sm"
                            placeholder="E.g., A cinematic slow-motion shot with golden hour lighting..."
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            disabled={isLoading}
                        />
                </div>
                
                {/* Main Action Button */}
                    <button 
                        onClick={handleCreateTask}
                        disabled={isLoading || files.length === 0}
                        className={`w-full py-3 px-4 text-sm font-bold rounded-lg shadow-sm transition-all flex items-center justify-center gap-2 ${
                            isLoading || files.length === 0
                            ? 'bg-zinc-100 text-zinc-400 cursor-not-allowed border border-zinc-200'
                            : 'bg-zinc-900 text-white hover:bg-black hover:shadow-md'
                        }`}
                    >
                        {isLoading ? (
                            <>
                                <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Wait a moment...
                            </>
                        ) : (
                            <>Generate Video <span className="text-zinc-400 ml-1">→</span></>
                        )}
                    </button>
            </div>
            </div>

            {/* RIGHT COLUMN: Preview & Logs */}
            <div className="flex-1 border-l border-zinc-100 pl-8 flex flex-col gap-6 animate-fade-in delay-75">
                <div className="flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-zinc-900">Output Preview</h2>
                    {status && (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${status === 'Done' ? 'bg-green-100 text-green-700' : 'bg-zinc-100 text-zinc-600'}`}>
                            {status}
                        </span>
                    )}
                </div>

                {/* Container for Output or Empty State */}
                <div className="flex-1 bg-zinc-50 rounded-xl border border-dashed border-zinc-200 flex flex-col items-center justify-center relative overflow-hidden min-h-[400px]">
                    {taskData && taskData.status === 'completed' ? (
                        <ResultGallery 
                            taskId={taskData.task_id}
                            videoPath={taskData.output_path}
                            thumbnailPath={taskData.thumbnail_path}
                        />
                    ) : (
                        <div className="text-center p-8 max-w-xs">
                            {isLoading ? (
                                <div className="w-full">
                                    {taskData && (
                                        <ProgressBar 
                                            progress={taskData.progress}
                                            currentStep={taskData.current_step}
                                            message={taskData.message}
                                            status={taskData.status}
                                        />
                                    )}
                                </div>
                            ) : (
                                <>
                                    <div className="w-12 h-12 bg-white rounded-xl shadow-sm border border-zinc-200 flex items-center justify-center mx-auto mb-4">
                                        <svg className="w-6 h-6 text-zinc-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                    </div>
                                    <h3 className="text-zinc-900 font-medium text-sm">No Preview Available</h3>
                                    <p className="text-zinc-400 text-xs mt-1">Configure parameters on the left and click Generate to see results here.</p>
                                </>
                            )}
                        </div>
                    )}
                </div>
                
                {/* Logs Panel attached to bottom of Right Column */}
                {(taskData || status) && (
                <div className="bg-white rounded-lg border border-zinc-200 p-4 shadow-sm">
                    <ReflectionLog taskId={taskData?.task_id || ''} />
                </div>
                )}
            </div>
        </div>
      )}
      <ToastContainer />
    </Layout>
  )
}


export default App
