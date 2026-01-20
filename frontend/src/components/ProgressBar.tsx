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
    <div className="w-full bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6">
      <div className="flex justify-between items-center mb-2">
        <span className={`font-semibold ${status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>
          {status === 'failed' ? 'Failed' : status === 'completed' ? 'Completed' : 'Processing...'}
        </span>
        <span className="text-gray-500 text-sm font-mono">{progress}%</span>
      </div>
      
      {/* Main Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden mb-4">
        <div 
          className={`h-full transition-all duration-500 ease-out ${
            status === 'failed' ? 'bg-red-500' : 
            status === 'completed' ? 'bg-green-500' : 
            'bg-blue-600 animate-pulse'
          }`}
          style={{ width: `${Math.max(5, progress)}%` }}
        />
      </div>
      
      {/* Message */}
      <p className="text-gray-600 text-sm mb-6 text-center italic">{message || "Waiting..."}</p>
      
      {/* Steps Visualization */}
      <div className="flex justify-between items-end h-20 text-xs">
        {STEPS.map((label, idx) => {
            const isActive = idx === currentStep;
            const isCompleted = idx < currentStep || status === 'completed';
            
            return (
                <div key={idx} className="flex flex-col items-center flex-1 group">
                    <div className={`w-3 h-3 rounded-full mb-2 transition-colors ${
                        isActive ? 'bg-blue-600 scale-125 ring-4 ring-blue-100' : 
                        isCompleted ? 'bg-green-500' : 
                        'bg-gray-300'
                    }`} />
                    <span className={`text-center transition-colors hidden sm:block ${
                        isActive ? 'text-blue-700 font-bold' : 
                        isCompleted ? 'text-green-600' : 
                        'text-gray-400'
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
