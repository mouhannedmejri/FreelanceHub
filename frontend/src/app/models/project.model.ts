export interface Milestone {
  id: string;
  title: string;
  due_date: string;
  status: 'pending' | 'in_progress' | 'done';
  deliverables: string[];
  budget_allocated: number;
}

export interface Task {
  id: string;
  milestone_id: string;
  title: string;
  description: string;
  assigned_to: string;
  status: 'todo' | 'in_progress' | 'review' | 'done';
  priority: 'low' | 'medium' | 'high';
  due_date: string;
  created_at: string;
}

export interface Deliverable {
  id: string;
  milestone_id: string;
  file_url: string;
  file_name: string;
  uploaded_by: string;
  uploaded_at: string;
  confirmed: boolean;
  confirmed_at?: string;
}

export interface ProjectParticipant {
  id: string;
  full_name: string;
  avatar_initials: string;
  rating?: number;
}

export interface ProjectDetail {
  id: string;
  title: string;
  status: string;
  client_id: string;
  freelancer_id: string;
  offer_id: string;
  budget: number;
  started_at: string;
  deadline: string;
  created_at: string;
  completed_at?: string;

  // Extended fields
  milestones: Milestone[];
  tasks: Task[];
  deliverables_list: Deliverable[];
  progress_percent: number;
  total_budget: number;
  paid_amount: number;

  // Populated
  freelancer?: ProjectParticipant;
  client?: ProjectParticipant;
}

export interface UpcomingMilestone {
  milestone_id: string;
  milestone_title: string;
  due_date: string;
  status: string;
  project_id: string;
  project_title: string;
  assignee?: ProjectParticipant;
}
