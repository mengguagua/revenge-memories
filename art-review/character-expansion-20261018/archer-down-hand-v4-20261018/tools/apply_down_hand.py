"""Change only the prepared downward drawing-hand layer's compositing order."""
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
import hashlib,json,os,subprocess,sys

V=Path(__file__).resolve().parents[1];R=V.parent;PREV=R/'archer-arms-step-v3-20261018';REV=V.name
sys.path.insert(0,str(R/'tools'))
from build_gallery import build
from export_gallery import export,render_frame
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgba(p):return Image.open(p).convert('RGBA')
def run(*args):subprocess.run(['/opt/homebrew/bin/magick',*map(str,args)],check=True)

keys=['class-12-ally','class-12-enemy'];target_ids={f'professions-{k}-maps-tactical-walk--{kind}-down'for k in keys for kind in ['walk','idle']}
baseline_file=V/'reference/unchanged-baseline.json'
if not baseline_file.exists():
    # Protect all prior archer frames and all unrelated mappings. This focused
    # correction does not rerun the broader art pipeline or any game import.
    assets=[*PREV.glob('deliverables/*/walk-*.png'),*PREV.glob('deliverables/*/idle-*.png')]
    assets += [p for p in R.glob('**/frame_mapping.json')if p.parent.name!='maps'or p.parent.parent.name not in keys]
    dump(baseline_file,{str(p.relative_to(R)):sha(p)for p in assets})
    dump(V/'reference/action-digests-before.json',{a['id']:a['contentDigest']for a in read(R/'demos/gallery-data.json')['actions']})
for key in keys:
    backup=V/f'reference/{key}-mapping-before.json'
    if not backup.exists():dump(backup,read(R/f'professions/{key}/maps/frame_mapping.json'))

hand=PREV/'layers/drawing-down.png';hand_rgba=rgba(hand);inventory=[];changes=[]
for key in keys:
    base=R/f'professions/{key}/maps';mapping=read(V/f'reference/{key}-mapping-before.json')
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-walk');out=V/'deliverables'/key;out.mkdir(exist_ok=True)
    for n in [4,5]:
        record=next(f for f in scenario['frame_mapping']if f['source_index']==n)
        source=(base/record['output_path']).resolve();destination=out/f'walk-{n:02}.png'
        run(source,hand,'-compose','Over','-composite',destination)
        subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3','--strip','safe',str(destination)],check=True)
        before=rgba(source);after=rgba(destination);points=[]
        for y in range(after.height):
            for x in range(after.width):
                a=before.getpixel((x,y));b=after.getpixel((x,y));h=hand_rgba.getpixel((x,y))
                if a!=b:
                    assert h[3]==255 and b==h,(key,n,x,y)
                    points.append([x,y])
                if h[3]:assert b==h
        assert len(points)==18 and after.size==(128,96)
        bounds=[min(p[0]for p in points),min(p[1]for p in points),max(p[0]for p in points)+1,max(p[1]for p in points)+1]
        assert bounds==[54,55,59,61]
        # The formerly visible string center at the nock is now covered by skin.
        assert before.getpixel((57,56))==(228,225,200,255)
        assert after.getpixel((57,56))==(221,167,125,255)
        assert len({p[:3]for p in after.getdata()if p[3]})==4
        assert set(after.getchannel('A').getdata())=={0,255}
        changes.append({'actor':key,'frame':n,'changed_pixels':len(points),'bounds':bounds,'outside_hand_unchanged':True,'string_nock_covered_by_hand':True})
        path=os.path.relpath(destination,base)
        record.update(path=path,output_path=path,bytes=destination.stat().st_size,sha256=sha(destination),art_revision=REV,
          construction='Existing drawing forearm/hand composited above the bowstring at the nock; no new drawing, no part translation.',generation_record=os.path.relpath(V/'README.md',base))
        inventory.append({'path':str(destination.relative_to(R)),'purpose':key+' downward walk hand occlusion','dimensions':[128,96],'bytes':destination.stat().st_size,'sha256':sha(destination)})
    atlas=Image.new('RGBA',(128*8,96))
    for record in scenario['frame_mapping']:atlas.paste(rgba((base/record['output_path']).resolve()),(record['source_index']*128,0))
    atlaspath=out/'walk-atlas.png';atlas.save(atlaspath,optimize=True)
    scenario.update(output_atlas=os.path.relpath(atlaspath,base),output_atlas_bytes=atlaspath.stat().st_size,revision=REV,
      review_note='本轮仅修向下：拉弦手覆盖弓弦交点，显示握住并拉弦；其他方向和步态保留。')
    scenario['motion_review']['downward_hand_correction']=str((V/'README.md').relative_to(R))
    mapping['latest_local_correction']={'revision':REV,'frames':[4,5],'scope':'downward drawing-hand over bowstring','runtime_integrated':False}
    dump(base/'frame_mapping.json',mapping)
