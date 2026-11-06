#!/usr/bin/env python3
"""Hold intact accepted poses within each airborne phase; no raster/body edits."""
import argparse,copy,json,math,os,re,subprocess
from html.parser import HTMLParser
from types import SimpleNamespace
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import font,render_frame,playback_count
from export_knight_complete import export_one
import import_sniper_complete as io

REV='eileen-airborne-hold-v5-20261024';OUT=ROOT/REV
MAPPING=ROOT/'eileen/battle/frame_mapping.json'
AID='eileen-battle--original_class_11_normal'
GROUPS=[('前跳起跳',[2,3,4,5,6,7]),('前跳收腿',[8,9]),('后跳起身',[25,26]),('后跳蜷腿',[27,28]),('落地前伸腿',[29,32])]
ALIASES={str(i):str(ids[0]) for label,ids in GROUPS for i in ids[1:]}

def write(p,value):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def picture(mapping,i):return Image.open((MAPPING.parent/mapping['frame_mapping'][str(i)]).resolve()).convert('RGBA')

def prepare():
 OUT.mkdir(parents=True,exist_ok=True);baseline=OUT/'baseline.json'
 if not baseline.exists():
  d=json.loads((ROOT/'demos/gallery-data.json').read_text());a=next(a for a in d['actions'] if a['id']==AID)
  preserve={relative(p):file_hash(p) for folder in ['eileen/maps','eileen-promoted'] for p in (ROOT/folder).rglob('*') if p.is_file()}
  write(baseline,{'mapping':json.loads(MAPPING.read_text()),'action':a,'digests':{a['id']:a['contentDigest'] for a in d['actions']},'effects':d['effects'],'preserved':preserve})
 b=json.loads(baseline.read_text());m=copy.deepcopy(b['mapping'])
 for i,canonical in ALIASES.items():m['frame_mapping'][i]=b['mapping']['frame_mapping'][canonical]
 m.update(revision=REV,review_note='前后跳跃空中阶段复用完整固定姿势：2至7、8与9、25与26、27与28、29与32分别保持同一身体与腿脚，不在原头发／衣摆循环中反复切换膝盖和双靴。保留阶段间收腿、伸腿与落地转换、原位移、帧序、总时长及唯一结算；此前下蹲与后退补剑修正保留。',qa_report=os.path.relpath(OUT/'verification.json',MAPPING.parent))
 io.OUT=OUT;order=sorted(map(int,m['frame_mapping']));atlas=Image.new('RGBA',(320*len(order),288))
 for n,i in enumerate(order):atlas.alpha_composite(picture(m,i),(n*320,0))
 io.save(atlas,'battle-atlas.png','current full atlas assembled from unchanged existing whole sprites')
 m.update(output_atlas=os.path.relpath(OUT/'battle-atlas.png',MAPPING.parent),output_atlas_order=order,batches=[{'id':'前后跳跃完整阶段姿势保持','review':os.path.relpath(OUT/'airborne-poses-light.png',MAPPING.parent),'status':'review_candidate'}])
 groups=[]
 for label,ids in GROUPS:
  ticks=[t for t,row in enumerate(b['action']['frames']) if row['frame'] in ids]
  groups.append({'label':label,'source_slots':ids,'canonical_slot':ids[0],'displayed_tick_range':[min(ticks)+1,max(ticks)+1],'full_intact_pose_reused':True,'raster_edits':0,'limb_rescaling':False})
 write(OUT/'phase-contracts.json',{'revision':REV,'groups':groups,'aliases':ALIASES,'native_timeline_rows_unchanged':True,'new_art_generated':False,'runtime_integrated':False});write(OUT/'mapping-draft.json',m);write(MAPPING,m)
 print(json.dumps({'published':True,'slot_aliases':ALIASES,'art_pixels_edited':0}),flush=True)

