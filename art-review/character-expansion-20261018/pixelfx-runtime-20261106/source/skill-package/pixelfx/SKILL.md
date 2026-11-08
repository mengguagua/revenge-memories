---
name: pixelfx
description: Create, recolor, remix, preview and export pixel-art VFX or weapon-effect animations with the local PixelFX library. Use for PixelFX, pixel hit effects, sword slashes, arrows, spells, sprite sheets and effect comparisons in a game. This is a code-driven effects workflow; character redesign and ordinary interface layout are separate tasks.
license: MIT
---

# PixelFX for Codex

Use the bundled Node toolkit to make repeatable pixel effects, inspect actual frames, and deliver game-sized results. The package includes all 244 upstream effects at the commit recorded in `upstream.json`; it does not need Claude, an Anthropic API key, npm installation or a fresh clone.

## Local tools

Resolve `<skill-dir>` from this SKILL.md's location. Node 18+ is required; ffmpeg is optional for GIF/MP4. The Python launcher routes commands to the bundled toolkit:

```bash
python3 <skill-dir>/scripts/pixelfx.py list arrow
python3 <skill-dir>/scripts/pixelfx.py render impacts/hit-spark --sheet --out <absolute-preview-directory>
python3 <skill-dir>/scripts/pixelfx.py render fire/torch --gif --out <absolute-preview-directory> --opts '{"palette":["#21343d","#466977","#a1c1c2","#e0e9de"],"light":0.3}'
python3 <skill-dir>/scripts/pixelfx.py act moves/arrow-shot --sheet --out <absolute-preview-directory>
python3 <skill-dir>/scripts/pixelfx.py check projectiles/arrow
```

Render/act outputs require an explicit `--out`, so generated files stay in the task's chosen directory. Keep the installed toolkit immutable. For custom code, make a task-local working copy:

```bash
python3 <skill-dir>/scripts/pixelfx.py workspace <absolute-task-directory/pixelfx-work>
python3 <skill-dir>/scripts/pixelfx.py --library <absolute-task-directory/pixelfx-work> new melee/my-slash
python3 <skill-dir>/scripts/pixelfx.py --library <absolute-task-directory/pixelfx-work> render melee/my-slash --sheet --out <absolute-preview-directory>
```

Use an existing task-local PixelFX copy when suitable. Do not overwrite an existing workspace. `list` searches names/tags; `toolkit/docs/CATALOG.md` is the full catalog. Read `toolkit/docs/AUTHORING.md` before authoring or changing effect code.

## Choose and adapt

- Inspect the actual game/reference and identify logical pixels, display scale, palette, direction, layer and event timing before choosing effects.
- Search existing effects first. Try their palette, light, seed, radius, height or other supported options. If their geometry is too large, adjust source shapes and particle counts for the target native size; simple downscaling is not a substitute.
- For whole attacks, inspect `src/fx/moves/` for sequencing. Keep the game's own character, weapon, gameplay events and damage count. A stock mannequin or an upstream critical/combo must not silently become a new character, critical or extra hit.
- Ordinary independent effects use `createFx`; `createAct` includes demonstration acting. Body-bound effects can paint the stock character: substitute the game's own mask or use an independent effect layer before delivery.
- Pin one seed for comparisons. Synchronize wind-up, release, contact and recovery to the actual game. A preview request does not authorize runtime integration.

## Render and verify

Open generated contact sheets and inspect motion, not only a single peak frame. Check native 1×, actual intended display scale, integer enlargement, dark/light backgrounds, alpha edges, complete bounds and clean endings/loops. Iterate on visible failures; scale verification to the change.

For a game comparison, use actual engine-rendered footage or a faithful documented reproduction. Keep reference and candidate on one clock, label what changed, and provide pause/scrub/frame stepping where useful. Distinguish engine/device capture and composited proposals.

For Godot/other non-JS engines, prefer offline PNG sprite sheets plus JSON. Preserve fps, frame rectangles, loop flag and pivot from `meta.pixelfx`; convert to the project's existing animation format rather than assuming drop-in compatibility. Preserve existing hit/HP/save ownership. Check front/back layering and the RGBA export's baked glow on the actual background.

Use existing local lossless compressors after visual acceptance. Record actual dimensions and bytes, retain sources, and follow the project's quality/size rules. Copy only required effects into an authorized runtime integration. Keep LICENSE/NOTICE for derived code/effects; the excluded gallery font is not MIT-covered.

## Project-specific routing

For `revenge-memories` / 复仇与回忆, read [the project workflow](references/revenge-memories.md) and the current project AGENTS.md. Other projects should use their own instructions.

The original upstream skill is retained at `references/upstream-skill.md` for attribution/reference. This Codex entrypoint governs the adapted workflow; do not mechanically follow upstream installation commands, mandatory iteration counts or automatic integration suggestions.
