#!/usr/bin/env python3
"""Focused side-gait and complete-battle-frame verification/export."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count,font,body_image
from export_knight_complete import export_one
from import_eileen_side_battle_v3 import REV,OUT,SRC,write,C,HAIR,NAVY,SKIN,parts,box,center

def main():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());byid={a['id']:a for a in d['actions']};profiles={p['id']:p for p in d['profiles']};m=json.loads((ROOT/'eileen/maps/frame_mapping.json').read_text());bm=json.loads((ROOT/'eileen/battle/frame_mapping.json').read_text());art=json.loads((OUT/'asset-manifest.json').read_text())
 changed=[a for a in d['actions']if a['contentDigest']!=b['digests'].get(a['id'])];selected=[a for a in changed if a['profile']in['eileen-battle','eileen-maps-tactical-walk']];external=[a['id']for a in changed if a not in selected]
 assert len(selected)==11,[(a['id'])for a in selected];assert all(a.startswith('professions-class-16-enemy-battle--')for a in external),external
 assert not d['validation']['structuralIssues']and all(a['ready']for a in selected)
 for path,digest in b['preserved'].items():assert file_hash(ROOT/path)==digest,('promoted change',path)
 old_s={s['id']:s for s in b['maps']['scenarios']};now_s={s['id']:s for s in m['scenarios']}
 for key in['story','world','tactical-idle']:assert now_s[key]==old_s[key],key
 for key in['source_atlas','source_frame_size','source_anchor','output_frame_size','output_anchor','logical_render_scale','directions','direction_mirror_x','timing','source_audit','ground_shadow']:assert now_s['tactical-walk'].get(key)==old_s['tactical-walk'].get(key),key
 now={x['source_index']:x for x in now_s['tactical-walk']['frame_mapping']};old={x['source_index']:x for x in old_s['tactical-walk']['frame_mapping']}
 for i in[0,1,4,5]:assert now[i]==old[i]
 for a in selected:
  old=b['actions'][a['id']]
  for key in['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==old.get(key),(a['id'],key)
 used={e['sprite']for a in b['actions'].values()for row in a['frames']+a.get('revisedFrames',[])+a.get('reviewTailFrames',[])for e in row.get('effects',[])}
 for key in used:assert d['effects'][key]==b['effects'][key],('Eileen effect',key)
 for key in['variant_keys','review_timeline','shared_spell_ids','heal_effect_revision']:assert bm.get(key)==b['battle'].get(key),key
 preserved_battle=set(b['battle']['frame_mapping'])-{str(i)for i in art['changed_battle_slots']}
 for key in preserved_battle:assert bm['frame_mapping'][key]==b['battle']['frame_mapping'][key]
 for a in art['assets']:
  p=ROOT/a['path'];assert file_hash(p)==a['sha256'];im=Image.open(p);assert list(im.size)==a['size']
  if '/frame-'in a['path']:
   q=im.convert('RGBA');assert set(q.getchannel('A').getdata())<={0,255};assert {v[:3]for v in q.getdata()if v[3]}<=set(C)
 for rec in art['battle_registrations']:
  assert rec['whole_unspliced_pose']and rec['body_patch_count']==0 and rec['clipped_pixels']==0
  assert rec['target_head_height']==31
 # Correct the exact bug: none of the first-flight registrations may use the
 # raised wrist, upper arm, or the extended front hand as its face landmark.
 mm=json.loads((OUT/'head-measurements.json').read_text())
 for i in range(2,11):
  rec=mm[str(i)];fb=rec['face_box'];assert fb[2]-fb[0]<=23 and fb[3]-fb[1]<=30
 # These three native face clusters are below the hands. Source references
 # are verified, rather than treating the lifted red hair as a bigger head.
 pp=profiles['eileen-battle'];clusters={13:[43,25,47,31],14:[43,41,47,47],15:[42,42,49,48]}
 for i,region in clusters.items():
  q=body_image(pp['sourceAtlas'],i,tuple(pp['sourceFrameSize']),pp['sourceColumns']).crop(region);assert sum(v==(254,204,197,255)for v in q.getdata())>=10
 def load(kind,i):return Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')
 for a,z in[(2,6),(3,7)]:assert load('map',a).transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==load('map',z).tobytes()
 map_regs=art['map_registrations'];assert map_regs[0]['uniform_group_scale']==map_regs[1]['uniform_group_scale'];assert abs(load('map',2).getbbox()[3]-load('map',3).getbbox()[3])<=1
 # One foreground figure per frame; slash19 intentionally has one detached arc.
 component_counts=[]
 for i in art['changed_battle_slots']:
  q=load('battle',i);gs=parts((x,y)for y in range(q.height)for x in range(q.width)if q.getpixel((x,y))[3]);large=[g for g in gs if len(g)>20]
  assert len(large)<=(2 if i==19 else 1),(i,[len(g)for g in large]);component_counts.append({'frame':i,'foreground_components':len(large),'intentional_arc':i==19})
 for name in['import_eileen_side_battle_v3.py','verify_eileen_side_battle_v3.py']:ast.parse((ROOT/'tools'/name).read_text())
 report={'status':'assets_passed','revision':REV,'affected_actions':len(selected),'changed_map_slots':4,'changed_battle_slots':25,'independent_generated_poses':6,'unchanged_other_actions':len(d['actions'])-len(selected)-len(external),'concurrent_external_changes_preserved':external,'promoted_form_unchanged':True,'story_world_up_down_and_idle_maps_unchanged':True,'accepted_standing_and_casting_frames_unchanged':len(preserved_battle),'native_schedules_origins_contacts_and_fps_exact':True,'shared_eileen_effects_unchanged':len(used),'no_lower_body_splicing':True,'single_foreground_actor_components':component_counts,'side_walk_shared_scale_and_ground_baseline':True,'left_right_mirror_exact':True,'hair_rise_native_head_clusters_verified':True,'runtime_integrated':False,'browser_ui_checked':False,'user_visual_acceptance':'pending'}
 write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','actions':len(selected)}),flush=True)
 exports=[]
 for a in selected:exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
 for a in selected:
  if a['kind']=='map_walk'or a['context']=='battle':
   exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)));print('Exported '+a['id'],flush=True)
 a=byid['eileen-battle--original_class_11_normal'];exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
 captures=[]
 for light in[False,True]:
  # Match each of the user's critical frames, plus standing, land and retreat.
  samples=[]
  for tick in[0,65,70,86,117,128,156,193,214]:
   q=render_frame(d,profiles[a['profile']],a,tick,4,light,True);samples.append(q)
  cw,ch=samples[0].size;board=Image.new('RGB',(cw*3,ch*3),(14,21,26))
  for n,q in enumerate(samples):board.paste(q,(n%3*cw,n//3*ch))
  p=OUT/('battle-playback-'+('light'if light else'dark')+'.png');board.save(p,optimize=True);captures.append(relative(p))
  p=profiles['eileen-maps-tactical-walk'];samples=[]
  for direction in['right','left']:
   for tick in[0,16]:samples.append(render_frame(d,p,byid[p['id']+'--walk-'+direction],tick,6,light))
  cw,ch=samples[0].size;board=Image.new('RGB',(cw*2,ch*2),(14,21,26))
  for n,q in enumerate(samples):board.paste(q,(n%2*cw,n//2*ch))
  pth=OUT/('side-playback-'+('light'if light else'dark')+'.png');board.save(pth,optimize=True);captures.append(relative(pth))
 decoded=[]
 for e in exports:
  if not e.get('video'):continue
  aa=byid[e['action']];s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(s['nb_read_frames'])==playback_count(aa);assert abs(float(s['duration'])-playback_count(aa)/aa['fps'])<1/aa['fps'];decoded.append({'path':e['video'],**s})
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for aa in latest['actions']:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{aa["id"]}{suffix}.{ext}';aa[field]=relative(path)if matched_export(path,aa['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n');write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});report.update(status='passed',exported_stills=len(selected),decoded_videos=len(decoded),offline_captures=captures);write(OUT/'verification.json',report);print(json.dumps({'status':'passed','stills':len(selected),'videos':len(decoded)}),flush=True)
if __name__=='__main__':main()
