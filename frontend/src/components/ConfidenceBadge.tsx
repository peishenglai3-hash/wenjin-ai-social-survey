/** Visual confidence badge — high/medium/low with color coding. */
import type { FC } from "react";

interface Props {
  confidence: number; // 0.0 – 1.0
  size?: "sm" | "md";
  showLabel?: boolean;
}

const LEVELS: Record<string, { label: string; color: string; bg: string }> = {
  high: { label: "高置信度", color: "#16a34a", bg: "#dcfce7" },
  medium: { label: "中置信度", color: "#ca8a04", bg: "#fef9c3" },
  low: { label: "低置信度", color: "#dc2626", bg: "#fee2e2" },
};

function getLevel(c: number): keyof typeof LEVELS {
  if (c >= 0.7) return "high";
  if (c >= 0.4) return "medium";
  return "low";
}

const ConfidenceBadge: FC<Props> = ({ confidence, size = "md", showLabel = true }) => {
  const level = LEVELS[getLevel(confidence)];
  const dotSize = size === "sm" ? 8 : 12;
  const fontSize = size === "sm" ? 11 : 13;

  return (
    <span
      title={`置信度: ${(confidence * 100).toFixed(0)}%`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: size === "sm" ? "1px 6px" : "2px 10px",
        borderRadius: "var(--radius, 4px)",
        background: level.bg,
        color: level.color,
        fontSize,
        fontWeight: 600,
        whiteSpace: "nowrap",
        lineHeight: 1.5,
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: dotSize,
          height: dotSize,
          borderRadius: "50%",
          background: level.color,
          flexShrink: 0,
        }}
      />
      {showLabel && level.label}
    </span>
  );
};

export default ConfidenceBadge;
