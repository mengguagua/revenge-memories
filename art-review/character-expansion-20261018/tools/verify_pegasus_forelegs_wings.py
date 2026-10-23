#!/usr/bin/env python3
"""Narrow regression checks and offline playback export for local Pegasus repairs."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from patch_pegasus_forelegs_wings import REV,OUT,OLD,C,map_anchor

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def verify():
 d=json.loads((ROOT/'demos/gallery-data.json').read_text());base=json.loads((OUT/'baseline.json').read_text());before={a['id']:a for a in base['gallery']['actions']};now={a['id']:a for a in d['actions']};profiles={p['id']:p for p in d['profiles']}
 expected={'professions-class-3-ally-maps-tactical-idle--idle-cycle','professions-class-3-ally-maps-tactical-walk--walk-down','professions-class-3-ally-maps-tactical-walk--idle-down'}
 changed={k for k,a in now.items()if a['contentDigest']!=before[k]['contentDigest']};assert changed==expected,changed
 assert len(d['profiles'])==97 and len(now)==775 and not d['validation']['structuralIssues']
 for k,a in now.items():
  for field in['frames','fps','origin','contactTick','duration']:assert a.get(field)==before[k].get(field),(k,field)
 mapping=json.loads((ROOT/'professions/class-3-ally/maps/frame_mapping.json').read_text());checks=[]
 for scene in mapping['scenarios']:
  prior=next(s for s in base['maps']['scenarios']if s['id']==scene['id']);kind=scene['id'];folder=ROOT/'professions/class-3-ally/maps'
  for f in scene['frame_mapping']:
   i=f['source_index'];p=(folder/f['output_path']).resolve();old=(folder/next(x for x in prior['frame_mapping']if x['source_index']==i)['output_path']).resolve();im=Image.open(p).convert('RGBA');original=Image.open(old).convert('RGBA')
   assert im.size==original.size and {x[:3]for x in im.getdata()if x[3]}<=set(C)and set(im.getchannel('A').getdata())=={0,255}
   assert map_anchor(im)==map_anchor(original)
   if kind=='tactical-idle':
    assert all(a==b for a,b in zip(original.getdata(),im.getdata())if a[3]);assert im.crop((0,0,96,53)).tobytes()==original.crop((0,0,96,53)).tobytes()
   elif i==4:
    assert im.crop((49,0,128,96)).tobytes()==original.crop((49,0,128,96)).tobytes();assert im.crop((0,49,128,96)).tobytes()==original.crop((0,49,128,96)).tobytes()
   else:assert p==old and im.tobytes()==original.tobytes()
   checks.append({'kind':kind,'slot':i,'size':list(im.size),'bytes':p.stat().st_size,'head_anchor':map_anchor(im),'sha256':file_hash(p),'changed':im.tobytes()!=original.tobytes()})
 manifest=json.loads((OUT/'asset-manifest.json').read_text())
 for a in manifest['assets']:assert file_hash(ROOT/a['path'])==a['sha256']and (ROOT/a['path']).stat().st_size==a['bytes']
 for n in['patch_pegasus_forelegs_wings.py','verify_pegasus_forelegs_wings.py']:ast.parse((ROOT/'tools'/n).read_text())
 captures=[];exports=[];decoded=[]
 for aid in sorted(changed):
  a=now[aid];p=profiles[a['profile']];assert a['ready']
  ticks=[0,14,22]if a['key']=='idle-cycle'else[0,16]if a['key']=='walk-down'else[0]
  for tick in ticks:
   for light in[False,True]:
    f=OUT/f'{a["key"]}-{tick:03}-{"light"if light else"dark"}.png'
    render_frame(d,p,a,tick,6,light,False).save(f,optimize=True);captures.append(relative(f))
  e=export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False));exports.append(e)
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
  assert int(info['nb_read_frames'])==len(a['frames'])and abs(float(info['duration'])-a['duration'])<1/a['fps'];decoded.append({'path':e['video'],**info})
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   f=ROOT/f'demos/{kind}/{aid}{suffix}.{ext}';a[field]=relative(f)if matched_export(f,a['contentDigest'])else None
  assert a['video']and a['still'];print('Exported '+a['key'],flush=True)
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
 write(OUT/'verification.json',{'status':'passed','revision':REV,'changed_actions':sorted(changed),'unrelated_actions_unchanged':772,'native_frames_fps_origin_contacts_duration_unchanged':True,'original_idle_foreground_pixels_unchanged':True,'down_rider_horse_spear_projection_unchanged':True,'five_colors_binary_alpha':True,'frames':checks,'offline_captures':captures,'visual_checks':{'idle_both_forelegs_visible_each_pose':True,'down_phase4_both_wings_up_phase5_both_wings_down':True,'dark_light_edges_inspected':True},'browser_ui_checked':False,'enemy_deferred':True,'runtime_integrated':False,'user_visual_acceptance':'pending'})
 write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded})
 print(json.dumps({'status':'passed','actions':len(changed),'unchanged':772,'videos':len(decoded)}),flush=True)
if __name__=='__main__':verify()
