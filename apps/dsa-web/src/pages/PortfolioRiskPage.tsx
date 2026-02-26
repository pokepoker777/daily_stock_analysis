import type React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import { portfolioApi } from '../api/portfolio';
import type { StockRiskMetrics, CorrelationAlert } from '../api/portfolio';

const PortfolioRiskPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [codesInput, setCodesInput] = useState('');
  const [lookback, setLookback] = useState(60);
  const [isLoading, setIsLoading] = useState(false);
  const [apiOffline, setApiOffline] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stockMetrics, setStockMetrics] = useState<StockRiskMetrics[]>([]);
  const [diversificationRatio, setDiversificationRatio] = useState<number | null>(null);
  const [alerts, setAlerts] = useState<CorrelationAlert[]>([]);
  const [summaryText, setSummaryText] = useState('');

  const fetchRisk = useCallback(async (codes?: string) => {
    setIsLoading(true);
    setError(null);
    setApiOffline(false);
    try {
      const res = await portfolioApi.getRisk(codes || undefined, lookback);
      if (res.success && res.data) {
        setStockMetrics(res.data.stock_metrics || []);
        setDiversificationRatio(res.data.diversification_ratio ?? null);
        setAlerts(res.data.alerts || []);
        setSummaryText(res.summary || '');
      } else {
        setError('未获取到风险数据');
      }
    } catch (err) {
      const msg = (err as Error).message;
      if (msg === 'Network Error' || msg.includes('ERR_CONNECTION')) {
        setApiOffline(true);
      } else {
        setError(msg);
      }
    } finally {
      setIsLoading(false);
    }
  }, [lookback]);

  useEffect(() => {
    fetchRisk();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAnalyze = () => {
    const codes = codesInput.trim() || undefined;
    fetchRisk(codes);
  };

  const fmtPct = (v: number) => `${(v * 100).toFixed(2)}%`;

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('portfolio.title')}</h1>
      </header>

      {/* Input bar */}
      <div className="portfolio-input-bar">
        <div className="portfolio-input-row">
          <input
            type="text"
            value={codesInput}
            onChange={(e) => setCodesInput(e.target.value)}
            placeholder="输入股票代码，逗号分隔 (如 600519,000001,300750)，留空使用默认持仓"
            className="portfolio-input"
          />
          <select
            value={lookback}
            onChange={(e) => setLookback(Number(e.target.value))}
            className="portfolio-select"
            title="回看窗口天数"
          >
            <option value={30}>30日</option>
            <option value={60}>60日</option>
            <option value={120}>120日</option>
            <option value={250}>250日</option>
          </select>
          <button onClick={handleAnalyze} disabled={isLoading} className="analysis-submit-btn">
            {isLoading ? '分析中...' : '风险分析'}
          </button>
        </div>
      </div>

      {/* Offline banner */}
      {apiOffline && (
        <div className="bt-offline-banner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 5.636a9 9 0 11-12.728 0M12 9v4m0 4h.01" />
          </svg>
          <span>后端服务未连接 — 请先启动 API 服务 (<code>python server.py</code>)，然后刷新页面</span>
        </div>
      )}

      {error && <p className="input-error-msg">{error}</p>}

      {/* Loading */}
      {isLoading && (
        <div className="page-loading"><div className="spinner" /><p>正在计算风险指标...</p></div>
      )}

      {/* Results */}
      {!isLoading && !apiOffline && stockMetrics.length > 0 && (
        <>
          {/* Summary metrics row */}
          <div className="metric-grid">
            <div className="metric-card">
              <div className="metric-card-dot color-orange" />
              <span className="metric-card-label">持仓数量</span>
              <span className="metric-card-value">{stockMetrics.length}</span>
            </div>
            <div className="metric-card">
              <div className="metric-card-dot color-green" />
              <span className="metric-card-label">分散化比率</span>
              <span className="metric-card-value">{diversificationRatio != null ? diversificationRatio.toFixed(2) : '—'}</span>
            </div>
            <div className="metric-card">
              <div className="metric-card-dot color-pink" />
              <span className="metric-card-label">风险预警</span>
              <span className="metric-card-value">{alerts.length}</span>
            </div>
            <div className="metric-card">
              <div className="metric-card-dot color-blue" />
              <span className="metric-card-label">回看窗口</span>
              <span className="metric-card-value">{lookback}日</span>
            </div>
          </div>

          {/* Stock risk table */}
          <section className="portfolio-section">
            <h2 className="market-section-title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z"/>
              </svg>
              个股风险指标
            </h2>
            <div className="portfolio-table-wrap">
              <table className="bt-results-table">
                <thead>
                  <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>夏普比率</th>
                    <th>VaR(95%)</th>
                    <th>最大回撤</th>
                    <th>Kelly比例</th>
                    <th>年化收益</th>
                    <th>年化波动</th>
                  </tr>
                </thead>
                <tbody>
                  {stockMetrics.map((s) => (
                    <tr key={s.code}>
                      <td className="bt-code-cell">{s.code}</td>
                      <td>{s.name || '—'}</td>
                      <td className={s.sharpe_ratio >= 1 ? 'bt-score-good' : s.sharpe_ratio >= 0 ? 'bt-score-neutral' : 'bt-score-bad'}>
                        {s.sharpe_ratio.toFixed(2)}
                      </td>
                      <td>{fmtPct(s.var_95)}</td>
                      <td className="bt-score-bad">{fmtPct(s.max_drawdown)}</td>
                      <td>{fmtPct(s.kelly_fraction)}</td>
                      <td className={s.annualized_return >= 0 ? 'bt-score-good' : 'bt-score-bad'}>
                        {fmtPct(s.annualized_return)}
                      </td>
                      <td>{fmtPct(s.annualized_volatility)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Alerts */}
          {alerts.length > 0 && (
            <section className="portfolio-section">
              <h2 className="market-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                高相关性预警
              </h2>
              <div className="portfolio-alerts">
                {alerts.map((a, i) => (
                  <div key={i} className="portfolio-alert-card">
                    <span className="portfolio-alert-pair">{a.pair[0]} ↔ {a.pair[1]}</span>
                    <span className="portfolio-alert-corr">相关系数: {a.correlation.toFixed(3)}</span>
                    <span className="portfolio-alert-msg">{a.message}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Summary text */}
          {summaryText && (
            <section className="portfolio-section">
              <h2 className="market-section-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                风险摘要
              </h2>
              <div className="portfolio-summary">
                <pre>{summaryText}</pre>
              </div>
            </section>
          )}
        </>
      )}

      {/* Empty state */}
      {!isLoading && !apiOffline && !error && stockMetrics.length === 0 && (
        <div className="page-empty">
          <div className="page-empty-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/>
            </svg>
          </div>
          <h3>输入股票代码开始风险分析</h3>
          <p>支持多只股票组合分析，计算夏普比率、VaR、最大回撤等风险指标</p>
        </div>
      )}
    </div>
  );
};

export default PortfolioRiskPage;
