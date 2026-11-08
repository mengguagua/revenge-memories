#!/usr/bin/env python3
"""Author and render short, isolated spell cues with the installed MLX model."""

import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from dataclasses import dataclass

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / ROOT.name
AUDIO = ROOT / "audio"
MODEL = Path("/Users/gcc/gaocc/project/StableAudio3SmallSFX/optimized/mlx")
SAMPLE_RATE = 44100
NEGATIVE = (
    "music, melody, beat, speech, whisper, vocals, crowd, ambient background, "
    "gunshot, extra attacks, repeating sound, long reverb, distortion"
)


@dataclass(frozen=True)
class Voice:
    title: str
    material: str
    fundamental: float
    band: tuple[int, int]
    charge: str
    release: str
    resolve: str
    seconds: tuple[float, float, float]


VOICES = {
    "levin": Voice("雷剑", "arc", 264, (750, 8200),
        "Electric charge crawling along a narrow steel blade, tight metallic tension",
        "One thin steel sweep dragging dry electrical fizz",
        "A sharp electrified blade crack with a brief resonant steel edge", (.42, .25, .52)),
    "fire": Voice("火球", "flame", 123, (170, 6700),
        "Compact turbulent fire forming in the palm, rising ember crackle",
        "One fast dense red fireball rush with a short fluttering flame tail",
        "A concentrated hot flame pop with a quick ember decay", (.42, .28, .59)),
    "thunder": Voice("雷电", "arc", 101, (230, 9600),
        "Air ionizing, fine dry static drawn into one point",
        "One very brief descending electrical leader hiss",
        "Single branching lightning crack, short controlled thunder body and dry static decay", (.34, .20, .75)),
    "ragnarok": Voice("诸神黄昏", "flame", 67, (95, 5700),
        "Heavy molten pressure gathering, low fire with a strained ember hiss",
        "A low sweeping rush of heat travelling along the ground",
        "One broad magma eruption, dense flame roar and quickly settling hot grit", (.64, .54, 1.05)),
    "holy": Voice("圣光", "glass", 642, (1050, 7600),
        "Small clustered light motes opening with an airy glass resonance",
        "Soft flutter of luminous wings through air, one gathered gesture",
        "A short gentle crystalline pressure pulse, luminous and compact", (.41, .43, .57)),
    "wind": Voice("风刃", "steel", 392, (1100, 11500),
        "A narrow curl of wind drawing in, light hiss without a tone",
        "One fast clean blade-shaped air slice",
        "Brief sharp air shear and a dry dispersing gust", (.29, .22, .44)),
    "rain": Voice("箭雨", "steel", 770, (1550, 10500),
        "A small group of thin metal points gathering in a tight upward sweep",
        "One downward sweep of many thin arrow whistles, tightly clustered",
        "A single tight cluster of dry silver impacts resolving together", (.38, .35, .55)),
    "halo": Voice("光环", "glass", 418, (680, 6500),
        "A circular warm resonant halo opening and moving gently outward",
        "One rotating airy brass overtone sweep",
        "A soft expanding ring of warm light breaking into quickly fading resonant fragments", (.55, .38, .80)),
    "wisp": Voice("鬼火", "shade", 286, (510, 6900),
        "A small cold flame flicker, dry airy fizz and hollow violet resonance",
        "One lightweight drifting ghost flame swish",
        "A crisp cold-flame puff dispersing into thin dry air", (.38, .30, .54)),
    "slime": Voice("史莱姆", "gel", 154, (140, 3400),
        "Viscous gel stretching and compressing, one short elastic squelch",
        "One sticky soft blob slinging through air",
        "A dense wet elastic splat, tiny collapsing bubbles, short clean decay", (.49, .40, .73)),
    "death": Voice("死亡", "shade", 78, (115, 4700),
        "Low shadow pressure drawing inwards, granular breath without voice",
        "A restrained hollow rushing shadow",
        "A single weighted vacuum implosion followed by a dark dry decay", (.60, .39, .78)),
    "medusa": Voice("美杜莎", "glass", 284, (760, 8800),
        "Tense thin crystal hiss forming in a dark focus",
        "A slithering high crystalline sweep, no animal voice",
        "A single brittle crystalline fracture and short hiss", (.49, .36, .74)),
    "drain": Voice("吸血", "shade", 194, (280, 4300),
        "Short dark red pressure being drawn inward, close dry air",
        "One tight reverse siphon sweep, soft and controlled",
        "One rounded low absorption pulse and thin dissolving residue", (.39, .31, .57)),
    "heal": Voice("恢复与治疗", "glass", 538, (800, 6200),
        "Gentle warm restorative aura beginning with a soft breath of light", "",
        "Single soothing rising resonance, warm glass and soft clean decay", (.43, 0, .68)),
    "warp": Voice("传送", "shade", 247, (480, 7300),
        "Small pressure fold in the air, clean upward suction", "",
        "One airy spatial snap blooming outward and resolving quickly", (.35, 0, .65)),
    "summon": Voice("召唤", "earth", 112, (140, 6800),
        "Quiet granular rising portal pressure and muted dust", "",
        "A compact summoning gate opening with a low sand-like shiver", (.37, 0, .74)),
    "expel": Voice("驱邪", "glass", 358, (510, 8100),
        "Bright directed pressure collecting in a short clean sweep", "",
        "Single cleansing dispersal, quick radiant snap and dust-like decay", (.31, 0, .65)),
    "phantom": Voice("幻影", "shade", 312, (380, 6200),
        "Thin mirage shimmer and a quiet hollow breath of air", "",
        "One soft phase-split flutter resolving into a short spectral tail", (.40, 0, .68)),
    "quake": Voice("地震", "earth", 58, (85, 4800),
        "Short dry stone tension and deep ground movement", "",
        "One compact ground rupture with granular rocks and fast bass decay", (.50, 0, .91)),
    "fieldfire": Voice("焰环", "flame", 91, (145, 7800),
        "A small concentrated flame seed lighting, contained crackling rush", "",
        "A single wide circular ignition, fire rushing out and then quick embers", (.34, 0, .82)),
    "suncrown": Voice("日冠聚光", "glass", 496, (530, 8800),
        "Tight solar ray focus, warm granular light becoming more intense", "",
        "A single concentrated searing beam pulse with a brief radiant afterring", (.47, 0, .76)),
    "rockspit": Voice("碎岩喷吐", "earth", 145, (280, 9300),
        "Grit collecting before a short pressurized rock burst", "",
        "A tight group of stone fragments landing together with a brief gritty decay", (.28, 0, .58)),
    "rotbreath": Voice("蚀息", "shade", 94, (130, 5600),
        "A low coarse gathering air-pressure hiss with no vocalization", "",
        "One concentrated dark aerosol rush, short grainy breath-like decay", (.35, 0, .62)),
    "magicblade": Voice("魔剑", "steel", 325, (770, 8900),
        "Short steel tension and subdued magic resonance", "",
        "One sharp enchanted sword release with a brief metallic shiver", (.31, 0, .54)),
}

