import assert from 'node:assert/strict';
import { join } from 'node:path';
import test from 'node:test';
import type {
  ExtensionAPI,
  ExtensionContext,
} from '@earendil-works/pi-coding-agent';
import { runChild, type Contract, type Request } from '../bridge.ts';
import extension, { render } from '../extension.ts';

const request: Request = {
  version: 1,
  request_id: 'test',
  operation: 'chat',
  session_id: 'a'.repeat(32),
  query: 'literal $(echo no) `test`\nline',
};
const session = {
  id: 'a'.repeat(32),
  repository: '/fixture',
  revision: 'b'.repeat(40),
  dirty_at_creation: true,
  excluded_count: 0,
  proposal_version: 0,
  turn_count: 0,
};
const success = {
  version: 1,
  status: 'ok',
  request_id: 'test',
  session,
  outcome: {
    kind: 'answer',
    message: 'hello',
    evidence: [],
    questions: [],
    proposal: null,
  },
};
const child = (value: unknown, code = 0) =>
  runChild(
    process.execPath,
    [
      '-e',
      `process.stdin.resume();process.stdin.on('end',()=>{console.log(${JSON.stringify(JSON.stringify(value))});process.exitCode=${code}})`,
    ],
    request,
  );

test('literal query crosses a real process boundary unchanged', async () => {
  const result = await runChild(
    join(process.cwd(), 'tests/fake-child.py'),
    [],
    request,
  );
  assert.equal(result.outcome?.message, request.query);
});
test('rejects mismatched sessions, malformed outcomes, protocol versions and inconsistent exit codes', async () => {
  await assert.rejects(
    child({ ...success, session: { ...session, id: 'c'.repeat(32) } }),
    /session ID/,
  );
  await assert.rejects(child({ ...success, version: 2 }), /protocol/);
  await assert.rejects(
    child({ ...success, outcome: { kind: 'invented' } }),
    /schema/,
  );
  await assert.rejects(child(success, 1), /after reporting success/);
  await assert.rejects(
    child({ version: 1, status: 'error', request_id: 'test', error: 'bad' }),
    /zero exit/,
  );
  await assert.rejects(
    child({ ...success, request_id: 'different' }),
    /request ID/,
  );
});
test('timeout stops an actual process and reports uncertain completion', async () => {
  await assert.rejects(
    runChild(process.execPath, ['-e', 'setInterval(()=>{},1000)'], request, {
      timeoutMs: 50,
    }),
    /not confirmed complete/,
  );
});
function mockPi() {
  const handlers = new Map<string, (...args: any[]) => any>();
  const commands = new Map<string, any>();
  const messages: any[] = [];
  const statuses: any[] = [];
  extension({
    on: (name: string, fn: any) => handlers.set(name, fn),
    registerCommand: (name: string, command: any) =>
      commands.set(name, command),
    sendMessage: (message: any, options: any) => {
      assert.equal(options.triggerTurn, false);
      messages.push(message);
    },
  } as unknown as ExtensionAPI);
  const ctx = {
    ui: {
      notify: () => undefined,
      setStatus: (_key: string, s: any) => statuses.push(s),
    },
  } as unknown as ExtensionContext;
  return { handlers, commands, messages, statuses, ctx };
}
async function idle(m: ReturnType<typeof mockPi>) {
  for (let i = 0; i < 200 && m.statuses.at(-1) !== undefined; i++)
    await new Promise((r) => setTimeout(r, 20));
  assert.equal(m.statuses.at(-1), undefined);
}
test('new/resume commands and follow-ups stay on the backend, with busy rejection and error recovery', async () => {
  process.env.SHINOBI_PYTHON = join(process.cwd(), 'tests/fake-child.py');
  try {
    const m = mockPi();
    await m.commands.get('shinobi-new').handler('/fixture', m.ctx);
    const input = m.handlers.get('input')!;
    assert.deepEqual(input({ text: 'SLOW' }, m.ctx), { action: 'handled' });
    input({ text: 'concurrent' }, m.ctx);
    assert.deepEqual(m.handlers.get('session_before_switch')!({}, m.ctx), {
      cancel: true,
    });
    await idle(m);
    assert(m.messages.some((x) => x.content.includes('Busy:')));
    input({ text: 'MALFORMED' }, m.ctx);
    await idle(m);
    assert(m.messages.some((x) => x.content.includes('malformed')));
    input({ text: 'follow-up' }, m.ctx);
    await idle(m);
    assert(
      m.messages.some(
        (x) => x.details?.result?.outcome?.message === 'follow-up',
      ),
    );
    await m.commands.get('shinobi-resume').handler('c'.repeat(32), m.ctx);
    input({ text: 'other session' }, m.ctx);
    await idle(m);
    assert.equal(m.messages.at(-1).details.result.session.id, 'c'.repeat(32));
    await m.commands.get('shinobi-sessions').handler('', m.ctx);
    assert(m.messages.at(-1).details.result.sessions);
    m.handlers.get('session_start')!({ reason: 'new' }, m.ctx);
    await m.commands.get('shinobi-session').handler('', m.ctx);
    assert(m.messages.at(-1).content.includes('No active session'));
  } finally {
    delete process.env.SHINOBI_PYTHON;
  }
});
test('shutdown stops the owned child and suppresses late output', async () => {
  process.env.SHINOBI_PYTHON = join(process.cwd(), 'tests/fake-child.py');
  try {
    const m = mockPi();
    await m.commands.get('shinobi-new').handler('/fixture', m.ctx);
    m.handlers.get('input')!({ text: 'HANG' }, m.ctx);
    const count = m.messages.length;
    await m.handlers.get('session_shutdown')!();
    assert.equal(m.messages.length, count);
  } finally {
    delete process.env.SHINOBI_PYTHON;
  }
});
test('draft proposal, citation and snapshot limitation are visible', () => {
  const text = render({
    version: 1,
    status: 'ok',
    request_id: 'test',
    session,
    proposal_version: 2,
    outcome: {
      kind: 'proposal',
      message: 'Change cap',
      questions: [],
      evidence: [
        { path: 'retry.py', start_line: 1, end_line: 2, claim: 'current cap' },
      ],
      proposal: {
        objective: 'New cap',
        constraints: ['Preserve API'],
        exclusions: [],
        approach: ['Update cap'],
        affected_paths: ['retry.py'],
        acceptance_criteria: ['Cap 20'],
        unresolved_questions: [],
      },
    },
  });
  assert.match(text, /Draft proposal v2/);
  assert.match(text, /retry.py:1-2/);
  assert.match(text, /Working-tree changes are excluded/);
  assert.match(text, /review an executable contract before approval/);
});

