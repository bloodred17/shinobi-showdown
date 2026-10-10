import { randomUUID } from 'node:crypto';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import type {
  ExtensionAPI,
  ExtensionContext,
} from '@earendil-works/pi-coding-agent';
import { redact, runChild } from './bridge.ts';

const root = dirname(fileURLToPath(import.meta.url));

export default function extension(pi: ExtensionAPI) {
  let busy = false;
  let closed = false;
  let controller: AbortController | undefined;
  let pending: Promise<void> | undefined;

  const displayError = (message: string, ctx: ExtensionContext) => {
    ctx.ui.notify(redact(message), 'error');
    pi.sendMessage(
      {
        customType: 'shinobi-poc',
        content: `Deep Agent error: ${redact(message)}`,
        display: true,
        details: { status: 'error' },
      },
      { triggerTurn: false },
    );
  };

  pi.on('input', (event, ctx) => {
    if (closed) return { action: 'handled' };
    if (busy) {
      displayError(
        'Busy: one Deep Agent request is already running. Try again when it finishes.',
        ctx,
      );
      return { action: 'handled' };
    }
    if (!event.text.trim()) {
      displayError('Enter a non-empty text query.', ctx);
      return { action: 'handled' };
    }
    if (event.images?.length) {
      displayError('Attachments are unsupported by this text-only POC.', ctx);
      return { action: 'handled' };
    }

    busy = true;
    controller = new AbortController();
    const request = { request_id: randomUUID(), query: event.text };
    const python =
      process.env.SHINOBI_POC_PYTHON || join(root, '.venv', 'bin', 'python');
    ctx.ui.setStatus('shinobi-poc', 'Deep Agent running…');
    pi.sendMessage(
      {
        customType: 'shinobi-poc-query',
        content: event.text,
        display: true,
        details: request,
      },
      { triggerTurn: false },
    );

    pending = runChild(python, ['-u', join(root, 'runner.py')], request, {
      signal: controller.signal,
      cwd: root,
    })
      .then((result) => {
        if (closed) return;
        const tools =
          (result.tool_calls ?? [])
            .map((call) => `${call.name}: ${call.status}`)
            .join(', ') || 'none';
        pi.sendMessage(
          {
            customType: 'shinobi-poc',
            content: redact(
              `${result.answer}\n\nWorkspace: ${result.workspace}\nModel: ${result.model}\nTools: ${tools}\nRequest: ${result.request_id}`,
            ),
            display: true,
            details: { query: request.query, result },
          },
          { triggerTurn: false },
        );
      })
      .catch((error: Error) => {
        if (!closed) displayError(error.message, ctx);
      })
      .finally(() => {
        busy = false;
        controller = undefined;
        if (!closed) ctx.ui.setStatus('shinobi-poc', undefined);
      });

    // The child runs in the background. Returning immediately keeps input responsive.
    return { action: 'handled' };
  });

  pi.on('session_shutdown', async () => {
    closed = true;
    controller?.abort();
    await pending;
  });
}
