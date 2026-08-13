import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../lib/api'

interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  date_joined: string
  groups: string[]
}

interface LoginResponse {
  access: string
  refresh: string
  user: User
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const data = await api.post<LoginResponse>('/auth/login/', {
            email,
            password,
          })
          localStorage.setItem('access_token', data.access)
          localStorage.setItem('refresh_token', data.refresh)
          set({ user: data.user, isAuthenticated: true, isLoading: false })
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : 'Login failed'
          set({ error: message, isLoading: false })
          throw err
        }
      },

      register: async (email, username, password) => {
        set({ isLoading: true, error: null })
        try {
          await api.post<User>('/auth/register/', {
            email,
            username,
            password,
          })
          set({ isLoading: false })
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : 'Registration failed'
          set({ error: message, isLoading: false })
          throw err
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false, error: null })
      },

      fetchMe: async () => {
        const token = localStorage.getItem('access_token')
        if (!token) {
          set({ user: null, isAuthenticated: false })
          return
        }
        set({ isLoading: true })
        try {
          const user = await api.get<User>('/auth/me/')
          set({ user, isAuthenticated: true, isLoading: false })
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)
