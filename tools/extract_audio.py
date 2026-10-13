#!/usr/bin/env python3
"""Render Fire Emblem Gaiden's unchanged bank 14 sound driver without a window.

Inputs: reconstructed iNES ROM (or standalone 16 KiB bank), an NSF-capable
Game Music Emu dylib, and ffmpeg. Runtime files have no emulator dependency.
An optional GME frame hook writes music-driver state for exact loop detection.
See tools/audio/README.md for renderer preparation and source ID evidence.
"""
import argparse
import array
import ctypes
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
FRAME_US = 16639
TRACE_SIZE = 224

# Original packed sound request IDs. See source_evidence in generated manifest.
TRACKS = [
    ("title", 0x71, 180, "music", "bank004 L049B98: title music request 113"),
    ("opening", 0x72, 180, "music", "bank004 L04A4F1: opening sequence request 114"),
    ("opening_alternate", 0x73, 180, "music", "bank004 L04B0F9: attract battle demo request 115"),
    ("village", 0xA6, 180, "music", "bank012 L0CB244[0] -> L0CB203[19]"),
    ("world_map", 0xA0, 180, "music", "bank007 L078A58[chapter1]"),
    ("battle", 0xA1, 180, "music", "bank006 L06BA5F[Alm player phase]"),
    ("enemy_phase", 0xA4, 180, "music", "bank006 L06BA5F[Alm enemy phase]"),
    ("combat", 0x86, 180, "music", "bank005 L058091: $06D8 = 64"),
    ("unit_death", 0x90, 20, "jingle", "bank005 L058583/L0585CC: player HP $033C=0; death quote $0304+13; bank001 L01B8A0"),
    ("levelup", 0x81, 20, "jingle", "bank005 L058667: $06D8 = 2"),
    ("menu_move", 0x12, 4, "sfx", "bank015 L0FF56C"),
    ("menu_confirm", 0x10, 4, "sfx", "bank015 L0FF572"),
    ("menu_cancel", 0x13, 4, "sfx", "bank015 L0FF578"),
    ("dialogue", 0x25, 3, "sfx", "bank010 L0A8816 text advance"),
    ("attack", 0x21, 4, "sfx", "Original driver effect 0x21; swing mapping pending animation opcode check"),
    ("hit", 0x03, 4, "sfx", "bank005 L059C3E normal damage -> $04A6=29; bank000 L00BED0 stops SFX, L00BED9 requests $03"),
    ("hp_tick", 0x12, 4, "sfx", "bank005 L0599F4: HP decrement tick; same request as menu movement"),
    ("miss", 0x43, 4, "sfx", "bank005 L059C18/L059C69: missed attack or zero damage"),
    ("death", 0x53, 4, "sfx", "bank005 L05912C battle transition sustained noise; death mapping pending"),
]


def build_nsf(bank: bytes) -> bytes:
    if len(bank) != 0x4000:
        raise ValueError("Sound bank must be exactly 16 KiB")
    body = bytearray(bank) + bytearray(0x4000)
    # Original sound-test API: linear ID -> request group / bit.
    # Initialize APU as RESET does, then invoke original frame entry $8000.
    init = bytes.fromhex(
        "48 A9 00 8D 15 40 A9 0F 8D 15 40 A9 C0 8D 17 40 "
        "20 00 80 68 48 4A 4A 4A A8 68 29 07 AA BD 40 C0 "
        "99 D0 06 20 00 80 60")
    body[0x4000:0x4000+len(init)] = init
    body[0x4030:0x4034] = bytes.fromhex("20 00 80 60")
    body[0x4040:0x4048] = bytes([1, 2, 4, 8, 16, 32, 64, 128])
    header = bytearray(128)
    header[:8] = b"NESM\x1a\x01\x60\x01"
    struct.pack_into("<HHH", header, 8, 0x8000, 0xC000, 0xC030)
    title = b"Fire Emblem Gaiden Original Driver"
    header[14:14+min(31, len(title))] = title[:31]
    struct.pack_into("<H", header, 110, FRAME_US)
    struct.pack_into("<H", header, 120, 19997)
    return bytes(header + body)


