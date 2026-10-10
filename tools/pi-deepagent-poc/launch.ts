import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const profile = mkdtempSync(join(tmpdir(), 'shinobi-poc-pi-'));
const child = spawn(
  process.execPath,
  [
    join(
      root,
      'node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js',
    ),
    '--offline',
    '--approve',
    '--no-session',
    '--no-tools',
    '--no-extensions',
    '--no-skills',
    '--no-prompt-templates',
    '--no-context-files',
    '--no-themes',
    '-e',
    join(root, 'extension.ts'),
  ],
  {
    stdio: 'inherit',
    env: { ...process.env, PI_CODING_AGENT_DIR: profile, PI_TELEMETRY: '0' },
  },
);
child.on('error', () => {
  console.error(
    'Unable to launch local Pi. Run npm exec -- nx run pi-deepagent-poc:setup.',
  );
  process.exitCode = 1;
});
child.on('exit', (code) => {
  process.exitCode = code ?? 1;
});
process.on('SIGTERM', () => child.kill('SIGTERM'));
