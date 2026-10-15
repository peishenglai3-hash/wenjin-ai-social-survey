/**
 * Skeleton loading placeholder — animated shimmer cards, text lines, etc.
 *
 * Usage:
 *   <Skeleton variant="text" width="60%" />
 *   <Skeleton variant="card" count={3} />
 *   <Skeleton variant="table-row" count={5} />
 */
import "./Skeleton.css";

interface SkeletonProps {
  variant?: "text" | "card" | "table-row" | "circle" | "inline";
  width?: string;
  height?: string;
  count?: number;
}

export default function Skeleton({
  variant = "text",
  width,
  height,
  count = 1,
}: SkeletonProps) {
  const items = Array.from({ length: count }, (_, i) => i);

  const baseClass = `skeleton skeleton-${variant}`;
  const style: React.CSSProperties = {};
  if (width) style.width = width;
  if (height) style.height = height;

  if (variant === "card") {
    return (
      <>
        {items.map((i) => (
          <div key={i} className={baseClass} style={style}>
            <div className="skeleton-card-img" />
            <div className="skeleton-card-body">
              <div className="skeleton-line skeleton-line--title" />
              <div className="skeleton-line skeleton-line--sub" />
              <div className="skeleton-line skeleton-line--sub short" />
            </div>
          </div>
        ))}
      </>
    );
  }

  if (variant === "table-row") {
    return (
      <>
        {items.map((i) => (
          <div key={i} className={baseClass} style={style}>
            <div className="skeleton-line skeleton-line--cell" />
            <div className="skeleton-line skeleton-line--cell" />
            <div className="skeleton-line skeleton-line--cell short" />
          </div>
        ))}
      </>
    );
  }

  return (
    <>
      {items.map((i) => (
        <div key={i} className={baseClass} style={style} />
      ))}
    </>
  );
}
