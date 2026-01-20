import React from 'react';

interface LayoutProps {
    children: React.ReactNode;
    onNavigate: (view: 'create' | 'lab') => void;
    currentView: 'create' | 'lab';
}

export const Layout: React.FC<LayoutProps> = ({ children, onNavigate, currentView }) => {
    return (
        <div className="flex h-screen w-full bg-white overflow-hidden">
            {/* Sidebar */}
            <aside className="w-[260px] h-full border-r border-zinc-200 bg-zinc-50/50 flex flex-col justify-between shrink-0 z-20">
                <div className="p-5">
                    {/* Logo Area */}
                    <div className="flex items-center gap-2 mb-8 cursor-pointer" onClick={() => onNavigate('create')}>
                        <div className="w-8 h-8 bg-black rounded-lg flex items-center justify-center text-white font-bold text-lg">
                            A
                        </div>
                        <span className="font-semibold text-zinc-900 tracking-tight">AdEasy Studio</span>
                    </div>

                    {/* Nav Links */}
                    <nav className="space-y-1">
                        <div 
                            onClick={() => onNavigate('create')}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors ${
                                currentView === 'create' 
                                ? 'bg-white border border-zinc-200 text-zinc-900 shadow-sm' 
                                : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900'
                            }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
                            New Project
                        </div>
                        
                         <div 
                            onClick={() => onNavigate('lab')}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium cursor-pointer transition-colors ${
                                currentView === 'lab' 
                                ? 'bg-white border border-zinc-200 text-zinc-900 shadow-sm' 
                                : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900'
                            }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                            Pipeline Lab
                        </div>
                        <div className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 cursor-pointer transition-colors">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
                            Library
                        </div>
                        <div className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 cursor-pointer transition-colors">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                            Settings
                        </div>
                    </nav>
                </div>

                {/* User / Footer */}
                <div className="p-4 border-t border-zinc-200">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-200"></div>
                        <div className="flex flex-col">
                            <span className="text-xs font-medium text-zinc-900">User Account</span>
                            <span className="text-[10px] text-zinc-500">Free Plan</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 h-full bg-white relative overflow-y-auto custom-scrollbar">
                {/* Optional Grid Background */}
                <div className="absolute inset-0 bg-grid-small pointer-events-none z-0 opacity-40" />
                
                <div className="relative z-10 w-full max-w-5xl mx-auto p-10">
                    {children}
                </div>
            </main>
        </div>
    );
};
