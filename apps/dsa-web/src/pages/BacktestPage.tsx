import type React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { backtestApi } from '../api/backtest';
import { useTranslation } from '../hooks/useTranslation';
import { Badge, Pagination } from '../components/common';
import type {
  BacktestResultItem,
  BacktestRunResponse,
  PerformanceMetrics,
} from '../types/backtest';

// ============ Helpers ============

function pct(value?: number | null): string {
  if (value == null) return '--';
  return `${value.toFixed(1)}%`;
}

function outcomeBadge(outcome?: string) {
  if (!outcome) return <Badge variant="default">--</Badge>;
  switch (outcome) {
    case 'win':
      return <Badge variant="success" glow>WIN</Badge>;
    case 'loss':
      return <Badge variant="danger" glow>LOSS</Badge>;
    case 'neutral':
      return <Badge variant="warning">NEUTRAL</Badge>;
    default:
      return <Badge variant="default">{outcome}</Badge>;
  }
}

function statusBadge(status: string) {
  switch (status) {
    case 'completed':
      return <Badge variant="success">completed</Badge>;
    case 'insufficient':
      return <Badge variant="warning">insufficient</Badge>;
    case 'error':
      return <Badge variant="danger">error</Badge>;
    default:
      return <Badge variant="default">{status}</Badge>;
  }
}

function boolIcon(value?: boolean | null) {
  if (value === true) return <span className="bt-icon-yes">&#10003;</span>;
  if (value === false) return <span className="bt-icon-no">&#10007;</span>;
  return <span className="bt-icon-na">--</span>;
}

// ============ Metric Row ============

const MetricRow: React.FC<{ label: string; value: string; accent?: boolean }> = ({ label, value, accent }) => (
  <div className="bt-metric-row">
    <span className="bt-metric-label">{label}</span>
    <span className={`bt-metric-value ${accent ? 'accent' : ''}`}>{value}</span>
  </div>
);

// ============ Performance Card ============

const PerformanceCard: React.FC<{ metrics: PerformanceMetrics; title: string }> = ({ metrics, title }) => (
  <div className="bt-perf-card">
    <div className="bt-perf-card-title">{title}</div>
    <MetricRow label="Direction Accuracy" value={pct(metrics.directionAccuracyPct)} accent />
    <MetricRow label="Win Rate" value={pct(metrics.winRatePct)} accent />
    <MetricRow label="Avg Sim. Return" value={pct(metrics.avgSimulatedReturnPct)} />
    <MetricRow label="Avg Stock Return" value={pct(metrics.avgStockReturnPct)} />
    <MetricRow label="SL Trigger Rate" value={pct(metrics.stopLossTriggerRate)} />
    <MetricRow label="TP Trigger Rate" value={pct(metrics.takeProfitTriggerRate)} />
    <MetricRow label="Avg Days to Hit" value={metrics.avgDaysToFirstHit != null ? metrics.avgDaysToFirstHit.toFixed(1) : '--'} />
    <div className="bt-perf-footer">
      <span className="bt-metric-label">Evaluations</span>
      <span className="bt-metric-value">
        {Number(metrics.completedCount)} / {Number(metrics.totalEvaluations)}
      </span>
    </div>
    <div className="bt-metric-row bt-metric-row-last">
      <span className="bt-metric-label">W / L / N</span>
      <span className="bt-metric-value">
        <span className="bt-icon-yes">{metrics.winCount}</span>
        {' / '}
        <span className="bt-icon-no">{metrics.lossCount}</span>
        {' / '}
        <span className="bt-text-orange">{metrics.neutralCount}</span>
      </span>
    </div>
  </div>
);

// ============ Run Summary ============

const RunSummary: React.FC<{ data: BacktestRunResponse }> = ({ data }) => (
  <div className="bt-run-summary">
    <span>Processed: <strong>{data.processed}</strong></span>
    <span>Saved: <strong className="bt-text-primary">{data.saved}</strong></span>
    <span>Completed: <strong className="bt-icon-yes">{data.completed}</strong></span>
    <span>Insufficient: <strong className="bt-text-orange">{data.insufficient}</strong></span>
    {data.errors > 0 && (
      <span>Errors: <strong className="bt-icon-no">{data.errors}</strong></span>
    )}
  </div>
);

