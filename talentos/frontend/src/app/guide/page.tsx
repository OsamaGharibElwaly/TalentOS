import Link from 'next/link';
import DeveloperMode from '../../components/ui/DeveloperMode';
import Icon from '../../components/ui/Icon';
import { DEVELOPER_RECIPES } from '../../lib/developer-recipes';

const STEPS = [
  {
    number: '01',
    title: 'Describe the role',
    path: '/jobs',
    action: 'Open Jobs & Scorecards, add the job title and a short description, then list the skills you care about and how important each one is.',
    why: 'Everyone who reviews later uses the same list, so decisions stay consistent and easy to explain.',
    icon: 'clipboard',
  },
  {
    number: '02',
    title: 'Bring in resumes',
    path: '/ingestion',
    action: 'Open Add Resumes and drop in the files you have. Each one is checked and added to your private workspace.',
    why: 'You get a searchable pool of people without copying details between emails and spreadsheets.',
    icon: 'upload',
  },
  {
    number: '03',
    title: 'Review people fairly',
    path: '/candidates',
    action: 'Open Review Candidates, choose a person, and read the resume beside the skills you set for the role. Mark your rating and note the line in the resume that supports it.',
    why: 'Every rating has its evidence next to it, which makes shortlisting easier to discuss with a hiring team.',
    icon: 'search',
  },
  {
    number: '04',
    title: 'Prepare the conversation',
    path: '/interviews',
    action: 'Open Interviews, pick a candidate and a role, then use the suggested questions to guide your conversation and capture your notes.',
    why: 'You walk into each interview with a clear plan and leave with notes you can actually compare.',
    icon: 'chat',
  },
  {
    number: '05',
    title: 'Find more people',
    path: '/talent-pool',
    action: 'Open Find Talent and search by skill, years of experience or current stage in your process.',
    why: 'A strong candidate from one role can be considered for another without starting over.',
    icon: 'spark',
  },
  {
    number: '06',
    title: 'See the whole picture',
    path: '/telemetry',
    action: 'Open Activity & Insights to see your pipeline numbers, common skills and suggested next steps. Recruiters and admins can open it.',
    why: 'You can spot bottlenecks early and explain what the team has accomplished.',
    icon: 'chart',
  },
] as const;

const JOURNEY = [
  { label: 'Plan the role', detail: 'Agree what good looks like' },
  { label: 'Meet the people', detail: 'Bring in and read resumes' },
  { label: 'Decide together', detail: 'Compare with evidence' },
  { label: 'Learn and improve', detail: 'See the full picture' },
] as const;

export default function GuidePage() {
  return (
    <section className="guide">
      <div className="page-hero guide-hero">
        <div>
          <p className="eyebrow">Getting started</p>
          <h1>One hire, from first hello to final decision.</h1>
          <p className="hero-copy">
            This guide is written for people who hire, not for people who build software. Follow it once
            and the whole workspace will feel familiar. It takes about ten minutes.
          </p>
          <div className="hero-actions">
            <Link href="/jobs" className="btn-primary">Start with step one <span aria-hidden="true">→</span></Link>
            <Link href="/" className="btn-ghost">Back to overview</Link>
          </div>
        </div>
        <div className="journey-art" aria-hidden="true">
          <div className="journey-track">
            {JOURNEY.map((item, index) => (
              <div className="journey-node" key={item.label} style={{ animationDelay: `${index * 500}ms` }}>
                <span className="journey-dot">{index + 1}</span>
                <strong>{item.label}</strong>
                <small>{item.detail}</small>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section-heading">
        <h2>Your journey, step by step</h2>
        <p className="muted">Move in this order for your first hire. After that, jump wherever you need to.</p>
      </div>

      <ol className="journey-steps">
        {STEPS.map((step, index) => (
          <li
            className={`journey-step tone-${index % 2 === 0 ? 'indigo' : 'teal'}`}
            key={step.number}
            style={{ animationDelay: `${index * 90}ms` }}
          >
            <span className="step-number" aria-hidden="true">{step.number}</span>
            <div className="step-body">
              <div className="step-title">
                <span className="step-icon" aria-hidden="true"><Icon name={step.icon} size={20} /></span>
                <h3>{step.title}</h3>
              </div>
              <p><strong>What you do:</strong> {step.action}</p>
              <p><strong>Why it helps:</strong> {step.why}</p>
              <Link href={step.path} className="step-link">Open this step <span aria-hidden="true">→</span></Link>
            </div>
          </li>
        ))}
      </ol>

      <div className="story-panel panel">
        <div>
          <p className="eyebrow">A real working rhythm</p>
          <h2>What this feels like day to day</h2>
          <p>
            Imagine you are hiring a senior engineer. On Monday you describe the role and the skills that matter.
            On Tuesday you drop in twenty resumes. On Wednesday you read the strongest six, each with the exact
            resume line that supports your rating. On Thursday you run interviews with prepared questions. By
            Friday you can see who is shortlisted, who needs another look and who has an offer — and you can
            explain every decision to your team.
          </p>
        </div>
        <div className="story-progress" aria-hidden="true">
          <span className="story-fill" />
          <span className="story-pin">Friday</span>
        </div>
      </div>

      <div className="section-heading">
        <h2>Good to know before you begin</h2>
      </div>
      <div className="tip-grid">
        <article className="tip-card tone-violet">
          <span className="tip-icon" aria-hidden="true"><Icon name="lock" size={18} /></span>
          <h3>Private by design</h3>
          <p>Each workspace is kept separate, so people in one organization never see another organization’s details.</p>
        </article>
        <article className="tip-card tone-amber">
          <span className="tip-icon" aria-hidden="true"><Icon name="computer" size={18} /></span>
          <h3>Stays on this computer</h3>
          <p>Everything you add is stored locally here. No outside service is needed to use the workspace.</p>
        </article>
        <article className="tip-card tone-cyan">
          <span className="tip-icon" aria-hidden="true"><Icon name="command" size={18} /></span>
          <h3>Move quickly</h3>
          <p>Press Ctrl+K or Command+K to jump straight to each screen without using the menu.</p>
        </article>
        <article className="tip-card tone-indigo">
          <span className="tip-icon" aria-hidden="true"><Icon name="shield" size={18} /></span>
          <h3>Choose your role</h3>
          <p>Use Sign in / switch user in the sidebar to pick a demo profile. Choose admin to see every insight.</p>
        </article>
      </div>

      <div className="guide-teaser guide-finish">
        <div>
          <p className="eyebrow">Ready when you are</p>
          <h2>Start with the role, then let the guide do the rest.</h2>
          <p className="muted">You can come back to this page whenever you like from the sidebar.</p>
        </div>
        <Link href="/jobs" className="btn-primary">Describe a role <span aria-hidden="true">→</span></Link>
      </div>

      <DeveloperMode {...DEVELOPER_RECIPES.guide} />
    </section>
  );
}
