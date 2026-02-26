import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import { validateStockCode } from '../utils/validation';
import apiClient from '../api/index';

interface KLineData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  changePercent: number | null;
}

interface HistoryResponse {
  stock_code: string;
  stock_name: string | null;
  period: string;
  data: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    amount: number;
    change_percent: number | null;
  }>;
}

function calcSMA(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) { result.push(null); continue; }
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += data[j];
    result.push(+(sum / period).toFixed(2));
  }
  return result;
}

function calcRSI(closes: number[], period = 14): (number | null)[] {
  const result: (number | null)[] = [null];
  const gains: number[] = [];
  const losses: number[] = [];
  for (let i = 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    gains.push(diff > 0 ? diff : 0);
    losses.push(diff < 0 ? -diff : 0);
    if (i < period) { result.push(null); continue; }
    const avgGain = gains.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
    const avgLoss = losses.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
    const rsi = avgLoss === 0 ? 100 : +(100 - 100 / (1 + avgGain / avgLoss)).toFixed(2);
    result.push(rsi);
  }
  return result;
}

const TechnicalsPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stockCode, setStockCode] = useState('');
  const [inputError, setInputError] = useState<string>();
  const [period, setPeriod] = useState<'daily' | 'weekly'>('daily');
  const [days, setDays] = useState(60);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [stockName, setStockName] = useState<string | null>(null);

  const handleFetch = async (codeOverride?: string) => {
    const code = codeOverride || stockCode;
    const { valid, message, normalized } = validateStockCode(code);
    if (!valid) { setInputError(message); return; }
    setInputError(undefined);
    setError(null);
    setIsLoading(true);
    try {
      const resp = await apiClient.get<HistoryResponse>(`/api/v1/stocks/${normalized}/history`, {
        params: { period, days },
      });
      const d = resp.data;
      setStockName(d.stock_name);
      setKlineData(
        d.data.map((item) => ({
          date: item.date,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
          volume: item.volume,
          amount: item.amount,
          changePercent: item.change_percent,
        })),
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '获取数据失败';
      const isNetwork = msg === 'Network Error' || msg.includes('ERR_CONNECTION');
      setError(isNetwork ? '后端服务未连接 — 请先启动 API 服务 (python server.py)' : msg);
    } finally {
      setIsLoading(false);
    }
  };

  const closes = klineData.map((d) => d.close);
  const sma5 = calcSMA(closes, 5);
  const sma10 = calcSMA(closes, 10);
  const sma20 = calcSMA(closes, 20);
  const rsi14 = calcRSI(closes, 14);
  const latestIdx = klineData.length - 1;
  const latestClose = closes[latestIdx];
  const latestChange = klineData[latestIdx]?.changePercent;
  const latestRSI = rsi14[latestIdx];

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('home.toolTechnicals')}</h1>
      </header>

      {/* Input bar */}
      <div className="analysis-input-bar">
        <div className="analysis-input-wrapper">
          <input
            type="text"
            value={stockCode}
            onChange={(e) => { setStockCode(e.target.value.toUpperCase()); setInputError(undefined); }}
            onKeyDown={(e) => e.key === 'Enter' && stockCode && handleFetch()}
            placeholder={t('app.inputPlaceholder')}
            disabled={isLoading}
            className="analysis-input"
          />
          <div className="tool-page-controls">
            <select
              className="tool-page-select"
              value={period}
              onChange={(e) => setPeriod(e.target.value as 'daily' | 'weekly')}
              title="K线周期"
            >
              <option value="daily">日K</option>
              <option value="weekly">周K</option>
            </select>
            <select
              className="tool-page-select"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              title="数据天数"
            >
              <option value={30}>30天</option>
              <option value={60}>60天</option>
              <option value={120}>120天</option>
              <option value={250}>250天</option>
            </select>
          </div>
          <button onClick={() => handleFetch()} disabled={!stockCode || isLoading} className="analysis-submit-btn">
            {isLoading ? t('common.loading') : '获取数据'}
          </button>
        </div>
        {inputError && <p className="input-error-msg">{inputError}</p>}
      </div>

      {error && (
        <div className="offline-banner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636a9 9 0 11-12.728 0M12 9v4m0 4h.01" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {klineData.length > 0 && (
        <>
          {/* Summary card */}
          <div className="tool-page-summary">
            <div className="tool-page-summary-title">
              {stockName ?? stockCode}
              <span className={`tool-page-tag ${(latestChange ?? 0) >= 0 ? 'tag-green' : 'tag-red'}`}>
                {(latestChange ?? 0) >= 0 ? '+' : ''}{latestChange?.toFixed(2) ?? '--'}%
              </span>
            </div>
            <div className="tool-page-summary-price">¥{latestClose?.toFixed(2)}</div>
          </div>

          {/* Indicators grid */}
          <div className="tool-page-grid">
            {/* Moving Averages */}
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4" />
                </svg>
                均线系统 (SMA)
              </h3>
              <div className="tool-page-indicators">
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">MA5</span>
                  <span className="tool-page-indicator-value">{sma5[latestIdx]?.toFixed(2) ?? '--'}</span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">MA10</span>
                  <span className="tool-page-indicator-value">{sma10[latestIdx]?.toFixed(2) ?? '--'}</span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">MA20</span>
                  <span className="tool-page-indicator-value">{sma20[latestIdx]?.toFixed(2) ?? '--'}</span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">趋势</span>
                  <span className={`tool-page-indicator-value ${(sma5[latestIdx] ?? 0) > (sma20[latestIdx] ?? 0) ? 'text-green' : 'text-red'}`}>
                    {(sma5[latestIdx] ?? 0) > (sma20[latestIdx] ?? 0) ? '多头排列 ↑' : '空头排列 ↓'}
                  </span>
                </div>
              </div>
            </div>

            {/* RSI */}
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z" />
                </svg>
                RSI(14)
              </h3>
              <div className="tool-page-indicators">
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">当前RSI</span>
                  <span className={`tool-page-indicator-value ${(latestRSI ?? 50) > 70 ? 'text-red' : (latestRSI ?? 50) < 30 ? 'text-green' : ''}`}>
                    {latestRSI?.toFixed(2) ?? '--'}
                  </span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">状态</span>
                  <span className="tool-page-indicator-value">
                    {(latestRSI ?? 50) > 70 ? '超买区间' : (latestRSI ?? 50) < 30 ? '超卖区间' : '中性区间'}
                  </span>
                </div>
              </div>
            </div>

            {/* Price Range */}
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
                区间统计
              </h3>
              <div className="tool-page-indicators">
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">最高价</span>
                  <span className="tool-page-indicator-value text-red">¥{Math.max(...klineData.map(d => d.high)).toFixed(2)}</span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">最低价</span>
                  <span className="tool-page-indicator-value text-green">¥{Math.min(...klineData.map(d => d.low)).toFixed(2)}</span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">平均成交量</span>
                  <span className="tool-page-indicator-value">
                    {(klineData.reduce((s, d) => s + d.volume, 0) / klineData.length / 10000).toFixed(0)}万手
                  </span>
                </div>
                <div className="tool-page-indicator">
                  <span className="tool-page-indicator-label">数据天数</span>
                  <span className="tool-page-indicator-value">{klineData.length}天</span>
                </div>
              </div>
            </div>

            {/* Volatility */}
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                波动率
              </h3>
              <div className="tool-page-indicators">
                {(() => {
                  const changes = klineData
                    .map((d) => d.changePercent)
                    .filter((v): v is number => v !== null);
                  const avg = changes.length ? changes.reduce((a, b) => a + b, 0) / changes.length : 0;
                  const variance = changes.length
                    ? changes.reduce((s, v) => s + (v - avg) ** 2, 0) / changes.length
                    : 0;
                  const std = Math.sqrt(variance);
                  return (
                    <>
                      <div className="tool-page-indicator">
                        <span className="tool-page-indicator-label">日均涨跌</span>
                        <span className={`tool-page-indicator-value ${avg >= 0 ? 'text-green' : 'text-red'}`}>
                          {avg >= 0 ? '+' : ''}{avg.toFixed(3)}%
                        </span>
                      </div>
                      <div className="tool-page-indicator">
                        <span className="tool-page-indicator-label">波动标准差</span>
                        <span className="tool-page-indicator-value">{std.toFixed(3)}%</span>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          </div>

          {/* Recent K-line table */}
          <div className="tool-page-card">
            <h3 className="tool-page-card-title">近期行情数据（最近10个交易日）</h3>
            <div className="tool-page-table-wrap">
              <table className="tool-page-table">
                <thead>
                  <tr>
                    <th>日期</th><th>开盘</th><th>最高</th><th>最低</th><th>收盘</th><th>涨跌幅</th><th>成交量</th>
                  </tr>
                </thead>
                <tbody>
                  {klineData.slice(-10).reverse().map((row) => (
                    <tr key={row.date}>
                      <td>{row.date}</td>
                      <td>{row.open.toFixed(2)}</td>
                      <td>{row.high.toFixed(2)}</td>
                      <td>{row.low.toFixed(2)}</td>
                      <td>{row.close.toFixed(2)}</td>
                      <td className={(row.changePercent ?? 0) >= 0 ? 'text-green' : 'text-red'}>
                        {row.changePercent !== null ? `${row.changePercent >= 0 ? '+' : ''}${row.changePercent.toFixed(2)}%` : '--'}
                      </td>
                      <td>{(row.volume / 10000).toFixed(0)}万</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!isLoading && klineData.length === 0 && !error && (
        <div className="page-empty">
          <div className="page-empty-icon">
            <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          </div>
          <h3>输入股票代码，查看技术面分析</h3>
          <p>支持 K线趋势、均线系统、RSI 指标等技术分析</p>
        </div>
      )}
    </div>
  );
};

export default TechnicalsPage;
