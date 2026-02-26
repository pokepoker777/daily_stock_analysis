import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import { validateStockCode } from '../utils/validation';
import { analysisApi } from '../api/analysis';

interface SentimentResult {
  stockCode: string;
  stockName: string | null;
  sentimentScore: number | null;
  sentimentLabel: string | null;
  operationAdvice: string | null;
  trendPrediction: string | null;
  analysisSummary: string | null;
  newsContent: string | null;
}

const SentimentPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [stockCode, setStockCode] = useState('');
  const [inputError, setInputError] = useState<string>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SentimentResult | null>(null);

  const handleAnalyze = async () => {
    const { valid, message, normalized } = validateStockCode(stockCode);
    if (!valid) { setInputError(message); return; }
    setInputError(undefined);
    setError(null);
    setIsLoading(true);
    try {
      const resp = await analysisApi.analyze({ stockCode: normalized, reportType: 'detailed' });
      const report = resp.report;
      setResult({
        stockCode: resp.stockCode ?? normalized,
        stockName: resp.stockName ?? null,
        sentimentScore: report?.summary?.sentimentScore ?? null,
        sentimentLabel: report?.summary?.sentimentLabel ?? null,
        operationAdvice: report?.summary?.operationAdvice ?? null,
        trendPrediction: report?.summary?.trendPrediction ?? null,
        analysisSummary: report?.summary?.analysisSummary ?? null,
        newsContent: report?.details?.newsContent ?? null,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '分析失败';
      const isNetwork = msg === 'Network Error' || msg.includes('ERR_CONNECTION');
      setError(isNetwork ? '后端服务未连接 — 请先启动 API 服务 (python server.py)' : msg);
    } finally {
      setIsLoading(false);
    }
  };

  const scoreColor = (score: number | null) => {
    if (score === null) return '';
    if (score >= 70) return 'text-green';
    if (score <= 30) return 'text-red';
    return 'text-orange';
  };

  const scoreLabel = (score: number | null) => {
    if (score === null) return '未知';
    if (score >= 70) return '积极';
    if (score <= 30) return '消极';
    return '中性';
  };

  return (
    <div className="page-container">
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('home.toolSentiment')}</h1>
      </header>

      {/* Input bar */}
      <div className="analysis-input-bar">
        <div className="analysis-input-wrapper">
          <input
            type="text"
            value={stockCode}
            onChange={(e) => { setStockCode(e.target.value.toUpperCase()); setInputError(undefined); }}
            onKeyDown={(e) => e.key === 'Enter' && stockCode && !isLoading && handleAnalyze()}
            placeholder={t('app.inputPlaceholder')}
            disabled={isLoading}
            className="analysis-input"
          />
          <button onClick={handleAnalyze} disabled={!stockCode || isLoading} className="analysis-submit-btn">
            {isLoading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                分析中...
              </>
            ) : '舆情分析'}
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
        <div className="page-loading">
          <div className="spinner" />
          <p>正在进行 AI 舆情分析，请稍候（可能需要 30-60 秒）...</p>
        </div>
      )}

      {result && !isLoading && (
        <>
          {/* Score hero */}
          <div className="tool-page-summary">
            <div className="tool-page-summary-title">
              {result.stockName ?? result.stockCode} · 舆情评分
            </div>
            <div className="sentiment-score-hero">
              <span className={`sentiment-score-number ${scoreColor(result.sentimentScore)}`}>
                {result.sentimentScore ?? '--'}
              </span>
              <span className={`tool-page-tag ${scoreColor(result.sentimentScore)}`}>
                {result.sentimentLabel || scoreLabel(result.sentimentScore)}
              </span>
            </div>
          </div>

          <div className="tool-page-grid">
            {/* Operation Advice */}
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                操作建议
              </h3>
              <p className="tool-page-card-body">{result.operationAdvice || '暂无建议'}</p>
            </div>

            {/* Trend Prediction */}
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                趋势预测
              </h3>
              <p className="tool-page-card-body">{result.trendPrediction || '暂无预测'}</p>
            </div>
          </div>

          {/* Full summary */}
          {result.analysisSummary && (
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                分析摘要
              </h3>
              <p className="tool-page-card-body tool-page-card-body-pre">{result.analysisSummary}</p>
            </div>
          )}

          {/* News content */}
          {result.newsContent && (
            <div className="tool-page-card">
              <h3 className="tool-page-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
                新闻舆情
              </h3>
              <p className="tool-page-card-body tool-page-card-body-pre">{result.newsContent}</p>
            </div>
          )}
        </>
      )}

      {!isLoading && !result && !error && (
        <div className="page-empty">
          <div className="page-empty-icon">
            <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
            </svg>
          </div>
          <h3>输入股票代码，分析市场舆情</h3>
          <p>AI 将综合新闻、公告、社交媒体情绪给出评分与建议</p>
        </div>
      )}
    </div>
  );
};

export default SentimentPage;
