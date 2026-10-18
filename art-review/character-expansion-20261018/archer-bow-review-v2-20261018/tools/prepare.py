"""Technical registration and palette normalization of ImageGen outputs."""
from pathlib import Path
from PIL import Image
import subprocess,json
V=Path(__file__).resolve().parents[1];G='/opt/homebrew/bin/magick';C=V/'candidates';C.mkdir(exist_ok=True)
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def bbox(p):return Image.open(p).convert('RGBA').getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox()
palette=Image.new('RGB',(4,1));palette.putdata([(23,38,56),(57,118,181),(228,225,200),(221,167,125)]);palette.save(C/'palette.png')
def quantize(src,dst):
    run(src,'-alpha','extract','-threshold','50%',C/'alpha.png')
    run(src,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',C/'palette.png',C/'rgb.png')
    run(C/'rgb.png',C/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',dst)
def register(src,dst,canvas,targetheight,targetcenter,bottom):
    b=bbox(src);factor=targetheight/(b[3]-b[1]);run(src,'-filter','point','-resize',f'{factor*100}%',C/'small.png')
    b=bbox(C/'small.png');dx=round(targetcenter-(b[0]+b[2])/2);dy=bottom-b[3]
    run('-size',f'{canvas[0]}x{canvas[1]}','xc:none',C/'small.png','-geometry',f'{dx:+d}{dy:+d}','-compose','Over','-composite',C/'aligned.png');quantize(C/'aligned.png',dst)
    return {'scale':factor,'offset':[dx,dy],'bbox':bbox(dst)}
def main():
    raw=V/'source/foreground-bow-v1.png';w,h=Image.open(raw).size;report={}
    for n,name,size,center,bottom in [(0,'idle',(96,96),48,80),(1,'down',(128,96),68,96),(2,'right',(128,96),68,96)]:
        cell=C/f'{name}-raw.png';run(raw,'-crop',f'{w//3}x{h}+{n*w//3}+0','+repage',cell)
        report[name]=register(cell,C/f'{name}-full.png',size,64,center,bottom)
    (C/'registration.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in ['idle','down','right']:run(C/f'{name}-full.png','-filter','point','-resize','800%',C/f'{name}-8x.png')
    print(report)
if __name__=='__main__':main()
