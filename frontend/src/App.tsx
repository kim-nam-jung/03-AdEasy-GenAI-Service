import { useState, useEffect, useRef } from 'react'
import { api, TaskResponse } from './api/client'
import { ImageUploader } from './components/ImageUploader'
import { ProgressBar } from './components/ProgressBar'
import { ResultGallery } from './components/ResultGallery'
import { ReflectionLog } from './components/ReflectionLog'

function App() {
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
      setStatus('Uploading & Queuing...');
      setTaskData(null); // Reset previous task data
      
      const res = await api.createTask(files, prompt);
      
      setStatus(`Processing Started! ID: ${res.task_id}`);
      
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
                setStatus(res.status === 'completed' ? 'Generation Successful!' : 'Generation Failed');
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
    <div className="min-h-screen bg-slate-50 relative overflow-hidden font-sans text-slate-900 selection:bg-indigo-100 selection:text-indigo-700">
      {/* Abstract Background Shapes */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-200/30 blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-200/30 blur-[120px]" />

      <div className="relative z-10 w-full max-w-4xl mx-auto px-6 py-12 md:py-20">
        
        {/* Header */}
        <header className="mb-12 text-center space-y-4 animate-fade-in">
            <div className="inline-block p-3 rounded-2xl bg-indigo-600/5 text-indigo-600 mb-2">
                <span className="font-bold tracking-wider text-xs uppercase">AI Video Generation</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-slate-900">
                AdEasy GenAI
            </h1>
            <p className="text-lg text-slate-500 max-w-lg mx-auto leading-relaxed">
                Transform your product images into professional short videos in seconds.
            </p>
        </header>
            
        {/* Main Card */}
        <div className="glass rounded-3xl p-8 md:p-12 shadow-2xl shadow-indigo-500/10 border border-white/50 space-y-12 animate-slide-up">
            {/* 1. Image Upload Section */}
            <section className="space-y-6">
                 <div className="flex items-center gap-4 mb-2">
                    <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-lg shadow-indigo-600/20">1</div>
                    <h2 className="text-2xl font-bold text-slate-800">Product Assets</h2>
                </div>
                <ImageUploader 
                    onImagesSelected={setFiles} 
                    isLoading={isLoading}
                />
            </section>

            {/* 2. Prompt Section */}
            <section className="space-y-6 border-t border-slate-100 pt-10">
                 <div className="flex items-center gap-4 mb-2">
                     <div className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-lg shadow-lg shadow-indigo-600/20">2</div>
                    <h2 className="text-2xl font-bold text-slate-800">Your Vision</h2>
                </div>
                
                <div className="relative group">
                    <textarea 
                        className="w-full p-6 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all resize-none text-slate-700 placeholder:text-slate-400 text-lg shadow-sm group-hover:border-indigo-300"
                        rows={4}
                        placeholder="Describe the mood, style, or key selling points (e.g., 'Luxury cinematic shot, slow motion')"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        disabled={isLoading}
                    />
                     <div className="absolute bottom-4 right-4 text-xs font-medium text-slate-400 bg-white px-2 py-1 rounded-md shadow-sm border border-slate-100">
                        Optional
                    </div>
                </div>
            </section>

            {/* 3. Action Section */}
             <div className="pt-6">
                <button 
                    onClick={handleCreateTask}
                    disabled={isLoading || files.length === 0}
                    className={`w-full py-5 text-xl font-bold rounded-2xl shadow-xl transition-all transform duration-200 group relative overflow-hidden ${
                        isLoading || files.length === 0
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-2xl hover:shadow-indigo-600/30 active:scale-[0.98]'
                    }`}
                >
                    <span className="relative z-10 flex items-center justify-center gap-3">
                        {isLoading ? (
                            <>
                                 <svg className="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Processing...
                            </>
                        ) : (
                             <>Generate Video <span className="group-hover:translate-x-1 transition-transform">→</span></>
                        )}
                    </span>
                 </button>
            </div>
        </div>
        
        {/* 4. Progress Section with Reflection */}
        {(taskData || status) && (
             <div className="mt-12 space-y-8 animate-slide-up">
                 {status && !taskData && (
                    <div className={`p-4 rounded-xl text-center font-medium animate-fade-in ${
                        status.startsWith('Error') 
                        ? 'bg-red-50 text-red-700 border border-red-200' 
                        : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                    }`}>
                        {status}
                    </div>
                )}

                {taskData && taskData.status !== 'completed' && (
                    <div className="space-y-8">
                        <ProgressBar 
                            progress={taskData.progress}
                            currentStep={taskData.current_step}
                            message={taskData.message}
                            status={taskData.status}
                        />
                        <ReflectionLog taskId={taskData.task_id} />
                    </div>
                )}
                
                {/* 5. Result Gallery (New) */}
                {taskData && taskData.status === 'completed' && (
                    <div className="space-y-12">
                        <ResultGallery 
                            taskId={taskData.task_id}
                            videoPath={taskData.output_path}
                            thumbnailPath={taskData.thumbnail_path}
                        />
                         {/* Show logs even after completion for review */}
                         <div className="opacity-75 hover:opacity-100 transition-opacity">
                            <h3 className="text-sm font-semibold text-slate-500 mb-2 uppercase tracking-wide">Process Log</h3>
                            <ReflectionLog taskId={taskData.task_id} />
                        </div>
                    </div>
                )}
            </div>
        )}
      </div>
    </div>
  )
}


export default App
