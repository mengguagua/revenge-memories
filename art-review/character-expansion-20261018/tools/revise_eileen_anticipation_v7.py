#!/usr/bin/env python3
"""Replace only the undersized rest pose1 with the matching complete pose0."""
import argparse,copy,json,os,re,subprocess,math
from types import SimpleNamespace
from PIL import Image,ImageDraw,ImageChops
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import font,render_frame,playback_count
from export_knight_complete import export_one
import import_sniper_complete as io
REV='eileen-anticipation-v7-20261024';OUT=ROOT/REV;MAPPING=ROOT/'eileen-promoted/battle/frame_mapping.json';AID='eileen-promoted-battle--original_class_11_normal'
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def picture(m,i):return Image.open((MAPPING.parent/m['frame_mapping'][str(i)]).resolve()).convert('RGBA')

def prepare():
 OUT.mkdir(parents=True,exist_ok=True);path=OUT/'baseline.json'
 if not path.exists():
  d=json.loads((ROOT/'demos/gallery-data.json').read_text());m=json.loads(MAPPING.read_text());a=next(a for a in d['actions']if a['id']==AID);files={(MAPPING.parent/s).resolve()for s in m['frame_mapping'].values()};files|={p for p in (ROOT/'eileen-promoted/maps').rglob('*')if p.is_file()};write(path,{'mapping':m,'action':a,'digests':{x['id']:x['contentDigest']for x in d['actions']},'effects':d['effects'],'preserved':{relative(p):file_hash(p)for p in files}})
 b=json.loads(path.read_text());m=copy.deepcopy(b['mapping']);m['frame_mapping']['1']=m['frame_mapping']['0'];m.update(revision=REV,review_note='第1姿势原图比前后第0／23站姿偏小；第1帧槽直接复用第0完整站姿，消除攻击前第10至13帧及回位第302至307帧整体缩小再恢复。保留身前持剑、落地屈腿后一次站直、其余姿势、312帧总长和第129帧唯一结算。',qa_report=os.path.relpath(OUT/'verification.json',MAPPING.parent))
 io.OUT=OUT;order=sorted(map(int,m['frame_mapping']));atlas=Image.new('RGBA',(320*len(order),288))
 for n,i in enumerate(order):atlas.alpha_composite(picture(m,i),(n*320,0))
 io.save(atlas,'battle-atlas.png','complete promoted battle atlas with rest pose1 using the existing pose0')
 m.update(output_atlas=os.path.relpath(OUT/'battle-atlas.png',MAPPING.parent),output_atlas_order=order,batches=[{'id':'攻击前站姿体型保持','review':os.path.relpath(OUT/'anticipation-detail.png',MAPPING.parent),'status':'review_candidate'}]);write(OUT/'mapping-draft.json',m);write(MAPPING,m);write(OUT/'asset-manifest.json',{'revision':REV,'changed_slots':[1],'alias':{'1':'0'},'existing_images_unchanged':True,'new_character_art':False,'runtime_integrated':False,'assets':io.ASSETS});print(json.dumps({'published':True,'only_alias':{'1':'0'}}),flush=True)

