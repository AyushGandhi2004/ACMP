import axios from 'axios'

const api = axios.create({
    baseURL : import.meta.env.VITE_API_BASE_URL,
    headers : {"Content-Type":"application-json"}
});

export const runPipeline = async (code , language=NULL) =>{
    const payload = code;
    if(language && language!=='auto'){
        payload.language = language;
    }
    const response = await api.post('api/v1/pipeline/run', payload);
    return response.data;
};

export const getPipelineResult = async (sessionId) => {
    const response = await api.get(`api/v1/pipeline/result/${sessionId}`);
    return response.data;
}

export const adminLogin = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('api/v1/admin/login', formData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
    return response.data;
};


export const uploadDocument = async (file, language, framework, token) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);
    formData.append("framework", framework);

    const response = await api.post('api/v1/admin/documents/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${token}`
        }
    })
    return response.data;
};

export const getDocuments = async (token) => {
    const response = await api.get('api/v1/admin/documents', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    return response.data;
};

export const getWebSocketUrl = (sessionId) => {
    const wsBase = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
    return `${wsBase}/api/v1/ws/${sessionId}`;
};

export default api;

