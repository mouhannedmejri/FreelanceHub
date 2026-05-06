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
  portfolio_projects?: PortfolioProject[];
  skills_endorsed?: SkillEndorsed[];
  video_intro_url?: string;
  availability_status?: 'available' | 'busy' | 'unavailable';
  languages?: LanguageItem[];
  work_experience?: WorkExperienceItem[];
  education?: EducationItem[];
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
  issuer?: string;
  date?: string;
  year?: string;
  credential_url?: string;
}

export interface PortfolioProject {
  id: string;
  title: string;
  description: string;
  category: string;
  images: string[];
  technologies: string[];
  project_url?: string;
  github_url?: string;
  completed_date?: string;
  client_name?: string;
  is_featured?: boolean;
}

export interface SkillEndorsed {
  skill_name: string;
  endorsement_count: number;
  category?: string;
  proficiency_level?: number;
}

export interface LanguageItem {
  language: string;
  proficiency_level: string;
}

export interface WorkExperienceItem {
  company: string;
  title: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export interface EducationItem {
  school: string;
  degree: string;
  start_date?: string;
  end_date?: string;
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
    username?: string;
    is_approved: boolean;
    created_at: string;
    interests?: string[];
  };
  profile: FreelancerProfile | null;
  follower_count?: number;
  is_following?: boolean;
  badges?: string[];
  availability?: string;
  share_url?: string;
  completion_percentage?: number;
  boost_suggestions?: string[];
  stats?: ProfileStats;
}
