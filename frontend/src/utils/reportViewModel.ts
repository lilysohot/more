import type { Analysis, Report, StructuredReportFinancials } from '@/types';

export const NO_DATA = '暂无数据';

export const FINANCIAL_FIELD_COUNT = 20;

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

export function getScoreTone(score?: number | null): 'positive' | 'neutral' | 'risk' | 'muted' {
  if (!isFiniteNumber(score)) return 'muted';
  if (score >= 8) return 'positive';
  if (score >= 6) return 'neutral';
  return 'risk';
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
