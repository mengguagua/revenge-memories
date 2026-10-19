from pathlib import Path
from PIL import Image
from fractions import Fraction
import json,hashlib,subprocess
V=Path(__file__).resolve().parents[1];R=V.parent
before=json.loads((V/'reference/gallery-before.json').read_text());after=json.loads((R/'demos/gallery-data.json').read_text())
old={a['id']:a for a in before['actions']};new={a['id']:a for a in after['actions']}
ids={a['id']for a in after['actions']if a['profile']in ['professions-class-12-ally-battle','professions-class-12-enemy-battle']}
assert old.keys()==new.keys()
for k in old:
 for field in ['frames','origin','fps','contactTick','duration']:assert old[k][field]==new[k][field],(k,field)
 assert (old[k]['contentDigest']!=new[k]['contentDigest'])==(k in ids),k
assert before['effects']==after['effects']
images=[]
for side in ['ally','enemy']:
 profile=next(p for p in after['profiles']if p['id']==f'professions-class-12-{side}-battle')
 palette=set()
 for k,path in profile['newFrames'].items():
  im=Image.open(R/path).convert('RGBA');colors={c[:3]for c in im.getdata()if c[3]};palette.update(colors)
  assert im.size==(320,256) and set(im.getchannel('A').getdata())=={0,255}
  record=next(x for x in json.loads((V/'registration.json').read_text())['records']if x['side']==side and str(x['frame'])==k)
  b=im.getbbox();assert b[3]-b[1]==record['original_bounds'][3]-record['original_bounds'][1]
  assert abs((b[2]-b[0])/(record['original_bounds'][2]-record['original_bounds'][0])-1.10)<.02
  f=im.crop((0,246,320,256)).getbbox();center=(f[0]+f[2])/2
  assert abs(center-record['target_foot_anchor'][0])<=.5
 assert len(palette)==32
 for key,meta in profile['revisedEffects'].items():
  original=before['effects'][key]
  assert {k:v for k,v in meta.items()if k!='path'}=={k:v for k,v in original.items()if k!='path'}
  im=Image.open(R/meta['path']).convert('RGBA');assert im.size==(192,64)
  assert {c[:3]for c in im.getdata()if c[3]}<=palette
  assert im.getbbox()==(104,40,184,52)
  assert all(im.getpixel((x,y))[3]==255 and min(im.getpixel((x,y))[:3])>140 for x in range(119,163)for y in range(44,48))
for path in sorted((V/'deliverables').rglob('*.png')):
 im=Image.open(path);assert path.stat().st_size<50000
 images.append({'path':str(path.relative_to(R)),'purpose':'character atlas'if'frame-'in path.name or'atlas'in path.name else'faction flying arrow','pixels':list(im.size),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
videos=[]
for id in sorted(ids):
 a=new[id];assert a['video'] and a['still']
 for key in ['video','closeVideo']:
  if not a.get(key):continue
  path=R/a[key];sidecar=json.loads(path.with_suffix('.json').read_text());assert sidecar['contentDigest']==a['contentDigest']
  p=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(path)],text=True))['streams'][0]
  assert int(p['nb_frames'])==len(a['frames']) and abs(float(Fraction(p['r_frame_rate']))-a['fps'])<.00001
  videos.append({'path':a[key],'frames':int(p['nb_frames']),'pixels':[p['width'],p['height']],'fps':p['r_frame_rate'],'bytes':path.stat().st_size})
assert (V/'overview.mp4').is_file()
validation=json.loads((R/'demos/validation-report.json').read_text());assert validation['pass']
assert not subprocess.check_output(['git','diff','--name-only','--','actual'],cwd=R.parents[1],text=True).strip()
report={'revision':V.name,'status':'pending_user_visual_acceptance','scope':'双方 class12 弓箭手的战斗场景；未改地图，未改游戏，未更新测试包','generation':'ImageGen precise edit, then alpha cleanup, XY foot registration, shared palette and lossless PNG optimization','width_increase':'9.3%–10.5% measured visible bounds','height_preserved':True,'max_foot_anchor_error_px_at_4x':.5,'shared_palette_opaque_colors_per_faction':32,'arrow_colors_from_character_palette':True,'arrow_geometry':'48x16 logical canvas, 192x64 image; visible area and effect anchor unchanged; cream shaft core kept at least one native pixel thick','actions_updated':len(ids),'actions_preserved':len(new)-len(ids),'all_547_timelines_origins_contacts_and_effect_trajectories_identical':True,'original_effect_images_and_metadata_preserved':True,'effect_overrides_scoped_to_two_profiles':True,'new_body_frames':6,'new_flying_arrow_images':2,'full_videos':26,'close_videos':5,'total_videos':len(videos),'video_probes':videos,'images':images,'gallery_validation':{'passed':validation['pass'],'alpha_extent_checks':validation['real_alpha_extent_checks'],'geometry_errors':len(validation['geometry_errors']),'structural_errors':len(validation['structural_errors'])},'manual_visual_review':['six previous/current poses','ally original-frame48 projectile moment','ally fully drawn bow close view','ally launch frame on dark ground','enemy launch frame on light ground'],'browser_visual_inspection':'Blocked by browser file URL security policy; no workaround attempted. Static frames and offline video exports checked instead.','game_files_changed':False,'no_new_test_package':True,'notes':['Source ImageGen sheet and previous accepted frames are retained as references.','Flight-arrow recoloring leaves shared original effects intact, including other professions and original reference panels.','Existing native holy-bow supplementary effects are retained; only its arrow projectile receives the faction palette.','User visual approval remains required before runtime import.']}
(V/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['actions_updated','actions_preserved','total_videos','new_body_frames','game_files_changed','gallery_validation']},ensure_ascii=False))
