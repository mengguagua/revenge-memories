#!/usr/bin/env python3
"""Narrow normal-attack checks and full continuous-phase review for promoted Eileen."""
import json,re,math,subprocess
from types import SimpleNamespace
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count
from export_knight_complete import export_one
from import_eileen_promoted_battle_v4 import REV,OUT,SRC,MAPPING,write,C
AID='eileen-promoted-battle--original_class_11_normal';ICE=(167,215,229,255)

def main():
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};a=aa[AID];p=pp[a['profile']];m=json.loads(MAPPING.read_text());art=json.loads((OUT/'asset-manifest.json').read_text())
 own=[x['id']for x in d['actions']if pp[x['profile']]['actor']=='eileen'and x['contentDigest']!=b['digests'].get(x['id'])];assert own==[AID],own
 for key in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['actions'][AID].get(key),key
 for path,h in b['preserved'].items():assert file_hash(ROOT/path)==h,path
 changed=set(art['changed_slots'])
 for i,path in b['mapping']['frame_mapping'].items():
  if int(i)not in changed:assert m['frame_mapping'][i]==path,i
 for reg in art['registrations']:
  height=reg['source_bounds'][3]-reg['source_bounds'][1]if 'source_bounds'in reg else Image.open(SRC/reg['source']).height
  assert abs(reg['anatomical_head_height']*reg['dimensions'][1]/height-30)<.2,reg['label'];assert reg['body_splices']==0 and reg['clipped_pixels']==0
 def pose(i):return Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')
 for alias,canonical in art['aliases'].items():assert pose(int(alias)).tobytes()==pose(canonical).tobytes(),alias
 body=Image.open(OUT/'layers/crouch-body.png').convert('RGBA');mask=[(x,y)for y in range(288)for x in range(320)if body.getpixel((x,y))[3]]
 for i in [16,17,18,19,22]:assert all(pose(i).getpixel(xy)==body.getpixel(xy)for xy in mask),i
 assert body.getbbox()[3]==257;assert pose(17).tobytes()!=pose(18).tobytes(),'braid phases lost'
 before=Image.open(OUT/'layers/retreat-body-without-sword.png').convert('RGBA');overlay=Image.open(OUT/'layers/retreat-sword-hand.png').convert('RGBA');after=pose(11)
 assert all(before.getpixel((x,y))==after.getpixel((x,y))for y in range(288)for x in range(320)if not overlay.getpixel((x,y))[3])
 blade=[(x,y)for y in range(288)for x in range(320)if overlay.getpixel((x,y))==ICE];grip=art['weapon_registration']['target_grip'];assert sum(x for x,y in blade)/len(blade)>grip[0]and sum(y for x,y in blade)/len(blade)>grip[1]
 weapon=[]
 for i in sorted({row['frame']for row in a['frames']}):
  im=pose(i);count=sum(v==ICE for v in im.getdata())
  if i in changed:assert count>=25,(i,'missing blade',count)
  else:assert im.tobytes()==Image.open(SRC/f'before-{i:03}.png').convert('RGBA').tobytes(),(i,'accepted sword pose changed')
  weapon.append({'slot':i,'ice_edge_pixels':count,'check':'new_silver_blade_pixels'if i in changed else'accepted_sword_pose_pixels_unchanged'})
 for asset in art['assets']:
  path=ROOT/asset['path'];assert file_hash(path)==asset['sha256'];im=Image.open(path);assert list(im.size)==asset['size']
  if '/battle/frame-'in asset['path']:
   q=im.convert('RGBA');assert{v[3]for v in q.getdata()}<={0,255};assert{v[:3]for v in q.getdata()if v[3]}<=set(C)
 used={e['sprite']for action in d['actions']if pp[action['profile']]['actor']=='eileen'for row in action['frames']+action.get('revisedFrames',[])+action.get('reviewTailFrames',[])for e in row.get('effects',[])};assert all(d['effects'][key]==b['effects'][key]for key in used);assert a['ready']and not d['validation']['structuralIssues']
 print(json.dumps({'status':'anatomy_crouch_weapon_checks_passed','affected_actions':1}),flush=True)
 exports=[export_one(d,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False))for close in [False,True]];decoded=[]
 for e in exports:
  stream=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(stream['nb_read_frames'])==playback_count(a)==312;assert abs(float(stream['duration'])-312/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**stream})
 sections={'airborne':[64,68,80,88,92,104,110,113,116,120,123,125],'crouch':[125,126,138,139,143,144,149,150,181,182],'retreat':[182,194,206,218,230,242,252,258,262,266,300,307]}
 for section,ticks in sections.items():
  for light in [False,True]:
   ims=[render_frame(d,p,a,t,6,light,True)for t in ticks];cw,ch=ims[0].size;q=Image.new('RGB',(cw*2,ch*math.ceil(len(ims)/2)),(14,21,26))
   for n,im in enumerate(ims):q.paste(im,(n%2*cw,n//2*ch))
   q.save(OUT/f'{section}-continuous-{"light"if light else"dark"}.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=AID:continue
  assert x['contentDigest']==a['contentDigest']
  for field,folder,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{folder}/{AID}{suffix}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-promoted-battle-v4-progress".*?</section>\s*','',text,flags=re.S)
 section=f'''<section id="eileen-promoted-battle-v4-progress" class="panel" style="margin-bottom:26px" aria-label="引光剑使战斗动作稳定"><div class="heading"><h2>引光剑使 · 战斗动作稳定</h2><p>统一体型 · 稳定蹲姿 · 回位持剑连续</p></div><p class="action-note">以真实面部和独立头颅尺寸校准空中姿势，排除举剑手、上扬头发造成的缩放误判；每个空中阶段保持完整姿势。落地蹲姿共用一套完整长衣、双腿和撑地手，只让后方松辫变化。后退第11姿势补齐后侧握剑手和银白长剑，避免回位突然缺剑。保留原动作顺序、跳跃轨迹、312帧总长、已有法术特效和第129帧唯一结算。</p><nav class="links" aria-label="引光剑使战斗稳定检查"><a href="?action={AID}#motion-player">普通攻击 · 当前动画</a><a href="{REV}/airborne-continuous-light.png">空中连续相位</a><a href="{REV}/crouch-continuous-light.png">落地与蹲姿</a><a href="{REV}/retreat-continuous-light.png">后跳与回位持剑</a><a href="{REV}/battle-current-light.png">当前战斗全姿势</a><a href="{REV}/README.md">素材与修订说明</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">更新31个普通攻击帧槽，只影响1项动作及正常／近景预览。已确认的待机、行走、其他法术和女魔剑士保持。本轮仅更新隔离美术对照。</p></section>\n'''
 marker='<section id="eileen-promoted-walk-v3-progress"';assert marker in text;text=text.replace(marker,section+marker,1);text=text.replace('href="eileen-identity-complete-v1-20261023/promoted-battle-light.png"',f'href="{REV}/battle-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{AID}"',text,count=1)
 for pattern in [r'(gallery-data\.js\?v=)[^" ]+',r'(tools/gallery\.js\?v=)[^" ]+']:text=re.sub(pattern,r'\g<1>'+REV,text)
 page.write_text(text);mf=ROOT/'eileen-promoted/manifest.json';v=json.loads(mf.read_text());v.update(revision=REV,review_record='../'+REV+'/README.md');write(mf,v)
 write(OUT/'verification.json',{'status':'assets_and_exports_passed','page_checks':'pending'})
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
  if row['bytes']>=200000:row['quality_reason']='保留无损离线源图及完整连续相位，播放器使用独立320×288索引小图，避免损伤轮廓和衣服细节。'
  inventory.append(row)
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory,'runtime_frame_max_bytes':max(row['bytes']for row in inventory if '/battle/frame-'in row['path'])});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'affected_actions':1,'changed_slots':31,'all_new_anatomical_head_heights':30,'registered_whole_bodies':len(art['registrations']),'body_splices':0,'airborne_phase_poses_exact':True,'complete_crouch_body_pixels_exact_in_all_five_slots':True,'braid_motion_preserved':True,'retreat_body_unchanged_outside_added_weapon':True,'rear_hand_down_right_sword_registered':True,'all_normal_attack_source_slots_have_sword':weapon,'original_frames_offsets_contacts_effects_and_timing_exact':True,'all_base_eileen_and_promoted_map_files_unchanged':True,'other_battle_frame_paths_unchanged':True,'eileen_used_effect_definitions_unchanged':len(used),'decoded_videos':decoded,'page_links_checked':count,'runtime_integrated':False,'browser_ui_checked':False,'text_safe_areas':'Existing padded gallery panel, wrapping links and centered measured export captions.','visual_acceptance':'pending'})
 print(json.dumps({'status':'passed','actions':1,'videos':2,'page_links':count}),flush=True)

if __name__=='__main__':main()
