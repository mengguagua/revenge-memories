"""Register generated artwork to the original source canvas and four-color palette."""
from pathlib import Path
from PIL import Image
import json,subprocess,sys
V=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def box(im):return im.convert('RGBA').getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
def register(key):
    rawpath=V/f'source/{key}-generated.png';raw=Image.open(rawpath).convert('RGBA')
    o=V/'candidates'/key;o.mkdir(parents=True,exist_ok=True)
    # Find transparent row gutters; no proportional thirds that cut off feet.
    alpha=raw.getchannel('A');occupied=[sum(v>=128 for v in alpha.crop((0,y,raw.width,y+1)).getdata())>4 for y in range(raw.height)]
    gaps=[];start=None
    for y,on in enumerate(occupied+[True]):
        if not on and start is None:start=y
        if on and start is not None:
            if y-start>12:gaps.append((start,y))
            start=None
    inner=[g for g in gaps if raw.height*.15<sum(g)/2<raw.height*.85]
    edges=[0]+[round(sum(min(inner,key=lambda g:abs(sum(g)/2-raw.height*i/3)))/2)for i in [1,2]]+[raw.height]
    assert edges==sorted(set(edges)),edges
    team=(174,81,72,255) if key.endswith('enemy') else (57,118,181,255)
    palette=Image.new('RGBA',(4,1));palette.putdata([(23,38,56,255),team,(228,225,200,255),(221,167,125,255)]);palette.save(o/'palette.png')
    scales={};records=[]
    for slot in range(9):
        context='tactical-walk' if slot<6 else 'tactical-idle';native_slot=slot if slot<6 else slot-6
        native=Image.open(V/f'reference/{key}-{context}-{native_slot:02}.png').convert('RGBA');nb=box(native)
        target_box=[n*4 for n in nb];target_size=[n*4 for n in native.size]
        c=slot%3;r=slot//3;x0=raw.width*c//3;x1=raw.width*(c+1)//3;y0=edges[r];y1=edges[r+1]
        cell=raw.crop((x0,y0,x1,y1));b=box(cell);group=(slot//2)*2 if slot<6 else 6
        if slot==group:scales[group]=(target_box[3]-target_box[1])/(b[3]-b[1])
        factor=scales[group];cut=o/f'raw-{slot:02}.png';small=o/f'small-{slot:02}.png'
        run(rawpath,'-crop',f'{x1-x0}x{y1-y0}+{x0}+{y0}','+repage',cut)
        run(cut,'-filter','point','-resize',f'{factor*100:.10f}%',small)
        sb=box(Image.open(small));dx=round((target_box[0]+target_box[2]-sb[0]-sb[2])/2);dy=target_box[3]-sb[3]
        rawframe=o/f'unquantized-{slot:02}.png'
        run('-size',f'{target_size[0]}x{target_size[1]}','xc:none',small,'-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',rawframe)
        run(rawframe,'-alpha','extract','-threshold','50%',o/f'alpha-{slot:02}.png')
        run(rawframe,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',o/'palette.png',o/f'rgb-{slot:02}.png')
        run(o/f'rgb-{slot:02}.png',o/f'alpha-{slot:02}.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',o/f'frame-{slot:02}.png')
        records.append({'slot':slot,'context':context,'native_slot':native_slot,'raw_cell':[x0,y0,x1,y1],'uniform_group_scale':factor,'translation':[dx,dy],'native_box':nb,'new_box':box(Image.open(o/f'frame-{slot:02}.png'))})
    (o/'registration.json').write_text(json.dumps(records,indent=2)+'\n')
    for color,name in [('#d9d6c9','light'),('#26343b','dark')]:
        run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[o/f'frame-{i:02}.png'for i in range(9)],'-tile','3x3','-geometry','128x96+8+8','-background',color,o/f'contact-{name}.png')
        run(o/f'contact-{name}.png','-filter','point','-resize','400%',o/f'contact-{name}-4x.png')
    print(key,{'scales':scales,'row_edges':edges})
if __name__=='__main__':
    for key in sys.argv[1:]:register(key)
