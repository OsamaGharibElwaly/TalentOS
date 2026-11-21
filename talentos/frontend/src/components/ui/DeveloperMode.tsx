import Icon from './Icon';

export interface DeveloperStep {
  readonly method: 'GET' | 'POST' | 'VIEW';
  readonly path: string;
  readonly body?: object;
}

export interface DeveloperRecipe {
  readonly process: string;
  readonly steps: readonly DeveloperStep[];
}

export default function DeveloperMode({ process, steps }: DeveloperRecipe) {
  return (
    <details className="developer-mode">
      <summary>
        <Icon name="command" size={16} />
        Developer Mode
      </summary>
      <pre><code>{JSON.stringify({ process, steps }, null, 2)}</code></pre>
    </details>
  );
}
