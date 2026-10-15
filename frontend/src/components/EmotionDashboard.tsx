/**
 * EmotionDashboard — Real-time emotion visualization panel.
 *
 * Displays live facial emotion signals from CameraCapture:
 *  - Emotion timeline chart (ECharts)
 *  - Current engagement gauge
 *  - Expression history log
 */

import { useEffect, useRef, useMemo } from "react";
import * as echarts from "echarts";
import type { FacialSignal } from "./CameraCapture";

interface EmotionDashboardProps {
  signals: FacialSignal[];
  maxHistory?: number;
  height?: number;
}

const EXPR_COLORS: Record<string, string> = {
  happy: "#10B981", surprised: "#F59E0B", concentrating: "#6366F1",
  tired: "#94A3B8", uncertain: "#F97316", neutral: "#6B7280",
};

export default function EmotionDashboard({
  signals, maxHistory = 60, height = 280,
}: EmotionDashboardProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstRef = useRef<echarts.ECharts | null>(null);

  const recent = useMemo(() => signals.slice(-maxHistory), [signals, maxHistory]);
  const latest = recent.length > 0 ? recent[recent.length - 1] : null;

  useEffect(() => {
    if (!chartRef.current) return;
    if (!chartInstRef.current) chartInstRef.current = echarts.init(chartRef.current);
    const chart = chartInstRef.current;

    const times = recent.map((s) => {
      const d = new Date(s.timestamp);
      return `${d.getMinutes()}:${String(d.getSeconds()).padStart(2, "0")}`;
    });

    chart.setOption({
      grid: { top: 10, right: 20, bottom: 30, left: 45 },
      tooltip: { trigger: "axis" },
      legend: { bottom: 0, textStyle: { fontSize: 10 } },
      xAxis: { type: "category", data: times, axisLabel: { fontSize: 9, rotate: 30 } },
      yAxis: { type: "value", min: 0, max: 1, axisLabel: { fontSize: 9 } },
      series: [
        {
          name: "专注度", type: "line", data: recent.map((s) => s.engagement),
          smooth: true, lineStyle: { color: "#6366F1", width: 2 },
          areaStyle: { color: "rgba(99,102,241,0.1)" }, symbol: "none",
        },
        {
          name: "EAR(眨眼)", type: "line",
          data: recent.map((s) => (s.ear_left + s.ear_right) / 2),
          smooth: true, lineStyle: { color: "#0EA5E9", width: 1.5, type: "dashed" },
          symbol: "none",
        },
        {
          name: "微笑度", type: "line",
          data: recent.map((s) => Math.max(0, s.mouth_curve)),
          smooth: true, lineStyle: { color: "#10B981", width: 1.5 }, symbol: "none",
        },
        {
          name: "偏头(°)", type: "line",
          data: recent.map((s) => s.head_yaw),
          smooth: true, lineStyle: { color: "#F97316", width: 1 }, symbol: "none",
        },
      ],
    }, true);
  }, [recent]);

  useEffect(() => {
    return () => { chartInstRef.current?.dispose(); chartInstRef.current = null; };
  }, []);

  const gaugeColor = latest
    ? latest.engagement > 0.7 ? "#10B981" : latest.engagement > 0.4 ? "#F59E0B" : "#EF4444"
    : "#6B7280";

  const exprColor = latest ? EXPR_COLORS[latest.expression] || "#6B7280" : "#6B7280";
  const exprLabel = latest
    ? latest.expression === "happy" ? "😊 愉悦" :
      latest.expression === "surprised" ? "😲 惊讶" :
      latest.expression === "concentrating" ? "🤔 专注" :
      latest.expression === "tired" ? "😴 疲惫" :
      latest.expression === "uncertain" ? "😕 迟疑" : "😐 中性"
    : "—";

  return (
    <div className="emotion-dashboard" style={{ padding: "12px 0" }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: 10, marginBottom: 16 }}>
        <div style={{ padding: "10px 12px", background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)", textAlign: "center" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>专注度</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: gaugeColor }}>
            {latest ? Math.round(latest.engagement * 100) : "—"}%
          </div>
        </div>
        <div style={{ padding: "10px 12px", background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)", textAlign: "center" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>表情</div>
          <div style={{ fontSize: 18, color: exprColor }}>{exprLabel}</div>
        </div>
        <div style={{ padding: "10px 12px", background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)", textAlign: "center" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>头部姿态</div>
          <div style={{ fontSize: 13, fontWeight: 600 }}>
            {latest ? `↔${Math.round(latest.head_yaw)}° ↕${Math.round(latest.head_pitch)}°` : "—"}
          </div>
        </div>
        <div style={{ padding: "10px 12px", background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)", textAlign: "center" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>数据点</div>
          <div style={{ fontSize: 18, fontWeight: 600 }}>{signals.length}</div>
        </div>
      </div>

      <div style={{ padding: "12px", background: "var(--surface)", borderRadius: 10, border: "1px solid var(--border)" }}>
        <h4 style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600 }}>📈 情绪时间线</h4>
        <div ref={chartRef} style={{ width: "100%", height }} />
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 12, flexWrap: "wrap", fontSize: 11, color: "var(--text-muted)" }}>
        <span>🟣 专注度</span> <span>🔵 EAR眨眼频率</span>
        <span>🟢 微笑度</span> <span>🟠 头部偏转(°)</span>
      </div>
    </div>
  );
}
