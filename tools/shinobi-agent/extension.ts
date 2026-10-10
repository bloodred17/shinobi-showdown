import { randomUUID } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type {
  ExtensionAPI,
  ExtensionContext,
} from '@earendil-works/pi-coding-agent';
import {
  redact,
  runChild,
  type Request,
  type Result,
  type Session,
  type Run,
  type ExecutionSettings,
} from './bridge.ts';

const root = dirname(fileURLToPath(import.meta.url));

export function render(result: Result): string {
  if (result.sessions)
    return result.sessions.length
      ? result.sessions
          .map((s) => `${s.id} — ${s.repository} @ ${s.revision.slice(0, 12)}`)
          .join('\n')
      : 'No saved sessions. Use /shinobi-new <repository path>.';
  const session = result.session;
  if (!session) throw new Error('Runner result is missing its session.');
  const lines: string[] = [];
  if (result.outcome) {
    const o = result.outcome;
    lines.push(o.message);
    if (o.questions.length)
      lines.push('\nQuestions:', ...o.questions.map((q) => `- ${q}`));
    if (o.proposal) {
      const p = o.proposal;
      lines.push(
        `\nDraft proposal v${result.proposal_version}: ${p.objective}`,
        `Task type: ${p.task_type || 'unspecified'}`,
      );
      for (const [label, values] of [
        ['Constraints', p.constraints],
        ['Exclusions', p.exclusions],
        ['Approach', p.approach],
        ['Affected paths', p.affected_paths],
        ['Acceptance criteria', p.acceptance_criteria],
        ['Unresolved questions', p.unresolved_questions],
      ] as const)
        if (values.length)
          lines.push(`\n${label}:`, ...values.map((v) => `- ${v}`));
      lines.push(
        '\nDraft only. Use /shinobi-contract to review an executable contract before approval.',
      );
    }
    if (o.evidence.length)
      lines.push(
        '\nSource evidence:',
        ...o.evidence.map(
          (e) => `- ${e.path}:${e.start_line}-${e.end_line}: ${e.claim}`,
        ),
      );
  } else if (result.contract || result.run || 'run' in result) {
    if (result.contract) {
      const c = result.contract;
      lines.push(
        `Executable contract v${c.data.version}: ${c.data.proposal.objective}`,
        `Proposal: v${c.data.proposal_version}`,
        `Source commit: ${c.data.source_revision}`,
        `Model: ${c.data.model}`,
        `Policy: ${c.data.policy_version}`,
        `Playbook: ${c.data.workflow?.task_type || 'legacy'} (${c.data.workflow?.fingerprint || 'unbound'})`,
        `Environment: ${c.data.environment?.id || 'legacy'} (${c.data.environment?.fingerprint || 'unbound'})`,
      );
      for (const [label, values] of [
        ['Constraints', c.data.proposal.constraints],
        ['Exclusions', c.data.proposal.exclusions],
        ['Writable paths', c.data.proposal.affected_paths],
        ['Acceptance criteria', c.data.proposal.acceptance_criteria],
      ] as const)
        lines.push(`\n${label}:`, ...values.map((v) => `- ${v}`));
      lines.push(
        '\nRequired checks:',
        ...c.data.checks.map(
          (check) =>
            `- ${check.id}: ${JSON.stringify(check.argv)} (cwd ${check.cwd || '.'}, ${check.timeout_seconds || 60}s)`,
        ),
        '\nWork assignments:',
        ...c.data.work_items.map(
          (item) =>
            `- ${item.id}: ${item.instruction}; owns ${item.paths.join(', ')}; after ${(item.depends_on || []).join(', ') || 'none'}`,
        ),
        `\nLimits: ${JSON.stringify(c.data.limits)}`,
        `Protected verification inputs: ${Object.keys(c.data.protected_inputs || {}).join(', ') || 'inline checks or legacy contract'}`,
        `Role models: ${JSON.stringify(c.data.workflow?.models || { model: c.data.model })}`,
        `\nFull effective contract:\n${JSON.stringify(c.data, null, 2)}`,
        'Checks run offline with a read-only repository. User changes are excluded.',
        `\nApprove this exact contract: /shinobi-approve ${c.hash}`,
      );
    }
    if (result.run) {
      const r = result.run;
      lines.push(`\nRun: ${r.id}`, `State: ${r.status}`, r.message);
      if (r.failure_category)
        lines.push(`Failure category: ${r.failure_category}`);
      if (r.baseline_checks?.length)
        lines.push(
          ...r.baseline_checks.map(
            (check) =>
              `Baseline ${check.id}: ${check.outcome} (exit ${check.exit_code})`,
          ),
        );
      if (r.checks?.length)
        lines.push(
          ...r.checks.map(
            (c) =>
              `Check ${c.id}: ${c.outcome || 'recorded'}; exit ${c.exit_code}, expected ${c.expected_exit_code ?? 0} (${c.artifact_hash})`,
          ),
        );
      for (const report of r.diagnostic_reports || [])
        lines.push(
          `Diagnostic ${report.item}: ${report.summary}`,
          ...report.observations.map((value) => `Observation: ${value}`),
          ...report.limitations.map((value) => `Limit: ${value}`),
        );
      if (r.artifact)
        lines.push(
          `\nPatch: ${r.artifact.patch}`,
          `Branch: ${r.artifact.branch}`,
          `Workspace: ${r.artifact.workspace}`,
          `Result commit: ${r.artifact.result_revision}`,
          `Artifact: ${r.artifact.artifact_hash}`,
          `Disposition: ${r.artifact.disposition || 'legacy deliverable'}`,
          'Verified, user accepted, and applied are separate states.',
        );
    } else if ('run' in result) lines.push('No execution run in this session.');
  } else if (result.history) {
    lines.push('Resumed saved conversation. Recent turns:');
    for (const turn of result.history)
      lines.push(`\n[${turn.status}] ${turn.query}`, turn.response.message);
  } else lines.push('New read-only repository conversation.');
  lines.push(
    `\nSession: ${session.id}`,
    `Repository: ${session.repository}`,
    `Commit: ${session.revision}`,
    'Only the selected committed snapshot is visible. Working-tree changes are excluded.',
  );
  if (session.dirty_at_creation)
    lines.push(
      'Uncommitted changes were present when this session was created.',
    );
  if (session.excluded_count)
    lines.push(
      `${session.excluded_count} binary, oversized, symlink, or submodule entries excluded.`,
    );
  lines.push(`Request: ${result.request_id}`);
  return redact(lines.join('\n'));
}

