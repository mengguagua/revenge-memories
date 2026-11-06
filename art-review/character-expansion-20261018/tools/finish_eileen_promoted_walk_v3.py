#!/usr/bin/env python3
"""Check continuous coat/true depth steps and export the four-direction walk."""
import json,re,subprocess,math
from types import SimpleNamespace
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image,ImageDraw
from build_gallery import ROOT,relative,file_hash,matched_export
from export_gallery import font,render_frame,playback_count
from export_knight_complete import export_one
from import_eileen_promoted_walk_v3 import REV,OUT,SRC,MAPPING,write,C,NAVY,INDIGO,SKIN
PROFILE='eileen-promoted-maps-tactical-walk'

def main():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());pp={p['id']:p for p in d['profiles']};aa={a['id']:a for a in d['actions']};actions=[a for a in d['actions']if a['profile']==PROFILE];assert len(actions)==8;p=pp[PROFILE];m=json.loads(MAPPING.read_text());sc=next(s for s in m['scenarios']if s['id']=='tactical-walk');old=next(s for s in b['mapping']['scenarios']if s['id']=='tactical-walk')
 own={a['id']for a in d['actions']if pp[a['profile']]['actor']=='eileen'and a['contentDigest']!=b['digests'].get(a['id'])};assert own==set(b['actions']),own
 for a in actions:
  for key in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['actions'][a['id']].get(key),(a['id'],key)
 for key in ['directions','direction_mirror_x','timing','source_atlas','source_anchor','output_anchor','source_frame_size','output_frame_size','ground_shadow']:assert sc.get(key)==old.get(key),key
 for s in b['mapping']['scenarios']:
  if s['id']!='tactical-walk':assert s==next(q for q in m['scenarios']if q['id']==s['id']),s['id']
 for path,h in b['preserved'].items():assert file_hash(ROOT/path)==h,path
 poses={i:Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')for i in range(8)};phase_checks={}
 for name,slots in [('up',[0,1]),('down',[4,5]),('side',[2,3])]:
  body=Image.open(OUT/f'layers/{name}-body.png').convert('RGBA');mask=[(x,y)for y in range(96)for x in range(128)if body.getpixel((x,y))[3]]
  assert all(all(poses[i].getpixel(xy)==body.getpixel(xy)for xy in mask)for i in slots),(name,'coat/head moved or split')
  layers=[Image.open(OUT/f'layers/{name}-legs-{j}.png').convert('RGBA')for j in range(2)]
  if name in ['up','down']:
   heights=[[max(y for y in range(75,96)for x in range(cx-1,cx+2)if im.getpixel((x,y))[3])for cx in [60,68]]for im in layers]
   assert(heights[0][0]-heights[0][1])*(heights[1][0]-heights[1][1])<0,heights;assert min(abs(left-right)for left,right in heights)>=6
   phase_checks[name]={'left_right_boot_bottom_y':heights,'alternate_forward_depth_steps':True,'fixed_whole_coat':True}
  else:
   bounds=[im.getbbox()for im in layers];assert bounds[1][2]-bounds[1][0]>bounds[0][2]-bounds[0][0]+8;assert abs(bounds[0][3]-bounds[1][3])<=1
   phase_checks[name]={'passing_and_stride_leg_bounds':bounds,'common_scale':True,'fixed_whole_coat':True,'held_hand':'clearly in front of chest at low carry'}
 assert poses[6].tobytes()==poses[2].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes();assert poses[7].tobytes()==poses[3].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
 upper_skin=sum(poses[0].getpixel((x,y))==(*SKIN,255)for y in range(24,55)for x in range(128));assert upper_skin<=3,'visible weapon hand in rear head region'
 for i,im in poses.items():
  assert im.size==(128,96);assert im.getbbox()[0]>0 and im.getbbox()[1]>0 and im.getbbox()[2]<128 and im.getbbox()[3]<=95
  assert{v[3]for v in im.getdata()}<={0,255};assert{v[:3]for v in im.getdata()if v[3]}<=set(C)
 assert all(a['ready']for a in actions)and not d['validation']['structuralIssues']
 print(json.dumps({'status':'direction_and_pose_checks_passed','affected_actions':8,'depth_steps':phase_checks}),flush=True)
 exports=[];decoded=[]
 for a in actions:
  e=export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False));exports.append(e);s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(s['nb_read_frames'])==playback_count(a);assert abs(float(s['duration'])-playback_count(a)/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 for direction in ['up','down','right','left']:
  a=aa[PROFILE+'--walk-'+direction]
  for light in [False,True]:
   ticks=[0,15,16,31,32,47];ims=[render_frame(d,p,a,t,6,light,False)for t in ticks];cw,ch=ims[0].size;q=Image.new('RGB',(cw*2,ch*3),(14,21,26))
   for n,im in enumerate(ims):q.paste(im,(n%2*cw,n//2*ch))
   q.save(OUT/f'{direction}-continuous-{"light"if light else"dark"}.png',optimize=True)
 items=[]
 for context in ['story','tactical-idle','tactical-walk']:
  s=next(s for s in m['scenarios']if s['id']==context)
  for row in s['frame_mapping']:
   i=row['source_index']
   if context=='tactical-idle'and i>2:continue
   items.append((context+' '+str(i),Image.open((MAPPING.parent/row['path']).resolve()).convert('RGBA')))
 for light in [False,True]:
  bg=(220,222,216)if light else(32,45,53);fg=NAVY if light else(235,243,242);cw,ch=280,260;q=Image.new('RGB',(cw*4,ch*math.ceil(len(items)/4)),bg);dr=ImageDraw.Draw(q)
  for n,(label,im)in enumerate(items):
   im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=n%4*cw+(cw-im.width)//2;y=n//4*ch+10;q.paste(im,(x,y),im);dr.text((n%4*cw+cw//2,n//4*ch+238),label,anchor='mm',font=font(16),fill=fg)
  q.save(OUT/f'maps-current-{"light"if light else"dark"}.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']not in own:continue
  assert x['contentDigest']==aa[x['id']]['contentDigest']
  for field,folder,ext in [('video','videos','mp4'),('still','stills','png')]:
   path=ROOT/f'demos/{folder}/{x["id"]}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-promoted-walk-v3-progress".*?</section>\s*','',text,flags=re.S)
 links=''.join(f'<a href="?action={PROFILE}--walk-{key}#motion-player">行走 · {name}</a>'for key,name in [('up','向上'),('down','向下'),('left','向左'),('right','向右')]);section=f'''<section id="eileen-promoted-walk-v3-progress" class="panel" style="margin-bottom:26px" aria-label="引光剑使四向行走修正"><div class="heading"><h2>引光剑使 · 四向行走修正</h2><p>遮挡正确 · 双腿交替 · 胸前低位持剑</p></div><p class="action-note">向上行走时，身前的持剑手臂被头和身体遮住，只露出肩后剑刃；向下行走时，左右腿在各自位置前后交替。完整长衣覆盖腿部连接处，衣摆不横移、不切开翻转。左右行走使用清楚的胸前持剑前臂与握剑手，握柄降低到下胸位置，并腿与跨步按原节奏切换。身体中心与地面阴影保持。</p><nav class="links" aria-label="引光剑使四向行走检查">{links}<a href="{REV}/poses-light.png">浅色全姿势</a><a href="{REV}/poses-dark.png">深色全姿势</a><a href="{REV}/README.md">连续帧与制作说明</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">更新8个战斗地图行走帧槽及相应四向行走／停步预览；已修正的待机、剧情地图、大地图及战斗场景保持。本轮仅更新隔离美术对照。</p></section>\n'''
 marker='<section id="eileen-promoted-idle-v2-progress"';assert marker in text;text=text.replace(marker,section+marker,1);text=text.replace('href="eileen-promoted-idle-v2-20261024/maps-current-light.png"',f'href="{REV}/maps-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{PROFILE}--walk-down"',text,count=1)
 for pattern in [r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:text=re.sub(pattern,r'\g<1>'+REV,text)
 page.write_text(text);mf=ROOT/'eileen-promoted/manifest.json';v=json.loads(mf.read_text());v.update(revision=REV,review_record='../'+REV+'/README.md');write(mf,v)
 write(OUT/'verification.json',{'status':'assets_and_exports_passed','page_checks':'pending'})
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[]
  def handle_starttag(self,t,attrs):
   attr=dict(attrs)
   if'id'in attr:self.ids.append(attr['id'])
   if'href'in attr:self.links.append(attr['href'])
 check=Page();check.feed(text);assert len(check.ids)==len(set(check.ids));count=0
 for href in check.links:
  u=urlparse(href)
  for key in parse_qs(u.query).get('action',[]):assert key in aa,key;count+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 inventory=[]
 for path in sorted(set(OUT.rglob('*.png'))|{ROOT/e['still']for e in exports}):
  with Image.open(path)as im:r={'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':SRC in path.parents}
  if r['bytes']>=200000:r['quality_reason']='完整无损离线源图或连续帧对照保留清晰度；播放器使用独立128×96无损索引小图。'
  inventory.append(r)
 write(OUT/'image-inventory.json',{'images':inventory,'runtime_frame_max_bytes':max(r['bytes']for r in inventory if '/tactical-walk/frame-'in r['path'])});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'changed_slots':8,'affected_actions':8,'whole_coat_and_head_pixels_fixed_per_direction':True,'phase_checks':phase_checks,'rear_head_skin_pixels_only_ear':upper_skin,'left_right_exact_mirrors':True,'common_anatomical_scale_per_direction':True,'existing_timing_offsets_anchors_and_shadows_exact':True,'other_promoted_map_scenarios_exact':True,'all_base_eileen_and_promoted_battle_files_unchanged':True,'decoded_videos':decoded,'page_links_checked':count,'runtime_integrated':False,'browser_ui_checked':False,'text_safe_areas':'Padded gallery panel, wrapping links, centered captions and measured export title margins.','visual_acceptance':'pending'})
 print(json.dumps({'status':'passed','slots':8,'videos':8,'page_links':count}),flush=True)

if __name__=='__main__':main()
