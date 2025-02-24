import api from './index';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('grant_type', 'password');
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    try {
      const response = await api.post('/api/v1/auth/token', formData.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      return response.data;
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Login error:', (error as any).response?.data || error.message);
      } else {
        console.error('Login error:', error);
      }
      throw error;
    }
  },

  register: async (data: RegisterData) => {
    try {
      const response = await api.post('/api/v1/auth/users', data);
      return response.data;
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Registration error:', (error as any).response?.data || error.message);
      } else {
        console.error('Registration error:', error);
      }
      throw error;
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await api.get('/api/v1/auth/users/me');
      return response.data;
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Get user error:', (error as any).response?.data || error.message);
      } else {
        console.error('Get user error:', error);
      }
      throw error;
    }
  },
};