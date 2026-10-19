from pathlib import Path
import json, subprocess

V = Path(__file__).resolve().parents[1]; R = V.parent
data = json.loads((R / 'demos/gallery-data.json').read_text())
actions = {x['id']: x for x in data['actions']}
clips = []
for side in ['enemy']:
    normal = 'original_class_8_normal' if side == 'ally' else 'original_class_8_enemy_normal'
    for key, repeats in [('reaction-idle', 1), (normal, 2),
                          (f'class_8_{side}_levin', 1),
                          (f'class_8_{side}_levin_far_enemy', 1),
                          ('reaction-hit', 1), ('reaction-miss', 1)]:
        action = actions[f'professions-class-8-{side}-battle--{key}']
        p = (R / action['video']).resolve()
        for _ in range(repeats):
            clips.append((p, action))
lines = []
for path, action in clips:
    lines += ["file '" + str(path) + "'", f'duration {len(action["frames"])/action["fps"]:.12f}']
source = V / 'overview-inputs.txt'; source.write_text('\n'.join(lines) + '\n')
# Ordinary sword and lightning shots have distinct source viewport heights.
# Pad to a common canvas; do not stretch or crop their native comparisons.
command = ['/opt/homebrew/bin/ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
    '-f', 'concat', '-safe', '0', '-i', str(source), '-vf',
    'pad=1224:712:(ow-iw)/2:(oh-ih)/2:color=0x0e151a,setsar=1',
    '-fps_mode', 'passthrough', '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(V / 'overview.mp4')]
subprocess.run(command, check=True)
probe = json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe', '-v', 'error',
    '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames,width,height,r_frame_rate',
    '-of', 'json', str(V / 'overview.mp4')], text=True))['streams'][0]
expected = sum(len(action['frames']) for _, action in clips)
assert int(probe['nb_frames']) == expected
(V / 'overview-report.json').write_text(json.dumps({'clips': len(clips),
    'expected_frames': expected, 'probe': probe, 'scaling': 'No scaling. Padding only.',
    'bytes': (V / 'overview.mp4').stat().st_size}, indent=2) + '\n')
print(json.dumps({'overview_frames': expected, 'clips': len(clips), 'pass': True}))