def driver_loop(trace_path: Path):
    if not trace_path.exists():
        return None
    raw = trace_path.read_bytes()
    frames = [raw[i:i+TRACE_SIZE] for i in range(0, len(raw), TRACE_SIZE)]
    # Note pointers, timing counters, tempo, transpose, and nested loop stacks.
    # Ignore oscillator-envelope scratch fields that do not define song position.
    keys = [f[:16] + f[16:34] + f[16+0x3B:16+0x44] + f[16+0x86:]
            for f in frames if len(f) == TRACE_SIZE]
    seen = {}
    for j, key in enumerate(keys):
        if not any(key[:8]):  # All musical channels have stopped.
            continue
        for i in seen.get(key, []):
            period = j-i
            if period < 120 or j+period > len(keys):
                continue
            if keys[i:j] == keys[j:j+period]:
                return {"start_frame": i+1, "end_frame": j+1,
                        "start_seconds": (i+1)*FRAME_US/1e6,
                        "end_seconds": (j+1)*FRAME_US/1e6,
                        "period_frames": period,
                        "verified_repeated_driver_frames": period}
        seen.setdefault(key, []).append(j)
    # The driver's fractional tempo accumulator can shift a musical repeat by
    # one NTSC frame, so some songs have no full RAM-state repeat in 180s.
    # Match original note-position sequences across the remaining full capture.
    from collections import Counter
    positions = [f[:8] + f[16+0x3B:16+0x40] for f in frames
                 if len(f) == TRACE_SIZE]
    first, candidates, pairs = {}, Counter(), {}
    for j, key in enumerate(positions):
        if not any(key[:8]) or (j and key == positions[j-1]):
            continue
        if key not in first:
            first[key] = j
            continue
        i = first[key]
        period = j-i
        if period >= 120:
            candidates[period] += 1
            pairs.setdefault(period, (i, j))
    for period, count in sorted(candidates.most_common(32)):
        i, j = pairs[period]
        check_frames = len(positions)-j-2
        if check_frames < period*1.5:
            continue
        matched = sum(positions[i+n] in positions[max(0,j+n-2):j+n+3]
                      for n in range(check_frames))
        similarity = matched/check_frames
        if similarity >= 0.985:
            return {"start_frame": i+1, "end_frame": j+1,
                    "start_seconds": (i+1)*FRAME_US/1e6,
                    "end_seconds": (j+1)*FRAME_US/1e6,
                    "period_frames": period,
                    "verified_note_position_frames": check_frames,
                    "note_position_match": round(similarity, 6),
                    "tempo_tolerance_frames": 2,
                    "timing_note": "Original fractional tempo may differ by one NTSC frame across repeats"}
    return None


class Renderer:
    def __init__(self, library: Path, nsf_path: Path):
        self.g = ctypes.CDLL(str(library))
        self.g.gme_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
        self.g.gme_open_file.restype = ctypes.c_char_p
        self.g.gme_start_track.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.g.gme_start_track.restype = ctypes.c_char_p
        self.g.gme_ignore_silence.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.g.gme_play.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_short)]
        self.g.gme_play.restype = ctypes.c_char_p
        self.g.gme_warning.argtypes = [ctypes.c_void_p]
        self.g.gme_warning.restype = ctypes.c_char_p
        self.g.gme_delete.argtypes = [ctypes.c_void_p]
        if hasattr(self.g, "fe2_set_trace"):
            self.g.fe2_set_trace.argtypes = [ctypes.c_char_p]
        self.nsf_path = nsf_path

    def render(self, request: int, seconds: float, trace: Path):
        emu = ctypes.c_void_p()
        self._check(self.g.gme_open_file(str(self.nsf_path).encode(), ctypes.byref(emu), RATE))
        self.g.gme_ignore_silence(emu, 1)
        if hasattr(self.g, "fe2_set_trace"):
            self.g.fe2_set_trace(str(trace).encode())
        # The ROM's debug sound test numbers groups as 8 slots each.
        linear = ((request >> 4)*8)+(request & 7)
        try:
            self._check(self.g.gme_start_track(emu, linear))
            pcm = array.array("h")
            for n in range(math.ceil(seconds)):
                count = min(RATE, round((seconds-n)*RATE))*2
                if count <= 0:
                    break
                block = (ctypes.c_short*count)()
                self._check(self.g.gme_play(emu, count, block))
                pcm.frombytes(bytes(block))
            warning = self.g.gme_warning(emu)
            if warning:
                raise RuntimeError(warning.decode())
            return pcm
        finally:
            if hasattr(self.g, "fe2_set_trace"):
                self.g.fe2_set_trace(None)
            self.g.gme_delete(emu)

    @staticmethod
    def _check(error):
        if error:
            raise RuntimeError(error.decode())


