# Chapter 3 actual-input audit

All 8 maps won in this audit and post-battle hub interactions completed. Godot 4.7.1 headless, actual main scene and keyboard controller input. No stats, RNG, unit positions, difficulty values or victory rules edited. No screenshots added.

Maps start from genuine independent checkpoints and enter the current map through normal preparation. All source save hashes unchanged. This is map-by-map verification, not one uninterrupted new campaign. Chapter boundary uses this audit's final-map post-battle save.

| Map | Victory turn | Full attempts | Newly dying playable members | Success save |
|---|---:|---:|---|---|
| M31 | 18 | 1 | 贝克 | [Save](current/current-M31-victory.json) |
| M32 | 11 | 1 | None | [Save](current/current-M32-victory.json) |
| M33 | 15 | 1 | None | [Save](current/current-M33-victory.json) |
| F31 | 18 | 1 | None | [Save](current/current-F31-victory.json) |
| F32 | 21 | 1 | None | [Save](current/current-F32-victory.json) |
| F33 | 18 | 1 | None | [Save](current/current-F33-victory.json) |
| S31 | 8 | 1 | None | [Save](current/current-S31-victory.json) |
| S32 | 10 | 1 | None | [Save](current/current-S32-victory.json) |

[Machine-readable summary](summary.json) lists genuine sources, all success/post-battle saves, turn states, new casualties and retained failed attempts. Original records are in `current/current-play.json`.

## Changes and evidence

Replaced tactical_notes with short player-facing directions. Removed internal field names, design implementation notes and old coordinates. visual_notes remain unchanged. The editing script asserted every other JSON field stayed identical: [before/after evidence](tactical-note-changes.json).

All edited objective menus reopened through actual input and pagination. This is content/input verification, not visual screenshot acceptance. Pure copy changes did not trigger battle replays.

M32 status said turn 5, but after_phase returns while turn <= 5: the cart actually starts on player turn 6. Text now matches and mentions opening the cart lock also stops it. [Evidence](m32-status-change.json).

The current M33 post-battle save completed both-team council, relationship dialogue, messenger handoff, chapter 3 closure and chapter 4 entry. [Boundary and eight objective menus](followup/followup.json).
