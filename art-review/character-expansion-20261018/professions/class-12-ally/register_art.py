"""ImageGen art registration and source comparison only; never edits actual/."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
B=R.parents[1]
MAGICK='/opt/homebrew/bin/magick'
OXIPNG='/opt/homebrew/bin/oxipng'
FONT=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',18)

def box(im):return im.getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox()
def foot_box(im,roi):
    b=box(im.crop(roi));return [b[0]+roi[0],b[1]+roi[1],b[2]+roi[0],b[3]+roi[1]]
def run(*args):subprocess.run([MAGICK,*map(str,args)],check=True)
def compress(p):subprocess.run([OXIPNG,'-o','3','--strip','safe',str(p)],check=True,capture_output=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def register(source,cell,head_top,feet_roi,output_size,target_head_y,target_foot,index,out_dir,scale_override=None):
    raw=Image.open(source).convert('RGBA').crop(cell);bb=box(raw);fb=foot_box(raw,feet_roi)
    scale=scale_override if scale_override is not None else (target_foot[1]-target_head_y)/(fb[3]-head_top)
    crop=[max(0,bb[0]-3),max(0,bb[1]-3),min(raw.width,bb[2]+3),min(raw.height,bb[3]+3)]
    width,height=crop[2]-crop[0],crop[3]-crop[1]
    crop_file=out_dir.parent/'source'/f'{out_dir.name}-crop-{index:03d}.png';resized=out_dir.parent/'source'/f'{out_dir.name}-resampled-{index:03d}.png'
    run(source,'-crop',f'{width}x{height}+{cell[0]+crop[0]}+{cell[1]+crop[1]}','+repage',crop_file)
    rw,rh=round(width*scale),round(height*scale)
    run(crop_file,'-filter','Lanczos','-resize',f'{rw}x{rh}!',resized)
    ri=Image.open(resized).convert('RGBA');resized_feet_roi=[max(0,round((feet_roi[0]-crop[0])*rw/width)),max(0,round((feet_roi[1]-crop[1])*rh/height)),min(rw,round((feet_roi[2]-crop[0])*rw/width)),min(rh,round((feet_roi[3]-crop[1])*rh/height))]
    rf=foot_box(ri,resized_feet_roi);x=round(target_foot[0]-(rf[0]+rf[2])/2);y=round(target_foot[1]-rf[3]);rb=box(ri)
    assert x+rb[0]>=0 and y+rb[1]>=0 and x+rb[2]<=output_size[0] and y+rb[3]<=output_size[1],(index,'visible art does not fit; revise artwork, never move body to clamp')
    out=out_dir/f'frame-{index:03d}.png'
    run('-size',f'{output_size[0]}x{output_size[1]}','xc:none',resized,'-geometry',f'{x:+d}{y:+d}','-compose','over','-composite',out);compress(out)
    fi=Image.open(out).convert('RGBA');final_roi=[max(0,resized_feet_roi[0]+x),max(0,resized_feet_roi[1]+y),min(output_size[0],resized_feet_roi[2]+x),min(output_size[1],resized_feet_roi[3]+y)]
    actual=foot_box(fi,final_roi);anchor=[(actual[0]+actual[2])/2,actual[3]]
    assert abs(anchor[0]-target_foot[0])<=.5 and abs(anchor[1]-target_foot[1])<=1,(index,anchor,target_foot)
    return {'source_frame':index,'representative_frame':index,'kind':'imagegen_from_native_pose','path':str(out.relative_to(out_dir.parent)),
      'generated_source':str(source.relative_to(out_dir.parent)),'generated_cell':list(cell),'generated_content_bounds':list(bb),'head_top':head_top,'generated_feet_roi':feet_roi,
      'generated_foot_bounds':fb,'uniform_scale':scale,'resampled_size':[rw,rh],'registration_offset':[x,y],
      'output_foot_roi':final_roi,'target_foot_anchor':target_foot,'registered_foot_anchor':anchor,
      'foot_delta':[anchor[0]-target_foot[0],anchor[1]-target_foot[1]],'visible_bounds':list(box(fi)),'size':list(fi.size),'bytes':out.stat().st_size,'sha256':sha(out)}

def battle():
    r=R/'battle';source=r/'source/batch-01-generated-v1.png';records=[]
    for col,(idx,headtop) in enumerate(zip([1,4,5],[166,168,168])):
        records.append(register(source,(col*724,0,(col+1)*724,724),headtop,[230,610,570,660],[320,256],128,[208,256],idx,r/'frames'))
    atlas=r/'frames/archer-battle-three.png';run(*[r/rec['path'] for rec in records],'+append',atlas);compress(atlas)
    native=B/'source-input/original-motion/class-12.png';n=Image.open(native).convert('RGBA')
    for background in ['dark','light']:
        bg='#1d2b35' if background=='dark' else '#e9e4d9';fg='#edf0e7' if background=='dark' else '#26333a'
        board=Image.new('RGBA',(1008,620),bg);draw=ImageDraw.Draw(board);draw.text((24,14),'盟军弓箭手 · 原作 / 新图 · 320×256，脚位相同',font=FONT,fill=fg)
        for col,idx in enumerate([1,4,5]):
            orig=n.crop((idx*80,0,(idx+1)*80,64)).resize((320,256),Image.Resampling.NEAREST)
            cur=Image.open(r/f'frames/frame-{idx:03d}.png').convert('RGBA');x=24+col*328
            board.alpha_composite(orig,(x,45));board.alpha_composite(cur,(x,329));draw.text((x+145,594),str(idx),font=FONT,fill=fg)
        board.convert('RGB').save(r/'reviews'/f'batch-01-original-vs-new-{background}.png',optimize=True)
    units=json.loads((B/'catalog/production-units.json').read_text())['units'];unit=next(u for u in units if u['id']=='class-12-ally')
    motion=json.loads((B/'source-input/original-motion/full-original-motion.json').read_text());keys=unit['bound_action_keys'];assert all(k in motion['variants'] for k in keys)
    data={'schema_version':1,'character_id':'ally-archer','display_name':'盟军弓箭手','original_class_id':12,'source_side':'ally',
      'status':'art_review_candidate','source_atlas':str(native.relative_to(B)),'source_atlas_base':'mapping directory',
      'source_frame_size':[80,64],'output_frame_size':[320,256],'source_anchor':[40,64],'output_anchor':[160,256],
      'source_frame_count':6,'source_columns':16,'frame_mapping':{str(rec['source_frame']):rec['path'] for rec in records},'records':records,
      'canonical_frames':[1,4,5],'variant_keys':keys,'output_atlas':'frames/archer-battle-three.png','output_atlas_frame_order':[1,4,5],
      'batches':[{'id':'batch-01','frames':[1,4,5],'status':'complete_review_candidate','review':'reviews/batch-01-original-vs-new-dark.png'}],
      'source_semantics':{'1':'upright empty bow / recovery','4':'full draw with one nocked arrow','5':'post-release empty bow'},
      'foot_anchor_registration':{'source_boot_roi':[45,60,59,64],'source_feet':[52,64],'target_feet':[208,256],'x_tolerance':.5,'y_tolerance':1,'no_body_clamp':True}}
    data['source_atlas']='../../../source-input/original-motion/class-12.png'
    (r/'frame_mapping.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'frames':[(x['source_frame'],x['registered_foot_anchor'],x['bytes']) for x in records],'atlas_bytes':atlas.stat().st_size},ensure_ascii=False))

def maps(only_idle=False):
    r=R/'maps';scenarios=[]
    if only_idle:
        scenarios=[s for s in json.loads((r/'frame_mapping.json').read_text())['scenarios'] if s['id']!='tactical-idle']
    configs=[{'kind':'tactical-walk','short':'walk','source_file':'walk-generated-v2.png','native':'../../../source-input/original-motion/original-walk-12.png','logical':[32,24],'anchor':[16,24],
      'original_indices':[0,1],'heads':[224,223],'feet_rois':[[350,770,570,840],[240,770,680,840]],'native_feet_rois':[[8,21,18,24],[11,20,24,24]],'target_head':32,'alias':[0,1,0,1,0,1]},
      {'kind':'tactical-idle','short':'idle','source_file':'idle-generated-v5.png','native':'../../../source-input/legacy-assets/assets/original/graphics/map_units/class_12_ally.png','logical':[24,24],'anchor':[12,20],
      'original_indices':[0,2],'heads':[119,167],'feet_rois':[[220,765,770,840],[220,765,780,840]],'native_feet_rois':[[4,17,20,20],[4,17,20,20]],'target_head':16,'alias':[0,0,2,0,0,0]}]
    for cfg in configs:
        if only_idle and cfg['short']!='idle':continue
        out_dir=r/f"{cfg['short']}-frames";out_dir.mkdir(exist_ok=True);native=(r/cfg['native']).resolve();ni=Image.open(native).convert('RGBA');fw,fh=cfg['logical'];records=[];by_index={}
        source=r/'source'/cfg['source_file'];si=Image.open(source);cw=si.width//2;ch=si.height
        for col,idx in enumerate(cfg['original_indices']):
            nf=ni.crop((idx*fw,0,(idx+1)*fw,fh));nfb=foot_box(nf,cfg['native_feet_rois'][col]);target=[(nfb[0]+nfb[2])*2,nfb[3]*4]
            fixed=records[0]['uniform_scale'] if cfg['short']=='idle' and records else None
            rec=register(source,(col*cw,0,(col+1)*cw,ch),cfg['heads'][col],cfg['feet_rois'][col],[fw*4,fh*4],cfg['target_head'],target,idx,out_dir,fixed)
            rec.update(source_index=idx,output_index=idx,output_path=rec['path'],native_feet_roi=cfg['native_feet_rois'][col],native_foot_bounds=nfb,source_visible_bounds=list(box(nf)),direction='northeast-ready' if cfg['short']=='idle' else 'right',scale_landmark='top-bow-tip' if cfg['short']=='idle' else 'hair-top')
            by_index[idx]=rec;records.append(rec)
        all_records=[]
        for slot,representative in enumerate(cfg['alias']):
            rec=dict(by_index[representative]);p=out_dir/f'frame-{slot:03d}.png'
            if slot!=representative:
                import shutil
                shutil.copy2(r/rec['path'],p)
            rec.update(source_index=slot,output_index=slot,source_frame=slot,representative_frame=representative,path=str(p.relative_to(r)),output_path=str(p.relative_to(r)),sha256=sha(p),bytes=p.stat().st_size)
            all_records.append(rec)
        atlas=r/'frames'/f"{cfg['kind']}.png";run(*[r/rec['path'] for rec in all_records],'+append',atlas);compress(atlas)
        idle=cfg['short']=='idle'
        entry={'id':cfg['kind'],'class_id':12,'source_side':'ally','character_id':'ally-archer','display_name':'盟军弓箭手','source_atlas':cfg['native'],
          'source_frame_size':cfg['logical'],'source_anchor':cfg['anchor'],'output_atlas':str(atlas.relative_to(r)),'output_frame_size':[fw*4,fh*4],
          'output_anchor':[v*4 for v in cfg['anchor']],'logical_render_scale':.25,'output_atlas_bytes':atlas.stat().st_size,'frame_mapping':all_records,
          'directions':{'all':[0,1,2,1]} if idle else {'down':[0,1],'up':[2,3],'right':[4,5],'left':[4,5]},'direction_mirror_x':{} if idle else {'left':True},
          'default_facing':'northeast-ready' if idle else 'right','static_facing':idle,'native_alias_groups':[[0,1,3,4,5],[2]] if idle else [[0,2,4],[1,3,5]],
          'timing':{'native_fps':60.0988,'cycle_frames':[0,1,2,1],'frame_ticks':[14,8,14,8]} if idle else {'native_fps':60.0988,'frame_ticks':16,'cycle_ticks':32,'move_ticks_per_tile':16,'phase':'continuous-clock'},
          'idle':{'kind':'original-fixed-facing-cycle','frames':[0,1,2,1]} if idle else {'kind':'hold-direction-slot-first-frame','directions':{'down':[0],'up':[2],'right':[4],'left':[4]}},
          'adaptation_note':'Same hatless sandy-brown-haired teal quilted-coat archer identity. Two distinct images with exact native slot aliases. '+('Crouched northeast drawn-bow ready pose, one nocked arrow and two taut string segments; no map projectile or attack event added.' if idle else 'Empty carried bow; no map shot animation invented.')}
        if not idle:
            explicit=[]
            for idx in [4,5]:
                p=r/all_records[idx]['path'];q=p.with_name(p.stem+'-left.png');run(p,'-flop',q);compress(q)
                explicit.append({'path':str(q.relative_to(r)),'source_index':idx,'derived_from':str(p.relative_to(r)),'transform':'horizontal-mirror-about-frame-center','size':[fw*4,fh*4],'bytes':q.stat().st_size})
            entry['explicit_left_frames']=explicit
        scenarios.append(entry)
        for background in ['dark','light']:
            bg='#1d2b35' if background=='dark' else '#e9e4d9';fg='#edf0e7' if background=='dark' else '#26333a'
            width=6*fw*4+48;height=fh*8+115;board=Image.new('RGBA',(width,height),bg);draw=ImageDraw.Draw(board)
            draw.text((20,14),f"盟军弓兵 {cfg['kind']} · 原作 / 新图 · 原六槽别名",font=FONT,fill=fg)
            for i in range(6):
                nf=ni.crop((i*fw,0,(i+1)*fw,fh)).resize((fw*4,fh*4),Image.Resampling.NEAREST);new=Image.open(r/all_records[i]['path']).convert('RGBA');x=24+i*fw*4
                board.alpha_composite(nf,(x,46));board.alpha_composite(new,(x,fh*4+68));draw.text((x+fw*2-5,fh*8+78),str(i),font=FONT,fill=fg)
            board.convert('RGB').save(r/'reviews'/f"{cfg['kind']}-{background}.png",optimize=True)
            frames=[];cycle=[0,1,2,1] if idle else [0,1];ticks=[14,8,14,8] if idle else [16,16]
            cumulative=[0]
            for tick in ticks:cumulative.append(cumulative[-1]+tick)
            boundaries=[round(t/60.0988*100)*10 for t in cumulative];dur=[b-a for a,b in zip(boundaries,boundaries[1:])]
            entry['preview_gif_timing']={'quantization_ms':10,'native_ticks':ticks,'durations_ms':dur,'exact_video_required':True}
            for idx in cycle:
                fr=Image.new('RGBA',(fw*8+100,fh*4+80),bg);dr=ImageDraw.Draw(fr);dr.text((18,12),cfg['kind']+' · 原节奏',font=FONT,fill=fg)
                nf=ni.crop((idx*fw,0,(idx+1)*fw,fh)).resize((fw*4,fh*4),Image.Resampling.NEAREST);new=Image.open(r/all_records[idx]['path']).convert('RGBA');fr.alpha_composite(nf,(30,52));fr.alpha_composite(new,(fw*4+70,52));frames.append(fr.convert('RGB'))
            gif=r/'reviews'/f"{cfg['kind']}-{background}.gif";frames[0].save(gif,save_all=True,append_images=frames[1:],duration=dur,loop=0,disposal=2,optimize=True);entry['preview_'+background]=str(gif.relative_to(r))
    data={'schema_version':1,'class_id':12,'source_side':'ally','actor_id':'ally-archer','character_id':'ally-archer','display_name':'盟军弓箭手',
      'width_height_scale':4,'runtime_integrated':False,'art_mode':'Built-in image_gen; ImageMagick crop/uniform registration; oxipng lossless','scenarios':scenarios}
    (r/'frame_mapping.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({s['id']:{'atlas_bytes':s['output_atlas_bytes'],'anchors':[(rec['source_index'],rec['registered_foot_anchor']) for rec in s['frame_mapping']]} for s in scenarios},ensure_ascii=False))

if __name__=='__main__':
    import sys
    maps(only_idle='--idle-only' in sys.argv) if '--maps' in sys.argv else battle()
