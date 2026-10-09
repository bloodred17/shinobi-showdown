# Shinobi Tactics — Development Handoff v0.5

**Prepared:** 2026-10-10

This package contains two companion specifications:

1. `UI_UX_Requirements_v0.5.md` — UX requirements for Angular, game UX/art, and Bevy client engineers. Requirement prefix: `UX-`.
2. `System_Requirements_v0.5.md` — authoritative game rules, Rust/Bevy/Angular boundaries, multiplayer protocol, security, testing and delivery plan. Requirement prefixes: `SYS-`, `T-`, `DEC-`.

## Working agreement

- **CONFIRMED** requirements came from the user and should not be changed without product approval.
- **PROPOSED** defaults unblock the early skeleton but must be reviewed by game design before balance/content freeze.
- **OPEN** items belong in the decision register. Developers should not convert these to requirements silently.
- In any cross-document conflict: user-confirmed game decisions take precedence; SRS governs authoritative rules and permissible data disclosure; UXRS governs interaction and presentation. Record corrections in the versioned specification.

## First sprint boundary

Start with the technical spike and core rule engine, rather than the full Naruto roster or character creator. Validate Bevy WASM embedding in Angular, a local map with logical tile picking, headless Rust round/action execution, and two-player WebSocket connection. Freeze the protocol before parallelizing UI and backend implementation.

## Suggested team ownership

| Workstream              | Lead deliverable                                                                         |
| ----------------------- | ---------------------------------------------------------------------------------------- |
| Game design             | Map/range formulas, small balance fixtures, chakra/jutsu/equipment content definitions   |
| Rust game rules         | Pure deterministic grid + visibility + initiative + actions + reactions                  |
| Rust networking/backend | Private rooms, player sessions, serialized matches, filtered views/events                |
| Bevy WASM               | Isometric renderer, tile picking, camera, animations, targeting overlays                 |
| Angular                 | Menu/lobby, private roster, EP/JP builder, HUD, player information panels                |
| QA/security             | Deterministic tests, multi-browser gameplay, adversarial fog-of-war audits               |
| Art                     | Cleared prototype assets, isometric tile set, character sprites, semantic overlay design |

## Non-negotiable first integration test

Connect two independent browsers. Have both select private 3-person teams and start a match. Confirm the server serializes an attack on an unseen tile, resolves hidden damage, and sends _different redacted views_ to the two clients without leaking enemy coordinates/HP/roster. Then run round 3 and confirm that pulse produces coarse, position-independent sectors only.

## Rights and brand

This concept is expressly set in the Naruto universe. Before public distribution, verify rights to use canon Naruto characters, original anime-specific assets, names and brand imagery. Developing game mechanics with original placeholder art is a separate technical task and does not grant IP rights.
