"""Technical slicing/registration only. Artwork was authored by built-in image_gen.

No anatomy, painted pixels, recoloring, or background synthesis occurs here.
ImageMagick preserves alpha while cropping, uniformly resizing, and compositing.
"""
from pathlib import Path
import json, shutil, subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
MAGICK = '/opt/homebrew/bin/magick'
OXIPNG = '/opt/homebrew/bin/oxipng'
FPS = 60.0988

def bounds(im):
    return im.getchannel('A').point(lambda p: 255 if p >= 32 else 0).getbbox()

def foot_center(im, b):
    depth = max(1, round((b[3]-b[1])*.12))
    foot = im.getchannel('A').point(lambda p: 255 if p >= 32 else 0).crop((0,b[3]-depth,im.width,b[3])).getbbox()
    return (foot[0]+foot[2])/2

def magick(*args):
    subprocess.run([MAGICK,*map(str,args)],check=True)

def save_frame(kind,index,art_path,cell,native_path,frame_size,body_top=None):
    art=Image.open(art_path).convert('RGBA').crop(cell)
    b=bounds(art)
    original=Image.open(native_path).convert('RGBA')
    ob=bounds(original)
    target_foot_x=foot_center(original,ob)*4
    target_foot_y=ob[3]*4
    # Keep body size constant across stationary sword-angle changes.
    scale=(ob[3]-ob[1])*4/(b[3]-(body_top if body_top is not None else b[1]))
    pad=3
    crop=(max(0,b[0]-pad),max(0,b[1]-pad),min(art.width,b[2]+pad),min(art.height,b[3]+pad))
    crop_global=[crop[0]+cell[0],crop[1]+cell[1],crop[2]+cell[0],crop[3]+cell[1]]
    cw,ch=crop[2]-crop[0],crop[3]-crop[1]
    rw,rh=round(cw*scale),round(ch*scale)
    # Integer raster dimensions differ only by rounding; no independent-axis fitting.
    fx=(foot_center(art,b)-crop[0])*rw/cw
    fy=(b[3]-crop[1])*rh/ch
    x=round(target_foot_x-fx)
    y=round(target_foot_y-fy)
    out=ROOT/'deliverables'/f'{kind}-{index:02d}.png'
    tmp=ROOT/'source'/f'crop-{kind}-{index:02d}.png'
    resized=ROOT/'source'/f'registered-content-{kind}-{index:02d}.png'
    magick(art_path,'-crop',f'{cw}x{ch}+{crop_global[0]}+{crop_global[1]}','+repage',tmp)
    magick(tmp,'-filter','Lanczos','-resize',f'{rw}x{rh}!',resized)
    resized_im=Image.open(resized).convert('RGBA');resized_bounds=bounds(resized_im)
    if kind=='tactical-idle' and index==1:
        # Correct the edited blade pose using measured resampled feet, not the
        # bounds of the asymmetrically extended weapon.
        x=round(target_foot_x-foot_center(resized_im,resized_bounds))
        y=round(target_foot_y-resized_bounds[3])
    # A long weapon must be redrawn; never silently move the whole body inward.
    assert x+resized_bounds[0]>=0 and x+resized_bounds[2]<=frame_size[0], (kind,index,'art exceeds horizontal canvas; regenerate prop')
    if y<0 or y+rh>frame_size[1]:
        # Preserve the already reviewed one-pixel transparent foot padding.
        padding_shift=max(0,min(y,frame_size[1]-rh))-y
        assert abs(padding_shift)<=1,(kind,index,'vertical content exceeds canvas')
        y+=padding_shift
    magick('-size',f'{frame_size[0]}x{frame_size[1]}','xc:none',resized,'-geometry',f'+{x}+{y}','-compose','over','-composite',out)
    subprocess.run([OXIPNG,'-o','3','--strip','safe',str(out)],check=True,capture_output=True)
    final=Image.open(out).convert('RGBA')
    rec={'source_index':index,'output_index':index,'path':str(out.relative_to(ROOT)),'output_path':str(out.relative_to(ROOT)),
      'generated_source':str(art_path.relative_to(ROOT)),'generated_source_cell':list(cell),'generated_content_bounds':list(b),
      'crop_global':crop_global,'uniform_scale':scale,'resampled_size':[rw,rh],'registration_offset':[x,y],
      'source_visible_bounds':list(ob),'source_foot_anchor':[foot_center(original,ob),ob[3]],
      'target_foot_anchor':[target_foot_x,target_foot_y],'output_visible_bounds':list(bounds(final)),
      'size':list(final.size),'bytes':out.stat().st_size,'alpha':'RGBA; generated alpha retained; alpha>=32 used only for bounds measurement',
      'compression':'oxipng lossless -o3; no color quantization'}
    return rec

