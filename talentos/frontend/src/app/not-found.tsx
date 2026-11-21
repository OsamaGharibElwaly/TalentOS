import Link from 'next/link';
import BrandMark from '../components/ui/BrandMark';
import ErrorState from '../components/ui/ErrorState';
import Icon from '../components/ui/Icon';

export default function NotFound() {
  return (
    <section className="page-error not-found-page">
      <div className="not-found-card">
        <div className="brand"><BrandMark size={30} /> TalentOS</div>
        <ErrorState
          title="We could not find that page"
          message="This link may be out of date. Head back to your overview and pick up the hiring task where you left off."
        />
        <div className="not-found-links">
          <Link href="/guide" className="btn-ghost">
            <Icon name="compass" size={16} /> Open the getting-started guide
          </Link>
          <Link href="/login" className="btn-ghost">
            <Icon name="lock" size={16} /> Switch workspace or user
          </Link>
        </div>
      </div>
    </section>
  );
}
