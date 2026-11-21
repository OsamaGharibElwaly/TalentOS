export default function BrandMark({ size = 30 }: { size?: number }) {
  return (
    <span className="brand-mark" style={{ width: size, height: size }} aria-hidden="true">
      <svg viewBox="0 0 32 32" width="72%" height="72%" fill="none">
        <path d="M7.5 8.5h17v4.5h-6.2v11h-4.6V13H7.5V8.5Z" fill="currentColor" />
        <circle cx="24" cy="23" r="2.4" fill="#7ef0d0" />
      </svg>
    </span>
  );
}
