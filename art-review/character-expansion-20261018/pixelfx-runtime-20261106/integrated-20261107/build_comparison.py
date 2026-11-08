"""Align actual before/after renderer frames at the recorded game contact."""
import argparse
import bisect
import json
import math
import mmap
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

WIDTH, HEIGHT, FPS = 592, 240, 60
ROW = WIDTH*3
FRAME = ROW*HEIGHT
HERE = Path(__file__).resolve().parent
MEDIA = HERE/'media'
FAMILY = {
    'cinema':'主角必杀','magic':'法术','lightning-sword':'雷剑','lance':'枪击',
    'archery':'弓箭','javelin':'投枪','support':'治疗与支援','map':'地图战斗',
    'sword':'剑击','monster':'怪物','mechanical':'机械怪',
}


def read(path):
    return json.loads(path.read_text())


def recording(root, job):
    return root/f"{job['id']}.json"


def require_pair(before, after):
    key = after['key']
    assert before['source']==after['source'], f'{key}: different native program'
    assert before['contacts']==after['contacts'] and before['commits']==after['commits'], key
    assert not before['layout'] and not after['layout'], (key,before['layout'],after['layout'])
    if 'map_outcome' in after:
        assert before['map_outcome']==after['map_outcome'], key
    else:
        assert before['event']==after['event'], key
        if after['event'].get('visual_only', False):
            initial = after['event']['hp_before']
            assert before['actual_hp'] == after['actual_hp'] == initial, key
            for take in (before, after):
                shown = take['hp_steps'][-1][1] if take['hp_steps'] else initial
                assert shown == take['expected_hp'], key
        else:
            assert before['actual_hp']==after['actual_hp']==after['expected_hp'], key
        assert before['source_hp']==after['source_hp'], key


def source_frame(meta, at):
    return max(0,bisect.bisect_right(meta['times'],at+1e-7)-1)


def make_clip(job, before_path, after_path, align_contact=True, media=MEDIA):
    before, after = read(before_path), read(after_path)
    require_pair(before,after)
    start_at = max(before['contact'],after['contact']) if align_contact else after['contact']
    assert start_at >= 0
    delay_before, delay_after = (max(0,start_at-m['contact']) if align_contact else 0 for m in (before,after))
    duration = max(before['times'][-1]+delay_before,after['times'][-1]+delay_after)+.24
    count = math.ceil(duration*FPS)
    duration = count/FPS
    key = job['id']
    movie = media/f'{key}.mp4'
    original = media/f'{key}-before.m4a'
    poster = media/f'{key}.png'
    at = min(duration-.05,start_at+(.10 if job['family']!='map' else .13))
    first_index = source_frame(before,at-delay_before)
    second_index = source_frame(after,at-delay_after)
    if not (movie.is_file() and original.is_file() and poster.is_file()):
        cmd = ['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
               '-s',f'{WIDTH*2}x{HEIGHT}','-r',str(FPS),'-i','pipe:0',
               '-i',str(after_path.with_suffix('.wav')),'-map','0:v','-map','1:a',
               '-filter_threads','1','-vf','scale=iw*2:ih*2:flags=neighbor,format=yuv420p',
               '-af',f'adelay={round(delay_after*1000)}:all=1,apad','-t',str(duration),
               '-c:v','libx264','-threads','3','-preset','veryfast','-crf','15','-c:a','aac','-b:a','128k',
               '-movflags','+faststart',str(movie)]
        with (before_path.with_suffix('.rgb').open('rb') as before_f,
              after_path.with_suffix('.rgb').open('rb') as after_f,
              mmap.mmap(before_f.fileno(),0,access=mmap.ACCESS_READ) as first,
              mmap.mmap(after_f.fileno(),0,access=mmap.ACCESS_READ) as second,
              subprocess.Popen(cmd,stdin=subprocess.PIPE) as encoder):
            old = (-1,-1)
            combined = bytearray(FRAME*2)
            for index in range(count):
                clock = index/FPS
                pair = (source_frame(before,clock-delay_before),source_frame(after,clock-delay_after))
                if pair != old:
                    a,b = (k*FRAME for k in pair)
                    for row in range(HEIGHT):
                        x = row*ROW
                        combined[x*2:x*2+ROW] = first[a+x:a+x+ROW]
                        combined[x*2+ROW:x*2+ROW*2] = second[b+x:b+x+ROW]
                    old = pair
                encoder.stdin.write(combined)
            encoder.stdin.close()
            assert encoder.wait()==0, key
            shot=Image.new('RGB',(WIDTH*2,HEIGHT))
            shot.paste(Image.frombytes('RGB',(WIDTH,HEIGHT),first[first_index*FRAME:(first_index+1)*FRAME]),(0,0))
            shot.paste(Image.frombytes('RGB',(WIDTH,HEIGHT),second[second_index*FRAME:(second_index+1)*FRAME]),(WIDTH,0))
            shot.save(poster,optimize=True)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(before_path.with_suffix('.wav')),
                        '-af',f'adelay={round(delay_before*1000)}:all=1,apad',
                        '-t',str(duration),'-c:a','aac','-b:a','128k',str(original)],check=True)
    return clip_row(job, after, start_at, delay_after, count, at, movie, original, poster) | (
        {'beforeDuration': before['times'][-1], 'afterDuration': after['times'][-1]}
        if not align_contact else {}
    )


