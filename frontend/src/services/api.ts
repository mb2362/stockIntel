import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type { ApiError } from '../types/api';
import { API_BASE_URL } from '../utils/constants';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add any auth tokens here if needed
        // const token = localStorage.getItem('token');
        // if (token) {
        //   config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error: AxiosError) => {
        const apiError: ApiError = {
            message: 'An error occurred',
            status: error.response?.status,
        };

        if (error.response) {
            // Server responded with error
            apiError.message = (error.response.data as any)?.message || error.message;
            apiError.code = (error.response.data as any)?.code;
        } else if (error.request) {
            // Request made but no response
            apiError.message = 'No response from server. Please check your connection.';
        } else {
            // Error in request setup
            apiError.message = error.message;
        }

        // Retry logic for network errors
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
            const config = error.config;
            if (config && !config.headers?.['X-Retry-Count']) {
                config.headers = config.headers || {};
                config.headers['X-Retry-Count'] = '1';
                return api.request(config);
            }
        }

        return Promise.reject(apiError);
    }
);

export default api;