export default function extension(pi: ExtensionAPI) {
  let session: Session | undefined;
  let busy = false;
  let closed = false;
  let controller: AbortController | undefined;
  let pending: Promise<void> | undefined;
  let activeRun: Run | undefined;
  let pollTimer: NodeJS.Timeout | undefined;
  let pollController: AbortController | undefined;
  let polling = false;
  let lastRunState = '';

  const display = (content: string, details: unknown = {}) =>
    pi.sendMessage(
      {
        customType: 'shinobi',
        content: redact(content),
        display: true,
        details,
      },
      { triggerTurn: false },
    );
  const error = (message: string, ctx: ExtensionContext) => {
    ctx.ui.notify(redact(message), 'error');
    display(`Shinobi error: ${message}`, { status: 'error' });
  };
  const call = (input: Omit<Request, 'version' | 'request_id'>) =>
    runChild(
      process.env.SHINOBI_PYTHON || join(root, '.venv/bin/python'),
      ['-u', join(root, 'runner.py')],
      { version: 1, request_id: randomUUID(), ...input },
      { cwd: root, signal: controller?.signal },
    );
  const stopPolling = () => {
    clearInterval(pollTimer);
    pollTimer = undefined;
    pollController?.abort();
  };
  const track = (result: Result) => {
    if (result.run) activeRun = result.run;
    if (
      !activeRun ||
      pollTimer ||
      [
        'verified',
        'failed',
        'blocked',
        'cancelled',
        'waiting_approval',
        'paused',
        'interrupted',
      ].includes(activeRun.status)
    )
      return;
    pollTimer = setInterval(() => {
      if (closed || polling || busy || !session || !activeRun) return;
      polling = true;
      const selected = session.id;
      pollController = new AbortController();
      void runChild(
        process.env.SHINOBI_PYTHON || join(root, '.venv/bin/python'),
        [join(root, 'runner.py')],
        {
          version: 1,
          request_id: randomUUID(),
          operation: 'status',
          session_id: selected,
          run_id: activeRun.id,
        },
        { cwd: root, signal: pollController.signal },
      )
        .then((result) => {
          if (closed || session?.id !== selected || !result.run) return;
          activeRun = result.run;
          const state = `${activeRun.status}:${activeRun.events?.at(-1)?.seq || 0}`;
          if (state !== lastRunState) {
            lastRunState = state;
            display(render({ ...result, contract: null }), { result });
          }
          if (
            [
              'verified',
              'failed',
              'blocked',
              'cancelled',
              'waiting_approval',
              'paused',
              'interrupted',
            ].includes(activeRun.status)
          )
            stopPolling();
        })
        .catch((error: Error) => {
          if (!closed && session?.id === selected)
            display(
              `Progress unavailable: ${error.message}. Use /shinobi-status.`,
              { status: 'error' },
            );
          stopPolling();
        })
        .finally(() => {
          polling = false;
        });
    }, 2000);
    pollTimer.unref();
  };
  const work = (ctx: ExtensionContext, fn: () => Promise<void>) => {
    if (closed) return;
    if (busy) {
      error('Busy: a request is already running.', ctx);
      return;
    }
    busy = true;
    controller = new AbortController();
    ctx.ui.setStatus('shinobi', 'Shinobi running…');
    pending = fn()
      .catch((e: Error) => {
        if (!closed) error(e.message, ctx);
      })
      .finally(() => {
        busy = false;
        controller = undefined;
        if (!closed) ctx.ui.setStatus('shinobi', undefined);
      });
    return pending;
  };
  const open = async (repository?: string) => {
    stopPolling();
    activeRun = undefined;
    const selected = repository || process.env.SHINOBI_REPOSITORY;
    if (!selected)
      throw new Error(
        'Select a repository with /shinobi-new <path> or SHINOBI_REPOSITORY.',
      );
    const result = await call({
      operation: 'create',
      repository: selected,
      revision: process.env.SHINOBI_REVISION || 'HEAD',
    });
    session = result.session;
    if (!closed) display(render(result), { result });
  };
  const resume = async (id: string) => {
    stopPolling();
    activeRun = undefined;
    const result = await call({ operation: 'resume', session_id: id });
    session = result.session;
    if (!closed) display(render(result), { result });
    const state = await call({ operation: 'status', session_id: id });
    if (state.run) {
      if (!closed) display(render(state), { result: state });
      track(state);
    }
  };
  pi.on('session_start', (event, ctx) => {
    if (['new', 'resume', 'fork'].includes(event.reason)) {
      session = undefined;
      activeRun = undefined;
      stopPolling();
    }
    const resumeId = process.env.SHINOBI_SESSION_ID;
    if (['startup', 'reload'].includes(event.reason) && resumeId)
      return work(ctx, () => resume(resumeId));
    ctx.ui.setStatus(
      'shinobi',
      'Read-only: /shinobi-new <repo> or /shinobi-resume <id>',
    );
  });
  const beforeSwitch = (_event: unknown, ctx: ExtensionContext) => {
    if (busy) {
      error('Wait for the active request before switching Pi sessions.', ctx);
      return { cancel: true };
    }
    return undefined;
  };
  pi.on('session_before_switch', beforeSwitch);
  pi.on('session_before_fork', beforeSwitch);
  pi.registerCommand('shinobi-new', {
    description: 'Start a read-only conversation at the selected commit',
    handler: async (args, ctx) => {
      await work(ctx, () => open(args.trim() || undefined));
    },
  });
  pi.registerCommand('shinobi-resume', {
    description: 'Resume a saved backend session by ID',
    handler: async (args, ctx) => {
      await work(ctx, () => resume(args.trim()));
    },
  });
  pi.registerCommand('shinobi-sessions', {
    description: 'List saved backend sessions',
    handler: async (_args, ctx) => {
      await work(ctx, async () => {
        const result = await call({ operation: 'list' });
        if (!closed) display(render(result), { result });
      });
    },
  });
  pi.registerCommand('shinobi-session', {
    description: 'Show the current session and recent turns',
    handler: async (_args, ctx) => {
      await work(ctx, async () => {
        if (!session)
          throw new Error(
            'No active session. Use /shinobi-new or /shinobi-resume.',
          );
        await resume(session.id);
      });
    },
  });
  for (const operation of [
    'contract',
    'approve',
    'status',
    'pause',
    'cancel',
    'continue',
    'steer',
    'recover',
  ] as const) {
    pi.registerCommand(`shinobi-${operation}`, {
      description: `${operation} the backend-owned contract or run`,
      handler: async (args, ctx) => {
        await work(ctx, async () => {
          if (!session)
            throw new Error(
              'No active session. Use /shinobi-new or /shinobi-resume.',
            );
          const input: Omit<Request, 'version' | 'request_id'> = {
            operation,
            session_id: session.id,
          };
          if (operation === 'approve') input.contract_hash = args.trim();
          else if (operation === 'contract' && args.trim())
            input.execution = JSON.parse(args) as ExecutionSettings;
          else if (operation === 'steer') input.query = args.trim();
          else if (activeRun) input.run_id = activeRun.id;
          const result = await call(input);
          if (!closed) {
            display(render(result), { result });
            track(result);
          }
        });
      },
    });
  }
  pi.on('input', (event, ctx) => {
    if (closed) return { action: 'handled' };
    if (!event.text.trim() || event.images?.length) {
      error(
        'Enter a non-empty text query; attachments are not supported.',
        ctx,
      );
      return { action: 'handled' };
    }
    void work(ctx, async () => {
      if (!session) await open();
      if (closed) return;
      const activeSession = session;
      if (!activeSession) throw new Error('No backend session was created.');
      pi.sendMessage(
        {
          customType: 'shinobi-query',
          content: event.text,
          display: true,
          details: { session_id: activeSession.id },
        },
        { triggerTurn: false },
      );
      const result = await call({
        operation: 'chat',
        session_id: activeSession.id,
        query: event.text,
      });
      session = result.session;
      if (!closed) display(render(result), { result });
    });
    return { action: 'handled' };
  });
  pi.on('session_shutdown', async () => {
    closed = true;
    stopPolling();
    controller?.abort();
    await pending;
  });
}
