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
def foot_box(im,roi,hoof=False):
    region=im.crop(roi)
    if hoof:
        mask=Image.new('L',region.size);mask.putdata([255 if a>=32 and max(red,green,blue)<105 and max(red,green,blue)-min(red,green,blue)<45 else 0 for red,green,blue,a in region.getdata()]);b=mask.getbbox()
    else:b=box(region)
    assert b is not None,('empty hoof ROI',roi)
    return [b[0]+roi[0],b[1]+roi[1],b[2]+roi[0],b[3]+roi[1]]
def run(*args):subprocess.run([MAGICK,*map(str,args)],check=True)
def compress(p):subprocess.run([OXIPNG,'-o','3','--strip','safe',str(p)],check=True,capture_output=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def register(source,cell,head_top,feet_roi,output_size,target_head_y,target_foot,index,out_dir,scale_override=None):
    raw=Image.open(source).convert('RGBA').crop(cell);bb=box(raw);fb=foot_box(raw,feet_roi,True)
    scale=scale_override if scale_override is not None else (target_foot[1]-target_head_y)/(fb[3]-head_top)
    crop=[max(0,bb[0]-3),max(0,bb[1]-3),min(raw.width,bb[2]+3),min(raw.height,bb[3]+3)]
    width,height=crop[2]-crop[0],crop[3]-crop[1]
    crop_file=out_dir.parent/'source'/f'{out_dir.name}-crop-{index:03d}.png';resized=out_dir.parent/'source'/f'{out_dir.name}-resampled-{index:03d}.png'
    run(source,'-crop',f'{width}x{height}+{cell[0]+crop[0]}+{cell[1]+crop[1]}','+repage',crop_file)
    rw,rh=round(width*scale),round(height*scale)
    run(crop_file,'-filter','Lanczos','-resize',f'{rw}x{rh}!',resized)
    ri=Image.open(resized).convert('RGBA');resized_feet_roi=[max(0,round((feet_roi[0]-crop[0])*rw/width)),max(0,round((feet_roi[1]-crop[1])*rh/height)),min(rw,round((feet_roi[2]-crop[0])*rw/width)),min(rh,round((feet_roi[3]-crop[1])*rh/height))]
    rf=foot_box(ri,resized_feet_roi,True);x=round(target_foot[0]-(rf[0]+rf[2])/2);y=round(target_foot[1]-rf[3]);rb=box(ri)
    assert x+rb[0]>=0 and y+rb[1]>=0 and x+rb[2]<=output_size[0] and y+rb[3]<=output_size[1],(index,'visible art does not fit; revise artwork, never move body to clamp')
    out=out_dir/f'frame-{index:03d}.png'
    run('-size',f'{output_size[0]}x{output_size[1]}','xc:none',resized,'-geometry',f'{x:+d}{y:+d}','-compose','over','-composite',out);compress(out)
    fi=Image.open(out).convert('RGBA');final_roi=[max(0,resized_feet_roi[0]+x),max(0,resized_feet_roi[1]+y),min(output_size[0],resized_feet_roi[2]+x),min(output_size[1],resized_feet_roi[3]+y)]
    actual=foot_box(fi,final_roi,True);anchor=[(actual[0]+actual[2])/2,actual[3]]
    assert abs(anchor[0]-target_foot[0])<=.5 and abs(anchor[1]-target_foot[1])<=1,(index,anchor,target_foot)
    return {'source_frame':index,'representative_frame':index,'kind':'imagegen_from_native_pose','path':str(out.relative_to(out_dir.parent)),
      'generated_source':str(source.relative_to(out_dir.parent)),'generated_cell':list(cell),'generated_content_bounds':list(bb),'head_top':head_top,'generated_feet_roi':feet_roi,
      'generated_foot_bounds':fb,'uniform_scale':scale,'resampled_size':[rw,rh],'registration_offset':[x,y],
      'output_foot_roi':final_roi,'target_foot_anchor':target_foot,'registered_foot_anchor':anchor,
      'foot_delta':[anchor[0]-target_foot[0],anchor[1]-target_foot[1]],'visible_bounds':list(box(fi)),'size':list(fi.size),'bytes':out.stat().st_size,'sha256':sha(out)}

def battle():
    r=R/'battle';native=B/'source-input/original-motion/class-3.png';ni=Image.open(native).convert('RGBA');records=[]
    configs=[(0,4,616,[430,1260,530,1335],[43,70,47,72],128),(3,2,470,[410,970,490,1010],[41,61,47,64],144),(7,3,618,[430,1260,540,1340],[43,70,47,72],128)]
    for idx,version,head,roi,nroi,target_head in configs:
        source=r/f'source/pose-{idx:03d}-generated-v{version}.png';si=Image.open(source);nf=ni.crop(((idx%16)*80,(idx//16)*96,(idx%16+1)*80,(idx//16+1)*96));fb=foot_box(nf,nroi);target=[(fb[0]+fb[2])*2,fb[3]*4]
        rec=register(source,(0,0,*si.size),head,roi,[320,384],target_head,target,idx,r/'frames');rec.update(native_hoof_roi=nroi,native_hoof_bounds=fb,hoof_measurement='Semantically chosen dark neutral hoof-cap mask inside explicit ROI; mask only measures registration, never colors/draws art. Wings excluded.',source_visible_bounds=list(box(nf)));records.append(rec)
    for bgname,bg,fg in [('dark','#1d2b35','#edf0e7'),('light','#e9e4d9','#26333a')]:
        board=Image.new('RGBA',(1008,880),bg);dr=ImageDraw.Draw(board);dr.text((24,14),'盟军天马骑士 · 原作 / 新图 · 320×384',font=FONT,fill=fg)
        for col,rec in enumerate(records):
            idx=rec['source_frame'];x=24+col*328;nf=ni.crop(((idx%16)*80,(idx//16)*96,(idx%16+1)*80,(idx//16+1)*96)).resize((320,384),Image.Resampling.NEAREST);board.alpha_composite(nf,(x,42));board.alpha_composite(Image.open(r/rec['path']).convert('RGBA'),(x,451));dr.text((x+145,849),str(idx),font=FONT,fill=fg)
        board.convert('RGB').save(r/'reviews'/f'keyposes-original-vs-new-{bgname}.png',optimize=True)
    unit=next(u for u in json.loads((B/'catalog/production-units.json').read_text())['units'] if u['id']=='class-3-ally')
    data={'schema_version':1,'character_id':'ally-pegasus-rider','display_name':'盟军天马骑士','original_class_id':3,'source_side':'ally','status':'keyposes_review_candidate','variant_keys':unit['bound_action_keys'],
      'source_atlas':'../../../source-input/original-motion/class-3.png','source_motion':'../../../source-input/original-motion/full-original-motion.json','source_frame_size':[80,96],'output_frame_size':[320,384],'source_anchor':[40,72],'output_anchor':[160,288],
      'source_oam_frame_count':16,'canonical_frames':unit['unique_art_frames'],'required_source_frames':unit['required_source_frames'],'source_aliases':{'16':0,'33':0},'frame_mapping':{str(rec['source_frame']):rec['path']for rec in records},'records':records,
      'batches':[{'id':'keyposes','frames':[0,3,7],'review':'reviews/keyposes-original-vs-new-dark.png'}],'runtime_integrated':False,'art_mode':'Built-in ImageGen. Technical crop/uniform scale/rigid registration only; no programmatic art drawing.'}
    (r/'frame_mapping.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps([(x['source_frame'],x['registered_foot_anchor'],x['target_foot_anchor'],x['visible_bounds'],x['bytes'])for x in records]))

if __name__=='__main__':battle()

