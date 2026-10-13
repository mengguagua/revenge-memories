# Original Fire Emblem Gaiden audio

These Ogg Vorbis assets are rendered from the original, unchanged 6502 sound driver and musical/effect data in fe2's `src/bank014.asm`. They are not newly composed or generic replacement effects. Runtime needs only Godot's standard audio decoder. No ROM execution window, recording device, online music generator, or emulator plug-in is used in the game.

The NSF wrapper copies the 16 KiB sound bank to `$8000`, initializes the APU as the original RESET routine does, sends a single request, and calls original `$8000` once every 16,639 microseconds (NTSC). The original `L0FF58A` request contract is `($06D0 + high_nibble) = 1 << low_nibble`. The NSF track parameter uses the original sound test's linear numbering, `high_nibble * 8 + low_nibble`.

## Playback in Godot

Read `data/audio.json`, choose `music` or `sfx`, and load the `path`. For `AudioStreamOggVorbis`, assign both `loop` and `loop_offset` from the entry. Title and opening are finite original tracks and stop naturally. Music loops use the original song's note position, including any intro. Some tracks retain a fractional tempo accumulator and repeat with a one-frame difference; their manifest records the tolerance. No loop is claimed when the capture does not prove one.

`default_enabled=false` means an original effect was extracted but its proposed scene binding has not been established. Do not play those entries by default. Normal missed/no-damage attacks request `$43`. Normal physical damage enters bank005 `L059C3E` state29: bank000 `L00BED0` stops existing effects with `$30`, then state30 `L00BED9` requests impact `$03`. That impact is also reused by the evil-sword branch. Individual HP decrements request `$12` under the separate `hp_tick` key. The pending death/transition effect `$53` is sustained until another original request stops it; it is not a self-terminating death jingle.

## Source evidence

| Key | Original request | Evidence |
| --- | --- | --- |
| title | `0x71` | bank004 `L049B98`, `LDA #113` |
| opening | `0x72` | bank004 `L04A4F1`, `LDA #114` |
| village | `0xA6` | bank012 `L0CB244[0]=0x13`, `L0CB203[0x13]=0xA6` |
| world_map | `0xA0` | bank007 `L078A58[0]` |
| battle | `0xA1` | bank006 `L06BA5F[0]` |
| enemy_phase | `0xA4` | bank006 `L06BA5F[1]` |
| combat | `0x86` | bank005 `L058091`, `$06D8=64` |
| unit_death | `0x90` | bank005 `L058583/L0585CC`: player HP `$033C=0`, death quote `characterID+13` |
| levelup | `0x81` | bank005 `L058667`, `$06D8=2` |
| menu_move / hp_tick | `0x12` | bank015 `L0FF56C`; bank005 `L0599F4` HP decrement |
| hit | `0x03` | bank005 `L059C3E` state29 -> bank000 `L00BED0/L00BED9` |
| menu_confirm | `0x10` | bank015 `L0FF572` |
| menu_cancel | `0x13` | bank015 `L0FF578` |
| dialogue | `0x25` | bank010 `L0A8816` |
| miss | `0x43` | bank005 `L059C18/L059C69` when hit flag or damage equals zero |

`unit_death` is the original allied-character death cue. The source dispatches `$90` only when allied HP `$033C` is zero, then selects `characterID+13` in bank001 `L01B8A0` for the death quote (Alm ID1 selects entry14 `L01BA6E`). Enemy HP zero goes through a different branch without `$90`. Do not use this cue for enemy kills or map victory. Character growth/death jingles pause the current music player; growth then resumes its prior position. On Alm defeat, stop the previous music before the death cue.

## Reproduce

Use the reconstructed iNES ROM and an upstream [Game Music Emu](https://github.com/libgme/game-music-emu) source checkout. Dependencies are build-time only. The extraction script also accepts a standalone 16 KiB sound-bank binary.

```sh
python3 tools/audio/build_renderer.py /path/to/game-music-emu /private/tmp/fe2-gme-renderer
clang -O2 -I/opt/homebrew/opt/libogg/include -I/opt/homebrew/opt/libvorbis/include tools/audio/encode_vorbis.c -L/opt/homebrew/opt/libvorbis/lib -L/opt/homebrew/opt/libogg/lib -lvorbisenc -lvorbis -logg -o /private/tmp/fe2-vorbis-encoder
python3 tools/extract_audio.py --rom /path/to/fe2.nes --gme /private/tmp/fe2-gme-renderer/libgme.dylib --encoder /private/tmp/fe2-vorbis-encoder
```

The renderer hook captures the actual driver pointers, duration counters, transposition and repeat stack for loop analysis. The original driver and data bytes remain unchanged. PCM is stereo 44.1 kHz, encoded with installed libvorbis at quality 0.6. The manifest records each resource's original request, duration, peak level, loop status, source evidence and actual file size.
