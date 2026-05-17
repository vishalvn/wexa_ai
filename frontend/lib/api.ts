/**
 * Centralized Axios API client.
 *
 * Features:
 * - Automatically attaches Bearer token to every request
 * - Auto-refreshes access token when it expires (401 response)
 * - Retry the original request after refresh
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create the axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: true,  // sends HTTP-only cookies (refresh token)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add access token from localStorage to every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Track if we're already refreshing (prevents infinite retry loops)
let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

// Response interceptor: handle 401 by refreshing the token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshToken = getCookie('refresh_token');
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newToken = data.access_token;
          localStorage.setItem('access_token', newToken);

          // Retry all pending requests with the new token
          pendingRequests.forEach((cb) => cb(newToken));
          pendingRequests = [];

          // Retry this request
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        } catch {
          // Refresh failed — redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        } finally {
          isRefreshing = false;
        }
      }

      // Queue this request until refresh completes
      return new Promise((resolve) => {
        pendingRequests.push((token: string) => {
          original.headers.Authorization = `Bearer ${token}`;
          resolve(api(original));
        });
      });
    }

    return Promise.reject(error);
  }
);

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

export default api;
