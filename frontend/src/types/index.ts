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
  progress_stage?: string | null;
  progress: number;
  message: string;
}

export interface Report {
  id: string;
  analysis_id: string;
  content_md: string | null;
  content_html: string | null;
  created_at: string;
  company?: StructuredReportCompany | null;
  financials?: StructuredReportFinancials | null;
  synthesis?: StructuredReportSynthesis | null;
  agents?: StructuredReportAgent[];
  data_quality?: StructuredReportDataQuality | null;
  original?: StructuredReportOriginal | null;
}

export interface StructuredReportCompany {
  company_name: string;
  stock_code?: string | null;
  ts_code?: string | null;
  exchange?: string | null;
  industry?: string | null;
  data_source?: string | null;
  data_date?: string | null;
}

export interface StructuredReportFinancials {
  revenue?: number | null;
  net_profit?: number | null;
  gross_margin?: number | null;
  net_margin?: number | null;
  roe?: number | null;
  roa?: number | null;
  total_assets?: number | null;
  total_liabilities?: number | null;
  equity?: number | null;
  market_cap?: number | null;
  pe_ratio?: number | null;
  pb_ratio?: number | null;
  ps_ratio?: number | null;
  close_price?: number | null;
  asset_liability_ratio?: number | null;
  debt_to_equity?: number | null;
  current_ratio?: number | null;
  quick_ratio?: number | null;
  operating_cash_flow?: number | null;
  operating_cash_flow_to_net_profit?: number | null;
}

export interface StructuredReportDisagreement {
  topic: string;
  munger?: string | null;
  industry?: string | null;
  audit?: string | null;
}

export interface StructuredReportSynthesis {
  company_profile?: string | null;
  consensus?: string[];
  disagreements?: StructuredReportDisagreement[];
  final_score?: number | null;
  investment_decision?: string | null;
  insufficient_data?: boolean;
  core_reasons?: string[];
  major_risks?: string[];
}

export interface StructuredReportEvidence {
  item: string;
  source?: string | null;
  source_type?: string | null;
  source_date?: string | null;
  excerpt?: string | null;
  confidence?: number | null;
}

export interface StructuredReportAgent {
  name: string;
  title: string;
  status: string;
  score?: number | null;
  summary?: string | null;
  thesis?: string[];
  positives?: string[];
  risks?: string[];
  red_flags?: string[];
  questions?: string[];
  evidence?: StructuredReportEvidence[];
  insufficient_data?: boolean;
  error_message?: string | null;
}

export interface StructuredReportDataQuality {
  is_mock?: boolean;
  quality_note?: string | null;
  missing_fields?: string[];
  missing_financial_fields?: string[];
  completed_agent_count?: number;
  failed_agent_roles?: string[];
}

export interface StructuredReportOriginal {
  content_md: string | null;
  content_html: string | null;
}

export interface AnalysisListResponse {
  items: Analysis[];
  total: number;
}

export interface UserStats {
  total_analyses: number;
  member_since: string;
}
