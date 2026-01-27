import { useCallback } from 'react';
import { useWebSocketManager } from './useWebSocketManager';
import { usePipelineStore } from '../store/pipelineStore';
import { useToastStore } from '../store/toastStore';
import { TaskEvent } from '../types/websocket';

export function useTaskWebSocket(taskId: string | null) {
    const { 
        updateTaskStatus, 
        setIsProcessing, 
        openFeedbackModal, 
        closeFeedbackModal,
        status 
    } = usePipelineStore();
    
    const { addToast } = useToastStore();

    const handleMessage = useCallback((msgData: TaskEvent) => {
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
                
                const updates: any = { status: msgData.status };
                if (msgData.status === 'completed') {
                    updates.isProcessing = false;
                    addToast('success', "Pipeline Completed Successfully!");
                } else if (msgData.status === 'failed') {
                    updates.isProcessing = false;
                    addToast('error', "Pipeline Failed");
                }
                updateTaskStatus(updates);
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
    }, [status, updateTaskStatus, openFeedbackModal, closeFeedbackModal, setIsProcessing, addToast]);

    const { isConnected } = useWebSocketManager(
        taskId ? `/ws/${taskId}` : null,
        handleMessage
    );

    return { isConnected };
}
