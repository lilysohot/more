import request from '@/utils/request';
import { Token, LoginCredentials, RegisterData } from '@/types';

export const authApi = {
  /**
   * 用户登录
   * 
   * @param credentials - 登录凭证
   * @returns 包含 token 和用户信息的响应
   */
  login: async (credentials: LoginCredentials): Promise<Token> => {
    return request({
      url: '/auth/login',
      method: 'POST',
      data: credentials,
    });
  },

  /**
   * 用户注册
   * 
   * @param data - 注册数据
   * @returns 包含 token 和用户信息的响应
   */
  register: async (data: RegisterData): Promise<Token> => {
    return request({
      url: '/auth/register',
      method: 'POST',
      data,
    });
  },

  /**
   * 用户登出
   */
  logout: async (): Promise<void> => {
    return request({
      url: '/auth/logout',
      method: 'POST',
    });
  },
};
