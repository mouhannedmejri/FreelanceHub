export interface FreelancerProfile {
  id: number;
  user_id: number;
  bio: string;
  title: string;
  hourly_rate: number;
  location: string;
  phone: string;
  skills: string[];
  portfolio: PortfolioItem[];
  certifications: Certification[];
  cv_filename: string;
  cv_size: number;
}

export interface PortfolioItem {
  id?: number;
  title: string;
  description: string;
  image_url: string;
  skills: string[];
}

export interface Certification {
  id?: number;
  name: string;
  issuer: string;
  year: string;
}

export interface FullProfile {
  user: {
    id: number;
    full_name: string;
    email: string;
    role: string;
    is_approved: boolean;
    created_at: string;
  };
  profile: FreelancerProfile | null;
}
