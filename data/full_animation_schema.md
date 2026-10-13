# Original animation resource contract

`graphics.json.battle.class_<id>_<side>` covers original classes1–22 and both
source sides. `promoted_alm_ally` selects Alm's promoted sword body/program.
`promoted_celica_ally` keeps the original class11 body (promotion changes her
portrait/status identity, not the CHR5 body). Portraits are indexed through
`portraits_by_index`; source character ids map through `character_portraits`.

All body entries have `frame_size`, `anchor`, and `sequences.idle`. The anchor is
the **feet baseline**, original body OAM y96 +32 = screen y128. Draw at
`actor_origin + offset - anchor`; never assume80×64 or a40×56 anchor. Class5
dragon and class21 Duma include their full source extents. The native viewport
clips the upper battlefield to its original256×128 region. OAM attack frame ids
start at0; background poses begin at `background_frame_offset`.

## Melee authored timeline

`attack_schedule.native_timeline.before_contact/after_contact` contains one item
per original authored tick: `{frame, offset:[x,y], flip}`. Offsets assume an actor
on the right facing left; negate x for an enemy. `flip` is **relative to the
actor's side**, so actual flip is `(side == enemy) XOR frame.flip`. Play the first
array, resolve damage once, then play the second. Source opcode dispatch/upload
overhead is omitted; pose timers and movement deltas are exact.
For frames below `source_oam_frame_count`, add `oam_flip_origin_offset` when the
final body flip is true. Background frames already encode their side-specific
upload normalization and do not need this OAM-only16px compensation.

## Original routine timelines: magic and projectiles

`attack_schedule.effect_variant` or `spell_variants[str(item_id)]` points into
`full_animation_effects.json.variants`. Example `class_15_ally_item_23` is Fire;
`class_12_enemy_bow` is an enemy archer shot. Use the suffix `_far_ally` when the
**exchange initiator** is an ally at Manhattan distance>1, or `_far_enemy` for
an enemy initiator. Keep that formation for the counterattack. Source L06ABFF
stores distance−1 only on the initiating actor; L05812E checks zero/nonzero,
so ranges2,3,4,5 all use the same far arrangement. Each formation was executed
independently, so projectile contact timing also changes: normal bow contact is
tick54 close and tick56 far (includes original bytecode overhead).

Each variant provides `actor_origin:[x,128]`, `source_actor_origins` for both
sides, `contact_tick`, `frames`, `source_class_id`, `source_side`, and source
program/effect ids. Each frame provides `{frame,offset,flip,effects}`. Unlike the
authored melee timeline, these offsets are already **screen-space**, including
the firing side: do not negate them again. Flip remains relative to side.
At frame `contact_tick`, resolve the native damage event **exactly once**, then
continue playback. No damage, HP growth, or gameplay results are baked in.

Each effect is `{sprite, position:[x,y], flip, priority}`. The sprite key resolves
in `full_animation_effects.json.sprites` to `{path, frame_size, anchor, frames:1}`.
Position is the original **raw OAM origin**, not feet, and the effect anchor is
relative to that raw origin. Draw `position - sprite.anchor`. Effect flip is
already the final source flip; when true add `sprite.flip_origin_offset` after
subtracting anchor. That16px horizontal compensation comes from source
L0FCB12–L0FCB2A (`OAM x becomes8-x` plus tile reflection), rather than mirroring
about the center of the bitmap. Do not apply the body's side flip again.

The opponent class in each standard variant is recorded: class14 for ally
attacks, class21 for enemy attacks. Append `_vs_heavy` after the formation suffix
to use a separately executed opponent-class4 configuration with recomputed
contact timing. This covers enemy targets class4/5/7 at x56, ally targets4/7 at
x184, and ally flying targets3/5 when those targets initiated a distant exchange
and stand at x184. All other original target classes have the standard origin.
Thus range2–5 and the8px class exceptions are actual source executions; do not
shift a projectile and leave an unrelated close-range contact tick.

`weapon_variants` selects original javelin/Gradivus, Levin sword, and Alm's bow
programs by item id. `spell_variants` selects Fire through enemy Medusa and the
white spells (Recover, Physic, Nosferatu, Warp, Fortify). Class11 retains its
normal sword attack schedule; casting selects its spell variant explicitly.
The unused Gaia slot30 has a null source effect and is not replaced by another
spell. Named/high-level enemy palettes are in each class's `palette_variants`;
the source's named override takes precedence over the `elite` level>=10 entry.

When a frame has `sound_requests`, dispatch those packed request integers
through `full_audio.json.sfx_by_request`. These were recorded from the original
effect handlers and bank000 sound-state routines. Damage feedback remains the
separate native contact event, so it can play its own impact/HP ticks. Warp
frames also expose source `target_palette` and `screen_emphasis` changes; warp
uses palette disappearance, rather than an invented projectile.

## Village actors

`graphics.village_sprites[str(source_sprite_id)]` covers all66 original CHR30
personal sprite ids. Use its `tile_origin` to draw relative to a map cell; its
frame dimensions can differ from the older six24×24 aliases. Down/up/side each
have two source frames. Native side art faces right; flip only for walking left.

## Extraction and limits

`extract_full_graphics.py` decodes original CHR/OAM/PPU tables. For magic,
`extract_full_effects.py` runs the original bank005 caster/effect routines with
bank000 pose/motion and bank001 trajectory routines through
`fe2_source_cpu.py`, **offline only**. Runtime consumes ordinary JSON/PNG.
Only damage-dependent HP/palette pause handlers are replaced by the native
contact event. Source RNG starts from a fixed seed for reproducible particles.
This is not a runtime emulator, and neither ROM nor extractor enters the pack.
The supplied effect images/timelines cover source OAM effects, body poses,
trajectories and effect requests. Mid-scanline PPU/raster rendering is not
emulated by the native player; renderer-level color/scroll transitions still
need to use the captured native feedback data.
