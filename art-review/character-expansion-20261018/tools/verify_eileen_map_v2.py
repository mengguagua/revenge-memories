#!/usr/bin/env python3
"""Focused QA and offline exports for Eileen's corrected base map frames."""
import ast,json,subprocess
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count,font
from export_knight_complete import export_one
from import_eileen_map_v2 import REV,OUT,SRC,write,C,HAIR,NAVY,SKIN,IVORY,ICE

def main():
 baseline=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());actions={a['id']:a for a in d['actions']};profiles={p['id']:p for p in d['profiles']}
 changed=[a for a in d['actions']if a['contentDigest']!=baseline['digests'].get(a['id'])];target=[a for a in changed if a['profile']in['eileen-maps-story','eileen-maps-world','eileen-maps-tactical-idle','eileen-maps-tactical-walk']];outside=[a['id']for a in changed if a not in target]
 assert len(target)==17,[(a['id'])for a in target]
 assert all(a.startswith('professions-class-16-enemy-battle--')for a in outside),('Unexpected external action change',outside)
 assert not d['validation']['structuralIssues']and all(a['ready']for a in target)
 used_effects={e['sprite']for a in baseline['actions'].values()for row in a['frames']+a.get('revisedFrames',[])+a.get('reviewTailFrames',[])for e in row.get('effects',[])}
 for key in used_effects:assert d['effects'][key]==baseline['effects'][key],('Eileen effect changed',key)
 external_effects=[k for k in set(d['effects'])|set(baseline['effects'])if d['effects'].get(k)!=baseline['effects'].get(k)]
 assert all(k.startswith('review-c16-medusa-ray-')for k in external_effects)
 for path,digest in baseline['preserve'].items():assert file_hash(ROOT/path)==digest,('protected file',path)
 m=json.loads((ROOT/'eileen/maps/frame_mapping.json').read_text());old=baseline['mapping'];old_s={s['id']:s for s in old['scenarios']}
 new_s={s['id']:s for s in m['scenarios']}
 for s in m['scenarios']:
  prev=old_s[s['id']]
  for field in['source_atlas','source_frame_size','source_anchor','output_frame_size','output_anchor','logical_render_scale','directions','direction_mirror_x','timing','source_audit','ground_shadow']:
   assert s.get(field)==prev.get(field),(s['id'],field)
 assert new_s['story']['frame_mapping']==new_s['world']['frame_mapping']
 assert profiles['eileen-maps-story']['newFrames']==profiles['eileen-maps-world']['newFrames']
 for a in target:
  prev=baseline['actions'][a['id']]
  for field in['frames','fps','origin','viewport','contactTick','revisedFrames','reviewTailFrames']:assert a.get(field)==prev.get(field),(a['id'],field)
  assert profiles[a['profile']]['mapShadow']['alpha']>0
  assert all(row['offset']==[0,0]for row in a['frames'])
 for kind,ids in [('story',[2,3]),('tactical-walk',[2,3,6,7])]:
  now={x['source_index']:x for x in new_s[kind]['frame_mapping']};prev={x['source_index']:x for x in old_s[kind]['frame_mapping']}
  for i in ids:assert now[i]==prev[i],(kind,i,'unrequested pose changed')
 art=json.loads((OUT/'asset-manifest.json').read_text())
 for record in art['assets']:
  p=ROOT/record['path'];assert file_hash(p)==record['sha256'];im=Image.open(p);assert list(im.size)==record['size']
  if '/frame-'in str(p):
   q=im.convert('RGBA');assert set(q.getchannel('A').getdata())<={0,255};assert {c[:3]for c in q.getdata()if c[3]}<=set(C)
   assert any(c==(*HAIR,255)for c in q.getdata())
 for r in art['registrations']:
  assert r['clipped_pixels']==0 and not r['leg_mirroring']
  assert all(abs(a-b)<=.51 for a,b in zip(r['registered_crown'],r['target_crown']))
 def im(kind,i):return Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')
 gait=[]
 for kind,pair in [('story',[0,1]),('tactical-walk',[0,1]),('tactical-walk',[4,5])]:
  a,b=[im(kind,i)for i in pair]
  # A true depth step has a different planted foot on the bottom five rows;
  # it is not a horizontally mirrored entire lower-body plate.
  points=[]
  for q in[a,b]:
   bottom=q.getbbox()[3];p=[(x,y)for y in range(bottom-5,bottom)for x in range(q.width)if q.getpixel((x,y))[3]];points.append(sum(x for x,y in p)/len(p))
  assert 2<abs(points[0]-points[1])<10,(kind,pair,points)
  lower=a.crop((0,74,a.width,a.height));assert lower.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()!=b.crop((0,74,b.width,b.height)).tobytes()
  gait.append({'kind':kind,'frames':pair,'planted_boot_centers_x':points,'head_crown_fixed':True,'whole_lower_body_mirrored':False})
 # Side phases must now visibly differ in hair AND arm regions, unlike V1.
 a,b=im('story',4),im('story',5)
 for label,region in [('hair',(22,30,53,61)),('arms',(54,60,79,80)),('legs',(43,77,80,96))]:assert a.crop(region).tobytes()!=b.crop(region).tobytes(),label
 for i in[0,1,2]:
  q=im('tactical-idle',i);eye=q.crop((40,31,50,40));assert sum(c==(*NAVY,255)for c in eye.getdata())>=2,'eye line missing'
 for name in['import_eileen_map_v2.py','verify_eileen_map_v2.py']:ast.parse((ROOT/'tools'/name).read_text())
 report={'status':'assets_passed','revision':REV,'affected_actions':len(target),'other_actions_unchanged':len(d['actions'])-len(target)-len(outside),'concurrent_external_action_changes_preserved':outside,'protected_promoted_and_battle_files_unchanged':len(baseline['preserve']),'eileen_used_effects_unchanged':len(used_effects),'concurrent_external_effect_changes_preserved':len(external_effects),'native_source_frames_schedules_origins_and_fps_exact':True,'world_reuses_story_exactly':True,'continuous_map_shadows':True,'registered_crowns_within_half_pixel':True,'whole_body_offset_zero':True,'gait_checks':gait,'side_hair_arms_and_legs_have_distinct_phases':True,'idle_eye_line_present':True,'runtime_integrated':False,'browser_ui_checked':False,'user_visual_acceptance':'pending'}
 write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','changed_actions':len(target)}),flush=True)
 exports=[];videos=[]
 for a in target:exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
 for a in target:
  if a['kind']=='map_walk'or a['key']=='idle-cycle':
   e=export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False));exports.append(e);videos.append(e);print('Exported '+a['id'],flush=True)
 # Offline actual-size phase contact sheets show the persistent shadow too.
 captures=[]
 for light in[False,True]:
  samples=[]
  for aid in['eileen-maps-story--walk-down','eileen-maps-story--walk-right','eileen-maps-story--walk-left','eileen-maps-tactical-idle--idle-cycle','eileen-maps-tactical-walk--walk-up','eileen-maps-tactical-walk--walk-down']:
   a=actions[aid];p=profiles[a['profile']]
   for t in([0,14,22]if a['key']=='idle-cycle'else[0,16]):
    samples.append(render_frame(d,p,a,t,4,light))
  cw,ch=samples[0].size;board=Image.new('RGB',(cw*2,ch*((len(samples)+1)//2)),(14,21,26))
  for n,q in enumerate(samples):board.paste(q,(n%2*cw,n//2*ch))
  path=OUT/('playback-phases-'+('light'if light else'dark')+'.png');board.save(path,optimize=True);captures.append(relative(path))
 decoded=[]
 for e in videos:
  a=actions[e['action']];path=ROOT/e['video'];probe=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(path)],capture_output=True,text=True,check=True).stdout)['streams'][0]
  assert int(probe['nb_read_frames'])==playback_count(a)and abs(float(probe['duration'])-playback_count(a)/a['fps'])<1/a['fps'];decoded.append({'action':a['id'],'path':e['video'],**probe})
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for a in latest['actions']:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded})
 report.update(status='passed',stills=len(target),decoded_videos=len(decoded),offline_phase_boards=captures);write(OUT/'verification.json',report)
 print(json.dumps({'status':'passed','stills':len(target),'videos':len(decoded)}),flush=True)
if __name__=='__main__':main()
