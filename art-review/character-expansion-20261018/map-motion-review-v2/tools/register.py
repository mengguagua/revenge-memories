"""Technical export of ImageGen pixel artwork: crop, uniform scale and shared palette.

Never draws a character. Whole-pair scale is fixed; motion locking is a separate
explicit layer-compositing step. Raw generated alpha/source images are retained.
"""
from pathlib import Path
from PIL import Image
import json, subprocess, sys

V=Path(__file__).resolve().parents[1]
R=V.parent
G='/opt/homebrew/bin/magick'
manifest=json.loads((V/'input-manifest.json').read_text())

def run(*a):
    subprocess.run([G,*map(str,a)],check=True)

def bbox(im):
    return im.convert('RGBA').getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()

def export(key):
    story=key.endswith('-story')
    owner='hunapu' if story else key
    mp=R/manifest[owner]['mapping']
    mapping=json.loads((V/'reference'/f'{owner}-mapping-before.json').read_text())
    scenes={s['id']:s for s in mapping['scenarios']}
    records=scenes['story']['frame_mapping'] if story else scenes['tactical-walk']['frame_mapping']+scenes['tactical-idle']['frame_mapping'][:3]
    cols,rows=(3,2) if story else (4,3)
    selected=json.loads((V/'selected-sources.json').read_text()) if (V/'selected-sources.json').exists() else {}
    rawpath=V/selected.get(key,f'source/{key}-style.png')
    raw=Image.open(rawpath).convert('RGBA')
    # Generated sheets may place rows slightly off the mathematical thirds.
    # Split in real transparent gutters so a boot never leaks into the next row.
    a=raw.getchannel('A')
    occupied=[sum(v>=128 for v in a.crop((0,y,raw.width,y+1)).getdata())>4 for y in range(raw.height)]
    gaps=[];start=None
    for y,on in enumerate(occupied+[True]):
        if not on and start is None:start=y
        if on and start is not None:
            if y-start>10:gaps.append((start,y))
            start=None
    row_edges=[0]
    for j in range(1,rows):
        target=raw.height*j/rows
        choices=[g for g in gaps if raw.height*.12<sum(g)/2<raw.height*.92]
        gap=min(choices,key=lambda g:abs(sum(g)/2-target))
        row_edges.append(round(sum(gap)/2))
    row_edges.append(raw.height)
    out=V/'candidates'/key
    out.mkdir(parents=True,exist_ok=True)
    reg=[]
    scales={}
    for f,record in enumerate(records):
        base=f//2*2 if story or f<8 else 8
        x0=raw.width*(f%cols)//cols;y0=row_edges[f//cols]
        x1=raw.width*(f%cols+1)//cols;y1=row_edges[f//cols+1]
        cell=raw.crop((x0,y0,x1,y1));b=bbox(cell)
        oldpath=mp.parent/record.get('output_path',record.get('path'))
        old=Image.open(oldpath).convert('RGBA');ob=bbox(old)
        # Only base pose determines scale; the counterpart never breathes/scales.
        if f==base: scales[base]=(ob[3]-ob[1])/(b[3]-b[1])
        scale=scales[base]
        cut=out/f'raw-cell-{f:02}.png';small=out/f'small-{f:02}.png'
        run(rawpath,'-crop',f'{x1-x0}x{y1-y0}+{x0}+{y0}','+repage',cut)
        run(cut,'-filter','point','-resize',f'{scale*100:.10f}%',small)
        sm=Image.open(small).convert('RGBA');sb=bbox(sm)
        # Coarse placement for review; exact fixed layers are composed later.
        dx=round((ob[0]+ob[2]-sb[0]-sb[2])/2)
        dy=ob[3]-sb[3]
        dst=out/f'frame-raw-{f:02}.png'
        run('-size',f'{old.width}x{old.height}','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','over','-composite',dst)
        reg.append({'frame':f,'base':base,'cell':[x0,y0,x1,y1],'uniform_scale':scale,'translation':[dx,dy],'old_bbox':ob,'raw_bbox':b,'size':list(old.size)})
    # One palette for the entire character sheet, then identical remap for frames.
    # Binary alpha is an explicit pixel-art export spec; the raw alpha is untouched.
    run(*[out/f'frame-raw-{f:02}.png' for f in range(len(records))],'+append',out/'unquantized.png')
    if key in ['hunapu','hunapu-story']:
        palette=Image.new('RGBA',(4,1));palette.putdata([(23,38,56,255),(57,118,181,255),(228,225,200,255),(221,167,125,255)])
        palette.save(out/'palette.png')
    else:
        run(out/'unquantized.png','-channel','A','-threshold','50%','+channel','-dither','None','-colors','12',out/'palette.png')
    for f in range(len(records)):
        run(out/f'frame-raw-{f:02}.png','-alpha','extract','-threshold','50%',out/f'alpha-{f:02}.png')
        run(out/f'frame-raw-{f:02}.png','-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',out/'palette.png',out/f'rgb-{f:02}.png')
        run(out/f'rgb-{f:02}.png',out/f'alpha-{f:02}.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',out/f'frame-{f:02}.png')
    (out/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
    for c,label in [('#e3dfcf','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[out/f'frame-{f:02}.png'for f in range(len(records))],'-tile',f'{cols}x{rows}','-geometry','128x96+8+12','-background',c,out/f'contact-{label}.png')
        run(out/f'contact-{label}.png','-filter','point','-resize','300%',out/f'contact-{label}-3x.png')
    print(key,len(records),'registered for review')

if __name__=='__main__':
    for key in sys.argv[1:]: export(key)
