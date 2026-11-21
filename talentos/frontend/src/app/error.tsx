'use client';

import { useEffect } from 'react';
import ErrorState from '../components/ui/ErrorState';
import { friendlyError } from '../lib/errors';

export default function Error({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="page-error">
      <ErrorState
        title="This screen could not open"
        message={friendlyError(error)}
        retry={retry}
      />
    </div>
  );
}
