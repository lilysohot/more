import { Alert, Card, Collapse, Empty, Progress, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { Report, StructuredReportAgent, StructuredReportEvidence } from '@/types';
import { formatPercent, formatScore, getScoreTone, NO_DATA } from '@/utils/reportViewModel';

const { Paragraph, Text, Title } = Typography;

const AGENT_STATUS_LABELS: Record<string, string> = {
  completed: '完成',
  failed: '失败',
  running: '运行中',
  pending: '等待中',
  skipped: '已跳过',
};

interface ReportPanelProps {
  report: Report;
}

interface RiskRow {
  key: string;
  level: '高' | '中' | '数据';
  item: string;
  source: string;
  followUp: string;
}

export function AgentTriad({ report }: ReportPanelProps) {
  const agents = report.agents || [];

  return (
    <section id="agents" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">05 / AGENT TRIAD</Text>
        <Title level={2}>三维 Agent 分析</Title>
      </div>
      {agents.length ? (
        <div className="report-agent-grid">
          {agents.map((agent) => <AgentPerspectiveCard key={agent.name} agent={agent} />)}
        </div>
      ) : <Empty description="暂无结构化 Agent 输出" />}
    </section>
  );
}

export function RiskLedger({ report }: ReportPanelProps) {
  const risks = buildRiskRows(report);
  const columns: ColumnsType<RiskRow> = [
    {
      title: '等级',
      dataIndex: 'level',
      key: 'level',
      width: 90,
      render: (level: RiskRow['level']) => <Tag color={level === '高' ? 'red' : level === '中' ? 'orange' : 'cyan'}>{level}</Tag>,
    },
    { title: '风险事项', dataIndex: 'item', key: 'item' },
    { title: '来源', dataIndex: 'source', key: 'source', width: 120 },
    { title: '后续跟踪', dataIndex: 'followUp', key: 'followUp' },
  ];

  return (
    <section id="risks" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">07 / RISK LEDGER</Text>
        <Title level={2}>风险台账</Title>
      </div>
      {risks.length ? (
        <div className="report-table-wrap">
          <Table rowKey="key" columns={columns} dataSource={risks} pagination={false} size="small" />
        </div>
      ) : <Empty description="暂无结构化风险项" />}
    </section>
  );
}

export function EvidenceShelf({ report }: ReportPanelProps) {
  const agentsWithEvidence = (report.agents || []).filter((agent) => agent.evidence?.length);

  return (
    <section id="evidence" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">08 / EVIDENCE SHELF</Text>
        <Title level={2}>证据与数据来源</Title>
      </div>
      <Alert className="report-source-alert" type="info" showIcon message="证据区用于区分数据源事实和模型推理判断，低置信度证据需人工复核。" />
      {agentsWithEvidence.length ? (
        <Collapse
          className="report-evidence-collapse"
          items={agentsWithEvidence.map((agent) => ({
            key: agent.name,
            label: `${agent.title} · ${agent.evidence?.length || 0} 条证据`,
            children: <EvidenceList evidence={agent.evidence || []} />,
          }))}
        />
      ) : <Empty description="暂无结构化证据来源" />}
      {report.data_quality?.quality_note ? <Paragraph className="report-quality-note">{report.data_quality.quality_note}</Paragraph> : null}
    </section>
  );
}

function AgentPerspectiveCard({ agent }: { agent: StructuredReportAgent }) {
  const tone = getScoreTone(agent.score);
  const redFlagCount = agent.red_flags?.length || 0;
  const statusLabel = AGENT_STATUS_LABELS[agent.status] || agent.status || '未知';

  return (
    <Card className={`report-agent-card report-tone-${tone}`} bordered={false}>
      <div className="report-agent-head">
        <div>
          <Text className="report-kicker">{agent.name.toUpperCase()}</Text>
          <Title level={3}>{agent.title}</Title>
        </div>
        <Tag color={agent.status === 'completed' ? 'green' : 'red'}>{statusLabel}</Tag>
      </div>
      <strong className="report-agent-score">{formatScore(agent.score)}</strong>
      <Paragraph>{agent.summary || agent.error_message || '该视角暂未返回摘要。'}</Paragraph>
      <Space wrap className="report-tag-row">
        {(agent.positives || []).slice(0, 3).map((item) => <Tag key={item} color="green">{item}</Tag>)}
        {(agent.risks || []).slice(0, 3).map((item) => <Tag key={item} color="orange">{item}</Tag>)}
        {redFlagCount ? <Tag color="red">红旗 {redFlagCount}</Tag> : <Tag>暂无红旗</Tag>}
      </Space>
      <Collapse
        ghost
        items={[{
          key: 'details',
          label: '展开 thesis / 风险 / 问题 / 证据',
          children: <AgentDetails agent={agent} />,
        }]}
      />
    </Card>
  );
}

function AgentDetails({ agent }: { agent: StructuredReportAgent }) {
  return (
    <div className="report-agent-details">
      <DetailList title="投资论点" items={agent.thesis || []} />
      <DetailList title="风险" items={agent.risks || []} danger />
      <DetailList title="红旗" items={agent.red_flags || []} danger />
      <DetailList title="待确认问题" items={agent.questions || []} />
      {agent.insufficient_data ? <Alert type="warning" showIcon message="该视角标记为数据不足。" /> : null}
    </div>
  );
}

function DetailList({ title, items, danger = false }: { title: string; items: string[]; danger?: boolean }) {
  if (!items.length) return null;
  return (
    <div className={danger ? 'report-detail-list report-detail-list-danger' : 'report-detail-list'}>
      <Text strong>{title}</Text>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: StructuredReportEvidence[] }) {
  return (
    <div className="report-evidence-list">
      {evidence.map((item) => (
        <Card key={`${item.source || 'source'}-${item.item}`} size="small" className="report-evidence-item">
          <Text strong>{item.item}</Text>
          <Paragraph>{item.excerpt || '暂无摘录。'}</Paragraph>
          <Space wrap>
            <Tag>{item.source || NO_DATA}</Tag>
            <Tag>{item.source_type || '来源类型未标注'}</Tag>
            <Tag>{item.source_date || '日期未知'}</Tag>
          </Space>
          {typeof item.confidence === 'number' ? <Progress percent={Math.round(item.confidence * 100)} size="small" format={() => formatPercent(item.confidence ? item.confidence * 100 : 0)} /> : null}
        </Card>
      ))}
    </div>
  );
}

function buildRiskRows(report: Report): RiskRow[] {
  const rows: RiskRow[] = [];
  (report.synthesis?.major_risks || []).forEach((risk, index) => {
    rows.push({ key: `major-${index}`, level: '高', item: risk, source: '综合汇总', followUp: '纳入投资结论前置检查。' });
  });

  (report.agents || []).forEach((agent) => {
    (agent.red_flags || []).forEach((risk, index) => {
      rows.push({ key: `${agent.name}-flag-${index}`, level: '高', item: risk, source: agent.title, followUp: '优先核验公告、年报和审计意见。' });
    });
    (agent.risks || []).forEach((risk, index) => {
      rows.push({ key: `${agent.name}-risk-${index}`, level: '中', item: risk, source: agent.title, followUp: '跟踪季度数据与产业变化。' });
    });
    (agent.questions || []).forEach((risk, index) => {
      rows.push({ key: `${agent.name}-question-${index}`, level: '数据', item: risk, source: agent.title, followUp: '补充数据后重新评估。' });
    });
  });

  return rows.slice(0, 18);
}
