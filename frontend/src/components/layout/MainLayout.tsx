import React, { useEffect } from 'react';
import { Layout, Menu, Dropdown, Avatar, Space, Grid } from 'antd';
import { UserOutlined, LogoutOutlined, SettingOutlined, HomeOutlined } from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store';

const { Header, Content, Sider } = Layout;
const { useBreakpoint } = Grid;

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const screens = useBreakpoint();
  const { user, logout, isAuthenticated } = useAuthStore();

  useEffect(() => {
    // 检查本地存储中的 token
    const token = localStorage.getItem('token');
    if (!token && !location.pathname.includes('/login') && !location.pathname.includes('/register')) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate, location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'api-config',
      icon: <SettingOutlined />,
      label: 'API 配置',
      onClick: () => navigate('/api-config'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const siderMenuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
      onClick: () => navigate('/'),
    },
  ];

  if (!isAuthenticated) {
    return <Outlet />;
  }

  return (
    <Layout className="min-h-screen">
      <Header className="bg-white shadow-sm flex items-center justify-between px-6">
        <div className="flex items-center">
          <h1 className="text-xl font-bold text-gray-800 m-0">
            <button type="button" className="bg-transparent border-0 p-0 cursor-pointer font-inherit text-inherit" onClick={() => navigate('/')}>公司分析研报助手</button>
          </h1>
        </div>
        
        <div className="flex items-center">
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space className="cursor-pointer">
              <Avatar icon={<UserOutlined />} />
              <span>{user?.username || user?.email}</span>
            </Space>
          </Dropdown>
        </div>
      </Header>
      
      <Layout>
        {screens.md ? (
          <Sider width={200} className="bg-white">
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              items={siderMenuItems}
              className="h-full border-r"
            />
          </Sider>
        ) : null}
        
        <Content className="p-6 bg-gray-50">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
