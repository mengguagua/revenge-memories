#!/usr/bin/env python3
"""Scoped new enemy18 gallery build, native checks, export and append-only merge."""
import argparse,contextlib,copy,io,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageOps
import integrate_enemy_11_14_review as shared
import import_cleft_eye_v1 as art
import build_gallery as G

ROOT=art.ROOT;OUT=art.OUT;PREFIX='professions-class-18-enemy-'
def own(row):return str(row.get('profile',row.get('id',''))).startswith(PREFIX)
def write(p,d):art.write(p,d)
def build():
 shared.MAPS=[art.MP,art.BP];module=shared.isolated_builder();before=shared.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert shared.snapshot_shared()==before and len(data['profiles'])==3 and len(data['actions'])==14
 assert all(own(row)for row in data['profiles']+data['actions']);write(OUT/'gallery-data.json',data);return data

def verify(data):
 audit=json.loads((art.SRC/'native-audit.json').read_text());native=[G.pack_frame(row)for row in audit['variant']['frames']];errors=[];checks=0;profiles={p['id']:p for p in data['profiles']};attack=next(a for a in data['actions']if a['kind']=='attack')
 assert attack['frames']==native and len(native)==240 and attack['contactTick']==83
 assert attack['origin']==audit['variant']['actor_origin'] and attack['fps']==audit['variant']['native_fps']
 assert not attack.get('revisedFrames')and not attack.get('reviewTailFrames')and not attack['effectIds']
 expected={'tactical-idle':{'idle-cycle'},'tactical-walk':{'walk-'+d for d in['up','right','down','left']}|{'idle-'+d for d in['up','right','down','left']},'battle':{'original_class_18_enemy_normal','idle','miss','hit','exit'}}
 for p in profiles.values():
  assert {a['key']for a in data['actions']if a['profile']==p['id']}==expected['battle'if p['context']=='battle'else p['id'].split('maps-')[-1]]
  for path in p['newFrames'].values():
   im=Image.open(ROOT/path).convert('RGBA');assert list(im.size)==p['outputFrameSize']and im.getbbox();assert {px[:3]for px in im.getdata()if px[3]}<=set(art.PALETTE);assert {px[3]for px in im.getdata()}<={0,255};checks+=1
 for a in data['actions']:
  assert a['ready'];p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=shared.V.image(p['sourceAtlas'])
  if a['key']=='idle-cycle':assert [r['frame']for r in a['frames']]==[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  if a['kind']=='map_walk':assert len(a['frames'])==96 and all(r['offset']==[0,0]for r in a['frames'])
  for tick,row in enumerate(a['frames']):
   f=row['frame'];flip=(p['context']=='battle')!=row.get('flip',False);off=row.get('offset',[0,0]);at=[a['origin'][i]+off[i]-p['anchor'][i]for i in(0,1)];at[0]+=row.get('shake',0)
   if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in(0,1)]
   x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh
   for kind,im in[('native',atlas.crop((x,y,x+fw,y+fh))),('redraw',shared.V.image(p['newFrames'][str(f)]))]:
    box=shared.V.box_at(im,at,[fw,fh],flip);checks+=1
    if shared.V.outside(box,a.get('viewport',data['viewport'])):errors.append({'action':a['id'],'tick':tick,'mode':'scene','kind':kind,'bounds':box})
    if a.get('closeCamera'):
     c=a['closeCamera'];view=[a['origin'][i]+off[i]+c['offset'][i]for i in(0,1)]+c['size'];checks+=1
     if shared.V.outside(box,view):errors.append({'action':a['id'],'tick':tick,'mode':'close','kind':kind,'bounds':box})
 cores=[]
 for group,folder,ids in[('tactical-idle','tactical-idle',[0,1,2]),('up','tactical-walk',[0,1]),('right','tactical-walk',[2,3]),('down','tactical-walk',[4,5]),('left','tactical-walk',[6,7])]:
  ims=[Image.open(OUT/folder/f'frame-{i:03}.png').convert('RGBA')for i in ids]
  for box in art.CORES[group]:assert all(im.crop(box).tobytes()==ims[0].crop(box).tobytes()for im in ims),(group,box);checks+=1
  assert len({im.tobytes()for im in ims})==len(ims),(group,'tail phases must remain distinct')
  cores.append({'direction':group,'fixed_regions':art.CORES[group],'fixed_core_drift_pixels':0,'gaze_and_tail_change_inside_fixed_shell':True})
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(Image.open(OUT/'tactical-walk'/f'frame-{a:03}.png').convert('RGBA')).tobytes()==Image.open(OUT/'tactical-walk'/f'frame-{b:03}.png').convert('RGBA').tobytes()
 idle=[Image.open(OUT/'tactical-idle'/f'frame-{i:03}.png').convert('RGBA')for i in[0,1,2]]
 assert all(im.getchannel('A').crop((25,12,72,58)).tobytes()==idle[0].getchannel('A').crop((25,12,72,58)).tobytes()for im in idle)
 cores[0]['fixed_complete_shell_alpha']=True
 down=[Image.open(OUT/'tactical-walk'/f'frame-{i:03}.png').convert('RGBA')for i in[4,5]];rim=Image.open(art.SRC/'down-fixed-rim-mask.png').convert('L')
 assert down[0].getchannel('A').crop((36,40,94,86)).tobytes()==down[1].getchannel('A').crop((36,40,94,86)).tobytes()
 assert all(a==b for a,b,m in zip(down[0].getdata(),down[1].getdata(),rim.getdata())if m)
 cores[-2].update(fixed_shell_alpha_and_two_pixel_rim=True,fixed_shell_bounds=[36,40,94,86])
 b0=Image.open(OUT/'battle/frame-000.png').convert('RGBA');bg=Image.new('RGBA',b0.size);bg.alpha_composite(b0,(-64,0));assert bg.tobytes()==Image.open(OUT/'battle/frame-007.png').convert('RGBA').tobytes()==Image.open(OUT/'battle/frame-013.png').convert('RGBA').tobytes()
 for slot in[4,5,6]:assert Image.open(OUT/'battle'/f'frame-{slot:03}.png').convert('RGBA').crop((164,128,223,188)).tobytes()==b0.crop((164,128,223,188)).tobytes()
 for rec in audit['walk']['frame_mapping']:
  source=Image.open(art.SRC/f'native-walk-{rec["source_slot"]:03}.png').convert('RGBA');assert __import__('hashlib').sha256(source.tobytes()).hexdigest()==rec['rgba_sha256']
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':3,'actions':14,'native_attack_ticks':240,'contact_tick':83,'native_actor_rows_exact':True,'fixed_core_measurements':cores,'native_walk_mirror_aliases_exact':True,'native_oam_and_bg_registration_preserved':True,'gaze_sequence':[0,1,3,2,0],'tail_sequence':[4,5,6,0],'attack_visual':'single forward collision, no beam or additional magic','errors':errors,'runtime_integrated':False,'user_acceptance':'pending'};write(OUT/'verification.json',report);assert not errors,errors[:5];return report

