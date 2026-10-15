import { useState, useEffect } from "react";
import api from "../api/client";

interface TokenSummary {
  hours: number;
  total_calls: number;
  failed_calls: number;
  total_tokens: number;
  estimated_cost_cny: number;
  by_model: Record<string, number>;
  by_task: Record<string, number>;
}

export default function Admin() {
  const [health, setHealth] = useState<string>("checking...");
  const [tokenSummary, setTokenSummary] = useState<TokenSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${import.meta.env.VITE_API_BASE_URL ?? ""}/health`)
        .then((r) => r.json())
        .then((d) => setHealth(JSON.stringify(d)))
        .catch(() => setHealth("unreachable")),
      api.get("/monitor/tokens/summary", { params: { hours: 168 } })
        .then((r) => setTokenSummary(r.data))
        .catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="page">
        <h2>管理面板</h2>
        <p className="subtitle">加载中…</p>
      </div>
    );
  }

  return (
    <div className="page">
      <h2>管理面板</h2>
      <p className="subtitle">系统状态 · 用量概览 · 用户管理</p>

      <section className="admin-section">
        <h3>系统状态</h3>
        <div className="admin-grid">
          <div className="stat-card">
            <div className="stat-label">后端健康</div>
            <div className="stat-value" style={{ color: health === "unreachable" ? "#dc2626" : "#16a34a" }}>
              {health === "unreachable" ? "不可达" : "正常"}
            </div>
            <div className="stat-detail">{health}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">访问地址</div>
            <div className="stat-value" style={{ fontSize: 14 }}>configured deployment</div>
            <div className="stat-detail">SSL已启用 · 域名正常运行</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">认证系统</div>
            <div className="stat-value" style={{ color: "#16a34a" }}>已启用</div>
            <div className="stat-detail">JWT + CAPTCHA · 管理员已创建</div>
          </div>
        </div>
      </section>

      <section className="admin-section">
        <h3>AI 用量概览（近7天）</h3>
        {tokenSummary ? (
          <div className="admin-grid">
            <div className="stat-card">
              <div className="stat-label">总调用次数</div>
              <div className="stat-value">{tokenSummary.total_calls}</div>
              <div className="stat-detail">失败 {tokenSummary.failed_calls} 次</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">总 Token 消耗</div>
              <div className="stat-value">{tokenSummary.total_tokens.toLocaleString()}</div>
              <div className="stat-detail">预估 ¥{tokenSummary.estimated_cost_cny.toFixed(2)} CNY</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">按模型分布</div>
              <div className="stat-detail" style={{ textAlign: "left", lineHeight: 1.8 }}>
                {Object.entries(tokenSummary.by_model).map(([model, count]) => (
                  <div key={model} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{model}</span>
                    <span>{count.toLocaleString()} tokens</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p className="subtitle">暂无用量的报告</p>
        )}
      </section>

      <section className="admin-section">
        <h3>注册用户</h3>
        <p className="subtitle">用户管理功能即将上线。</p>
        <div className="admin-grid">
          <div className="stat-card">
            <div className="stat-label">管理员</div>
            <div className="stat-value">configured account</div>
            <div className="stat-detail">role=admin</div>
          </div>
        </div>
      </section>
    </div>
  );
}
