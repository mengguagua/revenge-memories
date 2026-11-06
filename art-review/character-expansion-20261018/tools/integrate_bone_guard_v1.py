#!/usr/bin/env python3
"""Scoped new enemy17 gallery build, native checks, export and append-only merge."""
import argparse,contextlib,copy,io,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageOps
import integrate_enemy_11_14_review as shared
import import_bone_guard_v1 as art
import build_gallery as G

ROOT=art.ROOT;OUT=art.OUT;PREFIX='professions-class-17-enemy-'
def own(row):return str(row.get('profile',row.get('id',''))).startswith(PREFIX)
def write(p,d):art.write(p,d)
def build():
 shared.MAPS=[art.MP,art.BP];module=shared.isolated_builder();before=shared.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert shared.snapshot_shared()==before and len(data['profiles'])==3 and len(data['actions'])==14
 assert all(own(row)for row in data['profiles']+data['actions']);write(OUT/'gallery-data.json',data);return data

def verify(data):
 audit=json.loads((art.SRC/'native-audit.json').read_text());native=[G.pack_frame(row)for row in audit['variant']['frames']];errors=[];checks=0;profiles={p['id']:p for p in data['profiles']};attack=next(a for a in data['actions']if a['kind']=='attack')
 assert attack['frames']==native and len(native)==194 and attack['contactTick']==100
 assert attack['origin']==audit['variant']['actor_origin'] and not attack.get('revisedFrames')and not attack.get('reviewTailFrames')
 expected={'tactical-idle':{'idle-cycle'},'tactical-walk':{'walk-'+d for d in['up','right','down','left']}|{'idle-'+d for d in['up','right','down','left']},'battle':{'original_class_17_enemy_normal','idle','miss','hit','exit'}}
 for p in profiles.values():
  assert {a['key']for a in data['actions']if a['profile']==p['id']}==expected['battle'if p['context']=='battle'else p['id'].split('maps-')[-1]]
  for path in p['newFrames'].values():
   im=Image.open(ROOT/path).convert('RGBA');assert list(im.size)==p['outputFrameSize']and im.getbbox();assert {px[:3]for px in im.getdata()if px[3]}<=set(art.PALETTE);assert {px[3]for px in im.getdata()}<={0,255};checks+=1
 for a in data['actions']:
  assert a['ready'];p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=shared.V.image(p['sourceAtlas'])
  if a['key']=='idle-cycle':assert [r['frame']for r in a['frames']]==[k for _ in range(2)for k,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  if a['kind']=='map_walk':assert len(a['frames'])==96
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
 for group,folder,ids,boxes in[('idle','tactical-idle',[0,1,2],[(34,16,62,40),(39,39,60,55),(36,55,65,80)]),('up','tactical-walk',[0,1],[(48,28,76,49),(58,50,70,74)]),('right','tactical-walk',[2,3],[(46,28,75,49),(57,59,65,73)]),('down','tactical-walk',[4,5],[(49,28,77,49),(59,54,66,73)]),('left','tactical-walk',[6,7],[(53,28,82,49),(63,59,71,73)])]:
  ims=[Image.open(OUT/folder/f'frame-{i:03}.png').convert('RGBA')for i in ids]
  for box in boxes:assert all(im.crop(box).tobytes()==ims[0].crop(box).tobytes()for im in ims),(group,box);checks+=1
  cores.append({'direction':group,'fixed_regions':boxes,'fixed_core_drift_pixels':0})
 for a,b in[(2,6),(3,7)]:assert ImageOps.mirror(Image.open(OUT/'tactical-walk'/f'frame-{a:03}.png').convert('RGBA')).tobytes()==Image.open(OUT/'tactical-walk'/f'frame-{b:03}.png').convert('RGBA').tobytes()
 b0=Image.open(OUT/'battle/frame-000.png').convert('RGBA');bg=Image.new('RGBA',b0.size);bg.alpha_composite(b0,(-64,0));assert bg.tobytes()==Image.open(OUT/'battle/frame-009.png').convert('RGBA').tobytes()==Image.open(OUT/'battle/frame-017.png').convert('RGBA').tobytes()
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':3,'actions':14,'native_attack_ticks':194,'contact_tick':100,'native_actor_rows_exact':True,'fixed_core_measurements':cores,'native_walk_mirror_aliases_exact':True,'native_oam_and_bg_registration_preserved':True,'errors':errors,'runtime_integrated':False,'user_acceptance':'pending'};write(OUT/'verification.json',report);assert not errors,errors[:5];return report

def export(data):
 before=shared.OUT;shared.OUT=OUT
 try:shared.export_local(data,'all')
 finally:shared.OUT=before
 report=json.loads((OUT/'export-report.json').read_text());report['scope']='Only enemy17 bone guard: 14 action videos and one battle close-up; no other media written';write(OUT/'export-report.json',report)

def merge(data):
 paths=shared.source_paths();before=shared.snapshot_shared();live=json.loads(paths[1].read_text());assert shared.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=shared.merge_rows(live[field],data[field],own);assert[r for r in combined[field]if not own(r)]==[r for r in live[field]if not own(r)]
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);rows=[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']];report['actions']=shared.merge_rows(report['actions'],rows,own)
 payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.bone-guard-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert shared.snapshot_shared()==before,'concurrent shared writer; retry latest merge'
  for temp,p in staged:os.replace(temp,p)
 finally:
  for temp,_ in staged:temp.unlink(missing_ok=True)
 assert json.loads(paths[1].read_text())==combined and shared.parse_js(paths[0])==combined and shared.sha(paths[3])==before['index.html']
 write(OUT/'merge-report.json',{'target_profiles':3,'target_actions':14,'all_unrelated_profiles_and_actions_unchanged':True,'all_existing_spell_effects_unchanged':combined['effects']==live['effects'],'index_default_unchanged':True,'runtime_integrated':False})

def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();data=build();v=verify(data);print(json.dumps({'profiles':3,'actions':14,'checks':v['checks'],'native_attack_ticks':194,'contact_tick':100}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()
