"""Targeted review-art checks. Does not run, import, or modify the game."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from html.parser import HTMLParser
import hashlib, json, shutil, subprocess, sys
from urllib.parse import urlsplit,parse_qs,unquote

V=Path(__file__).resolve().parents[1];R=V.parent;PROJECT=R.parents[1]
sys.path.insert(0,str(R/'tools'))
from export_gallery import font
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def im(p):return Image.open(p).convert('RGBA')
def delta(a,b):return sum(x!=y for x,y in zip(a.getdata(),b.getdata()))
def components(image):
    pts={(x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y))[3]};groups=[]
    while pts:
        todo=[pts.pop()];part=[]
        while todo:
            x,y=todo.pop();part.append((x,y))
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    q=x+dx,y+dy
                    if q in pts:pts.remove(q);todo.append(q)
        groups.append(part)
    return groups
checks={}; keys=['class-12-ally','class-12-enemy','class-6-ally','class-6-enemy']
for filename,root in [('protected-baseline.json',PROJECT),('other-mappings-baseline.json',R)]:
    data=read(V/filename); changed=[p for p,h in data.items() if not(root/p).exists() or sha(root/p)!=h]
    assert not changed,changed
    checks[filename]={'files_checked':len(data),'changed':changed}
units={}
for key in keys:
    O=V/'deliverables'/key;L=V/'layers'/key;role='archer'if'12'in key else'spear';checks_for_unit=[]
    mapping=read(R/f'professions/{key}/maps/frame_mapping.json');before=read(V/'reference'/f'{key}-mapping-before.json')
    for context in ['tactical-walk','tactical-idle']:
        now=next(s for s in mapping['scenarios']if s['id']==context);old=next(s for s in before['scenarios']if s['id']==context)
        for field in ['source_atlas','source_frame_size','source_anchor','timing','directions','direction_mirror_x']:
            assert now[field]==old[field],(key,field)
        assert now['preview_ground']=='map-motion-review-v3/reference/grounds/tactical-M11.png'
        assert now['output_frame_size']==[n*4 for n in now['source_frame_size']]
        for f in now['frame_mapping']:
            p=(R/f'professions/{key}/maps'/f['output_path']).resolve();assert p.exists() and sha(p)==f['sha256']
    for a,b in [(0,1),(2,3),(4,5)]:
        first=im(O/f'walk-{a:02}.png');second=im(O/f'walk-{b:02}.png');mask=Image.open(L/f'mask-{a:02}.png').convert('L')
        outside=sum(x!=y for x,y,m in zip(first.getdata(),second.getdata(),mask.getdata()) if not m)
        assert outside==0,(key,a,'fixed pixels changed',outside)
        assert delta(first,second)>0
        checks_for_unit.append({'walk_pair':[a,b],'changed_pixels':delta(first,second),'outside_moving_region_changes':outside})
    for dst,src in [(6,2),(7,3)]:assert im(O/f'walk-{dst:02}.png').tobytes()==im(O/f'walk-{src:02}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
    aliases=[0,0,2,0,0,0]if role=='archer'else[0,1,2,1,0,1]
    for n,src in enumerate(aliases):assert im(O/f'idle-{n:02}.png').tobytes()==im(O/f'idle-{src:02}.png').tobytes()
    first=im(O/'idle-00.png')
    if role=='archer':
        moving=Image.open(L/'mask-06.png').convert('L')
    else:
        moving=Image.new('L',(96,96))
        for layer in ['spear.png','holding-arm.png']:
            alpha=im(L/'idle-layered'/layer).getchannel('A')
            for dx,dy in [(0,0),(-4,0),(-4,-4)]:
                shifted=Image.new('L',(96,96));shifted.paste(alpha,(dx,dy));moving=ImageChops.lighter(moving,shifted)
    for n in [1,2]:
        second=im(O/f'idle-{n:02}.png');outside=sum(x!=y for x,y,m in zip(first.getdata(),second.getdata(),moving.getdata())if not m)
        assert outside==0,(key,'idle fixed region',n,outside)
        if role=='spear':
            for rect in [(25,17,48,41),(48,38,62,53),(0,71,96,96),(39,57,60,65)]:assert first.crop(rect).tobytes()==second.crop(rect).tobytes()
        checks_for_unit.append({'idle_frame':n,'changed_pixels':delta(first,second),'outside_moving_region_changes':outside})
    colors=set();largest=0
    for kind,count,size in [('walk',8,(128,96)),('idle',6,(96,96))]:
        for i in range(count):
            p=O/f'{kind}-{i:02}.png';image=im(p);assert image.size==size
            assert set(image.getchannel('A').getdata())=={0,255}
            colors|={v[:3]for v in image.getdata()if v[3]}
            assert not [c for c in components(image)if len(c)<=3],(key,kind,i,'isolated fragment')
            largest=max(largest,p.stat().st_size)
    assert len(colors)==4
    if key.endswith('ally'):
        story=next(s for s in mapping['scenarios']if s['id']=='story');idle=next(s for s in mapping['scenarios']if s['id']=='tactical-idle')
        assert story['static_pose_preview'] and len(story['frame_mapping'])==1
        assert story['frame_mapping'][0]['output_path']==idle['frame_mapping'][0]['output_path']
        assert story['preview_ground']=='map-motion-review-v3/reference/grounds/story-P00-cobble.png'
    else:assert all(s['id']!='story' for s in mapping['scenarios'])
    assert not mapping['runtime_integrated'] and mapping['status']=='awaiting_user_review'
    units[key]={'checks':checks_for_unit,'opaque_colors':sorted(colors),'max_frame_bytes':largest,'source_timing_and_directions_unchanged':True,'mirror_pairs':[[6,2],[7,3]],'native_idle_aliases':aliases,'alpha':'binary','isolated_fragments_le_3_pixels':0}

shadow=im(R/'hunapu-story-shadow-20261018/story-shadow.png')
assert shadow.size==(11,3) and len(components(shadow))==1 and shadow.getpixel((5,1))[3]==255
data=read(R/'demos/gallery-data.json');actions={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']}
assert not data['validation']['structuralIssues']
selected=[a for a in data['actions']if any(a['profile'].startswith('professions-'+key+'-maps-')for key in keys)]
assert len(selected)==38
exports=[];safe_text=[]
draw=ImageDraw.Draw(Image.new('RGB',(584,328)))
for a in selected:
    assert a['ready'] and not a['missingFrames'] and not a['missingEffects'] and a['video'] and a['still']
    p=profiles[a['profile']];video=R/a['video'];metadata=read(video.with_suffix('.json'))
    assert metadata['contentDigest']==a['contentDigest']
    raw=subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,duration,r_frame_rate','-of','json',str(video)],text=True)
    info=json.loads(raw)['streams'][0];assert int(info['nb_frames'])==len(a['frames'])
    assert abs(float(info['duration'])-len(a['frames'])/a['fps'])<.002
    assert [info['width'],info['height']]==[584,328]
    title=p['actorName']+' · '+a['name'];f=next((font(n)for n in range(22,13,-1)if draw.textbbox((0,0),title,font=font(n))[2]<=536),font(14));bounds=draw.textbbox((0,0),title,font=f)
    assert bounds[2]-bounds[0]<=536 and 14+bounds[3]<48
    for text in [a.get('referenceLabel','原作'),'四倍像素重绘']:assert draw.textbbox((0,0),text,font=font(15))[2]<=232
    for n in [0,len(a['frames'])-1]:
        label=f'第 {n+1} / {len(a["frames"])} 帧  ·  源姿势 {a["frames"][n]["frame"]}  ·  {n/a["fps"]:.3f} 秒'
        bounds=draw.textbbox((0,0),label,font=font(15));assert bounds[2]<=536 and 284+bounds[3]<=312
    safe_text.append({'action':a['id'],'title_width':draw.textbbox((0,0),title,font=f)[2],'safe_width':536,'source_labels_and_footer_fit':True})
    exports.append({'action':a['id'],'frames':int(info['nb_frames']),'duration':float(info['duration']),'content_digest_current':True})
overview=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,duration','-of','json',str(V/'overview.mp4')],text=True))['streams'][0]
assert int(overview['nb_frames'])==2008 and abs(float(overview['duration'])-2008/60.0988)<.004
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ['href','src']:self.links.append(v)
links=Links();links.feed((R/'index.html').read_text())
for href in links.links:
    u=urlsplit(href)
    if u.scheme or u.netloc:continue
    if u.path:assert (R/unquote(u.path)).exists(),href
    if 'action'in parse_qs(u.query):assert parse_qs(u.query)['action'][0]in actions,href
node=shutil.which('node');assert node,'Node.js not found'
subprocess.run([node,'--check',str(R/'tools/gallery.js')],check=True)
subprocess.run([node,'--check',str(R/'gallery-data.js')],check=True)
report={'status':'technical_checks_passed_awaiting_user_visual_acceptance','scope':'Four tactical map sets plus two allied static story appearances; no test-package integration.',
  'protected_files':checks,'units':units,'continuous_shadow':{'size':[11,3],'components':1,'fixed_across_phases':True},
  'exports':exports,'overview':overview,'offline_text_safe_area':safe_text,'browser_visual_inspection':'Not performed; prior file URL access restriction respected. Offline gallery renders inspected instead.','gallery_summary':data['summary']}
(V/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'units':len(units),'actions':len(exports),'overview_frames':2008,'protected_files_unchanged':sum(x['files_checked']for x in checks.values()),'status':report['status']},ensure_ascii=False))
