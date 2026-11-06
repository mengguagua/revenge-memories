# Chapter 4 actual-input audit

All 10 maps won in this audit and post-battle hub interactions completed. Godot 4.7.1 headless, actual main scene and keyboard controller input. No stats, RNG, unit positions, difficulty values or victory rules edited. No screenshots added.

Maps start from genuine independent checkpoints and enter the current map through normal preparation. All source save hashes unchanged. This is map-by-map verification, not one uninterrupted new campaign. Chapter boundary uses this audit's final-map post-battle save.

| Map | Victory turn | Full attempts | Newly dying playable members | Success save |
|---|---:|---:|---|---|
| M41 | 14 | 1 | None | [Save](current/current-M41-victory.json) |
| M42 | 17 | 2 | None | [Save](m42-safer-leader/m42-safer-leader-M42-victory.json) |
| M43 | 10 | 1 | None | [Save](current/current-M43-victory.json) |
| M44 | 14 | 1 | None | [Save](current/current-M44-victory.json) |
| F41 | 12 | 1 | None | [Save](current/current-F41-victory.json) |
| F42 | 14 | 1 | None | [Save](current/current-F42-victory.json) |
| F43 | 19 | 1 | None | [Save](current/current-F43-victory.json) |
| F44 | 21 | 1 | None | [Save](current/current-F44-victory.json) |
| S41 | 10 | 1 | None | [Save](current/current-S41-victory.json) |
| S42 | 12 | 1 | None | [Save](current/current-S42-victory.json) |

[Machine-readable summary](summary.json) lists genuine sources, all success/post-battle saves, turn states, new casualties and retained failed attempts. Original records are in `current/current-play.json`.

## Changes and evidence

Replaced tactical_notes with short player-facing directions. Removed internal field names, design implementation notes and old coordinates. visual_notes remain unchanged. The editing script asserted every other JSON field stayed identical: [before/after evidence](tactical-note-changes.json).

All edited objective menus reopened through actual input and pagination. This is content/input verification, not visual screenshot acceptance. Pure copy changes did not trigger battle replays.

M42 first attempt naturally lost on turn 9 after the hero advanced away from his guard. Only driver tactics changed to keep the hero behind the guard; the single-map retry won on turn 17. No game difficulty change. [Retry](m42-safer-leader/m42-safer-leader-play.json).

S41 first win omitted optional refuge confirmation. Actual keeper dialogue refused the ring and explained missing facts cannot be supplied afterward. For reward coverage only, resumed the current turn-8 save, confirmed the refuge, won on turn 11, claimed exactly one ring, and confirmed repeat dialogue does not duplicate it. This supplemental branch is separate from failure retries. [Reward evidence](s41-reward/reward-followup.json).

F44 actual first post-battle dialogue promoted Eileen and delivered her light sword. Reload/repeat dialogue preserves both without duplicate delivery. The current F44 post-battle save then closed chapter 4 and opened chapter 5. [Boundary](boundary-retry/followup.json). An initial followup driver assertion used Array.count(17) on JSON float 17.0; corrected to int-normalized counting and reran only this range. No item was lost.

Promotion copy uses direct language for class base stats, retaining higher values, preserving current HP/level/experience/training, and spell HP cost. [Changes](promotion-copy-changes.json), [actual pagination](promotion-copy/pagination.json).

chapter4_state used old north-well coordinate [5,6]; current north well is [10,9]. The fixture now reads well_n.position. All 625 assertions pass; no game well location or capture rule changed. [Checks](state-checks.json).

Ten current objective menus and ineligible ring dialogue passed in the [first followup](followup/followup.json); its later int/float assertion failure and dependent early stop remain visible. The targeted retry above supplies final passing boundary evidence.
