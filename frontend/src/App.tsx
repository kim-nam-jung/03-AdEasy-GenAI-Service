import { useState, useEffect, useRef } from 'react'
import { api, TaskResponse } from './api/client'
import { Layout } from './components/Layout'
import { PipelineLab } from './components/PipelineLab'
import { ToastContainer } from './components/ToastContainer';
import { MessageList } from './components/chat/MessageList';
import { InputBar } from './components/chat/InputBar';
import { ArtifactPane } from './components/chat/ArtifactPane';
import { useReflectionStream } from './hooks/useReflectionStream';

function App() {
  const [currentView, setCurrentView] = useState<'create' | 'lab'>('create');

  // --- CHAT VIEW STATE ---
  const [userPrompt, setUserPrompt] = useState<string>("");
  const [userImages, setUserImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [taskId, setTaskId] = useState<string>('');
  const [isArtifactOpen, setIsArtifactOpen] = useState<boolean>(false);
  
  // Reflection Stream
  const { logs, isConnected } = useReflectionStream(taskId);
  
  // Polling State for Artifact
  const [taskData, setTaskData] = useState<TaskResponse | null>(null);
  const pollTimer = useRef<number | null>(null);

  const handleSend = async (files: File[], prompt: string) => {
    try {
      setIsLoading(true);
      setTaskId(''); // Reset
      setTaskData(null);
      
      // Store user inputs for the chat bubble
      setUserPrompt(prompt);
      const imagePreviews = files.map(f => URL.createObjectURL(f));
      setUserImages(imagePreviews);
      
      // Create Task
      const res = await api.createTask(files, prompt);
      setTaskId(res.task_id);
      setIsArtifactOpen(true); // Open side pane automatically
      
      // Start Polling
      startPolling(res.task_id);
      
    } catch (err) {
        console.error(err);
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
            }
        } catch (err) {
            console.error("Polling error", err);
        }
    }, 2000);
  };
  
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
        <div className={`relative min-h-[calc(100vh-20px)] flex flex-col transition-all duration-300 ${isArtifactOpen ? 'mr-[45%]' : ''}`}>
            {/* Header / Info */}
            {!taskId && !isLoading && (
               <div className="flex-1 flex flex-col items-center justify-center -mt-20 animate-fade-in px-8">
                  <div className="max-w-2xl text-center">
                    <h1 className="text-5xl font-extrabold text-zinc-900 tracking-tight mb-6">
                        영상을 현실로, <span className="text-zinc-400">AdEasy Studio</span>
                    </h1>
                    <p className="text-zinc-500 text-xl leading-relaxed">
                        이미지를 업로드하고 만들고 싶은 광고에 대해 설명해 주세요.<br/>
                        AI 에이전트가 단계를 나누어 고품질 영상을 제작합니다.
                    </p>
                  </div>
               </div>
            )}

            {/* Chat Stream */}
            <div className="flex-1 overflow-y-auto pt-8">
                <MessageList 
                logs={logs} 
                userPrompt={userPrompt} 
                userImages={userImages} 
                />
            </div>

            {/* Artifact Pane (Sidebar) */}
            <ArtifactPane 
               isOpen={isArtifactOpen} 
               onClose={() => setIsArtifactOpen(false)} 
               taskData={taskData}
               isLoading={isLoading}
            />

            {/* Input Bar */}
            <InputBar 
               onSend={handleSend} 
               isLoading={isLoading} 
               isArtifactOpen={isArtifactOpen}
            />
        </div>
      )}
      <ToastContainer />

      {/* Connection Status Button (Floating) */}
      {!isArtifactOpen && taskId && (
         <button 
           onClick={() => setIsArtifactOpen(true)}
           className="fixed right-8 bottom-32 bg-white border border-zinc-200 shadow-xl rounded-full px-4 py-2 flex items-center gap-2 hover:bg-zinc-50 transition-all z-40 animate-bounce"
         >
           <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
           <span className="text-xs font-bold text-zinc-600 uppercase">View Artifact</span>
         </button>
      )}
    </Layout>
  )
}

export default App;
