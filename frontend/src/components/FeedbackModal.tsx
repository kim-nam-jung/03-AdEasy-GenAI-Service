import React, { useState } from 'react';
import { usePipelineStore } from '../store/pipelineStore';
import { useToastStore } from '../store/toastStore';
import { API_URL } from '../api/config';

export const FeedbackModal: React.FC = () => {
    const { 
        taskId, 
        showFeedbackModal, 
        feedbackQuestion, 
        feedbackContext, 
        closeFeedbackModal 
    } = usePipelineStore();
    
    const { addToast } = useToastStore();
    const [feedbackInput, setFeedbackInput] = useState("");

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

    if (!showFeedbackModal) return null;

    return (
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
    );
};
