#!/usr/bin/env python3
"""Select bent landing then standing, retaining complete existing sprite poses."""
import argparse,copy,json,math,os,re,subprocess
from html.parser import HTMLParser
from types import SimpleNamespace
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image,ImageDraw,ImageChops
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import font,render_frame,playback_count
from export_knight_complete import export_one
import import_sniper_complete as io
REV='eileen-landing-v6-20261024';OUT=ROOT/REV;SRC=OUT/'source'
MAPPING=ROOT/'eileen-promoted/battle/frame_mapping.json';AID='eileen-promoted-battle--original_class_11_normal'
CHANGED=[30,31,11,23];ALIASES={'30':'11','31':'11','23':'0'}

def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def picture(m,i):return Image.open((MAPPING.parent/m['frame_mapping'][str(i)]).resolve()).convert('RGBA')

def prepare():
 OUT.mkdir(parents=True,exist_ok=True);SRC.mkdir(exist_ok=True);path=OUT/'baseline.json'
 if not path.exists():
  d=json.loads((ROOT/'demos/gallery-data.json').read_text());m=json.loads(MAPPING.read_text());a=next(a for a in d['actions']if a['id']==AID);selected={(MAPPING.parent/s).resolve()for s in m['frame_mapping'].values()};selected|={p for p in (ROOT/'eileen-promoted/maps').rglob('*')if p.is_file()}
  write(path,{'mapping':m,'action':a,'digests':{x['id']:x['contentDigest']for x in d['actions']},'effects':d['effects'],'preserved':{relative(p):file_hash(p)for p in selected}})
 b=json.loads(path.read_text());m=copy.deepcopy(b['mapping']);bent=picture(m,11);standing=picture(m,0);bent.save(SRC/'bent-before-registration.png');standing.save(SRC/'existing-standing.png')
 floor=standing.getbbox()[3];dy=floor-bent.getbbox()[3];q=Image.new('RGBA',bent.size);q.alpha_composite(bent,(0,dy));assert sum(c[3]>0 for c in q.getdata())==sum(c[3]>0 for c in bent.getdata());assert q.getbbox()[3]==floor==256
 io.OUT=OUT;io.save(q,'battle/frame-011.png','existing whole bent landing pose, translated vertically to the native ground; no limb/body rescaling')
 for i in [30,31,11]:m['frame_mapping'][str(i)]=os.path.relpath(OUT/'battle/frame-011.png',MAPPING.parent)
 m['frame_mapping']['23']=b['mapping']['frame_mapping']['0']
 m.update(revision=REV,review_note='后跳落地直接屈腿缓冲：30／31／11共用原有完整屈腿姿势，保持后一次站直，23直接使用现有站立待机姿势，不再直腿→屈腿→直腿。屈腿整体仅上移2像素对齐原地面256，身体和腿脚不缩放；身前持剑、空中与蹲姿、原312帧及第129帧唯一结算保留。',qa_report=os.path.relpath(OUT/'verification.json',MAPPING.parent))
 order=sorted(map(int,m['frame_mapping']));atlas=Image.new('RGBA',(320*len(order),288))
 for n,i in enumerate(order):atlas.alpha_composite(picture(m,i),(n*320,0))
 io.save(atlas,'battle-atlas.png','current promoted battle atlas assembled from existing complete poses')
 m.update(output_atlas=os.path.relpath(OUT/'battle-atlas.png',MAPPING.parent),output_atlas_order=order,batches=[{'id':'后跳落地屈腿后一次站直','review':os.path.relpath(OUT/'landing-poses-light.png',MAPPING.parent),'status':'review_candidate'}])
 write(OUT/'phase-contracts.json',{'revision':REV,'aliases':ALIASES,'landing_displayed_frames':[247,266],'standing_displayed_frames':[267,312],'body_registration_offset':[0,dy],'ground_bottom':floor,'whole_poses_reused':True,'limb_rescaling':False,'body_splicing':False,'new_art_generated':False,'native_timeline_rows_unchanged':True,'runtime_integrated':False});write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS,'changed_slots':CHANGED});write(OUT/'mapping-draft.json',m);write(MAPPING,m)
 print(json.dumps({'published':True,'changed_slots':CHANGED,'whole_pose_translation':[0,dy]}),flush=True)

