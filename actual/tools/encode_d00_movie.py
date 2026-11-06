from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'actual/reports/d00-prologue-20261026'
movie = json.loads((OUT / 'movie.json').read_text())
score = json.loads((ROOT / 'actual/data/soundtrack.json').read_text())
sfx = json.loads((ROOT / 'actual/data/sound_effects.json').read_text())
duration = movie['seconds']
video_name = 'D00-runtime-small-cast-v2.mp4' if (OUT / 'small-cast.json').exists() else 'D00-runtime-no-inset.mp4' if (OUT / 'no-inset.json').exists() else 'D00-runtime.mp4'

def local(path):
    return str(ROOT / 'actual' / path.removeprefix('res://'))

command = ['/opt/homebrew/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
           '-framerate', '30', '-i', movie['frame_directory'] + 'frame-%05d.png',
           '-stream_loop', '-1', '-i', local(score['tracks']['rm_prologue']['path'])]
filters = [f'[1:a]atrim=0:{duration},asetpts=PTS-STARTPTS,volume=0.5,afade=t=out:st={duration-1}:d=1[bg]']
tracks = ['[bg]']
used = []
for event in movie['sounds']:
    cue = event['cue']
    if cue not in ['rm_sfx_06', 'rm_sfx_03', 'rm_sfx_23']:
        continue
    entry = sfx['effects'][cue]
    index = len(used) + 2
    command += ['-i', local(entry['path'])]
    delay = round(event['seconds'] * 1000)
    label = f'cue{index}'
    filters.append(f'[{index}:a]volume=0.65,adelay={delay}:all=1[{label}]')
    tracks.append(f'[{label}]')
    used.append(event)
filters.append(''.join(tracks) + f'amix=inputs={len(tracks)}:normalize=0:duration=first,alimiter=limit=0.95[mix]')
command += ['-filter_complex', ';'.join(filters), '-map', '0:v:0', '-map', '[mix]',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '160k', '-t', str(duration), '-movflags', '+faststart', str(OUT / video_name)]
subprocess.run(command, check=True)
movie['delivery_video'] = video_name
movie['audio_method'] = 'Offline mix from the actual runtime cue log and the same rm_prologue / spell / impact / curtain resources, with game music/SFX gains. Not a microphone capture.'
movie['mixed_events'] = used
movie['bytes'] = (OUT / video_name).stat().st_size
(OUT / 'movie.json').write_text(json.dumps(movie, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'video': str(OUT / video_name), 'seconds': duration, 'bytes': movie['bytes'], 'events': used}))
