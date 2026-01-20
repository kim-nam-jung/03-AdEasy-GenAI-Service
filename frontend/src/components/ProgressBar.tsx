import React from 'react';

interface ProgressBarProps {
  progress: number;
  currentStep: number;
  message?: string;
  status: string;
}

// Updated for 3-step simplified pipeline
const STEPS = [
  "Segmentation",    // Step 1: Qwen-Image-Layered
  "Video Generation", // Step 2: LTX-Video
  "Post-processing"   // Step 3: RIFE + Real-CUGAN
];

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, currentStep, message, status }) => {
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
         <div className="flex items-center gap-2">
             <div className={`w-2 h-2 rounded-full ${status === 'completed' ? 'bg-green-500' : status === 'failed' ? 'bg-red-500' : 'bg-blue-500 animate-pulse'}`} />
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                {status === 'failed' ? 'Failed' : status === 'completed' ? 'Done' : 'Processing'}
            </span>
         </div>
         <span className="text-xs font-mono text-zinc-400">{progress}%</span>
      </div>
      
      {/* Tracker */}
      <div className="w-full bg-zinc-100 rounded-full h-1 overflow-hidden mb-3">
        <div 
          className={`h-full transition-all duration-500 ease-out ${
            status === 'failed' ? 'bg-red-500' : 
            status === 'completed' ? 'bg-green-500' : 
            'bg-blue-600'
          }`}
          style={{ width: `${Math.max(2, progress)}%` }}
        />
      </div>
      
      {/* Step Indicators */}
      <div className="flex justify-between mb-3">
        {STEPS.map((step, idx) => (
          <div key={step} className="flex flex-col items-center">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-all ${
              idx < currentStep 
                ? 'bg-green-500 text-white' 
                : idx === currentStep 
                  ? 'bg-blue-600 text-white ring-2 ring-blue-200' 
                  : 'bg-zinc-200 text-zinc-500'
            }`}>
              {idx < currentStep ? '✓' : idx + 1}
            </div>
            <span className={`text-[10px] mt-1 ${idx === currentStep ? 'text-blue-600 font-medium' : 'text-zinc-400'}`}>
              {step}
            </span>
          </div>
        ))}
      </div>
      
      {/* Current Step Text */}
      <div className="flex items-center justify-between text-[10px] text-zinc-400 font-mono border-t border-zinc-100 pt-2 mt-2">
         <span>{message || "Initializing..."}</span>
         <span>STEP {Math.min(currentStep + 1, STEPS.length)}/{STEPS.length}</span>
      </div>
    </div>
  );
};
