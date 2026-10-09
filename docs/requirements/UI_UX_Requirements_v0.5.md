# Shinobi Tactics — UI/UX Requirements Specification (UXRS)

**Version:** 0.5 · **Date:** 2026-10-10  
**Status:** Ready for design and prototype implementation; proposed defaults explicitly marked  
**Product:** Desktop-browser, 1v1, three-vs-three, turn-based tactical shinobi RPG set in the Naruto universe  
**Primary readers:** Product designer, UX designer, game UI artist, Angular developer, Bevy client developer, QA lead

> **Rights dependency:** Public use of Naruto characters, franchise visuals, names, and other protected elements needs appropriate authorization. Use licensed assets or properly segregated placeholder/original assets until distribution rights are established. This requirement does not block gameplay prototyping.

## 0. Requirement semantics and source of truth

- **CONFIRMED** = explicitly selected by the product owner in the design conversation.
- **PROPOSED** = implementation default recommended for a working vertical slice; change through a recorded decision, not silently.
- **OPEN** = deliberately unresolved; see Decision Register below.
- **P0** = required for first playable online match (unless marked P1 to designate a planned screen without blocking prototype).
- **P1** = target experience after vertical slice; architect for extensibility.
- **P2** = later polish/expansion.
- Requirement IDs remain stable through revisions. Acceptance criteria describe observable player-facing behavior.
- **SRS v0.5** is authoritative for game-state enforcement, validation and server-side information disclosure; this document is authoritative for presentation, interaction and feedback.

## 1. Product experience and design principles

**Experience promise:** Every match should reward team-building, positioning, chakra efficiency, deception, detection and correct jutsu timing—not merely raw damage.

**Player roles:** Player A and Player B are peers; neither can see the other's selected roster/loadout in preparation. There is no spectator, public matchmaking, story, campaign or mobile support in P0.

**UX principles:**

1. **Certainty is visible:** Distinguish confirmed enemy position, previous observation, coarse chakra activity, and unverified guesses using different shapes/patterns and text, never colors alone.
2. **Never reveal hidden state by accident:** Tooltips, hit previews, initiative, animation/audio cues, hover behavior, minimaps, network indicators and debug overlays must not disclose opponent-private information.
3. **Commitment is explicit:** Hover/selection previews are reversible; actual movement and attacks show a deliberate confirm/commit boundary, with optional one-click setting only later.
4. **The map owns the screen:** Strategic HUD occupies edges; nonessential panels collapse; attacks, targeting areas and obstacles remain legible when zoomed out.
5. **Character fantasy matters:** Anime/shinobi aesthetic, chakra, jutsu and ninja tools should be recognizable while respecting tactical clarity.
6. **Errors are actionable:** Explain constraints (too far, wrong affinity, not enough CP, reaction expired) without disclosing a concealed target.

## 2. Art, camera, viewport and responsive scope

**CONFIRMED:** square logical grid rendered in 2.5D/isometric perspective, visible terrain, obstacles, cover, 2D sprites with stylized low-poly influence, anime/Naruto aesthetic.  
**PROPOSED:** fixed diagonal isometric camera; pan + zoom, no camera rotation at first; terrain built using flat tile art or shallow 2.5D meshes; characters as directional sprite sheets, rendered on a fixed ground plane.

**Visual brief:** cel-shaded anime proportions, crisp silhouettes, hand-sign windups, substitution smoke, readable elemental effects, restrained ink/scroll accents. Team indicators must be distinct from chakra/elemental colors. Avoid pixel art and photorealistic 3D. Build visual language around visibility/detection, not generic black fog of war.

**Viewport targets (PROPOSED):** optimize for 1920×1080; fully usable at 1366×768, 1280×720 minimum; browser zoom 100–125%; gracefully show an unsupported-viewport explanation below that. Desktop keyboard/mouse only. HUD must not overlap board-critical hit areas or hide the active unit.

**UX-001 [P0]** Angular hosts a bounded, resize-aware Bevy canvas beneath/adjacent to HTML HUD; resizing cannot shift click-to-tile coordinate mapping.  
_Accept:_ at two viewport sizes, hovered logical tile agrees with the tile visually highlighted, including after zoom and browser resize.

**UX-002 [P0]** A loading view shows distinct progress/errors for webpage assets, WASM initialization, map/character assets and network connection.  
_Accept:_ recoverable errors offer Retry; unrecoverable browser/GPU issues show a supported-browser explanation.

