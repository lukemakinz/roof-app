import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authAPI } from '../lib/api';

export const useAuthStore = create(
    persist(
        (set, get) => ({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            login: async (email, password) => {
                set({ isLoading: true, error: null });
                try {
                    const response = await authAPI.login(email, password);
                    const { user, tokens } = response.data;

                    localStorage.setItem('accessToken', tokens.access);
                    localStorage.setItem('refreshToken', tokens.refresh);

                    set({ user, isAuthenticated: true, isLoading: false });
                    return { success: true };
                } catch (error) {
                    const message = error.response?.data?.error || 'Login failed';
                    set({ error: message, isLoading: false });
                    return { success: false, error: message };
                }
            },

            register: async (data) => {
                set({ isLoading: true, error: null });
                try {
                    const response = await authAPI.register(data);
                    const { user, tokens } = response.data;

                    localStorage.setItem('accessToken', tokens.access);
                    localStorage.setItem('refreshToken', tokens.refresh);

                    set({ user, isAuthenticated: true, isLoading: false });
                    return { success: true };
                } catch (error) {
                    const errors = error.response?.data || {};
                    const message = Object.values(errors).flat().join(', ') || 'Registration failed';
                    set({ error: message, isLoading: false });
                    return { success: false, error: message };
                }
            },

            logout: () => {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                set({ user: null, isAuthenticated: false });
            },

            fetchProfile: async () => {
                try {
                    const response = await authAPI.getProfile();
                    set({ user: response.data });
                } catch (error) {
                    if (error.response?.status === 401) {
                        get().logout();
                    }
                }
            },

            clearError: () => set({ error: null }),
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
        }
    )
);
