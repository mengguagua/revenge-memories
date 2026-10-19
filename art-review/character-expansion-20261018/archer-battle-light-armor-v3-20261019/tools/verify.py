from pathlib import Path
from PIL import Image
from fractions import Fraction
from collections import Counter
import json,hashlib,subprocess
V=Path(__file__).resolve().parents[1];R=V.parent
before=json.loads((V/'reference/gallery-before.json').read_text());after=json.loads((R/'demos/gallery-data.json').read_text());reg=json.loads((V/'registration.json').read_text())
a={x['id']:x for x in before['actions']};b={x['id']:x for x in after['actions']}
assert a.keys()==b.keys();ids={k for k,x in b.items()if x['profile']in ['professions-class-12-ally-battle','professions-class-12-enemy-battle']}
for k in a:
 for field in ['frames','origin','fps','contactTick','duration']:assert a[k][field]==b[k][field],(k,field)
 assert (a[k]['contentDigest']!=b[k]['contentDigest'])==(k in ids)
assert before['effects']==after['effects']
colors_report={};images=[]
for side,keys in [('ally',[1,4,5]),('enemy',[1,5,6])]:
 palette={tuple(bytes.fromhex(c[1:]))for c in reg['palettes'][side]};all_colors=set();frame_report=[]
 violet={tuple(bytes.fromhex(c[1:]))for c in reg['palettes']['enemy'][1:4]}
 for k in keys:
  p=V/f'deliverables/{side}/frame-{k:03d}.png';im=Image.open(p).convert('RGBA');prev=Image.open(V/f'reference/{side}-{k}.png').convert('RGBA')
  assert im.size==prev.size==(320,256)
  box=im.getbbox();old=prev.getbbox();assert (box[2]-box[0],box[3]-box[1])==(old[2]-old[0],old[3]-old[1])
  opaque=[c[:3]for c in im.getdata()if c[3]];cs=set(opaque);all_colors|=cs
  assert cs<=palette and set(im.getchannel('A').getdata())=={0,255}
  feet=im.crop((0,246,320,256)).getbbox();center=(feet[0]+feet[2])/2;target=208 if side=='ally'else 144
  assert abs(center-target)<=.5
  purple=sum(c in violet for c in opaque)/len(opaque)
  if side=='enemy':assert purple>.3
  frame_report.append({'frame':k,'opaque_colors':len(cs),'bounds':box,'foot_anchor':[center,box[3]],'blue_violet_pixel_fraction':round(purple,4)})
 assert 0<len(all_colors)<=10
 ar=Image.open(V/f'deliverables/{side}/flying-arrow.png').convert('RGBA');previous=Image.open(V/f'reference/{side}-arrow.png').convert('RGBA')
 assert ar.size==previous.size==(192,64) and ar.getchannel('A').tobytes()==previous.getchannel('A').tobytes()
 assert {c[:3]for c in ar.getdata()if c[3]}<=palette
 assert (V/f'deliverables/{side}/flying-arrow.png').read_bytes()==(V/f'reference/{side}-arrow.png').read_bytes()
 colors_report[side]={'previous_shared_colors':10,'current_shared_colors':len(all_colors),'palette':reg['palettes'][side],'frames':frame_report,'projectile_mask_preserved':True}
for p in sorted((V/'deliverables').rglob('*.png')):
 im=Image.open(p);assert p.stat().st_size<50000
 images.append({'path':str(p.relative_to(R)),'pixels':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
video_probes=[]
for k in sorted(ids):
 action=b[k];assert action['video']and action['still']
 for mode in ['video','closeVideo']:
  if not action.get(mode):continue
  p=R/action[mode];assert json.loads(p.with_suffix('.json').read_text())['contentDigest']==action['contentDigest']
  m=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate,width,height','-of','json',str(p)],text=True))['streams'][0]
  assert int(m['nb_frames'])==len(action['frames'])and abs(float(Fraction(m['r_frame_rate']))-action['fps'])<.00001
  video_probes.append({'path':action[mode],**m,'bytes':p.stat().st_size})
validation=json.loads((R/'demos/validation-report.json').read_text());assert validation['pass']
assert not subprocess.check_output(['git','diff','--name-only','--','actual'],cwd=R.parents[1],text=True).strip()
report={'revision':V.name,'status':'pending_user_visual_acceptance','scope':'仅双方弓箭手战斗场景轻甲服装重绘，保留已验收配色；未接入游戏','colors':colors_report,'all_source_timelines_and_contacts_preserved':True,'previous_body_width_height_preserved':True,'foot_anchor_max_error_4x_pixels':.5,'arrow_geometry_and_source_effects_preserved':True,'changed_actions':len(ids),'unchanged_actions':len(b)-len(ids),'video_probes':video_probes,'images':images,'geometry_validation':{'passed':validation['pass'],'alpha_extent_checks':validation['real_alpha_extent_checks'],'errors':len(validation['geometry_errors'])},'game_files_changed':False,'new_package_created':False,'manual_visual_review':['six previous/current poses','ally/enemy same-size dark-background pair','light-background faction pair and original-projectile launch stills'],'browser_visual_inspection':'Not performed: local-file browser access was blocked previously; offline comparisons and frame geometry are verified.','notes':['Both approved ten-color palettes are retained; individual frames may use fewer colors. Ally uses teal underlayer with brown leather armor; enemy armor stays blue-violet. Small shoulder protection, bracers and split hip guards replace ornamental tunics.','Skin and hair remain warm-colored. Accepted flying-arrow PNG files are byte-identical; only clothing was regenerated.','Generated source and prior frames retained; lossless optimization applied to prepared PNGs.']}
(V/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'actions':len(ids),'other_actions_preserved':len(b)-len(ids),'videos':len(video_probes),'palettes':{k:v['current_shared_colors']for k,v in colors_report.items()},'pass':True},ensure_ascii=False))