**UX-003 [P0]** Full-screen 2.5D map remains legible at minimum supported viewport and lowest supported zoom.  
_Accept:_ allied units, obstacles, target highlights and confirmed vs uncertain intelligence stay distinguishable.

## 3. Information architecture

**Navigation:** Main Menu → Create/Join Lobby → Team Select → Loadout Configuration → Ready/Waiting → Battle Arena → Results → Rematch/Lobby.

**P0 screens:** Main Menu, Lobby, Character Selection, Jutsu & Equipment Builder, Battle Arena, Results.  
**P0 overlays:** Character Inspection, Jutsu Details, Combat Forecast, Intelligence / Pulse History, Settings/Pause, Connection/Reconnect, Surrender Confirmation.  
**P1 screens:** Saved Loadouts, Player-created Shinobi Creator, tutorial/practice interface. Character creator remains a confirmed target feature but must not block the P0 private-match vertical slice; P0 supports predefined original characters plus eventual canon slots.

| ID     | Screen               | Mandatory interaction                                                   | Evidence of completion                                              |
| ------ | -------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------- |
| UX-010 | Main menu            | Create Room, Join Room, Settings                                        | Opening a room or joining by code works with error feedback         |
| UX-011 | Lobby                | Room code/copy, both seats, connection/ready states                     | Both participants see consistent lobby state                        |
| UX-012 | Character selection  | Choose exactly 3 distinct selectable squad slots                        | Cannot confirm an invalid team; opponent roster never rendered      |
| UX-013 | Loadout builder      | Equip items, assign jutsu, see 10 EP / 12 JP and chakra-affinity checks | Invalid build cannot be marked ready, clear reasons shown           |
| UX-014 | Ready/wait           | Ready and Unready before lock, both player statuses                     | Both ready causes server transition; no secret roster leakage       |
| UX-015 | Battle               | Tactical board, timeline, statuses, attack/move/jutsu/finish            | Full legal activation possible by mouse and keyboard                |
| UX-016 | Results              | Winner, own team stats, rematch and leave                               | Completed match never shows unearned hidden intelligence by default |
| UX-017 | Shinobi creator [P1] | Appearance, innate trait, affinities, stat allocation                   | Server-validated original unit can participate in private match     |

### 3.1 Main Menu and Room UX

**UX-020 [P0]** Main Menu presents _Create Room_, _Join Room_, _Settings_. Public matchmaking, rankings, chat and story buttons are not shown as functional affordances.  
**UX-021 [P0]** Create Room creates one private two-seat session and shows short shareable code; players may copy it and manually share.  
**UX-022 [P0]** Join Room accepts code, validates format, handles invalid/full/expired rooms without revealing participants or private details.  
**UX-023 [P0]** Lobby shows Player 1/2 connection and readiness, without selected heroes, equipment, affinities, or loadouts of the opponent. Own selected team may appear in own panel.  
**UX-024 [P0]** Ready button is disabled until exactly three eligible units and all three valid builds are selected. Editing any build automatically clears own Ready state.  
**UX-025 [P0]** When both are ready, show the same countdown/loading state; server owns transition and starts match once, idempotently. If readiness is revoked before lock, do not start.

### 3.2 Character Selection

**UX-030 [P0]** Roster cards: recognizable portrait/silhouette, name, category (_canon_ or _original_), role and chakra affinity; these are known for own selectable units only.  
**UX-031 [P0]** Selecting a card displays own character details: HP, STR, MAG, DEF, FOR, DEX, MAS, SPD, LCK, MOV, derived Vision, CP, traits and legal jutsu families.  
**UX-032 [P0]** Squad occupies three slots, independently editable; selected build persists while navigating preparation; reusing the same character identity in two squad slots is **PROPOSED disallowed** (OPEN for product owner).  
**UX-033 [P0]** Composition labels are advisory, not hard restrictions (e.g. Sensor/Support or Burst/Stealth).  
**UX-034 [P1]** Original-shinobi creator includes appearance, base archetype, limited innate traits, affinities and stat allocation, with balance validation and preview. Canon-specific protected assets must remain isolated from original-character creation.

### 3.3 Equipment and Jutsu Loadout Builder

**CONFIRMED:** all equipment available; 10 Equipment Points (EP) per character; jutsu freely selected subject to chakra affinity, with separate 12 Jutsu Points (JP) per character. No investment/progression gate.

