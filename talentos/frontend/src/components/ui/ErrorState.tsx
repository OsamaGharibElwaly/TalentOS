import Link from 'next/link';
import Icon from './Icon';

export default function ErrorState({
  title = 'We hit a snag',
  message,
  retry,
  compact = false,
}: {
  title?: string;
  message: string;
  retry?: () => void;
  compact?: boolean;
}) {
  return (
    <div className={`error-state${compact ? ' error-state-compact' : ''}`} role="alert">
      <span className="error-icon" aria-hidden="true"><Icon name="alert" size={compact ? 20 : 26} /></span>
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
        <div className="error-actions">
          {retry ? <button type="button" className="btn-primary" onClick={retry}>Try again</button> : null}
          <Link href="/" className="btn-ghost">Back to overview</Link>
        </div>
      </div>
    </div>
  );
}
