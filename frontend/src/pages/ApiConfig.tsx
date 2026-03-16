import { useAPIConfigStore } from '@/store';
import { APIConfig, APIConfigCreate, APIConfigUpdate } from '@/types';
import {
  CheckOutlined,
  DeleteOutlined,
  EditOutlined,
  ExperimentOutlined,
  PlusOutlined
} from '@ant-design/icons';
import {
  Alert,
  Button,
  Card,
  Form, Input,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import React, { useEffect, useState } from 'react';

const PROVIDERS = [
  { value: 'dashscope', label: 'DashScope（通义千问）' },
  { value: 'openai', label: 'OpenAI GPT' },
  { value: 'claude', label: 'Claude' },
  { value: 'custom', label: '自定义' },
];

const ApiConfigPage: React.FC = () => {
  const {
    configs, isLoading, fetchConfigs, createConfig,
    updateConfig, deleteConfig, setDefault, testConfig
  } = useAPIConfigStore();
  const [modalVisible, setModalVisible] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState<APIConfig | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [form] = Form.useForm();
  const [testForm] = Form.useForm();

  useEffect(() => {
    fetchConfigs();
  }, [fetchConfigs]);

  const handleCreate = () => {
    setEditingConfig(null);
    form.resetFields();
    form.setFieldsValue({ is_default: false });
    setModalVisible(true);
  };

  const handleEdit = (record: APIConfig) => {
    setEditingConfig(record);
    form.setFieldsValue({
      model_name: record.model_name,
      provider: record.provider,
      api_key: '',
      base_url: record.base_url,
      model_version: record.model_version,
      is_default: record.is_default,
    });
    setModalVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingConfig) {
        const updateData: APIConfigUpdate = {};
        if (values.model_name) updateData.model_name = values.model_name;
        if (values.provider) updateData.provider = values.provider;
        if (values.api_key) updateData.api_key = values.api_key;
        if (values.base_url !== undefined) updateData.base_url = values.base_url;
        if (values.model_version !== undefined) updateData.model_version = values.model_version;
        if (values.is_default !== undefined) updateData.is_default = values.is_default;

        await updateConfig(editingConfig.id, updateData);
        message.success('更新成功');
      } else {
        const createData: APIConfigCreate = {
          model_name: values.model_name,
          provider: values.provider,
          api_key: values.api_key,
          base_url: values.base_url,
          model_version: values.model_version,
          is_default: values.is_default,
        };
        await createConfig(createData);
        message.success('创建成功');
      }
      setModalVisible(false);
    } catch {
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteConfig(id);
      message.success('删除成功');
    } catch {
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await setDefault(id);
      message.success('已设为默认');
    } catch {
    }
  };

  const handleTest = (record: APIConfig) => {
    testForm.setFieldsValue({
      provider: record.provider,
      api_key: '',
      base_url: record.base_url,
      model_version: record.model_version,
    });
    setTestModalVisible(true);
    setTestResult(null);
  };

  const handleTestSubmit = async (values: any) => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testConfig(values);
      setTestResult(result);
    } catch {
      setTestResult({ success: false, message: '测试失败' });
    } finally {
      setTesting(false);
    }
  };

  const columns: ColumnsType<APIConfig> = [
    {
      title: '模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => {
        const p = PROVIDERS.find(item => item.value === provider);
        return p?.label || provider;
      },
    },
    {
      title: 'API Key',
      dataIndex: 'api_key_masked',
      key: 'api_key_masked',
    },
    {
      title: '模型版本',
      dataIndex: 'model_version',
      key: 'model_version',
      render: (version: string) => version || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_default',
      key: 'is_default',
      render: (isDefault: boolean) => (
        isDefault ? <Tag color="success">默认</Tag> : <Tag>普通</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {!record.is_default && (
            <Button
              type="link"
              icon={<CheckOutlined />}
              onClick={() => handleSetDefault(record.id)}
            >
              设为默认
            </Button>
          )}
          <Button
            type="link"
            icon={<ExperimentOutlined />}
            onClick={() => handleTest(record)}
          >
            测试
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此配置吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Card
        title="API 配置管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            添加新模型
          </Button>
        }
      >
        <Alert
          message="安全提示"
          description="您的 API Key 将使用 AES 加密存储，仅在调用时解密。建议定期更换 API Key 以确保安全。"
          type="info"
          showIcon
          className="mb-4"
        />

        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          pagination={false}
          locale={{ emptyText: '暂无 API 配置，请点击"添加新模型"按钮创建' }}
        />
      </Card>

      <Modal
        title={editingConfig ? '编辑 API 配置' : '添加 API 配置'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如：我的 GPT-4" />
          </Form.Item>

          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select options={PROVIDERS} placeholder="请选择提供商" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={editingConfig ? [] : [{ required: true, message: '请输入 API Key' }]}
          >
            <Input.Password placeholder={editingConfig ? '留空则保持原值' : '请输入 API Key'} />
          </Form.Item>

          <Form.Item name="base_url" label="Base URL（可选）">
            <Input placeholder="例如：https://api.openai.com/v1" />
          </Form.Item>

          <Form.Item name="model_version" label="模型版本（可选）">
            <Input placeholder="例如：gpt-4-turbo-preview" />
          </Form.Item>

          <Form.Item name="is_default" label="设为默认" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="测试 API 连接"
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        onOk={() => testForm.submit()}
        confirmLoading={testing}
      >
        <Form
          form={testForm}
          layout="vertical"
          onFinish={handleTestSubmit}
        >
          <Form.Item name="provider" label="提供商">
            <Select options={PROVIDERS} disabled />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: true, message: '请输入 API Key' }]}
          >
            <Input.Password placeholder="请输入 API Key 进行测试" />
          </Form.Item>

          <Form.Item name="base_url" label="Base URL">
            <Input placeholder="可选" />
          </Form.Item>

          <Form.Item name="model_version" label="模型版本">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>

        {testResult && (
          <Alert
            message={testResult.success ? '连接成功' : '连接失败'}
            description={testResult.message}
            type={testResult.success ? 'success' : 'error'}
            showIcon
          />
        )}
      </Modal>
    </div>
  );
};

export default ApiConfigPage;
