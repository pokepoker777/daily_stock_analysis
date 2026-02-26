import type React from 'react';
import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import type { HistoryItem, AnalysisReport, TaskInfo } from '../types/analysis';
import { historyApi } from '../api/history';
import { analysisApi, DuplicateTaskError } from '../api/analysis';
import { validateStockCode } from '../utils/validation';
import { getRecentStartDate, toDateInputValue } from '../utils/format';
import { useAnalysisStore } from '../stores/analysisStore';
import { ReportSummary } from '../components/report';
import { HistoryList } from '../components/history';
import { TaskPanel } from '../components/tasks';
import { useTaskStream } from '../hooks';
import { useTranslation } from '../hooks/useTranslation';

const AnalysisPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialCode = searchParams.get('code') || '';
  const { setLoading, setError: setStoreError } = useAnalysisStore();

  const [stockCode, setStockCode] = useState(initialCode);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [inputError, setInputError] = useState<string>();
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;
  const [selectedReport, setSelectedReport] = useState<AnalysisReport | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [activeTasks, setActiveTasks] = useState<TaskInfo[]>([]);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const analysisRequestIdRef = useRef<number>(0);

  const updateTask = useCallback((updatedTask: TaskInfo) => {
    setActiveTasks((prev) => {
      const index = prev.findIndex((t) => t.taskId === updatedTask.taskId);
      if (index >= 0) { const n = [...prev]; n[index] = updatedTask; return n; }
      return prev;
    });
  }, []);

  const removeTask = useCallback((taskId: string) => {
    setActiveTasks((prev) => prev.filter((t) => t.taskId !== taskId));
  }, []);

  const fetchHistory = useCallback(async (autoSelectFirst = false, reset = true) => {
    if (reset) { setIsLoadingHistory(true); setCurrentPage(1); } else { setIsLoadingMore(true); }
    const page = reset ? 1 : currentPage + 1;
    try {
      const response = await historyApi.getList({ startDate: getRecentStartDate(30), endDate: toDateInputValue(new Date()), page, limit: pageSize });
      if (reset) setHistoryItems(response.items); else setHistoryItems(prev => [...prev, ...response.items]);
      const totalLoaded = reset ? response.items.length : historyItems.length + response.items.length;
      setHasMore(totalLoaded < response.total);
      setCurrentPage(page);
      if (autoSelectFirst && response.items.length > 0 && !selectedReport) {
        setIsLoadingReport(true);
        try { const report = await historyApi.getDetail(response.items[0].queryId); setSelectedReport(report); }
        catch (err) { console.warn('[Analysis] Failed to fetch report:', (err as Error).message); }
        finally { setIsLoadingReport(false); }
      }
    } catch (err) { console.warn('[Analysis] API unavailable, skipping history load:', (err as Error).message); }
    finally { setIsLoadingHistory(false); setIsLoadingMore(false); }
  }, [selectedReport, currentPage, historyItems.length, pageSize]);

  useTaskStream({
    onTaskCreated: (task) => { setActiveTasks((prev) => prev.some((t) => t.taskId === task.taskId) ? prev : [...prev, task]); },
    onTaskStarted: updateTask,
    onTaskCompleted: (task) => { fetchHistory(); setTimeout(() => removeTask(task.taskId), 2000); },
    onTaskFailed: (task) => { updateTask(task); setStoreError(task.error || t('analysis.taskFailed')); setTimeout(() => removeTask(task.taskId), 5000); },
    onError: () => { console.warn('SSE reconnecting...'); },
    enabled: true,
  });

  useEffect(() => { fetchHistory(true); }, []);

  // Auto-analyze if code passed via URL
  useEffect(() => {
    if (initialCode) {
      const { valid, normalized } = validateStockCode(initialCode);
      if (valid) {
        setStockCode(normalized);
        // Trigger analysis after a short delay
        const timer = setTimeout(() => handleAnalyze(normalized), 300);
        return () => clearTimeout(timer);
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleHistoryClick = async (queryId: string) => {
    analysisRequestIdRef.current += 1;
    setIsLoadingReport(true);
    try { const report = await historyApi.getDetail(queryId); setSelectedReport(report); }
    catch (err) { console.warn('[Analysis] Failed to fetch report:', (err as Error).message); }
    finally { setIsLoadingReport(false); }
  };

  const handleAnalyze = async (codeOverride?: string) => {
    const code = codeOverride || stockCode;
    const { valid, message, normalized } = validateStockCode(code);
    if (!valid) { setInputError(message); return; }
    setInputError(undefined); setDuplicateError(null); setIsAnalyzing(true); setLoading(true); setStoreError(null);
    const currentRequestId = ++analysisRequestIdRef.current;
    try {
      await analysisApi.analyzeAsync({ stockCode: normalized, reportType: 'detailed' });
      if (currentRequestId === analysisRequestIdRef.current) setStockCode('');
    } catch (err) {
      if (currentRequestId === analysisRequestIdRef.current) {
        if (err instanceof DuplicateTaskError) setDuplicateError(t('analysis.duplicate'));
        else {
          const msg = err instanceof Error ? err.message : t('analysis.taskFailed');
          const isNetwork = msg === 'Network Error' || msg.includes('ERR_CONNECTION');
          setStoreError(isNetwork ? '后端服务未启动，请先启动 API 服务' : msg);
        }
      }
    } finally { setIsAnalyzing(false); setLoading(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && stockCode && !isAnalyzing) handleAnalyze();
  };

  return (
    <div className="page-container analysis-page">
      {/* Page header with back button */}
      <header className="page-header">
        <button className="page-back-btn" onClick={() => navigate('/')}>
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/>
          </svg>
          <span>{t('actions.back')}</span>
        </button>
        <h1 className="page-title">{t('analysis.title')}</h1>
      </header>

      {/* Input bar */}
      <div className="analysis-input-bar">
        <div className="analysis-input-wrapper">
          <input
            type="text" value={stockCode}
            onChange={(e) => { setStockCode(e.target.value.toUpperCase()); setInputError(undefined); }}
            onKeyDown={handleKeyDown}
            placeholder={t('app.inputPlaceholder')}
            disabled={isAnalyzing}
            className="analysis-input"
          />
          <button onClick={() => handleAnalyze()} disabled={!stockCode || isAnalyzing} className="analysis-submit-btn">
            {isAnalyzing ? (
              <><svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>{t('actions.analyzing')}</>
            ) : t('actions.analyze')}
          </button>
        </div>
        {inputError && <p className="input-error-msg">{inputError}</p>}
        {duplicateError && <p className="input-warning-msg">{duplicateError}</p>}
      </div>

      {/* Main content: history + report */}
      <div className="analysis-body">
        <div className="analysis-sidebar">
          <TaskPanel tasks={activeTasks} />
          <HistoryList
            items={historyItems} isLoading={isLoadingHistory} isLoadingMore={isLoadingMore}
            hasMore={hasMore} selectedQueryId={selectedReport?.meta.queryId}
            onItemClick={handleHistoryClick}
            onLoadMore={() => { if (!isLoadingMore && hasMore) fetchHistory(false, false); }}
            className="analysis-history-list"
          />
        </div>
        <section className="analysis-report">
          {isLoadingReport ? (
            <div className="page-loading"><div className="spinner" /><p>{t('common.loading')}</p></div>
          ) : selectedReport ? (
            <div className="report-content"><ReportSummary data={selectedReport} isHistory /></div>
          ) : (
            <div className="page-empty">
              <div className="page-empty-icon">
                <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
              <h3>{t('analysis.inputHint')}</h3>
              <p>{t('analysis.noHistory')}</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default AnalysisPage;
