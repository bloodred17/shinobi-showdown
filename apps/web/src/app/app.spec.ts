import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
    }).compileComponents();
  });

  it('renders the M0 architecture boundaries and canvas host', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('h1')?.textContent).toContain(
      'Shinobi Tactics',
    );
    expect(compiled.querySelector('#shinobi-game')).toBeInstanceOf(
      HTMLCanvasElement,
    );
    expect(compiled.textContent).toContain('Single transport');
  });
});
