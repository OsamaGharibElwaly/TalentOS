'use client';
import { friendlyError } from '../../lib/errors';

import { useState, type DragEvent } from 'react';
import { api } from '../../lib/api-client';
import { ALLOWED_RESUME_EXTENSIONS, isAllowedResume } from '../../lib/security';
import type { UploadStatus } from '../../types/talentos';

const ACCEPT = ALLOWED_RESUME_EXTENSIONS.join(',');

export default function BulkResumeDropzone() {
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<UploadStatus[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) {
      return;
    }
    const accepted = Array.from(incoming).filter((file) => isAllowedResume(file.name));
    setFiles((current) => [...current, ...accepted]);
    setError(
      accepted.length === incoming.length ? '' : 'Some files were skipped: only PDF, DOCX, TXT and MD are supported.',
    );
  };

  const drop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    addFiles(event.dataTransfer.files);
  };

  const upload = async () => {
    if (files.length === 0) {
      return;
    }
    setBusy(true);
    setError('');
    try {
      setResults(await api.ingestResumes(files));
      setFiles([]);
    } catch (cause: unknown) {
      setError(friendlyError(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <h2>Upload resumes</h2>
      <div
        className="dropzone"
        onDragOver={(event) => event.preventDefault()}
        onDrop={drop}
        style={{ border: '1px dashed var(--line)', borderRadius: 10, padding: 24 }}
      >
        <input
          type="file"
          multiple
          accept={ACCEPT}
          onChange={(event) => addFiles(event.target.files)}
        />
        <p className="muted">Drag files here or choose up to 50 at a time.</p>
      </div>
      {files.length > 0 ? (
        <p className="muted">Selected: {files.map((file) => file.name).join(', ')}</p>
      ) : null}
      <button type="button" onClick={upload} disabled={busy || files.length === 0}>
        {busy ? 'Parsing & indexing…' : 'Ingest batch'}
      </button>
      {error ? <p className="error">{error}</p> : null}
      {results.length > 0 ? (
        <table>
          <thead>
            <tr><th>File</th><th>Status</th><th>Duplicate</th><th>SHA-256</th></tr>
          </thead>
          <tbody>
            {results.map((item) => (
              <tr key={`${item.file_hash}-${item.filename}`}>
                <td>{item.filename}</td>
                <td>
                  <span className={item.status === 'FAILED' ? 'badge bad' : 'badge ok'}>
                    {item.status}
                  </span>
                  {item.error ? <span className="error"> {item.error}</span> : null}
                </td>
                <td>{item.duplicate ? 'yes (existing profile reused)' : 'no'}</td>
                <td><code>{item.file_hash.slice(0, 12)}…</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
