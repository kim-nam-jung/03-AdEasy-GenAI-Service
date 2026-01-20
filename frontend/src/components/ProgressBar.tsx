import React from 'react';

interface ProgressBarProps {
  progress: number;
  currentStep: number;
  message?: string;
  status: string;
}

const STEPS = [
  "Preprocessing",
  "Understanding",
  "Planning",
  "ControlNet",
  "Keyframes",
  "Video Gen (1)",
  "Video Gen (2)",
  "Video Gen (3)",
  "Assembly",
  "Validation"
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
      
      {/* Current Step Text */}
      <div className="flex items-center justify-between text-[10px] text-zinc-400 font-mono border-t border-zinc-100 pt-2 mt-2">
         <span>{message || "Initializing..."}</span>
         <span>STEP {currentStep + 1}/{STEPS.length}</span>
      </div>
    </div>
  );
};