const boundContract: Contract = {
  hash: 'c'.repeat(64),
  data: {
    version: 1,
    schema_version: 2,
    proposal_version: 1,
    source_revision: 'b'.repeat(40),
    model: 'test/offline',
    policy_version: 'local-bwrap-v2',
    mode: 'implement',
    checks: [
      {
        id: 'behavior',
        argv: ['python3.12', '-m', 'unittest'],
        protected_paths: ['test_behavior.py'],
      },
    ],
    work_items: [
      { id: 'cap', instruction: 'Cap retries', paths: ['reconnect.py'] },
    ],
    proposal: {
      objective: 'Cap retries',
      constraints: [],
      exclusions: [],
      approach: ['Change cap'],
      affected_paths: ['reconnect.py'],
      acceptance_criteria: ['Cap 10'],
      unresolved_questions: [],
      task_type: 'bug_fix',
    },
    environment: {
      id: 'offline-linux-system-v2',
      fingerprint: 'd'.repeat(64),
      details: { network: 'none' },
    },
    workflow: {
      task_type: 'bug_fix',
      version: 1,
      fingerprint: 'e'.repeat(64),
      models: { reviewer: 'test/reviewer' },
      definition: { stages: ['reproduce', 'verify'] },
      guidance: [{ id: 'independent-assurance', text: 'Challenge evidence' }],
    },
    protected_inputs: { 'test_behavior.py': ['f'.repeat(64), false] },
  },
};

test('effective authority and protected inputs are visible before hash approval', () => {
  const text = render({
    version: 1,
    status: 'ok',
    request_id: 'test',
    session,
    contract: boundContract,
  });
  assert.match(text, /Full effective contract/);
  assert.match(text, /test_behavior.py/);
  assert.match(text, /test\/reviewer/);
  assert.match(text, /Challenge evidence/);
  assert.match(text, /offline-linux-system-v2/);
  assert.match(text, /shinobi-approve/);
});

test('transport rejects unknown or incomplete bound contracts and renders typed blockers', async () => {
  await assert.rejects(
    child({
      ...success,
      contract: {
        ...boundContract,
        data: { ...boundContract.data, schema_version: 99 },
      },
    }),
    /schema version/,
  );
  await assert.rejects(
    child({
      ...success,
      contract: {
        ...boundContract,
        data: { ...boundContract.data, environment: undefined },
      },
    }),
    /bound environment/,
  );
  const result = await child({
    ...success,
    run: {
      id: 'a'.repeat(32),
      contract_hash: 'c'.repeat(64),
      status: 'blocked',
      failure_category: 'environment',
      message: 'Missing dependency',
    },
  });
  assert.equal(result.run?.status, 'blocked');
  const text = render({ ...result, outcome: undefined });
  assert.match(text, /Failure category: environment/);
});
