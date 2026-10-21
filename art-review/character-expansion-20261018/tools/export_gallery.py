#!/usr/bin/env python3
"""Offline compositing/export of source and approved/candidate frames, not art generation."""
from pathlib import Path
from functools import lru_cache
import argparse, json, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from build_gallery import ROOT, build

@lru_cache(maxsize=1024)
def load(path):
    return Image.open(ROOT / path).convert('RGBA')

@lru_cache(maxsize=2048)
def body_image(atlas, frame, frame_size, columns):
    w,h=frame_size;x=(frame%columns)*w;y=(frame//columns)*h
    return load(atlas).crop((x,y,x+w,y+h))

def font(size):
    for path in ['/System/Library/Fonts/PingFang.ttc','/System/Library/Fonts/STHeiti Light.ttc']:
        if Path(path).exists(): return ImageFont.truetype(path,size)
    return ImageFont.load_default()

def paste_at(canvas, image, point, size, scale, viewport, flip=False, alpha=1, tint=1):
    if flip: image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if tint != 1:
        transparency=image.getchannel('A');image=ImageEnhance.Brightness(image).enhance(tint);image.putalpha(transparency)
    if alpha != 1:
        image=image.copy();image.putalpha(image.getchannel('A').point(lambda v:round(v*alpha)))
    image=image.resize((round(size[0]*scale),round(size[1]*scale)),Image.Resampling.NEAREST)
    xy=(round((point[0]-viewport[0])*scale),round((point[1]-viewport[1])*scale))
    canvas.alpha_composite(image,xy)

def render_panel(data,profile,action,row,revised,scale=4,light=False,close=False):
    viewport=action.get('viewport',data['viewport'])
    if close and action['context']=='battle':
        camera=action['closeCamera'];offset=row.get('offset',[0,0])
        viewport=[action['origin'][i]+offset[i]+camera['offset'][i]for i in range(2)]+camera['size']
    bg=(220,222,216,255)if light else(32,45,53,255)
    canvas=Image.new('RGBA',(round(viewport[2]*scale),round(viewport[3]*scale)),bg)
    if profile.get('mapGround') and not light:
        ground=load(profile['mapGround'])
        canvas.alpha_composite(ground.resize(canvas.size,Image.Resampling.NEAREST))
    offset=row.get('offset',[0,0]);f=row['frame'];flip=(profile['context']=='battle'and profile.get('side')=='enemy') != row.get('flip',False)
    at=[action['origin'][0]+offset[0]-profile['anchor'][0]+row.get('shake',0),action['origin'][1]+offset[1]-profile['anchor'][1]]
    if flip and f<profile['sourceOamCutoff']:
        at=[at[i]+profile['flipOriginOffset'][i]for i in range(2)]
    if revised and profile.get('mapShadow'):
        shadow=profile['mapShadow'];size=shadow['size'];delta=shadow.get('offset',[0,0])
        point=[action['origin'][0]+offset[0]+delta[0]-size[0]/2,action['origin'][1]+offset[1]+delta[1]-size[1]/2]
        paste_at(canvas,load(shadow['path']),point,size,scale,viewport,False,shadow.get('alpha',1))
    if revised:
        if str(f)not in profile['newFrames']:raise ValueError(f'Missing redraw {f}; no fallback is permitted')
        image=load(profile['newFrames'][str(f)])
    else:image=body_image(profile['sourceAtlas'],f,tuple(profile['sourceFrameSize']),profile['sourceColumns'])
    paste_at(canvas,image,at,profile['sourceFrameSize'],scale,viewport,flip,row.get('alpha',1),row.get('tint',1))
    for effect in row.get('effects',[]):
        meta=profile.get('revisedEffects',{}).get(effect['sprite'],data['effects'][effect['sprite']])if revised else data['effects'][effect['sprite']]
        at=[effect['position'][i]-meta['anchor'][i]for i in range(2)]
        if effect.get('flip'):at=[at[i]+meta.get('flip_origin_offset',[0,0])[i]for i in range(2)]
        paste_at(canvas,load(meta['path']),at,meta['frame_size'],scale,viewport,effect.get('flip',False))
    return canvas

def playback_count(action):
    return len(action['frames'])+len(action.get('reviewTailFrames',[]))

def render_frame(data,profile,action,tick,scale=4,light=False,close=False):
    row=action['frames'][min(tick,len(action['frames'])-1)]
    revised_row=action.get('revisedFrames',action['frames'])[tick]if tick<len(action['frames'])else action['reviewTailFrames'][tick-len(action['frames'])]
    left=render_panel(data,profile,action,row,False,scale,light,close);right=render_panel(data,profile,action,revised_row,True,scale,light,close)
    margin=24;gap=24;top=76;bottom=60;w=left.width*2+margin*2+gap;h=left.height+top+bottom
    canvas=Image.new('RGB',(w+(w%2),h+(h%2)),(14,21,26));draw=ImageDraw.Draw(canvas)
    heading=profile['actorName']+' · '+action['name']
    if profile.get('revision') in ['knight-walk-paired-legs-v5-20261021','knight-idle-paired-legs-v4-20261021','knight-redraw-v3-20261021','knight-map-joints-v2-20261021','knight-complete-v1-20261021','cavalry-battle-lance-colors-v1-20261021','enemy-cavalry-map-blue-violet-v1-20261021','cavalry-map-white-v2-20261021','cavalry-map-anchor-palette-v1-20261021','mage-battle-round-hat-v1-20261021','mage-map-motion-v3-20261021','mage-robe-idle-warm-v2-20261021','mage-robe-idle-v1-20261021','curse-mage-battle-v1-20261020','curse-mage-cross-step-v5-20261020','curse-mage-low-arm-v4-20261020','curse-mage-sleeve-inset-v3-20261020','curse-mage-map-v2-20261020','curse-mage-idle-v1-20261020','gold-knight-idle-style-v6-20261020','gold-knight-side-anchor-v5-20261020','gold-knight-down-v4-20261020','gold-knight-walk-v3-20261020','gold-knight-idle-v2-20261020','mercenary-pixel-grid-v3-20261019','archer-battle-scale-v4-20261019','mercenary-enemy-deep-blue-v2-20261019','mercenary-battle-simple-v1-20261019','spearman-enemy-blue-violet-v2-20261019','spearman-battle-width-palette-20261019','archer-battle-light-armor-v3-20261019','archer-battle-simple-v2-20261019','archer-battle-width-palette-20261019','mercenary-left-neck-v3-20261019','mercenary-eyes-v2-20261019','mercenary-map-review-20261019','body-volume-motion-20261018','sol','archer-spearman-map-20261018','archer-bow-v2-20261018','archer-arms-step-v3-20261018','archer-down-hand-v4-20261018','spearman-map-v2-20261018','spearman-stance-v3-20261018']:
        heading_font=next((font(n)for n in range(22,13,-1)if draw.textbbox((0,0),heading,font=font(n))[2]<=canvas.width-2*margin),font(14))
        hb=draw.textbbox((0,0),heading,font=heading_font)
        if hb[2]-hb[0]>canvas.width-2*margin:raise ValueError('Title exceeds measured text safe area')
        draw.text(((canvas.width-(hb[2]-hb[0]))/2-hb[0],14),heading,font=heading_font,fill=(235,243,242))
        for origin,label,color in[(margin,action.get('referenceLabel','原作'),(160,178,189)),(margin+left.width+gap,'四倍像素重绘',(168,214,200))]:
            lb=draw.textbbox((0,0),label,font=font(15));draw.text((origin+(left.width-(lb[2]-lb[0]))/2-lb[0],48),label,font=font(15),fill=color)
    else:
        draw.text((margin,14),heading,font=font(22),fill=(235,243,242))
        draw.text((margin,48),action.get('referenceLabel','原作'),font=font(15),fill=(160,178,189));draw.text((margin+left.width+gap,48),'四倍像素重绘',font=font(15),fill=(168,214,200))
    canvas.paste(left.convert('RGB'),(margin,top));canvas.paste(right.convert('RGB'),(margin+left.width+gap,top))
    ending='  ·  原作结束，新稿'+action.get('reviewTailLabel','光点收尾')if tick>=len(action['frames'])else''
    label=f'第 {tick+1} / {playback_count(action)} 帧  ·  源姿势 {row["frame"]}  ·  {tick/action["fps"]:.3f} 秒'+ending
    draw.text((margin,top+left.height+16),label,font=font(15),fill=(160,178,189))
    return canvas

def export(data,action,args):
    profile=next(p for p in data['profiles']if p['id']==action['profile'])
    if not action['ready']:raise ValueError('Refusing incomplete action: '+action['id'])
    out=ROOT/'demos';(out/'videos').mkdir(parents=True,exist_ok=True);(out/'stills').mkdir(parents=True,exist_ok=True)
    suffix='--close'if args.close else''
    snapshot={'contentDigest':action['contentDigest'],'scale':args.scale,'light':args.light,'close':args.close,'action':action['id']}
    previous=(out/'stills'if args.stills_only else out/'videos')/(action['id']+suffix+('.png'if args.stills_only else'.mp4'))
    if previous.exists()and previous.with_suffix('.json').exists()and json.loads(previous.with_suffix('.json').read_text())==snapshot:
        return {'action':action['id'],'skipped_unchanged':True,'path':str(previous.relative_to(ROOT))}
    contact=action['contactTick'];still_tick=contact if contact is not None else min(8,len(action['frames'])-1)
    still=render_frame(data,profile,action,still_tick,args.scale,args.light,args.close)
    still_path=out/'stills'/(action['id']+suffix+'.png');still.save(still_path,optimize=True)
    still_path.with_suffix('.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    if args.stills_only:return {'action':action['id'],'still':str(still_path.relative_to(ROOT)),'video':None}
    video=out/'videos'/(action['id']+suffix+'.mp4');ffmpeg=shutil.which('ffmpeg')or'/opt/homebrew/bin/ffmpeg'
    fps=f'{action["fps"]:.8f}';size=f'{still.width}x{still.height}'
    command=[ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',size,'-r',fps,'-i','pipe:0','-an','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for tick in range(playback_count(action)):process.stdin.write(render_frame(data,profile,action,tick,args.scale,args.light,args.close).tobytes())
        process.stdin.close();error=process.stderr.read().decode();status=process.wait()
        if status:raise RuntimeError(error)
    except Exception:
        process.kill();process.wait();raise
    video.with_suffix('.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    return {'action':action['id'],'frames':playback_count(action),'fps':action['fps'],'expected_duration':action['duration'],'video':str(video.relative_to(ROOT)),'video_bytes':video.stat().st_size,'still':str(still_path.relative_to(ROOT)),'still_bytes':still_path.stat().st_size,'dimensions':list(still.size)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--action',action='append');parser.add_argument('--all-ready',action='store_true');parser.add_argument('--stills-only',action='store_true');parser.add_argument('--scale',type=int,default=4);parser.add_argument('--light',action='store_true');parser.add_argument('--close',action='store_true');args=parser.parse_args()
    if not args.action and not args.all_ready:parser.error('Choose --action ID or --all-ready')
    data=build();targets=[a for a in data['actions']if (args.all_ready and a['ready']and a.get('defaultVideo'))or a['id']in(args.action or[])]
    requested=set(args.action or[]);unknown=requested-{a['id']for a in targets}
    if unknown:parser.error('Unknown actions: '+','.join(sorted(unknown)))
    report=[]
    for action in targets:
        result=export(data,action,args);report.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
    (ROOT/'demos/export-report.json').write_text(json.dumps({'exports':report,'compositing':'Exact source sequence and explicit new frame mapping; original external effects preserved.','browser_inspection':'Not performed; environment access policy honored.'},ensure_ascii=False,indent=2)+'\n')
    build()

if __name__=='__main__':main()
