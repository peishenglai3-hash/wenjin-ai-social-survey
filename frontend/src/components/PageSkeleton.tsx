/**
 * PageSkeleton — Suspense fallback shown while lazy-loaded route chunks load.
 *
 * Uses the existing Skeleton component for visual consistency.
 * Designed to be lightweight enough for mobile devices with slow connections.
 */
import Skeleton from "./Skeleton";

export default function PageSkeleton() {
  return (
    <div className="page-skeleton" aria-busy="true" aria-label="页面加载中">
      {/* Header skeleton — mimics page title bar */}
      <div style={{ marginBottom: 24 }}>
        <Skeleton variant="text" width="35%" />
        <Skeleton variant="text" width="60%" />
      </div>

      {/* Content skeleton — mimics card layout */}
      <Skeleton variant="card" count={3} />

      {/* Secondary section */}
      <div style={{ marginTop: 24 }}>
        <Skeleton variant="text" width="25%" />
        <Skeleton variant="card" count={2} />
      </div>
    </div>
  );
}
