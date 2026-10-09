import { Component, HostListener, inject, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
import type { TileCoordinateDto } from '@shinobi-showdown/protocol';
import { BevyLoader } from './bevy-loader.service';
import { MatchTransport } from './match-transport.service';

@Component({
  imports: [RouterModule],
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly battlefield = inject(BevyLoader);
  protected readonly transport = inject(MatchTransport);
  protected readonly selectedTile = signal<TileCoordinateDto | undefined>(
    undefined,
  );

  @HostListener('window:shinobi:tile-selected', ['$event'])
  protected onTileSelected(event: Event): void {
    const coordinate = (event as CustomEvent<TileCoordinateDto>).detail;
    if (!coordinate) {
      return;
    }

    this.selectedTile.set(coordinate);
    this.transport.send({ type: 'tile_selected', coordinate });
  }

  protected pingServer(): void {
    this.transport.send({
      type: 'ping',
      request_id: crypto.randomUUID(),
    });
  }
}
