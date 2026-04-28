import { create } from 'zustand';
import { APIConfig, APIConfigCreate, APIConfigUpdate, APIConfigTest } from '@/types';
import { apiConfigApi } from '@/api';

interface APIConfigState {
  configs: APIConfig[];
  defaultConfig: APIConfig | null;
  isLoading: boolean;
  
  fetchConfigs: () => Promise<void>;
  fetchDefaultConfig: () => Promise<void>;
  createConfig: (data: APIConfigCreate) => Promise<APIConfig>;
  updateConfig: (id: string, data: APIConfigUpdate) => Promise<APIConfig>;
  deleteConfig: (id: string) => Promise<void>;
  setDefault: (id: string) => Promise<void>;
  testConfig: (data: APIConfigTest) => Promise<{ success: boolean; message: string }>;
}

export const useAPIConfigStore = create<APIConfigState>((set) => ({
  configs: [],
  defaultConfig: null,
  isLoading: false,

  fetchConfigs: async () => {
    set({ isLoading: true });
    try {
      const configs = await apiConfigApi.getConfigs();
      set({ configs, isLoading: false });
      
      const defaultConfig = configs.find(c => c.is_default) || null;
      set({ defaultConfig });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchDefaultConfig: async () => {
    try {
      const defaultConfig = await apiConfigApi.getDefaultConfig();
      set({ defaultConfig });
    } catch {
      set({ defaultConfig: null });
    }
  },

  createConfig: async (data: APIConfigCreate) => {
    const config = await apiConfigApi.createConfig(data);
    set((state) => ({
      configs: [config, ...state.configs],
      defaultConfig: config.is_default ? config : state.defaultConfig,
    }));
    return config;
  },

  updateConfig: async (id: string, data: APIConfigUpdate) => {
    const config = await apiConfigApi.updateConfig(id, data);
    set((state) => ({
      configs: state.configs.map((c) => (c.id === id ? config : c)),
      defaultConfig: config.is_default ? config : state.defaultConfig,
    }));
    return config;
  },

  deleteConfig: async (id: string) => {
    await apiConfigApi.deleteConfig(id);
    set((state) => ({
      configs: state.configs.filter((c) => c.id !== id),
      defaultConfig: state.defaultConfig?.id === id ? null : state.defaultConfig,
    }));
  },

  setDefault: async (id: string) => {
    const config = await apiConfigApi.setDefault(id);
    set((state) => ({
      configs: state.configs.map((c) => ({
        ...c,
        is_default: c.id === id,
      })),
      defaultConfig: config,
    }));
  },

  testConfig: async (data: APIConfigTest) => {
    const result = await apiConfigApi.testConfig(data);
    return result;
  },
}));
