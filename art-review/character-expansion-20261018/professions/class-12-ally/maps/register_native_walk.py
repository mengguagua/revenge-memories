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

def main():
    outdir=R/'tactical-native-frames';outdir.mkdir(exist_ok=True)
    ni=Image.open(B/'source-input/corrected-tactical-walk/class-12-ally.png').convert('RGBA')
    meta=json.loads((B/'source-input/corrected-tactical-walk/overlay.json').read_text())['records']['class-12-ally'];records=[]
    configs=[(0,'up',1,0,116,780,[13,23,16,24]),(1,'up',1,1,116,790,[16,23,19,24]),(4,'down',1,0,121,780,[16,23,20,24]),(5,'down',1,1,121,780,[13,23,19,24]),(6,'left',2,0,130,765,[9,23,14,24]),(7,'left',2,1,132,765,[8,23,12,24])]
    for idx,direction,v,col,head,foot_y,nroi in configs:
        source=R/f'source/native-{direction}-generated-v{v}.png';si=Image.open(source);w,h=si.size;cell=[col*w//2,0,(col+1)*w//2,h];roi=[0,foot_y,cell[2]-cell[0],h];nf=ni.crop((idx*32,0,(idx+1)*32,24));fb=foot_box(nf,nroi);target=[(fb[0]+fb[2])*2,fb[3]*4]
        rec=register(source,cell,head,roi,[128,96],32,target,idx,outdir)
        rec.update(source_index=idx,output_index=idx,output_path=rec['path'],direction=direction,native_feet_roi=nroi,native_foot_bounds=fb,native_cpu_frame=meta['frame_mapping'][idx],source_visible_bounds=list(box(nf)),registration_scope='Selected support boot sole center/baseline only; numerical error is not a claim that every joint or limb matches exactly.')
        records.append(rec)
    lookup={r['source_index']:r for r in records}
    for idx,rep in [(2,6),(3,7)]:
        a=ni.crop((idx*32,0,(idx+1)*32,24));b=ni.crop((rep*32,0,(rep+1)*32,24)).transpose(Image.Transpose.FLIP_LEFT_RIGHT);assert a.size==b.size and a.tobytes()==b.tobytes()
        base=lookup[rep];im=Image.open(R/base['path']).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);out=outdir/f'frame-{idx:03}.png';im.save(out,optimize=True);compress(out);roi=base['output_foot_roi'];nroi=base['native_feet_roi'];rec={**base,'source_index':idx,'source_frame':idx,'output_index':idx,'representative_frame':rep,'kind':'native_proven_full_canvas_mirror','path':str(out.relative_to(R)),'output_path':str(out.relative_to(R)),'direction':'right','output_foot_roi':[128-roi[2],roi[1],128-roi[0],roi[3]],'native_feet_roi':[32-nroi[2],nroi[1],32-nroi[0],nroi[3]],'target_foot_anchor':[128-base['target_foot_anchor'][0],base['target_foot_anchor'][1]],'registered_foot_anchor':[128-base['registered_foot_anchor'][0],base['registered_foot_anchor'][1]],'foot_delta':[-base['foot_delta'][0],base['foot_delta'][1]],'visible_bounds':list(box(im)),'bytes':out.stat().st_size,'sha256':sha(out),'native_cpu_frame':meta['frame_mapping'][idx],'mirror_after_registration':True};records.append(rec)
    records.sort(key=lambda x:x['source_index']);(R/'source/native-walk-registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    for direction,ids in meta['directions'].items():
        for theme,bg,fg in [('light','#e9e4d9','#26333a'),('dark','#1d2b35','#edf0e7')]:
            board=Image.new('RGBA',(552,500),bg);dr=ImageDraw.Draw(board);dr.text((16,10),'盟弓兵真实战术 '+direction+' · 原CPU / 新图',font=FONT,fill=fg)
            for col,idx in enumerate(ids):
                x=16+col*268;board.alpha_composite(ni.crop((idx*32,0,(idx+1)*32,24)).resize((256,192),Image.Resampling.NEAREST),(x,42));board.alpha_composite(Image.open(R/records[idx]['path']).convert('RGBA').resize((256,192),Image.Resampling.NEAREST),(x,264));dr.text((x+112,470),str(idx),font=FONT,fill=fg)
            board.convert('RGB').save(R/f'reviews/tactical-native-{direction}-{theme}.png',optimize=True)
    print([(x['source_index'],x['target_foot_anchor'],x['registered_foot_anchor'],x['visible_bounds'],x['bytes'])for x in records])

if __name__=='__main__':main()
