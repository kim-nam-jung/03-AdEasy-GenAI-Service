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
    <div className="w-full bg-white/50 backdrop-blur-sm p-8 rounded-2xl shadow-sm border border-white/60">
      <div className="flex justify-between items-center mb-4">
        <span className={`font-bold text-lg ${status === 'failed' ? 'text-red-600' : 'text-indigo-600'}`}>
          {status === 'failed' ? 'Generation Failed' : status === 'completed' ? 'Generation Complete' : 'Generating Video...'}
        </span>
        <span className="text-slate-500 font-mono font-medium">{progress}%</span>
      </div>
      
      {/* Main Progress Bar */}
      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden mb-6">
        <div 
          className={`h-full transition-all duration-700 ease-out ${
            status === 'failed' ? 'bg-red-500' : 
            status === 'completed' ? 'bg-emerald-500' : 
            'bg-indigo-600 shimmer-effect'
          }`}
          style={{ width: `${Math.max(5, progress)}%` }}
        />
      </div>
      
      {/* Message */}
      <p className="text-slate-600 text-sm mb-8 text-center italic opacity-80 animate-pulse">{message || "Waiting..."}</p>
      
      {/* Steps Visualization */}
      <div className="relative flex justify-between items-start w-full">
         {/* Connector Line */}
         <div className="absolute top-[5px] left-0 w-full h-[2px] bg-slate-200 -z-10" />

        {STEPS.map((label, idx) => {
            const isActive = idx === currentStep;
            const isCompleted = idx < currentStep || status === 'completed';
            
            // Only show checking/active for main milestones to avoid clutter if many steps
            // Or show all but make them small
            
            return (
                <div key={idx} className="flex flex-col items-center flex-1 group">
                    <div className={`w-3 h-3 rounded-full transition-all duration-300 z-10 ${
                        isActive ? 'bg-indigo-600 scale-150 ring-4 ring-indigo-100' : 
                        isCompleted ? 'bg-indigo-400' : 
                        'bg-slate-300'
                    }`} />
                    <span className={`text-[10px] sm:text-xs mt-3 text-center transition-colors px-1 ${
                        isActive ? 'text-indigo-700 font-bold' : 
                        isCompleted ? 'text-indigo-400' : 
                        'text-slate-400'
                    }`}>
                        {label}
                    </span>
                </div>
            )
        })}
      </div>
    </div>
  );
};