def clip_row(job, after, start_at, delay_after, count, at, movie, original, poster):
    hp = after.get('hp_steps', [])
    event = after.get('event', {})
    visual_only = event.get('visual_only', False)
    actual = (hp[-1][1] if hp else event.get('hp_before')) if visual_only else after.get('actual_hp')
    row = {
        'key':job['id'],'title':job['title'],'family':FAMILY[job['family']],
        'kind':job['family'],'duration':count/FPS,'frames':count,'contact':start_at,
        'video':'media/'+movie.name,'beforeAudio':'media/'+original.name,
        'poster':'media/'+poster.name,'posterTime':at,
        'commits':after['commits'],'contacts':after['contacts'],'source':after['source'],
        'hpStart':event.get('hp_before'),'hpEnd':actual,
        'hpAt':round(hp[len(hp)//2][0]+delay_after,4) if hp else None,
        'cueAt':next((round(t+delay_after,4) for t,k in after['cues'] if k not in ['hp_tick','hit','miss']),None),
        'cues':[[round(t+delay_after,4),cue] for t,cue in after['cues'] if cue!='hp_tick'],
        'hpSteps':[[round(t+delay_after,4),h] for t,h in hp],
    }
    if visual_only:
        row['support'] = True
    if 'archive' in job:
        row['archive'] = job['archive']
    if event:
        row['classId'] = int(job['actor']['class_id'])
        row['distance'] = int(event['distance'])
        row['side'] = job['actor']['side']
    if job['family'] == 'cinema':
        row['portraitAt'] = 1.55 + delay_after
    if job['id'] == 'cinema-hunapu-sword-advanced':
        row['firstSlashAt'] = start_at - 10/FPS + .025
    return row


def refresh_poster(before, before_time, after_path, after, after_time, poster):
    # Use the original capture pixels on the current side. Re-decoding the
    # new H.264 adds compression noise to both the screenshot and its size.
    original = subprocess.check_output(['ffmpeg','-hide_banner','-loglevel','error',
        '-ss',str(max(0,before_time)),'-i',str(before),'-frames:v','1','-filter_threads','1',
        '-vf',f'crop={WIDTH*2}:{HEIGHT*2}:0:0,scale={WIDTH}:{HEIGHT}:flags=neighbor',
        '-pix_fmt','rgb24','-threads','1','-f','rawvideo','pipe:1'])
    with after_path.with_suffix('.rgb').open('rb') as native:
        native.seek(source_frame(after,after_time)*FRAME)
        updated = native.read(FRAME)
    shot = Image.new('RGB',(WIDTH*2,HEIGHT))
    shot.paste(Image.frombytes('RGB',(WIDTH,HEIGHT),original),(0,0))
    shot.paste(Image.frombytes('RGB',(WIDTH,HEIGHT),updated),(WIDTH,0))
    shot.save(poster,optimize=True)


def refresh_clip(job, old, after_path, media):
    """Keep the original side of an already published comparison."""
    after = read(after_path)
    key = job['id']
    assert after['source'] == old['source'], (key, 'different animation program')
    assert after['contacts'] == old['contacts'] and after['commits'] == old['commits'], key
    assert not after['layout'], (key, after['layout'])
    assert after['actual_hp'] == old['hpEnd'] == after['expected_hp'], key
    assert [step[1] for step in after['hp_steps']] == [step[1] for step in old['hpSteps']], key
    same_start = 'beforeDuration' in old
    start = after['contact'] if same_start else max(old['contact'], after['contact'])
    delay_left = 0 if same_start else start - old['contact']
    delay_right = 0 if same_start else start - after['contact']
    count = math.ceil(max(old['duration']+delay_left,after['times'][-1]+delay_right+.24)*FPS-1e-6)
    duration = count/FPS
    at = start+.10
    movie = media/f'{key}.mp4'
    original = media/f'{key}-before.m4a'
    poster = media/f'{key}.png'
    historical_movie = HERE / old['video'].split('?')[0]
    historical_audio = HERE / old['beforeAudio'].split('?')[0]
    ffmpeg = ['ffmpeg','-hide_banner','-loglevel','error','-y']
    filters = (
        f'[0:v]crop={WIDTH*2}:{HEIGHT*2}:0:0,'
        f'tpad=start_mode=clone:start_duration={delay_left:.6f}:stop_mode=clone:stop_duration={duration:.6f}[original];'
        f'[1:v]scale={WIDTH*2}:{HEIGHT*2}:flags=neighbor,format=yuv420p[updated];'
        '[original][updated]hstack[out]'
    )
    cmd = ffmpeg + ['-i',str(historical_movie),'-f','rawvideo','-pix_fmt','rgb24',
        '-s',f'{WIDTH}x{HEIGHT}','-r',str(FPS),'-i','pipe:0','-i',str(after_path.with_suffix('.wav')),
        '-filter_complex_threads','1','-filter_complex',filters,'-map','[out]','-map','2:a',
        '-af',f'adelay={round(delay_right*1000)}:all=1,apad','-t',str(duration),
        '-c:v','libx264','-threads','3','-preset','veryfast','-crf','15','-c:a','aac','-b:a','128k',
        '-movflags','+faststart',str(movie)]
    if not (movie.is_file() and original.is_file() and poster.is_file()):
        with (after_path.with_suffix('.rgb').open('rb') as data,
              mmap.mmap(data.fileno(),0,access=mmap.ACCESS_READ) as frames,
              subprocess.Popen(cmd,stdin=subprocess.PIPE) as encoder):
            for i in range(count):
                offset = source_frame(after,i/FPS-delay_right)*FRAME
                encoder.stdin.write(frames[offset:offset+FRAME])
            encoder.stdin.close()
            assert encoder.wait()==0, key
        if not delay_left and duration <= old['duration']:
            original.write_bytes(historical_audio.read_bytes())
        else:
            subprocess.run(ffmpeg + ['-i',str(historical_audio),'-t',str(duration),
                '-af',f'adelay={round(delay_left*1000)}:all=1,apad','-c:a','aac','-b:a','128k',str(original)],check=True)
        refresh_poster(historical_movie,at-delay_left,after_path,after,at-delay_right,poster)
    result = clip_row(job, after, start, delay_right, count, at, movie, original, poster)
    if same_start:
        result.update(beforeDuration=old['beforeDuration'], afterDuration=after['times'][-1])
    if 'dashAt' in old:
        result['dashAt'] = old['dashAt']-old['contact']+start
    return result


def build_refresh(root, jobs, old_path, out):
    if out.resolve() == HERE:
        raise ValueError('Build in a staging directory so the historical side stays readable')
    media = out/'media'
    media.mkdir(parents=True,exist_ok=True)
    old = {row['key']:row for row in json.loads(old_path.read_text().split('=',1)[1].strip().removesuffix(';'))}
    rows = {row['id']:old[row['id']] for row in jobs if row['family']=='map'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = {}
        while len(rows) < len(jobs):
            for job in jobs:
                key = job['id']
                if key in rows or key in active:
                    continue
                extra = key not in old
                after_dir = root/('after-extra-record' if extra else 'record')
                if job['family']=='cinema' and (root/'cinema-record').is_dir():
                    after_dir = root/'cinema-record'
                if key in {'05cd08dfed6e','201053d393f0'} and (root/'bound-record').is_dir():
                    after_dir = root/'bound-record'
                a = recording(after_dir,job)
                b = recording(root/'before-record',job) if extra else None
                if not a.is_file() or b is not None and not b.is_file():
                    if (after_dir/'run.json').is_file() and not a.is_file():
                        raise RuntimeError(f'Missing current recording: {key}')
                    if b is not None and not b.is_file() and (root/'before-record/run.json').is_file():
                        raise RuntimeError(f'Missing original recording: {key}')
                    continue
                try:
                    read(a)
                    if b is not None:
                        read(b)
                except json.JSONDecodeError:
                    continue
                cached = media/f'{key}.mp4'
                if cached.is_file() and cached.stat().st_mtime_ns < a.stat().st_mtime_ns:
                    for path in (cached,media/f'{key}-before.m4a',media/f'{key}.png'):
                        path.unlink(missing_ok=True)
                active[key] = (pool.submit(make_clip,job,b,a,True,media) if extra else
                               pool.submit(refresh_clip,job,old[key],a,media))
            for key,future in list(active.items()):
                if future.done():
                    rows[key] = future.result()
                    del active[key]
                    print(key, rows[key]['frames'], 'frames', flush=True)
            if len(rows) < len(jobs):
                time.sleep(.75)
    result = [rows[j['id']] for j in jobs]
    (out/'clips.js').write_text('window.BATTLE_REVIEW='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n')
    print('Encoded',len(result),'native comparisons')


def run(root, jobs):
    MEDIA.mkdir(exist_ok=True)
    rows = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = {}
        while len(rows)<len(jobs):
            for job in jobs:
                key = job['id']
                if key in rows or key in active:
                    continue
                b=recording(root/('before-map-record' if job['family']=='map' else 'before-record'),job)
                a=recording(root/'release-record',job)
                if not b.is_file() or not a.is_file():
                    continue
                try:
                    read(a)
                except json.JSONDecodeError:
                    continue
                active[key]=pool.submit(make_clip,job,b,a,key!='d29883179289')
            for key,future in list(active.items()):
                if future.done():
                    rows[key]=future.result()
                    del active[key]
            if (root/'release-record/run.json').is_file() and len(active)+len(rows)<len(jobs):
                missing=[j['id'] for j in jobs if j['id'] not in rows and j['id'] not in active]
                raise RuntimeError('Capture omitted '+', '.join(missing))
            if len(rows)<len(jobs):
                time.sleep(.75)
    ordered=[rows[j['id']] for j in jobs]
    (HERE/'clips.js').write_text('window.BATTLE_REVIEW='+json.dumps(ordered,ensure_ascii=False,separators=(',',':'))+';\n')
    print('Encoded',len(ordered),'native comparisons')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('work',type=Path)
    parser.add_argument('--published',type=Path)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    jobs = args.work/'final-jobs.json'
    fixtures = read(jobs if jobs.is_file() else HERE/'capture-fixtures.json')
    if args.published is None:
        run(args.work,fixtures)
    else:
        build_refresh(args.work,fixtures,args.published,args.out or args.work/'comparison')