def finish():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={x['id']:x for x in d['actions']};a=aa[AID];p=next(x for x in d['profiles']if x['id']==a['profile']);m=json.loads(MAPPING.read_text());own=[x['id']for x in d['actions']if x['profile']=='eileen-promoted-battle'and x['contentDigest']!=b['digests'].get(x['id'])];assert own==[AID],own
 for k in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(k)==b['action'].get(k),k
 for path,h in b['preserved'].items():assert file_hash(ROOT/path)==h,path
 for i,path in b['mapping']['frame_mapping'].items():
  if i!='1':assert m['frame_mapping'][i]==path,i
 assert picture(m,0).tobytes()==picture(m,1).tobytes()==picture(m,23).tobytes();rows=a.get('revisedFrames',a['frames']);assert all(picture(m,row['frame']).tobytes()==picture(m,0).tobytes()for row in rows[:20]);affected=[t+1 for t,row in enumerate(rows)if row['frame']==1];assert affected==list(range(10,14))+list(range(302,308)),affected
 used={e['sprite']for action in d['actions']if action['profile']=='eileen-promoted-battle'for row in action['frames']+action.get('revisedFrames',[])+action.get('reviewTailFrames',[])for e in row.get('effects',[])};assert all(d['effects'][k]==b['effects'][k]for k in used);assert a['ready']and not d['validation']['structuralIssues'];print(json.dumps({'status':'rest_pose_size_fixed','affected_displayed_frames':affected}),flush=True)
 exports=[export_one(d,a,SimpleNamespace(close=c,scale=4,light=False,stills_only=False))for c in [False,True]];decoded=[]
 for e in exports:
  s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(s['nb_read_frames'])==playback_count(a)==312;assert abs(float(s['duration'])-312/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 for light in [True,False]:
  bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);q=Image.new('RGB',(1280,330),bg);dr=ImageDraw.Draw(q)
  for n,(i,name)in enumerate([(0,'站姿0'),(1,'修正后1'),(23,'站姿23'),(1,'修正前1')]):
   im=picture(b['mapping']if n==3 else m,i);q.paste(im,(n*320,0),im);dr.text((n*320+160,308),name,anchor='mm',font=font(18),fill=fg)
  q.save(OUT/f'pose-comparison-{"light"if light else"dark"}.png',optimize=True)
 ticks=[0,8,9,11,12,13,18,19,20];ims=[render_frame(d,p,a,t,4,True,True)for t in ticks];cw,ch=ims[0].size;q=Image.new('RGB',(cw*3,ch*3),(14,21,26))
 for n,im in enumerate(ims):q.paste(im,(n%3*cw,n//3*ch))
 q.save(OUT/'anticipation-continuous.png',optimize=True);pieces=[im.crop((624,76,1200,524))for im in ims];bb=None
 for im in pieces:
  z=ImageChops.difference(im,Image.new('RGB',im.size,(220,222,216))).getbbox();bb=z if bb is None else(min(bb[0],z[0]),min(bb[1],z[1]),max(bb[2],z[2]),max(bb[3],z[3]))
 bb=(bb[0]-14,bb[1]-14,bb[2]+14,bb[3]+14);tw=bb[2]-bb[0];th=bb[3]-bb[1]+44;q=Image.new('RGB',(tw*3,th*3),(220,222,216));dr=ImageDraw.Draw(q)
 for n,(im,t)in enumerate(zip(pieces,ticks)):x=n%3*tw;y=n//3*th;q.paste(im.crop(bb),(x,y));dr.text((x+tw/2,y+th-22),f'第 {t+1} 帧',font=font(16),anchor='mm',fill=(23,38,56))
 q.save(OUT/'anticipation-detail.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=AID:continue
  assert x['contentDigest']==a['contentDigest']
  for field,folder,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{folder}/{AID}{suffix}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-anticipation-v7-progress".*?</section>\s*','',text,flags=re.S);panel=f'''<section id="eileen-anticipation-v7-progress" class="panel" style="margin-bottom:26px" aria-label="引光剑使攻击前体型保持"><div class="heading"><h2>引光剑使 · 攻击前体型保持</h2><p>第0、1、23站姿保持同一体型</p></div><p class="action-note">修正第1姿势偏小造成的整体缩小再恢复：第1帧槽直接复用同一完整站姿，攻击前第1至20帧体型与中心保持，第10至13帧不再突然缩小。回位使用第1姿势的第302至307帧同步保持。后续起势、空中、落地屈腿后一次站直、身前持剑以及原312帧和第129帧结算保持。</p><nav class="links" aria-label="攻击前体型检查"><a href="?action={AID}#motion-player">普通攻击 · 当前动画</a><a href="{REV}/anticipation-detail.png">攻击前连续细节</a><a href="{REV}/pose-comparison-light.png">修正前后 · 浅底</a><a href="{REV}/pose-comparison-dark.png">修正前后 · 深底</a><a href="{REV}/README.md">修订与检查记录</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">只修改1个帧槽的选用关系，原画不缩放、不重绘；更新正常／近景预览，仅用于隔离美术对照。</p></section>\n''';marker='<section id="eileen-landing-v6-progress"';assert marker in text;text=text.replace(marker,panel+marker,1);text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{AID}"',text,count=1)
 for pattern in [r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:text=re.sub(pattern,r'\g<1>'+REV,text)
 page.write_text(text);mf=ROOT/'eileen-promoted/manifest.json';v=json.loads(mf.read_text());v.update(revision=REV,review_record='../'+REV+'/README.md');write(mf,v);write(OUT/'verification.json',{'status':'assets_and_exports_passed'})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[]
  def handle_starttag(self,t,attrs):
   at=dict(attrs)
   if'id'in at:self.ids.append(at['id'])
   if'href'in at:self.links.append(at['href'])
 check=Page();check.feed(text);assert len(check.ids)==len(set(check.ids));count=0
 for href in check.links:
  u=urlparse(href)
  for key in parse_qs(u.query).get('action',[]):assert key in aa,key;count+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 inventory=[]
 for path in sorted(set(OUT.rglob('*.png'))|{ROOT/e['still']for e in exports}):
  with Image.open(path)as im:row={'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path)}
  if row['bytes']>=200000:row['quality_reason']='无损离线连续对照图，保留人物与标签清晰度；播放器直接复用既有完整小图。'
  inventory.append(row)
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory,'new_individual_character_images':0});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'affected_actions':1,'changed_slots':[1],'alias':{'1':'0'},'affected_displayed_frames':affected,'poses_0_1_23_identical_pixels':True,'first_20_frames_size_and_center_fixed':True,'all_other_frame_paths_existing_images_and_maps_preserved':True,'native_frames_offsets_contacts_and_timing_exact':True,'promoted_effect_definitions_unchanged':len(used),'decoded_videos':decoded,'page_links_checked':count,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending'});print(json.dumps({'status':'passed','actions':1,'videos':2,'page_links':count}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--finish',action='store_true');args=p.parse_args()
 if args.prepare:prepare()
 if args.finish:finish()
