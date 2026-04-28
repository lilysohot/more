import { Alert, Card, Col, Empty, Progress, Row, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { Report, StructuredReportDisagreement } from '@/types';
import { formatMoney, formatScore, getFinancialCoverage, getScoreTone, NO_DATA } from '@/utils/reportViewModel';

const { Paragraph, Text, Title } = Typography;

interface ReportPanelProps {
  report: Report;
}

export function HeroVerdict({ report }: ReportPanelProps) {
  const synthesis = report.synthesis;
  const score = synthesis?.final_score ?? null;
  const tone = getScoreTone(score);
  const scorePercent = typeof score === 'number' ? Math.max(0, Math.min(100, score * 10)) : 0;
  const coverage = getFinancialCoverage(report.financials);
  const isLowConfidence = Boolean(
    synthesis?.insufficient_data
    || report.data_quality?.missing_financial_fields?.length
    || coverage.covered < coverage.total
  );

  return (
    <section id="verdict" className={`report-panel report-verdict report-tone-${tone}`}>
      <div className="report-section-heading">
        <Text className="report-kicker">01 / VERDICT</Text>
        <Title level={2}>投资结论总览</Title>
      </div>
      <div className="report-verdict-grid">
        <div className="report-score-card">
          <Progress type="circle" percent={scorePercent} format={() => formatScore(score)} strokeColor="#c59b62" trailColor="rgba(14, 30, 25, 0.1)" />
          <Tag className="report-confidence-tag">{isLowConfidence ? '低置信度' : '数据可用'}</Tag>
        </div>
        <div className="report-verdict-copy">
          <Text className="report-kicker">INVESTMENT DECISION</Text>
          <Title level={3}>{synthesis?.investment_decision || '暂无明确投资结论'}</Title>
          <Paragraph>{synthesis?.company_profile || '后端尚未返回综合画像，当前仅保留原文报告作为附录。'}</Paragraph>
          <div className="report-two-column-list">
            <SummaryList title="核心理由" items={synthesis?.core_reasons || []} emptyText="暂无核心理由" />
            <SummaryList title="主要风险" items={synthesis?.major_risks || []} emptyText="暂无主要风险" danger />
          </div>
        </div>
      </div>
      {isLowConfidence ? <Alert type="warning" showIcon message="部分关键数据缺失，本报告结论需结合公告、年报和行情终端继续核验。" /> : null}
    </section>
  );
}

export function CompanyProfilePanel({ report }: ReportPanelProps) {
  const coverage = getFinancialCoverage(report.financials);
  const tags = [
    report.company?.industry,
    report.company?.exchange,
    report.company?.data_source,
    `数据覆盖 ${coverage.covered}/${coverage.total}`,
  ].filter(Boolean);

  return (
    <section id="profile" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">02 / COMPANY PROFILE</Text>
        <Title level={2}>公司画像与业务本质</Title>
      </div>
      <Paragraph className="report-profile-lede">
        {report.synthesis?.company_profile || '暂无结构化业务画像。可在下方原文报告中查看模型生成内容。'}
      </Paragraph>
      <Space wrap className="report-tag-row">
        {tags.map((tag) => <Tag key={tag}>{tag}</Tag>)}
      </Space>
      <Row gutter={[16, 16]} className="report-profile-stats">
        <Col xs={12} md={6}><MiniStat label="市值" value={formatMoney(report.financials?.market_cap)} /></Col>
        <Col xs={12} md={6}><MiniStat label="营业收入" value={formatMoney(report.financials?.revenue)} /></Col>
        <Col xs={12} md={6}><MiniStat label="净利润" value={formatMoney(report.financials?.net_profit)} /></Col>
        <Col xs={12} md={6}><MiniStat label="数据日期" value={report.company?.data_date || NO_DATA} /></Col>
      </Row>
    </section>
  );
}

export function ConsensusDisagreementPanel({ report }: ReportPanelProps) {
  const consensus = report.synthesis?.consensus || [];
  const disagreements = report.synthesis?.disagreements || [];
  const columns: ColumnsType<StructuredReportDisagreement> = [
    { title: '议题', dataIndex: 'topic', key: 'topic', width: 180 },
    { title: '芒格视角', dataIndex: 'munger', key: 'munger', render: (value?: string | null) => value || NO_DATA },
    { title: '产业视角', dataIndex: 'industry', key: 'industry', render: (value?: string | null) => value || NO_DATA },
    { title: '审计视角', dataIndex: 'audit', key: 'audit', render: (value?: string | null) => value || NO_DATA },
  ];

  return (
    <section id="consensus" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">06 / CONSENSUS</Text>
        <Title level={2}>共识、分歧与决策依据</Title>
      </div>
      <div className="report-two-column-list">
        <SummaryList title="主要共识" items={consensus} emptyText="暂无共识条目" />
        <SummaryList title="决策依据" items={report.synthesis?.core_reasons || []} emptyText="暂无决策依据" />
      </div>
      {disagreements.length ? (
        <div className="report-table-wrap">
          <Table rowKey="topic" columns={columns} dataSource={disagreements} pagination={false} size="small" />
        </div>
      ) : <Empty description="暂无结构化分歧矩阵" />}
    </section>
  );
}

interface SummaryListProps {
  title: string;
  items: string[];
  emptyText: string;
  danger?: boolean;
}

function SummaryList({ title, items, emptyText, danger = false }: SummaryListProps) {
  return (
    <Card className={danger ? 'report-list-card report-risk-list-card' : 'report-list-card'} bordered={false}>
      <Text strong>{title}</Text>
      {items.length ? (
        <ol>
          {items.slice(0, 6).map((item) => <li key={item}>{item}</li>)}
        </ol>
      ) : <Text className="report-muted">{emptyText}</Text>}
    </Card>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="report-mini-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
