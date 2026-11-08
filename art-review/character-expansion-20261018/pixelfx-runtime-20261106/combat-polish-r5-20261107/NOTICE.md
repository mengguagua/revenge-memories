# Notices

**Hugo Duprez.** `src/core/sim.js` and the effects that say so at the top of their file adapt Sprite Fusion's
open-source pixel art VFX (https://www.spritefusion.com/pixel-art-vfx), Copyright (c) 2026 Hugo Duprez, MIT License.

**Hollow Crown.** `src/core/act.js` adapts how Hollow Crown plays its skills (poses on 12 fps steps, hit-stops, the springy
straw target), from
https://github.com/rehan-remade/hollow-crown, Copyright (c) 2026 rehan-remade, MIT License.

**Patch Pixel.** The font in `gallery/fonts` is Patch's own and is not covered by this repository's MIT license. See
`gallery/fonts/NOTICE.md`.

## This preview

PixelFX source: patch-gg/pixelfx v0.3.0, commit a84159688af3ca37a4be05a0d422b94451b2e24e. Native-size, palette and timing adaptations are isolated under source/full-battle-20261107/pixelfx-work in the parent review directory. The Patch Pixel gallery font and sample actors are not included. Game captures and game artwork remain part of the existing game project; the PixelFX MIT notice does not relicense those assets.

## Revision 2

The 83 newly authored native effect atlases adapt PixelFX particle simulation, lightning inking, flame geometry and arrow timing. Source and reproducible export scripts are in `source/weapon-magic-r2-20261107/` in the parent review directory. The eight lance styles, five bow styles, thirteen spell families and hero choreography are preview-specific adaptations. The original PixelFX attribution above is retained. This preview includes no Patch Pixel font or PixelFX mannequin artwork. All animation callbacks, results and source frames are retained from the same isolated Godot sampling snapshot.

## Revision 3

PixelFX fire palettes and the native spell opening and ending layers use the same pinned toolkit. Their export source is in the parent review directory under `source/magic-sound-r3-20261107/`. The 64 candidate audio cues were rendered offline using local Stable Audio 3 Small-SFX and authored timing guides. Source receipts and waveform metrics are in `qa/audio-generation.json`.

## Revision 4

The render workbench was initialized by the installed Codex PixelFX Skill. The Fireball, Lightning strike, Double slash, Spin slash, Scythe reap and supporting effects are direct module renders or adaptations of the pinned PixelFX source. The stock reference videos use the upstream stand-in figures only to show the original effects. The game candidate uses the game's own characters, sword sprites and guard lance/shield. Module names, SHA-256 fingerprints, modified options, and action timing are listed in `qa/r4-provenance.json`. The continuous Fireball audio re-edits the locally generated R3 model takes; see `qa/r4-fire-audio.json`.

## Revision 5

This preview adds direct renders of PixelFX `ui/damage-number` and `shadow/life-steal`. Fire colors were sampled from the original battle captures. The native health cards and hit tick are drawn from the existing game, using the ordinary attack cadence measured in the capture. The left-hand capture remains intact. See `qa/r5-provenance.json` for upstream source hashes, color samples and hit timing.
