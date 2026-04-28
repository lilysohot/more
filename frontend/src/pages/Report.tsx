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
import { getReportCompanyName, hasStructuredReport } from '@/utils/reportViewModel';

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

  return (
    <div className="report-workbench">
      <ReportCommandHeader
        report={report}
        currentAnalysis={currentAnalysis}
        onBack={handleBack}
        onDownloadMd={handleDownloadMd}
        onDownloadHtml={handleDownloadHtml}
        onExportPdf={handleExportPdf}
        onShare={handleShare}
      />
      <div className="report-layout-grid">
        <nav className="report-anchor-nav" aria-label="报告章节导航">
          {anchorItems.map((item) => <a key={item.href} href={item.href}>{item.label}</a>)}
        </nav>
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
