import React, { useState, useEffect, useRef } from 'react';
import { 
  Typography, 
  Card, 
  Input, 
  Button, 
  Space, 
  Progress, 
  Collapse, 
  Select, 
  Checkbox, 
  message,
} from 'antd';
import { SearchOutlined, SettingOutlined, LoadingOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAnalysisStore } from '@/store/analysisStore';
import { useAPIConfigStore } from '@/store/apiConfigStore';
import { APIConfig } from '@/types';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;
const { Option } = Select;

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState('');
  const [includeCharts, setIncludeCharts] = useState(true);
  const [selectedConfigId, setSelectedConfigId] = useState<string | undefined>(undefined);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const {
    currentAnalysis,
    progress,
    isAnalyzing,
    error,
    startAnalysis,
    fetchProgress,
    clearCurrentAnalysis,
    clearError,
  } = useAnalysisStore();

  const { configs, defaultConfig, fetchConfigs, fetchDefaultConfig } = useAPIConfigStore();

  useEffect(() => {
    fetchConfigs();
    fetchDefaultConfig();
  }, []);

  useEffect(() => {
    if (defaultConfig && !selectedConfigId) {
      setSelectedConfigId(defaultConfig.id);
    }
  }, [defaultConfig]);

  useEffect(() => {
    if (error) {
      message.error(error);
      clearError();
    }
  }, [error]);

  useEffect(() => {
    if (currentAnalysis && isAnalyzing) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const prog = await fetchProgress(currentAnalysis.id);
          if (prog.status === 'completed') {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            message.success('分析完成！');
            navigate(`/report/${currentAnalysis.id}`);
          } else if (prog.status === 'failed') {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            message.error('分析失败，请重试');
          }
        } catch (err) {
          console.error('Failed to fetch progress:', err);
        }
      }, 2000);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [currentAnalysis, isAnalyzing]);

  const handleStartAnalysis = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入公司名称或股票代码');
      return;
    }

    let companyName = inputValue.trim();
    let stockCode: string | undefined = undefined;

    const codeMatch = inputValue.match(/^(\d{6}|[A-Z]{1,5})$/);
    if (codeMatch) {
      stockCode = codeMatch[1];
    }

    try {
      await startAnalysis({
        company_name: companyName,
        stock_code: stockCode,
        include_charts: includeCharts,
        api_config_id: selectedConfigId,
      });
      message.success('分析任务已创建，正在处理中...');
    } catch (err) {
      console.error('Failed to start analysis:', err);
    }
  };

  const handleCancel = () => {
    clearCurrentAnalysis();
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    message.info('已取消当前分析');
  };

  return (
    <div>
      <Card className="mb-6">
        <div className="text-center py-8">
          <Title level={2}>公司分析研报助手</Title>
          <Paragraph className="text-gray-500 mb-8">
            输入公司名称或股票代码，一键生成专业的投资分析研报
          </Paragraph>
          
          <Space.Compact className="w-full max-w-2xl mx-auto">
            <Input
              placeholder="请输入公司名称或股票代码，例如：特变电工、600089、AAPL"
              size="large"
              className="flex-1"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onPressEnter={handleStartAnalysis}
              disabled={isAnalyzing}
            />
            <Button 
              type="primary" 
              size="large" 
              icon={isAnalyzing ? <LoadingOutlined /> : <SearchOutlined />}
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? '分析中...' : '开始分析'}
            </Button>
          </Space.Compact>
        </div>

        <Collapse 
          className="mt-4" 
          defaultActiveKey={[]}
          ghost
        >
          <Panel 
            header={
              <span className="text-gray-600">
                <SettingOutlined className="mr-2" />
                高级选项（可选）
              </span>
            } 
            key="1"
          >
            <div className="space-y-4 pt-2">
              <div className="flex items-center">
                <Text className="w-24">分析模式：</Text>
                <Select 
                  value="standard" 
                  style={{ width: 200 }}
                  disabled
                >
                  <Option value="standard">标准分析</Option>
                </Select>
                <Text type="secondary" className="ml-2 text-sm">（当前阶段仅支持标准分析）</Text>
              </div>

              <div className="flex items-center">
                <Text className="w-24">当前模型：</Text>
                <Select 
                  value={selectedConfigId || 'default'}
                  style={{ width: 200 }}
                  onChange={(value) => {
                    if (value === 'default') {
                      setSelectedConfigId(undefined);
                    } else {
                      setSelectedConfigId(value);
                    }
                  }}
                  disabled={isAnalyzing}
                >
                  <Option value="default">系统默认模型</Option>
                  {configs.map((config: APIConfig) => (
                    <Option key={config.id} value={config.id}>
                      {config.model_name}
                    </Option>
                  ))}
                </Select>
                <Button 
                  type="link" 
                  onClick={() => navigate('/api-config')}
                  disabled={isAnalyzing}
                >
                  配置我的模型
                </Button>
              </div>

              <div className="flex items-center">
                <Text className="w-24">包含图表：</Text>
                <Checkbox 
                  checked={includeCharts}
                  onChange={(e) => setIncludeCharts(e.target.checked)}
                  disabled={isAnalyzing}
                />
              </div>
            </div>
          </Panel>
        </Collapse>

        {isAnalyzing && progress && (
          <Card className="mt-6 bg-gray-50">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <Text strong>分析进度</Text>
                <Button size="small" danger onClick={handleCancel}>
                  取消
                </Button>
              </div>
              <Progress 
                percent={progress.progress} 
                status={progress.status === 'failed' ? 'exception' : 'active'}
              />
              <Text type="secondary">{progress.message}</Text>
            </div>
          </Card>
        )}
      </Card>

      <Card title="功能介绍">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4">
            <div className="text-4xl mb-4">📊</div>
            <Title level={4}>三维合一分析</Title>
            <Paragraph className="text-gray-500">
              芒格视角、产业专家视角、审计专家视角深度分析
            </Paragraph>
          </div>
          
          <div className="text-center p-4">
            <div className="text-4xl mb-4">📈</div>
            <Title level={4}>数据可视化</Title>
            <Paragraph className="text-gray-500">
              自动生成图表，直观展示财务数据和分析结果
            </Paragraph>
          </div>
          
          <div className="text-center p-4">
            <div className="text-4xl mb-4">📄</div>
            <Title level={4}>多格式报告</Title>
            <Paragraph className="text-gray-500">
              支持 Markdown 和 HTML 格式，方便分享和存档
            </Paragraph>
          </div>
        </div>
      </Card>

      <Card title="标准分析说明" className="mt-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <tbody>
              <tr className="border-b">
                <td className="py-2 font-medium w-32">分析模式</td>
                <td className="py-2">标准分析（默认）</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 font-medium">数据验证</td>
                <td className="py-2">当前阶段不涉及数据交叉验证流程</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 font-medium">AI 模型</td>
                <td className="py-2">系统默认接入，用户也可自行配置 API</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 font-medium">分析流程</td>
                <td className="py-2">配置的 AI 直接执行三维合一分析</td>
              </tr>
              <tr>
                <td className="py-2 font-medium">适用场景</td>
                <td className="py-2">快速获取公司分析报告</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Paragraph className="mt-4 text-gray-500">
          💡 提示：系统默认提供 AI 模型，用户无需配置即可使用。如需使用自己的 API，可在高级选项中配置。
        </Paragraph>
      </Card>
    </div>
  );
};

export default HomePage;
