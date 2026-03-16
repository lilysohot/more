import React, { useEffect, useState } from 'react';
import { Card, Descriptions, Button, Modal, Form, Input, message, Spin, Statistic, Row, Col, List, Tag } from 'antd';
import { EditOutlined, FileTextOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store';
import { userApi } from '@/api';
import { UserStats, Analysis } from '@/types';
import dayjs from 'dayjs';

const ProfilePage: React.FC = () => {
  const { user, setUser } = useAuthStore();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [history, setHistory] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, historyData] = await Promise.all([
        userApi.getStats(),
        userApi.getHistory(0, 10),
      ]);
      setStats(statsData);
      setHistory(historyData);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (values: { username: string }) => {
    try {
      const updatedUser = await userApi.updateProfile(values);
      setUser(updatedUser);
      message.success('更新成功');
      setEditModalVisible(false);
    } catch {
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '等待中' },
      processing: { color: 'processing', text: '分析中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
    };
    const config = statusMap[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Card title="个人信息" extra={
        <Button icon={<EditOutlined />} onClick={() => {
          form.setFieldsValue({ username: user?.username || '' });
          setEditModalVisible(true);
        }}>
          编辑
        </Button>
      }>
        <Descriptions column={2}>
          <Descriptions.Item label="邮箱">{user?.email}</Descriptions.Item>
          <Descriptions.Item label="用户名">{user?.username || '未设置'}</Descriptions.Item>
          <Descriptions.Item label="注册时间">
            {dayjs(user?.created_at).format('YYYY-MM-DD HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="账号状态">
            <Tag color={user?.is_active ? 'success' : 'error'}>
              {user?.is_active ? '正常' : '已禁用'}
            </Tag>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="使用统计" className="mt-6">
        <Row gutter={24}>
          <Col span={8}>
            <Statistic
              title="已生成报告"
              value={stats?.total_analyses || 0}
              suffix="份"
              prefix={<FileTextOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="会员时长"
              value={dayjs().diff(dayjs(stats?.member_since), 'day')}
              suffix="天"
            />
          </Col>
        </Row>
      </Card>

      <Card title="最近分析记录" className="mt-6">
        <List
          dataSource={history}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button type="link" key="view">查看</Button>,
                <Button type="link" key="download">下载</Button>,
              ]}
            >
              <List.Item.Meta
                title={`${item.company_name}${item.stock_code ? ` (${item.stock_code})` : ''}`}
                description={dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
              />
              {getStatusTag(item.status)}
            </List.Item>
          )}
          locale={{ emptyText: '暂无分析记录' }}
        />
      </Card>

      <Modal
        title="编辑个人信息"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdateProfile}
        >
          <Form.Item name="username" label="用户名">
            <Input placeholder="请输入用户名" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProfilePage;
