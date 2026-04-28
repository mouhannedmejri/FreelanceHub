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
  avg_rating?: number;
  total_reviews?: number;
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

export interface ProfileStats {
  earnings: number;
  hired: number;
  rating: number;
  reviews: number;
  followers: number;
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
  follower_count?: number;
  is_following?: boolean;
  badges?: string[];
  availability?: string;
  stats?: ProfileStats;
}
