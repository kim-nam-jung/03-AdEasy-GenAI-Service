import React, { useState } from 'react';

interface ImageUploaderProps {
  onImagesSelected: (files: File[]) => void;
  isLoading: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onImagesSelected, isLoading }) => {
  const [previews, setPreviews] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      processFiles(files);
    }
  };

  const processFiles = (files: File[]) => {
    if (files.length > 4) {
      alert("Maximum 4 images allowed");
      return;
    }

    const newPreviews = files.map(file => URL.createObjectURL(file));
    setPreviews(newPreviews);
    onImagesSelected(files);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (isLoading) return;
    
    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/'));
      processFiles(files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
           <label className="text-sm font-semibold text-zinc-900">Source Assets</label>
           <span className="text-xs text-zinc-500 font-mono">MAX 4</span>
      </div>
      
      <div 
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`group relative h-48 w-full border border-dashed rounded-lg transition-all duration-200 flex flex-col items-center justify-center cursor-pointer ${
          isLoading 
            ? 'bg-zinc-50 border-zinc-200 cursor-not-allowed opacity-60' 
            : isDragging
                ? 'bg-blue-50/50 border-blue-500 shadow-inner'
                : 'bg-white border-zinc-300 hover:border-zinc-500 hover:bg-zinc-50/50'
        }`}
      >
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handleFileChange}
          disabled={isLoading}
          className="hidden"
          id="file-upload"
        />
        
        {previews.length > 0 ? (
             <div className="absolute inset-2 flex gap-2 overflow-hidden pointer-events-none">
                 {previews.map((src, idx) => (
                    <div key={idx} className="h-full aspect-square rounded-md overflow-hidden border border-zinc-200 shadow-sm relative">
                        <img src={src} alt="" className="w-full h-full object-cover" />
                        <div className="absolute bottom-1 right-1 bg-black/60 text-white text-[10px] px-1.5 py-0.5 rounded font-mono">
                            0{idx + 1}
                        </div>
                    </div>
                ))}
             </div>
        ) : (
            <label htmlFor="file-upload" className="w-full h-full flex flex-col items-center justify-center cursor-pointer p-6 text-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-3 transition-colors ${isDragging ? 'bg-blue-100 text-blue-600' : 'bg-zinc-100 text-zinc-400 group-hover:bg-zinc-200'}`}>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
                </div>
                <p className="text-sm font-medium text-zinc-700">Drop files here or click to upload</p>
                <p className="text-xs text-zinc-400 mt-1">Supports JPG, PNG, WebP</p>
            </label>
        )}
      </div>
    </div>
  );
};
