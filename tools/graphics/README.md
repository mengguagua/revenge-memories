# Original FE2 graphics extraction

`python3 tools/extract_graphics.py --source /path/to/fe2` decodes original NES 2-bpp CHR and composes the original source tile/OAM tables. It does not redraw images, resample runtime sprites, or generate new art. Source revision is recorded in `data/graphics.json`.

`python3 tools/extract_graphics.py --village-only --source /path/to/fe2` rebuilds only the six village character sheets and their source metadata, retaining the rest of the graphics and any localized font metadata.

## Godot contract

- `graphics.json.title`: native 256×240 static title composition and 152×16 logo. Original logo, sword OAM, copyright and source screen positions; intro rotation/fade has not been rebuilt.
- `graphics.json.portraits[name]`: 48×48 original portrait, six tiles per row, tile flip and four original per-character palettes reconstructed from `L09AE97`, `L09AF6B`, `L09B014`, and `L09BAFD`.
- `graphics.json.map_units[class_side]`: 144×24 sheet, six 24×24 frames. Original class metatile table and CHR 24,25,21,25 cycle; battlefield idle actors do not turn toward movement. The green terrain color is transparent for compositing over ground tiles; black outlines remain opaque.
- `graphics.json.village_units[name]`: 144×24 sheet, six 24×24 frames. `sprite_id - 1` lookup comes from `L0FCC01`. Opening actor ids come from `L0A8D33`. Original village palette is `L0D9230`. Village CHR **30** (`bank015.chr`, first 4KiB) is restored to both MMC4 pattern latches by `L0DADA0` / `L0DADB0`; CHR 26 belongs to tactical-map movement and corrupts the village figures despite using the same OAM pointer tables. `tile_origin=[4,4]` aligns each 24×24 frame with the 16×16 village tile; `anchor=[4,20]` records its left/ground anchor.
- `graphics.json.battle[class_side]`: original OAM poses in an 80×64 horizontal sheet. Fighter has 60 frames, Soldier 12, Villager/Brigand 16. Anchor is `[40,56]`. Class→PRG OAM table, CHR bank and palette lookup are recovered from `L0FE436`, `L0FE44C`, `L058E98`, `L058EAE`, `L058EC4`, `L058EDA`. Standard attack pose order and authored per-pose tick durations are recovered from `L009FF1` / `L00A051`. `attack_schedule` includes contact pose/tick, approach/return source per-tick dx/dy, and the damage-pause boundary. A full copy of the original damage/HP/opcode scheduler is still the parent native game's responsibility.
- `graphics.json.battle_background`: original 256×128 black side-view field. `L05803C` clears name tables via `L0FC23D`; original HUD begins at y128. There is no illustrated grass/forest battle background in this path. `battle_hud_frame.png` restores the lower 256×112 UI structure with original HIT/AT/DF bitmap labels and leaves dynamic fields empty.
- `graphics.json.panel`: original 24×24 nine-patch frame; keep 8-pixel corner/edge margins fixed, and pad content by at least 10 native pixels. A uniform black center allows variable width/height without stretching ornaments. Composition comes from `L0BA6F5` through `L0BA782`.
- `cursor.png`: native tile F3 cursor; source glyph alpha.
- `font.png`/`ui.png`: first 4KiB of CHR0, 16×16 tiles, 8×8 each. `source/jp.tbl` preserves original text code mapping. `font.char_codes` maps Unicode to source bytes; 0F/1F combining marks render above the preceding base glyph with x offset 0, y offset -8, and no extra advance. Reserve 8 pixels above each text baseline and 16-pixel native line spacing.
- `maps/*.png`: losslessly re-encoded original tileset/building/world map atlases.

Use nearest filtering and integer pixel scaling. Source `.chr` files and text mapping remain isolated under `assets/original/graphics/source/`. The source folder has `.gdignore` to isolate original binary inputs from Godot import/export. Raw atlas output and unused OAM entries are retained for future analysis, and need not be instantiated by the first-battle scene.

## Verification performed

- Every asset's dimensions, actual PNG bytes, intended kind and source are recorded in `data/graphics.json`.
- All extracted runtime PNG alpha values are 0 or 255; no partial alpha, white matte or filtered edge is introduced.
- Full source OAM coordinate bounds fit the 80×64 battle frame: Fighter x[-23,34), y[-24,40); Soldier x[-28,29), y[0,32); Villager/Brigand x[-24,24), y[-16,32).
- Opening village frame source bounds x[0,17), y[-8,8) fit the 24×24 safe crop. One-pixel mirrored OAM offset is preserved.
- After correcting the village CHR bank, all 36 walking/directional frames were checked for complete OAM bounds and binary alpha. Original-size and 4× nearest-neighbor contact sheets plus per-frame bounds/opaque-pixel counts are recorded in `reports/screenshots/village-sprites-repaired-*.png` and `reports/village-sprite-repair.json`.
- Initial Alm portrait selection is `L09BDBF[1]=36`; promotion changes the lookup to `L09BDBF[36]=0`. Initial Celica uses `L09BDBF[2]=48`, promoted Celica `L09BDBF[37]=16`. The original portrait sequence is not chronological, so indices 36/48 are correct for the opening characters.
- Palette RGB values use a fixed NES color profile; source palette indices remain recorded. Hardware/emulator color profiles can look slightly different.
- No Godot window was launched by this extraction task. Runtime spacing and animation/sound synchronization still require the parent game's background rendering verification.
