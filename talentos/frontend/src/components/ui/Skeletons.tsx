export function Skeleton({
  width = '100%',
  height = 14,
}: {
  width?: string;
  height?: number;
}) {
  return <div className="skeleton" aria-hidden="true" style={{ width, height }} />;
}

export function CandidateListSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="skeleton-stack" aria-hidden="true" aria-busy="true">
      {Array.from({ length: rows }, (_, index) => (
        <div className="skeleton-row" key={index}>
          <Skeleton width="40%" height={18} />
          <Skeleton width="25%" height={12} />
        </div>
      ))}
    </div>
  );
}

export function EvidenceSkeleton() {
  return (
    <div className="skeleton-stack" aria-hidden="true" aria-busy="true">
      <Skeleton width="70%" height={22} />
      <Skeleton height={12} />
      <Skeleton width="85%" height={12} />
      <Skeleton width="60%" height={12} />
      <Skeleton height={160} />
    </div>
  );
}
