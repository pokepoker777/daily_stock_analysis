import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import { validateStockCode } from '../utils/validation';
import apiClient from '../api/index';

interface StockSnapshot {
  stockCode: string;
  stockName: string | null;
  currentPrice: number;
  change: number | null;
  changePercent: number | null;
  high: number | null;
  low: number | null;
  open: number | null;
  prevClose: number | null;
  volume: number | null;
  amount: number | null;
}

const ComparePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [codeA, setCodeA] = useState('');
  const [codeB, setCodeB] = useState('');
  const [inputError, setInputError] = useState<string>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snapshots, setSnapshots] = useState<StockSnapshot[]>([]);

  const fetchQuote = async (code: string): Promise<StockSnapshot | null> => {
    try {
      const resp = await apiClient.get<{
        stock_code: string; stock_name: string | null;
        current_price: number; change: number | null; change_percent: number | null;
        high: number | null; low: number | null; open: number | null;
        prev_close: number | null; volume: number | null; amount: number | null;
      }>(`/api/v1/stocks/${code}/quote`);
      const d = resp.data;
      return {
        stockCode: d.stock_code, stockName: d.stock_name,
        currentPrice: d.current_price, change: d.change, changePercent: d.change_percent,
        high: d.high, low: d.low, open: d.open, prevClose: d.prev_close,
        volume: d.volume, amount: d.amount,
      };
    } catch {
      return null;
    }
  };

  const handleCompare = async () => {
    const vA = validateStockCode(codeA);
    const vB = validateStockCode(codeB);
    if (!vA.valid) { setInputError(`股票A: ${vA.message}`); return; }
    if (!vB.valid) { setInputError(`股票B: ${vB.message}`); return; }
    setInputError(undefined);
    setError(null);
    setIsLoading(true);
    try {
      const [a, b] = await Promise.all([fetchQuote(vA.normalized), fetchQuote(vB.normalized)]);
      if (!a && !b) {
        setError('未获取到任何行情数据，请检查后端服务或股票代码');
        setSnapshots([]);
      } else {
        const list: StockSnapshot[] = [];
        if (a) list.push(a);
        if (b) list.push(b);
        setSnapshots(list);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '对比失败';
      const isNetwork = msg === 'Network Error' || msg.includes('ERR_CONNECTION');
      setError(isNetwork ? '后端服务未连接 — 请先启动 API 服务 (python server.py)' : msg);
    } finally {
      setIsLoading(false);
    }
  };

  const fmtNum = (v: number | null, suffix = '') => v !== null ? `${v.toFixed(2)}${suffix}` : '--';
  const fmtVol = (v: number | null) => v !== null ? `${(v / 10000).toFixed(0)}万` : '--';
  const fmtAmt = (v: number | null) => v !== null ? `${(v / 100000000).toFixed(2)}亿` : '--';

  const rows: { label: string; getter: (s: StockSnapshot) => string; highlight?: boolean }[] = [
    { label: '现价', getter: (s) => `¥${s.currentPrice.toFixed(2)}` },
    { label: '涨跌幅', getter: (s) => fmtNum(s.changePercent, '%'), highlight: true },
    { label: '涨跌额', getter: (s) => fmtNum(s.change) },
    { label: '今开', getter: (s) => fmtNum(s.open) },
    { label: '最高', getter: (s) => fmtNum(s.high) },
    { label: '最低', getter: (s) => fmtNum(s.low) },
    { label: '昨收', getter: (s) => fmtNum(s.prevClose) },
    { label: '成交量', getter: (s) => fmtVol(s.volume) },
    { label: '成交额', getter: (s) => fmtAmt(s.amount) },
  ];

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('home.toolCompare')}</h1>
      </header>

      {/* Dual input */}
      <div className="analysis-input-bar">
        <div className="compare-input-row">
          <input
            type="text" value={codeA}
            onChange={(e) => { setCodeA(e.target.value.toUpperCase()); setInputError(undefined); }}
            onKeyDown={(e) => e.key === 'Enter' && codeA && codeB && handleCompare()}
            placeholder="股票A，如 600519"
            disabled={isLoading}
            className="analysis-input"
          />
          <span className="compare-vs">VS</span>
          <input
            type="text" value={codeB}
            onChange={(e) => { setCodeB(e.target.value.toUpperCase()); setInputError(undefined); }}
            onKeyDown={(e) => e.key === 'Enter' && codeA && codeB && handleCompare()}
            placeholder="股票B，如 000858"
            disabled={isLoading}
            className="analysis-input"
          />
          <button onClick={handleCompare} disabled={!codeA || !codeB || isLoading} className="analysis-submit-btn">
            {isLoading ? t('common.loading') : '对比'}
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

      {isLoading && (
        <div className="page-loading"><div className="spinner" /><p>获取行情数据中...</p></div>
      )}

      {snapshots.length >= 2 && !isLoading && (
        <div className="tool-page-card">
          <h3 className="tool-page-card-title">对比结果</h3>
          <div className="tool-page-table-wrap">
            <table className="tool-page-table compare-table">
              <thead>
                <tr>
                  <th>指标</th>
                  <th>{snapshots[0].stockName ?? snapshots[0].stockCode}</th>
                  <th>{snapshots[1].stockName ?? snapshots[1].stockCode}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.label}>
                    <td className="compare-label">{row.label}</td>
                    <td className={row.highlight ? ((snapshots[0].changePercent ?? 0) >= 0 ? 'text-green' : 'text-red') : ''}>
                      {row.getter(snapshots[0])}
                    </td>
                    <td className={row.highlight ? ((snapshots[1].changePercent ?? 0) >= 0 ? 'text-green' : 'text-red') : ''}>
                      {row.getter(snapshots[1])}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="compare-actions">
            <button className="tool-page-action-btn" onClick={() => navigate(`/analysis?code=${snapshots[0].stockCode}`)}>
              分析 {snapshots[0].stockName ?? snapshots[0].stockCode}
            </button>
            <button className="tool-page-action-btn" onClick={() => navigate(`/analysis?code=${snapshots[1].stockCode}`)}>
              分析 {snapshots[1].stockName ?? snapshots[1].stockCode}
            </button>
          </div>
        </div>
      )}

      {snapshots.length === 1 && !isLoading && (
        <div className="offline-banner">
          <span>仅获取到 {snapshots[0].stockName ?? snapshots[0].stockCode} 的数据，另一只股票未找到</span>
        </div>
      )}

      {!isLoading && snapshots.length === 0 && !error && (
        <div className="page-empty">
          <div className="page-empty-icon">
            <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
            </svg>
          </div>
          <h3>个股横向对比</h3>
          <p>输入两只股票代码，实时对比行情数据</p>
        </div>
      )}
    </div>
  );
};

export default ComparePage;
