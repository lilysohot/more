import { ArrowLeftOutlined, CodeOutlined, FileMarkdownOutlined, FilePdfOutlined, MoreOutlined, ShareAltOutlined } from '@ant-design/icons';
import { Button, Dropdown, Space, Tag, Typography } from 'antd';
import type { MenuProps } from 'antd';
import type { Analysis, Report } from '@/types';
import { formatAgentRoleLabel, formatDateTime, formatPlainDate, formatScore, getFinancialCoverage, getReportCompanyName, getReportStockCode } from '@/utils/reportViewModel';

const { Text, Title } = Typography;

interface ReportCommandHeaderProps {
  report: Report;
  currentAnalysis?: Analysis | null;
  onBack: () => void;
  onDownloadMd: () => void;
  onDownloadHtml: () => void;
  onExportPdf: () => void;
  onShare: () => void;
}

export function ReportCommandHeader({
  report,
  currentAnalysis,
  onBack,
  onDownloadMd,
  onDownloadHtml,
  onExportPdf,
  onShare,
}: ReportCommandHeaderProps) {
  const companyName = getReportCompanyName(report, currentAnalysis);
  const stockCode = getReportStockCode(report, currentAnalysis);
  const failedAgentRoles = report.data_quality?.failed_agent_roles || [];
  const financialCoverage = getFinancialCoverage(report.financials);
  const totalAgents = report.agents?.length || 0;
  const completedAgentCount = report.data_quality?.completed_agent_count ?? report.agents?.filter((agent) => agent.status === 'completed').length ?? 0;
  const headerHighlights = [
    { label: '投资判断', value: report.synthesis?.investment_decision || '等待综合结论' },
    { label: '综合评分', value: formatScore(report.synthesis?.final_score ?? null) },
    { label: '数据完整度', value: `${financialCoverage.covered} / ${financialCoverage.total}` },
    { label: 'Agent 进度', value: totalAgents ? `${completedAgentCount} / ${totalAgents} 已完成` : '暂无结构化输出' },
  ];
  const items: MenuProps['items'] = [
    { key: 'md', icon: <FileMarkdownOutlined />, label: '下载 Markdown', onClick: onDownloadMd },
    { key: 'html', icon: <CodeOutlined />, label: '下载 HTML', onClick: onDownloadHtml },
    { key: 'pdf', icon: <FilePdfOutlined />, label: '导出 PDF', onClick: onExportPdf },
    { key: 'share', icon: <ShareAltOutlined />, label: '复制分享链接', onClick: onShare },
  ];

  return (
    <header className="report-command-header">
      <div className="report-command-topline">
        <Button className="report-dark-button" icon={<ArrowLeftOutlined />} onClick={onBack}>返回</Button>
        <Text className="report-kicker">RESEARCH DOSSIER</Text>
      </div>
      <div className="report-command-main">
        <div className="report-command-copy">
          <Title level={1}>{companyName}</Title>
          <p className="report-command-summary">
            {report.synthesis?.company_profile || '当前报告已保留原文附录，结构化摘要会随着后端组装结果自动补齐。'}
          </p>
          <Space wrap className="report-meta-row">
            <Tag className="report-code-tag">{stockCode}</Tag>
            <span>{report.company?.industry || '行业未披露'}</span>
            <span>{report.company?.exchange || '交易所未知'}</span>
            <span>数据源：{report.company?.data_source || '未标注'}</span>
            <span>数据日期：{formatPlainDate(report.company?.data_date)}</span>
          </Space>
        </div>
        <div className="report-command-actions">
          <Space wrap>
            <Button icon={<FileMarkdownOutlined />} onClick={onDownloadMd}>下载 Markdown</Button>
            <Button icon={<CodeOutlined />} onClick={onDownloadHtml}>下载 HTML</Button>
            <Button icon={<FilePdfOutlined />} onClick={onExportPdf}>导出 PDF</Button>
            <Button type="primary" icon={<ShareAltOutlined />} onClick={onShare}>分享</Button>
          </Space>
          <Dropdown menu={{ items }} placement="bottomRight">
            <Button className="report-mobile-action" icon={<MoreOutlined />}>更多</Button>
          </Dropdown>
        </div>
      </div>
      <div className="report-command-highlight-grid">
        {headerHighlights.map((item) => (
          <div key={item.label} className="report-command-highlight">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
      <div className="report-command-footer">
        <span>生成时间：{formatDateTime(report.created_at)}</span>
        <span>状态：分析完成</span>
        {failedAgentRoles.length ? <span>降级角色：{formatAgentRoleLabels(failedAgentRoles)}</span> : null}
      </div>
    </header>
  );
}

function formatAgentRoleLabels(roles: string[]): string {
  return roles.map((role) => formatAgentRoleLabel(role)).join(' / ');
}
