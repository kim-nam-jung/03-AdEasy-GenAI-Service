import React, { useState, useRef } from 'react';

interface InputBarProps {
  onSend: (files: File[], prompt: string) => void;
  isLoading: boolean;
}

export const InputBar: React.FC<InputBarProps> = ({ onSend, isLoading }) => {
  const [prompt, setPrompt] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const newFiles = [...selectedFiles, ...files].slice(0, 4);
    setSelectedFiles(newFiles);

    // Create previews
    const newPreviews = newFiles.map(f => URL.createObjectURL(f));
    setPreviews(newPreviews);
  };

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    const newPreviews = previews.filter((_, i) => i !== index);
    setPreviews(newPreviews);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading || (prompt.trim() === "" && selectedFiles.length === 0)) return;
    onSend(selectedFiles, prompt);
    setPrompt("");
    setSelectedFiles([]);
    setPreviews([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="fixed bottom-0 left-[260px] right-0 bg-gradient-to-t from-white via-white to-transparent pt-12 pb-8 px-8 z-50 transition-all duration-300">
      <div className="max-w-3xl mx-auto w-full">
        <form 
          onSubmit={handleSubmit}
          className="bg-white border border-zinc-200 rounded-2xl shadow-xl shadow-zinc-200/40 p-2 focus-within:ring-1 focus-within:ring-zinc-400 focus-within:border-zinc-400 transition-all"
        >
          {/* Previews Area */}
          {previews.length > 0 && (
            <div className="flex gap-2 p-2 px-3 overflow-x-auto">
              {previews.map((url, i) => (
                <div key={i} className="relative group shrink-0">
                  <img src={url} alt="preview" className="w-16 h-16 rounded-xl object-cover border border-zinc-200 shadow-sm" />
                  <button 
                    onClick={() => removeFile(i)}
                    className="absolute -top-2 -right-2 bg-zinc-900 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center gap-2 pr-2">
            <button 
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-3 text-zinc-500 hover:text-zinc-900 transition-colors"
              disabled={isLoading || selectedFiles.length >= 4}
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
              </svg>
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                multiple 
                accept="image/*" 
                onChange={handleFileChange}
              />
            </button>

            <textarea 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="제작하고 싶은 영상에 대해 설명해 주세요..."
              className="flex-1 max-h-48 py-3 bg-transparent outline-none resize-none text-[15px] placeholder:text-zinc-400 text-zinc-800 scrollbar-hide"
              rows={1}
              style={{ height: 'auto' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = `${target.scrollHeight}px`;
              }}
              disabled={isLoading}
            />

            <button 
              type="submit"
              disabled={isLoading || (prompt.trim() === "" && selectedFiles.length === 0)}
              className={`p-2.5 rounded-xl transition-all ${
                isLoading || (prompt.trim() === "" && selectedFiles.length === 0)
                ? 'bg-zinc-100 text-zinc-300 pointer-events-none'
                : 'bg-zinc-900 text-white hover:bg-black active:scale-95 shadow-md'
              }`}
            >
              <svg className="w-5 h-5 translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </form>
        <p className="text-[10px] text-zinc-400 text-center mt-3 uppercase tracking-wider font-semibold">
           AdEasy GenAI Service · Step-by-Step Pipeline
        </p>
      </div>
    </div>
  );
};
