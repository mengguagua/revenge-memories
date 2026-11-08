"""Stage the two advanced sword ultimates with the game's own character art.

Pass the stock act data and effect atlas descriptions exported by
export_puppet_pixelfx.mjs with its SWORD_SOURCE_JSON argument.
"""

import argparse
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ACTUAL = Path(__file__).resolve().parents[1]
DATA = ACTUAL / 'data/battle_fx.json'
CINEMA = json.loads((ACTUAL / 'data/critical_cinema.json').read_text())
FPS = 60
FLOOR = 290
NN = Image.Resampling.NEAREST

# Stable body centers in the approved sprites, measured under each pelvis.
CENTERS = {
    54: 75, 61: 118, 62: 73, 66: 80, 68: 67, 69: 56, 70: 55, 71: 56, 72: 60,
    86: 43, 93: 67, 94: 104, 95: 99, 103: 87, 104: 69, 105: 63, 106: 61, 107: 69,
}
FEMALE_DASH = (94, 95, 94, 95)
MALE_RUN = (69, 70, 71, 72)
FEMALE_RUN = (104, 105, 106, 107)


@lru_cache(maxsize=None)
def art(index):
    record = CINEMA['images'][index]
    source = ACTUAL / record['path'].removeprefix('res://')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == record['sha256']
    with Image.open(source) as picture:
        return picture.convert('RGBA')


def sword_arm(angle):
    # Keep the exact in-game sword, guard and gauntlet attached to the
    # shoulder. Only this part turns through the stock rig's sword angles.
    base = art(66)
    shoulder = (97, 51)
    mask = Image.new('L', base.size)
    ImageDraw.Draw(mask).polygon([
        (92, 43), (99, 42), (107, 45), (115, 60), (128, 70), (143, 80),
        (160, 85), (206, 98), (206, 122), (147, 114), (121, 103),
        (107, 90), (99, 82), (91, 66), (88, 54),
    ], fill=255)
    arm = Image.new('RGBA', base.size)
    arm.paste(base, mask=mask)
    body = base.copy()
    body.paste((0, 0, 0, 0), (0, 0, *body.size), mask)
    canvas = Image.new('RGBA', (base.width+16, base.height+84))
    canvas.alpha_composite(body, (0, 84))
    arm_canvas = Image.new('RGBA', canvas.size)
    arm_canvas.alpha_composite(arm, (0, 84))
    # The source sword already points 20 degrees below the horizon.
    rotated = arm_canvas.rotate(20-angle, NN, center=(shoulder[0], shoulder[1]+84))
    canvas.alpha_composite(rotated)
    return canvas


def progress(t, start, end, ramp=.12):
    """Move at constant speed through the run, with short soft ends."""
    phase = max(0., min(1., (t-start)/(end-start)))
    if phase < ramp:
        return phase*phase/(2*ramp*(1-ramp))
    if phase > 1-ramp:
        tail = 1-phase
        return 1-tail*tail/(2*ramp*(1-ramp))
    return (phase-ramp/2)/(1-ramp)


def lerp(a, b, t):
    return a+(b-a)*t


def run_pose(t, since, cycle):
    return cycle[math.floor((t-since)*12) % len(cycle)]


def hunapu(t, first, index, stock, origin, scale):
    idle = 91+75*.815
    launch = 88+73*.815
    run_start = 3.27
    plant = origin+stock[0]['pose']['x']*scale
    if t < run_start:
        return 61, lerp(launch, launch+14, progress(t,3.20,run_start)), False, 1., None
    if index < 0:
        pos = lerp(launch+14, plant, progress(t,run_start,first))
        return run_pose(t,run_start,MALE_RUN), pos, True, 1., None
    if index < len(stock):
        sample = stock[index]
        pose = sample['pose']
        x = origin+pose['x']*scale
        if sample['t'] < 0:
            return 62, x, False, 1., None
        return 66, x, False, 1., round(math.degrees(pose['sa']))
    recovery = origin+stock[-1]['pose']['x']*scale
    if t < 5.42:
        return 68, recovery, False, 1., None
    if t < 5.53:
        # One turn to leave. The body never fades or switches to the old track.
        turn = progress(t,5.42,5.53)
        return 69, recovery, False, .80+.20*turn, None
    if t < 6.63:
        pos = lerp(recovery, idle, progress(t,5.53,6.63))
        return run_pose(t,5.53,MALE_RUN), pos, False, 1., None
    return 54, idle, False, 1., None


def eileen(t, hit, spin):
    idle = 108+43*.815
    launch = 89+67*.815
    ready = 415
    slash_start = hit-spin['hits'][0]['t']
    dash_start, dash_end = 2.75, slash_start-.085
    if t < dash_start:
        return 93, launch, False, 1., None
    if t < dash_end:
        pos = lerp(launch, ready, progress(t,dash_start,dash_end))
        return run_pose(t,dash_start,FEMALE_DASH), pos, False, 1., None
    if t < slash_start:
        return 93, ready, False, 1., None
    age = t-slash_start
    if age < spin['hits'][0]['t']:
        # The stock act turns away, across the back, then comes round to
        # face the target. Hold the same foot pivot through all four views.
        yaw = next(p.get('yaw',0.) for stamp,p,*_ in reversed(spin['poses']) if stamp<=age)
        return {
            0.: (103, ready, False, 1., None),
            -1.57: (93, ready, False, .70, None),
            -3.14: (93, ready, True, .94, None),
            -4.71: (103, ready, True, .70, None),
        }[yaw]
    if t < 5.18:
        return 103, ready, False, 1., None
    if t < 5.40:
        return 93, ready, False, 1., None
    if t < 5.53:
        return 104, ready, False, .80+.20*progress(t,5.40,5.53), None
    if t < 6.63:
        pos = lerp(ready, idle, progress(t,5.53,6.63))
        return run_pose(t,5.53,FEMALE_RUN), pos, False, 1., None
    return 86, idle, False, 1., None


