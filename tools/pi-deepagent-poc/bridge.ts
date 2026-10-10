import { spawn } from 'node:child_process';

export const TIMEOUT_MS = 120_000;
export const MAX_REQUEST_BYTES = 64 * 1024;
export const MAX_STDOUT_BYTES = 256 * 1024;
export const MAX_STDERR_BYTES = 64 * 1024;

export interface Request {
  request_id: string;
  query: string;
}

export interface ToolCall {
  name: string;
  status: 'ok' | 'error' | 'pending';
  [key: string]: unknown;
}

export interface Result {
  request_id: string;
  status: 'ok' | 'error';
  answer?: string;
  error?: string;
  model?: string;
  workspace?: string;
  tool_calls?: ToolCall[];
  [key: string]: unknown;
}

export function redact(value: string): string {
  const key = process.env.OPENROUTER_API_KEY;
  return (key ? value.replaceAll(key, '[redacted]') : value)
    .replace(/\bsk-[A-Za-z0-9_-]+/g, '[redacted]')
    .replace(/Bearer\s+[^\s"']+/gi, 'Bearer [redacted]');
}

function parseResult(stdout: string, requestId: string): Result {
  let value: unknown;
  try {
    value = JSON.parse(stdout);
  } catch {
    throw new Error('Runner returned malformed JSON or no result.');
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Runner returned an invalid result object.');
  }
  const result = value as Result;
  if (result.request_id !== requestId) {
    throw new Error('Runner response request ID does not match.');
  }
  if (result.status === 'error' && typeof result.error === 'string') {
    return result;
  }
  if (
    result.status !== 'ok' ||
    typeof result.answer !== 'string' ||
    typeof result.model !== 'string' ||
    typeof result.workspace !== 'string' ||
    !Array.isArray(result.tool_calls) ||
    !result.tool_calls.every(
      (call) =>
        call &&
        typeof call.name === 'string' &&
        ['ok', 'error', 'pending'].includes(call.status),
    )
  ) {
    throw new Error('Runner returned an invalid result schema.');
  }
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
      new Error('Request cancelled; partial work is unverified.'),
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
    const cancel = () => stop('Request cancelled; partial work is unverified.');
    const timeout = setTimeout(
      () => stop('Runner timed out; partial scratch work is unverified.'),
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
      stopped = new Error('Unable to launch Python; check SHINOBI_POC_PYTHON.');
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
        const result = parseResult(stdout, request.request_id);
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
