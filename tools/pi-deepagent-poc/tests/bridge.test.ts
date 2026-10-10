import assert from 'node:assert/strict';
import { join } from 'node:path';
import test from 'node:test';
import type {
  ExtensionAPI,
  ExtensionContext,
} from '@earendil-works/pi-coding-agent';
import { runChild } from '../bridge.ts';
import extension from '../extension.ts';

const request = {
  request_id: 'test-001',
  query: 'literal $(touch /tmp/do-not-create) `echo no`\nquery',
};

const success = (id = request.request_id) => ({
  request_id: id,
  status: 'ok',
  answer: '42',
  model: 'fake-test-only',
  workspace: '/tmp/fake',
  tool_calls: [],
});

const child = (code: string, timeoutMs = 1000) =>
  runChild(process.execPath, ['--input-type=module', '-e', code], request, {
    timeoutMs,
  });

const reply = (value: unknown) =>
  `process.stdin.resume();process.stdin.on('end',()=>console.log(${JSON.stringify(JSON.stringify(value))}))`;

test('JSON carries shell syntax and newlines literally; valid result is decoded', async () => {
  const result = await child(
    `let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>{const r=JSON.parse(s);console.log(JSON.stringify({...${JSON.stringify(success())},answer:r.query}))})`,
  );
  assert.equal(result.answer, request.query);
});

test('launch failure, empty output, malformed JSON, ID mismatch, and inconsistent exit codes reject', async () => {
  await assert.rejects(
    runChild('/tmp/shinobi-poc-missing-python', [], request),
    /Unable to launch/,
  );
  await assert.rejects(child('process.stdin.resume()'), /no result/);
  await assert.rejects(child("console.log('not JSON')"), /malformed/);
  await assert.rejects(child(reply(success('different'))), /ID does not match/);
  await assert.rejects(
    child(`${reply(success())};process.exitCode=1`),
    /after reporting success/,
  );
  await assert.rejects(
    child(
      reply({
        request_id: request.request_id,
        status: 'error',
        error: 'failure',
      }),
    ),
    /zero exit code/,
  );
  await assert.rejects(
    child(
      reply({
        ...success(),
        tool_calls: [{ name: 'read_file', status: 'invented' }],
      }),
    ),
    /schema/,
  );
});

test('a controlled runner error is visible and API keys are redacted', async () => {
  const old = process.env.OPENROUTER_API_KEY;
  process.env.OPENROUTER_API_KEY = 'test-private-key';
  try {
    await assert.rejects(
      child(
        `console.log(${JSON.stringify(JSON.stringify({ request_id: request.request_id, status: 'error', error: 'provider test-private-key' }))});process.exitCode=1`,
      ),
      /provider \[redacted\]/,
    );
  } finally {
    if (old === undefined) delete process.env.OPENROUTER_API_KEY;
    else process.env.OPENROUTER_API_KEY = old;
  }
});

test('stdout/stderr and request size limits are enforced', async () => {
  await assert.rejects(
    child("process.stdout.write('x'.repeat(300000));setInterval(()=>{},1000)"),
    /stdout limit/,
  );
  await assert.rejects(
    child("process.stderr.write('x'.repeat(70000));setInterval(()=>{},1000)"),
    /stderr limit/,
  );
  await assert.rejects(
    runChild(process.execPath, [], { ...request, query: 'x'.repeat(70000) }),
    /request limit/,
  );
});

test('timeout and shutdown cancellation stop the actual child before resolving', async () => {
  await assert.rejects(child('setInterval(()=>{},1000)', 50), /timed out/);
  const controller = new AbortController();
  const pending = runChild(
    process.execPath,
    ['-e', 'setInterval(()=>{},1000)'],
    request,
    { signal: controller.signal },
  );
  controller.abort();
  await assert.rejects(pending, /cancelled/);
});

function mockPi() {
  const handlers = new Map<string, (...args: any[]) => any>();
  const messages: any[] = [];
  const status: (string | undefined)[] = [];
  const pi = {
    on: (name: string, fn: (...args: any[]) => any) => handlers.set(name, fn),
    sendMessage: (message: any, options: any) => {
      assert.equal(options.triggerTurn, false);
      messages.push(message);
    },
  } as unknown as ExtensionAPI;
  const ctx = {
    ui: {
      notify: () => undefined,
      setStatus: (_key: string, value: string | undefined) =>
        status.push(value),
    },
  } as unknown as ExtensionContext;
  extension(pi);
  return { handlers, messages, status, ctx };
}

async function complete(mock: ReturnType<typeof mockPi>) {
  for (let i = 0; i < 100 && mock.status.at(-1) !== undefined; i++) {
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  assert.equal(mock.status.at(-1), undefined, 'busy state must clear');
}

test('extension consumes input promptly, rejects a concurrent query, and shows the result', async () => {
  process.env.SHINOBI_POC_PYTHON = join(process.cwd(), 'tests/fake-python.py');
  try {
    const mock = mockPi();
    const input = mock.handlers.get('input')!;
    assert.deepEqual(
      input({ text: 'FAKE_SLOW', source: 'interactive' }, mock.ctx),
      { action: 'handled' },
    );
    assert.deepEqual(
      input({ text: 'second', source: 'interactive' }, mock.ctx),
      { action: 'handled' },
    );
    await complete(mock);
    assert.equal(
      mock.messages.filter((x) => x.customType === 'shinobi-poc-query').length,
      1,
    );
    assert(mock.messages.some((x) => x.content.includes('Busy:')));
    assert(mock.messages.some((x) => x.details?.result?.answer === '42'));
  } finally {
    delete process.env.SHINOBI_POC_PYTHON;
  }
});

test('extension recovers after malformed runner output and consumes empty/attachment input', async () => {
  process.env.SHINOBI_POC_PYTHON = join(process.cwd(), 'tests/fake-python.py');
  try {
    const mock = mockPi();
    const input = mock.handlers.get('input')!;
    assert.deepEqual(input({ text: '', source: 'interactive' }, mock.ctx), {
      action: 'handled',
    });
    assert.deepEqual(
      input({ text: 'image', images: [{}], source: 'interactive' }, mock.ctx),
      { action: 'handled' },
    );
    input({ text: 'FAKE_MALFORMED', source: 'interactive' }, mock.ctx);
    await complete(mock);
    assert(mock.messages.some((x) => x.content.includes('malformed JSON')));
    input({ text: 'next', source: 'interactive' }, mock.ctx);
    await complete(mock);
    assert(mock.messages.some((x) => x.details?.result?.answer === '42'));
    await mock.handlers.get('session_shutdown')!({}, mock.ctx);
  } finally {
    delete process.env.SHINOBI_POC_PYTHON;
  }
});

test('session shutdown cancels an active extension child and suppresses late messages', async () => {
  process.env.SHINOBI_POC_PYTHON = join(process.cwd(), 'tests/fake-python.py');
  try {
    const mock = mockPi();
    mock.handlers.get('input')!(
      { text: 'FAKE_HANG', source: 'interactive' },
      mock.ctx,
    );
    const count = mock.messages.length;
    await mock.handlers.get('session_shutdown')!({}, mock.ctx);
    assert.equal(mock.messages.length, count);
  } finally {
    delete process.env.SHINOBI_POC_PYTHON;
  }
});
