/**
 * ErrorState — unified error display with optional retry.
 *
 * Usage:
 *   <ErrorState message="搜索失败" onRetry={() => refetch()} />
 *   <ErrorState message="暂无数据" variant="empty" />
 */
import "./ErrorState.css";

interface ErrorStateProps {
  message: string;
  details?: string;
  variant?: "error" | "empty" | "offline";
  onRetry?: () => void;
}

const ICONS: Record<string, string> = {
  error: "⚠️",
  empty: "📭",
  offline: "🔌",
};

const TITLES: Record<string, string> = {
  error: "出错了",
  empty: "暂无内容",
  offline: "网络连接中断",
};

export default function ErrorState({
  message,
  details,
  variant = "error",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className={`error-state error-state--${variant}`}>
      <div className="error-state-icon">{ICONS[variant]}</div>
      <h3 className="error-state-title">{TITLES[variant]}</h3>
      <p className="error-state-message">{message}</p>
      {details && <p className="error-state-details">{details}</p>}
      {onRetry && (
        <button className="btn-primary error-state-retry" onClick={onRetry}>
          🔄 重试
        </button>
      )}
    </div>
  );
}
