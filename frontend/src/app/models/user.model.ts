export interface User {
  id: number;
  full_name: string;
  email: string;
  role: 'freelancer' | 'client' | 'admin';
  created_at: string;
  is_approved: boolean;
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  full_name: string;
  email: string;
  password: string;
  role: 'freelancer' | 'client';
}