**PROPOSED slots:** weapon 1, armor 1, ninja tools 2; basic attack separate, three active jutsu slots and one pre-armed reaction slot. Slot counts are implementation defaults, not confirmed. JP costs and equipment effects belong to server content data.

**UX-040 [P0]** Visibly separate EP used/available from JP used/available and battle CP (chakra). Never merge these concepts.  
**UX-041 [P0]** Item/jutsu catalogue supports search/filter by affinity, discipline, cost, damage/effect, targeting, cooldown and reaction type.  
**UX-042 [P0]** Invalid jutsu remains discoverable with a clear eligibility explanation (missing Fire affinity, missing trait, insufficient JP, wrong slot).  
**UX-043 [P0]** Equipment selection previews deltas (e.g., DEF +3, MOV −1), resulting attributes and current budget before commit.  
**UX-044 [P0]** Each jutsu card displays range, targeting shape, CP cost, cooldown, hit behavior, visibility requirement, and friendly-fire behavior when relevant.  
**UX-045 [P0]** Reaction jutsu card describes arming cost, trigger, auto-resolution, timeout/expiry and any selected escape location or policy.  
**UX-046 [P0]** Build validation runs locally for immediate feedback and authoritatively on server before ready; server rejection names own invalid item but never enemy information.  
**UX-047 [P1]** Save/load presets with versioning; gracefully invalidate presets when catalogue/balance changes.

## 4. Isometric battlefield and movement UX

**CONFIRMED geometry:** authoritative logical coordinates `(x, y)` on square grid, projected isometrically; terrain always visible, with obstacles and cover; enemy units hidden outside allied visibility.

**PROPOSED P0 map:** 20×20 logical tiles; four-way orthogonal tile adjacency; integer movement-cost budget; no elevation or destructibility at first; two symmetrical deployment zones separated by blockers. Isometric projection MUST NOT change the movement graph. A 20×20 map is a balance hypothesis, not approved map size.

**Tile presentation layers (back-to-front):** terrain → blocking/cover geometry → permissible public terrain indicators → own vision tint → movement/path overlay → range/AoE/trajectory overlay → unit sprites and selection indicators → player-visible combat effects → tooltips. Always resolve visual layering and input priority explicitly; do not render enemy-private overlays.

**UX-050 [P0]** Hover tile shows terrain and logical coordinate (if enabled), public cover state, movement-cost/obstruction only from known terrain; never shows invisible unit occupancy.  
**UX-051 [P0]** Selected active unit displays one movement range overlay derived from path cost; hover candidate shows path and destination and whether the character still has its single movement allowance.  
**UX-052 [P0]** Clicking destination previews then commits the move; completed movement cannot be split or resumed within that activation. Main action may precede or follow the move.  
**UX-053 [P0]** Tile occupation/obstruction discovered during movement is resolved authoritatively; client must not use path-preview failures as a hidden-unit radar. If server interrupts movement, show neutral feedback (e.g. _Movement interrupted_) without revealing unauthorized details.  
**UX-054 [P0]** Camera supports wheel zoom, middle-drag pan, focus active unit, and no free rotation. Camera cannot scroll map off-screen irrecoverably.  
**UX-055 [P0]** Obstacles/cover have readable silhouettes and optional inspectable icons. Full block vs partial cover needs visibly different treatment.  
**UX-056 [P0]** Terrain can be covered by UI only where interaction/selection isn't required; panels collapse on small supported viewports.  
**UX-057 [P0]** On character activation, focus/outline updates, move/main-action availability resets, and timeline highlights current actor. Hidden enemy identity is replaced with a generic unknown turn indicator.

## 5. Battlefield HUD / navigation

**Proposed desktop HUD layout:**

```
┌ Round / pulse countdown ───── Initiative slots (filtered) ─── Timer / menu ┐
│                                                                            │
│                         BEVY ISOMETRIC MAP                                 │
│             Tile hover + path + attacks + observed units                   │
│                                                                            │
│ Own 3-unit status panel                Contextual inspect/intelligence      │
├ Active unit: portrait · HP · CP · Move used? · Action used? · Reaction ─────┤
│ Basic | Jutsu 1 | Jutsu 2 | Jutsu 3 | Arm Reaction | Move | End Activation  │
└────────────────────────────────────────────────────────────────────────────┘
```

