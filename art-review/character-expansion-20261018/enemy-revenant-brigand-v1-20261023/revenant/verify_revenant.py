#!/usr/bin/env python3
"""Verify this isolated class11 review candidate; no gallery/game mutations."""
from pathlib import Path
from PIL import Image
import hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parent.parent
BASE=json.loads((OUT/'source/native-baseline.json').read_text())
def read(p):return json.loads(p.read_text())
def hashbytes(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(p):return Image.open(p).convert('RGBA')
def asset(path):return (ROOT/'professions/class-11-enemy/battle'/path).resolve()
checks=[]
def check(ok,label):
 checks.append({'label':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
m=read(OUT/'mapping-drafts.json');manifest=read(OUT/'asset-manifest.json');battle=m['professions/class-11-enemy/battle/frame_mapping.json'];maps=m['professions/class-11-enemy/maps/frame_mapping.json']
check(battle['variant_keys']==list(BASE['variants']),'all and only native class11 variants')
check('review_timeline'not in battle,'no custom temporal rewrite or extra tail')
check(set(map(int,battle['frame_mapping']))==set(BASE['body']['required_source_frames']),'every required body source frame mapped')
for key,v in BASE['variants'].items():
 summary=BASE['variant_summaries'][key];check(len(v['frames'])==summary['ticks']==472,'native 472 tick cycle '+key);check(v['contact_tick']==summary['contact_tick']==274,'native contact tick274 '+key)
 digest=hashlib.sha256(json.dumps(v['frames'],sort_keys=True,separators=(',',':')).encode()).hexdigest();check(digest==summary['frame_rows_sha256'],'native frame/offset/flip/effect sequence exact '+key)
for s in maps['scenarios']:
 if s['id']=='tactical-idle':check(s['timing']['cycle_frames']==[0,1,2,1]and s['timing']['frame_ticks']==[14,8,14,8],'idle pose order and phase timing exact')
 else:check(s['directions']=={'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7]}and s['timing']['frame_ticks']==16,'eight independent directional source slots and16tick holds')
 check(s['source_anchor']==([12,20]if s['id']=='tactical-idle'else[16,24]),'native map anchor '+s['id'])
for a in manifest['assets']:
 path=ROOT/a['path'];im=Image.open(path);check(im.size==tuple(a['size'])and path.stat().st_size==a['bytes']and hashbytes(path)==a['sha256'],'asset size/hash '+a['path'])
for r in manifest['registration']:
 check(r['landmark_kind']in['head_neck','hip','native_ground_residue']and r['clipped_pixels']==0 and r['landmark_error_pixels']<=.51,'anatomical registration without clipped pixels '+r['kind']+str(r['frame']))
paths=battle['frame_mapping'];p33=rgba(asset(paths['33']));p83=rgba(asset(paths['83']));shifted=Image.new('RGBA',p33.size);shifted.alpha_composite(p33,(-64,0));check(shifted.tobytes()==p83.tobytes(),'BG83 is exact idle33 shifted -16logical X')
check(rgba(asset(paths['98'])).tobytes()==p83.tobytes(),'BG98 exact alias83')
check(rgba(asset(paths['49'])).getbbox()is None,'native submerged interval49 stays fully transparent')
expected=rgba(asset(paths['48']));arc=rgba(OUT/'source/native-claw-arc-047.png').resize(expected.size,Image.Resampling.NEAREST);expected.alpha_composite(arc);check(expected.tobytes()==rgba(asset(paths['47'])).tobytes(),'attack47 preserves original claw arc over exact body48')
palette={tuple(bytes.fromhex(c))for c in manifest['palette']}
for n,path in paths.items():
 if int(n)==47:continue
 check(all(p[:3]in palette for p in rgba(asset(path)).getdata()if p[3]),'six body materials only '+n)
motion=read(OUT/'map-registration-checks.json')
check(motion['passed'] and len(motion['metrics'])==5,'all five map cycles have measured anatomical drift and head-size comparison')
for group in motion['metrics']:check(group['passed'],'map head/waist registration '+group['group'])
foot=read(OUT/'native-foot-phase-checks.json')
check(foot['passed'] and len(foot['slots'])==8,'all eight walk slots match native support leg or open/passing phase')
for row in foot['slots']:check(row.get('support_phase_matches',True),'native foot phase slot'+str(row['slot']))
report={'native_foot_phase':foot,'map_core_measurements':motion['metrics'],'continuous_frame_boards':['map-continuous-dark.png','map-continuous-light.png'],'passed':True,'scope':'isolated candidate only; original timeline/order/contact unchanged, full source slots/aliases, anatomical registration, source silhouette pixel checks and asset integrity. Final visual acceptance remains with user.','checks':len(checks),'results':checks,'runtime_integrated':False,'shared_gallery_modified':False,'palette':manifest['palette'],'native_programs':{k:{'ticks':len(v['frames']),'contact_tick':v['contact_tick']}for k,v in BASE['variants'].items()}}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('REVENANT_VERIFIED',len(checks))
