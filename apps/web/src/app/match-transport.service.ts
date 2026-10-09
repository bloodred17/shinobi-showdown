import { Injectable, OnDestroy, signal } from '@angular/core';
import type { ClientMessage, ServerMessage } from '@shinobi-showdown/protocol';

export type ConnectionState =
  'disconnected' | 'connecting' | 'connected' | 'error';

@Injectable({ providedIn: 'root' })
export class MatchTransport implements OnDestroy {
  private socket: WebSocket | undefined;

  readonly state = signal<ConnectionState>('disconnected');
  readonly lastMessage = signal<ServerMessage | undefined>(undefined);

  connect(): void {
    if (
      this.socket?.readyState === WebSocket.CONNECTING ||
      this.socket?.readyState === WebSocket.OPEN
    ) {
      return;
    }

    this.state.set('connecting');
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(
      `${protocol}://${window.location.hostname}:3000/ws/dev/echo`,
    );
    this.socket = socket;

    socket.addEventListener('open', () => this.state.set('connected'));
    socket.addEventListener('message', ({ data }) => {
      if (typeof data !== 'string') {
        return;
      }

      try {
        this.lastMessage.set(JSON.parse(data) as ServerMessage);
      } catch {
        this.state.set('error');
      }
    });
    socket.addEventListener('error', () => this.state.set('error'));
    socket.addEventListener('close', () => {
      if (this.socket === socket) {
        this.state.set('disconnected');
        this.socket = undefined;
      }
    });
  }

  send(message: ClientMessage): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return false;
    }

    this.socket.send(JSON.stringify(message));
    return true;
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = undefined;
    this.state.set('disconnected');
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