TAILS = {
    "holy": (.53, "Tiny warm glass and wing-like air motes fading, soft single diffuse tail"),
    "rain": (.42, "Fine silver flecks falling quiet, a light dry fizz, no additional arrow hit"),
    "drain": (.49, "One quiet inward burgundy air ripple resolving, no extra hit"),
}
PHASES = ("charge", "release", "resolve")


def specs():
    for name, voice in VOICES.items():
        for phase, duration in zip(PHASES, voice.seconds):
            if duration:
                yield f"{name}-{phase}", name, phase, duration, getattr(voice, phase)
        if name in TAILS:
            duration, prompt = TAILS[name]
            yield f"{name}-tail", name, "tail", duration, prompt


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def band_noise(noise, low, high):
    freq = np.fft.rfftfreq(len(noise), 1 / SAMPLE_RATE)
    safe = np.maximum(freq, 1e-6)
    weight = (1 + (low / safe) ** 8) ** -.5 * (1 + (safe / high) ** 8) ** -.5
    weight[0] = 0
    shaped = np.fft.irfft(np.fft.rfft(noise) * weight, len(noise))
    return shaped / max(float(shaped.std()), 1e-8)


def gesture(voice, phase, duration, seed):
    """Compose one attack/decay guide. The model supplies its material texture."""
    n = round(duration * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    u = t / duration
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, n)
    low, high = voice.band
    hiss = band_noise(noise, low, high)
    pressure = band_noise(noise, max(75, low * .33), min(high * .55, 2400))
    rise, drop = {"charge": (.095, 2.7), "release": (.030, 4.0),
                  "resolve": (.013, 4.6), "tail": (.13, 3.7)}[phase]
    contour = (1 - np.exp(-u / rise)) * np.exp(-u * drop)
    contour *= np.minimum(1, (1 - u) / .14) ** 2
    pitch = voice.fundamental * (.76 + .88 * u if phase == "charge" else 1.36 - .60 * u)
    angle = 2 * np.pi * np.cumsum(pitch) / SAMPLE_RATE
    mode = voice.material
    if mode == "flame":
        grain = .78 + .22 * np.sin(2 * np.pi * (47 * t + 25 * t * t))
        body = .63 * pressure + .28 * hiss * grain + .16 * np.sin(angle) * np.exp(-u * 7)
    elif mode == "arc":
        buzz = np.tanh(2.3 * np.sin(angle * 2.14))
        grain = .42 + .58 * np.abs(np.sin(angle * .38 + 1.2 * np.sin(angle * .29))) ** 3
        body = .65 * hiss * grain + .27 * pressure + .14 * buzz
        if voice.title == "雷剑":
            body += .24 * np.sin(angle * 4.27) * np.exp(-u * 6)
    elif mode == "glass":
        partials = np.sin(angle) + .42 * np.sin(2.08 * angle) + .23 * np.sin(3.77 * angle)
        body = .44 * hiss + .16 * pressure + .40 * partials * np.exp(-u * 1.8)
    elif mode == "steel":
        steel = np.sin(angle * 3.31) + .39 * np.sin(angle * 4.76)
        body = .71 * hiss + .21 * pressure + .20 * steel * np.exp(-u * 5.8)
    elif mode == "gel":
        wobble = angle + .45 * np.sin(angle * .27)
        body = .40 * pressure + .21 * hiss * (1 - .7 * u) + .49 * np.sin(wobble)
        body += .19 * np.sin(2.31 * wobble) * np.exp(-u * 3)
    elif mode == "earth":
        body = .68 * pressure + .35 * hiss * (.65 + .35 * np.sin(angle * 1.9) ** 2)
        body += .21 * np.sin(angle) * np.exp(-u * 6)
    else:
        body = .56 * pressure + .32 * hiss + .22 * np.sin(angle + np.sin(angle * 1.41))
    cue = body * contour
    cue -= cue.mean()
    cue *= contour ** .22
    cue *= .68 / max(float(np.abs(cue).max()), 1e-8)
    return cue.astype(np.float32), contour