def finish():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};a=aa[AID];p=next(p for p in d['profiles']if p['id']==a['profile']);m=json.loads(MAPPING.read_text());contract=json.loads((OUT/'phase-contracts.json').read_text())
 own=[x['id']for x in d['actions']if x['profile']=='eileen-promoted-battle'and x['contentDigest']!=b['digests'].get(x['id'])];assert own==[AID],own
 for key in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['action'].get(key),key
 for path,h in b['preserved'].items():assert file_hash(ROOT/path)==h,path
 for i,path in b['mapping']['frame_mapping'].items():
  if int(i)not in CHANGED:assert m['frame_mapping'][i]==path,i
 bent=picture(m,11);standing=picture(m,0);assert all(picture(m,i).tobytes()==bent.tobytes()for i in [30,31]);assert picture(m,23).tobytes()==standing.tobytes();assert bent.getbbox()[3]==standing.getbbox()[3]==picture(m,1).getbbox()[3]==256
 source=Image.open(SRC/'bent-before-registration.png').convert('RGBA');registered=Image.new('RGBA',source.size);registered.alpha_composite(source,tuple(contract['body_registration_offset']));assert registered.tobytes()==bent.tobytes()
 rows=a.get('revisedFrames',a['frames']);phases=[]
 for t,row in enumerate(rows[246:],246):
  phase='bent'if row['frame']in [30,31,11]else'standing';expected=bent if phase=='bent'else standing
  if phase=='bent':assert picture(m,row['frame']).tobytes()==expected.tobytes()
  else:assert row['frame']in [23,1,0,97]
  if not phases or phases[-1]['phase']!=phase:phases.append({'phase':phase,'starts_displayed_frame':t+1})
 assert phases==[{'phase':'bent','starts_displayed_frame':247},{'phase':'standing','starts_displayed_frame':267}],phases
 used={e['sprite']for action in d['actions']if action['profile']=='eileen-promoted-battle'for row in action['frames']+action.get('revisedFrames',[])+action.get('reviewTailFrames',[])for e in row.get('effects',[])};assert all(d['effects'][k]==b['effects'][k]for k in used);assert a['ready']and not d['validation']['structuralIssues']
 print(json.dumps({'status':'single_landing_bend_then_stand_passed','phases':phases}),flush=True)
 exports=[export_one(d,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False))for close in [False,True]];decoded=[]
 for e in exports:
  s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(s['nb_read_frames'])==playback_count(a)==312;assert abs(float(s['duration'])-312/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=(23,38,56)if light else(235,243,242);order=sorted(map(int,m['frame_mapping']));board=Image.new('RGB',(1280,330*math.ceil(len(order)/4)),bg);dr=ImageDraw.Draw(board)
  for n,i in enumerate(order):im=picture(m,i);x=n%4*320;y=n//4*330;board.paste(im,(x,y),im);dr.text((x+160,y+308),str(i),anchor='mm',font=font(17),fill=fg)
  board.save(OUT/f'battle-current-{"light"if light else"dark"}.png',optimize=True)
  seq=[29,30,31,11,23,1,0];board=Image.new('RGB',(320*len(seq),330),bg);dr=ImageDraw.Draw(board)
  for n,i in enumerate(seq):im=picture(m,i);board.paste(im,(n*320,0),im);dr.text((n*320+160,308),str(i),anchor='mm',font=font(18),fill=fg)
  board.save(OUT/f'landing-poses-{"light"if light else"dark"}.png',optimize=True)
 ticks=[242,245,246,251,252,257,258,265,266,291,300,301,307,311];ims=[render_frame(d,p,a,t,4,True,True)for t in ticks];cw,ch=ims[0].size;board=Image.new('RGB',(cw*2,ch*7),(14,21,26))
 for n,im in enumerate(ims):board.paste(im,(n%2*cw,n//2*ch))
 board.save(OUT/'landing-continuous.png',optimize=True)
 # One fixed crop across all panels keeps relative head/foot heights visible.
 pieces=[im.crop((624,76,1200,524))for im in ims];bb=None
 for im in pieces:
  z=ImageChops.difference(im,Image.new('RGB',im.size,(220,222,216))).getbbox();bb=z if bb is None else(min(bb[0],z[0]),min(bb[1],z[1]),max(bb[2],z[2]),max(bb[3],z[3]))
 bb=(bb[0]-14,bb[1]-14,bb[2]+14,bb[3]+14);tw=bb[2]-bb[0];th=bb[3]-bb[1]+44;detail=Image.new('RGB',(tw*4,th*4),(220,222,216));dr=ImageDraw.Draw(detail)
 for n,(im,t)in enumerate(zip(pieces,ticks)):x=n%4*tw;y=n//4*th;detail.paste(im.crop(bb),(x,y));dr.text((x+tw/2,y+th-22),f'第 {t+1} 帧',font=font(16),anchor='mm',fill=(23,38,56))
 detail.save(OUT/'landing-detail.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=AID:continue
  assert x['contentDigest']==a['contentDigest']
  for field,folder,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{folder}/{AID}{suffix}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-landing-v6-progress".*?</section>\s*','',text,flags=re.S)
 section=f'''<section id="eileen-landing-v6-progress" class="panel" style="margin-bottom:26px" aria-label="引光剑使落地屈腿顺序"><div class="heading"><h2>引光剑使 · 落地屈腿顺序</h2><p>直接屈腿缓冲 → 一次站直</p></div><p class="action-note">后跳落地第247帧直接进入完整屈腿姿势，第247至266帧保持稳定缓冲，第267帧一次站直并接回原有待机，去掉落地先直腿、随后又屈腿的反复。完整姿势复用已有画帧，脚底统一原地面高度；人物、腿脚和武器不缩放，身前持剑保持。原312帧、跳跃轨迹、节奏与第129帧唯一结算保持。</p><nav class="links" aria-label="落地屈腿顺序检查"><a href="?action={AID}#motion-player">普通攻击 · 当前动画</a><a href="{REV}/landing-detail.png">落地到站直 · 连续细节</a><a href="{REV}/landing-continuous.png">原作并列连续帧</a><a href="{REV}/landing-poses-light.png">完整姿势 · 浅底</a><a href="{REV}/landing-poses-dark.png">完整姿势 · 深底</a><a href="{REV}/README.md">修订与检查记录</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">仅调整4个普通攻击帧槽的选用与整体注册，更新正常／近景预览。本轮仍为隔离美术对照。</p></section>\n'''
 marker='<section id="eileen-front-sword-v5-progress"';assert marker in text;text=text.replace(marker,section+marker,1);text=text.replace('href="eileen-front-sword-v5-20261024/battle-current-light.png"',f'href="{REV}/battle-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{AID}"',text,count=1)
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
  with Image.open(path)as im:row={'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':SRC in path.parents}
  if row['bytes']>=200000:row['quality_reason']='完整无损离线检查图，保留人物、剑刃与文字清晰度；播放器仅复用已有小图与1张整体注册副本。'
  inventory.append(row)
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory,'new_registered_individual_images':1});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'affected_actions':1,'changed_slots':CHANGED,'aliases':ALIASES,'landing_phases':phases,'landing_complete_pose_pixels_fixed':True,'one_bend_then_stand_without_reversal':True,'common_ground_bottom':256,'bent_body_only_translated':contract['body_registration_offset'],'limbs_and_weapon_not_rescaled':True,'standing_pose_exactly_existing_idle':True,'other_battle_slots_source_images_and_maps_preserved':True,'all_native_frames_offsets_contacts_and_timing_exact':True,'promoted_effect_definitions_unchanged':len(used),'decoded_videos':decoded,'continuous_ticks':ticks,'page_links_checked':count,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending'})
 print(json.dumps({'status':'passed','actions':1,'videos':2,'page_links':count}),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--finish',action='store_true');args=p.parse_args()
 if args.prepare:prepare()
 if args.finish:finish()
