#!/usr/bin/env python3
"""Targeted recovery continuity validation and two preview exports."""
from baseline_json import read_baseline
import json,math,re,subprocess
from types import SimpleNamespace
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count
from export_knight_complete import export_one
from import_knight_redraw_v3 import parts
from import_eileen_front_sword_v5 import REV,OUT,SRC,MAPPING,POINTS,write,C
AID='eileen-promoted-battle--original_class_11_normal';ICE=(167,215,229,255)

def main():
 b=read_baseline(OUT/'baseline.json');d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};a=aa[AID];p=pp[a['profile']];m=json.loads(MAPPING.read_text());art=json.loads((OUT/'asset-manifest.json').read_text())
 own=[x['id']for x in d['actions']if x['profile']=='eileen-promoted-battle'and x['contentDigest']!=b['digests'].get(x['id'])];assert own==[AID],own
 concurrent=[x['id']for x in d['actions']if pp[x['profile']]['actor']=='eileen'and x['profile']!='eileen-promoted-battle'and x['contentDigest']!=b['digests'].get(x['id'])]
 # Another task is updating the base heroine's thunder effect. Preserve
 # its live mapping and gallery records instead of restoring our snapshot.
 for key in concurrent:assert aa[key]['frames']==b['actions'][key]['frames'],key
 for key in ['frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport']:assert a.get(key)==b['actions'][AID].get(key),key
 external_files={}
 for path,h in b['preserved'].items():
  if path=='eileen/battle/frame_mapping.json'and concurrent:external_files[path]=file_hash(ROOT/path)
  else:assert file_hash(ROOT/path)==h,path
 for i,path in b['mapping']['frame_mapping'].items():
  if int(i)not in POINTS:assert m['frame_mapping'][i]==path,i
 def pose(i):return Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')
 canonical=Image.open(OUT/'layers/front-hand-sword.png').convert('RGBA');metrics=[]
 for reg in art['registrations']:
  i=reg['slot'];im=pose(i);layer=Image.open(OUT/f'layers/front-hand-sword-{i:03}.png').convert('RGBA');assert im.getbbox()[3]==reg['preserved_floor'];assert abs(reg['source_head_height']*reg['dimensions'][1]/reg['source_size'][1]-30)<.2
  assert max(abs(reg['registered_face'][j]-([188,144]if i in [30,31]else[192,144])[j])for j in range(2))<2
  shifted=Image.new('RGBA',im.size);shifted.alpha_composite(canonical,tuple(reg['weapon_layer_shift']));assert shifted.tobytes()==layer.tobytes()
  assert all(im.getpixel((x,y))==layer.getpixel((x,y))for y in range(im.height)for x in range(im.width)if layer.getpixel((x,y))[3])
  blade=[(x,y)for y in range(layer.height)for x in range(layer.width)if layer.getpixel((x,y))==ICE];assert len(blade)>100;cx=sum(x for x,y in blade)/len(blade);cy=sum(y for x,y in blade)/len(blade);assert cx<reg['front_grip'][0]-12 and cy>reg['front_grip'][1]+10
  groups=parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(groups)==1,(i,'detached weapon or debris')
  # No long ice blade may survive behind the shoulder/coat.
  rear=[g for g in parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))==ICE and x>reg['registered_face'][0]+20)if len(g)>12 and max(x for x,y in g)-min(x for x,y in g)>12];assert not rear,(i,'rear blade remains')
  assert {v[3]for v in im.getdata()}<={0,255};assert {v[:3]for v in im.getdata()if v[3]}<=set(C)
  metrics.append({'slot':i,'grip':reg['front_grip'],'blade_centroid':[cx,cy],'identical_weapon_pixels':len(blade),'physical_head_height':reg['source_head_height']*reg['dimensions'][1]/reg['source_size'][1],'floor':reg['preserved_floor']})
 for asset in art['assets']:assert file_hash(ROOT/asset['path'])==asset['sha256']
 used={e['sprite']for action in d['actions']if action['profile']=='eileen-promoted-battle'for row in action['frames']+action.get('revisedFrames',[])+action.get('reviewTailFrames',[])for e in row.get('effects',[])};assert all(d['effects'][key]==b['effects'][key]for key in used);assert a['ready']and not d['validation']['structuralIssues']
 print(json.dumps({'status':'front_carry_checks_passed','changed_slots':list(POINTS)}),flush=True)
 exports=[export_one(d,a,SimpleNamespace(close=close,scale=4,light=False,stills_only=False))for close in [False,True]];decoded=[]
 for e in exports:
  s=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(s['nb_read_frames'])==playback_count(a)==312;assert abs(float(s['duration'])-312/a['fps'])<1/a['fps'];decoded.append({'path':e['video'],**s})
 ticks=[230,245,246,251,252,257,258,265,266,300,301,306,307,309]
 for light in [False,True]:
  ims=[render_frame(d,p,a,t,6,light,True)for t in ticks];cw,ch=ims[0].size;q=Image.new('RGB',(cw*2,ch*math.ceil(len(ims)/2)),(14,21,26))
  for n,im in enumerate(ims):q.paste(im,(n%2*cw,n//2*ch))
  q.save(OUT/f'recovery-continuous-{"light"if light else"dark"}.png',optimize=True)
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for x in latest['actions']:
  if x['id']!=AID:continue
  assert x['contentDigest']==a['contentDigest']
  for field,folder,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{folder}/{AID}{suffix}.{ext}';x[field]=relative(path)if matched_export(path,x['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 page=ROOT/'index.html';text=page.read_text();text=re.sub(r'<section id="eileen-front-sword-v5-progress".*?</section>\s*','',text,flags=re.S)
 panel=f'''<section id="eileen-front-sword-v5-progress" class="panel" style="margin-bottom:26px" aria-label="引光剑使落地持剑连续"><div class="heading"><h2>引光剑使 · 落地持剑连续</h2><p>落地、回位到待机 · 一直身前持剑</p></div><p class="action-note">修正后跳落地30／31及回位11／23：持剑手一直在身前低位，剑尖连续指向左下，不再突然甩到身后。复用前一姿势的同一套握剑手、剑格与完整剑刃，统一长度、角度和轮廓，再接回身前持剑的待机。保持已校准的体型、各姿势落脚高度、空中相位、完整蹲姿及原312帧时序。</p><nav class="links" aria-label="落地持剑检查"><a href="?action={AID}#motion-player">普通攻击 · 当前动画</a><a href="{REV}/recovery-continuous-light.png">后跳至待机 · 连续帧</a><a href="{REV}/front-carry-sequence-light.png">持剑方向 · 浅底</a><a href="{REV}/front-carry-sequence-dark.png">持剑方向 · 深底</a><a href="{REV}/battle-current-light.png">当前战斗全姿势</a><a href="{REV}/README.md">制作与检查记录</a><a href="{REV}/verification.json">针对性检查</a></nav><p class="action-note">仅修改4个普通攻击帧槽，更新正常／近景预览；其余动作与地图素材保留。本轮仍为隔离美术对照。</p></section>\n'''
 marker='<section id="eileen-promoted-battle-v4-progress"';assert marker in text;text=text.replace(marker,panel+marker,1);text=text.replace('后退第11姿势补齐后侧握剑手和银白长剑，避免回位突然缺剑。','第11姿势曾补齐持剑；后跳落地和回位方向已由本轮统一为身前低位。');text=text.replace('href="eileen-promoted-battle-v4-20261024/battle-current-light.png"',f'href="{REV}/battle-current-light.png"');text=re.sub(r'<body data-default-action="[^"]+"',f'<body data-default-action="{AID}"',text,count=1)
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
  if row['bytes']>=200000:row['quality_reason']='无损离线生成源图或完整连续帧检查图；运行使用独立320×288索引图片，保留透明轮廓与剑刃清晰度。'
  inventory.append(row)
 for path,h in external_files.items():assert file_hash(ROOT/path)==h,path
 write(OUT/'concurrent-work-preserved.json',{'untouched_external_actions':concurrent,'untouched_external_mapping_hashes':external_files,'reason':'Base Eileen thunder effects changed in parallel; only the four promoted recovery slots and their own preview exports are published here.'})
 write(OUT/'image-inventory.json',{'revision':REV,'images':inventory,'runtime_frame_max_bytes':max(row['bytes']for row in inventory if '/battle/frame-'in row['path'])});write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_videos':decoded});write(OUT/'verification.json',{'status':'passed','revision':REV,'affected_actions':1,'changed_slots':list(POINTS),'front_carry_metrics':metrics,'same_front_weapon_layer_for_all_four_poses':True,'no_rear_blade':True,'single_connected_character_and_weapon':True,'native_floor_and_head_scale_preserved':True,'all_native_frames_offsets_contacts_effects_and_timing_exact':True,'other_promoted_battle_slots_base_bitmaps_and_all_maps_unchanged':True,'promoted_used_effect_definitions_unchanged':len(used),'decoded_videos':decoded,'continuous_ticks':ticks,'page_links_checked':count,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending'})
 print(json.dumps({'status':'passed','actions':1,'videos':2,'page_links':count}),flush=True)

if __name__=='__main__':main()
