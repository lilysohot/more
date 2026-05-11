import { useEffect, useState } from 'react';
import { Alert, message } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { AgentTriad, EvidenceShelf, RiskLedger } from '@/components/report/ReportAgents';
import { ReportCommandHeader } from '@/components/report/ReportCommandHeader';
import { MetricMatrix, VisualInsightPanel } from '@/components/report/ReportMetrics';
import { ReportEmptyState, ReportFailedState, ReportLoadingState } from '@/components/report/ReportStates';
import { CompanyProfilePanel, ConsensusDisagreementPanel, HeroVerdict } from '@/components/report/ReportSummaryPanels';
import { OriginalReportTabs } from '@/components/report/OriginalReportTabs';
import { useAnalysisStore } from '@/store/analysisStore';
import { formatAgentRoleLabel, formatFinancialFieldLabel, formatPlainDate, getFinancialCoverage, getReportCompanyName, hasStructuredReport } from '@/utils/reportViewModel';

const anchorItems = [
  { href: '#verdict', label: '01 结论' },
  { href: '#profile', label: '02 公司画像' },
  { href: '#metrics', label: '03 指标矩阵' },
  { href: '#visuals', label: '04 图表' },
  { href: '#agents', label: '05 Agent' },
  { href: '#consensus', label: '06 共识分歧' },
  { href: '#risks', label: '07 风险' },
  { href: '#evidence', label: '08 证据' },
  { href: '#original', label: '09 原文' },
];

