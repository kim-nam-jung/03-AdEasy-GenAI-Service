import React, { useEffect, useState } from 'react';
import { usePipelineStore } from '../store/pipelineStore';
import { ReflectionLog } from './ReflectionLog';
import { ImageUploader } from './ImageUploader';
import { api } from '../api/client';
import { useToastStore } from '../store/toastStore';

import { API_URL, WS_BASE_URL } from '../api/config';

export const PipelineLab: React.FC = () => {
    // Global Store
    const {
        taskId, status, progress,
        isProcessing,
        showFeedbackModal, feedbackQuestion, feedbackContext,
        
        setTaskId, 
        setIsProcessing,
        openFeedbackModal, closeFeedbackModal, updateTaskStatus, resetPipeline
    } = usePipelineStore();
    
    // Toast
    const { addToast } = useToastStore();
    
    // Local inputs for creating a new task
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [prompt, setPrompt] = useState("");
    const [feedbackInput, setFeedbackInput] = useState("");

    // WebSocket Connection Manager
    useEffect(() => {
        if (!taskId) return;

        const wsBase = WS_BASE_URL;
        const wsUrl = `${wsBase}/ws/${taskId}`;
        
        console.log(`Connecting to WS: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);
        
        let nextSeqNum = 1;
        const messageBuffer = new Map<number, any>();

        const processMessage = (msgData: any) => {
            switch (msgData.type) {
                case 'log':
                    console.log(`[${msgData.level}] ${msgData.message}`);
                    break;
                case 'progress':
                    updateTaskStatus({ 
                        progress: msgData.value, 
                        status: msgData.status || status 
                    });
                    break;
                case 'status':
                    console.log(`[Status] Moved to ${msgData.status}`);
                    handleStatusUpdate(msgData);
                    break;
                case 'human_input_request':
                    openFeedbackModal(msgData.question || "Guidance needed", msgData.context || "");
                    break;
                case 'human_input_received':
                    closeFeedbackModal();
                    console.log("[Human] Feedback received, resuming...");
                    break;
                case 'error':
                     console.log(`[Error] ${msgData.message}`);
                     setIsProcessing(false);
                     addToast('error', msgData.message);
                     break;
            }
        };

        const drainBuffer = () => {
            while (messageBuffer.has(nextSeqNum)) {
                processMessage(messageBuffer.get(nextSeqNum));
                messageBuffer.delete(nextSeqNum);
                nextSeqNum++;
            }
        };
        
        ws.onopen = () => console.log(`[System] Connected to task stream: ${taskId}`);
        
        ws.onmessage = (event) => {
            try {
                const envelope = JSON.parse(event.data);
                
                if (envelope.type === 'ping') return;

                if (envelope.seq === undefined) {
                    processMessage(envelope);
                    return;
                }

                messageBuffer.set(envelope.seq, envelope.data);
                drainBuffer();
            } catch (e) {
                console.error("WS Parse Error", e);
            }
        };

        ws.onclose = () => console.log("[System] WebSocket Disconnected");
        ws.onerror = (e) => {
            console.error("WS Error", e);
            addToast('error', "WebSocket connection failed");
        };

        return () => ws.close();
    }, [taskId, status, updateTaskStatus, openFeedbackModal, closeFeedbackModal, setIsProcessing, addToast]);

    // Parse status updates to populate results
    const handleStatusUpdate = (data: any) => {
         const updates: any = { status: data.status };

         if (data.status === 'completed') {
             updates.isProcessing = false;
             addToast('success', "Pipeline Completed Successfully!");
         } else if (data.status === 'failed') {
             updates.isProcessing = false;
             addToast('error', "Pipeline Failed");
         }

         updateTaskStatus(updates);
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return addToast('warning', "Please select an image first.");
        
        resetPipeline();
        updateTaskStatus({ isProcessing: true, activeTab: "logs" });
        
        const formData = new FormData();
        selectedFiles.forEach((file) => formData.append("files", file));
        formData.append("prompt", prompt);
        
        try {
            const res = await fetch(`${API_URL}/api/v1/tasks/`, {
                method: "POST",
                headers: {
                    "X-API-Key": "adeasy-secret-key"
                },
                body: formData
            });
            
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(typeof errData.detail === 'string' ? errData.detail : "Check console for detail");
            }
            
            const data = await res.json();
            setTaskId(data.task_id);
            addToast('success', `Task Initialized: ${data.task_id}`);
            console.log(`[System] Task Initialized: ${data.task_id}`);
            
        } catch (err: any) {
            console.error(err);
            updateTaskStatus({ isProcessing: false });
            addToast('error', "Failed to start task: " + err.message);
        }
    };

    const submitFeedback = async () => {
        if (!taskId || !feedbackInput.trim()) return;
        
        try {
            const formData = new FormData();
            formData.append("feedback", feedbackInput);
            const res = await fetch(`${API_URL}/api/v1/tasks/${taskId}/feedback`, {
                method: "POST",
                headers: {
                    "X-API-Key": "adeasy-secret-key"
                },
                body: formData
            });

            if (!res.ok) throw new Error("Feedback submission failed");
            
            setFeedbackInput("");
            closeFeedbackModal();
            addToast('success', "Feedback submitted");
        } catch (err) {
            addToast('error', "Failed to submit feedback");
            console.error(err);
        }
    };

    const handleCleanup = async () => {
        try {
            await api.debugCleanup();
            console.log("[System] VRAM Cleared manually.");
            addToast('success', "VRAM Cleared");
        } catch (e: any) {
             addToast('error', `Cleanup failed: ${e.message}`);
        }
    };

    return (
        <div className="flex flex-col h-full animate-fade-in font-sans text-zinc-800">
             {/* Feedback Modal */}
             {showFeedbackModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
                    <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-lg animate-scale-in border border-red-200">
                        <div className="flex items-center gap-2 text-red-600 mb-4">
                            <span className="text-2xl">⚠️</span>
                            <h3 className="text-xl font-bold">Agent Needs Help</h3>
                        </div>
                        
                        <p className="text-lg font-medium mb-2">{feedbackQuestion}</p>
                        {feedbackContext && (
                            <div className="bg-zinc-50 p-3 rounded-lg border border-zinc-200 text-sm text-zinc-600 italic mb-4">
                                {feedbackContext}
                            </div>
                        )}
                        
                        <textarea
                            className="w-full border border-zinc-300 rounded-lg p-3 h-32 mb-4 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                            placeholder="Provide guidance..."
                            value={feedbackInput}
                            onChange={(e) => setFeedbackInput(e.target.value)}
                        />
                        
                        <div className="flex justify-end gap-3">
                            <button 
                                onClick={closeFeedbackModal}
                                className="px-4 py-2 text-zinc-500 hover:bg-zinc-100 rounded-lg"
                            >
                                Ignore
                            </button>
                            <button 
                                onClick={submitFeedback}
                                disabled={!feedbackInput.trim()}
                                className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
                            >
                                Send Guidance
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                     <h1 className="text-3xl font-bold tracking-tight text-zinc-900">AdGen Agent</h1>
                     <p className="text-zinc-500 mt-1">Autonomous Video Generation Pipeline status monitor.</p>
                </div>
                <div className="flex gap-2">
                     <button onClick={handleCleanup} className="px-3 py-1.5 text-xs text-zinc-600 border rounded hover:bg-zinc-50">Clear VRAM</button>
                </div>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Main Content Area */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-1">
                {activeTab === 'upload' && !isProcessing && !taskId && (
                    <div className="space-y-6 max-w-2xl mx-auto pt-10">
                         <section className="bg-white p-8 rounded-3xl border border-zinc-200 shadow-xl shadow-zinc-200/50">
                            <h3 className="text-2xl font-bold text-zinc-900 mb-6">Create New Video</h3>
                            <div className="space-y-6">
                                <ImageUploader onImagesSelected={setSelectedFiles} isLoading={isProcessing} />
                                
                                <div className="space-y-2">
                                    <label className="block text-sm font-bold text-zinc-500 uppercase tracking-wider ml-1">Motion Prompt</label>
                                    <textarea
                                        className="w-full p-4 border border-zinc-200 rounded-2xl h-32 text-[15px] focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all placeholder:text-zinc-300"
                                        placeholder="Describe the desired video motion and atmosphere (e.g. 'Cinematic tracking shot, soft lighting, 4k')..."
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                    />
                                </div>
                                
                                <button 
                                    onClick={handleUpload}
                                    disabled={isProcessing || selectedFiles.length === 0}
                                    className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl font-bold text-lg hover:shadow-lg hover:shadow-blue-500/30 disabled:opacity-50 transition-all transform active:scale-[0.98]"
                                >
                                    {isProcessing ? "Agent Working..." : "Generate Autonomous Video"}
                                </button>
                            </div>
                         </section>
                    </div>
                )}

                {(isProcessing || taskId) && (
                     <div className="bg-white rounded-3xl border border-zinc-200 h-full overflow-hidden flex flex-col shadow-inner">
                         {isProcessing && (
                           <div className="px-6 py-3 bg-blue-600 text-white flex items-center justify-between text-xs font-bold uppercase tracking-widest">
                             <div className="flex items-center gap-3">
                               <div className="w-2 h-2 rounded-full bg-white animate-ping" />
                               Autonomous Agent Processing...
                             </div>
                             <div className="flex gap-4">
                               <span>Step: {progress > 66 ? 'Postprocess' : progress > 33 ? 'Video Gen' : 'Segmentation'}</span>
                               <span>{Math.round(progress)}%</span>
                             </div>
                           </div>
                         )}
                         <div className="flex-1 overflow-y-auto p-4">
                            <ReflectionLog taskId={taskId || ''} />
                         </div>
                     </div>
                )}
            </div>

                {/* Sidebar Status */}
                <div className="w-72 hidden xl:block bg-zinc-50 rounded-xl border border-zinc-200 p-5">
                    <h4 className="font-semibold text-zinc-900 mb-4">Status</h4>
                    <div className="space-y-4">
                        <div>
                            <span className="text-xs text-zinc-500 uppercase font-bold">Current State</span>
                            <div className={`mt-1 inline-block px-3 py-1 rounded-full text-sm font-medium border ${
                                status === 'completed' ? 'bg-green-100 text-green-700 border-green-200' :
                                status === 'failed' ? 'bg-red-100 text-red-700 border-red-200' :
                                isProcessing ? 'bg-blue-100 text-blue-700 border-blue-200 animate-pulse' :
                                'bg-zinc-100 text-zinc-600 border-zinc-200'
                            }`}>
                                {status.replace(/_/g, " ")}
                            </div>
                        </div>
                        
                        <div>
                             <span className="text-xs text-zinc-500 uppercase font-bold">Task ID</span>
                             <p className="text-xs font-mono bg-white p-2 border border-zinc-200 rounded mt-1 truncate">
                                 {taskId || "-"}
                             </p>
                        </div>
                        
                        <div>
                             <span className="text-xs text-zinc-500 uppercase font-bold">Progress</span>
                             <div className="w-full bg-zinc-200 rounded-full h-2 mt-2">
                                 <div 
                                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                                    style={{ width: `${progress}%` }}
                                 />
                             </div>
                             <p className="text-right text-xs text-zinc-500 mt-1">{Math.round(progress)}%</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
