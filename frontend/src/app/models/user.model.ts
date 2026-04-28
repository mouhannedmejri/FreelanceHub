export interface User {
  id: number | string;
  full_name: string;
  email: string;
  role: 'freelancer' | 'client' | 'admin';
  created_at: string;
  is_approved: boolean;
  onboarding_complete?: boolean;
  preferences?: {
    role_goal?: 'client' | 'freelancer';
    skills_or_interests?: string[];
    budget_or_rate?: number;
    notifications?: {
      proposals?: boolean;
      messages?: boolean;
      marketing?: boolean;
      product_updates?: boolean;
    };
  };
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
