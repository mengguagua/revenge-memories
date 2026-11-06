"""Lossless PC MAP captures and stream-copy of the approved engine demo."""
from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
source=ROOT/'source/map-captures'
visual=json.loads((source/'visual.json').read_text())
assert visual['passed'] and visual['guard'] and len(visual['cases'])==5 and not visual['errors']
keys=['hunapu-base','hunapu-advanced','hunapu-bow','eileen-base','eileen-advanced']
records=[]
for key in keys:
    for view,suffix in [('impact','motion-24' if key=='hunapu-bow' else 'motion-18'),('range','target-free')]:
        src=source/(key+'-'+suffix+'.png');dst=ROOT/'assets/images'/('map-'+key+'-'+view+('-20261102b' if key=='hunapu-bow' and view=='impact' else '')+'.webp')
        original=src;crop=None
        if view=='impact':
            # A pixel-preserving close view of the actual PC capture. Keep the full frame.
            bounds=subprocess.check_output(['/opt/homebrew/bin/magick',str(source/(key+'-motion-00.png')),str(src),'-compose','difference','-composite','-crop','1278x600+0+120','-threshold','2%','-trim','-format','%w %h %X %Y','info:'],text=True)
            w,h,x,y=map(int,bounds.split());left=max(0,min(558,round((x+w/2-360)/3)*3));top=max(0,min(315,round((y+h/2-202.5)/3)*3));crop=f'720x405+{left}+{top}'
            src=source/(key+'-impact-crop.png')
            subprocess.run(['/opt/homebrew/bin/magick',str(original),'-crop',crop,'+repage',str(src)],check=True)
        subprocess.run(['/opt/homebrew/bin/magick',str(src),'-strip','-define','webp:lossless=true','-define','webp:method=6',str(dst)],check=True)
        result=subprocess.run(['/opt/homebrew/bin/magick','compare','-metric','AE',str(src),str(dst),'null:'],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        records.append({'purpose':'PC MAP '+view+' capture; directed demonstration placements','asset':str(dst.relative_to(ROOT)),'source':str(src.relative_to(REPO)),'pixels':'720x405' if view=='impact' else '1278x720','original_capture':str(original.relative_to(REPO)),'crop':crop,'bytes':dst.stat().st_size,'source_bytes':src.stat().st_size,'pixel_identical':True,'method':'lossless WebP, metadata stripped'})
old=json.loads((ROOT/'reports/image-assets.json').read_text());old=[r for r in old if r['asset'] not in {x['asset'] for x in records} and r['asset']!='assets/images/map-hunapu-bow-impact.webp']
(ROOT/'assets/images/map-hunapu-bow-impact.webp').unlink(missing_ok=True)
(ROOT/'reports/image-assets.json').write_text(json.dumps(old+records,ensure_ascii=False,indent=2)+'\n')
movie=REPO/'art-review/map-20261029/runtime/map-runtime-all.mp4';out=ROOT/'assets/video/map-skills-20261102.mp4'
subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-i',str(movie),'-map','0','-c','copy','-movflags','+faststart',str(out)],check=True)
def stream_hash(p):
    return subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(p),'-map','0','-c','copy','-f','streamhash','-hash','sha256','-'],text=True)
assert stream_hash(movie)==stream_hash(out)
report={'date':'2026-11-02','images':records,'video':{'source':str(movie.relative_to(REPO)),'asset':str(out.relative_to(ROOT)),'bytes':out.stat().st_size,'duration_seconds':6.4,'width':1280,'height':592,'video_and_audio_packet_hash_equal':True,'scope':'Existing current production-engine demonstration, staged placements, five animations and attack SFX. Not labelled PC or device recording.'},'rules_source':'actual/core/map_skills.gd','capture_scope':visual['scope'],'guard':visual['guard'],'layout_errors':visual['errors']}
(ROOT/'reports/map-feature-assets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'new_images':len(records),'image_bytes':sum(r['bytes'] for r in records),'largest_image':max(r['bytes'] for r in records),'video_bytes':out.stat().st_size,'stream_copy':True}))
