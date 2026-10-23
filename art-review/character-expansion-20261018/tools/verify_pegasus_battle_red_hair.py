#!/usr/bin/env python3
"""Palette-only invariants and fresh gallery exports for Pegasus battle hair."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,relative,file_hash,matched_export
from export_gallery import render_frame
from export_knight_complete import export_one
from patch_pegasus_battle_red_hair import OUT,REV,C,SPEC

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def verify():
 d=json.loads((ROOT/'demos/gallery-data.json').read_text());baseline=json.loads((OUT/'baseline.json').read_text());before={a['id']:a for a in baseline['gallery']['actions']};now={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']}
 changed={k for k,a in now.items()if a['contentDigest']!=before[k]['contentDigest']};expected={a['id']for a in now.values()if a['profile']=='professions-class-3-ally-battle'};assert changed==expected and len(changed)==11
 assert len(d['profiles'])==97 and len(now)==775 and not d['validation']['structuralIssues']
 for k,a in now.items():
  for field in['frames','fps','origin','contactTick','duration']:assert a.get(field)==before[k].get(field),(k,field)
 p=pp['professions-class-3-ally-battle'];oldp=next(x for x in baseline['gallery']['profiles']if x['id']==p['id'])
 assert p['revisedEffects']==oldp['revisedEffects']
 reg=json.loads((OUT/'material-registration.json').read_text());checks=[]
 for row in reg['frames']:
  i=row['source_frame'];path=OUT/f'ally/battle/frame-{i:03}.png';im=Image.open(path).convert('RGBA');old=Image.open((ROOT/'professions/class-3-ally/battle'/baseline['battle']['frame_mapping'][str(i)]).resolve()).convert('RGBA')
  assert im.size==old.size==(320,384)and im.getchannel('A').tobytes()==old.getchannel('A').tobytes()
  assert {p[:3]for p in im.getdata()if p[3]}<=set(C)and set(im.getchannel('A').getdata())=={0,255}
  head=SPEC[i][0];outside=0
  for y in range(384):
   for x in range(320):
    a,b=old.getpixel((x,y)),im.getpixel((x,y))
    if a!=b and not(head[0]<=x<head[2]and head[1]<=y<head[3]):assert a[:3]==C[4];outside+=1
  assert outside==row['incorrect_nonhair_red_pixels_removed'];checks.append({'slot':i,'alpha_and_position_unchanged':True,'changed_pixels':row['changed_pixels'],'hair_pixels':row['hair_pixels'],'size':list(im.size),'bytes':path.stat().st_size})
 for i in[16,33]:assert Image.open(OUT/f'ally/battle/frame-{i:03}.png').tobytes()==Image.open(OUT/'ally/battle/frame-000.png').tobytes()
 assets=json.loads((OUT/'asset-manifest.json').read_text())
 for row in assets['assets']:assert file_hash(ROOT/row['path'])==row['sha256']and(ROOT/row['path']).stat().st_size==row['bytes']
 for name in['patch_pegasus_battle_red_hair.py','verify_pegasus_battle_red_hair.py']:ast.parse((ROOT/'tools'/name).read_text())
 captures=[];exports=[];decoded=[]
 for aid in sorted(changed):
  a=now[aid];assert a['ready']
  if a['key']=='original_class_3_normal':
   ticks=[next(n for n,f in enumerate(a['frames'])if f['frame']==i)for i in range(8)]
  elif a['key']=='class_3_ally_javelin':ticks=[0,18,21,51]
  else:ticks=[]
  for tick in ticks:
   for light in[False,True]:
    path=OUT/f'{a["key"]}-{tick:03}-{"light"if light else"dark"}.png';render_frame(d,p,a,tick,6,light,True).save(path,optimize=True);captures.append(relative(path))
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
  if a['key']in['original_class_3_normal','class_3_ally_javelin']:exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  print('Exported '+a['key'],flush=True)
 for e in exports:
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
  assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 for aid in changed:
  a=now[aid]
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   f=ROOT/f'demos/{kind}/{aid}{suffix}.{ext}';a[field]=relative(f)if matched_export(f,a['contentDigest'])else None
  assert a['video']and a['still']
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
 write(OUT/'verification.json',{'status':'passed','changed_actions':sorted(changed),'unrelated_actions_unchanged':764,'map_corrections_unchanged':True,'native_frames_timing_offsets_contacts_unchanged':True,'effect_metadata_unchanged':True,'original_alpha_positions_sizes_unchanged':True,'head_material_regions':checks,'five_colors_binary_alpha':True,'offline_captures':captures,'browser_ui_checked':False,'runtime_integrated':False,'enemy_deferred':True,'user_visual_acceptance':'pending'})
 write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});print(json.dumps({'status':'passed','actions':11,'unchanged':764,'videos':len(decoded)}),flush=True)
if __name__=='__main__':verify()