def export(data):
 before=shared.OUT;shared.OUT=OUT
 try:shared.export_local(data,'all')
 finally:shared.OUT=before
 report=json.loads((OUT/'export-report.json').read_text());report['scope']='Only enemy18 cleft eye: 14 action videos and one battle close-up; no other media written';write(OUT/'export-report.json',report)

def merge(data):
 paths=shared.source_paths();before=shared.snapshot_shared();live=json.loads(paths[1].read_text());assert shared.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=shared.merge_rows(live[field],data[field],own);assert[r for r in combined[field]if not own(r)]==[r for r in live[field]if not own(r)]
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);rows=[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']];report['actions']=shared.merge_rows(report['actions'],rows,own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.cleft-eye-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert shared.snapshot_shared()==before,'concurrent shared writer; retry latest merge'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert json.loads(paths[1].read_text())==combined and shared.parse_js(paths[0])==combined and shared.sha(paths[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':14,'all_unrelated_profiles_and_actions_unchanged':True,'all_existing_spell_effects_unchanged':combined['effects']==live['effects'],'index_default_unchanged':True,'runtime_integrated':False})

def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();data=build();v=verify(data);print(json.dumps({'profiles':3,'actions':14,'checks':v['checks'],'native_attack_ticks':240,'contact_tick':83}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
