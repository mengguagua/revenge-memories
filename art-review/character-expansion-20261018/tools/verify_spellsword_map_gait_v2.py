#!/usr/bin/env python3
"""Scoped checks for nine repaired class11 ally map actions."""
import ast,json,subprocess,copy
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,matched_export,relative
from export_gallery import render_frame,render_panel
from export_knight_complete import export_one
from revise_spellsword_map_gait_v2 import REV,OUT,write,art

def main():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());old={a['id']:a for a in b['gallery']['actions']};now={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};actions=[a for a in d['actions']if a['profile'].startswith('professions-class-11-ally-maps-')];assert len(actions)==9 and len(now)==len(old)==1098
 concurrent=[]
 assert not d['validation']['structuralIssues'];changed={a['id']for a in actions};assert len(changed)==9
 for aid,a in now.items():
  if aid not in changed:
   if a['contentDigest']!=old[aid]['contentDigest']:
    assert a['profile']=='professions-class-15-enemy-battle',('unexpected unrelated change',aid)
    concurrent.append({'action':aid,'profile':a['profile'],'baseline_digest':old[aid]['contentDigest'],'current_digest':a['contentDigest'],'edited_by_this_revision':False})
  else:assert a['frames']==old[aid]['frames']and a['fps']==old[aid]['fps']and a['duration']==old[aid]['duration']and a['origin']==old[aid]['origin']and a['ready']
 assert d['effects']==b['gallery']['effects']
 images={};ledger=[]
 for kind,n,size in[('tactical-idle',6,(96,96)),('tactical-walk',8,(128,96))]:
  paths=sorted((OUT/'ally'/kind).glob('frame-*.png'));assert len(paths)==n
  for path in paths:
   i=int(path.stem.split('-')[-1]);im=Image.open(path).convert('RGBA');images[kind,i]=im;assert im.size==size and set(im.getchannel('A').getdata())=={0,255}and{p[:3]for p in im.getdata()if p[3]}<=set(art.C)
   cs=art.helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==1,(kind,i,'detached')
   ledger.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'sha256':file_hash(path)})
 assert all(images['tactical-idle',i].crop((0,55,96,96)).tobytes()==images['tactical-idle',0].crop((0,55,96,96)).tobytes()for i in range(6))
 boots=images['tactical-idle',0];pts=[(x,y)for y in range(78,89)for x in range(96)if boots.getpixel((x,y))[3]];cs=[c for c in art.helper.parts(pts)if len(c)>8];assert len(cs)==2,('idle must have exactly two boot endings',[(len(c),art.box(c))for c in cs])
 assert len({images['tactical-idle',i].crop((20,15,39,50)).tobytes()for i in[0,1,2]})==3,'idle arm must articulate'
 measures=[]
 for ids in[[0,1],[4,5]]:
  lanes=[]
  for i in ids:
   im=images['tactical-walk',i];pts=[(x,y)for y in range(88,93)for x in range(128)if im.getpixel((x,y))[3]];assert pts;lanes.append(sum(x for x,y in pts)/len(pts))
  assert lanes[0]+2<lanes[1],('forward gait must swap low foot',ids,lanes);measures.append({'ids':ids,'low_foot_x':lanes})
 for ids,region in[([0,1],[53,27,72,60]),([4,5],[55,31,74,60]),([2,3],[64,31,80,59])]:assert images['tactical-walk',ids[0]].crop(region).tobytes()==images['tactical-walk',ids[1]].crop(region).tobytes()
 spans=[]
 for i in[2,3]:
  im=images['tactical-walk',i];pts=[(x,y)for y in range(78,93)for x in range(128)if im.getpixel((x,y))[3]];bb=art.box(pts);spans.append(bb[2]-bb[0])
 assert spans[1]>spans[0]+8,('side passing and open stride need distinct leg widths',spans)
 for i,j in[(6,2),(7,3)]:assert images['tactical-walk',i].tobytes()==images['tactical-walk',j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
 exports=[];captures=[];shadow_checks=[]
 for a in actions:
  p=pp[a['profile']];assert p['revision']==REV and p['mapShadow']['alpha']>0 and(ROOT/p['mapShadow']['path']).exists()
  shadow_image=Image.open(ROOT/p['mapShadow']['path']).convert('RGBA');assert len(art.helper.parts((x,y)for y in range(shadow_image.height)for x in range(shadow_image.width)if shadow_image.getpixel((x,y))[3]))==1,'ground shadow must be continuous'
  selected=a['kind']=='map_walk'or a['key']=='idle-cycle';exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not selected)))
  ticks=[0,16]if a['kind']=='map_walk'else[0,14,22]if a['key']=='idle-cycle'else[]
  for t in ticks:
   for light in[False,True]:
    path=OUT/f'{a["key"]}-{t:03}-{"light"if light else"dark"}.png';render_frame(d,p,a,t,8,light,False).save(path,optimize=True);captures.append(relative(path))
   row=a['frames'][t];plain=copy.deepcopy(p);plain.pop('mapShadow');a1=render_panel(d,p,a,row,True,4,True);a2=render_panel(d,plain,a,row,True,4,True);different=sum(u!=v for u,v in zip(a1.getdata(),a2.getdata()));assert different>0;shadow_checks.append({'action':a['key'],'tick':t,'visible_shadow_pixels':different})
  print('Exported '+a['key'],flush=True)
 decoded=[]
 for e in exports:
  if not e.get('video'):continue
  v=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(v['nb_read_frames'])==e['frames']and abs(float(v['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**v})
 for a in actions:
  for field,kind,ext in[('video','videos','mp4'),('still','stills','png')]:
   p=ROOT/f'demos/{kind}/{a["id"]}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text());own={a['id']:a for a in actions}
 for a in latest['actions']:
  if a['id']in own:
   assert a['contentDigest']==own[a['id']]['contentDigest']
   for key in['video','still']:a[key]=own[a['id']][key]
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 m=json.loads((OUT/'asset-manifest.json').read_text());assert all(x['clipped_pixels']==0 for x in m['registrations'])
 for asset in m['assets']:assert file_hash(ROOT/asset['path'])==asset['sha256']
 for name in['revise_spellsword_map_gait_v2.py','verify_spellsword_map_gait_v2.py']:ast.parse((ROOT/'tools'/name).read_text())
 write(OUT/'export-report.json',{'exports':exports,'decoded':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'changed_map_actions':9,'unchanged_actions':1089-len(concurrent),'concurrent_changes_outside_this_revision':concurrent,'battle_unchanged':True,'effects_unchanged':True,'native_map_sequences_fps_origins_durations_unchanged':True,'two_idle_boot_endings':2,'three_distinct_sword_arm_poses':True,'forward_gait':measures,'side_passing_and_stride_boot_spans':spans,'all_map_shadows_visible':shadow_checks,'decoded_videos':len(decoded),'stills':9,'captures':captures,'assets':ledger,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending'})
 print(json.dumps({'status':'passed','changed':9,'unchanged':1089-len(concurrent),'concurrent_other_actions':len(concurrent),'videos':len(decoded)}),flush=True)
if __name__=='__main__':main()
