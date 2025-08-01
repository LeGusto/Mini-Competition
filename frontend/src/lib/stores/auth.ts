// src/lib/stores/auth.ts
import { writable } from 'svelte/store';

interface User {
  id: number;
  username: string;
  email?: string;
  role?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

// Create the auth store
function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    loading: true
  });

  return {
    subscribe,
    
    // Initialize auth state from localStorage
    init: () => {
      const token = localStorage.getItem('auth_token');
      const user = localStorage.getItem('auth_user');
      
      if (token && user) {
        set({
          user: JSON.parse(user),
          token,
          isAuthenticated: true,
          loading: false
        });
      } else {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          loading: false
        });
      }
    },
    
    // Set authenticated state
    setAuth: (user: User, token: string) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(user));
      
      set({
        user,
        token,
        isAuthenticated: true,
        loading: false
      });
    },
    
    // Clear auth state
    logout: () => {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false
      });
    },
    
    // Update user data
    updateUser: (userData: Partial<User>) => {
      update(state => {
        if (state.user) {
          const updatedUser = { ...state.user, ...userData };
          localStorage.setItem('auth_user', JSON.stringify(updatedUser));
          return { ...state, user: updatedUser };
        }
        return state;
      });
    }
  };
}

export const authStore = createAuthStore();