**UX-060 [P0]** Own active unit panel shows HP/CP exact values, derived vision, MOV, action availability, status effects and cooldowns.  
**UX-061 [P0]** Own team panel shows three HP/status summaries and permits inspecting allies, but does not change active actor.  
**UX-062 [P0]** Enemy inspection shows exact identity and last-known sighting once discovered; never auto-exposes HP, CP, loadouts or numeric stats. Separately earned intelligence reveals only authorized fields.  
**UX-063 [P0]** Initiative timeline shows own relevant order and publicly known information; never reveals never-discovered enemy identities, stats or concealed presence locations.  
**UX-064 [P0]** Action bar includes basic attack, configured jutsu, reaction preparation, movement and End Activation; disabled reason appears on focus/hover.  
**UX-065 [P0]** Combat forecast reflects public/known calculations and avoids hidden-target oracle behavior. Unknown tile targeting shows range/area/resource effects without secret target HP, cover modifiers or hit confirmation.  
**UX-066 [P0]** End Activation needs confirmation if both movement and main action remain unused; after user accepts it can be immediate in later settings.  
**UX-067 [P1]** Expandable observed-combat log uses _Observed_, _Previously Observed_ and _Inferred_ qualifiers and does not reveal hidden action metadata.

## 6. Vision, discovery and intelligence UI

**CONFIRMED:** terrain visible from outset; opponent units are hidden beyond combined friendly vision. Discovering an enemy reveals **identity and current location**, but NOT HP/CP/stats/equipment/jutsu. Combat observations and specialized techniques can disclose additional allowed facts. Last-known location is not a live position.

**UX-070 [P0]** Ally vision overlay has a toggle and is distinct from movement or attack highlights. Visibility follows the union of three surviving allied units' visibility and defined sensory effects.  
**UX-071 [P0]** Entering vision: render detected enemy identity and accurate current tile. Leaving vision: remove live sprite/marker and optionally show timestamped last-known location with a _last seen round_ label.  
**UX-072 [P0]** Enemy health bars, numeric damage forecast modifiers, active reaction statuses and equipment remain hidden until explicitly learned.  
**UX-073 [P0]** Blind-ground attacks permit targeting valid terrain tiles even when no unit is visible. UI cannot indicate whether a concealed enemy occupies the tile.  
**UX-074 [P0]** A blind attack that strikes a hidden unit cannot automatically produce attacker-visible damage popup, vibration, special sound, combat-log confirmation or non-generic error. Defender may receive valid local damage feedback.  
**UX-075 [P0]** Observation and sensory indicators must convey confidence levels: `VISIBLE_EXACT`, `LAST_KNOWN`, `PULSE_REGION`, `UNCONFIRMED`. Do not color-code alone.  
**UX-076 [P0]** Intelligence panel shows discoveries, last sightings and currently retained pulse regions, with timestamps and expiry. It cannot display previously replaced pulse regions as live data.

## 7. Periodic chakra-pulse UX

**CONFIRMED:** global pulse happens **after every third complete round** (rounds 3, 6, 9...). It shows **broad regions**, not precise tiles or unit counts; it remains as **timestamped history until replaced by the next pulse**. Enemy pulse-avoidance can be passive, equipment-based or skill-based.

**PROPOSED sector map for 20×20 arena:** static quadrants of approximately 10×10 tiles; the display identifies zero or more sectors containing at least one unsuppressed opponent at the pulse snapshot, not the source location or count. Do not center a marker on actual enemy coordinates; no gradients whose center is derived from enemy position. Visible friendly positions are not pulse 'enemy' readings.

**UX-080 [P0]** Countdown says `Next chakra pulse after Round N` or `Pulse in X completed rounds`; never counts individual activations.  
**UX-081 [P0]** After triggering round ends, receive server-supplied pulse sector IDs, display broad shaded regions and `Detected during Round N` information. No enemy identity, quantity, location or per-unit marker.  
**UX-082 [P0]** Pulse regions remain until the following scheduled pulse replaces them, whether or not the next pulse returns any detected sectors. On replacement, remove or archive old regions outside the live map; no accumulation.  
**UX-083 [P0]** Friendly concealment UI shows whether own character currently suppresses **chakra sensing**, clearly separate from optical visibility and terrain cover.  
**UX-084 [P0]** A pulse with no reported activity must NOT be described as confirmation that the opposing team is absent: concealed shinobi may exist.  
**UX-085 [P1]** Optional pulse history can be viewed in event log but older results must remain clearly expired and non-interactive in the battlefield.

## 8. Attacks, chakra, jutsu, reactions

