import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refreshToken');
                if (refreshToken) {
                    const response = await axios.post(`${API_URL}/auth/refresh/`, {
                        refresh: refreshToken,
                    });

                    const { access } = response.data;
                    localStorage.setItem('accessToken', access);
                    originalRequest.headers.Authorization = `Bearer ${access}`;

                    return api(originalRequest);
                }
            } catch (refreshError) {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    login: (email, password) => api.post('/auth/login/', { email, password }),
    register: (data) => api.post('/auth/register/', data),
    getProfile: () => api.get('/auth/profile/'),
    updateProfile: (data) => api.patch('/auth/profile/', data),
};

// Materials API
export const materialsAPI = {
    getAll: () => api.get('/materials/'),
    getById: (id) => api.get(`/materials/${id}/`),
};

// Quotes API
export const quotesAPI = {
    getAll: (params) => api.get('/quotes/', { params }),
    getById: (id) => api.get(`/quotes/${id}/`),
    create: (data) => api.post('/quotes/', data),
    update: (id, data) => api.patch(`/quotes/${id}/`, data),
    delete: (id) => api.delete(`/quotes/${id}/`),

    // Special actions
    uploadImage: (id, file) => {
        const formData = new FormData();
        formData.append('image', file);
        return api.post(`/quotes/${id}/upload/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
    processAI: (id) => api.post(`/quotes/${id}/process/`),
    getStatus: (id) => api.get(`/quotes/${id}/status/`),
    updateDimensions: (id, data) => api.patch(`/quotes/${id}/dimensions/`, data),
    updateObstacles: (id, obstacles) => api.patch(`/quotes/${id}/obstacles/`, { obstacles }),
    calculate: (id, materialId, marginPercent = 35) =>
        api.post(`/quotes/${id}/calculate/`, { material_id: materialId, margin_percent: marginPercent }),
    generatePDF: (id, clientData) => api.post(`/quotes/${id}/generate_pdf/`, clientData),
    duplicate: (id) => api.post(`/quotes/${id}/duplicate/`),
};

export default api;