// ============ Main Page ============

const BacktestPage: React.FC = () => {
  // Input state
  const [codeFilter, setCodeFilter] = useState('');
  const [evalDays, setEvalDays] = useState('');
  const [forceRerun, setForceRerun] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<BacktestRunResponse | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  // API status
  const [apiOffline, setApiOffline] = useState(false);

  // Results state
  const [results, setResults] = useState<BacktestResultItem[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const pageSize = 20;

  // Performance state
  const [overallPerf, setOverallPerf] = useState<PerformanceMetrics | null>(null);
  const [stockPerf, setStockPerf] = useState<PerformanceMetrics | null>(null);
  const [isLoadingPerf, setIsLoadingPerf] = useState(false);

  // Fetch results
  const fetchResults = useCallback(async (page = 1, code?: string, windowDays?: number) => {
    setIsLoadingResults(true);
    try {
      const response = await backtestApi.getResults({ code: code || undefined, evalWindowDays: windowDays, page, limit: pageSize });
      setResults(response.items);
      setTotalResults(response.total);
      setCurrentPage(response.page);
    } catch (err) {
      console.warn('[Backtest] Failed to fetch results:', (err as Error).message);
    } finally {
      setIsLoadingResults(false);
    }
  }, []);

  // Fetch performance
  const fetchPerformance = useCallback(async (code?: string, windowDays?: number) => {
    setIsLoadingPerf(true);
    try {
      const overall = await backtestApi.getOverallPerformance(windowDays);
      setOverallPerf(overall);

      if (code) {
        const stock = await backtestApi.getStockPerformance(code, windowDays);
        setStockPerf(stock);
      } else {
        setStockPerf(null);
      }
    } catch (err) {
      console.warn('[Backtest] Failed to fetch performance:', (err as Error).message);
    } finally {
      setIsLoadingPerf(false);
    }
  }, []);

  // Initial load — fetch performance first, then filter results by its window
  useEffect(() => {
    const init = async () => {
      try {
        // Get latest performance (unfiltered returns most recent summary)
        const overall = await backtestApi.getOverallPerformance();
        setOverallPerf(overall);
        // Use the summary's eval_window_days to filter results consistently
        const windowDays = overall?.evalWindowDays;
        if (windowDays && !evalDays) {
          setEvalDays(String(windowDays));
        }
        fetchResults(1, undefined, windowDays);
      } catch {
        setApiOffline(true);
      }
    };
    init();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Run backtest
  const handleRun = async () => {
    setIsRunning(true);
    setRunResult(null);
    setRunError(null);
    try {
      const code = codeFilter.trim() || undefined;
      const evalWindowDays = evalDays ? parseInt(evalDays, 10) : undefined;
      const response = await backtestApi.run({
        code,
        force: forceRerun || undefined,
        minAgeDays: forceRerun ? 0 : undefined,
        evalWindowDays,
      });
      setRunResult(response);
      // Refresh data with same eval_window_days
      fetchResults(1, codeFilter.trim() || undefined, evalWindowDays);
      fetchPerformance(codeFilter.trim() || undefined, evalWindowDays);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Backtest failed';
      const isNetwork = msg === 'Network Error' || msg.includes('ERR_CONNECTION');
      setRunError(isNetwork ? '后端服务未启动，请先启动 API 服务' : msg);
    } finally {
      setIsRunning(false);
    }
  };

  // Filter by code
  const handleFilter = () => {
    const code = codeFilter.trim() || undefined;
    const windowDays = evalDays ? parseInt(evalDays, 10) : undefined;
    setCurrentPage(1);
    fetchResults(1, code, windowDays);
    fetchPerformance(code, windowDays);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleFilter();
    }
  };

  // Pagination
  const totalPages = Math.ceil(totalResults / pageSize);
  const handlePageChange = (page: number) => {
    const windowDays = evalDays ? parseInt(evalDays, 10) : undefined;
    fetchResults(page, codeFilter.trim() || undefined, windowDays);
  };

  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="page-container bt-page">
      {/* Page header with back */}
      <div className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('backtest.title')}</h1>
      </div>

      {/* Filter bar */}
      <div className="bt-filter-bar">
        <div className="bt-filter-row">
          <input
            type="text"
            value={codeFilter}
            onChange={(e) => setCodeFilter(e.target.value.toUpperCase())}
            onKeyDown={handleKeyDown}
            placeholder="Filter by stock code (leave empty for all)"
            disabled={isRunning}
            className="bt-filter-input"
          />
          <button type="button" onClick={handleFilter} disabled={isLoadingResults} className="bt-filter-btn">
            Filter
          </button>
          <span className="bt-filter-label">Window</span>
          <input
            type="number" min={1} max={120} value={evalDays}
            onChange={(e) => setEvalDays(e.target.value)}
            placeholder="10" disabled={isRunning}
            className="bt-filter-input bt-filter-input-sm"
          />
          <button
            type="button"
            onClick={() => setForceRerun(!forceRerun)}
            disabled={isRunning}
            className={`bt-force-btn ${forceRerun ? 'active' : ''}`}
          >
            <span className={`bt-force-dot ${forceRerun ? 'active' : ''}`} />
            Force
          </button>
          <button type="button" onClick={handleRun} disabled={isRunning} className="analysis-submit-btn">
            {isRunning ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
        {runResult && <RunSummary data={runResult} />}
        {runError && <p className="input-error-msg">{runError}</p>}
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

      {/* Main content */}
      <div className="bt-main">
        {/* Left sidebar - Performance */}
        <div className="bt-sidebar">
          {isLoadingPerf ? (
            <div className="page-loading"><div className="spinner" /></div>
          ) : overallPerf ? (
            <PerformanceCard metrics={overallPerf} title="Overall Performance" />
          ) : (
            <div className="bt-perf-card">
              <p className="bt-empty-hint">
                No backtest data yet. Run a backtest to see performance metrics.
              </p>
            </div>
          )}

          {stockPerf && (
            <PerformanceCard metrics={stockPerf} title={`${stockPerf.code || codeFilter}`} />
          )}
        </div>

        {/* Right content - Results table */}
        <section className="bt-results">
          {isLoadingResults ? (
            <div className="page-loading"><div className="spinner" /><p>Loading results...</p></div>
          ) : results.length === 0 ? (
            <div className="page-empty">
              <div className="page-empty-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3>No Results</h3>
              <p>Run a backtest to evaluate historical analysis accuracy</p>
            </div>
          ) : (
            <>
              <div className="bt-table-wrap">
                <table className="bt-table">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Date</th>
                      <th>Advice</th>
                      <th>Dir.</th>
                      <th>Outcome</th>
                      <th className="bt-th-right">Return%</th>
                      <th className="bt-th-center">SL</th>
                      <th className="bt-th-center">TP</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((row) => (
                      <tr key={row.analysisHistoryId}>
                        <td className="bt-code">{row.code}</td>
                        <td>{row.analysisDate || '--'}</td>
                        <td className="bt-advice" title={row.operationAdvice || ''}>{row.operationAdvice || '--'}</td>
                        <td>
                          <span className="bt-dir-cell">
                            {boolIcon(row.directionCorrect)}
                            <span className="bt-icon-na">{row.directionExpected || ''}</span>
                          </span>
                        </td>
                        <td>{outcomeBadge(row.outcome)}</td>
                        <td className="bt-th-right">
                          <span className={row.simulatedReturnPct != null ? (row.simulatedReturnPct > 0 ? 'bt-icon-yes' : row.simulatedReturnPct < 0 ? 'bt-icon-no' : 'bt-text-secondary') : 'bt-icon-na'}>
                            {pct(row.simulatedReturnPct)}
                          </span>
                        </td>
                        <td className="bt-th-center">{boolIcon(row.hitStopLoss)}</td>
                        <td className="bt-th-center">{boolIcon(row.hitTakeProfit)}</td>
                        <td>{statusBadge(row.evalStatus)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="bt-pagination-wrap">
                <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} />
              </div>
              <p className="bt-total-count">{totalResults} result{totalResults !== 1 ? 's' : ''} total</p>
            </>
          )}
        </section>
      </div>
    </div>
  );
};

export default BacktestPage;
