export interface Lead {
  id: string;
  first_name?: string;
  last_name?: string;
  phone: string;
  email?: string;
  stage: string;
  source: string;
  is_suppressed: boolean;
  custom_fields: Record<string, any>;
  created_at: string;
}

export interface KnowledgeChunk {
  id: string;
  title: string;
  fact_text: string;
  status: 'draft' | 'approved' | 'rejected';
  created_at: string;
}

export interface Script {
  id: string;
  title: string;
  is_approved: boolean;
  content: string;
  created_at: string;
}

export interface CallLog {
  id: string;
  provider_call_sid: string;
  provider_type: string;
  direction: string;
  status: string;
  destination: string;
  duration_seconds: number;
  cost_inr: number;
  summary?: string;
  recording_url?: string;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed';
  due_date?: string;
  created_at: string;
}
