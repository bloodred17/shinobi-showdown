import { PROTOCOL_VERSION, type ClientMessage } from './index';

describe('generated protocol boundary', () => {
  it('exposes a discriminated client message without authoritative state', () => {
    const message: ClientMessage = {
      type: 'tile_selected',
      coordinate: { x: 3, y: 5 },
    };

    expect(PROTOCOL_VERSION).toBe('0.1.0');
    expect(message).toEqual({
      type: 'tile_selected',
      coordinate: { x: 3, y: 5 },
    });
    expect(message).not.toHaveProperty('match_state');
  });
});
