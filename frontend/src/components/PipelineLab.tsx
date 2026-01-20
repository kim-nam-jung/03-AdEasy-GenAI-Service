import React, { useEffect, useState } from 'react';
import { usePipelineStore } from '../store/pipelineStore';
import { ImageUploader } from './ImageUploader';
import { api } from '../api/client';
import { useToastStore } from '../store/toastStore';

export const PipelineLab: React.FC = () => {
    // Global Store
    const {
        taskId, status, progress, logs,
        activeTab, isProcessing,
        visionResult, segmentationResult, rawVideoResult, finalResult,
        showFeedbackModal, feedbackQuestion, feedbackContext,
        
        setTaskId, setStatus, setProgress, addLog, clearLogs,
        setVisionResult, setSegmentationResult, setVideoResult, setFinalResult,
        setActiveTab, setIsProcessing,
        openFeedbackModal, closeFeedbackModal, resetPipeline
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

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Ensure we don't duplicate slashes if env var has/hasn't one
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const wsBase = apiUrl.replace(/^http/, protocol === 'wss:' ? 'wss' : 'ws'); 
        const wsUrl = `${wsBase}/ws/${taskId}`;
        
        console.log(`Connecting to WS: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => addLog(`[System] Connected to task stream: ${taskId}`);
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'log':
                        addLog(`[${data.level}] ${data.message}`);
                        break;
                    case 'progress':
                        setProgress(data.value);
                        if (data.status) setStatus(data.status);
                        break;
                    case 'status':
                        setStatus(data.status);
                        addLog(`[Status] Moved to ${data.status}`);
                        handleStatusUpdate(data);
                        break;
                    case 'human_input_request':
                        openFeedbackModal(data.question || "Guidance needed", data.context || "");
                        break;
                    case 'human_input_received':
                        closeFeedbackModal();
                        addLog("[Human] Feedback received, resuming...");
                        break;
                    case 'error':
                         addLog(`[Error] ${data.message}`);
                         setIsProcessing(false);
                         break;
                }
            } catch (e) {
                console.error("WS Parse Error", e);
            }
        };

        ws.onclose = () => addLog("[System] WebSocket Disconnected");
        ws.onerror = (e) => {
            console.error("WS Error", e);
            addLog("[Error] WebSocket connection failed");
        };

        return () => ws.close();
    }, [taskId]);

    // Parse status updates to populate results
    const handleStatusUpdate = (data: any) => {
         if (!data.data) return;
         
         if (data.status === 'vision_completed') {
             setVisionResult(data.data);
             setActiveTab('vision');
         } else if (data.status === 'step1_completed') {
             setSegmentationResult(data.data);
             setActiveTab('segmentation');
         } else if (data.status === 'step2_completed') {
             setVideoResult(data.data);
             setActiveTab('video');
         } else if (data.status === 'completed') {
             setFinalResult(data.data);
             setIsProcessing(false);
             addLog("[System] Pipeline Success!");
             addToast('success', "Pipeline Completed Successfully!");
             setActiveTab('result'); // Optional: switch to result tab
         } else if (data.status === 'failed') {
             addToast('error', "Pipeline Failed");
             setIsProcessing(false);
         }
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return addToast('warning', "Please select an image first.");
        
        resetPipeline();
        setIsProcessing(true);
        setActiveTab("logs"); // Switch to logs initially
        
        const formData = new FormData();
        selectedFiles.forEach((file) => formData.append("files", file));
        formData.append("prompt", prompt);
        
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/tasks/`, {
                method: "POST",
                body: formData
            });
            
            if (!res.ok) throw new Error("Upload failed");
            
            const data = await res.json();
            setTaskId(data.task_id);
            addLog(`[System] Task Initialized: ${data.task_id}`);
            
        } catch (err: any) {
            console.error(err);
            addLog(`[Error] Upload Failed: ${err.message}`);
            setIsProcessing(false);
            addToast('error', "Failed to start task: " + err.message);
        }
    };

    const submitFeedback = async () => {
        if (!taskId || !feedbackInput.trim()) return;
        
        try {
            const formData = new FormData();
            formData.append("feedback", feedbackInput);
            await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/tasks/${taskId}/feedback`, {
                method: "POST",
                body: formData
            });
            
            setFeedbackInput("");
            closeFeedbackModal();
            addLog("[System] Feedback submitted.");
            addToast('success', "Feedback submitted");
        } catch (err) {
            addToast('error', "Failed to submit feedback");
            console.error(err);
        }
    };

    const handleCleanup = async () => {
        try {
            await api.debugCleanup();
            addLog("[System] VRAM Cleared manually.");
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

            {/* Tabs */}
            <div className="flex border-b border-zinc-200 mb-6">
                {['upload', 'logs', 'vision', 'segmentation', 'video', 'result'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-5 py-2.5 text-sm font-medium capitalize border-b-2 transition-colors ${
                            activeTab === tab 
                            ? 'border-blue-600 text-blue-600' 
                            : 'border-transparent text-zinc-500 hover:text-zinc-700'
                        }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Main Content Area */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-1">
                    {activeTab === 'upload' && (
                        <div className="space-y-6 max-w-2xl">
                             <section className="bg-white p-6 rounded-xl border border-zinc-200 shadow-sm">
                                <h3 className="text-lg font-semibold mb-4">New Task</h3>
                                <div className="space-y-4">
                                    <ImageUploader onImagesSelected={setSelectedFiles} isLoading={isProcessing} />
                                    
                                    <div>
                                        <label className="block text-sm font-medium text-zinc-700 mb-1">Prompt (Optional)</label>
                                        <textarea
                                            className="w-full p-3 border border-zinc-200 rounded-lg h-24 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                                            placeholder="Describe the desired video motion and atmosphere..."
                                            value={prompt}
                                            onChange={(e) => setPrompt(e.target.value)}
                                        />
                                    </div>
                                    
                                    <button 
                                        onClick={handleUpload}
                                        disabled={isProcessing || selectedFiles.length === 0}
                                        className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 transition-all shadow-sm"
                                        data-debug-processing={isProcessing.toString()}
                                        data-debug-files={selectedFiles.length}
                                    >
                                        {console.log(`[DEBUG] Button State: isProcessing=${isProcessing}, files=${selectedFiles.length}`)}
                                        {isProcessing ? "Agent Working..." : "Start Agent Task"}
                                    </button>
                                </div>
                             </section>
                        </div>
                    )}

                    {activeTab === 'logs' && (
                         <div className="bg-zinc-900 text-zinc-300 p-4 rounded-xl font-mono text-xs h-full overflow-y-auto">
                            {logs.length === 0 ? <p className="text-zinc-600">No logs yet...</p> : logs.map((log, i) => (
                                <div key={i} className="mb-1 border-b border-zinc-800 pb-1 last:border-0">{log}</div>
                            ))}
                         </div>
                    )}
                    
                    {activeTab === 'vision' && (
                         <div className="space-y-4">
                            {visionResult ? (
                                <pre className="bg-zinc-50 p-4 rounded-xl text-xs font-mono border border-zinc-200 overflow-auto">
                                    {JSON.stringify(visionResult, null, 2)}
                                </pre>
                            ) : <div className="text-zinc-400 text-center py-10">No Vision Analysis data yet.</div>}
                         </div>
                    )}
                    
                    {activeTab === 'segmentation' && (
                         <div className="space-y-4">
                            {segmentationResult ? (
                                <div className="grid grid-cols-2 gap-4">
                                     {segmentationResult.segmented_layers?.map((layer: string, idx: number) => (
                                         <div key={idx} className="border border-zinc-200 p-2 rounded-lg">
                                             <img src={layer} alt={`Layer ${idx}`} className="w-full h-auto rounded" />
                                             <p className="text-xs text-center mt-1 text-zinc-500">Layer {idx}</p>
                                         </div>
                                     ))}
                                </div>
                            ) : <div className="text-zinc-400 text-center py-10">No Segmentation data yet.</div>}
                         </div>
                    )}

                    {activeTab === 'video' && (
                         <div className="space-y-4">
                            {rawVideoResult ? (
                                <div className="max-w-xl mx-auto">
                                     <h4 className="font-semibold mb-2">Raw Video</h4>
                                     <video controls src={rawVideoResult.raw_video_path} className="w-full rounded-lg shadow-lg" />
                                </div>
                            ) : <div className="text-zinc-400 text-center py-10">No Raw Video yet.</div>}
                         </div>
                    )}
                    
                    {activeTab === 'result' && (
                         <div className="space-y-4">
                            {finalResult ? (
                                <div className="max-w-xl mx-auto text-center">
                                     <h2 className="text-2xl font-bold text-green-600 mb-4">Final Output</h2>
                                     <video controls src={finalResult.video_path} poster={finalResult.thumbnail_path} className="w-full rounded-xl shadow-2xl border-4 border-green-100" />
                                     <p className="mt-4 text-zinc-600 text-sm">Task Completed Successfully</p>
                                </div>
                            ) : <div className="text-zinc-400 text-center py-10">No Final Result yet.</div>}
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