**CONFIRMED:** one uninterrupted move + one main action in either order. Basic attacks hit if legally valid; some jutsu may miss. Blind targeting can be legal. Pre-armed defensive jutsu may trigger automatically outside turns; reactive manual player prompts during opponent turn are excluded.

**UX-090 [P0]** Basic attack targeting distinguishes a _legal target_ from _guaranteed nonzero damage_. Shield, reduction, immunity and substitution may alter resolution.  
**UX-091 [P0]** Every jutsu details panel shows requirements, CP cost, cooldown, hit model, damage/effect type, line of sight, target shape and whether blind targeting is legal.  
**UX-092 [P0]** Targeting patterns at first: single-target, ground AoE and straight line. Later: cone, projectile path, traps, summoned entities. Pattern previews show only public geometry.  
**UX-093 [P0]** Selecting ground-targeted attack previews valid tile, affected tiles, and chakra/resource cost; confirmation posts one intent to server and becomes pending until acknowledged.  
**UX-094 [P0]** When reaction is armed, show own trigger, remaining duration/expiry and whether CP already spent. It remains visually distinguishable from a passive trait.  
**UX-095 [P0]** Substitution-like reaction that relocates a character may need an escape tile or fallback policy selected at arming time; do not interrupt opponent action to ask for input.  
**UX-096 [P0]** A reaction cannot be manually activated on another character's turn. The resulting animation is shown only to viewers authorized to observe it.  
**UX-097 [P0]** On a server rejection, reset pending state and show a generic error if the reason might disclose unseen opponents. On valid rejection (not enough CP, wrong phase), show specific reason.  
**UX-098 [P0]** Chakra bars, cooldown badges and animation countdowns use meaningful readable numerical labels, not color alone.

## 9. Keyboard/mouse interaction map (PROPOSED)

| Input                                  | Expected behavior                                                |
| -------------------------------------- | ---------------------------------------------------------------- |
| Left click own selectable unit         | Inspect; selected active unit remains the only actor             |
| Hover logical tile                     | Show tile coordinate, known public terrain, applicable preview   |
| Left click a legal tile while Moving   | Stage movement preview / confirm destination                     |
| Left click target/tile while targeting | Stage attack and confirm in preview                              |
| Right click / Esc                      | Cancel target mode or dismiss modal; never undo committed action |
| Mouse wheel                            | Zoom camera                                                      |
| Middle-drag                            | Pan camera                                                       |
| Space                                  | Focus camera on active unit                                      |
| 1, 2, 3                                | Select equipped active jutsu                                     |
| 4                                      | Select basic attack                                              |
| R                                      | Arm currently equipped reaction (during own activation)          |
| V                                      | Toggle allied vision overlay                                     |
| I                                      | Toggle intelligence / pulse overlays                             |
| M                                      | Toggle movement range                                            |
| Tab                                    | Cycle inspection across own squad                                |
| Enter                                  | Confirm staged legal action (if appropriate)                     |

**UX-100 [P0]** Controls are shown in settings and contextual hints. Inputs must respect focus: typing into a room-code field cannot trigger jutsu or move camera.  
**UX-101 [P0]** Keyboard focus must be visible. All main menu, lobby, preparation and combat HUD controls must be keyboard navigable.  
**UX-102 [P1]** Bindings may be customized and persisted for the local browser.  
**UX-103 [P0]** Provide UI state for loading/pending/committed/failed actions, disconnected opponent, own reconnect, timed-out activation, surrendered and match completed.

## 10. Accessibility, polish and feedback

**UX-110 [P0]** Aim for WCAG 2.2 AA for Angular HTML controls where applicable: keyboard access, visible focus, sufficient contrast, readable text, labeled controls, error descriptions. Canvas-specific alternatives and limitations must be documented and assessed.  
**UX-111 [P0]** Meaningful overlays use patterns, labels and shape in addition to hue: movement, ability range, danger, vision, sensing, own/enemy teams.  
**UX-112 [P0]** Offer reduced-motion and screen shake intensity settings; no essential information may be conveyed only through short animations.  
**UX-113 [P0]** Attack/jutsu effects have text-based event equivalents for observed events. No audio-only discovery cues.  
**UX-114 [P1]** Scalable HUD text and rebindable hotkeys; color-blind-friendly palette presets.

### In-app error states

- Invalid/full room: helpful retry or re-enter code; do not disclose secret room data.
- Opponent lost connection: connection status; paused/reconnect policy shown when available.
- WebGL2/WebGPU unsupported: explain compatibility and offer retry/settings.
- Server rejects selected build: identify own invalid item or jutsu and how to fix it.
- Server rejects action: explain only information already allowed to the acting player.
- Match resume: show recovery banner while fetching fresh filtered state; discard stale local overlays.

