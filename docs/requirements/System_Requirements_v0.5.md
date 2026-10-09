# Shinobi Tactics — System Requirements Specification (SRS)

**Version:** 0.5 · **Date:** 2026-10-10  
**Status:** Implementation baseline; decisions labeled CONFIRMED/PROPOSED/OPEN  
**Readers:** Rust backend engineer, Bevy engineer, Angular engineer, game systems designer, infrastructure engineer, security reviewer, QA lead  
**Companion:** `UI_UX_Requirements_v0.5.md`

> **Scope / rights:** This design is set in the Naruto universe and combines franchise characters with original shinobi. Production distribution of copyrighted character/art/mark assets is contingent on rights clearance. First prototype should use properly cleared or original placeholder assets and avoid assuming permission to publish Naruto IP.

## 1. Requirements conventions and product scope

- **CONFIRMED**: selected by product owner. **PROPOSED**: engineering default pending review. **OPEN**: unanswered; see Decisions/risks.
- **P0**: first online vertical slice. **P1**: near-term target. **P2**: future.
- The server is authoritative for rules and what each player is allowed to know. Bevy and Angular do not decide winners, damage, visibility, occupancy, initiative or hidden effects.
- This SRS specifies a source-of-truth _domain rule engine_ separate from the game renderer.

### 1.1 Confirmed facts

| Domain            | Requirement                                                                                           |
| ----------------- | ----------------------------------------------------------------------------------------------------- |
| Session           | Exactly two human participants, private room; no story mode                                           |
| Squad             | Each participant selects exactly three shinobi                                                        |
| Roster            | Naruto canon characters + predefined original shinobi + full original shinobi creator (can be phased) |
| Jutsu             | Fully configurable legal loadout constrained by chakra affinity; 12 JP/character                      |
| Equipment         | All items available to both players; 10 EP/character                                                  |
| Battle            | Isometric rendering over authoritative square logical grid with obstacles and cover                   |
| Turn system       | SPD order; each living character acts once per complete round                                         |
| Action economy    | One uninterrupted move and one main action in either order                                            |
| Attacks           | Basic attacks always hit when legally resolved; chosen jutsu may miss                                 |
| Visibility        | Entire terrain always visible; hidden enemies outside allied vision                                   |
| Targeting         | Valid ground-targeted blind attacks may select unseen tiles                                           |
| Intelligence      | When a unit is seen, identity and current position revealed, not stats/loadout                        |
| Reactions         | Only pre-armed techniques trigger automatically out of turn                                           |
| Chakra pulse      | At end of each third complete round; broad regions not exact positions                                |
| Pulse persistence | Timestamped latest pulse result remains on map until replaced by next pulse                           |
| Pulse evasion     | Some innate/passive, item-based, or actively activated skills                                         |
| Victory           | All opposing shinobi defeated                                                                         |

### 1.2 Deliberate non-goals for P0

Public matchmaking, ranking/rating, season passes, spectator mode, story campaign, chat, mobile input, monetization, blockchain, large inventory economy, real-time simultaneous action, physical campaign progression, network rollback, cross-match persistence beyond essential guest/session metadata, free camera rotation, 3D height/elevation, destructible terrain, large summoned-unit armies.

**P1, already in product direction:** full player-created shinobi workflow, saved build presets, expanded terrains, richer combat logs and custom appearance assets. Architect interfaces so these can be added without modifying core command semantics.

## 2. Technical stack and architectural boundaries

**Confirmed frontend stack:** Angular web app; Rust Bevy WASM game view; Rust backend.  
**PROPOSED backend/framework:** Axum + Tokio HTTP/WebSockets; HTTPS/WSS at edge; Rust shared domain crate; lightweight in-memory room/match registry for P0; optional PostgreSQL only when persistent user profiles and original characters/presets are required.

**Current ecosystem checks (2026-10-10):** Bevy 0.20 released 2026-10-08. Verify chosen plugins, shader and browser build features against 0.20 before pinning. WebGL2 is the baseline browser renderer for compatibility, WebGPU an optional improved path. Bevy's `Window` has web `canvas` and `fit_canvas_to_parent` options. Axum exposes WebSocketUpgrade under its `ws` feature. Angular supports signal-driven/zoneless application updates; keep high-frequency map rendering outside Angular templating.

### 2.1 Suggested architecture

```
Desktop browser
 ┌─────────────────────────────────────────────────────────────────────┐
 │ Angular SPA                                                         │
 │ Lobby / selection / loadouts / overlays / HUD / reconnect           │
 │   ┌─────────────────────┐    ┌───────────────────────────────────┐  │
 │   │ Typed UI state      │    │ Bevy WASM client                  │  │
 │   │ (player-visible)    │◄──►│ Scene / sprites / camera / input │  │
 │   └──────────┬──────────┘    └───────────────────────────────────┘  │
 │              │                                                       │
 │   Client transport: one WS per player; commands & projected events │
 └──────────────┼───────────────────────────────────────────────────────┘
                │ HTTPS / WSS
 ┌──────────────▼───────────────────────────────────────────────────────┐
 │ Rust Axum/Tokio service                                             │
 │ Room/lobby management │ session auth │ command admission           │
 │ Match actor/serialized engine │ state/events │ per-player projector │
 │   ┌─────────────────────────────────────────────────────────────┐   │
 │   │ Shared pure Rust rules (no Bevy dependency)                 │   │
 │   │ Grid/path/LOS │ turn/actions │ chakra/jutsu/reactions       │   │
 │   │ Damage/status │ visibility │ sensing │ rules validation     │   │
 │   └─────────────────────────────────────────────────────────────┘   │
 └──────────────────────────────────────────────────────────────────────┘
```

