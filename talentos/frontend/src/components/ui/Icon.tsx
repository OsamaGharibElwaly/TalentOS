export type IconName =
  | 'home'
  | 'compass'
  | 'clipboard'
  | 'upload'
  | 'search'
  | 'chat'
  | 'spark'
  | 'chart'
  | 'lock'
  | 'computer'
  | 'command'
  | 'shield'
  | 'alert'
  | 'briefcase'
  | 'users'
  | 'trophy'
  | 'refresh';

const PATHS: Readonly<Record<IconName, readonly string[]>> = {
  home: ['M3 11.5 12 4l9 7.5', 'M5.5 10v10h13V10', 'M9.5 20v-6h5v6'],
  compass: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'm15.5 8.5-2 5-5 2 2-5 5-2Z'],
  clipboard: [
    'M9 4h6v3H9z',
    'M8 5.5H6.5A1.5 1.5 0 0 0 5 7v12.5A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V7a1.5 1.5 0 0 0-1.5-1.5H16',
    'M9 12h6',
    'M9 16h4',
  ],
  upload: ['M12 16V4', 'm7.5 8.5 4.5-4.5 4.5 4.5', 'M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3'],
  search: ['M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z', 'm16 16 4.5 4.5'],
  chat: ['M20 15a2 2 0 0 1-2 2H9l-5 4V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v9Z', 'M8 9h8', 'M8 12.5h5'],
  spark: ['m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z', 'M18.5 16.5 19 18l1.5.5L19 19l-.5 1.5L18 19l-1.5-.5L18 18l.5-1.5Z'],
  chart: ['M4 20V4', 'M4 20h16', 'M8 16v-4', 'M12.5 16V8', 'M17 16v-6'],
  lock: ['M6.5 10h11a1.5 1.5 0 0 1 1.5 1.5v8A1.5 1.5 0 0 1 17.5 21h-11A1.5 1.5 0 0 1 5 19.5v-8A1.5 1.5 0 0 1 6.5 10Z', 'M8.5 10V7a3.5 3.5 0 0 1 7 0v3'],
  computer: ['M4 5h16v11H4z', 'M2 19h20', 'M9 19l1-3', 'M14 16l1 3'],
  command: ['M9 7a2.5 2.5 0 1 0-2.5 2.5H9V7Z', 'M15 7a2.5 2.5 0 1 1 2.5 2.5H15V7Z', 'M9 17a2.5 2.5 0 1 1-2.5-2.5H9V17Z', 'M15 17a2.5 2.5 0 1 0 2.5-2.5H15V17Z', 'M9 9.5h6v5H9z'],
  shield: ['M12 3 5 6v5.5c0 4.4 2.9 8.2 7 9.5 4.1-1.3 7-5.1 7-9.5V6l-7-3Z', 'm9 12 2 2 4-4'],
  alert: ['M12 3 2.5 20h19L12 3Z', 'M12 9v5', 'M12 17h.01'],
  briefcase: ['M4 8h16v12H4z', 'M9 8V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V8', 'M4 13h16', 'M11 12h2'],
  users: ['M9 12a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z', 'M2.5 20c.5-3.6 3-5.5 6.5-5.5s6 1.9 6.5 5.5', 'M16 5.5a3.5 3.5 0 0 1 0 6.5', 'M17.5 14.7c2.5.5 4 2.3 4.5 5.3'],
  trophy: ['M8 4h8v5a4 4 0 0 1-8 0V4Z', 'M8 6H5v1a3 3 0 0 0 3 3', 'M16 6h3v1a3 3 0 0 1-3 3', 'M12 13v3', 'M9 20h6', 'M10 16h4v4h-4z'],
  refresh: ['M20 11a8 8 0 1 0-.8 4.5', 'M20 5v6h-6'],
};

export default function Icon({
  name,
  size = 20,
  className = '',
}: {
  name: IconName;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      className={`ui-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name].map((d) => <path key={d} d={d} />)}
    </svg>
  );
}
