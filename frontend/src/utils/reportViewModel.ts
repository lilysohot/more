import type { Analysis, Report, StructuredReportFinancials } from '@/types';

export const NO_DATA = '暂无数据';

export const FINANCIAL_FIELD_COUNT = 20;

const AGENT_ROLE_LABELS: Record<string, string> = {
  munger: '芒格视角',
  industry: '产业视角',
  audit: '审计视角',
  synthesis: '综合汇总',
};

const FINANCIAL_FIELD_LABELS: Record<string, string> = {
  revenue: '营业收入',
  net_profit: '净利润',
  gross_margin: '毛利率',
  net_margin: '净利率',
  roe: 'ROE',
  roa: 'ROA',
  total_assets: '总资产',
  total_liabilities: '总负债',
  equity: '净资产',
  market_cap: '市值',
  pe_ratio: 'PE',
  pb_ratio: 'PB',
  ps_ratio: 'PS',
  close_price: '收盘价',
  asset_liability_ratio: '资产负债率',
  debt_to_equity: '产权比率',
  current_ratio: '流动比率',
  quick_ratio: '速动比率',
  operating_cash_flow: '经营现金流',
  operating_cash_flow_to_net_profit: '现金流/净利',
};

const SOURCE_TYPE_LABELS: Record<string, string> = {
  annual_report: '年报',
  'annual-report': '年报',
  quarterly_report: '季报',
  'quarterly-report': '季报',
  research: '研究报告',
  industry_report: '行业报告',
  'industry-report': '行业报告',
  earnings_call: '业绩会纪要',
  'earnings-call': '业绩会纪要',
  announcement: '公告',
  news: '新闻',
  unit_test: '测试夹具',
  'unit-test': '测试夹具',
};

export function hasStructuredReport(report: Report | null): report is Report {
  return Boolean(
    report?.synthesis
    || report?.agents?.length
    || (report?.financials && Object.values(report.financials).some(isFiniteNumber))
  );
}

export function getReportCompanyName(report: Report, currentAnalysis?: Analysis | null): string {
  return report.company?.company_name || currentAnalysis?.company_name || '未知公司';
}

export function getReportStockCode(report: Report, currentAnalysis?: Analysis | null): string {
  return report.company?.ts_code || report.company?.stock_code || currentAnalysis?.stock_code || '未知代码';
}

export function formatDateTime(value?: string | null): string {
  if (!value) return NO_DATA;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN', { hour12: false });
}

export function formatPlainDate(value?: string | null): string {
  if (!value) return NO_DATA;
  if (/^\d{8}$/.test(value)) {
    return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`;
  }
  return value;
}

export function formatMoney(value?: number | null): string {
  if (!isFiniteNumber(value)) return NO_DATA;
  const absValue = Math.abs(value);
  if (absValue >= 100000000) return `${formatFixed(value / 100000000, 2)} 亿`;
  if (absValue >= 10000) return `${formatFixed(value / 10000, 2)} 万`;
  return formatNumber(value);
}

export function formatNumber(value?: number | null, digits = 2): string {
  if (!isFiniteNumber(value)) return NO_DATA;
  return new Intl.NumberFormat('zh-CN', {
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatPercent(value?: number | null): string {
  if (!isFiniteNumber(value)) return NO_DATA;
  return `${formatFixed(value, 1)}%`;
}

export function formatRatio(value?: number | null): string {
  if (!isFiniteNumber(value)) return NO_DATA;
  return formatFixed(value, 2);
}

export function formatScore(value?: number | null): string {
  if (!isFiniteNumber(value)) return NO_DATA;
  return `${formatFixed(value, 1)} / 10`;
}

export function formatAgentRoleLabel(role?: string | null): string {
  if (!role) return NO_DATA;
  return AGENT_ROLE_LABELS[role] || role;
}

export function formatFinancialFieldLabel(field?: string | null): string {
  if (!field) return NO_DATA;
  return FINANCIAL_FIELD_LABELS[field] || field;
}

export function formatSourceTypeLabel(sourceType?: string | null): string {
  if (!sourceType) return NO_DATA;
  return SOURCE_TYPE_LABELS[sourceType] || sourceType.replace(/[_-]/g, ' ');
}

export function getScoreTone(score?: number | null): 'positive' | 'neutral' | 'risk' | 'muted' {
  if (!isFiniteNumber(score)) return 'muted';
  if (score >= 8) return 'positive';
  if (score >= 6) return 'neutral';
  return 'risk';
}

export function isLowConfidenceReport(report: Report): boolean {
  const coverage = getFinancialCoverage(report.financials);
  const missingFinancialCount = report.data_quality?.missing_financial_fields?.length ?? 0;
  const failedRoles = report.data_quality?.failed_agent_roles?.length ?? 0;
  return Boolean(
    report.synthesis?.insufficient_data
    || failedRoles > 0
    || missingFinancialCount >= 3
    || (coverage.total > 0 && coverage.covered / coverage.total < 0.75)
  );
}

export function getFinancialCoverage(financials?: StructuredReportFinancials | null): { covered: number; total: number } {
  if (!financials) return { covered: 0, total: FINANCIAL_FIELD_COUNT };
  const covered = Object.values(financials).filter(isFiniteNumber).length;
  return { covered, total: FINANCIAL_FIELD_COUNT };
}

export function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatFixed(value: number, digits: number): string {
  return value.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
}
