export interface User {
  id: string;
  email: string;
  username: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  username?: string;
}

export interface UserUpdate {
  username?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface APIConfig {
  id: string;
  model_name: string;
  provider: string;
  api_key_masked: string;
  base_url: string | null;
  model_version: string | null;
  is_default: boolean;
  created_at: string;
}

export interface APIConfigCreate {
  model_name: string;
  provider: string;
  api_key: string;
  base_url?: string;
  model_version?: string;
  is_default?: boolean;
}

export interface APIConfigUpdate {
  model_name?: string;
  provider?: string;
  api_key?: string;
  base_url?: string;
  model_version?: string;
  is_default?: boolean;
}

export interface APIConfigTest {
  provider: string;
  api_key: string;
  base_url?: string;
  model_version?: string;
}

export interface APIConfigTestResult {
  success: boolean;
  message: string;
}

export interface Analysis {
  id: string;
  user_id: string;
  company_name: string;
  stock_code: string | null;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export interface AnalysisCreate {
  company_name: string;
  stock_code?: string;
  include_charts?: boolean;
  api_config_id?: string;
}

export interface AnalysisProgress {
  analysis_id: string;
  status: string;
  progress: number;
  message: string;
}

export interface Report {
  id: string;
  analysis_id: string;
  content_md: string | null;
  content_html: string | null;
  created_at: string;
}

export interface AnalysisListResponse {
  items: Analysis[];
  total: number;
}

export interface UserStats {
  total_analyses: number;
  member_since: string;
}
