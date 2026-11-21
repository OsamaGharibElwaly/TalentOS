'use client';

import ErrorState from '../components/ui/ErrorState';
import { friendlyError } from '../lib/errors';
import './globals.css';

export default function GlobalError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  return (
    <html lang="en">
      <body className="global-error-body">
        <ErrorState
          title="TalentOS could not start"
          message={friendlyError(error)}
          retry={retry}
        />
      </body>
    </html>
  );
}