export default function ReportPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const {
    report,
    currentAnalysis,
    progress,
    isLoading,
    error,
    fetchReport,
    fetchProgress,
    clearError,
  } = useAnalysisStore();

  useEffect(() => {
    let cancelled = false;

    async function loadReport() {
      if (!analysisId) {
        setIsChecking(false);
        setLoadError('缺少分析任务 ID');
        return;
      }

      setIsChecking(true);
      setLoadError(null);

      try {
        const latestProgress = await fetchProgress(analysisId);
        if (cancelled) return;

        if (latestProgress.status === 'failed') {
          setLoadError(latestProgress.message || '分析失败，请重新发起任务');
          return;
        }

        if (latestProgress.status !== 'completed') {
          setLoadError(`分析尚未完成，当前阶段：${latestProgress.message}`);
          return;
        }

        await fetchReport(analysisId);
      } catch (requestError) {
        if (!cancelled) {
          setLoadError(requestError instanceof Error ? requestError.message : '获取报告失败');
        }
      } finally {
        if (!cancelled) setIsChecking(false);
      }
    }

    loadReport();

    return () => {
      cancelled = true;
    };
  }, [analysisId, fetchProgress, fetchReport]);

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [clearError, error]);

  const handleBack = () => navigate('/');

  const handleRetry = () => {
    if (analysisId) {
      setIsChecking(true);
      setLoadError(null);
      fetchReport(analysisId)
        .catch((requestError) => {
          setLoadError(requestError instanceof Error ? requestError.message : '获取报告失败');
        })
        .finally(() => setIsChecking(false));
    }
  };

  const handleDownloadMd = () => {
    if (!report?.content_md) return;
    downloadBlob(report.content_md, `${getReportCompanyName(report, currentAnalysis)}_分析报告.md`, 'text/markdown');
    message.success('Markdown 文件下载成功');
  };

  const handleDownloadHtml = () => {
    if (!report?.content_html) return;
    downloadBlob(report.content_html, `${getReportCompanyName(report, currentAnalysis)}_分析报告.html`, 'text/html');
    message.success('HTML 文件下载成功');
  };

  const handleExportPdf = () => {
    message.info('已打开打印对话框，可选择“另存为 PDF”。');
    window.print();
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      message.success('链接已复制到剪贴板');
    }).catch(() => {
      message.error('复制链接失败');
    });
  };

  if (isChecking || isLoading) {
    return <ReportLoadingState progress={progress} />;
  }

  if (loadError && !report) {
    return <ReportFailedState error={loadError} progress={progress} onBack={handleBack} onRetry={handleRetry} />;
  }

  if (!report) {
    return <ReportEmptyState onBack={handleBack} />;
  }

  const structured = hasStructuredReport(report);
  const coverage = getFinancialCoverage(report.financials);
  const agents = report.agents || [];
  const completedAgentCount = report.data_quality?.completed_agent_count ?? agents.filter((agent) => agent.status === 'completed').length;
  const availableFormats = [report.content_html ? 'HTML' : null, report.content_md ? 'Markdown' : null].filter(Boolean);
  const failedAgentRoles = report.data_quality?.failed_agent_roles || [];
  const missingFinancialFields = report.data_quality?.missing_financial_fields || [];
  const overviewItems = [
    { label: '报告形态', value: structured ? '结构化投研' : '原文降级' },
    { label: '数据日期', value: formatPlainDate(report.company?.data_date) },
    { label: '财务覆盖', value: `${coverage.covered} / ${coverage.total}` },
    { label: 'Agent 完成度', value: agents.length ? `${completedAgentCount} / ${agents.length}` : '暂无' },
    { label: '原文附录', value: availableFormats.length ? availableFormats.join(' / ') : '无附件' },
  ];
  const readingNotes = structured
    ? [
      '先读结论总览，再看共识分歧与风险台账。',
      '关键结论需要回到证据区核对来源与日期。',
      '原文附录保留模型完整输出，适合逐段复查。',
    ]
    : [
      '当前仅提供原文报告，请优先查看附录内容。',
      '结构化模块会在后端补齐后自动恢复展示。',
      '若要做人工判断，请结合公告、财报和行情终端二次核验。',
    ];

  return (
    <div className="report-workbench">
      <div className="report-shell">
        <ReportCommandHeader
          report={report}
          currentAnalysis={currentAnalysis}
          onBack={handleBack}
          onDownloadMd={handleDownloadMd}
          onDownloadHtml={handleDownloadHtml}
          onExportPdf={handleExportPdf}
          onShare={handleShare}
        />
        <section className="report-overview-strip" aria-label="报告摘要">
          {overviewItems.map((item) => (
            <article key={item.label} className="report-overview-card">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </article>
          ))}
        </section>
        <div className="report-layout-grid">
          <main className="report-main-stack">
            {structured ? (
              <>
                <HeroVerdict report={report} />
                <CompanyProfilePanel report={report} />
                <MetricMatrix report={report} />
                <VisualInsightPanel report={report} />
                <AgentTriad report={report} />
                <ConsensusDisagreementPanel report={report} />
                <RiskLedger report={report} />
                <EvidenceShelf report={report} />
              </>
            ) : (
              <Alert
                type="warning"
                showIcon
                message="当前报告缺少结构化数据"
                description="已降级展示原文报告。后端完成结构化报告组装后，本页面会自动展示投研工作台模块。"
              />
            )}
            <OriginalReportTabs report={report} />
            <p className="report-disclaimer">本报告仅供研究参考，不构成投资建议。模型输出可能受数据延迟、数据缺失、口径差异和推理偏差影响。</p>
          </main>
          <aside className="report-sidebar-stack">
            <section className="report-sidebar-card">
              <p className="report-kicker">SECTION MAP</p>
              <h2 className="report-sidebar-title">快速定位</h2>
              <p className="report-sidebar-copy">按阅读顺序排列章节，适合先抓结论，再回溯证据。</p>
              <nav className="report-anchor-nav" aria-label="报告章节导航">
                {anchorItems.map((item) => <a key={item.href} href={item.href}>{item.label}</a>)}
              </nav>
            </section>
            <section className="report-sidebar-card">
              <p className="report-kicker">READING GUIDE</p>
              <h2 className="report-sidebar-title">阅读说明</h2>
              <ul className="report-sidebar-list">
                {readingNotes.map((note) => <li key={note}>{note}</li>)}
              </ul>
            </section>
            <section className="report-sidebar-card">
              <p className="report-kicker">DATA QUALITY</p>
              <h2 className="report-sidebar-title">数据状态</h2>
              <p className="report-sidebar-copy">
                {report.data_quality?.quality_note || '当前页优先展示结构化结果，数据缺口与降级角色会在这里集中提示。'}
              </p>
              <div className="report-sidebar-chip-grid">
                {failedAgentRoles.map((role) => (
                  <span key={role} className="report-sidebar-chip report-sidebar-chip-warning">降级 {formatAgentRoleLabel(role)}</span>
                ))}
                {missingFinancialFields.slice(0, 6).map((field) => (
                  <span key={field} className="report-sidebar-chip">缺失 {formatFinancialFieldLabel(field)}</span>
                ))}
                {!failedAgentRoles.length && !missingFinancialFields.length ? (
                  <span className="report-sidebar-chip report-sidebar-chip-muted">未发现额外缺口</span>
                ) : null}
              </div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
