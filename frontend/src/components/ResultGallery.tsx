import React from 'react';

interface ResultGalleryProps {
  videoPath?: string;
  thumbnailPath?: string;
  taskId: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ResultGallery: React.FC<ResultGalleryProps> = ({ videoPath, thumbnailPath, taskId }) => {
  if (!videoPath) return null;

  // Construct full URLs
  // videoPath from backend is like "outputs/{task_id}/final.mp4"
  // API_URL might be "http://localhost:8000"
  // So full URL: "http://localhost:8000/outputs/..."
  const fullVideoUrl = `${API_URL}/${videoPath}`;
  const fullThumbnailUrl = thumbnailPath ? `${API_URL}/${thumbnailPath}` : undefined;

  return (
    <div className="w-full mt-8 animate-fade-in text-center">
      <h2 className="text-xl font-bold text-gray-800 mb-4">🎉 Generation Complete!</h2>
      
      <div className="bg-black rounded-lg overflow-hidden shadow-2xl mx-auto max-w-sm">
        <video 
            src={fullVideoUrl}
            poster={fullThumbnailUrl}
            controls
            autoPlay
            loop
            className="w-full h-auto"
        />
      </div>
      
      <div className="mt-6 flex justify-center gap-4">
        <a 
            href={fullVideoUrl} 
            download={`adeasy_${taskId}.mp4`}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow flex items-center gap-2"
        >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Video
        </a>
      </div>
    </div>
  );
};
