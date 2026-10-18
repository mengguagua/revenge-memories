"""Register ImageGen patches to the already reviewed fixed body, using hair landmarks."""
from pathlib import Path
from PIL import Image
import subprocess,json
V=Path(__file__).resolve().parents[1];R=V.parent;P=R/'archer-bow-review-v2-20261018';C=V/'candidates';G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def rgba(p):return Image.open(p).convert('RGBA')
def bbox(p):return rgba(p).getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
palette=Image.new('RGB',(4,1));palette.putdata([(23,38,56),(57,118,181),(228,225,200),(221,167,125)]);palette.save(C/'palette.png')
def quantize(src,dst,palette=C/'palette.png'):
    run(src,'-alpha','extract','-threshold','50%',C/'alpha.png')
    run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',palette,C/'rgb.png')
    run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def blue_hair(p):
    a=rgba(p);b=a.getbbox();limit=b[1]+(b[3]-b[1])*.65
    pts={(x,y)for y in range(a.height)for x in range(a.width)if y<limit and a.getpixel((x,y))==(57,118,181,255)};groups=[]
    while pts:
        q=[pts.pop()];g=[]
        while q:
            x,y=q.pop();g.append((x,y))
            for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if n in pts:pts.remove(n);q.append(n)
        groups.append(g)
    primary=max(groups,key=len);top=min(y for x,y in primary);bottom=max(y for x,y in primary)+1
    # Union the substantial hair pieces separated by the foreground string;
    # discard tiny blue fringe noise on the weapon and lower clothing pieces.
    g=[p for group in groups if len(group)>=len(primary)*.1 and min(y for x,y in group)<top+(bottom-top)*.6 for p in group]
    return(min(x for x,y in g),min(y for x,y in g),max(x for x,y in g)+1,max(y for x,y in g)+1)
def main():
    raw=V/'source/arms-neutral-final.png';w,h=Image.open(raw).size;report={}
    for n,name in enumerate(['idle','down','right']):
        target=P/('layers/idle-body.png'if name=='idle'else f'candidates/{name}-body-a.png');size=Image.open(target).size
        cell=C/f'{name}-raw.png';run(raw,'-crop',f'{w//3}x{h}+{n*w//3}+0','+repage',cell);quantize(cell,C/'colored.png')
        old=blue_hair(target);new=blue_hair(C/'colored.png');factor=(old[2]-old[0])/(new[2]-new[0])
        run(cell,'-filter','point','-resize',f'{factor*100}%',C/'small.png');quantize(C/'small.png',C/'colored-small.png');b=blue_hair(C/'colored-small.png')
        dx=round((old[0]+old[2]-b[0]-b[2])/2);dy=old[1]-b[1]
        dst=C/f'{name}-aligned.png';run('-size',f'{size[0]}x{size[1]}','xc:none',C/'colored-small.png','-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',dst)
        run(dst,'-filter','point','-resize','800%',C/f'{name}-8x.png')
        report[name]={'scale':factor,'offset':[dx,dy],'hair_before':old,'hair_after':blue_hair(dst),'bounds':bbox(dst)}
    (C/'registration.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