**SYS-ARCH-001 [P0]** Domain crate shall compile/test without any graphics, Angular, filesystem or network dependency.  
**SYS-ARCH-002 [P0]** Server holds authoritative match state, authoritative RNG/seed, initiative, all hidden information, legal action sets and result.  
**SYS-ARCH-003 [P0]** Angular and Bevy only consume permitted `PlayerView`/public-event projections; neither receives complete world state for convenience.  
**SYS-ARCH-004 [P0]** Exactly one client-side transport manager owns the live match WebSocket; no duplicate competing sockets from Angular and Bevy. Bevy client sends player intentions through an explicit interop bridge.  
**SYS-ARCH-005 [P0]** Client protocol schema is versioned; server may reject incompatible clients before match begins.  
**SYS-ARCH-006 [P0]** Each match processes mutations serially using an actor/task queue or equivalent per-match lock to prevent concurrent command races.  
**SYS-ARCH-007 [P0]** Content assets (units, jutsu, equipment, map definitions) use versioned data definitions validated at startup/build-time; battle logic must not be reimplemented in Angular.

### 2.2 Suggested repository

```
/apps/web/                     Angular SPA
/crates/game-domain/            Pure Rust deterministic domain rules
/crates/game-content/           Data schemas/validation for characters, jutsu, items, maps
/crates/game-server/            Axum HTTP/WS, sessions, room/match lifecycle
/crates/game-client/            Bevy scene/render/input/WebAssembly bridge
/packages/protocol/             Generated/maintained TypeScript client types
/content/                       Versioned gameplay JSON/RON/TOML or similar
/assets/                        Licensed/cleared art and sound
/tests/integration/             Two-client E2E, visibility and replay scenarios
/docs/                          ADRs, decisions, UXRS, SRS
```

## 3. Canonical domain model

