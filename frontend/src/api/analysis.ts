/**
 * 分析模块 API 调用封装
 * 
 * 提供分析相关的 API 接口调用方法，包括：
 * - 创建分析任务
 * - 获取分析列表
 * - 获取分析详情
 * - 获取分析进度
 * - 获取分析报告
 * - 删除分析记录
 */

import request from '@/utils/request';
import {
  Analysis,
  AnalysisCreate,
  AnalysisProgress,
  Report,
  AnalysisListResponse,
} from '@/types';

export const analysisApi = {
  /**
   * 创建新的分析任务
   * 
   * @param data - 分析创建参数
   * @param data.company_name - 公司名称（必填）
   * @param data.stock_code - 股票代码（可选）
   * @param data.include_charts - 是否包含图表，默认 true
   * @param data.api_config_id - 用户自定义的 API 配置ID（可选）
   * @returns 创建的分析记录
   */
  createAnalysis: async (data: AnalysisCreate): Promise<Analysis> => {
    return request({
      url: '/analyses',
      method: 'POST',
      data,
    });
  },

  /**
   * 获取分析记录列表
   * 
   * @param skip - 分页偏移量，默认 0
   * @param limit - 每页数量限制，默认 20
   * @returns 分析记录列表及总数
   */
  listAnalyses: async (skip: number = 0, limit: number = 20): Promise<AnalysisListResponse> => {
    return request({
      url: '/analyses',
      method: 'GET',
      params: { skip, limit },
    });
  },

  /**
   * 获取单个分析记录详情
   * 
   * @param analysisId - 分析记录ID
   * @returns 分析记录详情
   */
  getAnalysis: async (analysisId: string): Promise<Analysis> => {
    return request({
      url: `/analyses/${analysisId}`,
      method: 'GET',
    });
  },

  /**
   * 获取分析任务的进度状态
   * 
   * @param analysisId - 分析记录ID
   * @returns 进度信息，包含状态、百分比、消息
   */
  getProgress: async (analysisId: string): Promise<AnalysisProgress> => {
    return request({
      url: `/analyses/${analysisId}/progress`,
      method: 'GET',
    });
  },

  /**
   * 获取分析报告内容
   * 
   * @param analysisId - 分析记录ID
   * @returns 报告内容，包含 Markdown 和 HTML 格式
   */
  getReport: async (analysisId: string): Promise<Report> => {
    return request({
      url: `/analyses/${analysisId}/report`,
      method: 'GET',
    });
  },

  /**
   * 删除分析记录
   * 
   * @param analysisId - 分析记录ID
   */
  deleteAnalysis: async (analysisId: string): Promise<void> => {
    return request({
      url: `/analyses/${analysisId}`,
      method: 'DELETE',
    });
  },
};
