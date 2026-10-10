import { spawn } from 'node:child_process';

export const TIMEOUT_MS = 120_000;
export const MAX_REQUEST_BYTES = 64 * 1024;
export const MAX_STDOUT_BYTES = 256 * 1024;
export const MAX_STDERR_BYTES = 64 * 1024;

export interface Request {
  version: 1;
  request_id: string;
  operation:
    | 'create'
    | 'resume'
    | 'list'
    | 'chat'
    | 'contract'
    | 'approve'
    | 'status'
    | 'pause'
    | 'cancel'
    | 'continue'
    | 'steer'
    | 'recover';
  session_id?: string;
  repository?: string;
  revision?: string;
  query?: string;
  contract_hash?: string;
  run_id?: string;
  execution?: ExecutionSettings;
}

export interface ExecutionSettings {
  checks: {
    id: string;
    argv: string[];
    cwd?: string;
    timeout_seconds?: number;
    affected_items?: string[];
  }[];
  work_items: {
    id: string;
    instruction: string;
    paths: string[];
    depends_on?: string[];
  }[];
  limits?: {
    max_workers?: number;
    repair_cycles?: number;
    replans?: number;
    wall_seconds?: number;
    model_calls?: number;
    graph_steps?: number;
  };
}

export interface Contract {
  hash: string;
  data: ExecutionSettings & {
    version: number;
    proposal_version: number;
    source_revision: string;
    model: string;
    policy_version: string;
    proposal: Proposal;
  };
}

export interface Run {
  id: string;
  status: string;
  contract_hash: string;
  message: string;
  events?: { seq: number; kind: string }[];
  checks?: { id: string; exit_code: number; artifact_hash: string }[];
  artifact?: {
    workspace: string;
    branch: string;
    source_revision: string;
    result_revision: string;
    artifact_hash: string;
    patch: string;
    patch_sha256: string;
    evidence?: string;
  } | null;
}

export interface Proposal {
  objective: string;
  constraints: string[];
  exclusions: string[];
  approach: string[];
  affected_paths: string[];
  acceptance_criteria: string[];
  unresolved_questions: string[];
}
export interface Outcome {
  kind: 'answer' | 'needs_input' | 'proposal';
  message: string;
  questions: string[];
  evidence: {
    path: string;
    start_line: number;
    end_line: number;
    claim: string;
  }[];
  proposal: Proposal | null;
}
export interface Session {
  id: string;
  repository: string;
  revision: string;
  dirty_at_creation: boolean;
  proposal_version: number;
  excluded_count: number;
  turn_count: number;
}
export interface Result {
  version: 1;
  request_id: string;
  status: 'ok' | 'error';
  error?: string;
  session?: Session;
  sessions?: Pick<Session, 'id' | 'repository' | 'revision'>[];
  history?: { query: string; status: string; response: { message: string } }[];
  outcome?: Outcome;
  proposal_version?: number;
  model?: string;
  tool_calls?: { name: string; status: string }[];
  contract?: Contract | null;
  run?: Run | null;
  [key: string]: unknown;
}

