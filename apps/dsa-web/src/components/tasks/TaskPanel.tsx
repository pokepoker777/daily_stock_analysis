import type React from 'react';
import type { TaskInfo } from '../../types/analysis';

/**
 * 任务项组件属性
 */
interface TaskItemProps {
  task: TaskInfo;
}

/**
 * 单个任务项
 */
const TaskItem: React.FC<TaskItemProps> = ({ task }) => {
  const isPending = task.status === 'pending';
  const isProcessing = task.status === 'processing';

  return (
    <div className="task-item">
      <div className="task-item-icon">
        {isProcessing ? (
          <div className="spinner spinner-xs" />
        ) : isPending ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="task-item-clock">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ) : null}
      </div>
      <div className="task-item-content">
        <div className="task-item-header">
          <span className="task-item-name">{task.stockName || task.stockCode}</span>
          <span className="task-item-code">{task.stockCode}</span>
        </div>
        {task.message && <p className="task-item-msg">{task.message}</p>}
      </div>
      <span className={`task-item-badge ${isProcessing ? 'processing' : 'pending'}`}>
        {isProcessing ? '分析中' : '等待中'}
      </span>
    </div>
  );
};

/**
 * 任务面板属性
 */
interface TaskPanelProps {
  /** 任务列表 */
  tasks: TaskInfo[];
  /** 是否显示 */
  visible?: boolean;
  /** 标题 */
  title?: string;
  /** 自定义类名 */
  className?: string;
}

/**
 * 任务面板组件
 * 显示进行中的分析任务列表
 */
export const TaskPanel: React.FC<TaskPanelProps> = ({
  tasks,
  visible = true,
  title = '分析任务',
  className = '',
}) => {
  // 筛选活跃任务（pending 和 processing）
  const activeTasks = tasks.filter(
    (t) => t.status === 'pending' || t.status === 'processing'
  );

  // 无任务或不可见时不渲染
  if (!visible || activeTasks.length === 0) {
    return null;
  }

  const pendingCount = activeTasks.filter((t) => t.status === 'pending').length;
  const processingCount = activeTasks.filter((t) => t.status === 'processing').length;

  return (
    <div className={`task-panel ${className}`}>
      <div className="task-panel-header">
        <div className="task-panel-header-left">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span className="task-panel-title">{title}</span>
        </div>
        <div className="task-panel-stats">
          {processingCount > 0 && (
            <span className="task-panel-stat-active">
              <span className="task-panel-stat-dot" />
              {processingCount} 进行中
            </span>
          )}
          {pendingCount > 0 && <span>{pendingCount} 等待中</span>}
        </div>
      </div>
      <div className="task-panel-body">
        {activeTasks.map((task) => (
          <TaskItem key={task.taskId} task={task} />
        ))}
      </div>
    </div>
  );
};

export default TaskPanel;
