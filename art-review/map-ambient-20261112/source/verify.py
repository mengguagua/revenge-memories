from pathlib import Path
import hashlib,json,subprocess,shutil
from PIL import Image

review=Path(__file__).resolve().parents[1]
project=review.parents[1]
assets=project/'actual/assets/map-ambient-20261112'
usage={'sheen':'Moving short water crests, 16px water cells','ripple':'Calm cave/pool/marsh/salt water rings, clipped to live water cells','foam':'Four shoreline orientations with 32 frames each','flame':'Animated flame on existing cave braziers','torch':'S11 wall-mounted bracket and flame','lamplight':'Gentle light on existing ritual lamps, no flame added','shadow':'Ground-projected slow moving cloud shadow'}
asset_rows=[]
for name,note in usage.items():
 p=assets/(name+'.png')
 with Image.open(p) as im:size=list(im.size)
 asset_rows.append({'name':name,'use':note,'size':size,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
validation=[]
for mode in ['map','phone']:
 report=json.loads((review/f'{mode}-verification.json').read_text())
 assert report['passed'] and len(report['maps'])==40
 for row in report['maps']:
  assert row['source_unchanged'] and row['game_state_unchanged']
  assert row['presentation_revision']=='all40-reduced-treetop-20261112'
  source=project/'actual'/row['source'].removeprefix('res://')
  assert hashlib.sha256(source.read_bytes()).hexdigest()==row['source_sha256']
  video=review/'media'/f'{row["code"]}-{mode}.mp4'
  d=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','quiet','-show_streams','-of','json',str(video)]))['streams'][0]
  assert d['codec_name']=='h264' and int(d['nb_frames'])==96 and float(d['duration'])==8
  assert video.stat().st_size==row['video_bytes']
  validation.append({'code':row['code'],'view':mode,'size':[d['width'],d['height']],'seconds':8,'frames':96})
assert len(list((review/'media').glob('*-map.mp4')))==40
assert len(list((review/'media').glob('*-phone.mp4')))==40
shutil.copyfile('/private/tmp/map-ambient-20261112/play-check.json',review/'play-verification.json')
play=json.loads((review/'play-verification.json').read_text())
assert play['passed'] and len(play['checks'])==40
(review/'asset-manifest.json').write_text(json.dumps({'source':'https://github.com/patch-gg/pixelfx','commit':'a84159688af3ca37a4be05a0d422b94451b2e24e','license':'MIT','runtime':'Godot sprite-sheet rendering; PixelFX JavaScript is used only by the offline exporter','assets':asset_rows},ensure_ascii=False,indent=2)+'\n')
(review/'verification-summary.json').write_text(json.dumps({'passed':True,'date':'2026-11-12','scope':'40 battle maps, all five chapters','tree_change':'Upper crown only, total native excursion reduced from2px to1px; lower crown/trunk fixed','geometry':'Live water categories and bridge updates; salt/sand wind only on corresponding outdoor ground; no effect geometry writes','source_saves_unchanged':True,'game_state_unchanged':True,'phone_layout':'Godot 1334x750 layout, integer native scale3; not physical iPhone footage','interaction_checks':'40 actual keyboard play checks; movement, objectives, wait, end turn. Not full campaign completion.','browser_checks':'80 local MP4 decodes,40 map switches,play/pause/frame-step,390/667-width layout,text-safe controls','videos':validation},ensure_ascii=False,indent=2)+'\n')
print('PASS 80 videos,8seconds,96frames;40 unchanged source saves;40 ordinary-input play checks;7 native-pixel atlases')
