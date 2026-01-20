import React, { useState } from 'react';
import { api } from '../api/client';
import { ImageUploader } from './ImageUploader';

export const PipelineLab: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'step1' | 'step2'>('step1');

    // Step 1 State
    const [s1Files, setS1Files] = useState<File[]>([]);
    const [s1Prompt, setS1Prompt] = useState<string>("");
    const [s1Loading, setS1Loading] = useState(false);
    const [s1Result, setS1Result] = useState<any>(null);

    // Step 2 State
    const [s2Files, setS2Files] = useState<File[]>([]);
    const [s2AnalysisJson, setS2AnalysisJson] = useState<string>("");
    const [s2Prompt, setS2Prompt] = useState<string>("");
    const [s2Loading, setS2Loading] = useState(false);
    const [s2Result, setS2Result] = useState<any>(null);

    const handleRunStep1 = async () => {
        if (s1Files.length === 0) return alert("Please upload an image");
        
        try {
            setS1Loading(true);
            setS1Result(null);
            const res = await api.debugAnalyzeStep1(s1Files[0], s1Prompt);
            setS1Result(res.result);
            
            // Auto-populate Step 2
            setS2Files([s1Files[0]]);
            setS2AnalysisJson(JSON.stringify(res.result, null, 2));
            
        } catch (e: any) {
            alert(e.message);
        } finally {
            setS1Loading(false);
        }
    };

    const handleRunStep2 = async () => {
        if (s2Files.length === 0) return alert("Please upload an image");
        if (!s2AnalysisJson) return alert("Please provide analysis JSON");

        try {
            setS2Loading(true);
            setS2Result(null);
            const analysisData = JSON.parse(s2AnalysisJson);
            const res = await api.debugPlanStep2(s2Files[0], analysisData, s2Prompt);
            setS2Result(res.result);
        } catch (e: any) {
            alert(e.message);
        } finally {
            setS2Loading(false);
        }
    };

    return (
        <div className="flex flex-col h-full animate-fade-in">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-zinc-900 tracking-tight">Pipeline Lab</h1>
                <p className="text-zinc-500 text-sm mt-1">Debug individual generation steps in isolation.</p>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-zinc-200 mb-6">
                <button 
                    onClick={() => setActiveTab('step1')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'step1' ? 'border-zinc-900 text-zinc-900' : 'border-transparent text-zinc-500 hover:text-zinc-700'}`}
                >
                    1. Analysis & Augmentation
                </button>
                <button 
                    onClick={() => setActiveTab('step2')}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'step2' ? 'border-zinc-900 text-zinc-900' : 'border-transparent text-zinc-500 hover:text-zinc-700'}`}
                >
                    2. Scenario Planning
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
                                <h3 className="font-semibold text-zinc-900">User Prompt (Optional)</h3>
                                <textarea 
                                    className="w-full p-3 bg-white border border-zinc-200 rounded-lg text-sm font-mono h-24 focus:ring-2 focus:ring-blue-500/20 outline-none"
                                    placeholder="E.g. Focus on the organic ingredients..."
                                    value={s1Prompt}
                                    onChange={e => setS1Prompt(e.target.value)}
                                />
                            </section>

                            <button 
                                onClick={handleRunStep1}
                                disabled={s1Loading || s1Files.length === 0}
                                className="w-full py-3 bg-zinc-900 text-white rounded-lg font-medium hover:bg-black disabled:opacity-50 transition-all"
                            >
                                {s1Loading ? "Analyzing..." : "Run Analysis"}
                            </button>
                        </>
                    ) : (
                        <>
                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Input Image (Context)</h3>
                                <ImageUploader onImagesSelected={setS2Files} isLoading={s2Loading} />
                            </section>

                            <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Analysis JSON (from Step 1)</h3>
                                <textarea 
                                    className="w-full p-3 bg-zinc-50 border border-zinc-200 rounded-lg text-xs font-mono h-48 focus:ring-2 focus:ring-blue-500/20 outline-none"
                                    placeholder="{ 'main_object': ... }"
                                    value={s2AnalysisJson}
                                    onChange={e => setS2AnalysisJson(e.target.value)}
                                />
                            </section>
                            
                             <section className="space-y-4">
                                <h3 className="font-semibold text-zinc-900">Planning Prompt (Optional)</h3>
                                <textarea 
                                    className="w-full p-3 bg-white border border-zinc-200 rounded-lg text-sm font-mono h-24 focus:ring-2 focus:ring-blue-500/20 outline-none"
                                    placeholder="E.g. Make it fast-paced and energetic..."
                                    value={s2Prompt}
                                    onChange={e => setS2Prompt(e.target.value)}
                                />
                            </section>

                             <button 
                                onClick={handleRunStep2}
                                disabled={s2Loading || s2Files.length === 0}
                                className="w-full py-3 bg-zinc-900 text-white rounded-lg font-medium hover:bg-black disabled:opacity-50 transition-all"
                            >
                                {s2Loading ? "Planning..." : "Generate Scenario"}
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
                        {(activeTab === 'step1' ? s1Result : s2Result) ? (
                            <pre className="text-xs font-mono text-zinc-600 whitespace-pre-wrap">
                                {JSON.stringify(activeTab === 'step1' ? s1Result : s2Result, null, 2)}
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
