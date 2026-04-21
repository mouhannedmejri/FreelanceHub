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
}

export interface PortfolioItem {
  title: string;
  description: string;
  image_url: string;
  tags: string[];
}

export interface Certification {
  name: string;
  issuer: string;
  year: number;
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
