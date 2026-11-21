'use client';

import BulkResumeDropzone from '../../components/ingestion/BulkResumeDropzone';
import DeveloperMode from '../../components/ui/DeveloperMode';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';

export default function IngestionPage() {
  return (
    <section>
      <h1>Add resumes</h1>
      <p className="muted">
        Drop in one resume or many. We read each file, add the person to your workspace and skip duplicates.
      </p>
      <BulkResumeDropzone />
      <DeveloperMode {...DEVELOPER_RECIPES.ingestion} />
    </section>
  );
}
