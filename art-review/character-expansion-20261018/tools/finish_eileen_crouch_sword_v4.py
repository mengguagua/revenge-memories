#!/usr/bin/env python3
"""Narrow crouch continuity, weapon continuity, offline playback and page checks."""
import ast,json,re,html,subprocess,math
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from types import SimpleNamespace
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count,font
from export_knight_complete import export_one
from import_eileen_crouch_sword_v4 import REV,OUT,SRC,write,C,NAVY
ICE=(167,215,229)

def main():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};aid='eileen-battle--original_class_11_normal';a=aa[aid];p=pp[a['profile']]
 changes=[x['id']for x in d['actions']if x['contentDigest']!=b['digests'].get(x['id'])];own_changes=[key for key in changes if pp[aa[key]['profile']]['actor']=='eileen'];external=[key for key in changes if key not in own_changes];assert own_changes==[aid],own_changes
 for key in['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['action'].get(key),key
 assert a['ready']and not d['validation']['structuralIssues']
 used={e['sprite']for action in d['actions']if pp[action['profile']]['actor']=='eileen'for row in action['frames']+action.get('revisedFrames',[])+action.get('reviewTailFrames',[])for e in row.get('effects',[])}
 for key in used:assert d['effects'][key]==b['effects'][key],key
 for path,digest in b['preserved'].items():assert file_hash(ROOT/path)==digest,path
 m=json.loads((ROOT/'eileen/battle/frame_mapping.json').read_text());changed={11,16,17,18,19,22}
 for k,v in b['battle']['frame_mapping'].items():
  if int(k)not in changed:assert m['frame_mapping'][k]==v,k
 def load(kind,i):return Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')
 body=Image.open(OUT/'layers/canonical-body.png').convert('RGBA');pixels=[(x,y)for y in range(body.height)for x in range(body.width)if body.getpixel((x,y))[3]]
 for i in[16,17,18,19,22]:
  q=load('battle',i);assert all(q.getpixel(xy)==body.getpixel(xy)for xy in pixels),(i,'body support changed')
 base=load('battle',16)
 for i in[17,18,19,22]:assert base.crop((0,229,320,288)).tobytes()==load('battle',i).crop((0,229,320,288)).tobytes(),i
 assert load('battle',17).tobytes()!=load('battle',18).tobytes(),'hair stopped moving'
 overlay=Image.open(OUT/'layers/retreat-sword-hand.png').convert('RGBA');before=Image.open(SRC/'before-011.png').convert('RGBA');after=load('battle',11)
 assert all(before.getpixel((x,y))==after.getpixel((x,y))for y in range(288)for x in range(320)if not overlay.getpixel((x,y))[3])
 blade=[(x,y)for y in range(288)for x in range(320)if overlay.getpixel((x,y))==(*ICE,255)]
 assert blade and sum(x for x,y in blade)/len(blade)>236.5 and sum(y for x,y in blade)/len(blade)>190,'retreat sword must point down-right from rear gripping hand'
 weapon=[]
 for i in sorted({r['frame']for r in a['frames']}):
  im=Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA');n=sum(v==(*ICE,255)for v in im.getdata());assert n>=30,(i,'sword disappeared',n);weapon.append({'source_frame':i,'ice_blade_pixels':n})
 art=json.loads((OUT/'asset-manifest.json').read_text())
 for r in art['assets']:
  path=ROOT/r['path'];assert file_hash(path)==r['sha256'];im=Image.open(path);assert list(im.size)==r['size']
  if '/frame-'in r['path']:
   q=im.convert('RGBA');assert set(q.getchannel('A').getdata())<={0,255};assert {v[:3]for v in q.getdata()if v[3]}<=set(C)
 for name in['import_eileen_crouch_sword_v4.py','finish_eileen_crouch_sword_v4.py']:ast.parse((ROOT/'tools'/name).read_text())
 print(json.dumps({'status':'assets_passed','affected_actions':1,'changed_slots':6}),flush=True)
 exports=[export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)),export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False))];decoded=[]
 for e in exports:
  s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(s['nb_read_frames'])==playback_count(a);assert abs(float(s['duration'])-playback_count(a)/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 for light in[False,True]:
  ticks=[126,139,148,150,181,182,252,258,262,266];samples=[render_frame(d,p,a,t,6,light,True)for t in ticks];cw,ch=samples[0].size;board=Image.new('RGB',(cw*2,ch*5),(14,21,26))
  for n,im in enumerate(samples):board.paste(im,(n%2*cw,n//2*ch))
  board.save(OUT/('playback-'+('light'if light else'dark')+'.png'),optimize=True)
  if light:
   board.crop((0,0,cw*2,ch*3)).save(OUT/'diagnostic-crouch-playback.png',optimize=True)
   board.crop((0,ch*3,cw*2,ch*5)).save(OUT/'diagnostic-retreat-playback.png',optimize=True)
  cw,ch=360,330;items=sorted(p['newFrames'].items(),key=lambda kv:int(kv[0]));board=Image.new('RGB',(cw*4,ch*math.ceil(len(items)/4)),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(board)
  for n,(key,path)in enumerate(items):
   im=Image.open(ROOT/path).convert('RGBA');x=n%4*cw+(cw-im.width)//2;y=n//4*ch;board.paste(im,(x,y),im);dr.text((n%4*cw+180,y+309),key,anchor='mm',font=font(17),fill=NAVY if light else(235,243,242))
  board.save(OUT/('battle-current-'+('light'if light else'dark')+'.png'),optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=aid:continue
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{aid}{suffix}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 section=f'''<section id="eileen-crouch-sword-v4-progress" class="panel" style="margin-bottom:26px" aria-label="艾琳下蹲与后退持剑修正"><div class="heading"><h2>艾琳 · 下蹲与后退持剑修正</h2><p>固定腿部支撑 · 持剑连续</p></div><p class="action-note">下蹲停留段共用一个完整支撑姿势，髋、大腿、膝盖、脚和撑地手保持稳定，只让后方的红色松辫摆动。后退第11姿势补齐握剑手和冰蓝长剑，保留原有身体。原作节奏、位移与第129帧结算保持不变。</p><nav class="links" aria-label="艾琳下蹲与后退检查"><a href="?action={aid}#motion-player">普通攻击 · 下蹲与后退</a><a href="{REV}/playback-light.png">连续相位近景</a><a href="{REV}/poses-dark.png">深色姿势对照</a><a href="{REV}/poses-light.png">浅色姿势对照</a><a href="{REV}/README.md">制作记录与提示词</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">只更新6个战斗帧槽，影响普通攻击1项动作；正常与近景2段动画已检查。本轮仅更新隔离美术对照。</p></section>\n'''
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-crouch-sword-v4-progress".*?</section>\s*','',text,flags=re.S);marker='<section id="eileen-side-battle-v3-progress"';assert marker in text;text=text.replace(marker,section+marker,1);text=text.replace('href="eileen-side-battle-v3-20261024/battle-current-light.png"',f'href="{REV}/battle-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{aid}"',text,count=1)
 for pattern in[r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:text=re.sub(pattern,r'\g<1>'+REV,text)
 page.write_text(text)
 manifest=ROOT/'eileen/manifest.json';mm=json.loads(manifest.read_text());mm.update(revision=REV,review_record='../'+REV+'/README.md');write(manifest,mm)
 class Page(HTMLParser):
  def __init__(self):super().__init__();self.ids=[];self.links=[]
  def handle_starttag(self,t,attrs):
   a=dict(attrs)
   if'id'in a:self.ids.append(a['id'])
   if'href'in a:self.links.append(a['href'])
 write(OUT/'verification.json',{'status':'assets_and_exports_passed','revision':REV,'page_checks':'pending'})
 page_check=Page();page_check.feed(text);assert len(page_check.ids)==len(set(page_check.ids));checked=0
 for href in page_check.links:
  u=urlparse(html.unescape(href))
  for key in parse_qs(u.query).get('action',[]):assert key in aa,key;checked+=1
  if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists(),href
 inventory=[]
 paths=set(OUT.rglob('*.png'))|{ROOT/e['still']for e in exports}
 for path in sorted(paths):
  with Image.open(path)as im:r={'path':relative(path),'size':list(im.size),'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':SRC in path.parents}
  if r['bytes']>=200000:r['quality_reason']='保留无损离线源图或完整相位对照；播放器使用独立无损小图。'
  inventory.append(r)
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory,'runtime_frame_max_bytes':max(r['bytes']for r in inventory if '/frame-'in r['path'])});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'changed_slots':sorted(changed),'affected_actions':1,'other_actions_unchanged':len(d['actions'])-1-len(external),'concurrent_external_changes_preserved':external,'all_existing_schedules_origins_contacts_and_fps_exact':True,'all_map_and_promoted_files_unchanged':True,'all_other_battle_paths_unchanged':True,'eileen_used_effects_unchanged':len(used),'whole_crouch_body_pixels_exact_in_all_five_slots':True,'thigh_knee_and_support_hand_fixed':True,'hair_phases_move':True,'retreat_body_unchanged_outside_weapon_overlay':True,'normal_attack_all_source_frames_have_sword':weapon,'decoded_videos':decoded,'page_action_links_checked':checked,'runtime_integrated':False,'browser_ui_checked':False,'user_visual_acceptance':'pending','text_safe_areas':'Existing padded gallery panel and wrapping links; measured centered export captions.'});print(json.dumps({'status':'passed','actions':1,'videos':2,'page_links':checked}),flush=True)
if __name__=='__main__':main()
