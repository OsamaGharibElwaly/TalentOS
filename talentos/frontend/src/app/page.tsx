import Link from 'next/link';
import HiringDashboard from '../components/dashboard/HiringDashboard';
import BrandMark from '../components/ui/BrandMark';
import DeveloperMode from '../components/ui/DeveloperMode';
import Icon from '../components/ui/Icon';
import { DEVELOPER_RECIPES } from '../lib/developer-recipes';
import { WORKFLOW_ITEMS } from '../lib/navigation';

export default function OverviewPage() {
  return (
    <section className="overview">
      <div className="page-hero">
        <div>
          <p className="eyebrow"><BrandMark size={18} /> Your hiring workspace</p>
          <h1>Good to see you. Here is today at a glance.</h1>
          <p className="hero-copy">
            TalentOS keeps your roles, resumes, reviews and interviews together in one calm place.
            Start with the guided tour if this is your first visit.
          </p>
          <div className="hero-actions">
            <Link href="/guide" className="btn-primary">Take the guided tour <span aria-hidden="true">→</span></Link>
            <Link href="/ingestion" className="btn-ghost">Add resumes</Link>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <span className="orbit orbit-one" />
          <span className="orbit orbit-two" />
          <span className="hero-card hero-card-one">Roles</span>
          <span className="hero-card hero-card-two">People</span>
          <span className="hero-card hero-card-three">Offers</span>
        </div>
      </div>

      <HiringDashboard />

      <div className="section-heading">
        <h2>What you can do</h2>
        <p className="muted">Every step of a hire, in the order a person would actually do it.</p>
      </div>
      <div className="capability-grid">
        {WORKFLOW_ITEMS.map((item) => (
          <Link key={item.path} href={item.path} className={`capability-card tone-${item.tone}`}>
            <span className="capability-icon" aria-hidden="true"><Icon name={item.icon} size={22} /></span>
            <strong>{item.label}</strong>
            <span className="muted">{item.description}</span>
            <span className="capability-arrow" aria-hidden="true">→</span>
          </Link>
        ))}
      </div>

      <div className="guide-teaser">
        <div>
          <p className="eyebrow">New to this workspace?</p>
          <h2>Follow one hire from start to finish</h2>
          <p className="muted">
            The guide walks through each screen with plain instructions and a small visual of what happens next.
          </p>
        </div>
        <Link href="/guide" className="btn-primary">Open the guide <span aria-hidden="true">→</span></Link>
      </div>

      <DeveloperMode {...DEVELOPER_RECIPES.overview} />
    </section>
  );
}
