import { CodeOutlined, FileMarkdownOutlined } from '@ant-design/icons';
import { Empty, Tabs, Typography } from 'antd';
import ReactMarkdown from 'react-markdown';
import type { Report } from '@/types';

const { Text, Title } = Typography;

interface OriginalReportTabsProps {
  report: Report;
}

export function OriginalReportTabs({ report }: OriginalReportTabsProps) {
  const defaultActiveKey = report.content_html ? 'html' : 'md';

  return (
    <section id="original" className="report-panel report-paper-card">
      <div className="report-section-heading">
        <Text className="report-kicker">09 / ORIGINAL REPORT</Text>
        <Title level={2}>原文附录</Title>
      </div>
      <Tabs
        defaultActiveKey={defaultActiveKey}
        items={[
          {
            key: 'html',
            label: <span><CodeOutlined /> HTML 原文</span>,
            children: report.content_html ? (
              <iframe className="report-original-frame" title="HTML 原文报告" sandbox="allow-scripts" srcDoc={report.content_html} />
            ) : <Empty description="HTML 内容不可用" />,
          },
          {
            key: 'md',
            label: <span><FileMarkdownOutlined /> Markdown 原文</span>,
            children: report.content_md ? (
              <div className="report-original-markdown">
                <ReactMarkdown>{report.content_md}</ReactMarkdown>
              </div>
            ) : <Empty description="Markdown 内容不可用" />,
          },
        ]}
      />
    </section>
  );
}
