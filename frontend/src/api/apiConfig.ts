import request from '@/utils/request';
import {
  APIConfig,
  APIConfigCreate,
  APIConfigUpdate,
  APIConfigTest,
  APIConfigTestResult,
} from '@/types';

export const apiConfigApi = {
  getConfigs: async (): Promise<APIConfig[]> => {
    return request({
      url: '/api-configs',
      method: 'GET',
    });
  },

  getDefaultConfig: async (): Promise<APIConfig> => {
    return request({
      url: '/api-configs/default',
      method: 'GET',
    });
  },

  createConfig: async (data: APIConfigCreate): Promise<APIConfig> => {
    return request({
      url: '/api-configs',
      method: 'POST',
      data,
    });
  },

  updateConfig: async (id: string, data: APIConfigUpdate): Promise<APIConfig> => {
    return request({
      url: `/api-configs/${id}`,
      method: 'PUT',
      data,
    });
  },

  deleteConfig: async (id: string): Promise<void> => {
    return request({
      url: `/api-configs/${id}`,
      method: 'DELETE',
    });
  },

  setDefault: async (id: string): Promise<APIConfig> => {
    return request({
      url: `/api-configs/${id}/set-default`,
      method: 'POST',
    });
  },

  testConfig: async (data: APIConfigTest): Promise<APIConfigTestResult> => {
    return request({
      url: '/api-configs/test',
      method: 'POST',
      data,
    });
  },
};
