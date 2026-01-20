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
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 font-sans">
      <div className="w-full max-w-2xl px-6">
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="bg-blue-600 p-6">
                <h1 className="text-2xl font-bold text-white text-center">AdEasy GenAI</h1>
                <p className="text-blue-100 text-center text-sm mt-1">Short Video Generator</p>
            </div>
            
            <div className="p-8 space-y-8">
                {/* 1. Image Upload Section */}
                <section>
                    <h2 className="text-lg font-semibold text-gray-800 mb-3">1. Upload Product Images</h2>
                    <ImageUploader 
                        onImagesSelected={setFiles} 
                        isLoading={isLoading}
                    />
                </section>

                {/* 2. Prompt Section */}
                <section>
                    <h2 className="text-lg font-semibold text-gray-800 mb-3">2. Description (Optional)</h2>
                    <textarea 
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
                        rows={3}
                        placeholder="Describe the mood, style, or key selling points (e.g., 'Luxury cinematic shot, slow motion')"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        disabled={isLoading}
                    />
                </section>

                {/* 3. Action Section */}
                <button 
                    onClick={handleCreateTask}
                    disabled={isLoading || files.length === 0}
                    className={`w-full py-4 text-lg font-bold rounded-lg shadow-md transition-all transform active:scale-95 ${
                        isLoading || files.length === 0
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg'
                    }`}
                >
                    {isLoading ? (
                        <span className="flex items-center justify-center gap-2">
                             <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Processing...
                        </span>
                    ) : 'Generate Video'}
                </button>
                
                {/* 4. Progress Section with Reflection */}
                {taskData && taskData.status !== 'completed' && (
                    <section className="animate-fade-in space-y-4">
                        <ProgressBar 
                            progress={taskData.progress}
                            currentStep={taskData.current_step}
                            message={taskData.message}
                            status={taskData.status}
                        />
                        
                        {/* Reflection Log (Supervisor Thoughts) */}
                        <div className="mt-4">
                            <ReflectionLog taskId={taskData.task_id} />
                        </div>
                    </section>
                )}
                
                {/* 5. Result Gallery (New) */}
                {taskData && taskData.status === 'completed' && (
                    <section className="animate-fade-in space-y-6">
                        <ResultGallery 
                            taskId={taskData.task_id}
                            videoPath={taskData.output_path}
                            thumbnailPath={taskData.thumbnail_path}
                        />
                         {/* Show logs even after completion for review */}
                         <div className="mt-6 opacity-75 hover:opacity-100 transition-opacity">
                            <h3 className="text-sm font-semibold text-gray-500 mb-2">Process Log</h3>
                            <ReflectionLog taskId={taskData.task_id} />
                        </div>
                    </section>
                )}
                
                {status && !taskData && (
                    <div className={`p-4 rounded-lg text-center font-medium animate-fade-in ${
                        status.startsWith('Error') ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'
                    }`}>
                        {status}
                    </div>
                )}
            </div>
        </div>
      </div>
    </div>
  )
}


export default App
