import type React from 'react';
import { useRef, useCallback, useEffect } from 'react';
import type { HistoryItem } from '../../types/analysis';
import { formatDateTime } from '../../utils/format';

interface HistoryListProps {
  items: HistoryItem[];
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  selectedQueryId?: string;
  onItemClick: (queryId: string) => void;
  onLoadMore: () => void;
  className?: string;
}

/**
 * 历史记录列表组件
 * 显示最近的股票分析历史，支持点击查看详情和滚动加载更多
 */
export const HistoryList: React.FC<HistoryListProps> = ({
  items,
  isLoading,
  isLoadingMore,
  hasMore,
  selectedQueryId,
  onItemClick,
  onLoadMore,
  className = '',
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const loadMoreTriggerRef = useRef<HTMLDivElement>(null);

  // 使用 IntersectionObserver 检测滚动到底部
  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const target = entries[0];
      // 只有当触发器真正可见且有更多数据时才加载
      if (target.isIntersecting && hasMore && !isLoading && !isLoadingMore) {
        // 确保容器有滚动能力（内容超过容器高度）
        const container = scrollContainerRef.current;
        if (container && container.scrollHeight > container.clientHeight) {
          onLoadMore();
        }
      }
    },
    [hasMore, isLoading, isLoadingMore, onLoadMore]
  );

  useEffect(() => {
    const trigger = loadMoreTriggerRef.current;
    const container = scrollContainerRef.current;
    if (!trigger || !container) return;

    const observer = new IntersectionObserver(handleObserver, {
      root: container,
      rootMargin: '20px', // 减小预加载距离
      threshold: 0.1, // 触发器至少 10% 可见时才触发
    });

    observer.observe(trigger);

    return () => {
      observer.disconnect();
    };
  }, [handleObserver]);

  return (
    <aside className={`history-panel ${className}`}>
      <div className="history-panel-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="history-panel-title">历史记录</span>
      </div>

      <div ref={scrollContainerRef} className="history-panel-body">
        {isLoading ? (
          <div className="history-empty"><div className="spinner spinner-sm" /></div>
        ) : items.length === 0 ? (
          <div className="history-empty">暂无历史记录</div>
        ) : (
          <>
            {items.map((item) => (
              <button
                key={item.queryId}
                type="button"
                onClick={() => onItemClick(item.queryId)}
                className={`history-item ${selectedQueryId === item.queryId ? 'active' : ''}`}
              >
                {item.sentimentScore !== undefined && (
                  <span
                    className={`history-item-indicator history-sentiment-bg-${item.sentimentScore >= 70 ? 'positive' : item.sentimentScore >= 40 ? 'neutral' : 'negative'}`}
                  />
                )}
                <div className="history-item-content">
                  <div className="history-item-row">
                    <span className="history-item-name">
                      {item.stockName || item.stockCode}
                    </span>
                    {item.sentimentScore !== undefined && (
                      <span
                        className={`history-item-score history-sentiment-${item.sentimentScore >= 70 ? 'positive' : item.sentimentScore >= 40 ? 'neutral' : 'negative'}`}
                      >
                        {item.sentimentScore}
                      </span>
                    )}
                  </div>
                  <div className="history-item-meta">
                    <span className="history-item-code">{item.stockCode}</span>
                    <span className="history-item-dot">·</span>
                    <span className="history-item-time">{formatDateTime(item.createdAt)}</span>
                  </div>
                </div>
              </button>
            ))}

            <div ref={loadMoreTriggerRef} style={{ height: 16 }} />

            {isLoadingMore && (
              <div className="history-empty"><div className="spinner" style={{ width: 16, height: 16 }} /></div>
            )}

            {!hasMore && items.length > 0 && (
              <div className="history-end">已加载全部</div>
            )}
          </>
        )}
      </div>
    </aside>
  );
};