def main():
    groups=[]
    specs=[('story-world-walk','story-walk','story-walk-generation-04.png','actual/assets/original/graphics/map_units/personal_01.png',[32,24],[16,24]),
           ('tactical-walk','tactical-walk','tactical-walk-generation-03-shield.png','actual/source/characters/original-motion/original-walk-21.png',[32,24],[16,24])]
    for out_kind,native_kind,art_name,original_path,logical,anchor in specs:
        art_path=ROOT/'source'/art_name; art=Image.open(art_path);w,h=art.size;records=[]
        for i in range(6):
            x,y=i%2,i//2
            if out_kind=='tactical-walk' and i==1:
                mirror_path=ROOT/'source/tactical-walk-frame01-source-verified-mirror.png';mi=Image.open(mirror_path)
                rec=save_frame(out_kind,i,mirror_path,(0,0,mi.width,mi.height),ROOT/'reference'/f'{native_kind}-{i:02d}-native.png',[v*4 for v in logical])
                rec['derivation']='Horizontal mirror of new frame0; original native frames0 and1 tightly cropped are byte-identical under horizontal mirror. Registered to original frame1 foot offset.'
                records.append(rec)
            else:
                records.append(save_frame(out_kind,i,art_path,(x*w//2,y*h//3,(x+1)*w//2,(y+1)*h//3),ROOT/'reference'/f'{native_kind}-{i:02d}-native.png',[v*4 for v in logical]))
        groups.append((out_kind,original_path,logical,anchor,records))
    records=[]
    strip=ROOT/'source/tactical-idle-generation-04-shield.png'
    for i in range(3):
        p=strip;cell=(i*724,0,(i+1)*724,724);head_top=[161,159,158][i]
        if i==1:
            p=ROOT/'source/tactical-idle-pose1-generation-05-short-sword.png';im=Image.open(p);cell=(0,0,im.width,im.height);head_top=None
        records.append(save_frame('tactical-idle',i,p,cell,ROOT/'reference'/f'tactical-idle-{i:02d}-native.png',[96,96],head_top))
    for i,source in [(3,1),(4,0),(5,1)]:
        p=ROOT/'deliverables'/f'tactical-idle-{i:02d}.png';shutil.copy2(ROOT/records[source]['path'],p)
        record=dict(records[source]);record.update(source_index=i,output_index=i,path=str(p.relative_to(ROOT)),output_path=str(p.relative_to(ROOT)),repeat_of=source)
        records.append(record)
    groups.append(('tactical-idle','actual/assets/original/graphics/map_units/class_21_ally.png',[24,24],[12,20],records))
    scenarios=[]
    for kind,source,logical,anchor,records in groups:
        src=ROOT/'reference'/f'{kind}-source-atlas.png';shutil.copy2(PROJECT/source,src)
        atlas=ROOT/'deliverables'/f'{kind}.png'
        magick(*[ROOT/r['path'] for r in records],'+append',atlas)
        subprocess.run([OXIPNG,'-o','3','--strip','safe',str(atlas)],check=True,capture_output=True)
        idle=kind=='tactical-idle'
        for rec in records:
            rec['direction']='static-right-three-quarter' if idle else ['down','down','up','up','right','right'][rec['source_index']]
            rec['original_source_path']=source
        entry={'id':kind,'source_atlas':str(src.relative_to(ROOT)),'original_source_path':source,'source_frame_size':logical,
          'source_anchor':anchor,'output_atlas':str(atlas.relative_to(ROOT)),'output_frame_size':[v*4 for v in logical],
          'output_anchor':[v*4 for v in anchor],'logical_render_scale':0.25,'output_atlas_bytes':atlas.stat().st_size,
          'frame_mapping':records,'directions':{'all':[0,1,2,1]} if idle else {'down':[0,1],'up':[2,3],'right':[4,5],'left':[4,5]},
          'direction_mirror_x':{} if idle else {'left':True},'default_facing':'right','static_facing':idle,
          'timing':{'native_fps':FPS,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]} if idle else {'native_fps':FPS,'move_ticks_per_tile':16,'frame_ticks':16,'cycle_ticks':32,'phase':'continuous-clock','source_timing_evidence':['actual/core/story_hub.gd:315','actual/core/main.gd:592','actual/core/legacy_main.gd:1190'],'timing_status':'verified 16 ticks per leg frame; 16 movement ticks per tile, phase does not reset per tile'},
          'idle':{'kind':'original-fixed-facing-cycle','frames':[0,1,2,1]} if idle else {'kind':'hold-current-direction-first-frame','directions':{'down':[0],'up':[2],'right':[4],'left':[4]}},
          'adaptation_note':'Original small rectangular shield restored at matching hand position and occlusion; ivory metal rim, dark navy face, copper edge. No gameplay effect changed.' if kind.startswith('tactical') else 'Travel sword sheathed; exact town/world character identity shared.'}
        if kind=='story-world-walk':
            for name in ['story','world']:
                e=dict(entry);e['id']=name;e['shared_artifact']='story-world-walk';scenarios.append(e)
        else:scenarios.append(entry)
    payload={'schema_version':1,'actor_id':'hunapu','character_id':1,'class_id':21,'width_height_scale':4,
      'art_mode':'built-in image_gen; technical slicing/registration uses ImageMagick; lossless oxipng',
      'approved_identity_reference':'../../../hunapu-20261018-v1/deliverables/pose-000.png',
      'source_originals_unchanged':True,'runtime_integrated':False,'scenarios':scenarios}
    (ROOT/'frame_mapping.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'frames':sum(len(g[-1]) for g in groups),'scenarios':[s['id'] for s in scenarios],'mapping':str(ROOT/'frame_mapping.json')},ensure_ascii=False))

if __name__=='__main__':main()
