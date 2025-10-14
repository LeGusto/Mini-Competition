import { authStore } from '../stores/auth';
import { API_BASE_URL } from '../config';

const API_BASE = API_BASE_URL;

interface LoginData {
  username: string;
  password: string;
}

interface RegisterData {
  username: string;
  email?: string;
  password: string;
}

interface AuthResponse {
  success: boolean;
  token?: string;
  user?: any;
  error?: string;
}

class AuthService {
  // Login user
  async login(data: LoginData): Promise<AuthResponse> {
    try {
      // Get user's timezone
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...data,
          timezone: userTimezone
        })
      });

      const result = await response.json();
      if (response.ok && result.token) {
        authStore.setAuth(result.user, result.token);
        return { success: true, user: result.user, token: result.token };
      } else {
        return { success: false, error: result.error || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  }

  // Register user
  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (response.ok && result.user && result.token) {
        // Auto-login after successful registration
        authStore.setAuth(result.user, result.token);
        return { success: true, user: result.user, token: result.token };
      } else {
        return { success: false, error: result.error || 'Registration failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  }

  // Logout user
  logout(): void {
    authStore.logout();
  }

  // Get auth headers for API requests
  getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('auth_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  // Make authenticated API request
  async authenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const headers: Record<string, string> = {
      ...this.getAuthHeaders()
    };

    // Add any custom headers from options
    if (options.headers) {
      Object.assign(headers, options.headers);
    }

    // Only set Content-Type for JSON requests if not already set and not FormData
    if (!headers['Content-Type'] && !url.includes('/statement') && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      // Token expired or invalid
      this.logout();
      window.location.href = '/login';
    }

    return response;
  }

  // Verify token
  async verifyToken(): Promise<boolean> {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return false;

      const response = await fetch(`${API_BASE}/auth/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
      });

      const result = await response.json();
      return result.valid;
    } catch {
      return false;
    }
  }
}

export const authService = new AuthService(); 