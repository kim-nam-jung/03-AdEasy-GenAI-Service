import React from 'react';
import { useToastStore, ToastType } from '../store/toastStore';

const ToastItem: React.FC<{
    id: string;
    type: ToastType;
    message: string;
    onClose: (id: string) => void;
}> = ({ id, type, message, onClose }) => {
    const bgColors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-amber-500',
    };
    
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️',
    };

    return (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white mb-3 animate-slide-in-right min-w-[300px] ${bgColors[type]}`}>
            <span className="text-lg">{icons[type]}</span>
            <p className="flex-1 text-sm font-medium">{message}</p>
            <button onClick={() => onClose(id)} className="text-white/80 hover:text-white transition-colors">
                ✕
            </button>
        </div>
    );
};

export const ToastContainer: React.FC = () => {
    const { toasts, removeToast } = useToastStore();

    return (
        <div className="fixed top-5 right-5 z-[9999] flex flex-col items-end pointer-events-none">
            <div className="pointer-events-auto">
                {toasts.map((toast) => (
                    <ToastItem
                        key={toast.id}
                        id={toast.id}
                        type={toast.type}
                        message={toast.message}
                        onClose={removeToast}
                    />
                ))}
            </div>
        </div>
    );
};
