/** QuickNav — cross-feature navigation for 问津's 5-stage workflow.
 *
 *  Design informed by Notion, Linear, and Typeform UX patterns:
 *  - Linear wizard "Next Step" CTA at natural completion points
 *  - Compact bar that shows where the user is in the overall journey
 *  - Only appears after user has completed a meaningful action on the page
 */

import { useNavigate } from "react-router-dom";

interface Step {
  label: string;
  path: string;
  icon: string;
}

const WORKFLOW: Step[] = [
  { label: "身份设置",   path: "/identity",       icon: "👤" },
  { label: "选题设计",   path: "/topic",           icon: "💡" },
  { label: "问卷设计",   path: "/questionnaire",   icon: "📋" },
  { label: "方法论规划", path: "/methodology",     icon: "📐" },
  { label: "田野工具",   path: "/fieldwork",       icon: "🎙" },
  { label: "数据分析",   path: "/analysis",        icon: "📊" },
  { label: "成果导出",   path: "/export",          icon: "📄" },
  { label: "调查档案",   path: "/library",         icon: "📚" },
];

export interface QuickNavProps {
  currentPath: string;
  /** Only render when user has completed something on this page */
  visible: boolean;
  nextPath?: string;
  nextLabel?: string;
  prevPath?: string;
  prevLabel?: string;
}

export default function QuickNav({
  currentPath,
  visible,
  nextPath,
  nextLabel,
  prevPath,
  prevLabel,
}: QuickNavProps) {
  const navigate = useNavigate();

  const idx = WORKFLOW.findIndex((s) => s.path === currentPath);
  if (idx === -1 || !visible) return null;

  const current = WORKFLOW[idx];
  const prev = prevPath
    ? WORKFLOW.find((s) => s.path === prevPath)
    : idx > 0 ? WORKFLOW[idx - 1] : null;
  const next = nextPath
    ? WORKFLOW.find((s) => s.path === nextPath)
    : idx < WORKFLOW.length - 1 ? WORKFLOW[idx + 1] : null;

  return (
    <div
      style={{
        marginTop: 32,
        padding: "14px 18px",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        display: "flex",
        alignItems: "center",
        gap: 12,
        flexWrap: "wrap",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      <div style={{
        display: "flex", alignItems: "center", gap: 6,
        fontSize: 12, color: "var(--text-muted)", minWidth: 100,
      }}>
        <span style={{ fontSize: 16 }}>{current.icon}</span>
        <span>步骤 {idx + 1}/{WORKFLOW.length}：<strong>{current.label}</strong></span>
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ display: "flex", gap: 8 }}>
        {prev && (
          <button
            onClick={() => navigate(prev.path)}
            style={{
              padding: "8px 14px",
              background: "var(--surface)",
              color: "var(--text-muted)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            ← {prevLabel || prev.label}
          </button>
        )}

        {next && (
          <button
            onClick={() => navigate(next.path)}
            style={{
              padding: "8px 20px",
              background: "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}
          >
            {nextLabel || next.label} →
          </button>
        )}
      </div>
    </div>
  );
}

export { WORKFLOW };
