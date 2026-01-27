export const getApiUrl = () => {
    const envUrl = import.meta.env.VITE_API_URL;
    const isLocalhost = typeof window !== 'undefined' && 
        (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
    
    // 1. If we are actually on localhost, use the env var or default
    if (isLocalhost) return envUrl || 'http://localhost:8000';

    // 2. If env var is set and NOT localhost, use it (Cloud Run / Prod)
    if (envUrl && envUrl.startsWith('http') && !envUrl.includes('localhost')) return envUrl;
    
    // 3. Cloud VM Fallback: assume backend is on port 8000 of the same host we are accessing
    return `${window.location.protocol}//${window.location.hostname}:8000`;
};

export const getWsBaseUrl = () => {
    const apiBase = getApiUrl();
    return apiBase.replace('http', 'ws');
};

export const API_URL = getApiUrl();
export const WS_BASE_URL = getWsBaseUrl();
export const API_KEY = import.meta.env.VITE_API_KEY || 'adeasy-secret-key';
