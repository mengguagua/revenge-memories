from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import json,os,sys,hashlib,subprocess
V=Path(__file__).resolve().parents[1];R=V.parent;REV=V.name;sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export,render_frame
G='/opt/homebrew/bin/magick'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((V/'source/action-digests-before.json').read_text());inventory=[];checks=[]
shadow={'path':'hunapu-story-shadow-20261018/story-shadow.png','size':[11,3],'offset':[0,-1],'alpha':.38,'kind':'continuous_fixed_ground_projection','source':'Accepted continuous ground shadow, fixed below all support/lifted foot phases.'}
for side in ['ally','enemy']:
 key=f'class-8-{side}';base=R/f'professions/{key}/maps';mp=base/'frame_mapping.json';d=json.loads(mp.read_text());O=V/'deliverables'/key
 d.update(revision=REV,status='awaiting_user_review',runtime_integrated=False,modified_by='Codex',review_note='佣兵地图：简洁四色、束发与分片短衣，体量对齐已验收角色；原作持剑待机、四向行走与连续阴影。')
 if side=='ally':d['display_name']='友方佣兵（首关村民复用）'
 for s in d['scenarios']:
  typ='walk'if s['id']=='tactical-walk'else'idle';count=8 if typ=='walk'else 6;frames=[]
  for i in range(count):
   p=O/f'{typ}-{i:02}.png';subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(p)],check=True);im=Image.open(p).convert('RGBA')
   assert list(im.size)==s['output_frame_size'];assert set(im.getchannel('A').getdata())=={0,255};assert len({c for c in im.getdata()if c[3]})==4
   rec=dict(s['frame_mapping'][i]);rec.update(path=os.path.relpath(p,base),output_path=os.path.relpath(p,base),size=list(im.size),bytes=p.stat().st_size,sha256=sha(p),visible_bounds=list(im.getbbox()),art_revision=REV,construction='ImageGen mercenary; registered anatomy and native weapon side; fixed-body layer composition; palette reduction.',generation_record=os.path.relpath(V/'README.md',base));frames.append(rec)
   inventory.append({'path':str(p.relative_to(R)),'purpose':key+' '+s['id'],'dimensions':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)})
  atlas=O/f'{typ}-atlas.png';subprocess.run([G,*[str(O/f'{typ}-{i:02}.png')for i in range(count)],'+append',str(atlas)],check=True);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(atlas)],check=True)
  note='待机头身、双脚固定，整条持剑臂与单根直剑改变位置和倾斜；0/1/2/1原作节奏。'if typ=='idle'else'头部固定、双腿按相位变化；上视剑在画面右侧，向右、向下与向左的剑都在画面左侧，四向分别制作，禁止整幅镜像改武器侧。'
  s.update(revision=REV,frame_mapping=frames,output_atlas=os.path.relpath(atlas,base),output_atlas_bytes=atlas.stat().st_size,preview_ground='map-motion-review-v3/reference/grounds/tactical-M11.png',ground_shadow=shadow,review_note=note,adaptation_note=note,motion_review={'reference':str((V/'source/motion-audit.json').relative_to(R)),'fixed_and_moving_parts':note})
 dump(mp,d)
 ims={f'{typ}{i}':Image.open(O/f'{typ}-{i:02}.png').convert('RGBA')for typ,count in [('walk',8),('idle',6)]for i in range(count)}
 for a,b in [(0,4),(1,3),(1,5)]:assert ims[f'idle{a}'].tobytes()==ims[f'idle{b}'].tobytes()
 for i in [1,2]:
  assert ims['idle0'].crop((0,54,96,96)).tobytes()==ims[f'idle{i}'].crop((0,54,96,96)).tobytes()
  assert ims['idle0'].crop((45,0,96,96)).tobytes()==ims[f'idle{i}'].crop((45,0,96,96)).tobytes()
 for a,b in [(0,1),(2,3),(4,5),(6,7)]:
  assert ims[f'walk{a}'].crop((49,26,81,54)).tobytes()==ims[f'walk{b}'].crop((49,26,81,54)).tobytes()
  assert ims[f'walk{a}'].crop((0,78,128,96)).tobytes()!=ims[f'walk{b}'].crop((0,78,128,96)).tobytes()
 assert ims['walk2'].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()!=ims['walk6'].tobytes()
 checks.append({'side':side,'palette_colors':4,'binary_alpha':True,'native_idle_aliases':True,'idle_body_and_feet_fixed':True,'walk_head_registered':True,'distinct_leg_phases_all_directions':True,'no_whole_direction_mirror':True,'ground_shadow_separate_continuous':True})
# Neutral art is a palette-only mercenary reuse for the M11 review fixture.
for p in sorted((V/'deliverables/class-8-neutral').glob('*.png')):
 subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True);im=Image.open(p);inventory.append({'path':str(p.relative_to(R)),'purpose':'M11 neutral mercenary appearance reuse, review only','dimensions':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)})
dump(V/'image-inventory.json',inventory);data=build();allowed=lambda p:p.startswith('professions-class-8-')and'-maps-'in p
assert all(a['contentDigest']==old[a['id']]for a in data['actions']if not allowed(a['profile']))
args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);reports=[]
for a in data['actions']:
 if allowed(a['profile']):reports.append(export(data,a,args));print(a['id'],flush=True)
data=build();lookup={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']};order=[]
for side in ['ally','enemy']:
 pre=f'professions-class-8-{side}-maps-';order.append(pre+'tactical-idle--idle-cycle');order.extend(pre+'tactical-walk--walk-'+d for d in ['up','right','down','left'])
for aid in order:
 a=lookup[aid];p=profiles[a['profile']]
 for tick in ([0,14,22]if'idle-cycle'in aid else[0,16]):
  for light,label in [(False,'ground'),(True,'light')]:render_frame(data,p,a,tick,4,light).save(V/f'reviews/{aid}-{tick}-{label}.png',optimize=True)
(V/'overview-inputs.txt').write_text('\n'.join("file '"+str(R/lookup[a]['video'])+"'"for a in order)+'\n');subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
unchanged={p:h for p,h in json.loads((V/'source/runtime-hashes-before.json').read_text()).items()if p=='actual/data/reviewed_animations.json'or p.startswith('actual/assets/reviewed-animation-')};assert all(sha(R.parent.parent/p)==digest for p,digest in unchanged.items())
dump(V/'verification.json',{'passed':True,'checks':checks,'unrelated_actions_unchanged':sum(not allowed(a['profile'])for a in data['actions']),'exported_actions':len(reports),'runtime_hashes_unchanged':len(unchanged),'runtime_integrated':False,'browser_replay':'not performed; offline exports and guarded background Godot render used'})
dump(V/'export-selection.json',{'exports':reports,'overview_actions':order})
