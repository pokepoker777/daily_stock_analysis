import apiClient from './index';

export interface StockRiskMetrics {
  code: string;
  name?: string;
  sharpe_ratio: number;
  var_95: number;
  max_drawdown: number;
  kelly_fraction: number;
  annualized_return: number;
  annualized_volatility: number;
}

export interface CorrelationAlert {
  pair: [string, string];
  correlation: number;
  message: string;
}

export interface PortfolioRiskData {
  stock_metrics: StockRiskMetrics[];
  correlation_matrix?: Record<string, Record<string, number>>;
  diversification_ratio?: number;
  alerts?: CorrelationAlert[];
}

export interface PortfolioRiskResponse {
  success: boolean;
  data: PortfolioRiskData;
  summary: string;
}

export const portfolioApi = {
  async getRisk(codes?: string, lookback = 60): Promise<PortfolioRiskResponse> {
    const params: Record<string, string | number> = { lookback };
    if (codes) params.codes = codes;
    const response = await apiClient.get('/portfolio/risk', { params });
    return response.data;
  },

  async getRiskSummary(codes?: string, lookback = 60): Promise<{ success: boolean; summary: string }> {
    const params: Record<string, string | number> = { lookback };
    if (codes) params.codes = codes;
    const response = await apiClient.get('/portfolio/risk/summary', { params });
    return response.data;
  },
};