def source_paths(key):
    folder = AUDIO / "sources"
    return folder / f"{key}-guide.wav", folder / f"{key}-model.wav", folder / f"{key}.json"


def worker(key):
    wanted = {row[0]: row for row in specs()}
    _, name, phase, duration, direction = wanted[key]
    guide_path, raw, receipt = source_paths(key)
    seed = 2026110700 + list(wanted).index(key)
    if raw.is_file() and receipt.is_file():
        previous = json.loads(receipt.read_text())
        if previous.get("seed") == seed and previous.get("sha256") == digest(raw):
            return

    files = ("t5gemma_f16.npz", "dit_sm-sfx_f16.npz",
             "same_s_decoder_f32.npz", "same_s_encoder_f32.npz")
    for name_on_disk in files:
        if not (MODEL / "models/mlx" / name_on_disk).is_file():
            raise FileNotFoundError(f"Required local weight is missing: {name_on_disk}")
    sys.path.insert(0, str(MODEL / "scripts"))
    import sa3_mlx

    guide_path.parent.mkdir(parents=True, exist_ok=True)
    cue, _ = gesture(VOICES[name], phase, duration, seed)
    sf.write(guide_path, np.column_stack((cue, cue)), SAMPLE_RATE, subtype="PCM_16")
    temporary = raw.with_suffix(".partial.wav")

    def save_float(path, samples, sample_rate=SAMPLE_RATE):
        if not np.isfinite(samples).all() or np.max(np.abs(samples)) < 1e-4:
            raise ValueError(f"Invalid model samples for {key}")
        sf.write(path, samples.T, sample_rate, subtype="FLOAT")

    sa3_mlx.save_wav = save_float
    prompt = (
        "TrackType: SFX. " + direction + ". Single isolated fantasy strategy game sound, "
        "one compact gesture, dry close perspective and quick clean fade. No music or voice."
    )
    args = ["sa3_mlx.py", "--dit", "sm-sfx", "--decoder", "same-s", "--dit-dtype", "fp32",
            "--seconds", "2.5", "--steps", "8", "--cfg", "2", "--seed", str(seed),
            "--init-audio", str(guide_path), "--init-noise-level", ".48",
            "--prompt", prompt, "--negative-prompt", NEGATIVE, "--out", str(temporary)]
    started = time.monotonic()
    sys.argv = args
    sa3_mlx.main()
    temporary.replace(raw)
    write_json(receipt, {
        "id": key, "model": "Stable Audio 3 sm-sfx / same-s (MLX)", "offline": True,
        "seed": seed, "seconds": 2.5, "steps": 8, "cfg": 2, "dit_dtype": "fp32",
        "noise_level": .48, "prompt": prompt, "negative_prompt": NEGATIVE,
        "guide": str(guide_path.relative_to(ROOT)), "guide_sha256": digest(guide_path),
        "source": str(raw.relative_to(ROOT)), "sha256": digest(raw),
        "wall_seconds": round(time.monotonic() - started, 2),
    })


