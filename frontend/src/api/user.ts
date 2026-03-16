import request from '@/utils/request';
import { User, UserUpdate, Analysis, UserStats } from '@/types';

export const userApi = {
  getProfile: async (): Promise<User> => {
    return request({
      url: '/users/profile',
      method: 'GET',
    });
  },

  updateProfile: async (data: UserUpdate): Promise<User> => {
    return request({
      url: '/users/profile',
      method: 'PUT',
      data,
    });
  },

  getHistory: async (skip: number = 0, limit: number = 20): Promise<Analysis[]> => {
    return request({
      url: '/users/history',
      method: 'GET',
      params: { skip, limit },
    });
  },

  getStats: async (): Promise<UserStats> => {
    return request({
      url: '/users/stats',
      method: 'GET',
    });
  },
};