## 11. Required design deliverables

| Artifact                       | Owner              | Acceptance gate                                                     |
| ------------------------------ | ------------------ | ------------------------------------------------------------------- |
| Sitemap and click paths        | UX                 | Covers all P0 routes including return/error paths                   |
| Desktop wireframes             | UX                 | Menu, lobby, roster, two builders, battle, results                  |
| Design tokens                  | UI artist          | Typography, 8-point spacing, semantic colors, range/vision patterns |
| Battlefield overlay legend     | UX + game designer | Clearly distinguishes all intelligence confidence levels            |
| Jutsu targeting specifications | UX + game designer | Covers visible target, blind tile, AoE, line, blocked action        |
| UI state inventory             | UX + frontend QA   | Empty, loading, waiting, pending, error, reconnect, completed       |
| Interaction specification      | UX + Bevy engineer | Mouse/keyboard mappings and commit/cancel boundaries                |
| Accessibility checklist        | UX + QA            | Keyboard traversal, focus, contrast, reduced motion                 |

## 12. Core UI/UX acceptance scenarios

1. **Preparation privacy:** Open a match in browsers A and B. Each player selects three different shinobi and changes JP/EP builds. Neither opponent's roster nor loadout appears on the other screen or in corresponding client payloads.
2. **Move-after-attack:** A player uses a main action then legally moves once. All remaining movement is consumed on commit; attempting a second movement shows disabled state.
3. **Blind target:** A player targets an empty-looking tile. The preview is identical regardless of hidden enemy occupancy; attacker cannot learn occupancy from result feedback unless an authorized reveal follows.
4. **Discovery:** When an enemy enters vision, name/identity and current tile appear; numeric HP/CP and loadout do not. When leaving vision, live sprite disappears and previous location gets a last-seen timestamp.
5. **Pulse:** After round 3 ends, wide static region(s) appear. They remain timestamped until round 6 pulse and then are replaced; never show exact coordinates or counts.
6. **Concealment:** A pulse-suppressed enemy contributes no ordinary pulse sector. A character may still be visually detected normally.
7. **Reaction:** Player arms a defensive jutsu on their turn. It triggers automatically against a qualifying subsequent attack without an interrupt dialog.
8. **Reconnection:** A disconnected player resumes to a fresh player-filtered state, with no duplicate action and no stale attack/vision overlays.

## 13. Decision register: not blocking skeleton implementation

| ID     | Question                                                     | PROPOSED default / mitigation                                    |
| ------ | ------------------------------------------------------------ | ---------------------------------------------------------------- |
| UX-D01 | Same character twice on own squad?                           | No; unique identity per squad                                    |
| UX-D02 | Tile movement neighborhood?                                  | Four-way; no diagonals for P0                                    |
| UX-D03 | Movement preview versus one-click commit?                    | Two-stage confirm for first release                              |
| UX-D04 | Time budget per activation?                                  | Configurable 45 s, pending playtest                              |
| UX-D05 | Friendly-fire behavior?                                      | Ability-specific and prominently indicated                       |
| UX-D06 | Visually hidden ally during concealment?                     | No; own units always visible                                     |
| UX-D07 | Pulse region partition?                                      | Four large fixed sectors on 20×20 map                            |
| UX-D08 | Slot structure?                                              | 3 active + 1 reaction, 1 weapon/1 armor/2 tools                  |
| UX-D09 | Visual detection mechanics through cover?                    | Full LOS-blockers hide, low cover modifies attack/defense only   |
| UX-D10 | Custom shinobi creation available at initial public release? | Confirmed long-term feature; P1 after multiplayer vertical slice |

## 14. Engineering reference links

These are relevant official documentation, not automatic commitments to specific package versions:

- [Bevy 0.20 release notes](https://bevy.org/news/bevy-0-20/)
- [Bevy `Window.canvas` and `fit_canvas_to_parent` documentation](https://docs.rs/bevy/latest/bevy/window/struct.Window.html)
- [Angular zoneless change detection guide](https://angular.dev/guide/zoneless)
- [Axum WebSocket upgrade](https://docs.rs/axum/latest/axum/extract/struct.WebSocketUpgrade.html)
- [W3C WCAG 2.2 keyboard focus guidance](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible)
