import React, { useState } from 'react';

interface ImageUploaderProps {
  onImagesSelected: (files: File[]) => void;
  isLoading: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onImagesSelected, isLoading }) => {
  const [previews, setPreviews] = useState<string[]>([]);

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
    if (isLoading) return;
    
    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/'));
      processFiles(files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="w-full space-y-6">
      <div 
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`group border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-300 ${
          isLoading 
            ? 'bg-slate-50 border-slate-200 cursor-not-allowed opacity-50' 
            : 'border-indigo-200 bg-indigo-50/50 hover:border-indigo-500 hover:bg-indigo-50 cursor-pointer hover:shadow-lg hover:shadow-indigo-500/10'
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
        <label htmlFor="file-upload" className="w-full h-full flex flex-col items-center justify-center cursor-pointer">
          <div className="w-16 h-16 bg-white rounded-full shadow-md flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
             <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
             </svg>
          </div>
          <span className="text-slate-700 font-semibold text-lg mb-1 group-hover:text-indigo-700 transition-colors">
            Click to upload or drag and drop
          </span>
          <span className="text-slate-400 text-sm">
            Max 4 Images (JPG, PNG, WebP)
          </span>
        </label>
      </div>

      {previews.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in">
          {previews.map((src, idx) => (
            <div key={idx} className="relative aspect-square rounded-xl overflow-hidden border border-slate-200 shadow-sm group">
                <img src={src} alt={`preview ${idx}`} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="text-white font-medium text-sm bg-black/50 px-3 py-1 rounded-full backdrop-blur-sm">Image {idx + 1}</span>
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
