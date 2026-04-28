import ReactECharts from 'echarts-for-react';
import { Card, Empty, Progress, Tooltip, Typography } from 'antd';
import type { Report, StructuredReportFinancials } from '@/types';
import { formatMoney, formatPercent, formatRatio, getFinancialCoverage, isFiniteNumber, NO_DATA } from '@/utils/reportViewModel';

const { Text, Title } = Typography;

interface ReportPanelProps {
  report: Report;
}

type MetricKind = 'money' | 'percent' | 'ratio' | 'plain';

interface MetricItem {
  label: string;
  value?: number | null;
  kind: MetricKind;
  group: string;
  hint: string;
}

export function MetricMatrix({ report }: ReportPanelProps) {
  const financials = report.financials;
  const coverage = getFinancialCoverage(financials);
  const metrics = buildMetrics(financials);

  return (
    <section id="metrics" className="report-panel report-paper-card">
      <div className="report-section-heading report-section-heading-split">
        <div>
          <Text className="report-kicker">03 / METRIC MATRIX</Text>
          <Title level={2}>核心财务与估值矩阵</Title>
        </div>
        <div className="report-coverage-meter">
          <span>数据完整度</span>
          <Progress percent={Math.round((coverage.covered / coverage.total) * 100)} size="small" strokeColor="#1c7c73" />
          <strong>{coverage.covered} / {coverage.total}</strong>
        </div>
      </div>
      <div className="report-metric-grid">
        {metrics.map((metric) => (
          <Tooltip key={metric.label} title={metric.hint}>
            <Card className="report-metric-card" bordered={false}>
              <span>{metric.group}</span>
              <strong className={!isFiniteNumber(metric.value) ? 'report-missing-value' : undefined}>{formatMetric(metric)}</strong>
              <em>{metric.label}</em>
            </Card>
          </Tooltip>
        ))}
      </div>
    </section>
  );
}

export function VisualInsightPanel({ report }: ReportPanelProps) {
  const financials = report.financials;
  const hasChartData = Boolean(financials && buildChartValues(financials).some(isFiniteNumber));

  return (
    <section id="visuals" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">04 / VISUAL INSIGHT</Text>
        <Title level={2}>财务质量可视化</Title>
      </div>
      {hasChartData ? (
        <div className="report-chart-grid">
          <ReactECharts className="report-chart-card" option={buildRadarOption(financials)} notMerge />
          <ReactECharts className="report-chart-card" option={buildValuationOption(financials)} notMerge />
        </div>
      ) : <Empty description="暂无足够指标生成图表" />}
    </section>
  );
}

function buildMetrics(financials?: StructuredReportFinancials | null): MetricItem[] {
  return [
    { label: '营业收入', value: financials?.revenue, kind: 'money', group: '规模', hint: '公司最近一期营业收入。' },
    { label: '净利润', value: financials?.net_profit, kind: 'money', group: '规模', hint: '公司最近一期归属利润或净利润。' },
    { label: '市值', value: financials?.market_cap, kind: 'money', group: '规模', hint: '总市值，受行情数据源影响。' },
    { label: '毛利率', value: financials?.gross_margin, kind: 'percent', group: '盈利', hint: '衡量产品或服务的毛利空间。' },
    { label: '净利率', value: financials?.net_margin, kind: 'percent', group: '盈利', hint: '衡量收入转化为利润的能力。' },
    { label: 'ROE', value: financials?.roe, kind: 'percent', group: '盈利', hint: '净资产收益率，衡量股东资本回报。' },
    { label: 'ROA', value: financials?.roa, kind: 'percent', group: '盈利', hint: '总资产收益率，衡量资产创造利润的能力。' },
    { label: 'PE', value: financials?.pe_ratio, kind: 'ratio', group: '估值', hint: '市盈率，越高代表市场对盈利预期越高。' },
    { label: 'PB', value: financials?.pb_ratio, kind: 'ratio', group: '估值', hint: '市净率，用于资产型公司估值参考。' },
    { label: 'PS', value: financials?.ps_ratio, kind: 'ratio', group: '估值', hint: '市销率，用于收入规模与市场定价比较。' },
    { label: '资产负债率', value: financials?.asset_liability_ratio, kind: 'percent', group: '偿债', hint: '总负债占总资产比例。' },
    { label: '流动比率', value: financials?.current_ratio, kind: 'ratio', group: '偿债', hint: '流动资产覆盖流动负债的能力。' },
    { label: '速动比率', value: financials?.quick_ratio, kind: 'ratio', group: '偿债', hint: '剔除存货后的短期偿债能力。' },
    { label: '经营现金流', value: financials?.operating_cash_flow, kind: 'money', group: '质量', hint: '经营活动产生的现金流。' },
    { label: '现金流/净利', value: financials?.operating_cash_flow_to_net_profit, kind: 'percent', group: '质量', hint: '衡量利润现金含量。' },
  ];
}

