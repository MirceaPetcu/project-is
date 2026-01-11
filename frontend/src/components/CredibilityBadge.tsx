interface CredibilityBadgeProps {
  score: number;
  showLabel?: boolean;
}

function getCredibilityLevel(score: number): {
  label: string;
  className: string;
} {
  if (score >= 0.8) return { label: 'Verified', className: 'badge-success' };
  if (score >= 0.6) return { label: 'High', className: 'badge-success' };
  if (score >= 0.4) return { label: 'Medium', className: 'badge-warning' };
  if (score >= 0.2) return { label: 'Low', className: 'badge-danger' };
  return { label: 'Unverified', className: 'badge-neutral' };
}

export default function CredibilityBadge({
  score,
  showLabel = true,
}: CredibilityBadgeProps) {
  const { label, className } = getCredibilityLevel(score);

  return (
    <span className={`badge ${className}`}>
      {showLabel ? label : `${Math.round(score * 100)}%`}
    </span>
  );
}