| Entity                          | Core fields / invariants                                                                                                                            |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CharacterDefinition`           | unique id, source `canon/original`, display identity, base stats, CP, chakra affinity set, traits, permitted special techniques                     |
| `CharacterInstance`             | definition/custom id, owner player id, unit id, current stats/HP/CP, status effects, position, cooldowns, actions used, alive, armed reaction       |
| `OriginalCharacterProfile` [P1] | id, owning guest/account, appearance references, archetype, affinity, bounded points, traits, validation version                                    |
| `JutsuDefinition`               | id, JP cost, CP cost, affinities, optional trait/prereq, target shape, range, accuracy model, LOS rules, cooldown, effects, reaction trigger if any |
| `EquipmentDefinition`           | id, EP cost, slot, stat modifiers, granted effects or charges, public visuals, eligibility if needed                                                |
| `Loadout`                       | unit identity, equipment refs, jutsu refs, JP <=12, EP <=10, slot uniqueness, compatibility version                                                 |
| `MapDefinition`                 | width/height, tile coordinate system, terrain movement costs, obstacles, LOS blockers, cover, spawn zones, sensing sectors                          |
| `MatchState`                    | players/seats, match phase, round number, initiative, active unit, all unit states, RNG, map, observations, latest pulse snapshot                   |
| `PlayerKnowledge`               | discovered identities, exact visible units, last-seen unit records, observed attacks/effects, scanned disclosures, last pulse sectors               |
| `ArmedReaction`                 | owner unit, ability id, trigger specification, paid CP, expiry bound, optional prepared relocation/fallback                                         |
| `ActionCommand`                 | match/unit id, owner, command id, expected version, move/attack/jutsu/arm/end payload                                                               |
| `DomainEvent`                   | mutation result with visibility policy, event id, sequence, round/activation, facts allowed for different recipients                                |
| `PlayerView`                    | own complete team, authorized observed opposing facts, visible world, public terrain, allowed timeline info, latest permitted pulse                 |

**SYS-DATA-001 [P0]** Match content snapshots are pinned at match start, so catalogue edits cannot mutate in-progress battles.  
**SYS-DATA-002 [P0]** Every action produces a monotonic authoritative revision or rejects without state mutation.  
**SYS-DATA-003 [P0]** The server retains per-player discovery facts independently; a confirmed visible enemy may become invisible and retain a stale last-known marker without becoming a live tracking marker.  
**SYS-DATA-004 [P0]** All representations of tiles and positions use logical integer coordinates. Projection to pixels never appears in authoritative payloads.  
**SYS-DATA-005 [P0]** HP, CP, cooldowns, reveal tiers, and action availability are strongly typed; avoid free-form status strings inside the rule engine.

## 4. Battlefield geometry, pathfinding and visibility

### 4.1 Logical map

**SYS-MAP-001 [P0]** Square grid and isometric 2.5D presentation are separate concerns. Use unique tile coordinate `(x,y)` where `0 <= x < width` and `0 <= y < height`.  
**SYS-MAP-002 [P0]** Static entire terrain is public from match start, including impassable obstacles and cover, except explicitly concealed dynamic objects such as traps.  
**SYS-MAP-003 [P0]** Map must define passability, movement cost, LOS-blocking, attack-blocking and cover separately; an obstacle need not imply all four properties.  
**SYS-MAP-004 [P0]** Validate fixed spawn regions, exactly three legal spawn cells per team, no overlapping units, and fair obstacle distribution before a map enters rotation.  
**SYS-MAP-005 [P0]** Static collision and LOS queries work independent of graphics; no physics-engine requirement for grid combat.

**PROPOSED geometry for initial rules test:** 20×20, four-direction orthogonal movement, no diagonals or height, tile cost integer >=1, impassable obstacles never entered; A* or Dijkstra for weighted shortest path. `distance=|dx|+|dy|` is a practical baseline for nominal tile range; actual legal movement uses path cost not geometric distance. Rays through map blocking properties determine LOS independently of movement. Standardize ray corner/edge handling in test fixtures so clients cannot disagree.

**SYS-MOVE-001 [P0]** Active character can move at most once in a continuous path during its activation, no split movement. Move can occur before or after its one main action.  
**SYS-MOVE-002 [P0]** Server validates path continuity, cost <= effective MOV, impassability, occupancy and active actor ownership. If client submits just destination, server derives route using canonical deterministic tie-break. Prefer client submitting candidate path plus server full validation if path choice affects exposures or traps.  
**SYS-MOVE-003 [P0]** Move commits once; interrupted path uses the documented cost/refund policy. P0 proposed: movement spent even if interrupted and resolve only to last legal tile; interruption feedback must not reveal hidden blocker type.  
**SYS-MOVE-004 [P0]** Vision changes along the actual movement traversal, tile by tile; only allowed observed events disclosed. Whether discovery stops a movement should be recorded before design finalization (PROPOSED: does not stop unless path becomes illegal).  
**SYS-MOVE-005 [P0]** Hidden units never appear in client preview occupancy/invalidity results. Client-side prospective movement validation is based on public terrain and own visible units only.

### 4.2 LOS, vision, cover and target legality

**SYS-VIS-001 [P0]** Player optical vision is union of surviving ally units' LOS-limited vision and any special allied detection effects. Vision radius is derived from character+loadout+status; exact distance metric and blocker ray algorithm are consistent server-side.  
**SYS-VIS-002 [P0]** Full LOS blockers obstruct ordinary optical detection; partial cover affects defensive/attack resolution, not necessarily vision. Chakra sensing uses an independent ruleset and is not blocked simply by walls.  
**SYS-VIS-003 [P0]** Enemy unit identity and exact position become knowable while visually observed. Other private values (HP, CP, stats, jutsu, items, reaction state) are never released solely for visual observation.  
**SYS-VIS-004 [P0]** Last-seen observation includes old position + observation round, not updated unit state. At any time, own units are fully visible to owner.  
**SYS-VIS-005 [P0]** Damage events, animation, target preview, error response and pathfinding may not disclose hidden unit occupancy or private values unless the rule explicitly entitles observer to knowledge.  
**SYS-VIS-006 [P0]** Detection strength and suppression strength are explicit domains. A unit may evade chakra sensing without being optically invisible.

**PROPOSED cover rule:** Full obstacle blocks LOS and eligible projectiles. Half cover mitigates damage on valid guaranteed-hit basic attacks (never converts them into random misses) and may reduce accuracy for jutsu that have a miss model. Cover does not block the global sensing pulse. Whether cover is directional, destructible or occupies a tile vs tile edge remains OPEN; use simple per-tile static cover initially.

## 5. Match lifecycle and team preparation

**SYS-ROOM-001 [P0]** Private room has exactly two active seats, cryptographically random unguessable-enough code, bounded expiry, connection/ready states. Additional joins fail.  
**SYS-ROOM-002 [P0]** Each participant has a securely bound ephemeral guest session or scoped room seat identity. Unknown clients cannot impersonate seat or submit opponent actions.  
**SYS-ROOM-003 [P0]** Each team contains exactly three valid character instances and a valid loadout for each. Enemy selections remain secret until permitted discovery during the match.  
**SYS-ROOM-004 [P0]** Loadout constraint: `sum(equipment.ep) <= 10` and `sum(jutsu.jp) <= 12` independently per character, legal slot composition, prereqs including chakra affinity. No equipment unlock disparity.  
**SYS-ROOM-005 [P0]** Changing own roster/loadout before match locking resets own Ready state. When both valid and ready, atomically lock snapshots then create battle once.  
**SYS-ROOM-006 [P0]** Team selection and loadout payloads are delivered only to their owner, except server-known metadata permitted by UI (e.g., opponent READY).  
**SYS-ROOM-007 [P1]** Original character creator validates balanced points/traits, appearance metadata, compatible chakra affinities; immutable snapshot at match start. Full creator delivery can follow the initial online prototype.

**Match state machine:** `ROOM_OPEN -> PREPARING -> READY_LOCKED -> MATCH_LOADING -> IN_PROGRESS -> COMPLETED | ABANDONED`. Transitions are idempotent and version-checked. Reconnection preserves original seat identity, not permission to join as a new third player.

## 6. Turn engine, clock and victory

**SYS-TURN-001 [P0]** At each round start, build initiative list of all _living_ characters, each exactly once, sorted by effective SPD descending.  
**SYS-TURN-002 [P0]** Equal SPD uses stable seeded/publicly fair tie-break, not network arrival order. Do not expose hidden attributes via initial detailed initiative UI.  
**SYS-TURN-003 [P0]** Each actor has `movement_available=true`, `main_action_available=true` at its activation start, subject to statuses. They may consume either in either order. A consumed movement or action may not be restored within that activation except an explicitly modeled jutsu effect.  
**SYS-TURN-004 [P0]** A turn ends on explicit End Activation, exhaustion of actionable choices as applicable, server timeout if enabled, or incapacitation.  
**SYS-TURN-005 [P0]** Round completes after all its valid activations are processed or skipped due to defeat. Server runs end-of-round effects, then any scheduled pulse, then starts next round.  
**SYS-TURN-006 [P0]** SPD alterations during round affect the _next_ round's initiative ordering (PROPOSED freeze) to avoid queue mutation; confirm with product before balancing.  
**SYS-TURN-007 [P0]** Win condition: one side has zero living shinobi. Do not emit extra rounds/pulses after final win. Handle simultaneous knockout with defined tie rule (OPEN; PROPOSED draw).  
**SYS-TURN-008 [P0]** Match lifecycle handles disconnected/time-out actor without indefinite deadlock (policy OPEN; proposed resume window + eventual forfeiture).  
**SYS-TURN-009 [P0]** An explicit server-configurable anti-stall end condition must exist; proposed max 15 rounds and draw at cap until win/tie-break approved. Pulse-evasion cannot create limitless matches.

**PROPOSED clock:** 45 seconds/character activation; server-time authoritative; latency accommodation and timer UX tested under simulated 150 ms RTT. Do not ship final value without playtest sign-off.

## 7. Jutsu/equipment/chakra and combat resolution

**SYS-BUILD-001 [P0]** Equipment and jutsu definitions have separate EP/JP and independent in-match CP cost. All equipment definitions are equally selectable at preparation time by both players.  
**SYS-BUILD-002 [P0]** Character's chakra-affinity set gates eligible techniques. Other specialty prerequisites may be used for canon-exclusive or clan traits, but must be explicit and validated (avoid accidental universalization of signature abilities).  
**SYS-BUILD-003 [P0]** Class/role labels are descriptive; restrictions are defined per jutsu/trait/equipment, not implicitly derived from class name.  
**SYS-BUILD-004 [P0]** Equipped items and jutsu contribute to final effective stats deterministically; invalid build cannot be readied or instantiated.  
**SYS-BUILD-005 [P0]** Built-in basic attack is distinct from equipped jutsu; it requires no CP by default.  
**SYS-BUILD-006 [P0]** **PROPOSED slots:** weapon 1, armor 1, ninja tools 2, active jutsu 3, pre-armed reaction 1. All slot counts are configurable content rules until signed off.

**SYS-COMBAT-001 [P0]** Action validates phase, ownership, active unit, resources, range, targeting mode, LOS/obstruction, cooldown and one-main-action budget.  
**SYS-COMBAT-002 [P0]** Basic attack's hit roll is deterministic success when its target/action is legally valid. Damage can be zero due to damage reduction, immunity or armed reaction.  
**SYS-COMBAT-003 [P0]** A jutsu definition chooses its hit model (guaranteed tile effect / accuracy roll / per-unit effect); any randomness resolved on server using replayable seeded RNG.  
**SYS-COMBAT-004 [P0]** Ground-targeted blind attack may be issued at an unseen tile if valid by targeting/range/terrain. Hidden presence cannot be inferred from command-accept/reject or attack-preview differences.  
**SYS-COMBAT-005 [P0]** Attack commands consume CP/cooldown/action according to the jutsu definition, even if blind tile is empty; hits on concealed units need not reveal attacker-visible hit confirmation.  
**SYS-COMBAT-006 [P0]** Attack effects model physical/magical damage, AoE/line, healing, shields, status, displacement, detection and concealment as composable effect types.  
**SYS-COMBAT-007 [P0]** Determine source->target damage accounting STR/MAG and DEF/FOR. DEX/LCK impact on applicable special attacks/crit; MAS role is OPEN and should be inert or conservative until defined. Avoid inventing balance formulas as locked requirements.  
**SYS-COMBAT-008 [P0]** Line/area geometry, cover, friendly-fire eligibility, exact LOS requirement, visibility eligibility and effect disclosure live in data-driven ability definition, not frontend conditionals.  
**SYS-COMBAT-009 [P0]** Simultaneous-looking effects resolve in deterministic documented order; complete combat events have visibility filtering and redacted combat logs.

### 7.1 Defensive reactions

**SYS-REACT-001 [P0]** Only main-action _prepare/arm_ command can create a pending reaction; no manual input prompts mid-opponent activation.  
**SYS-REACT-002 [P0]** One armed reaction per unit (PROPOSED), costs deducted at arming (PROPOSED), expires on trigger or before next activation (PROPOSED).  
**SYS-REACT-003 [P0]** Eligible incoming event triggers deterministic reaction before corresponding damage/effects, using fully authoritative event data. Armed ability may negate/reduce, retaliate or relocate.  
**SYS-REACT-004 [P0]** Reaction cannot recursively trigger another reaction for P0. If teleport/substitution requires relocation, destination or fallback policy is selected when armed; legality rechecked when fired.  
**SYS-REACT-005 [P0]** Reaction effects and animations disclosed only to player views entitled to observe them. Reaction readiness on enemy never exposed merely because player sees unit.

**PROPOSED resolution order:** Validate action intent → charge cost/apply cooldown → resolve prearmed reactions where eligible → resolve main ability remaining effects → update HP/status/positions → recompute LOS/knowledge → evaluate victory → project per-player event(s). If effects span multiple tiles, define deterministic order and reaction trigger count in ability tests.

## 8. Chakra sensing, concealment and retained pulse history

**SYS-PULSE-001 [P0]** On completed rounds `round_number % 3 == 0`, after all end-of-round mutations and before next round, compute new global pulse. _An activation is not a round._  
**SYS-PULSE-002 [P0]** Each player's pulse detects opponent chakra sources only; it returns broad fixed `sector_id`s containing >=1 detectable source. Never exact tile, enemy id, health, count, equipment or precise signal centroid.  
**SYS-PULSE-003 [P0]** Pulse sector partitions are map data independent of enemy position. **PROPOSED** for 20×20: four fixed 10×10 quadrants (25% of total map each) for strong uncertainty; do not use centered circles or heatmaps with hidden source-derived intensity.  
**SYS-PULSE-004 [P0]** `latest_pulse` includes triggered round, sector IDs and version. It is retained as _historic snapshot_ until the next scheduled pulse atomically replaces it (including empty result). Moving units never update an old pulse zone.  
**SYS-PULSE-005 [P0]** Passive suppression trait, equipped consumable and active jutsu each may suppress ordinary global pulse contribution; optical visibility remains independent.  
**SYS-PULSE-006 [P0]** Detection power vs suppression power is deterministic and data-driven. Higher-tier specialized sensor abilities may defeat basic suppression; exact tiers are PROPOSED and must be balanced.  
**SYS-PULSE-007 [P0]** No pulse activity does **not** prove an area or match is empty, since chakra suppression exists; server/client messaging must preserve that semantics.  
**SYS-PULSE-008 [P0]** Sensing does not by itself mark a character's identity as discovered. A unit may appear directly from skill-specific detection only if that jutsu's disclosure contract permits it.

### Pulse example (no information leak)

- On round 3 completion, Player A's opponent has two unsuppressed units in NE and one suppressed unit in SW. Player A receives `['NE']`, with `round=3`; not `['NE','NE']` or exact unit positions.
- On rounds 4 and 5, those units move: the round-3 NE marker remains unchanged and timestamped.
- On round 6 completion, Player A receives a new sector set, replacing the round-3 record. If all surviving enemies are suppressed, result may be empty, with an explanation that no detectable signature was registered.

## 9. Network APIs and protocol contract

Use REST for room catalogue and room lifecycle; WebSocket for real-time lobby/match state. Exact URLs below are **PROPOSED** contracts to be finalized in an API spec. Avoid embedding credentials in long-lived query strings or logging secrets.

| Method/stream | Proposed endpoint/event      | Purpose                                                  |
| ------------- | ---------------------------- | -------------------------------------------------------- |
| GET           | `/api/v1/catalog`            | Versioned client-visible roster, jutsu and item metadata |
| POST          | `/api/v1/rooms`              | Create private room and bind seat 1 guest identity       |
| POST          | `/api/v1/rooms/{code}/join`  | Join seat 2, obtain session association                  |
| GET           | `/api/v1/rooms/{id}`         | Room status for authorized participant                   |
| POST          | `/api/v1/rooms/{id}/session` | Resume/refresh authorized guest connection if needed     |
| WS            | `/ws/v1/rooms/{id}`          | Room and battle commands, filtered snapshots/events      |

**PROPOSED client-to-server message shapes** (JSON for early debugging; compact binary can be adopted after profiling):

```json
{
  "type": "submit_team",
  "command_id": "c-101",
  "expected_revision": 8,
  "characters": [
    {
      "definition_id": "shinobi-a",
      "equipment_ids": ["kunai", "vest"],
      "jutsu_ids": ["fireball", "smoke", "sensor_scan", "substitution"]
    }
  ]
}
```

> In real validation the `characters` array above must include exactly **3**, not one; shortened to show one entry's structure.

```json
{
  "type": "act",
  "command_id": "c-220",
  "expected_revision": 34,
  "unit_id": "own-unit-1",
  "action": {
    "kind": "use_jutsu",
    "jutsu_id": "fireball",
    "target": { "kind": "tile", "x": 12, "y": 8 }
  }
}
```

```json
{
  "type": "act",
  "command_id": "c-221",
  "expected_revision": 35,
  "unit_id": "own-unit-1",
  "action": {
    "kind": "move",
    "path": [
      [4, 7],
      [5, 7],
      [6, 7]
    ]
  }
}
```

```json
{
  "type": "player_view",
  "revision": 37,
  "round": 3,
  "own_units": [
    { "unit_id": "own-unit-1", "hp": 80, "cp": 45, "x": 6, "y": 7 }
  ],
  "observed_enemies": [
    { "public_contact_id": "seen-9", "identity": "shinobi-b", "x": 12, "y": 8 }
  ],
  "last_seen": [],
  "latest_pulse": { "round": 3, "sector_ids": ["NE"] }
}
```

**Illustrative shape only:** formal contract needs discriminated unions, all required fields, coordinate bounds, data serialization and the authorization/disclosure table. In particular, `observed_enemies` must omit HP/CP/equipment/jutsu unless independently discovered. Public contact IDs must not allow tracking never-discovered units through hidden transitions.

**SYS-NET-001 [P0]** All incoming commands include authenticated player/session, match, idempotent command ID and expected revision; commands from the wrong actor are rejected.  
**SYS-NET-002 [P0]** Duplicate command ID returns same accepted/rejected result without double action spending, damage or CP deduction.  
**SYS-NET-003 [P0]** Server streams ordered versioned views/events; any revision gap requires fresh filtered snapshot, not full-world recovery.  
**SYS-NET-004 [P0]** Event publishing occurs only through per-player projection/redaction layer. Raw domain event with hidden position must not go to general browser event bus.  
**SYS-NET-005 [P0]** Handle socket close, network degradation, reconnection, heartbeat, and stale client re-sync gracefully.  
**SYS-NET-006 [P0]** Bounded message sizes, per-client buffers and command rates protect server from flooding; project events in batches if needed.  
**SYS-NET-007 [P0]** Disclosing a reason for a rejected action cannot leak concealed occupancy. Error codes are separated into public facts (no CP, invalid phase) vs private simulation details (generic action invalid/interrupted).  
**SYS-NET-008 [P0]** Match snapshots are player-scoped; current knowledge state can be regenerated deterministically from authoritative state plus recorded per-player observations.

## 10. Security, session and rights controls

**SYS-SEC-001 [P0]** HTTPS/WSS only outside local development. Validate WebSocket `Origin` and authorized room membership, not room code alone, for every connection and command.  
**SYS-SEC-002 [P0]** Treat room codes as discovery handles, not complete authentication; bind guest player identity securely (e.g. HttpOnly/Secure/SameSite cookie with server session, or comparably secure short-lived connection tickets). Apply rate limits and expiry.  
**SYS-SEC-003 [P0]** Never ship full authoritative opponent state, hidden unit references, private attack targets, undiscovered stats or unrevealed loadouts to client, even if visually hidden.  
**SYS-SEC-004 [P0]** Sensitive server/debug logs and client telemetry must redact guest tokens, secret content, unrevealed enemy state and full match hidden-event payloads.  
**SYS-SEC-005 [P0]** Validate all user input against schemas and content hashes; never trust client-calculated damage, resource costs, chance rolls, route legality, initiative or vision.  
**SYS-SEC-006 [P0]** Define policy for copyrighted Naruto character assets/content, permitted distribution and user-created uploads before public release. Do not mix externally sourced unlicensed art into distributable game bundles.

**Information-control threat tests:**

- Modified browser reads every WS frame and cached Angular/Bevy state; cannot locate a never-discovered enemy.
- Sequence of failed movement probes cannot cheaply reveal hidden enemy by distinct error text/rejection class (interruption under committed movement may provide _intended_ gameplay information; record exact rule).
- Invisible enemy taking damage from blind AoE yields no hit-indicator oracle.
- Previewing ability on a hidden tile shows the same preview whether enemy occupies it or not.
- Opponent roster and equipment absent from unready/ready lobby messages.
- Clock/initiative does not disclose hidden SPD or identity.

## 11. Performance, deployment and reliability targets

All metrics below are **PROPOSED acceptance targets**, to validate against real hardware/network; not user-confirmed SLAs.

| Area                 | Target                                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Browser              | Current Chrome, Edge and Firefox desktop on Windows/macOS/Linux; verify WebGL2 capability before launch                  |
| Rendering            | 60 FPS target at 1080p on chosen midrange reference desktop; functional at >=30 FPS during combat animations             |
| Input feedback       | Local hover/selection preview <100 ms p95 on target machine                                                              |
| Game command         | Server simulation/validation <50 ms p95 for a 20×20/6-unit match in test environment                                     |
| Command response     | Visible server acknowledgement generally <300 ms p95 with test RTT ~100 ms and healthy server; define under load testing |
| Reconnect            | Refresh into correctly filtered latest view without duplicated actions within permitted reconnect window                 |
| Loading              | Progressive asset loading and usable feedback; define byte budgets/first interactive target after wasm/art profiling     |
| Observability        | Match id, command id, revision, round, state transition, runtime timing, redacted errors                                 |
| Test reproducibility | Same content version + same command/event seed => identical authoritative simulation                                     |

**SYS-NFR-001 [P0]** Support server-side headless tests and a CLI replay runner for deterministic match simulations.  
**SYS-NFR-002 [P0]** Do not require a database in hot path for each activation; serialize match processing. P0 may use an in-memory registry with clear restart behavior; persistent reconnect beyond process restart is P1 unless deployment requirements dictate otherwise.  
**SYS-NFR-003 [P0]** Instrument WebSocket connection churn, per-match command latency, validation failures, visibility projection time, client frame rate/load errors, match completion rates; preserve private information.  
**SYS-NFR-004 [P0]** Assets may be fetched lazily; WASM/content bundling must be measured on target browser. Avoid heavyweight Bevy features not needed for a 2.5D square-grid game.  
**SYS-NFR-005 [P0]** Client supports GPU/backend fallback or explanatory unsupported state; do not assume WebGPU available to all browsers.

## 12. Testing and verification strategy

### 12.1 Unit and property-based tests — pure Rust domain

- Valid/invalid JP and EP budgets, affinity permissions, slot occupancy, custom character bounds.
- Grid edges, path costs, obstacles, LOS rays along all corner boundaries, movement allowed after attack but not split.
- Exactly one activation per living unit per round, stable SPD tie behavior, defeated units skipped.
- Basic guaranteed hit when legal, legal zero damage, dodge applies only to specified jutsu.
- Reaction arming, CP charge, expiry, triggers and no recursive reaction chains.
- Effect composition and simultaneous KO/tie rules.
- Round 3/6/9 pulse, fixed sectors, suppression and historical replacement.
- `PlayerView` noninterference: changing hidden enemy HP/loadout/position without changing observable public facts yields equivalent opponent-visible view (except when legitimate visible/pulse-sector changes occur).
- Determinism: seed + content snapshot + ordered accepted commands produces same result.

### 12.2 Integration tests — two clients and server

| ID    | Scenario                             | Expected result                                                        |
| ----- | ------------------------------------ | ---------------------------------------------------------------------- |
| T-001 | Third player tries to join full room | Rejected without room occupant disclosures                             |
| T-002 | Both players choose 3 and ready      | One authoritative match created; rosters private                       |
| T-003 | Action then move                     | Valid; another movement in same activation rejected                    |
| T-004 | Move then attack                     | Valid if both allowances remain                                        |
| T-005 | Hidden unit beyond allied LOS        | No client payload leaking unit position/HP or identity                 |
| T-006 | Enemy visually discovered            | Identity + exact visible position only                                 |
| T-007 | Blind AoE hits concealed enemy       | Defender state changes, attacker gets no unauthorized hit confirmation |
| T-008 | Round 3 pulse                        | Broad sector(s) only; no count, centroid or identity                   |
| T-009 | Round 4 movement                     | Round-3 pulse region unchanged and timestamped                         |
| T-010 | Round 6 new pulse                    | Previous active pulse region replaced, including empty case            |
| T-011 | Passive/item/jutsu suppression       | Correctly filtered sources; optical LOS independent                    |
| T-012 | Prepared substitution triggered      | Autoresolves without opponent-turn prompt; CP not paid twice           |
| T-013 | Duplicate action command             | No double move, CP charge or damage                                    |
| T-014 | Disconnect/reconnect                 | Seat restored, filtered snapshot, no stale/extra actions               |
| T-015 | Forged opponent unit id              | Rejected; not transformed into hidden occupancy oracle                 |
| T-016 | All three opponents defeated         | Match completed exactly once, correct winner                           |
| T-017 | Same seed/replay                     | Identical authoritative state and public event ordering                |
| T-018 | Client inspects cached state/WS      | No undiscovered enemy position, roster or loadout                      |

### 12.3 UI/UX end-to-end tests

Use desktop two-browser runs for viewport handling, ready changes, blocked/rejected actions, attack targeting, pulse overlays, keyboard focus, known/unknown information, animation disclosure, reconnection and results. See UXRS acceptance scenarios.

## 13. Delivery workstreams and acceptance gates

| Workstream   | Initial deliverables                                                                                            | Dependency                     |
| ------------ | --------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Game design  | Rule definitions, content schema, first six sample shinobi, 8–12 initial jutsu, equipment catalogue, sample map | Immediate                      |
| Backend Rust | Pure engine, rule fixtures, match actor, per-player projection, room management, WS transport                   | Rule baseline                  |
| Bevy client  | Embedded canvas proof, tile renderer, projection/picking, movement/jutsu overlays, sprite animations            | Map schema and bridge          |
| Angular team | Lobby, roster, loadout builder, HUD, error/reconnect UX, WS store                                               | API contract and design tokens |
| Art/design   | UI wireframes, semantic overlay system, original placeholder sprites/map assets, animation spec                 | UXRS                           |
| QA/security  | Deterministic fixture tests, two-browser E2E, redaction tests, latency/performance harness                      | Domain/protocol implementation |

### Recommended milestones (no calendar promise)

**M0: Stack / contracts spike.** Browser can host Bevy WASM in an Angular route and exchange typed messages. Headless Rust domain compiles/tests; exact browser/backend versions pinned after validation. **Gate:** build/CI, pointer picking, dev server and WS echo.

**M1: Offline battle simulation.** 20×20 placeholder grid; 3v3; initiative; pathfinding; one move+main; basic attack and at least one line/AoE jutsu. **Gate:** local match completes deterministically in headless tests and client.

**M2: Information warfare.** Per-player views, LOS, discovery, blind attacks, pulse every third round, retained coarse regions, concealment and armed reaction. **Gate:** adversarial no-information-leak test matrix passes.

**M3: Two-player end-to-end.** Room join, private roster, EP/JP builder, ready, authoritative WS command loop, reconnect, win/rematch. **Gate:** two remote browsers finish match with filtered state.

**M4: Character creation and polish.** Original shinobi creator, saved presets, anime asset pipeline, balance telemetry and accessibility polishing. **Gate:** profile and original-character rules validated with multiplayer compatibility.

### Definition of Done for first playable online slice

1. Two separate desktop browsers can join one private room, configure exactly three characters and lock valid EP/JP loadouts.
2. Server runs all six characters in correct SPD order; every surviving unit has one move and one main action each complete round; basic and selected jutsu resolve correctly.
3. Static map is visible, hidden enemy state stays off unauthorized clients, discovery shows identity only, and player can use legal blind-ground attacks.
4. Chakra pulse triggers after rounds 3/6 and returns broad fixed areas, replacing prior timestamped snapshot; suppression behaves as designed.
5. Armed defensive jutsu triggers without an out-of-turn input prompt.
6. Disconnect/rejoin, duplicate commands and illegal actions are handled without inconsistent or leaked state.
7. A match ends on elimination, and client receives appropriately redacted results and rematch/leave options.

## 14. Decisions still open — proposed defaults, not blockers for foundation

| ID     | Decision                                          | Risk if not settled                     | Interim proposal / gate                                      |
| ------ | ------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------ |
| DEC-01 | Map size/spawn geometry                           | Vision/duration balance                 | 20×20 mirrored/validated map                                 |
| DEC-02 | Diagonal movement/range metric                    | Path balance and UI overlays            | Four-way movement, Manhattan nominal range                   |
| DEC-03 | LOS corner/ray rules                              | Exploits and client/server disagreement | Single server canonical ray, exhaustive fixtures             |
| DEC-04 | Partial cover effect                              | Guaranteed-hit rule contradiction       | Damage reduction basic; accuracy penalty only missable jutsu |
| DEC-05 | Character / equipment / jutsu exact numbers       | Impossible to balance without fixtures  | Data-driven values with playtest baselines                   |
| DEC-06 | MAS and crit/dodge formulas                       | Stat irrelevance or dominance           | Conservative placeholder, no complex affinity multiplier     |
| DEC-07 | Jutsu slot count and signature traits             | Team-build UX changes                   | 3 active + 1 reaction; trait-gated signatures                |
| DEC-08 | Reaction resource/expiry/fallback                 | Unpredictable turn timing               | CP at arm, one active, expire before next activation         |
| DEC-09 | Friendly fire, AoE sequencing and terrain effects | Balance and information leakage         | Per ability, explicit resolution order                       |
| DEC-10 | Concealment power and counter-detection           | Endless stalling                        | Tiered deterministic sensing + end cap                       |
| DEC-11 | Character creator balancing                       | Overpowered custom shinobi              | Fixed archetype points/trait budget; ship after core match   |
| DEC-12 | SPD ties, freeze timing                           | Turn fairness                           | Seeded ties; rebuild each complete round                     |
| DEC-13 | Timeout/disconnect and cap outcome                | Match stalls, frustration               | 45 sec/activation, reconnect window, 15-round cap, draw      |
| DEC-14 | Deployment/spawn choice                           | Hidden roster advantage                 | Fixed mirrored starting placements for M1; deployment later  |
| DEC-15 | Hidden unit collision feedback                    | Information oracle                      | Movement consumed on interrupted traversal; generic event    |
| DEC-16 | Naruto licensing/public release                   | IP/distribution risk                    | Cleared assets for prototype, rights review before launch    |

## 15. Official technical references (verified 2026-10-10)

- [Bevy 0.20 release notes, October 8, 2026](https://bevy.org/news/bevy-0-20/)
- [Bevy web examples: WebGL2](https://bevy.org/examples/)
- [Bevy WebGPU examples and support limitations](https://bevy.org/examples-webgpu/)
- [Bevy Window documentation (HTML canvas selector, canvas sizing)](https://docs.rs/bevy/latest/bevy/window/struct.Window.html)
- [Axum WebSocketUpgrade](https://docs.rs/axum/latest/axum/extract/struct.WebSocketUpgrade.html)
- [Angular zoneless change detection](https://angular.dev/guide/zoneless)
- [MDN browser WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [W3C WCAG 2.2 focus visibility](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible)
