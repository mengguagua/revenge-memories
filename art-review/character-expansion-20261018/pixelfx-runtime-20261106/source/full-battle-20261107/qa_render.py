from pathlib import Path
from PIL import Image, ImageDraw
import json,math
import build_gallery as G

def case(key):
    s=(G.OUT/'cases'/f'{key}.js').read_text();return json.loads(s.split(']=',1)[1].rstrip(';\n'))

class Painter:
    def __init__(self,c):self.c=c;self.cache={};self.fx=json.loads((G.OUT/'assets/fx/manifest.json').read_text())['effects']
    def image(self,path):
        if path not in self.cache:self.cache[path]=Image.open(G.OUT/path).convert('RGBA')
        return self.cache[path]
    def layer(self,name,idx):
        c=self.c;tile=c.get('layerMap',{}).get(name,list(range(max(c['timeline'])+1)))[idx];spec=c.get('layerSpecs',{}).get(name,{'size':[592,240],'at':[0,0]});w,h=spec['size'];cell=tile%c['atlasFrames']
        im=self.image(c['atlases'][name][tile//c['atlasFrames']]);x=cell%c['atlasCols']*w;y=cell//c['atlasCols']*h;return im.crop((x,y,x+w,y+h)),spec['at']
    def draw_layer(self,canvas,name,idx):
        im,at=self.layer(name,idx);canvas.alpha_composite(im,tuple(at))
    def fx_layer(self,name,elapsed,point,flip=False,alpha=1):
        s=self.fx[name];f=math.floor(elapsed*s['fps']+1e-6)
        if f<0 or (not s['loop'] and f>=s['frames']) or point is None:return None
        f%=s['frames'];w,h=s['frameSize'];px,py=s['pivot'];x=f%s['columns']*w;y=f//s['columns']*h
        im=self.image(s['path']).crop((x,y,x+w,y+h))
        if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);px=w-px
        if alpha<1:im.putalpha(im.getchannel('A').point(lambda v:round(v*alpha)))
        return im,(round(point[0])-px,round(point[1])-py)
    def render(self,time):
        c=self.c;n=min(len(c['timeline'])-1,max(0,math.floor(time*60+1e-6)));idx=c['timeline'][n];before=Image.new('RGBA',(592,240))
        if 'plate' in c['atlases']:self.draw_layer(before,'plate',idx)
        self.draw_layer(before,'current',idx);after=before.copy();fx=Image.new('RGBA',(592,240))
        if c.get('suppressFlash'):self.draw_layer(after,'clean',idx)
        if c.get('projectile'):
            p=c['projectile'];at=p['anchors'][n]
            if at:
                if p['kind']=='arrow':self.draw_layer(after,'clean',idx)
                item=self.fx_layer(p['kind'],time-p['start'],at,p['flip'],.6 if p['kind']=='wake' else 1)
                if item:fx.alpha_composite(item[0],item[1])
        for p in c['fxPlan']:
            item=self.fx_layer(p['effect'],time-p['start'],p['track'][n] if 'track' in p else p['anchor'],p.get('flip',False),p.get('alpha',1))
            if item:fx.alpha_composite(item[0],item[1])
        if c.get('cinemaEffect') and time>=c['contact']:
            if c.get('cinemaReplacement'):self.draw_layer(after,'clean',idx)
            pt=c['cinemaTargets'][n]
            item=self.fx_layer(c['cinemaEffect'],time-c['contact'],[pt[0],pt[1]-4] if pt else None,False,.94)
            if item:fx.alpha_composite(item[0],item[1])
        x,y,w,h=c['field'];after.alpha_composite(fx.crop((x,y,x+w,y+h)),(x,y))
        return before,after

def contact_sheet(keys,outname,times=(.08,.28)):
    output=Image.new('RGB',(1100,len(keys)*550),'#17252e');draw=ImageDraw.Draw(output)
    for row,key in enumerate(keys):
        c=case(key);p=Painter(c);draw.text((12,row*550+8),key,fill='#e4eadd')
        for col,dt in enumerate(times):
            a,b=p.render(c['contact']+dt);x,y,w,h=c['crop'];h=128 if c['family'] not in ['cinema','map'] else 240
            scale=1 if w>300 else 2
            for side,im in enumerate([a,b]):
                tile=im.crop((x,y,x+w,y+h)).resize((w*scale,h*scale),Image.Resampling.NEAREST)
                # For ordinary closeups each row shows a direct A/B pair at one beat.
                if len(times)==1:output.paste(tile,(20+side*540,row*550+36))
                elif side==1:output.paste(tile,(20+col*540,row*550+36))
    output.save(G.OUT/'qa'/outname)

if __name__=='__main__':
    available={p.stem for p in (G.OUT/'cases').glob('*.js')}
    keys=['cinema-hunapu-sword','cinema-eileen-fire-advanced','map-eileen-advanced','map-heal-18','map-hunapu-bow']
    contact_sheet([k for k in keys if k in available],'special-ab.png',(.12,))
    print(G.OUT/'qa/special-ab.png')
