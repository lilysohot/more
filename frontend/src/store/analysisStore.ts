/**
 * 分析模块状态管理
 * 
 * 使用 Zustand 管理分析相关的全局状态，包括：
 * - 当前分析任务
 * - 分析进度
 * - 分析报告
 * - 分析历史列表
 * - API 配置
 * 
 * 主要功能：
 * - 创建分析任务
 * - 轮询获取进度
 * - 获取报告内容
 * - 管理分析历史
 */

import { create } from 'zustand';
import { Analysis, AnalysisCreate, AnalysisProgress, Report, APIConfig } from '@/types';
import { analysisApi } from '@/api/analysis';
import { apiConfigApi } from '@/api/apiConfig';

const getErrorMessage = (error: unknown, fallback: string) => {
  const detail = (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail;
  return typeof detail === 'string' ? detail : fallback;
};

interface AnalysisState {
  /** 当前分析任务 */
  currentAnalysis: Analysis | null;
  /** 分析进度 */
  progress: AnalysisProgress | null;
  /** 分析报告 */
  report: Report | null;
  /** 分析历史列表 */
  analyses: Analysis[];
  /** 分析总数 */
  total: number;
  /** 默认 API 配置 */
  defaultConfig: APIConfig | null;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 是否正在分析中 */
  isAnalyzing: boolean;
  /** 错误信息 */
  error: string | null;

  /** 创建并启动分析任务 */
  startAnalysis: (data: AnalysisCreate) => Promise<Analysis>;
  /** 获取分析进度 */
  fetchProgress: (analysisId: string) => Promise<AnalysisProgress>;
  /** 获取分析报告 */
  fetchReport: (analysisId: string) => Promise<Report>;
  /** 获取分析历史列表 */
  fetchAnalyses: (skip?: number, limit?: number) => Promise<void>;
  /** 获取默认 API 配置 */
  fetchDefaultConfig: () => Promise<void>;
  /** 删除分析记录 */
  deleteAnalysis: (analysisId: string) => Promise<void>;
  /** 清除当前分析状态 */
  clearCurrentAnalysis: () => void;
  /** 清除错误信息 */
  clearError: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  currentAnalysis: null,
  progress: null,
  report: null,
  analyses: [],
  total: 0,
  defaultConfig: null,
  isLoading: false,
  isAnalyzing: false,
  error: null,

  /**
   * 创建并启动分析任务
   * 
   * @param data - 分析创建参数
   * @returns 创建的分析记录
   */
  startAnalysis: async (data: AnalysisCreate) => {
    set({ isLoading: true, isAnalyzing: true, error: null });
    try {
      const analysis = await analysisApi.createAnalysis(data);
      set({ currentAnalysis: analysis, isLoading: false });
      return analysis;
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error, '创建分析失败'),
        isLoading: false,
        isAnalyzing: false
      });
      throw error;
    }
  },

  /**
   * 获取分析进度
   * 
   * @param analysisId - 分析记录ID
   * @returns 进度信息
   */
  fetchProgress: async (analysisId: string) => {
    try {
      const progress = await analysisApi.getProgress(analysisId);
      set({ progress });
      
      // 如果分析完成或失败，更新状态
      if (progress.status === 'completed' || progress.status === 'failed') {
        set({ isAnalyzing: false });
      }
      
      return progress;
    } catch (error: unknown) {
      set({ error: getErrorMessage(error, '获取进度失败') });
      throw error;
    }
  },

  /**
   * 获取分析报告
   * 
   * @param analysisId - 分析记录ID
   * @returns 报告内容
   */
  fetchReport: async (analysisId: string) => {
    set({ isLoading: true, error: null });
    try {
      const report = await analysisApi.getReport(analysisId);
      set({ report, isLoading: false });
      return report;
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error, '获取报告失败'),
        isLoading: false
      });
      throw error;
    }
  },

  /**
   * 获取分析历史列表
   * 
   * @param skip - 分页偏移量
   * @param limit - 每页数量限制
   */
  fetchAnalyses: async (skip: number = 0, limit: number = 20) => {
    set({ isLoading: true, error: null });
    try {
      const response = await analysisApi.listAnalyses(skip, limit);
      set({ analyses: response.items, total: response.total, isLoading: false });
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error, '获取分析列表失败'),
        isLoading: false
      });
    }
  },

  /**
   * 获取默认 API 配置
   */
  fetchDefaultConfig: async () => {
    try {
      const config = await apiConfigApi.getDefaultConfig();
      set({ defaultConfig: config });
    } catch (error) {
      set({ defaultConfig: null });
    }
  },

  /**
   * 删除分析记录
   * 
   * @param analysisId - 分析记录ID
   */
  deleteAnalysis: async (analysisId: string) => {
    try {
      await analysisApi.deleteAnalysis(analysisId);
      const { analyses } = get();
      set({ 
        analyses: analyses.filter(a => a.id !== analysisId),
        total: get().total - 1
      });
    } catch (error: unknown) {
      set({ error: getErrorMessage(error, '删除分析失败') });
      throw error;
    }
  },

  /**
   * 清除当前分析状态
   */
  clearCurrentAnalysis: () => {
    set({ 
      currentAnalysis: null, 
      progress: null, 
      report: null,
      isAnalyzing: false 
    });
  },

  /**
   * 清除错误信息
   */
  clearError: () => {
    set({ error: null });
  },
}));
