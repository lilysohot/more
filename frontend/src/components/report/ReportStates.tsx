import { Alert, Button, Card, Empty, Progress, Skeleton, Space, Typography } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons';
import type { AnalysisProgress } from '@/types';

const { Text, Title } = Typography;

const stageLabels = [
  '数据采集',
  '比率计算',
  '构建上下文',
  '芒格视角',
  '产业视角',
  '审计视角',
  '综合汇总',
  '报告生成',
];

interface ReportStateProps {
  progress?: AnalysisProgress | null;
  error?: string | null;
  onBack: () => void;
  onRetry?: () => void;
}

export function ReportLoadingState({ progress }: Pick<ReportStateProps, 'progress'>) {
  return (
    <section className="report-workbench report-state-shell" aria-busy="true">
      <Card className="report-state-card">
        <Text className="report-kicker">REPORT PIPELINE</Text>
        <Title level={3}>正在组装结构化投研报告</Title>
        <Text className="report-muted">{progress?.message || '正在读取分析进度和报告内容...'}</Text>
        <Progress percent={progress?.progress ?? 18} strokeColor="#c59b62" trailColor="rgba(255,255,255,0.12)" />
        <div className="report-stage-grid" aria-label="分析流程">
          {stageLabels.map((label) => (
            <span key={label}>{label}</span>
          ))}
        </div>
        <Skeleton active paragraph={{ rows: 4 }} />
      </Card>
    </section>
  );
}

export function ReportEmptyState({ onBack }: Pick<ReportStateProps, 'onBack'>) {
  return (
    <section className="report-workbench report-state-shell">
      <Card className="report-state-card report-paper-card">
        <Empty description="报告尚未生成或已被删除" />
        <div className="report-state-actions">
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回首页</Button>
        </div>
      </Card>
    </section>
  );
}

export function ReportFailedState({ error, progress, onBack, onRetry }: ReportStateProps) {
  return (
    <section className="report-workbench report-state-shell">
      <Card className="report-state-card report-paper-card">
        <Alert
          type="error"
          showIcon
          message="报告生成或加载失败"
          description={error || progress?.message || '当前分析任务未能完成，请返回首页重新发起分析。'}
        />
        <Space className="report-state-actions" wrap>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack}>返回首页</Button>
          {onRetry ? <Button type="primary" icon={<ReloadOutlined />} onClick={onRetry}>重试加载</Button> : null}
        </Space>
      </Card>
    </section>
  );
}
