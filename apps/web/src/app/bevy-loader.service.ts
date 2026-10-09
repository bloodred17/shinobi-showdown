import { Injectable, signal } from '@angular/core';

export type BattlefieldState = 'idle' | 'loading' | 'ready' | 'error';

interface BevyWasmModule {
  default: () => Promise<unknown>;
  start_game: () => void;
}

@Injectable({ providedIn: 'root' })
export class BevyLoader {
  readonly state = signal<BattlefieldState>('idle');
  private started = false;

  async start(): Promise<void> {
    if (this.started || this.state() === 'loading') {
      return;
    }

    this.state.set('loading');
    try {
      const moduleUrl = '/wasm/shinobi_game_client.js';
      const gameModule = (await import(
        /* @vite-ignore */ moduleUrl
      )) as BevyWasmModule;
      await gameModule.default();
      this.started = true;
      gameModule.start_game();
      this.state.set('ready');
    } catch (error) {
      console.error('Unable to start the Bevy battlefield', error);
      this.state.set('error');
    }
  }
}
