import { CodeOutlined, FileMarkdownOutlined } from '@ant-design/icons';
import { Empty, Tabs } from 'antd';
import ReactMarkdown from 'react-markdown';
import type { Report } from '@/types';

interface OriginalReportTabsProps {
  report: Report;
}

export function OriginalReportTabs({ report }: OriginalReportTabsProps) {
  return (
    <section id="original" className="report-panel report-paper-card">
      <Tabs
        defaultActiveKey="html"
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