def pack(name, poses):
    w,h = 168,136
    pivot = 75,130
    cols, capacity = 5,15
    paths = []
    for start in range(0,len(poses),capacity):
        tiles = poses[start:start+capacity]
        atlas = Image.new('RGBA',(w*cols,h*math.ceil(len(tiles)/cols)))
        for i,(sprite,anchor) in enumerate(tiles):
            x,y = round(pivot[0]-anchor),pivot[1]-sprite.height
            bounds = sprite.getbbox()
            assert bounds is not None
            assert x+bounds[0]>0 and y+bounds[1]>0 and x+bounds[2]<w and y+bounds[3]<h
            atlas.alpha_composite(sprite,(i%cols*w+x,i//cols*h+y))
        filename = f'{name}-{start//capacity:02}.png'
        path = ACTUAL/'assets/battle-fx'/filename
        atlas.save(path,optimize=True)
        paths.append('res://assets/battle-fx/'+filename)
        print(filename,atlas.width,atlas.height,path.stat().st_size)
    return dict(paths=paths,size=[w,h],pivot=list(pivot),fps=FPS,frames=len(poses),columns=cols,cells=capacity,loop=False)


def revise(bank, stock, hero, start):
    key = hero+'-sword-advanced'
    plan = bank['cinema'][key]
    spec = CINEMA['cases'][key]
    hit = spec['hit']
    density = plan['density']
    plan.update(contact=hit,first=-hit,replace=[start-hit,5.64-hit])
    clock_offset = 0
    if hero == 'hunapu':
        double = stock['double']
        samples = double['samples']
        hit_frame = double['hits'][1]['frame']
        first_tick = round(hit*FPS)-hit_frame
        clock_offset = hit-round(hit*FPS)/FPS
        plan['contact'] = hit-clock_offset
        effect_start = -hit_frame/FPS
        act_scale = 1.85
        origin = 502-double['target']*act_scale
        effect_end = effect_start+len(samples)/FPS
        plan['layers'] = [dict(effect='hunapu-double-slash-stock',start=effect_start,
                               end=effect_end,at=[origin,FLOOR],scale=act_scale*density)]
        plan['end'] = effect_end
        plan['stock_impact'] = {
            'start': effect_start, 'scale': act_scale, 'hits': double['hits'],
            'frames': [[*s['shake'],s['flash'],round(math.tan(s['tilt'])*.8,5)] for s in samples],
        }
        sampler = lambda t,tick: hunapu(t,hit+effect_start,tick-first_tick,samples,origin,act_scale)
    else:
        # Match the stock ring-to-actor ratio on the larger cinematic stage.
        # The geometry and two-layer timing are the stock module's own.
        effect_start = -stock['spin']['hits'][0]['t']
        plan['layers'] = [
            dict(effect='eileen-fire-spin-'+layer,layer=layer,start=effect_start,
                 end=effect_start+.8,at=[415,FLOOR],scale=1.95)
            for layer in ['back','front']
        ]
        plan['end'] = effect_start+.8
        sampler = lambda t,tick: eileen(t,hit,stock['spin'])
    lookup, poses, frames = {}, [], []
    for tick in range(round(start*FPS), math.ceil(spec['duration']*FPS)+1):
        index,x,flip,width,angle = sampler(tick/FPS+clock_offset,tick)
        # Keep the acting poses at their original armor/cloth proportions.
        scale = density*(.815 if index not in (*MALE_RUN,*FEMALE_RUN) else .97)
        # Quantize the squash on the quarter-turn to native pixel widths.
        width = round(width*20)/20
        tile = index,flip,width,angle
        if tile not in lookup:
            image = art(index) if angle is None else sword_arm(angle)
            center = CENTERS[index]
            if flip:
                image = ImageOps.mirror(image)
                center = image.width-center
            w,h = round(image.width*scale*width),round(image.height*scale)
            lookup[tile] = len(poses)
            poses.append((image.resize((w,h),NN),center*w/image.width))
        frames.append([lookup[tile],round(x,3),FLOOR,False,1.0])
    # The stock lunge starts with an authored snap forward. The incoming
    # run and return must stay continuous; the original slash can step.
    for tick,(a,b) in enumerate(zip(frames,frames[1:]), round(start*FPS)):
        if hero != 'hunapu' or not first_tick <= tick < first_tick+len(samples):
            assert abs(b[1]-a[1])<8, (key,tick)
    name = plan['actor']['effect']
    bank['effects'][name] = pack(name,poses)
    plan['actor'] = dict(effect=name,first=round(start*FPS),frames=frames)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stock',type=Path)
    stock = json.loads(parser.parse_args().stock.read_text())
    bank = json.loads(DATA.read_text())
    bank['effects'].update(stock['effects'])
    revise(bank,stock,'hunapu',3.20)
    revise(bank,stock,'eileen',2.65)
    DATA.write_text(json.dumps(bank,ensure_ascii=False,separators=(',',':'))+'\n')