function formatMetric(metric: MetricItem): string {
  if (!isFiniteNumber(metric.value)) return NO_DATA;
  if (metric.kind === 'money') return formatMoney(metric.value);
  if (metric.kind === 'percent') return formatPercent(metric.value);
  if (metric.kind === 'ratio') return formatRatio(metric.value);
  return String(metric.value);
}

function buildChartValues(financials: StructuredReportFinancials): Array<number | null | undefined> {
  return [
    financials.gross_margin,
    financials.net_margin,
    financials.roe,
    financials.roa,
    financials.operating_cash_flow_to_net_profit,
    financials.pe_ratio,
    financials.pb_ratio,
    financials.ps_ratio,
  ];
}

function buildRadarOption(financials?: StructuredReportFinancials | null) {
  const safeValue = (value?: number | null) => (isFiniteNumber(value) ? Math.max(0, Math.min(value, 100)) : 0);
  return {
    backgroundColor: 'transparent',
    tooltip: {},
    radar: {
      indicator: [
        { name: '毛利率', max: 100 },
        { name: '净利率', max: 100 },
        { name: 'ROE', max: 60 },
        { name: 'ROA', max: 40 },
        { name: '现金含量', max: 150 },
      ],
      splitLine: { lineStyle: { color: 'rgba(14, 30, 25, 0.14)' } },
      splitArea: { areaStyle: { color: ['rgba(197,155,98,0.08)', 'rgba(28,124,115,0.05)'] } },
      axisName: { color: '#31443d' },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          safeValue(financials?.gross_margin),
          safeValue(financials?.net_margin),
          safeValue(financials?.roe),
          safeValue(financials?.roa),
          safeValue(financials?.operating_cash_flow_to_net_profit),
        ],
        areaStyle: { color: 'rgba(197, 155, 98, 0.28)' },
        lineStyle: { color: '#9f6f3b' },
      }],
    }],
  };
}

function buildValuationOption(financials?: StructuredReportFinancials | null) {
  const safeValue = (value?: number | null) => (isFiniteNumber(value) ? value : 0);
  return {
    backgroundColor: 'transparent',
    tooltip: {},
    grid: { left: 48, right: 20, top: 28, bottom: 40 },
    xAxis: { type: 'value', axisLine: { lineStyle: { color: '#65766f' } }, splitLine: { lineStyle: { color: 'rgba(14,30,25,0.08)' } } },
    yAxis: { type: 'category', data: ['PE', 'PB', 'PS'], axisLine: { lineStyle: { color: '#65766f' } } },
    series: [{
      type: 'bar',
      data: [safeValue(financials?.pe_ratio), safeValue(financials?.pb_ratio), safeValue(financials?.ps_ratio)],
      itemStyle: { color: '#1c7c73', borderRadius: [0, 6, 6, 0] },
      barWidth: 18,
    }],
  };
}