def rms(samples):
    return float(np.sqrt(np.mean(np.square(samples))))


def db(value):
    return round(20 * math.log10(max(value, 1e-9)), 2)


def master(key, family, phase, duration, direction):
    guide_path, raw, receipt_path = source_paths(key)
    receipt = json.loads(receipt_path.read_text())
    if digest(raw) != receipt["sha256"] or digest(guide_path) != receipt["guide_sha256"]:
        raise ValueError(f"Source digest mismatch: {key}")
    guide, rate = sf.read(guide_path, dtype="float32", always_2d=True)
    generated, source_rate = sf.read(raw, dtype="float32", always_2d=True)
    if rate != SAMPLE_RATE or source_rate != SAMPLE_RATE:
        raise ValueError(f"Unexpected sample rate: {key}")
    guide = guide.mean(axis=1)
    n = len(guide)
    model = generated.mean(axis=1)[:n].astype(np.float64)
    model -= model.mean()
    freq = np.fft.rfftfreq(n, 1 / rate)
    highpass = (1 + (72 / np.maximum(1e-6, freq)) ** 8) ** -.5
    lowpass = (1 + (freq / 13300) ** 10) ** -.5
    model = np.fft.irfft(np.fft.rfft(model) * highpass * lowpass, n)
    _, contour = gesture(VOICES[family], phase, duration, receipt["seed"])
    model *= (contour / max(float(contour.max()), 1e-8)) ** .62
    if not np.isfinite(model).all() or rms(model) < 1e-5:
        raise ValueError(f"Inactive model texture: {key}")
    model *= rms(guide) / rms(model)
    # A soft cap on exceptional model transients keeps a single intentional gesture.
    cap = max(.14, float(np.abs(guide).max()))
    model = cap * np.tanh(model / cap)
    mix = .63 * guide + .37 * model
    mix -= mix.mean()
    edge = min(round(rate * .006), n // 5)
    tail = min(round(rate * .058), n // 4)
    mix[:edge] *= np.sin(np.linspace(0, np.pi / 2, edge)) ** 2
    mix[-tail:] *= np.cos(np.linspace(0, np.pi / 2, tail)) ** 2
    goal_db = {"charge": -28, "release": -25, "resolve": -21, "tail": -31}[phase]
    peak_db = {"charge": -12, "release": -10, "resolve": -7, "tail": -16}[phase]
    mix *= min(10 ** (goal_db / 20) / rms(mix),
               10 ** (peak_db / 20) / float(np.max(np.abs(mix))))
    out = AUDIO / "masters" / f"{key}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, mix, rate, subtype="PCM_16")
    signal, _ = sf.read(out, dtype="float32")
    window = 220
    blocks = signal[:len(signal) // window * window].reshape(-1, window)
    levels = np.sqrt(np.mean(blocks ** 2, axis=1))
    active = np.flatnonzero(levels >= max(.012 * float(levels.max()), 10 ** (-52 / 20)))
    if not len(active) or not np.isfinite(signal).all() or np.max(np.abs(signal)) >= .8:
        raise ValueError(f"Invalid mastered output: {key}")
    track = {
        "id": key, "family": family, "name": VOICES[family].title, "phase": phase,
        "design": direction, "duration": round(len(signal) / rate, 6), "sample_rate": rate,
        "channels": 1, "bytes": out.stat().st_size, "sha256": digest(out),
        "peak_dbfs": db(float(np.max(np.abs(signal)))), "rms_dbfs": db(rms(signal)),
        "active_onset_ms": round(float(active[0] * window / rate * 1000), 2),
        "last_10ms_rms_dbfs": db(rms(signal[-round(rate * .01):])),
        "model_source": str(receipt_path.relative_to(ROOT)),
        "master": str(out.relative_to(ROOT)),
    }
    return track, out


def publish():
    tracks = []
    bank = {}
    for spec in specs():
        track, path = master(*spec)
        tracks.append(track)
        bank[track["id"]] = {
            "duration": track["duration"],
            "wav": base64.b64encode(path.read_bytes()).decode("ascii"),
        }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "spell-audio-bank.js").write_text(
        "window.PIXELFX_SOUND_BANK=" + json.dumps(bank, separators=(",", ":")) + ";\n"
    )
    write_json(OUT / "qa/audio-generation.json", {
        "model": "Local Stable Audio 3 sm-sfx / same-s (MLX)",
        "voices": len(VOICES), "cues": len(tracks), "offline": True,
        "method": "Original single-gesture guides plus 37% model texture before final gain",
        "total_pcm_bytes": sum(track["bytes"] for track in tracks),
        "tracks": tracks,
    })
    print(f"MASTERED {len(tracks)} cues across {len(VOICES)} sound designs", flush=True)


def generate(only):
    expected = {row[0] for row in specs()}
    if set(only) - expected:
        raise ValueError(f"Unknown cues: {set(only) - expected}")
    logs = AUDIO / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    for key, *_ in specs():
        if only and key not in only:
            continue
        log_path = logs / f"{key}.log"
        with log_path.open("w") as log:
            run = subprocess.run([sys.executable, "-B", str(__file__), "worker", key],
                                 stdout=log, stderr=subprocess.STDOUT)
        if run.returncode:
            raise RuntimeError(log_path.read_text()[-4500:])
        print(f"GENERATED {key}", flush=True)
    if not only:
        publish()


if __name__ == "__main__":
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      PYTHONDONTWRITEBYTECODE="1")
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("generate", "worker", "publish"))
    parser.add_argument("keys", nargs="*")
    args = parser.parse_args()
    if args.mode == "worker":
        worker(args.keys[0])
    elif args.mode == "generate":
        generate(args.keys)
    else:
        publish()
