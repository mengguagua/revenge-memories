from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import json,os,sys,hashlib,subprocess
V=Path(__file__).resolve().parents[1];R=V.parent;REV=V.name
sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export
G='/opt/homebrew/bin/magick'
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inventory=[];checks=[]
for cid,kind in [(12,'archer'),(6,'spearman')]:
 for side in ['ally','enemy']:
  key=f'class-{cid}-{side}';base=R/f'professions/{key}/maps';O=V/'deliverables'/key;mp=base/'frame_mapping.json';d=json.loads(mp.read_text())
  d.update(revision=REV,status='awaiting_device_test',runtime_integrated=True,review_note='已验收增厚身体样板扩展至待机及四向行走，统一放大6.25%，四色配色。')
  for s in d['scenarios']:
   typ='walk'if s['id']=='tactical-walk'else'idle';count=8 if typ=='walk'else 1 if s['id']=='story'else 6;frames=[]
   for i in range(count):
    p=O/f'{typ}-{i:02}.png';subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(p)],check=True)
    im=Image.open(p).convert('RGBA');assert list(im.size)==s['output_frame_size'];assert set(im.getchannel('A').getdata())=={0,255};assert len({c for c in im.getdata()if c[3]})==4
    rec=dict(s['frame_mapping'][i]);rec.update(path=os.path.relpath(p,base),output_path=os.path.relpath(p,base),size=list(im.size),bytes=p.stat().st_size,sha256=sha(p),visible_bounds=list(im.getbbox()),art_revision=REV,construction='ImageGen body volume revision; registered layers, fixed-region motion, nearest-neighbor scaling.',generation_record=os.path.relpath(V/'README.md',base));frames.append(rec)
    inventory.append({'path':str(p.relative_to(R)),'purpose':key+' '+s['id'],'dimensions':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p)})
   atlas=O/('idle-00.png'if s['id']=='story'else f'{typ}-atlas.png')
   if s['id']!='story':subprocess.run([G,*[str(O/f'{typ}-{i:02}.png')for i in range(count)],'+append',str(atlas)],check=True)
   note=('弓箭手待机仅双臂与整弓箭移动，行走上身及弓箭固定、只换腿脚。'if cid==12 else'枪兵保持侧身跨腿待机，持枪臂与单根长枪移动；左右行走为站直＋跨腿。')+' 身体增厚并统一放大6.25%，保留原作部位运动方式。'
   if s['id']=='story':note='友军剧情仅同款待机首帧静止形象。'
   s.update(revision=REV,frame_mapping=frames,output_atlas=os.path.relpath(atlas,base),output_atlas_bytes=atlas.stat().st_size,review_note=note,adaptation_note=note,motion_review={'reference':str((V/'README.md').relative_to(R)),'fixed_and_moving_parts':note})
  dump(mp,d)
  ims={f'{typ}{i}':Image.open(O/f'{typ}-{i:02}.png').convert('RGBA')for typ,count in [('idle',6),('walk',8)]for i in range(count)}
  assert ims['idle0'].tobytes()==Image.open(R/f'body-volume-static-20261018/deliverables/{kind}-{side}.png').convert('RGBA').tobytes()
  for a,b in [(2,6),(3,7)]:assert ims[f'walk{a}'].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==ims[f'walk{b}'].tobytes()
  if cid==12:
   for a,b in [(0,1),(2,3),(4,5),(6,7)]:assert ims[f'walk{a}'].crop((0,0,128,76)).tobytes()==ims[f'walk{b}'].crop((0,0,128,76)).tobytes()
  for a,b in [(0,1),(2,3),(4,5)]:assert ims[f'walk{a}'].tobytes()!=ims[f'walk{b}'].tobytes()
  checks.append({'key':key,'accepted_idle0_exact':True,'same_phase_mirror':True,'distinct_leg_phases':True,'four_color_binary_alpha':True,'archer_upper_body_fixed':cid==12})
dump(V/'image-inventory.json',inventory)
data=build();allowed=lambda p:any(p.startswith(f'professions-class-{c}-')and'-maps-'in p for c in [12,6]);old=json.loads((V/'source/action-digests-before.json').read_text());assert all(a['contentDigest']==old[a['id']]for a in data['actions']if not allowed(a['profile']))
args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);reports=[]
for a in data['actions']:
 if allowed(a['profile']):reports.append(export(data,a,args));print(a['id'],flush=True)
data=build();lookup={a['id']:a for a in data['actions']};order=[]
for cid in [12,6]:
 for side in ['ally','enemy']:
  prefix=f'professions-class-{cid}-{side}-maps-';order.append(prefix+'tactical-idle--idle-cycle');order.extend(prefix+'tactical-walk--walk-'+direction for direction in ['down','right','left','up'])
 order.append(f'professions-class-{cid}-ally-maps-story--idle-pose')
(V/'overview-inputs.txt').write_text('\n'.join("file '"+str(R/lookup[a]['video'])+"'"for a in order)+'\n')
subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
dump(V/'verification.json',{'passed':True,'checks':checks,'unrelated_actions_unchanged':sum(not allowed(a['profile'])for a in data['actions']),'exported_actions':len(reports),'browser_replay':'not performed; local-file browser restriction respected'})
dump(V/'export-selection.json',{'exports':reports,'overview_actions':order})
