import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '@/components/layout/MainLayout';
import AuthPage from '@/pages/Login';
import HomePage from '@/pages/Home';
import ProfilePage from '@/pages/Profile';
import ApiConfigPage from '@/pages/ApiConfig';
import ReportPage from '@/pages/Report';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <AuthPage />,
  },
  {
    path: '/register',
    element: <AuthPage />,
  },
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'api-config',
        element: <ApiConfigPage />,
      },
      {
        path: 'report/:analysisId',
        element: <ReportPage />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export default router;