def read_bank(path: Path) -> bytes:
    content = path.read_bytes()
    if content[:4] == b"NES\x1a":
        trainer = 512 if content[6] & 4 else 0
        offset = 16+trainer+14*0x4000
        return content[offset:offset+0x4000]
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gme", type=Path, required=True)
    parser.add_argument("--ffmpeg", default="/opt/homebrew/bin/ffmpeg")
    parser.add_argument("--encoder", type=Path, help="Optional tools/audio/encode_vorbis.c binary")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--output", type=Path, default=ROOT/"assets/original/audio")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bank = read_bank(args.rom)
    tracks = [t for t in TRACKS if args.only is None or t[0] in args.only]
    manifest_path = ROOT/"data/audio.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "source": "fe2 reconstructed bank014 original 6502 sound driver",
        "renderer": "Game Music Emu NSF NES APU emulation, NTSC",
        "sample_rate": RATE,
        "driver_sha256": hashlib.sha256(bank).hexdigest(),
        "music": {}, "sfx": {}}
    with tempfile.TemporaryDirectory(prefix="fe2-audio-render-") as tmp:
        tmp = Path(tmp)
        nsf = tmp/"fe2.nsf"
        nsf.write_bytes(build_nsf(bank))
        renderer = Renderer(args.gme, nsf)
        for name, request, seconds, kind, evidence in tracks:
            trace = tmp/(name+".trace")
            pcm = renderer.render(request, seconds, trace)
            loop = driver_loop(trace) if kind == "music" else None
            if kind == "music" and loop:
                end_sample = round(loop["end_seconds"]*RATE)
                pcm = pcm[:end_sample*2]
            elif not loop:
                # Preserve the audio filter tail; remove only >0.1s trailing silence.
                last = next((i for i in range(len(pcm)-1, -1, -1) if abs(pcm[i]) > 12), 0)
                end = min(len(pcm), ((last//2)+round(RATE*0.12))*2)
                pcm = pcm[:end]
            if max(map(abs, pcm), default=0) == 0:
                raise RuntimeError(f"Original request {request:02X} rendered silence")
            wav = tmp/(name+".wav")
            with wave.open(str(wav), "wb") as out:
                out.setnchannels(2)
                out.setsampwidth(2)
                out.setframerate(RATE)
                out.writeframes(pcm.tobytes())
            ogg = args.output/(name+".ogg")
            command = [args.ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav),
                       "-c:a", "vorbis", "-strict", "experimental", "-q:a", "5"]
            if loop:
                command += ["-metadata", f"LOOPSTART={round(loop['start_seconds']*RATE)}",
                            "-metadata", f"LOOPEND={len(pcm)//2}"]
            if args.encoder:
                command = [str(args.encoder), str(wav), str(ogg)]
                if loop:
                    command += [str(round(loop["start_seconds"]*RATE)), str(len(pcm)//2)]
                subprocess.run(command, check=True)
            else:
                subprocess.run(command+[str(ogg)], check=True)
            peak = max(map(abs, pcm))/32768
            data = {"path": "res://assets/original/audio/"+ogg.name,
                    "source_request": f"0x{request:02X}", "source_evidence": evidence,
                    "duration": round(len(pcm)/(RATE*2), 6),
                    "peak": round(peak, 6), "peak_dbfs": round(20*math.log10(peak), 3),
                    "bytes": ogg.stat().st_size, "loop": bool(loop),
                    "loop_offset": loop["start_seconds"] if loop else 0.0,
                    "loop_analysis": loop,
                    "default_enabled": "pending" not in evidence.lower(),
                    "mapping_status": "pending" if "pending" in evidence.lower() else "source_verified",
                    "manual_stop": name == "death"}
            manifest["music" if kind != "sfx" else "sfx"][name] = data
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
            print(name, json.dumps(data, ensure_ascii=False), flush=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")


if __name__ == "__main__":
    main()
