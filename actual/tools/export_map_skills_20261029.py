#!/usr/bin/env python3
"""Export production-rendered MAP footage with the exact recorded SFX events."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[2]
ACTUAL = ROOT / 'actual'
REPORT = ACTUAL / 'reports/map-skills-20261029'
OUT = ROOT / 'art-review/map-20261029/runtime'
SR = 44100
FFMPEG = '/opt/homebrew/bin/ffmpeg'
OXIPNG = '/opt/homebrew/bin/oxipng'


def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    visual = json.loads((REPORT / 'visual.json').read_text())
    manifest = json.loads((ACTUAL / 'data/sound_effects.json').read_text())
    audio = json.loads((REPORT / 'audio.json').read_text())
    entries = {**manifest['effects'], **manifest['gameplay_effects']}
    all_mix = np.zeros((round(visual['seconds'] * SR), 2), np.float32)
    temp = Path('/private/tmp/revenge-map-skills-movie-20261029')
    files = []
    for seg in visual['segments']:
        key = seg['key']
        mix = np.zeros((round(seg['seconds'] * SR), 2), np.float32)
        for cue in seg['sounds']:
            canonical = manifest['named_aliases'].get(cue['key'], cue['key'])
            entry = entries[canonical]
            if not entry.get('default_enabled', True):
                raise ValueError('Disabled playback cue: ' + cue['key'])
            path = ACTUAL / entry['path'].removeprefix('res://')
            samples, sr = sf.read(path, dtype='float32', always_2d=True)
            if sr != SR:
                gcd = math.gcd(sr, SR)
                samples = resample_poly(samples, SR // gcd, sr // gcd)
            if samples.shape[1] == 1:
                samples = np.repeat(samples, 2, axis=1)
            start = round(cue['time'] * SR)
            length = min(len(samples), len(mix) - start)
            if length > 0:
                mix[start:start + length] += samples[:length] * .65
        # The game does not block input for a sound tail. Export clips stay at
        # the exact visual duration and gently end only their final 15 ms.
        fade = min(round(.015 * SR), len(mix))
        mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
        assert np.isfinite(mix).all() and np.abs(mix).max() < 1
        start = round(seg['start_seconds'] * SR)
        all_mix[start:start + len(mix)] = mix
        wav = temp / (key + '.wav')
        sf.write(wav, mix, SR, subtype='PCM_16')
        output = OUT / (key + '.mp4')
        run([FFMPEG, '-y', '-loglevel', 'error', '-framerate', '30',
             '-start_number', str(seg['frame_start']), '-i',
             str(temp / 'frame-%05d.png'), '-i', str(wav),
             '-frames:v', str(seg['frames']), '-c:v', 'libx264', '-preset',
             'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
             '-b:a', '160k', '-movflags', '+faststart', str(output)])
        files.append({'purpose': 'production engine clip with SFX', 'file': output.name,
                      'bytes': output.stat().st_size, 'seconds': seg['seconds'],
                      'sha256': sha(output)})
        close = OUT / (key + '-close.mp4')
        run([FFMPEG, '-y', '-loglevel', 'error', '-i', str(output), '-vf',
             'crop=460:360:470:100,scale=920:720:flags=neighbor', '-c:v',
             'libx264', '-preset', 'medium', '-crf', '17', '-c:a', 'copy',
             '-movflags', '+faststart', str(close)])
        files.append({'purpose': 'nearest-neighbor review crop of the same engine clip',
                      'file': close.name, 'bytes': close.stat().st_size,
                      'seconds': seg['seconds'], 'sha256': sha(close)})
        poster = OUT / (key + '-close.jpg')
        run([FFMPEG, '-y', '-loglevel', 'error', '-i', str(close), '-ss', '0.6',
             '-frames:v', '1', '-q:v', '2', str(poster)])
        files.append({'purpose': 'actual video frame poster', 'file': poster.name,
                      'width': 920, 'height': 720, 'bytes': poster.stat().st_size,
                      'sha256': sha(poster)})
        case = key.replace('_', '-')
        for suffix in ['menu', 'target-free', 'target-third', 'motion-11', 'motion-18']:
            source = REPORT / (case + '-' + suffix + '.png')
            target = OUT / source.name
            shutil.copyfile(source, target)
            run([OXIPNG, '-q', '-o', '3', '--strip', 'safe', str(target)])
            files.append({'purpose': 'production engine screenshot', 'file': target.name,
                          'width': 1280, 'height': 592, 'bytes': target.stat().st_size,
                          'sha256': sha(target)})
    wav = temp / 'map-runtime-all.wav'
    sf.write(wav, all_mix, SR, subtype='PCM_16')
    output = OUT / 'map-runtime-all.mp4'
    run([FFMPEG, '-y', '-loglevel', 'error', '-framerate', '30', '-i',
         str(temp / 'frame-%05d.png'), '-i', str(wav), '-frames:v',
         str(visual['frames']), '-c:v', 'libx264', '-preset', 'medium',
         '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
         '-movflags', '+faststart', str(output)])
    files.append({'purpose': 'five-case production engine reel with SFX',
                  'file': output.name, 'bytes': output.stat().st_size,
                  'seconds': visual['seconds'], 'sha256': sha(output)})
    close = OUT / 'map-runtime-all-close.mp4'
    run([FFMPEG, '-y', '-loglevel', 'error', '-i', str(output), '-vf',
         'crop=460:360:470:100,scale=920:720:flags=neighbor', '-c:v',
         'libx264', '-preset', 'medium', '-crf', '17', '-c:a', 'copy',
         '-movflags', '+faststart', str(close)])
    files.append({'purpose': 'nearest-neighbor review crop of five-case reel',
                  'file': close.name, 'bytes': close.stat().st_size,
                  'seconds': visual['seconds'], 'sha256': sha(close)})
    signals = []
    for track in audio['tracks']:
        p = ACTUAL / track['path'].removeprefix('res://')
        a, sr = sf.read(p, dtype='float32', always_2d=True)
        mono = a.mean(axis=1)
        block = 441
        envelope = np.sqrt(np.mean(mono[:len(mono)//block*block].reshape(-1, block)**2, axis=1))
        active = np.flatnonzero(envelope > max(envelope.max() * .08, 1e-5))
        spectrum = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) ** 2
        signals.append({'key': track['key'], 'sha256': sha(p),
                        'finite': bool(np.isfinite(a).all()),
                        'clipped_samples': int((np.abs(a) >= 1).sum()),
                        'attack_above_minus22_relative_db_seconds': int(active[0]) * block / sr,
                        'active_end_seconds': (int(active[-1]) + 1) * block / sr,
                        'strongest_fft_bin_energy_fraction': float(spectrum.max() / spectrum.sum()),
                        'duration': len(a)/sr})
        shutil.copyfile(p, OUT / p.name)
    dump(REPORT / 'audio-signal-review.json', {'human_listening': False, 'tracks': signals,
         'scope': 'No clipping/nonfinite samples; short event envelope and spectral concentration measured. These checks do not certify artistic quality.'})
    dump(OUT / 'manifest.json', {'scope': visual['scope'], 'fps': 30,
         'game_sfx_gain': .65, 'background_music': False, 'sound_events': visual['segments'],
         'files': files, 'audio': audio['tracks'],
         'audio_export': 'Same gameplay gain and recorded cue times. Clip endings have a 15ms fade; game audio tails never delay input.'})
    print(json.dumps({'files': len(files), 'seconds': visual['seconds'],
                      'movie_bytes': output.stat().st_size, 'signal_review': signals}, indent=2))


if __name__ == '__main__':
    main()
