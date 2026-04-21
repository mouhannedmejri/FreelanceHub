export interface Offer {
  id: number;
  client_id: number;
  client_name: string;
  title: string;
  description: string;
  category: string;
  skills: string[];
  budget_min: number;
  budget_max: number;
  duration: string;
  location: string;
  proposals_count: number;
  status: string;
  created_at: string;
}

export interface OffersResponse {
  offers: Offer[];
  total: number;
}

export interface CreateOfferPayload {
  title: string;
  description: string;
  category: string;
  skills: string[];
  budget_min: number;
  budget_max: number;
  duration: string;
  location: string;
}
