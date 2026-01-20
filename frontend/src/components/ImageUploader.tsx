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
    <div className="w-full space-y-4">
      <div 
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isLoading ? 'bg-gray-100 border-gray-300 cursor-not-allowed' : 'border-blue-300 hover:border-blue-500 hover:bg-blue-50 cursor-pointer'
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
          <svg className="w-12 h-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="text-gray-600 font-medium">
            Click to upload or drag and drop
          </span>
          <span className="text-gray-400 text-sm mt-1">
            Max 4 IMAGES (JPG, PNG, WebP)
          </span>
        </label>
      </div>

      {previews.length > 0 && (
        <div className="grid grid-cols-4 gap-4 mt-4">
          {previews.map((src, idx) => (
            <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 shadow-sm">
                <img src={src} alt={`preview ${idx}`} className="w-full h-full object-cover" />
                <div className="absolute top-0 left-0 bg-black/50 text-white text-xs px-2 py-1">
                    {idx + 1}
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
