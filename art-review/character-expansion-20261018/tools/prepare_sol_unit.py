# -*- coding: utf-8 -*-
"""Prepare frozen source crops and labelled geometry boards; never author art."""
from pathlib import Path
from PIL import Image, ImageDraw
import argparse, json, math
R=Path(__file__).resolve().parents[1]
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def board(items,path,scale=4,columns=4):
    cellw=max(im.width for _,im in items)*scale+24
    cellh=max(im.height for _,im in items)*scale+40
    out=Image.new('RGB',(cellw*min(columns,len(items)),cellh*math.ceil(len(items)/columns)),'#e6e1d5');draw=ImageDraw.Draw(out)
    for n,(f,im) in enumerate(items):
        x=(n%columns)*cellw;y=(n//columns)*cellh
        draw.text((x+12,y+6),str(f),fill='#20242a');im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);out.paste(im,(x+12,y+28),im)
    out.save(path,optimize=True)
def main(uid):
    unit=next(u for u in json.loads((R/'catalog/production-units.json').read_text())['units']if u['id']==uid)
    P=R/'professions'/uid;Q=P/'reference';Q.mkdir(parents=True,exist_ok=True)
    for part in ['battle','maps']:
        for sub in ['source','frames','reviews']:(P/part/sub).mkdir(parents=True,exist_ok=True)
    write(Q/'production-unit.json',unit)
    atlas=Image.open(R/unit['source_atlas']).convert('RGBA');w,h=unit['source_frame_size'];cols=unit['columns'];items=[]
    for f in unit['required_source_frames']:
        im=atlas.crop((f%cols*w,f//cols*h,f%cols*w+w,f//cols*h+h));im.save(Q/f'original-{f:03}.png',optimize=True)
        if f in unit['unique_art_frames']:items.append((f,im))
    for n in range(0,len(items),6):board(items[n:n+6],Q/f'battle-{n//6:02}-geometry.png',4,3)
    overlay=json.loads((R/'source-input/corrected-tactical-walk/overlay.json').read_text());rec=overlay['records'].get(uid)
    if rec:
        write(Q/'native-walk-record.json',rec);path=R/'source-input/corrected-tactical-walk'/rec['source_atlas'];im=Image.open(path).convert('RGBA')
        walk=[]
        for f in range(8):
            a=im.crop((32*f,0,32*f+32,24));a.save(Q/f'walk-{f}.png',optimize=True);walk.append((f,a))
        board(walk,Q/'walk-geometry.png',10,4)
    im=Image.open(R/unit['map_idle_source']).convert('RGBA');fs=im.width//6;idle=[]
    for f in range(6):
        a=im.crop((fs*f,0,fs*f+fs,im.height));a.save(Q/f'idle-{f}.png',optimize=True)
        if f<3:idle.append((f,a))
    board(idle,Q/'idle-geometry.png',10,3)
    print(uid,len(items),'battle independent; source boards prepared')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('unit');main(a.parse_args().unit)
