'use client';

import TalentSearchWorkbench from '../../components/search/TalentSearchWorkbench';
import DeveloperMode from '../../components/ui/DeveloperMode';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';

export default function TalentPoolPage() {
  return (
    <section>
      <h1>Find talent</h1>
      <p className="muted">Search everyone in your organization by skill, years of experience and where they are in your process.</p>
      <TalentSearchWorkbench />
      <DeveloperMode {...DEVELOPER_RECIPES.talentPool} />
    </section>
  );
}
