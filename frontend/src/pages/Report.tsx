import React, { useEffect, useState } from 'react';
import { 
  Typography, 
  Card, 
  Button, 
  Space, 
  Tabs, 
  Spin, 
  message,
  Empty,
} from 'antd';
import { 
  DownloadOutlined, 
  ShareAltOutlined, 
  FileMarkdownOutlined,
  CodeOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { useAnalysisStore } from '@/store/analysisStore';
import ReactMarkdown from 'react-markdown';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const ReportPage: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'html' | 'md'>('html');
  
  const {
    report,
    currentAnalysis,
    isLoading,
    error,
    fetchReport,
    fetchProgress,
    clearError,
  } = useAnalysisStore();

  useEffect(() => {
    if (analysisId) {
      fetchProgress(analysisId).then((progress) => {
        if (progress.status === 'completed') {
          fetchReport(analysisId);
        } else {
          message.warning('分析尚未完成，请稍后再试');
          navigate('/');
        }
      }).catch(() => {
        message.error('获取分析状态失败');
        navigate('/');
      });
    }
  }, [analysisId]);

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error]);

  const handleDownloadMd = () => {
    if (!report?.content_md) return;
    
    const blob = new Blob([report.content_md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentAnalysis?.company_name || 'report'}_分析报告.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('Markdown 文件下载成功');
  };

  const handleDownloadHtml = () => {
    if (!report?.content_html) return;
    
    const blob = new Blob([report.content_html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentAnalysis?.company_name || 'report'}_分析报告.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('HTML 文件下载成功');
  };

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      message.success('链接已复制到剪贴板');
    }).catch(() => {
      message.error('复制链接失败');
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Spin size="large" tip="加载报告中..." />
      </div>
    );
  }

  if (!report) {
    return (
      <Card>
        <Empty description="报告不存在或尚未生成" />
        <div className="text-center mt-4">
          <Button onClick={() => navigate('/')}>返回首页</Button>
        </div>
      </Card>
    );
  }

  return (
    <div>
      <Card className="mb-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <Button 
              type="text" 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/')}
              className="mr-2"
            />
            <Title level={4} className="mb-0">
              {currentAnalysis?.company_name}（{currentAnalysis?.stock_code || '未知'}）深度分析报告
            </Title>
          </div>
          <Space>
            <Button 
              icon={<FileMarkdownOutlined />} 
              onClick={handleDownloadMd}
            >
              Markdown 下载
            </Button>
            <Button 
              icon={<CodeOutlined />} 
              onClick={handleDownloadHtml}
            >
              HTML 下载
            </Button>
            <Button 
              icon={<ShareAltOutlined />} 
              onClick={handleShare}
            >
              分享
            </Button>
          </Space>
        </div>
      </Card>

      <Card>
        <Tabs activeKey={activeTab} onChange={(key) => setActiveTab(key as 'html' | 'md')}>
          <TabPane 
            tab={<span><CodeOutlined /> HTML 预览</span>} 
            key="html"
          >
            {report.content_html ? (
              <div 
                className="report-content"
                dangerouslySetInnerHTML={{ __html: report.content_html }}
                style={{
                  padding: '20px',
                  backgroundColor: '#fff',
                  borderRadius: '8px',
                }}
              />
            ) : (
              <Empty description="HTML 内容不可用" />
            )}
          </TabPane>
          <TabPane 
            tab={<span><FileMarkdownOutlined /> Markdown 预览</span>} 
            key="md"
          >
            {report.content_md ? (
              <div className="prose max-w-none p-4">
                <ReactMarkdown>{report.content_md}</ReactMarkdown>
              </div>
            ) : (
              <Empty description="Markdown 内容不可用" />
            )}
          </TabPane>
        </Tabs>
      </Card>

      <style>{`
        .report-content {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          line-height: 1.8;
          color: #333;
        }
        .report-content h1 {
          font-size: 2em;
          margin: 0.67em 0;
          border-bottom: 2px solid #667eea;
          padding-bottom: 10px;
        }
        .report-content h2 {
          font-size: 1.5em;
          margin: 0.83em 0;
          color: #667eea;
        }
        .report-content h3 {
          font-size: 1.17em;
          margin: 1em 0;
        }
        .report-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 15px 0;
        }
        .report-content th,
        .report-content td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid #eee;
        }
        .report-content th {
          background: #f8f9fa;
          font-weight: 600;
        }
        .report-content tr:hover {
          background: #f8f9fa;
        }
        .report-content blockquote {
          border-left: 4px solid #667eea;
          padding-left: 16px;
          margin: 16px 0;
          color: #666;
        }
        .report-content ul, .report-content ol {
          padding-left: 24px;
          margin: 16px 0;
        }
        .report-content li {
          margin: 8px 0;
        }
        .prose {
          max-width: 100%;
        }
        .prose h1 {
          font-size: 2em;
          margin-bottom: 0.67em;
        }
        .prose h2 {
          font-size: 1.5em;
          margin-bottom: 0.83em;
          color: #667eea;
        }
        .prose h3 {
          font-size: 1.17em;
          margin-bottom: 1em;
        }
        .prose table {
          width: 100%;
          border-collapse: collapse;
        }
        .prose th, .prose td {
          border: 1px solid #ddd;
          padding: 8px 12px;
        }
        .prose th {
          background-color: #f5f5f5;
        }
      `}</style>
    </div>
  );
};

export default ReportPage;
