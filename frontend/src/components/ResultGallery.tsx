import React from 'react';

interface ResultGalleryProps {
  videoPath?: string;
  thumbnailPath?: string;
  taskId: string;
}

import { API_URL } from '../api/config';

export const ResultGallery: React.FC<ResultGalleryProps> = ({ videoPath, thumbnailPath, taskId }) => {
  if (!videoPath) return null;

  // Construct full URLs
  const fullVideoUrl = `${API_URL}/${videoPath}`;
  const fullThumbnailUrl = thumbnailPath ? `${API_URL}/${thumbnailPath}` : undefined;

  return (
    <div className="w-full mt-12 text-center relative group">
       <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-indigo-500/20 blur-[100px] rounded-full -z-10" />

      <h2 className="text-3xl font-extrabold text-slate-800 mb-8 tracking-tight">
        <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-blue-500">
            Vision Realized.
        </span>
      </h2>
      
      <div className="relative mx-auto max-w-sm rounded-[2rem] p-2 bg-gradient-to-b from-white/80 to-white/40 shadow-2xl backdrop-blur-xl border border-white/60">
        <div className="rounded-[1.5rem] overflow-hidden shadow-inner bg-black aspect-[9/16] relative">
            <video 
                src={fullVideoUrl}
                poster={fullThumbnailUrl}
                controls
                autoPlay
                loop
                className="w-full h-full object-cover"
            />
        </div>
      </div>
      
      <div className="mt-10 flex justify-center gap-4">
        <a 
            href={fullVideoUrl} 
            download={`adeasy_${taskId}.mp4`}
            className="group relative px-8 py-3 bg-indigo-600 text-white font-bold rounded-full shadow-lg shadow-indigo-600/30 overflow-hidden transition-all hover:scale-105 hover:bg-indigo-700 active:scale-95"
        >
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]"></div>
            <span className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Video
            </span>
        </a>
      </div>
    </div>
  );
};
