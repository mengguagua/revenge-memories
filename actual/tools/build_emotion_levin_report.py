#!/usr/bin/env python3
"""Build lossless comparison stills and timestamped silent demonstration videos."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/emotion-levin-0.5.3'
load=lambda p:json.loads(p.read_text())
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def save(im,p):
    im.save(p,optimize=True);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
def upscale(source,name,scale=3):
    image=Image.open(source);save(image.resize((image.width*scale,image.height*scale),Image.Resampling.NEAREST),REPORT/(name+'.png'))
def video(records,name):
    rows=[]
    for i,row in enumerate(records):
        p=ROOT/row['path'].replace('res://','')
        duration=max(.01,((records[i+1]['clock_ms']-row['clock_ms'])/1000.0) if i+1<len(records) else .04)
        rows.extend(["file '"+str(p).replace("'","'\\''")+"'",'duration '+str(duration)])
    rows.append(rows[-2])
    concat=REPORT/(name+'.ffconcat');concat.write_text('\n'.join(rows)+'\n')
    subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-vf','scale=iw*4:ih*4:flags=neighbor,fps=60','-an','-c:v','libx264','-crf','8','-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart',str(REPORT/(name+'.mp4'))],check=True)
    print('Encoded '+name,flush=True)
    return {'path':name+'.mp4','frames':len(records),'captured_duration_ms':records[-1]['clock_ms']-records[0]['clock_ms'],'pixels':[1704,960],'audio':False,'timing':'Recorded wall-clock timestamps; nearest-neighbour integer 4x; 60fps delivery.'}
def source_comparison(kind):
    data=load(ROOT/'data/hunapu_visuals.json')['executed_melee'][kind]
    sheets=[Image.open(ROOT/'assets/original/graphics/battle/class_21_ally.png').convert('RGBA'),Image.open(ROOT/'assets/hunapu-0.5.3/battle.png').convert('RGBA')]
    frames=[]
    for row in data['frames']:
        im=Image.new('RGB',(384,144),(29,43,54));draw=ImageDraw.Draw(im);draw.text((12,5),'Original source',(239,238,214));draw.text((204,5),'Hunapu 0.5.3',(239,238,214))
        for i,sheet in enumerate(sheets):
            f=row['frame'];cell=sheet.crop((f*80,0,(f+1)*80,72));at=(int(144+row['offset'][0])-40+i*192,40+int(row['offset'][1]))
            if row['flip']:
                cell=cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if f<60:at=(at[0]+16,at[1])
            im.paste(cell,at,cell)
        frames.append(im.resize((768,288),Image.Resampling.NEAREST))
    durations=[round((i+1)*100/60.0988)*10-round(i*100/60.0988)*10 for i in range(len(frames))]
    frames[0].save(REPORT/('source-'+kind+'.gif'),save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=True)
def main():
    motion=load(REPORT/'motion/motion-checks.json');assert motion['passed']
    assert all('source_tick'in f for f in motion['frames'])
    for kind in ['normal','critical']:
        ticks={f['source_tick']for f in motion['frames']if f['movie']==kind}
        expected=load(ROOT/'data/hunapu_visuals.json')['executed_melee'][kind]
        assert any(f['source_variant']=='hunapu_'+kind for f in motion['frames']if f['movie']==kind)
        assert max(ticks)==len(expected['frames'])-1,(kind,max(ticks))
    videos=[]
    for movie in ['walk','normal','critical','miss','hit','dying','levin-near','levin']:
        records=[row for row in motion['frames']if row['movie']==movie];assert records
        videos.append(dict(video(records,movie),fixture=movie!='walk'))
    for kind in ['normal','critical']:source_comparison(kind)
    upscale(REPORT/'motion/01-caption-and-native-actor.png','live-caption')
    upscale(REPORT/'motion/02-hunapu-mouth-actual-dialogue.png','live-dialogue')
    walking=next(row for row in motion['frames'] if row['movie']=='walk' and row['step']==1)
    upscale(ROOT/walking['path'].replace('res://',''),'live-walk')
    for i,code in [(1,'M11')]:upscale(REPORT/f'round{i}/{code}-entry.png','live-'+code)
    # Exact native-size previous/current comparisons; no resampling of actors.
    old=Image.open(ROOT/'assets/hunapu-0.5.1/hub.png').convert('RGBA');new=Image.open(ROOT/'assets/hunapu-0.5.2/hub.png').convert('RGBA');native=Image.open(ROOT/'assets/original/graphics/map_units/personal_01.png').convert('RGBA')
    im=Image.new('RGB',(768,240),(29,43,54));d=ImageDraw.Draw(im)
    for i,(label,sheet) in enumerate([('Original',native),('0.5.1',old),('0.5.3 (same native walk)',new)]):
        cell=sheet.crop((128,0,160,24)).resize((256,192),Image.Resampling.NEAREST);im.paste(cell,(i*256,20),cell);d.text((i*256+12,214),label,fill='white')
    save(im,REPORT/'walk-comparison.png')
    faces=load(REPORT/'portrait-manifest.json')
    im=Image.new('RGB',(1440,264),(29,43,54));d=ImageDraw.Draw(im)
    for i,row in enumerate(faces):
        face=Image.open(ROOT/row['path']).convert('RGB').resize((240,240),Image.Resampling.NEAREST)
        im.paste(face,(i*240,0));d.text((i*240+6,245),row['key'].replace('hunapu_',''),fill='white')
    save(im,REPORT/'portrait-comparison.png')
    for row in motion['actual_dialogue']:
        upscale(ROOT/row['path'].replace('res://',''),'live-dialogue-'+row['emotion'])
    for kind,path in motion['levin_hold_shots'].items():
        upscale(ROOT/path.replace('res://',''),'live-'+kind+'-body')
    for emotion in ['anger','relief']:
        phase='memory' if emotion=='anger' else 'victory'
        upscale(REPORT/f'visual/portrait-{phase}-{emotion}-384.png','fixture-dialogue-'+emotion)
    old_sheet=Image.open(ROOT/'assets/hunapu-0.5.2/battle.png').convert('RGBA')
    new_sheet=Image.open(ROOT/'assets/hunapu-0.5.3/battle.png').convert('RGBA')
    im=Image.new('RGB',(640,308),(29,43,54));d=ImageDraw.Draw(im)
    for i,sheet in enumerate([old_sheet,new_sheet]):
        cell=sheet.crop((124*80,0,125*80,72)).resize((320,288),Image.Resampling.NEAREST)
        im.paste(cell,(i*320,0),cell);d.text((i*320+8,290),'0.5.2' if i==0 else '0.5.3 cumulative body',fill='white')
    save(im,REPORT/'levin-before-after.png')
    # Retain actual attack/recovery stills from the one real keyboard round.
    actual=[]
    for i in [1]:
        report=load(REPORT/f'round{i}/play-checks.json');assert report['passed']
        for pose in [0,1,2,3,8,9,60]:
            row=next((r for r in report['animation_shots']if r['hero_pose']==pose),None)
            if row:
                name=f'round{i}-pose-{pose}';upscale(ROOT/row['path'].replace('res://',''),name)
                actual.append({'round':i,'pose':pose,'path':name+'.png','fixture':False})
    real=load(REPORT/'round1/play-checks.json')['native_animation_frames']
    start=next(i for i,row in enumerate(real)if row['attacker']=='hunapu');end=start
    while end+1<len(real)and real[end+1]['attacker']=='hunapu':end+=1
    videos.append(dict(video(real[start:end+1],'actual-attack'),fixture=False,source='Round 1 real keyboard combat'))
    write(REPORT/'videos.json',videos);write(REPORT/'actual-stills.json',actual)
    manifest=[]
    for p in sorted(REPORT.rglob('*')):
        if p.suffix not in ['.png','.gif','.mp4'] or (p.parent.name.startswith('round') and p.name.startswith('animation-')) or p.parent.name=='motion':continue
        size=list(Image.open(p).size) if p.suffix!='.mp4' else [1704,960]
        manifest.append({'path':str(p.relative_to(REPORT)),'pixels':size,'bytes':p.stat().st_size,'quality_note':'Integer zoom or lossless source-frame animation; preserve clear pixel contours and temporal detail.' if p.stat().st_size>=200000 else 'Native/nearest-neighbour pixels; no blur filters.'})
    write(REPORT/'image-video-manifest.json',manifest)
    print('Videos, source comparisons, native before/after portraits and real battle stills:',len(videos),len(actual))
if __name__=='__main__':main()