dump(V/'image-inventory.json',inventory)

data=build();targets=[a for a in data['actions']if a['id']in target_ids];assert len(targets)==4
args=SimpleNamespace(close=False,scale=4,light=False,stills_only=False);exports=[]
for action in targets:exports.append(export(data,action,args))
data=build();lookup={a['id']:a for a in data['actions']};profiles={p['id']:p for p in data['profiles']}
old_digests=read(V/'reference/action-digests-before.json')
changed_actions=[a['id']for a in data['actions']if old_digests.get(a['id'])!=a['contentDigest']]
assert set(changed_actions)==target_ids,changed_actions

# Refresh the full overview from existing unchanged clips plus the four updated
# downward walk/hold exports. Other directions are not rendered again.
order=[]
for key in keys:
    prefix='professions-'+key+'-maps-';order.append(prefix+'tactical-idle--idle-cycle')
    order.extend(prefix+'tactical-walk--walk-'+d for d in ['down','right','left','up'])
order.append('professions-class-12-ally-maps-story--idle-pose')
lines=[]
for aid in order:
    assert lookup[aid]['video'];lines.append("file '"+str(R/lookup[aid]['video'])+"'")
(V/'overview-inputs.txt').write_text('\n'.join(lines)+'\n')
subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(V/'overview-inputs.txt'),'-c','copy','-movflags','+faststart',str(V/'overview.mp4')],check=True)
for key in keys:
    a=lookup[f'professions-{key}-maps-tactical-walk--walk-down'];p=profiles[a['profile']]
    for tick in [0,16]:render_frame(data,p,a,tick,6).save(V/f'reviews/{key}-down-{tick:02}.png',optimize=True)

for path,h in read(baseline_file).items():assert sha(R/path)==h,path
video_checks=[]
for a in targets:
    current=lookup[a['id']];path=R/current['video'];assert read(path.with_suffix('.json'))['contentDigest']==current['contentDigest']
    info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,duration','-of','json',str(path)],text=True))['streams'][0]
    assert int(info['nb_frames'])==len(current['frames']) and abs(float(info['duration'])-len(current['frames'])/current['fps'])<.002
    video_checks.append({'action':current['id'],'frames':int(info['nb_frames']),'duration':float(info['duration'])})
assert not data['validation']['structuralIssues']
dump(V/'verification.json',{'status':'targeted_checks_passed_awaiting_user_review','frame_changes':changes,'changed_action_digests':changed_actions,'other_action_digests_unchanged':len(old_digests)-len(changed_actions),
  'previous_art_and_other_mappings_unchanged':len(read(baseline_file)),'videos':video_checks,'runtime_integrated':False,'browser_playback':'Not performed; exported comparison frames inspected.'})
dump(V/'export-selection.json',{'exports':exports,'overview_actions':order})
print({'frames_changed':4,'pixels_changed_per_frame':18,'changed_actions':4,'other_actions_unchanged':len(old_digests)-4})
