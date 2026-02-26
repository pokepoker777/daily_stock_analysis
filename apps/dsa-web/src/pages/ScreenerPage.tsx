import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import apiClient from '../api/index';

interface QuoteResult {
  stockCode: string;
  stockName: string | null;
  currentPrice: number;
  change: number | null;
  changePercent: number | null;
  volume: number | null;
  amount: number | null;
  high: number | null;
  low: number | null;
}

const PRESET_STOCKS = [
  '600519', '300750', '002594', '000858', '601318',
  '600036', '000333', '002415', '601012', '600900',
  '603259', '002475', '600276', '601899', '000001',
];

const ScreenerPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<QuoteResult[]>([]);
  const [sortKey, setSortKey] = useState<'changePercent' | 'volume' | 'amount'>('changePercent');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [customCodes, setCustomCodes] = useState('');

  const handleScreen = async () => {
    setError(null);
    setIsLoading(true);
    const codes = customCodes.trim()
      ? customCodes.split(/[,，\s]+/).map(c => c.trim()).filter(Boolean)
      : PRESET_STOCKS;

    const fetched: QuoteResult[] = [];
    try {
      const promises = codes.map(async (code) => {
        try {
          const resp = await apiClient.get<{
            stock_code: string;
            stock_name: string | null;
            current_price: number;
            change: number | null;
            change_percent: number | null;
            volume: number | null;
            amount: number | null;
            high: number | null;
            low: number | null;
          }>(`/api/v1/stocks/${code}/quote`);
          const d = resp.data;
          return {
            stockCode: d.stock_code,
            stockName: d.stock_name,
            currentPrice: d.current_price,
            change: d.change,
            changePercent: d.change_percent,
            volume: d.volume,
            amount: d.amount,
            high: d.high,
            low: d.low,
          } as QuoteResult;
        } catch {
          return null;
        }
      });

      const all = await Promise.all(promises);
      for (const item of all) {
        if (item) fetched.push(item);
      }

      if (fetched.length === 0) {
        setError('未获取到任何有效行情数据，请检查后端服务或股票代码');
      }
      setResults(fetched);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '筛选失败';
      const isNetwork = msg === 'Network Error' || msg.includes('ERR_CONNECTION');
      setError(isNetwork ? '后端服务未连接 — 请先启动 API 服务 (python server.py)' : msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSort = (key: typeof sortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const sorted = [...results].sort((a, b) => {
    const va = a[sortKey] ?? 0;
    const vb = b[sortKey] ?? 0;
    return sortDir === 'desc' ? vb - va : va - vb;
  });

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('home.toolScreener')}</h1>
      </header>

      {/* Input area */}
      <div className="analysis-input-bar">
        <div className="analysis-input-wrapper">
          <input
            type="text"
            value={customCodes}
            onChange={(e) => setCustomCodes(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleScreen()}
            placeholder="输入股票代码（逗号分隔），留空使用预置热门股"
            disabled={isLoading}
            className="analysis-input"
          />
          <button onClick={handleScreen} disabled={isLoading} className="analysis-submit-btn">
            {isLoading ? t('common.loading') : '开始筛选'}
          </button>
        </div>
        <p className="tool-page-hint">
          预置热门股：{PRESET_STOCKS.slice(0, 8).join('、')}… 共 {PRESET_STOCKS.length} 只
        </p>
      </div>

      {error && (
        <div className="offline-banner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636a9 9 0 11-12.728 0M12 9v4m0 4h.01" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {isLoading && (
        <div className="page-loading">
          <div className="spinner" />
          <p>正在获取行情数据...</p>
        </div>
      )}

      {sorted.length > 0 && !isLoading && (
        <div className="tool-page-card">
          <h3 className="tool-page-card-title">
            筛选结果（{sorted.length} 只）
          </h3>
          <div className="tool-page-table-wrap">
            <table className="tool-page-table">
              <thead>
                <tr>
                  <th>代码</th>
                  <th>名称</th>
                  <th>现价</th>
                  <th className="tool-page-th-sortable" onClick={() => handleSort('changePercent')}>
                    涨跌幅 {sortKey === 'changePercent' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
                  </th>
                  <th>最高</th>
                  <th>最低</th>
                  <th className="tool-page-th-sortable" onClick={() => handleSort('volume')}>
                    成交量 {sortKey === 'volume' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
                  </th>
                  <th className="tool-page-th-sortable" onClick={() => handleSort('amount')}>
                    成交额 {sortKey === 'amount' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
                  </th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((row) => (
                  <tr key={row.stockCode}>
                    <td className="font-mono">{row.stockCode}</td>
                    <td>{row.stockName ?? '--'}</td>
                    <td>¥{row.currentPrice.toFixed(2)}</td>
                    <td className={(row.changePercent ?? 0) >= 0 ? 'text-green' : 'text-red'}>
                      {row.changePercent !== null ? `${row.changePercent >= 0 ? '+' : ''}${row.changePercent.toFixed(2)}%` : '--'}
                    </td>
                    <td>{row.high?.toFixed(2) ?? '--'}</td>
                    <td>{row.low?.toFixed(2) ?? '--'}</td>
                    <td>{row.volume ? `${(row.volume / 10000).toFixed(0)}万` : '--'}</td>
                    <td>{row.amount ? `${(row.amount / 100000000).toFixed(2)}亿` : '--'}</td>
                    <td>
                      <button
                        className="tool-page-action-btn"
                        onClick={() => navigate(`/analysis?code=${row.stockCode}`)}
                        title="分析"
                      >
                        分析
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!isLoading && results.length === 0 && !error && (
        <div className="page-empty">
          <div className="page-empty-icon">
            <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
          </div>
          <h3>智能条件选股</h3>
          <p>输入股票代码或使用预置热门股列表，一键获取实时行情对比</p>
        </div>
      )}
    </div>
  );
};

export default ScreenerPage;
