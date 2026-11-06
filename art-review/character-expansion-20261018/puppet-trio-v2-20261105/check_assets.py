# coding: utf-8
from pathlib import Path
from PIL import Image,ImageEnhance,ImageOps,ImageDraw
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,subprocess,ast,re
R=Path(__file__).resolve().parent;ROOT=R.parents[2];BASE=R.parent
M=json.loads((R/'asset-manifest.json').read_text());D=json.loads((R/'design.json').read_text());s=(R/'gallery-extension.js').read_text();G=json.loads(s.split('const extra = ',1)[1].split(';\nwindow.PUPPET_TRIO_DATA',1)[0]);checks=[]
def check(ok,label):
 checks.append({'label':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
for image in M['images']:
 p=R/image['path'];im=Image.open(p);check(im.size==tuple(image['pixels']) and p.stat().st_size==image['bytes'],'Image dimensions/bytes '+image['path'])
 check(p.stat().st_size<(200000 if p.name=='healing-ground-f25.png' else 50000),'Optimized image size '+image['path'])
for group,frames in M['frames'].items():
 unit=group.split('-')[0];battle=group.endswith('battle')
 check(len(frames)==({'cyclops':8,'owl':10,'prometheus':6}[unit] if battle else 20 if unit=='cyclops' else 16),'Complete pose set '+group)
 for f in frames:
  im=Image.open(R/f['path']).convert('RGBA');b=im.getbbox();check(b is not None and b[0]>=2 and b[1]>=2 and b[2]<=im.width-2 and b[3]<=im.height-2,'Intact transparent contour '+f['path'])
  check(set(im.getchannel('A').getdata())<={0,255},'Hard native alpha '+f['path'])
for p in G['profiles']:
 for path in p['newFrames'].values():check((BASE/path).is_file(),'Pose/transition resolves '+path)
 source=Image.open(BASE/p['sourceAtlas']);check(source.size==tuple(p['sourceAtlasSize']),'Reference atlas dimensions '+p['id'])
for a in G['actions']:
 p=next(p for p in G['profiles'] if p['id']==a['profile']);check(a['contactTick'] is None or 0<=a['contactTick']<len(a['frames']),'Contact timing '+a['id'])
 check(all(str(row['frame']) in p['newFrames'] for row in a['frames']),'Every frame available '+a['id'])
 check(all(e['id'] in G['effects'] and e.get('sprite')==e['id'] for row in a['frames'] for e in row.get('effects',[])),'All bitmap effects resolve '+a['id'])
 if a['state'] in ['fire-broken','both-broken']:check(a['key']!='fire','Broken fire has no magic '+a['id'])
 if a['state'] in ['life-broken','both-broken']:check(a['key'] not in ['regen','revive'],'Broken life has no life effects '+a['id'])
 if a['unit']=='owl' and a['state']=='broken':check(a['key']!='canto','Broken engine has no canto '+a['id'])
 if a['key']=='hit':check(all(row['frame']==0 for row in a['frames']),'Hit feedback uses fixed pose '+a['id'])
for key in ['cyclops','owl']:
 for state in ['intact','broken']:
  for i in range(4):
   right=Image.open(R/f'assets/{key}-{state}-maps-{4+i:02}.png').convert('RGBA');left=Image.open(R/f'assets/{key}-{state}-maps-{12+i:02}.png').convert('RGBA')
   check(right.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==left.tobytes(),'Symmetric whole-frame mirror '+key+state+str(i))
for key in D['units']:
 for state in D['visuals']['states'][key]:
  for direction,start in [('down',0),('right',4),('up',8),('left',12)]:check(len({Image.open(R/f'assets/{key}-{state}-maps-{start+i:02}.png').tobytes() for i in range(4)})>=3,'Distinct movement phases '+key+state+direction)
class Doc(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.resources=[];self.history=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if tag=='a' and a.get('href'):self.links.append(a['href'])
  if tag in ['script','img','link'] and (a.get('src') or a.get('href')):self.resources.append(a.get('src') or a.get('href'))
  if tag=='details' and a.get('id')=='revision-history':self.history.append(a)
def doc(p):x=Doc();x.feed(p.read_text());return x
old=doc(R/'source/main-index-before.html');new=doc(BASE/'index.html');check(set(old.ids)<=set(new.ids),'Every existing main-gallery anchor retained');check(set(old.links)<=set(new.links),'Every existing main-gallery link retained');check(len(new.ids)==len(set(new.ids)),'Main gallery unique IDs');check(len(new.history)==1 and 'open' not in new.history[0],'One default-closed revision history');check((BASE/'index.html').read_text().count('puppet-trio-v2-20261105/gallery-extension.js')==1,'Extension loaded once');check((BASE/'index.html').read_text().index('puppet-trio-v2-20261105/gallery-extension.js')<(BASE/'index.html').read_text().index('src="tools/gallery.js'),'Extension loads before player')
for page in [R/'index.html',BASE/'index.html']:
 t=doc(page);check(len(t.ids)==len(set(t.ids)),'Unique IDs '+page.name)
 links=t.resources+t.links if page==R/'index.html' else [x for x in t.links+t.resources if 'puppet-trio' in x]
 for path in links:
  u=urlsplit(path)
  if u.scheme or path.startswith('#') or u.path=='qa/verification.json':continue
  check((page.parent/unquote(u.path)).exists(),'HTML resource resolves '+str(page.relative_to(BASE))+' '+path)
# Both installed art-review pages stay on the same programs.
actions={(a['unit'],a['state'],a['key']):a for a in G['actions']}
profiles={p['id']:p for p in G['profiles']}
for state in ('intact','broken'):
 a=actions['cyclops',state,'map-idle']
 check([a['frames'][i]['frame'] for i in (0,14,22,36)]==[16,17,18,19] and all(f['offset']==[0,0] for f in a['frames']),'Independent symmetric Cyclops idle '+state)
 a=actions['cyclops',state,'walk-up']
 check(a['referenceFrame']==8 and a['neededFrames']==[8,9,10,11] and all(f['source']=='cyclops-idle-rear' for f in M['frames'][f'cyclops-{state}-maps'][8:12]),'True rear walk and reference '+state)
 a=actions['owl',state,'attack'];rows=a['frames'];check([rows[i]['frame'] for i in (32,54,79,92,120)]==[3,4,5,6,7] and rows[54]['offset'][1]==-50 and rows[92]['offset'][1]==0 and a['contactTick']==92,'Owl climbs then dives for one hit '+state)
 check(any('jet-' in e for e in a['effectIds'])==(state=='intact'),'Engine controls wing jet only '+state)
for state,key,n,occupied in [('intact','aura',5,6),('intact','aura-full',8,8),('intact','aura-empty',0,0),('broken','aura',0,6)]:
 a=actions['cyclops',state,key]
 check(a['reviewGround'].endswith('healing-ground-f25.png') and len(a['reviewCompanions'])==occupied and len(a['frames'][30]['effects'])==n,'Real ground and precise occupied healing '+state+' '+key)
 allowed={tuple(s['fxPosition']) for i,s in enumerate(a['healSlots']) if i in a['healedSlots']}
 check(all({tuple(e['position']) for e in row['effects']}==(allowed if 24<=i<76 else set()) for i,row in enumerate(a['frames'])),'Only healed targets emit effects '+state+' '+key)
a=actions['owl','intact','canto'];rows=a['frames'];check(rows[-1]['offset']==[96,0] and 'trio-jet-main' in a['effectIds'] and rows[34]['offset'][0]-rows[24]['offset'][0]>rows[22]['offset'][0]-rows[12]['offset'][0],'Engine burst accelerates across exactly three tiles')
for state in D['visuals']['states']['prometheus']:
 a=actions['prometheus',state,'defeat'];rows=a['frames']
 check(all(r['frame']==0 and r['offset']==[0,0] and r.get('alpha',1)==(0 if i>=28 else 1) for i,r in enumerate(rows)),'Boss remains upright until in-place removal '+state)
 check([rows[i]['effects'][0]['id'] for i in (25,28,50,83)]==['trio-blast-flash','trio-blast-peak','trio-blast-debris','trio-blast-smoke'] and all(e['position'][0]==a['origin'][0] for r in rows for e in r['effects']),'Flash, explosion, debris and smoke centered '+state)
 if state in ('intact','life-broken'):
  a=actions['prometheus',state,'fire'];rows=a['frames']
  check([rows[i]['effects'][0]['id'] for i in (38,55,68,104)]==['trio-flame-ignite','trio-flame-stream','trio-flame-crest','trio-flame-embers'] and G['effects'][rows[68]['effects'][0]['id']]['frame_size'][0]>=130 and a['contactTick']==68,'Long fire crest with single settlement '+state)
 if state in ('intact','fire-broken'):
  a=actions['prometheus',state,'revive']
  check(a['frames'][28]['state_override']==('life-broken' if state=='intact' else 'both-broken') and a['effectIds']==['trio-revive'],'Standing revival does not explode or change fire state '+state)
for a in G['actions']:
 for audio in a.get('soundEvents',[]):
  check((BASE/audio['path']).is_file() and 0<=audio['tick']<len(a['frames']),'Audio resolves '+a['id'])
check(all(not v['touching_source_edge'] for v in M['source_evidence'].values()),'Used generated sheets have no trimmed character contour')
# Existing runtime code/data/assets (exclude generated caches and reports).
before=json.loads((R/'source/runtime-before.json').read_text());changed=[]
skip={'.godot','.git','reports','dist','build','__pycache__'}
present={str(p.relative_to(ROOT)) for p in (ROOT/'actual').rglob('*') if p.is_file() and not (set(p.relative_to(ROOT/'actual').parts)&skip)}
added=sorted(present-set(before));removed=sorted(set(before)-present)
for p,digest in before.items():
 f=ROOT/p
 if f.exists() and hashlib.sha256(f.read_bytes()).hexdigest()!=digest:changed.append(p)
check(not (changed or removed or added),'Runtime code/data/resources byte-for-byte unchanged ('+str(len(before))+') '+str((changed,removed,added))[:350])
for f in ['build_assets.py','build_gallery.py','check_assets.py']:ast.parse((R/f).read_text())
for f in [R/'rules.js',R/'preview.js',R/'gallery-extension.js',BASE/'tools/gallery.js']:subprocess.run(['node','--check',str(f)],check=True)

# Art-only composites implement the same draw order and registered positions as the player.
def draw(a,t,bg,reference=False):
 p=profiles[a['profile']];row=a['frames'][t];out=Image.new('RGBA',(256,160),bg)
 def blit(path,pos,size,flip=False,alpha=1,tint=1,sat=1):
  im=Image.open(BASE/path).convert('RGBA').resize(tuple(map(round,size)),Image.Resampling.NEAREST)
  if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if tint!=1 or sat!=1:
   band=im.getchannel('A');im=ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(tint)).enhance(sat);im.putalpha(band)
  if alpha!=1:im.putalpha(im.getchannel('A').point(lambda v:round(v*alpha)))
  out.alpha_composite(im,tuple(map(round,pos)))
 if a.get('reviewGround'):blit(a['reviewGround'],[0,0],[256,160])
 for c in a.get('reviewCompanions',[]):blit(c['path'],[c['origin'][0]-c['anchor'][0]+row.get('companionShake',0),c['origin'][1]-c['anchor'][1]],c['size'],c['flip'],tint=row.get('companionTint',1))
 def paint(layer):
  for e in row.get('effects',[]):
   if e.get('layer','front')!=layer:continue
   f=G['effects'][e['id']];w,h=e.get('size',f['frame_size']);ax,ay=f['anchor'];blit(f['path'],[e['position'][0]-ax*w/f['frame_size'][0],e['position'][1]-ay*h/f['frame_size'][1]],[w,h],e.get('flip',False),e.get('alpha',1),e.get('tint',1),f.get('saturation',1))
 paint('back')
 origin=a['origin'];anchor=p['anchor'];f=a['referenceFrame'] if reference else row['frame']
 blit(p['newFrames'][str(f)],[origin[0]+row['offset'][0]-anchor[0]+row.get('shake',0),origin[1]+row['offset'][1]-anchor[1]],p['sourceFrameSize'],(p['context']=='battle' and p['side']=='enemy')!=row['flip'],row.get('alpha',1),row.get('tint',1),p.get('reviewSaturation',1))
 paint('front')
 return out
qa=R/'qa';shots=[]
def sheet(name,rows):
 w,h=256,160;gap=24;page=Image.new('RGB',(max(map(len,rows))*w,len(rows)*(h+gap)),(20,30,36));d=ImageDraw.Draw(page)
 for y,row in enumerate(rows):
  for x,(u,s,k,t) in enumerate(row):
   page.paste(draw(actions[u,s,k],t,(27,42,52,255)).convert('RGB'),(x*w,y*(h+gap)));d.text((x*w+8,y*(h+gap)+h+5),f'{s} / {k} / {t+1}',fill=(225,238,235))
 path=name+'.png';page.save(qa/path,optimize=True);shots.append(path)
def spec(u,s,k,*ticks):return [(u,s,k,t) for t in ticks]
sheet('cyclops-healing',[
 spec('cyclops','intact','aura',0,30)+spec('cyclops','intact','aura-empty',30),
 spec('cyclops','intact','aura-full',30)+spec('cyclops','broken','aura',30)+spec('cyclops','intact','aura',85)])
sheet('cyclops-map-poses',[spec('cyclops',s,k,*ticks) for s,k,ticks in [('intact','map-idle',[0,16,25,38]),('broken','map-idle',[0,16,25,38]),('intact','walk-up',[0,13,25,37]),('broken','walk-up',[0,13,25,37])]])
sheet('owl-dive', [spec('owl',s,'attack',32,54,79,92) for s in ('intact','broken')])
sheet('owl-canto', [spec('owl','intact','canto',8,30,64,96)])
sheet('prometheus-flame', [spec('prometheus','intact','fire',38,55,68,104)])
sheet('prometheus-blast', [spec('prometheus',s,'defeat',16,25,28,50,83) for s in ('intact','fire-broken','life-broken','both-broken')])
sheet('prometheus-revival', [spec('prometheus',s,'revive',20,45) for s in ('intact','fire-broken')])
# Verify revised poses and visible FX stay inside the ordinary scene camera.
from functools import lru_cache
@lru_cache(None)
def bounds(path):return Image.open(BASE/path).convert('RGBA').getbbox()
def within(b,pos,scale=(1,1),flip=False,width=0):
 l,t,r,b=b
 if flip:l,r=width-r,width-l
 return 0<=pos[0]+l*scale[0] and 0<=pos[1]+t*scale[1] and pos[0]+r*scale[0]<=256 and pos[1]+b*scale[1]<=160
for a in G['actions']:
 if (a['unit']=='owl' and a['key'] in ('attack','canto')) or (a['unit']=='prometheus' and a['key'] in ('fire','defeat')):
  p=profiles[a['profile']];ox,oy=a['origin'];ax,ay=p['anchor'];pw=p['sourceFrameSize'][0]
  for row in a['frames']:
   dx,dy=row['offset']
   if row.get('alpha',1)>0:
    if not within(bounds(p['newFrames'][str(row['frame'])]),(ox+dx-ax,oy+dy-ay),flip=(p['context']=='battle' and p['side']=='enemy')!=row['flip'],width=pw):raise AssertionError((a['id'],row))
   for e in row['effects']:
    f=G['effects'][e['id']];w,h=f['frame_size'];ew,eh=e.get('size',(w,h));sx,sy=ew/w,eh/h;x,y=e['position'];ex,ey=f['anchor']
    if not within(bounds(f['path']),(x-ex*sx,y-ey*sy),(sx,sy),e['flip'],w):raise AssertionError((a['id'],e))
  check(True,'Full silhouettes and FX stay within regular camera '+a['id'])

# Native map comparison: real enemy bowman first, then revised puppet states.
def native_sample(unit,state,scene):
 p=R/f'assets/{unit}-{state}-{scene}-00.png';im=Image.open(p).convert('RGBA')
 return im.resize((im.width//2,im.height//2),Image.Resampling.NEAREST) if scene=='maps' else im
archer=json.loads((ROOT/'actual/data/tactical_idle_20261031.json').read_text())['12_enemy']['path'].removeprefix('res://')
ar=Image.open(ROOT/'actual'/archer).convert('RGBA').crop((0,0,96,96))
ar=ar.resize((24,24),Image.Resampling.NEAREST)
native=[(u,s,native_sample(u,s,'battle'),native_sample(u,s,'maps')) for u in D['units'] for s in D['visuals']['states'][u]]
def avg_saturation(im):
 h=im.convert('RGB').convert('HSV').getchannel('S')
 data=[s for s,a in zip(h.getdata(),im.getchannel('A').getdata()) if a>=128]
 return round(sum(data)/len(data)/255,3)
sample_saturation={'runtime_archer':avg_saturation(ar),**{u+'-'+s:avg_saturation(m) for u,s,b,m in native}}
check(M['baked_palette']=={'character_saturation':.72,'effect_saturation':.82},'Low-saturation preview grade is baked into all packed actors and FX')
for theme,bg,ink in [('dark',(27,42,52),(228,234,238)),('light',(218,225,230),(25,37,42))]:
 out=Image.new('RGB',(880,368),bg);draw_text=ImageDraw.Draw(out)
 draw_text.text((8,6),'runtime enemy archer / native map',fill=ink)
 out.paste(ar,(68,144),ar);out.paste(ar,(68,328),ar)
 for i,(u,s,b,m) in enumerate(native):
  x,y=176+(i%4)*176,(i//4)*184;draw_text.text((x+8,y+6),u+' / '+s,fill=ink)
  out.paste(b,(x+(176-b.width)//2,y+120-b.height),b)
  out.paste(m,(x+(176-m.width)//2,y+167-m.height),m)
 name=f'native-1x-{theme}.png';out.save(qa/name,optimize=True);shots.append(name)
 check((qa/name).stat().st_size<200000,'Native contrast contact sheet under 200KB '+theme)
rule=json.loads((qa/'rule-checks.json').read_text());gallery=json.loads((qa/'gallery-checks.json').read_text());report={'passed':True,'static_checks':len(checks),'checks':checks,'rule_and_handler_checks':rule['count'],'main_gallery_checks':gallery['count'],'native_map_mean_hsv_saturation':sample_saturation,'units':3,'states':8,'profiles':len(G['profiles']),'actions':len(G['actions']),'whole_pose_images':sum(map(len,M['frames'].values())),'fx_images':len(G['effects']),'runtime_files_hashed':len(before),'runtime_changed':changed,'stage_deployment':None,'browser_rendering_verified':False,'browser_limitation':'Local file protocol was unavailable to the browser tool; checks use a non-rendering DOM mock and art composites.','art_composites':shots,'mobile_layout':'Native 1x sizes checked as standalone bitmap composites. Browser layout not verified.'}
(qa/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['static_checks','rule_and_handler_checks','runtime_files_hashed','actions','whole_pose_images','browser_rendering_verified']},ensure_ascii=False))
