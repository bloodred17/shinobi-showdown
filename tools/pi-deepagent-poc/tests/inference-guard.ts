import { appendFileSync } from 'node:fs';
import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';

// Test-only provider: proves the selected Pi inference path fails on any call.
export default function guard(pi: ExtensionAPI) {
  const evidencePath = process.env.SHINOBI_POC_GUARD_LOG;
  if (!evidencePath)
    throw new Error('Set SHINOBI_POC_GUARD_LOG for the test guard.');
  const record = (event: unknown) =>
    appendFileSync(evidencePath, JSON.stringify(event) + '\n');
  let calls = 0;
  pi.registerProvider('poc-guard', {
    name: 'POC fail-on-call guard',
    baseUrl: 'http://127.0.0.1:1',
    apiKey: 'not-a-real-credential',
    api: 'openai-completions',
    models: [
      {
        id: 'fail-on-call',
        name: 'Fail on call',
        reasoning: false,
        input: ['text'],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 32768,
        maxTokens: 4096,
      },
    ],
    streamSimple: () => {
      calls++;
      record({ type: 'native_model_call', calls });
      throw new Error('POC_NATIVE_INFERENCE_CALLED');
    },
  });
  pi.on('session_start', () => {
    record({ type: 'ready' });
  });
  pi.on('input', (event) => {
    record({ type: 'input', source: event.source, query: event.text });
  });
  const captured = new Set<string>();
  pi.registerCommand('poc-snapshot', {
    description: 'Capture the public in-memory transcript for the TUI smoke',
    handler: async (_args, ctx) => {
      for (const entry of ctx.sessionManager.getEntries()) {
        if (entry.type === 'custom_message' && !captured.has(entry.id)) {
          captured.add(entry.id);
          record({ type: 'displayed', message: entry });
        }
      }
    },
  });
  pi.registerCommand('poc-proof', {
    description: 'Record the test-only native inference count',
    handler: async () => {
      record({ type: 'proof', calls });
    },
  });
  pi.on('session_shutdown', () => {
    record({ type: 'shutdown', calls });
  });
}
