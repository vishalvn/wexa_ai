/**
 * Zustand global state store.
 * Manages authentication state, current user, and UI state.
 *
 * Why Zustand? It's simpler than Redux but more scalable than Context API.
 * State is accessible anywhere in the app without prop-drilling.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from './api';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'owner' | 'admin' | 'analyst' | 'viewer';
  organization: {
    id: number;
    name: string;
    slug: string;
    api_key: string;
  };
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

interface SignupData {
  email: string;
  full_name: string;
  password: string;
  organization_name: string;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post('/auth/login', { email, password });
          localStorage.setItem('access_token', data.access_token);
          // Load full user profile
          const { data: user } = await api.get('/auth/me');
          set({ user, isAuthenticated: true });
        } finally {
          set({ isLoading: false });
        }
      },

      signup: async (signupData: SignupData) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post('/auth/signup', signupData);
          // After signup, log in automatically
          await get().login(signupData.email, signupData.password);
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        await api.post('/auth/logout');
        localStorage.removeItem('access_token');
        set({ user: null, isAuthenticated: false });
        window.location.href = '/login';
      },

      loadUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        try {
          const { data } = await api.get('/auth/me');
          set({ user: data, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'auth-storage',  // localStorage key
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// Dashboard UI state
interface DashboardUIState {
  activeDashboardId: number | null;
  setActiveDashboard: (id: number | null) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useDashboardStore = create<DashboardUIState>((set) => ({
  activeDashboardId: null,
  setActiveDashboard: (id) => set({ activeDashboardId: id }),
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
