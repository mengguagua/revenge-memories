#!/usr/bin/env python3
"""Targeted promoted idle verification and isolated review-page delivery."""
import json,re,subprocess,math
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,relative,file_hash,matched_export
from export_gallery import font,render_frame,playback_count
from export_knight_complete import export_one
from import_eileen_promoted_idle_v2 import REV,OUT,SRC,MAPPING,write,C,NAVY,IVORY,INDIGO,BRASS
AID='eileen-promoted-maps-tactical-idle--idle-cycle'

def main():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={x['id']:x for x in d['actions']};pp={p['id']:p for p in d['profiles']};a=aa[AID];p=pp[a['profile']];m=json.loads(MAPPING.read_text());sc=next(s for s in m['scenarios']if s['id']=='tactical-idle');old=next(s for s in b['mapping']['scenarios']if s['id']=='tactical-idle')
 own=[x['id']for x in d['actions']if pp[x['profile']]['actor']=='eileen'and x['contentDigest']!=b['digests'].get(x['id'])];assert own==[AID],own
 for key in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['action'].get(key),key
 for key in ['directions','direction_mirror_x','timing','source_atlas','source_anchor','output_anchor','source_frame_size','output_frame_size','ground_shadow']:assert sc.get(key)==old.get(key),key
 for scenario in b['mapping']['scenarios']:
  if scenario['id']!='tactical-idle':assert scenario==next(s for s in m['scenarios']if s['id']==scenario['id'])
 for path,h in b['preserved'].items():assert file_hash(ROOT/path)==h,path
 fixed=Image.open(OUT/'layers/body.png').convert('RGBA');mask=[(x,y)for y in range(96)for x in range(96)if fixed.getpixel((x,y))[3]];poses=[]
 for row in sc['frame_mapping']:
  im=Image.open((MAPPING.parent/row['path']).resolve()).convert('RGBA');poses.append(im);assert im.size==(96,96);assert all(im.getpixel(xy)==fixed.getpixel(xy)for xy in mask)
  assert all(im.getpixel((x,y))!=(*IVORY,255)for y in range(30,37)for x in range(40,47)),'white face pixels'
  assert set(v[:3]for v in im.crop((0,73,96,80)).getdata()if v[3])<={NAVY,INDIGO},'noisy boot palette'
  assert im.getbbox()[0]>0 and im.getbbox()[1]>0 and im.getbbox()[2]<96 and im.getbbox()[3]==80
  assert {v[3]for v in im.getdata()}<={0,255};assert {v[:3]for v in im.getdata()if v[3]}<=set(C)
  assert file_hash((MAPPING.parent/row['path']).resolve())==row['sha256']
 assert len({im.tobytes()for im in poses})==3
 assert poses[0].tobytes()==poses[4].tobytes()and poses[1].tobytes()==poses[3].tobytes()==poses[5].tobytes()
 assert sum(fixed.getpixel((x,y))==(*BRASS,255)for y in range(31,34)for x in range(43,47))>=1,'amber iris lost'
 assert a['ready']and not d['validation']['structuralIssues']
 print(json.dumps({'status':'pose_checks_passed','affected_actions':1,'body_fixed':True,'face_white_pixels':0}),flush=True)
 e=export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False));probe=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0]
 assert int(probe['nb_read_frames'])==playback_count(a)==88;assert abs(float(probe['duration'])-88/a['fps'])<1/a['fps']
 for light in [False,True]:
  ticks=[0,14,22,36,44,58,66,80];ims=[render_frame(d,p,a,t,4,light,False)for t in ticks];cw,ch=ims[0].size;q=Image.new('RGB',(cw*2,ch*4),(14,21,26))
  for n,im in enumerate(ims):q.paste(im,(n%2*cw,n//2*ch))
  q.save(OUT/f'cycle-{"light"if light else"dark"}.png',optimize=True)
 # A current promoted-map board, preserving the other scene assets exactly.
 items=[]
 for context in ['story','tactical-idle','tactical-walk']:
  scenario=next(s for s in m['scenarios']if s['id']==context)
  for row in scenario['frame_mapping']:
   i=row['source_index']
   if context=='tactical-idle'and i>2:continue
   im=Image.open((MAPPING.parent/row['path']).resolve()).convert('RGBA');items.append((context+' '+str(i),im))
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);cw,ch=280,260;q=Image.new('RGB',(cw*4,ch*math.ceil(len(items)/4)),bg);dr=ImageDraw.Draw(q)
  for n,(label,im)in enumerate(items):
   im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=n%4*cw+(cw-im.width)//2;y=n//4*ch+10;q.paste(im,(x,y),im);dr.text((n%4*cw+cw//2,n//4*ch+238),label,anchor='mm',font=font(16),fill=fg)
  q.save(OUT/f'maps-current-{"light"if light else"dark"}.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=AID:continue
  assert x['contentDigest']==a['contentDigest']
  for field,folder,ext in [('video','videos','mp4'),('still','stills','png')]:
   path=ROOT/f'demos/{folder}/{AID}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-promoted-idle-v2-progress".*?</section>\s*','',text,flags=re.S)
 section=f'''<section id="eileen-promoted-idle-v2-progress" class="panel" style="margin-bottom:26px" aria-label="引光剑使待机清理"><div class="heading"><h2>引光剑使 · 待机修正</h2><p>清晰眼睛 · 稳定头部 · 统一双靴</p></div><p class="action-note">清理脸部散乱白点，使用清楚的深色眼线与柔和琥珀色眼睛。三个姿势共用同一个完整头部、身体和双腿，保持纯色红发与连续靛蓝小腿／靴面；持剑手臂和银白长剑绕固定肩部共同运动。原待机0／1／2／1循环、88帧节奏与地面阴影保持。</p><nav class="links" aria-label="引光剑使待机检查"><a href="?action={AID}#motion-player">当前待机动画</a><a href="{REV}/poses-light.png">浅色三姿势</a><a href="{REV}/poses-dark.png">深色三姿势</a><a href="{REV}/cycle-light.png">完整循环相位</a><a href="{REV}/maps-current-light.png">引光剑使地图全姿势</a><a href="{REV}/README.md">素材与制作说明</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">只更新引光剑使战斗地图待机，其他场景与女魔剑士保持。本轮仅更新隔离美术对照。</p></section>\n'''
 marker='<section id="eileen-airborne-hold-v5-progress"';assert marker in text;text=text.replace(marker,section+marker,1);text=text.replace('href="eileen-identity-complete-v1-20261023/promoted-maps-light.png"',f'href="{REV}/maps-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{AID}"',text,count=1)
 for pattern in [r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:text=re.sub(pattern,r'\g<1>'+REV,text)
 page.write_text(text);mf=ROOT/'eileen-promoted/manifest.json';v=json.loads(mf.read_text());v.update(revision=REV,review_record='../'+REV+'/README.md');write(mf,v)
 write(OUT/'verification.json',{'status':'assets_and_export_passed','page_checks':'pending'})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[]
  def handle_starttag(self,t,attrs):
   attr=dict(attrs)
   if 'id'in attr:self.ids.append(attr['id'])
   if 'href'in attr:self.links.append(attr['href'])
 page_check=Page();page_check.feed(text);assert len(page_check.ids)==len(set(page_check.ids));count=0
 for href in page_check.links:
  u=urlparse(href)
  for key in parse_qs(u.query).get('action',[]):assert key in aa,key;count+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 inventory=[]
 for path in sorted(set(OUT.rglob('*.png'))|{ROOT/e['still']}):
  with Image.open(path)as im:r={'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':SRC in path.parents}
  if r['bytes']>=200000:r['quality_reason']='保留完整无损离线源图与检查图；播放器使用独立96×96无损索引小图。'
  inventory.append(r)
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory,'runtime_frame_max_bytes':max(r['bytes']for r in inventory if '/tactical-idle/frame-'in r['path'])});write(OUT/'export-report.json',{'status':'passed','export':e,'decoded_video':probe})
 write(OUT/'verification.json',{'status':'passed','revision':REV,'affected_actions':1,'slots':6,'unique_phases':3,'whole_body_pixels_exact_in_all_frames':True,'face_white_pixel_count':0,'amber_eye_present':True,'lower_boots_palette':['172638','31445d'],'hand_and_sword_rigid_shoulder_phases':[14,4,-8],'native_cycle_frames_offsets_fps_and_shadow_exact':True,'base_eileen_and_promoted_battle_unchanged':True,'other_map_scenarios_exact':True,'decoded_video':probe,'page_links_checked':count,'text_safe_areas':'Padded gallery panel, wrapping links, centered pose captions and measured export title margins.','browser_ui_checked':False,'runtime_integrated':False,'visual_acceptance':'pending'})
 print(json.dumps({'status':'passed','affected_actions':1,'videos':1,'page_links':count}),flush=True)

if __name__=='__main__':main()
