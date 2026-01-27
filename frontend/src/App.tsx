import { useState, useEffect, useRef } from 'react'
import { api, TaskResponse } from './api/client'
import { Layout } from './components/Layout'
import { PipelineLab } from './components/PipelineLab'
import { ToastContainer } from './components/ToastContainer';
import { MessageList } from './components/chat/MessageList';
import { InputBar } from './components/chat/InputBar';
import { useReflectionStream } from './hooks/useReflectionStream';

function App() {
  const [currentView, setCurrentView] = useState<'create' | 'lab'>('create');

  // --- CHAT VIEW STATE ---
  const [userPrompt, setUserPrompt] = useState<string>("");
  const [userImages, setUserImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [taskId, setTaskId] = useState<string>('');
  const { logs } = useReflectionStream(taskId);

  const handleSend = async (files: File[], prompt: string) => {
    try {
      setIsLoading(true);
      setTaskId(''); // Reset
      
      // Store user inputs for the chat bubble
      setUserPrompt(prompt);
      const imagePreviews = files.map(f => URL.createObjectURL(f));
      setUserImages(imagePreviews);
      
      // Create Task
      const res = await api.createTask(files, prompt);
      setTaskId(res.task_id);
      
      // No more polling needed, we use the reflection stream events
      
    } catch (err) {
        console.error(err);
        setIsLoading(false);
    }
  };
  


  return (
    <Layout currentView={currentView} onNavigate={setCurrentView}>
      {currentView === 'lab' ? (
        <PipelineLab />
      ) : (
        <div className="relative min-h-[calc(100vh-20px)] flex flex-col transition-all duration-300">
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

            {/* Input Bar */}
            <InputBar 
               onSend={handleSend} 
               isLoading={isLoading} 
            />
        </div>
      )}
      <ToastContainer />
    </Layout>
  )
}

export default App;