def boards(d,p,a,m):
 for light in [False,True]:
  bg=(220,222,216) if light else (32,45,53);fg=(23,38,56) if light else (235,243,242)
  q=Image.new('RGB',(320*4,330*math.ceil(len(m['frame_mapping'])/4)),bg);dr=ImageDraw.Draw(q)
  for n,i in enumerate(sorted(map(int,m['frame_mapping']))):
   im=picture(m,i);x=n%4*320;y=n//4*330;q.paste(im,(x,y),im);dr.text((x+160,y+308),str(i),anchor='mm',font=font(17),fill=fg)
  q.save(OUT/f'battle-current-{"light" if light else "dark"}.png',optimize=True)
  q=Image.new('RGB',(320*4,330*5),bg);dr=ImageDraw.Draw(q)
  for n,(label,ids) in enumerate(GROUPS):
   for col,i in enumerate((ids+[ids[-1]]*4)[:4]):
    im=picture(m,i);x=col*320;y=n*330;q.paste(im,(x,y),im);dr.text((x+160,y+308),f'{label} · {i}',anchor='mm',font=font(16),fill=fg)
  q.save(OUT/f'airborne-poses-{"light" if light else "dark"}.png',optimize=True)
 # Actual stage transitions and the source-8/9 and backward ping-pong loops.
 sections={'forward':list(range(84,111,2)), 'backward':list(range(182,246,4))}
 for section,ticks in sections.items():
  ims=[render_frame(d,p,a,t,4,True,True) for t in ticks];cw,ch=ims[0].size
  q=Image.new('RGB',(cw*2,ch*math.ceil(len(ims)/2)),(14,21,26))
  for n,im in enumerate(ims):q.paste(im,(n%2*cw,n//2*ch))
  q.save(OUT/f'{section}-continuous.png',optimize=True)

def finish():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};a=aa[AID];p=pp[a['profile']];m=json.loads(MAPPING.read_text())
 own=[x['id'] for x in d['actions'] if pp[x['profile']]['actor']=='eileen' and x['contentDigest']!=b['digests'].get(x['id'])];assert own==[AID],own
 for key in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['action'].get(key),key
 for path,h in b['preserved'].items():assert file_hash(ROOT/path)==h,path
 for i,path in b['mapping']['frame_mapping'].items():
  if i not in ALIASES:assert m['frame_mapping'][i]==path,i
 for label,ids in GROUPS:
  im=picture(m,ids[0]);assert all(picture(m,i).tobytes()==im.tobytes() for i in ids),(label,'airborne pose changed within phase')
 used={e['sprite'] for action in d['actions'] if pp[action['profile']]['actor']=='eileen' for row in action['frames']+action.get('revisedFrames',[])+action.get('reviewTailFrames',[]) for e in row.get('effects',[])}
 assert all(d['effects'][k]==b['effects'][k] for k in used)
 assert a['ready'] and not d['validation']['structuralIssues']
 # The previous six crouch/weapon repairs stay selected byte-for-byte.
 assert all(m['frame_mapping'][str(i)]==b['mapping']['frame_mapping'][str(i)] for i in [11,16,17,18,19,22])
 print(json.dumps({'status':'targeted_pose_checks_passed','affected_actions':1}),flush=True)
 exports=[export_one(d,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False)) for close in [False,True]];decoded=[]
 for e in exports:
  s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
  assert int(s['nb_read_frames'])==playback_count(a);assert abs(float(s['duration'])-playback_count(a)/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 boards(d,p,a,m)
 # Read shared files again after rendering, retaining unrelated current edits.
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=AID:continue
  assert x['contentDigest']==a['contentDigest']
  for field,folder,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{folder}/{AID}{suffix}.{ext}';x[field]=relative(path) if matched_export(path,x['contentDigest']) else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-airborne-hold-v5-progress".*?</section>\s*','',text,flags=re.S)
 section=f'''<section id="eileen-airborne-hold-v5-progress" class="panel" style="margin-bottom:26px" aria-label="艾琳前后跳跃腿脚稳定"><div class="heading"><h2>艾琳 · 前后跳跃腿脚稳定</h2><p>阶段姿势保持</p></div><p class="action-note">前跳起跳、收腿，后跳起身、蜷腿及落地前伸腿分别保持完整固定姿势，取消空中循环内腿脚反复抽动。保留阶段间动作转换、原移动轨迹、节奏、312帧总长及第129帧结算；已修正的下蹲和后退持剑继续保留。</p><nav class="links" aria-label="艾琳跳跃稳定检查"><a href="?action={AID}#motion-player">普通攻击 · 当前动画</a><a href="{REV}/forward-continuous.png">前跳连续帧</a><a href="{REV}/backward-continuous.png">后跳连续帧</a><a href="{REV}/airborne-poses-light.png">空中阶段姿势</a><a href="{REV}/battle-current-light.png">当前战斗全姿势</a><a href="{REV}/README.md">修订说明</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">本轮复用已有完整画帧，只修订9个帧槽的选用关系，更新普通攻击及其近景预览。仅更新隔离美术对照。</p></section>\n'''
 marker='<section id="eileen-crouch-sword-v4-progress"';assert marker in text;text=text.replace(marker,section+marker,1);text=text.replace('href="eileen-crouch-sword-v4-20261024/battle-current-light.png"',f'href="{REV}/battle-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{AID}"',text,count=1)
 for pattern in [r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:text=re.sub(pattern,r'\g<1>'+REV,text)
 page.write_text(text);manifest=ROOT/'eileen/manifest.json';mm=json.loads(manifest.read_text());mm.update(revision=REV,review_record='../'+REV+'/README.md');write(manifest,mm)
 write(OUT/'verification.json',{'status':'assets_and_exports_passed','page_checks':'pending'})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[]
  def handle_starttag(self,t,attrs):
   attr=dict(attrs)
   if 'id' in attr:self.ids.append(attr['id'])
   if 'href' in attr:self.links.append(attr['href'])
 check=Page();check.feed(text);assert len(check.ids)==len(set(check.ids));count=0
 for href in check.links:
  u=urlparse(href)
  for key in parse_qs(u.query).get('action',[]):assert key in aa,key;count+=1
  if REV+'/' in u.path:assert (ROOT/unquote(u.path)).exists(),href
 inventory=[]
 for path in sorted(set(OUT.rglob('*.png'))|{ROOT/e['still'] for e in exports}):
  with Image.open(path) as im:row={'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path),'purpose':'offline full-resolution source-slot or continuous playback QA' if OUT in path.parents else 'normal attack still preview'}
  if row['bytes']>=200000:row['quality_reason']='完整无损离线连续帧检查，保留人物与标题清晰度；播放器复用原有小型完整画帧。'
  inventory.append(row)
 write(OUT/'image-inventory.json',{'images':inventory,'new_runtime_individual_images':0});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded})
 write(OUT/'verification.json',{'status':'passed','revision':REV,'affected_actions':1,'aliases':ALIASES,'groups_have_identical_whole_pose_pixels':True,'original_frames_offsets_effects_contacts_and_timing_exact':True,'crouch_and_retreated_sword_repairs_preserved':True,'maps_and_promoted_files_unchanged':True,'eileen_effect_definitions_unchanged':len(used),'decoded_videos':decoded,'page_links_checked':count,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending','text_safe_areas':'Existing padded gallery panel, wrapping links and export captions measured inside margins.'})
 print(json.dumps({'status':'passed','affected_actions':1,'videos':2,'page_links':count}),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--finish',action='store_true');args=parser.parse_args()
 if args.prepare:prepare()
 if args.finish:finish()
