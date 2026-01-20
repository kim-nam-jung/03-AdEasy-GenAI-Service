import React, { useState } from 'react';
import { api } from '../api/client';
import { ImageUploader } from './ImageUploader';

export const PipelineLab: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'step1' | 'step2' | 'step3'>('step1');

    // Step 1 State - Segmentation
    const [s1Files, setS1Files] = useState<File[]>([]);
    const [s1NumLayers, setS1NumLayers] = useState<number>(4);
    const [s1Resolution, setS1Resolution] = useState<number>(640);
    const [s1Loading, setS1Loading] = useState(false);
    const [s1Result, setS1Result] = useState<any>(null);

    // Step 2 State - Video Generation
    const [s2ImagePath, setS2ImagePath] = useState<string>("");
    const [s2Prompt, setS2Prompt] = useState<string>("");
    const [s2NumFrames, setS2NumFrames] = useState<number>(96);
    const [s2Loading, setS2Loading] = useState(false);
    const [s2Result, setS2Result] = useState<any>(null);

    // Step 3 State - Post-processing
    const [s3VideoPath, setS3VideoPath] = useState<string>("");
    const [s3RifeEnabled, setS3RifeEnabled] = useState<boolean>(true);
    const [s3CuganEnabled, setS3CuganEnabled] = useState<boolean>(true);
    const [s3Loading, setS3Loading] = useState(false);
    const [s3Result, setS3Result] = useState<any>(null);

    const handleRunStep1 = async () => {
        if (s1Files.length === 0) return alert("Please upload an image");
        
        try {
            setS1Loading(true);
            setS1Result(null);
            
            const res = await api.debugStep1Segmentation(s1Files[0], s1NumLayers, s1Resolution);
            setS1Result(res.result);
            
            // Auto-fill Step 2 image path
            if (res.result?.main_product_layer) {
                setS2ImagePath(res.result.main_product_layer);
            }
            
        } catch (e: any) {
            alert(e.message);
        } finally {
            setS1Loading(false);
        }
    };

    const handleRunStep2 = async () => {
        if (!s2ImagePath) return alert("Please provide an image path");
        if (!s2Prompt) return alert("Please provide a prompt");

        try {
            setS2Loading(true);
            setS2Result(null);
            
            const res = await api.debugStep2VideoGeneration(s2ImagePath, s2Prompt, s2NumFrames);
            setS2Result(res.result);
            
            // Auto-fill Step 3 video path
            if (res.result?.raw_video_path) {
                setS3VideoPath(res.result.raw_video_path);
            }
        } catch (e: any) {
            alert(e.message);
        } finally {
            setS2Loading(false);
        }
    };

    const handleRunStep3 = async () => {
        if (!s3VideoPath) return alert("Please provide a video path");

        try {
            setS3Loading(true);
            setS3Result(null);
            
            const res = await api.debugStep3Postprocess(s3VideoPath, s3RifeEnabled, s3CuganEnabled);
            setS3Result(res.result);
            
        } catch (e: any) {
            alert(e.message);
        } finally {
            setS3Loading(false);
        }
    };

    const handleCleanup = async () => {
        try {
            await api.debugCleanup();
            alert("VRAM Cleanup successful");
        } catch (e: any) {
            alert(e.message);
        }
    };

    return (
        <div className="flex flex-col h-full animate-fade-in">
            <div className="mb-6 flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Pipeline Lab</h1>
                    <p className="text-zinc-500 text-sm mt-1">Debug the 3-step video generation pipeline.</p>
                </div>
                <button 
                    onClick={handleCleanup}
                    className="px-3 py-1.5 text-xs font-medium text-zinc-600 border border-zinc-200 rounded-lg hover:bg-zinc-50 transition-colors"
                >
                    Clear VRAM
                </button>
            </div>

            {/* Tabs - 3 Steps */}
            <div className="flex border-b border-zinc-200 mb-6">
                <button 
                    onClick={() => setActiveTab('step1')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'step1' ? 'border-blue-600 text-blue-600' : 'border-transparent text-zinc-500 hover:text-zinc-700'}`}
                >
                    1. Segmentation
                </button>
                <button 
                    onClick={() => setActiveTab('step2')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'step2' ? 'border-blue-600 text-blue-600' : 'border-transparent text-zinc-500 hover:text-zinc-700'}`}
                >
                    2. Video Generation
                </button>
                <button 
                    onClick={() => setActiveTab('step3')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'step3' ? 'border-blue-600 text-blue-600' : 'border-transparent text-zinc-500 hover:text-zinc-700'}`}
                >
                    3. Post-processing
                </button>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* --- INPUT PANEL --- */}
                <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-6">
                    {activeTab === 'step1' ? (
                        <>
                             <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Input Image</h3>
                                <ImageUploader onImagesSelected={setS1Files} isLoading={s1Loading} />
                            </section>
                            
                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Segmentation Config</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm text-zinc-500 block mb-1">Layers (3-8)</label>
                                        <input 
                                            type="number" 
                                            min={3} max={8}
                                            className="w-full p-2 bg-white border border-zinc-200 rounded-lg text-sm"
                                            value={s1NumLayers}
                                            onChange={e => setS1NumLayers(Number(e.target.value))}
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm text-zinc-500 block mb-1">Resolution</label>
                                        <select 
                                            className="w-full p-2 bg-white border border-zinc-200 rounded-lg text-sm"
                                            value={s1Resolution}
                                            onChange={e => setS1Resolution(Number(e.target.value))}
                                        >
                                            <option value={640}>640 (Recommended)</option>
                                            <option value={1024}>1024 (High Quality)</option>
                                        </select>
                                    </div>
                                </div>
                            </section>

                            <button 
                                onClick={handleRunStep1}
                                disabled={s1Loading || s1Files.length === 0}
                                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-all"
                            >
                                {s1Loading ? "Segmenting..." : "Run Segmentation"}
                            </button>
                        </>
                    ) : activeTab === 'step2' ? (
                        <>
                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Layer Image Path</h3>
                                <input 
                                    type="text"
                                    className="w-full p-3 bg-white border border-zinc-200 rounded-lg text-sm font-mono"
                                    placeholder="/path/to/segmented/layer_0.png"
                                    value={s2ImagePath}
                                    onChange={e => setS2ImagePath(e.target.value)}
                                />
                            </section>

                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Video Prompt</h3>
                                <textarea 
                                    className="w-full p-3 bg-white border border-zinc-200 rounded-lg text-sm h-24"
                                    placeholder="A product rotating slowly with soft lighting..."
                                    value={s2Prompt}
                                    onChange={e => setS2Prompt(e.target.value)}
                                />
                            </section>
                            
                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Frames</h3>
                                <input 
                                    type="number" 
                                    min={24} max={197} step={1}
                                    className="w-full p-2 bg-white border border-zinc-200 rounded-lg text-sm"
                                    value={s2NumFrames}
                                    onChange={e => setS2NumFrames(Number(e.target.value))}
                                />
                                <p className="text-xs text-zinc-400">Recommended: 96 frames (4 seconds @ 24fps)</p>
                            </section>

                             <button 
                                onClick={handleRunStep2}
                                disabled={s2Loading || !s2ImagePath || !s2Prompt}
                                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-all"
                            >
                                {s2Loading ? "Generating..." : "Generate Video"}
                            </button>
                        </>
                    ) : (
                        <>
                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Raw Video Path</h3>
                                <input 
                                    type="text"
                                    className="w-full p-3 bg-white border border-zinc-200 rounded-lg text-sm font-mono"
                                    placeholder="/path/to/raw_video.mp4"
                                    value={s3VideoPath}
                                    onChange={e => setS3VideoPath(e.target.value)}
                                />
                            </section>

                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Enhancement Options</h3>
                                <div className="space-y-3">
                                    <label className="flex items-center gap-3 cursor-pointer">
                                        <input 
                                            type="checkbox" 
                                            checked={s3RifeEnabled}
                                            onChange={e => setS3RifeEnabled(e.target.checked)}
                                            className="w-4 h-4 rounded border-zinc-300"
                                        />
                                        <span className="text-sm">RIFE Frame Interpolation (24fps → 48fps)</span>
                                    </label>
                                    <label className="flex items-center gap-3 cursor-pointer">
                                        <input 
                                            type="checkbox" 
                                            checked={s3CuganEnabled}
                                            onChange={e => setS3CuganEnabled(e.target.checked)}
                                            className="w-4 h-4 rounded border-zinc-300"
                                        />
                                        <span className="text-sm">Real-CUGAN Upscaling (2x)</span>
                                    </label>
                                </div>
                            </section>

                             <button 
                                onClick={handleRunStep3}
                                disabled={s3Loading || !s3VideoPath}
                                className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-all"
                            >
                                {s3Loading ? "Processing..." : "Run Post-processing"}
                            </button>
                        </>
                    )}
                </div>

                {/* --- OUTPUT PANEL --- */}
                <div className="flex-1 bg-zinc-50 rounded-xl border border-zinc-200 p-6 overflow-hidden flex flex-col">
                    <div className="flex justify-between items-center mb-4">
                         <h3 className="font-semibold text-zinc-900">Output Result</h3>
                         <span className="text-xs text-zinc-400 font-mono">JSON RESPONSE</span>
                    </div>
                    
                    <div className="flex-1 overflow-auto custom-scrollbar bg-white rounded-lg border border-zinc-200 p-4">
                        {(activeTab === 'step1' ? s1Result : activeTab === 'step2' ? s2Result : s3Result) ? (
                            <pre className="text-xs font-mono text-zinc-600 whitespace-pre-wrap">
                                {JSON.stringify(activeTab === 'step1' ? s1Result : activeTab === 'step2' ? s2Result : s3Result, null, 2)}
                            </pre>
                        ) : (
                            <div className="h-full flex items-center justify-center text-zinc-400 text-sm">
                                No result yet. Run the step to see output.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
