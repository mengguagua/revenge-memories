"""Publish only the spear review and hero world-shadow comparison, then export."""
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import json,os,sys,hashlib,subprocess,shutil
V=Path(__file__).resolve().parents[1];R=V.parent;REV=V.name;OLD=R/'archer-spearman-map-review-20261018'
sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export,render_frame
G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((R/'demos/gallery-data.json').read_text());inventory=[];checks=[]
for key in ['class-6-ally','class-6-enemy']:
 base=R/f'professions/{key}/maps';O=V/'deliverables'/key;mp=base/'frame_mapping.json'
 if not (V/'source'/f'{key}-mapping-before.json').exists():shutil.copy2(mp,V/'source'/f'{key}-mapping-before.json')
 d=json.loads(mp.read_text());d.update(revision=REV,status='awaiting_user_review',runtime_integrated=False,review_note='枪兵：正面脸、单根长枪与连续裸露持枪手臂；左右腿分清支撑、抬脚与前跨。')
 for s in d['scenarios']:
  kind='walk' if s['id']=='tactical-walk' else 'idle';count=8 if kind=='walk' else 1 if s['id']=='story' else 6
  frames=[]
  for i in range(count):
   p=O/f'{kind}-{i:02}.png';subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(p)],check=True)
   image=Image.open(p).convert('RGBA');assert list(image.size)==s['output_frame_size'];assert set(image.getchannel('A').getdata())=={0,255}
   colors={c for c in image.getdata() if c[3]};assert len(colors)==4
   rec=dict(s['frame_mapping'][i]);rec.update(path=os.path.relpath(p,base),output_path=os.path.relpath(p,base),size=list(image.size),bytes=p.stat().st_size,sha256=sha(p),visible_bounds=list(image.getbbox()),art_revision=REV,construction='Built-in ImageGen layers; native registration, occlusion and limb composition.',generation_record=os.path.relpath(V/'README.md',base));frames.append(rec)
   inventory.append({'path':str(p.relative_to(R)),'purpose':key+' '+s['id'],'dimensions':list(image.size),'bytes':p.stat().st_size,'sha256':sha(p)})
  atlas=O/('idle-00.png' if s['id']=='story' else f'{kind}-atlas.png')
  if s['id']!='story':run(*[O/f'{kind}-{i:02}.png' for i in range(count)],'+append',atlas)
  note='待机：脸朝正前方，头身与双脚固定；一根完整长枪和连续的持枪裸臂按原作偏移，另一只手臂固定。' if kind=='idle' else '左右行走：头与躯干固定，保留原有手臂和长枪动作，近侧腿与远侧腿交替前后；向上、向下保持原稿。'
  if s['id']=='story':note='友军剧情仅同款待机首帧静止形象。'
  s.update(revision=REV,frame_mapping=frames,output_atlas=os.path.relpath(atlas,base),output_atlas_bytes=atlas.stat().st_size,review_note=note,adaptation_note=note,motion_review={'reference':str((V/'README.md').relative_to(R)),'fixed_and_moving_parts':note})
 dump(mp,d)
 # Native aliases, fixed face/body/feet and exact side mirroring.
 images={i:Image.open(O/f'idle-{i:02}.png').convert('RGBA') for i in range(6)}
 for a,b in [(0,4),(1,3),(1,5)]:assert images[a].tobytes()==images[b].tobytes()
 fixed=Image.open(V/'layers/idle-fixed.png').convert('RGBA')
 for box in [(30,16,59,41),(49,46,66,62),(28,66,65,80)]:
  assert all(images[0].getpixel((x,y))==images[i].getpixel((x,y)) for i in [1,2] for y in range(box[1],box[3]) for x in range(box[0],box[2]) if fixed.getpixel((x,y))[3]),(key,box)
 for a,b in [(2,6),(3,7)]:
  x=Image.open(O/f'walk-{a:02}.png').convert('RGBA');y=Image.open(O/f'walk-{b:02}.png').convert('RGBA');assert x.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==y.tobytes()
 for i in [0,1,4,5]:assert Image.open(O/f'walk-{i:02}.png').convert('RGBA').tobytes()==Image.open(OLD/f'deliverables/{key}/walk-{i:02}.png').convert('RGBA').tobytes()
 a=Image.open(O/'walk-02.png').convert('RGBA');b=Image.open(O/'walk-03.png').convert('RGBA');assert a.crop((51,31,76,55)).tobytes()==b.crop((51,31,76,55)).tobytes();assert a.crop((34,78,83,96)).tobytes()!=b.crop((34,78,83,96)).tobytes()
 checks.append({'key':key,'native_idle_aliases':True,'face_free_arm_feet_fixed':True,'side_head_fixed':True,'side_legs_differ':True,'same_phase_mirror':True,'up_down_unchanged':True,'palette_colors':4})
dump(V/'image-inventory.json',inventory)
data=build();allowed=lambda p:p.startswith('professions-class-6-') and '-maps-' in p or p=='hunapu-maps-world'
old={a['id']:a for a in before['actions']};assert all(a['contentDigest']==old[a['id']]['contentDigest'] for a in data['actions'] if not allowed(a['profile']))
targets=[a for a in data['actions'] if allowed(a['profile'])];args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False)
reports=[]
for a in targets:reports.append(export(data,a,args));print(a['id'],flush=True)
data=build();lookup={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']};order=[]
for key in ['class-6-ally','class-6-enemy']:
 prefix='professions-'+key+'-maps-';order.extend([prefix+'tactical-idle--idle-cycle',prefix+'tactical-walk--walk-right',prefix+'tactical-walk--walk-left'])
order+=['professions-class-6-ally-maps-story--idle-pose','hunapu-maps-world--walk-down','hunapu-maps-world--walk-right']
(V/'overview-inputs.txt').write_text('\n'.join("file '"+str(R/lookup[aid]['video'])+"'" for aid in order)+'\n')
subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
for aid in order:
 action=lookup[aid];profile=profiles[action['profile']]
 for tick in ([0,14,22] if 'idle-cycle' in aid else [0,16] if 'walk-' in aid else [0]):
  for light,label in [(False,'ground'),(True,'light')]:render_frame(data,profile,action,tick,4,light).save(V/f'reviews/{aid}-{tick}-{label}.png',optimize=True)
dump(V/'verification.json',{'passed':True,'checks':checks,'unrelated_actions_unchanged':sum(not allowed(a['profile']) for a in data['actions']),'runtime_spearmen_integrated':False,'world_shadow_matches_story':profiles['hunapu-maps-world']['mapShadow']==profiles['hunapu-maps-story']['mapShadow'],'browser_replay':'not performed; existing local-file browser access restriction respected'})
dump(V/'export-selection.json',{'exports':reports,'overview_actions':order})
print('Published spear review and hero world-shadow correction.')