export function redact(value: string): string {
  const key = process.env.OPENROUTER_API_KEY;
  return (key ? value.replaceAll(key, '[redacted]') : value)
    .replace(/\bsk-[A-Za-z0-9_-]+/g, '[redacted]')
    .replace(/Bearer\s+[^\s"']+/gi, 'Bearer [redacted]');
}

function parseResult(stdout: string, request: Request): Result {
  let value: unknown;
  try {
    value = JSON.parse(stdout);
  } catch {
    throw new Error('Runner returned malformed JSON or no result.');
  }
  if (!value || typeof value !== 'object' || Array.isArray(value))
    throw new Error('Invalid result object.');
  const result = value as Result;
  if (result.request_id !== request.request_id)
    throw new Error('Runner response request ID does not match.');
  if (result.version !== 1)
    throw new Error('Unsupported runner protocol version.');
  if (result.status === 'error' && typeof result.error === 'string')
    return result;
  if (result.status !== 'ok') throw new Error('Invalid result schema.');
  if (request.operation === 'list') {
    if (
      !Array.isArray(result.sessions) ||
      !result.sessions.every(
        (s) =>
          typeof s.id === 'string' &&
          typeof s.repository === 'string' &&
          typeof s.revision === 'string',
      )
    )
      throw new Error('Invalid session list.');
    return result;
  }
  const s = result.session;
  if (
    !s ||
    !/^[a-f0-9]{32}$/.test(s.id) ||
    typeof s.repository !== 'string' ||
    typeof s.revision !== 'string'
  )
    throw new Error('Invalid session schema.');
  if (request.session_id && s.id !== request.session_id)
    throw new Error('Runner session ID does not match.');
  if (result.contract) {
    const c = result.contract;
    if (
      !/^[a-f0-9]{64}$/.test(c.hash) ||
      !c.data ||
      !Number.isInteger(c.data.version) ||
      !Number.isInteger(c.data.proposal_version) ||
      !/^[a-f0-9]{40,64}$/.test(c.data.source_revision) ||
      typeof c.data.model !== 'string' ||
      typeof c.data.proposal?.objective !== 'string' ||
      !Array.isArray(c.data.checks) ||
      !Array.isArray(c.data.work_items)
    )
      throw new Error('Invalid contract schema.');
  }
  if (result.run) {
    const r = result.run;
    if (
      !/^[a-f0-9]{32}$/.test(r.id) ||
      !/^[a-f0-9]{64}$/.test(r.contract_hash) ||
      ![
        'queued',
        'running',
        'pausing',
        'paused',
        'cancelling',
        'cancelled',
        'interrupted',
        'waiting_approval',
        'failed',
        'verified',
      ].includes(r.status) ||
      typeof r.message !== 'string' ||
      (request.run_id && request.run_id !== r.id)
    )
      throw new Error('Invalid run schema.');
  }
  if (request.operation === 'contract' && !result.contract)
    throw new Error('Missing executable contract.');
  if (
    ['approve', 'pause', 'cancel', 'continue', 'steer', 'recover'].includes(
      request.operation,
    ) &&
    !result.run
  )
    throw new Error('Missing run result.');
  if (
    request.operation === 'status' &&
    (!('run' in result) || !('contract' in result))
  )
    throw new Error('Missing status result.');
  if (request.operation === 'chat') {
    const o = result.outcome;
    const strings = (x: unknown): x is string[] =>
      Array.isArray(x) && x.every((v) => typeof v === 'string');
    if (
      !o ||
      !['answer', 'needs_input', 'proposal'].includes(o.kind) ||
      typeof o.message !== 'string' ||
      !strings(o.questions) ||
      !Array.isArray(o.evidence)
    )
      throw new Error('Invalid outcome schema.');
    for (const e of o.evidence)
      if (
        !e ||
        typeof e.path !== 'string' ||
        typeof e.claim !== 'string' ||
        !Number.isInteger(e.start_line) ||
        !Number.isInteger(e.end_line) ||
        e.start_line < 1 ||
        e.end_line < e.start_line
      )
        throw new Error('Invalid citation schema.');
    if (o.kind === 'needs_input' && !o.questions.length)
      throw new Error('Missing clarification question.');
    if (o.kind === 'proposal') {
      const p = o.proposal;
      if (
        !p ||
        typeof p.objective !== 'string' ||
        ![
          'constraints',
          'exclusions',
          'approach',
          'affected_paths',
          'acceptance_criteria',
          'unresolved_questions',
        ].every((k) => strings(p[k as keyof Proposal])) ||
        !o.evidence.length ||
        !Number.isInteger(result.proposal_version)
      )
        throw new Error('Invalid proposal schema.');
    } else if (o.proposal !== null) throw new Error('Unexpected proposal.');
  }
  if (
    request.operation === 'resume' &&
    (!Array.isArray(result.history) ||
      !result.history.every(
        (t) =>
          typeof t.query === 'string' &&
          typeof t.status === 'string' &&
          typeof t.response?.message === 'string',
      ))
  )
    throw new Error('Invalid history schema.');
  return result;
}

export function runChild(
  executable: string,
  args: string[],
  request: Request,
  options: { signal?: AbortSignal; timeoutMs?: number; cwd?: string } = {},
): Promise<Result> {
  const encoded = JSON.stringify(request) + '\n';
  if (Buffer.byteLength(encoded) > MAX_REQUEST_BYTES) {
    return Promise.reject(new Error('Query exceeds the 64 KiB request limit.'));
  }
  if (options.signal?.aborted) {
    return Promise.reject(
      new Error(
        'Request cancelled; turn is not confirmed complete. Resume the session to inspect its status.',
      ),
    );
  }
  return new Promise((resolve, reject) => {
    const child = spawn(executable, args, {
      shell: false,
      cwd: options.cwd,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    let stdoutBytes = 0;
    let stderrBytes = 0;
    let stopped: Error | undefined;
    let killTimer: NodeJS.Timeout | undefined;

    const stop = (message: string) => {
      if (stopped) return;
      stopped = new Error(message);
      child.kill('SIGTERM');
      killTimer = setTimeout(() => child.kill('SIGKILL'), 1_000);
    };
    const cancel = () =>
      stop(
        'Request cancelled; turn is not confirmed complete. Resume the session to inspect its status.',
      );
    const timeout = setTimeout(
      () =>
        stop(
          'Runner timed out; turn is not confirmed complete. Resume the session to inspect its status.',
        ),
      options.timeoutMs ?? TIMEOUT_MS,
    );
    options.signal?.addEventListener('abort', cancel, { once: true });
    child.stdout.setEncoding('utf8');
    child.stderr.setEncoding('utf8');
    child.stdout.on('data', (chunk: string) => {
      stdoutBytes += Buffer.byteLength(chunk);
      if (stdoutBytes > MAX_STDOUT_BYTES) {
        stop('Runner exceeded the 256 KiB stdout limit.');
      } else {
        stdout += chunk;
      }
    });
    child.stderr.on('data', (chunk: string) => {
      stderrBytes += Buffer.byteLength(chunk);
      if (stderrBytes > MAX_STDERR_BYTES) {
        stop('Runner exceeded the 64 KiB stderr limit.');
      } else {
        stderr += chunk;
      }
    });
    child.on('error', () => {
      stopped = new Error('Unable to launch Python; check SHINOBI_PYTHON.');
    });
    child.stdin.on('error', () => {
      // close handles an early exit; do not leak an unhandled EPIPE.
    });
    child.on('close', (code) => {
      clearTimeout(timeout);
      clearTimeout(killTimer);
      options.signal?.removeEventListener('abort', cancel);
      if (stopped) {
        reject(stopped);
        return;
      }
      try {
        const result = parseResult(stdout, request);
        if (result.status === 'error') {
          if (code === 0)
            throw new Error('Runner error response had a zero exit code.');
          reject(
            new Error(redact(result.error ?? 'Runner returned an error.')),
          );
        } else if (code !== 0) {
          reject(
            new Error(
              `Runner exited with code ${code} after reporting success.`,
            ),
          );
        } else {
          resolve(result);
        }
      } catch (error) {
        const detail = stderr.trim() ? ` ${redact(stderr).slice(0, 512)}` : '';
        reject(new Error(`${(error as Error).message}${detail}`));
      }
    });
    child.stdin.end(encoded);
  });
}
