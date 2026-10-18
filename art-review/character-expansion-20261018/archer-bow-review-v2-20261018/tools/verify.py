"""Targeted checks for archer frames, weapon/arm motion, exports and protected scope."""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from html.parser import HTMLParser
from urllib.parse import urlsplit,parse_qs
import json,hashlib,subprocess,shutil,sys
V=Path(__file__).resolve().parents[1];R=V.parent;PROJECT=R.parents[1];OLD=R/'archer-spearman-map-review-20261018'
sys.path.insert(0,str(R/'tools'))
from export_gallery import font
def read(p):return json.loads(p.read_text())
def im(p):return Image.open(p).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def components(a):
    pts={(x,y)for y in range(a.height)for x in range(a.width)if a.getpixel((x,y))[3]};groups=[]
    while pts:
        q=[pts.pop()];group=[]
        while q:
            x,y=q.pop();group.append((x,y))
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    p=x+dx,y+dy
                    if p in pts:pts.remove(p);q.append(p)
        groups.append(group)
    return groups
protected=read(V/'protected-baseline.json');changed=[p for p,h in protected.items()if not(PROJECT/p).exists()or sha(PROJECT/p)!=h];assert not changed,changed
weapon=im(V/'layers/bow-ne.png');assert len(components(weapon))==1
assert im(V/'layers/bow-se.png').tobytes()==weapon.transpose(Image.Transpose.ROTATE_270).tobytes()
assert im(V/'layers/bow-sw.png').tobytes()==im(V/'layers/bow-se.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
assembly=im(V/'layers/idle-assembly.png');shifted=Image.new('RGBA',assembly.size);shifted.paste(assembly,(0,4))
assert shifted.tobytes()==im(V/'layers/idle-moving-2.png').tobytes()
body=im(V/'layers/idle-body.png');units={}
for key in ['class-12-ally','class-12-enemy']:
    O=V/'deliverables'/key;d=read(R/f'professions/{key}/maps/frame_mapping.json');before=read(V/f'reference/{key}-mapping-before.json')
    for s,old in zip(d['scenarios'],before['scenarios']):
        for field in ['source_atlas','source_anchor','source_frame_size','output_frame_size','directions','direction_mirror_x','timing','ground_shadow','preview_ground']:
            assert s[field]==old[field],(key,s['id'],field)
        for f in s['frame_mapping']:
            p=(R/f'professions/{key}/maps'/f['output_path']).resolve();assert p.exists() and sha(p)==f['sha256']
    colors=set();tiny=[];sizes=[]
    for kind,count,size in [('walk',8,(128,96)),('idle',6,(96,96))]:
        for n in range(count):
            p=O/f'{kind}-{n:02}.png';a=im(p);assert a.size==size
            assert set(a.getchannel('A').getdata())=={0,255}
            colors|={x[:3]for x in a.getdata()if x[3]};sizes.append(p.stat().st_size)
            for comp in components(a):
                if len(comp)<=2:tiny.append({'frame':p.name,'pixels':comp})
    assert len(colors)==4 and not tiny,(key,tiny)
    for n in [0,1]:assert im(O/f'walk-{n:02}.png').tobytes()==im(OLD/f'deliverables/{key}/walk-{n:02}.png').tobytes()
    for a,b in [(2,3),(4,5)]:
        x=im(O/f'walk-{a:02}.png');y=im(O/f'walk-{b:02}.png')
        assert x.crop((0,0,128,80)).tobytes()==y.crop((0,0,128,80)).tobytes()
        assert x.tobytes()!=y.tobytes()
    for dst,src in [(6,2),(7,3)]:assert im(O/f'walk-{dst:02}.png').tobytes()==im(O/f'walk-{src:02}.png').transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
    for n,src in enumerate([0,0,2,0,0,0]):assert im(O/f'idle-{n:02}.png').tobytes()==im(O/f'idle-{src:02}.png').tobytes()
    for n,dy in [(0,0),(2,4)]:
        expected=body.copy();expected.alpha_composite(assembly,(0,dy))
        if key.endswith('enemy'):
            expected.putdata([(174,81,72,p[3])if p[:3]==(57,118,181)else p for p in expected.getdata()])
        # PNG hidden RGB is immaterial; compare premultiplied visible data.
        actual=im(O/f'idle-{n:02}.png')
        assert all((p==q)or(p[3]==q[3]==0)for p,q in zip(expected.getdata(),actual.getdata()))
    if key.endswith('ally'):
        story=next(s for s in d['scenarios']if s['id']=='story');idle=next(s for s in d['scenarios']if s['id']=='tactical-idle')
        assert story['static_pose_preview']and len(story['frame_mapping'])==1
        assert story['frame_mapping'][0]['output_path']==idle['frame_mapping'][0]['output_path']
    units[key]={'palette':sorted(colors),'max_frame_bytes':max(sizes),'upward_frames_unchanged':True,'walk_fixed_upper_body':True,'same_phase_mirrors':True,'idle_whole_assembly_translation':[0,4],'idle_body_fixed':True,'stray_fragments':tiny}
data=read(R/'demos/gallery-data.json');assert not data['validation']['structuralIssues']
targets=[a for a in data['actions']if a.get('revision')=='archer-bow-v2-20261018'];assert len(targets)==19
profiles={p['id']:p for p in data['profiles']};exports=[];draw=ImageDraw.Draw(Image.new('RGB',(584,328)))
for a in targets:
    assert a['ready'] and a['video']and a['still']and not a['missingFrames']
    path=R/a['video'];assert read(path.with_suffix('.json'))['contentDigest']==a['contentDigest']
    info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,duration,width,height','-of','json',str(path)],text=True))['streams'][0]
    assert int(info['nb_frames'])==len(a['frames'])and abs(float(info['duration'])-len(a['frames'])/a['fps'])<.002
    title=profiles[a['profile']]['actorName']+' · '+a['name'];bounds=draw.textbbox((0,0),title,font=font(22));assert bounds[2]<=536
    exports.append({'action':a['id'],'frames':len(a['frames']),'duration':float(info['duration']),'title_safe_width':bounds[2],'digest_current':True})
overview=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,duration','-of','json',str(V/'overview.mp4')],text=True))['streams'][0]
assert int(overview['nb_frames'])==1004
class Links(HTMLParser):
    def __init__(self):super().__init__();self.values=[]
    def handle_starttag(self,tag,attrs):self.values.extend(v for k,v in attrs if k in ['href','src'])
links=Links();links.feed((R/'index.html').read_text());ids={a['id']for a in data['actions']}
for value in links.values:
    u=urlsplit(value)
    if u.scheme or u.netloc:continue
    if u.path:assert(R/u.path).exists(),value
    if 'action'in parse_qs(u.query):assert parse_qs(u.query)['action'][0]in ids
for p in [R/'gallery-data.js',R/'tools/gallery.js']:subprocess.run([shutil.which('node'),'--check',str(p)],check=True)
report={'status':'technical_checks_passed_awaiting_user_visual_review','protected_file_count':len(protected),'protected_changes':changed,'units':units,
  'weapon':{'connected_components':1,'all_orientations_from_same_complete_bitmap':True,'render_order':'fixed body, rear holding hand/drawing forearm, foreground complete bow/string/arrow'},'exports':exports,'overview':overview,'runtime_integrated':False,
  'visual_checks':'Inspected exported project-ground frames and dark/light contact sheets. Browser playback not performed; existing file access restriction respected.'}
(V/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'protected_files_unchanged':len(protected),'archer_groups':2,'exports':len(exports),'overview_frames':1004,'status':report['status']}))
