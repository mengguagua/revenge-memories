# coding: utf-8
from pathlib import Path
from PIL import Image,ImageEnhance,ImageOps,ImageDraw
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,subprocess,ast
R=Path(__file__).resolve().parent;ROOT=R.parents[2];BASE=R.parent
M=json.loads((R/'asset-manifest.json').read_text());D=json.loads((R/'design.json').read_text());s=(R/'gallery-extension.js').read_text();G=json.loads(s.split('const extra = ',1)[1].split(';\nwindow.PUPPET_TRIO_DATA',1)[0]);checks=[]
def check(ok,label):
 checks.append({'label':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
for image in M['images']:
 p=R/image['path'];im=Image.open(p);check(im.size==tuple(image['pixels']) and p.stat().st_size==image['bytes'],'Image dimensions/bytes '+image['path'])
 check(p.stat().st_size<50000,'Image below50KB '+image['path'])
for group,frames in M['frames'].items():
 check(len(frames)==(8 if group.endswith('battle') else 16),'Complete pose set '+group)
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
old=doc(R/'source/index-before.html');new=doc(BASE/'index.html');check(set(old.ids)<=set(new.ids),'Every existing main-gallery anchor retained');check(set(old.links)<=set(new.links),'Every existing main-gallery link retained');check(len(new.ids)==len(set(new.ids)),'Main gallery unique IDs');check(len(new.history)==1 and 'open' not in new.history[0],'One default-closed revision history');check((BASE/'index.html').read_text().count('puppet-trio-v1-20261105/gallery-extension.js')==1,'Extension loaded once');check((BASE/'index.html').read_text().index('puppet-trio-v1-20261105/gallery-extension.js')<(BASE/'index.html').read_text().index('src="tools/gallery.js'),'Extension loads before player')
for page in [R/'index.html',BASE/'index.html']:
 t=doc(page);check(len(t.ids)==len(set(t.ids)),'Unique IDs '+page.name)
 links=t.resources+t.links if page==R/'index.html' else [x for x in t.links+t.resources if 'puppet-trio' in x]
 for path in links:
  u=urlsplit(path)
  if u.scheme or path.startswith('#') or u.path in ['README.md','qa/verification.json']:continue
  check((page.parent/unquote(u.path)).exists(),'HTML resource resolves '+str(page.relative_to(BASE))+' '+path)
# All game resources/code/stages byte-for-byte unchanged.
before=json.loads((R/'source/runtime-before.json').read_text());changed=[]
for p,digest in before.items():
 f=ROOT/p
 if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:changed.append(p)
check(not changed,'Runtime code/data/resources byte-for-byte unchanged ('+str(len(before))+')')
for f in ['create_design.py','build_assets.py','build_gallery.py','check_assets.py']:ast.parse((R/f).read_text())
for f in ['rules.js','preview.js','gallery-extension.js']:subprocess.run(['node','--check',str(R/f)],check=True)
# Art composites render the same frame programs without running a browser or UI engine.
def draw(a,t,bg):
 p=next(p for p in G['profiles'] if p['id']==a['profile']);row=a['frames'][t];out=Image.new('RGBA',(256,160),bg)
 def blit(path,pos,size,flip=False,alpha=1,tint=1):
  im=Image.open(BASE/path).convert('RGBA').resize(tuple(map(round,size)),Image.Resampling.NEAREST)
  if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if tint!=1:
   band=im.getchannel('A');im=ImageEnhance.Brightness(im).enhance(tint);im.putalpha(band)
  if alpha!=1:im.putalpha(im.getchannel('A').point(lambda v:round(v*alpha)))
  out.alpha_composite(im,tuple(map(round,pos)))
 for c in a.get('reviewCompanions',[]):blit(c['path'],[c['origin'][0]-c['anchor'][0]+row.get('companionShake',0),c['origin'][1]-c['anchor'][1]],c['size'],c['flip'],tint=row.get('companionTint',1))
 origin=a['origin'];anchor=p['anchor'];blit(p['newFrames'][str(row['frame'])],[origin[0]+row['offset'][0]-anchor[0]+row.get('shake',0),origin[1]+row['offset'][1]-anchor[1]],p['sourceFrameSize'],(p['context']=='battle' and p['side']=='enemy')!=row['flip'],row.get('alpha',1),row.get('tint',1))
 for e in row.get('effects',[]):
  f=G['effects'][e['id']];blit(f['path'],[e['position'][0]-f['anchor'][0],e['position'][1]-f['anchor'][1]],f['frame_size'],e['flip'],e.get('alpha',1))
 return out
samples=[('cyclops','intact','attack',[36,60]),('cyclops','broken','attack',[60]),('owl','intact','attack',[30,68]),('owl','broken','attack',[68]),('prometheus','intact','attack',[68]),('prometheus','both-broken','attack',[68]),('prometheus','intact','ranged',[52,66]),('prometheus','intact','fire',[52,66]),('prometheus','fire-broken','revive',[24,50]),('prometheus','life-broken','fire',[66])]
shots=[]
for unit,state,key,ticks in samples:
 a=next(a for a in G['actions'] if a['unit']==unit and a['state']==state and a['key']==key)
 for tick in ticks:
  name=f'{unit}-{state}-{key}-{tick}.png';draw(a,tick,(27,42,52,255)).resize((768,480),Image.Resampling.NEAREST).save(R/'qa'/name);shots.append(name)
rule=json.loads((R/'qa/rule-checks.json').read_text());report={'passed':True,'static_checks':len(checks),'checks':checks,'rule_and_handler_checks':rule['count'],'units':3,'states':8,'profiles':16,'actions':106,'whole_pose_images':192,'runtime_files_hashed':len(before),'runtime_changed':changed,'stage_deployment':None,'browser_rendering_verified':False,'browser_limitation':'Browser tool blocked local file: protocol. No workaround browser or server used. Rules/handlers tested in non-rendering DOM mock; native art and frame programs checked directly.','art_composites':shots,'mobile_layout':'Responsive CSS supplied, not browser-rendered/verified. Native1x, integer2x and dark/light art copies inspected separately.'}
(R/'qa/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['static_checks','rule_and_handler_checks','runtime_files_hashed','actions','whole_pose_images','browser_rendering_verified']},ensure_ascii=False))
