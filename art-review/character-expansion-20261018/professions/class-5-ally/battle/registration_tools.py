"""ImageGen art registration and source comparison only; never edits actual/."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess,hashlib
R=Path(__file__).resolve().parent
B=R.parents[2]
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

