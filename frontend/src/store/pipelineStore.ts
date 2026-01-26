import { create } from 'zustand';

// Define types reflecting backend responses
export interface VisionAnalysis {
  product_name: string;
  category: string;
  visual_characteristics: string[];
  suggested_video_prompt: string;
  segmentation_hint: string;
}

export interface SegmentationResult {
  segmented_layers: string[];
  main_product_layer: string;
}

export interface VideoResult {
  raw_video_path: string;
}

export interface FinalResult {
  video_path: string;
  thumbnail_path: string;
  metadata: Record<string, any>;
}

interface PipelineState {
  // Task State
  taskId: string | null;
  status: string; // 'idle' | 'processing' | 'completed' | 'failed' | 'paused'
  progress: number;
  logs: string[];
  
  // Data State
  visionResult: VisionAnalysis | null;
  segmentationResult: SegmentationResult | null;
  rawVideoResult: VideoResult | null;
  finalResult: FinalResult | null;
  
  // UI State
  activeTab: string;
  isProcessing: boolean;
  
  // Human-in-the-loop State
  showFeedbackModal: boolean;
  feedbackQuestion: string;
  feedbackContext: string;

  // Actions
  setTaskId: (id: string) => void;
  setStatus: (status: string) => void;
  setProgress: (progress: number) => void;
  addLog: (log: string) => void;
  clearLogs: () => void;
  
  setVisionResult: (result: VisionAnalysis) => void;
  setSegmentationResult: (result: SegmentationResult) => void;
  setVideoResult: (result: VideoResult) => void;
  setFinalResult: (result: FinalResult) => void;
  
  setActiveTab: (tab: string) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  
  openFeedbackModal: (question: string, context: string) => void;
  closeFeedbackModal: () => void;
  
  updateTaskStatus: (updates: {
    status?: string;
    progress?: number;
    visionResult?: VisionAnalysis;
    segmentationResult?: SegmentationResult;
    rawVideoResult?: VideoResult;
    finalResult?: FinalResult;
    isProcessing?: boolean;
    activeTab?: string;
  }) => void;
  
  resetPipeline: () => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  taskId: null,
  status: 'idle',
  progress: 0,
  logs: [],
  
  visionResult: null,
  segmentationResult: null,
  rawVideoResult: null,
  finalResult: null,
  
  activeTab: 'upload',
  isProcessing: false,
  
  showFeedbackModal: false,
  feedbackQuestion: "",
  feedbackContext: "",

  setTaskId: (id) => set({ taskId: id }),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  addLog: (log) => set((state) => ({ logs: [...state.logs, log] })),
  clearLogs: () => set({ logs: [] }),
  
  setVisionResult: (result) => set({ visionResult: result }),
  setSegmentationResult: (result) => set({ segmentationResult: result }),
  setVideoResult: (result) => set({ rawVideoResult: result }),
  setFinalResult: (result) => set({ finalResult: result }),
  
  setActiveTab: (tab) => set({ activeTab: tab }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
  
  openFeedbackModal: (question, context) => set({ 
    showFeedbackModal: true, 
    feedbackQuestion: question, 
    feedbackContext: context 
  }),
  closeFeedbackModal: () => set({ showFeedbackModal: false }),
  
  updateTaskStatus: (updates) => set((state) => ({ ...state, ...updates })),
  
  resetPipeline: () => set({
    taskId: null,
    status: 'idle',
    progress: 0,
    logs: [],
    visionResult: null,
    segmentationResult: null,
    rawVideoResult: null,
    finalResult: null,
    isProcessing: false,
    activeTab: 'upload',
    showFeedbackModal: false
  })
}));
