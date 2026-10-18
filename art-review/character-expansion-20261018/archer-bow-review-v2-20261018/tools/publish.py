"""Update archer review mappings only, then render their offline demonstrations."""
from pathlib import Path
from PIL import Image
from types import SimpleNamespace
import copy,hashlib,json,os,subprocess,sys
V=Path(__file__).resolve().parents[1];R=V.parent;REV='archer-bow-v2-20261018'
sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export,render_frame
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
keys=['class-12-ally','class-12-enemy'];inventory=[]
for key in keys:
    base=R/f'professions/{key}/maps';O=V/'deliverables'/key
    d=json.loads((V/f'reference/{key}-mapping-before.json').read_text());d.update(revision=REV,status='awaiting_user_review',runtime_integrated=False,
      review_note='弓箭手本轮修订：完整前景弓身、两段弓弦和斜向箭杆；待机双手相关部分与弓箭同动，左右人物面向与行走方向一致。',qa_report=os.path.relpath(V/'verification.json',base))
    for s in d['scenarios']:
        kind='walk'if s['id']=='tactical-walk'else'idle';count=8 if kind=='walk'else 1 if s['id']=='story'else 6;frames=[]
        for i in range(count):
            p=O/f'{kind}-{i:02}.png';subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(p)],check=True)
            prior=s['frame_mapping'][i];image=Image.open(p).convert('RGBA')
            rec={k:v for k,v in prior.items()if k in ['source_index','output_index','native_cpu_frame','source_frame','direction','source_visible_bounds']}
            rec.update(path=os.path.relpath(p,base),output_path=os.path.relpath(p,base),size=list(image.size),bytes=p.stat().st_size,sha256=sha(p),visible_bounds=list(image.getbbox()),art_revision=REV,
              construction='ImageGen body and complete foreground bow/arm layers; fixed-body composite; native mirror and timing retained.',
              generation_record=os.path.relpath(V/'README.md',base))
            frames.append(rec);inventory.append({'path':str(p.relative_to(R)),'purpose':key+' '+s['id'],'dimensions':list(image.size),'bytes':p.stat().st_size,'sha256':sha(p)})
        if s['id']=='story':atlaspath=O/'idle-00.png'
        else:
            w,h=s['output_frame_size'];atlas=Image.new('RGBA',(w*count,h))
            for i in range(count):atlas.paste(Image.open(O/f'{kind}-{i:02}.png'),(w*i,0))
            atlaspath=O/f'{kind}-atlas.png';atlas.save(atlaspath,optimize=True)
        s.update(revision=REV,frame_mapping=frames,output_atlas=os.path.relpath(atlaspath,base),output_atlas_bytes=atlaspath.stat().st_size)
        note='完整弓身在前景；两段弓弦和斜向箭杆保留。'
        if kind=='walk':note+='上身、弓箭及手臂固定，仅腿脚变换；左右脸部和脚部朝向与移动方向一致；向上帧保留。'
        elif s['id']=='story':note+='友军剧情形象与本轮战斗待机首帧一致，仅静止展示。'
        else:note+='拉弦前臂、后方持弓手臂与完整弓箭作为同一组上下移动，身体和腿保持固定。'
        s.update(review_note=note,adaptation_note=note,motion_review={'reference':str((V/'semantic-correction.json').relative_to(R)),'fixed_and_moving_parts':note})
    dump(base/'frame_mapping.json',d)
dump(V/'image-inventory.json',inventory)
data=build();targets=[a for a in data['actions']if any(a['profile'].startswith('professions-'+k+'-maps-')for k in keys)];assert len(targets)==19
args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);reports=[]
for a in targets:reports.append(export(data,a,args));print(a['id'],flush=True)
data=build();lookup={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']};order=[]
for key in keys:
    prefix='professions-'+key+'-maps-';order.append(prefix+'tactical-idle--idle-cycle')
    order.extend(prefix+'tactical-walk--walk-'+direction for direction in ['down','right','left','up'])
order.append('professions-class-12-ally-maps-story--idle-pose')
lines=[];segments=[];frame=0
for aid in order:
    a=lookup[aid];lines.append("file '"+str(R/a['video'])+"'");segments.append({'action':aid,'start_frame':frame,'frames':len(a['frames'])});frame+=len(a['frames'])
(V/'overview-inputs.txt').write_text('\n'.join(lines)+'\n')
subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
for key in keys:
    prefix='professions-'+key+'-maps-'
    for suffix,ticks in [('tactical-idle--idle-cycle',[0,22]),('tactical-walk--walk-down',[0,16]),('tactical-walk--walk-right',[0,16]),('tactical-walk--walk-left',[0,16])]:
        a=lookup[prefix+suffix];p=profiles[a['profile']]
        for tick in ticks:
            for light,name in [(False,'ground'),(True,'light')]:render_frame(data,p,a,tick,4,light).save(V/f'reviews/{key}-{suffix}-{tick}-{name}.png',optimize=True)
dump(V/'export-selection.json',{'actions':reports,'overview_segments':segments,'overview_frames':frame})
print('Published archer review only; 19 exports, 11 overview segments.')
