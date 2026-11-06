"""Encode fresh production PC footage; keep source stills and packet-identical delivery copies."""
from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent
SOURCE=ROOT/'source/critical-captures'
visual=json.loads((SOURCE/'capture.json').read_text());assert visual['passed'] and visual['guard'] and not visual['errors']
images=[];videos=[]
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def stream_hash(p,which='0'):
 return subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(p),'-map',which,'-c','copy','-f','streamhash','-hash','sha256','-'],text=True)
for case in visual['records']:
 key=case['key']
 assert len(case['contacts'])==1 and case['final_hp']==24
 for phase in ['portrait','impact']:
  source=SOURCE/(key+'-'+phase+'.png');dest=ROOT/'assets/images'/('critical-'+key+'-'+phase+'-20261104.webp')
  run(['/opt/homebrew/bin/magick',str(source),'-strip','-define','webp:lossless=true','-define','webp:method=6',str(dest)])
  diff=subprocess.run(['/opt/homebrew/bin/magick','compare','-metric','AE',str(source),str(dest),'null:'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
  images.append({'asset':str(dest.relative_to(ROOT)),'source':str(source.relative_to(REPO)),'pixels':'1278x720','bytes':dest.stat().st_size,'pixel_identical':True,'purpose':'Current PC critical '+phase+' capture; staged battle','method':'Lossless WebP, metadata stripped'})
 audio=REPO/'art-review/critical-cinema-20261103/videos'/(key+'.mp4')
 master=SOURCE/(key+'-pc.mp4');dest=ROOT/'assets/video'/('critical-'+key+'-20261104.mp4')
 run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(Path(case['movie_frames'])/'frame-%04d.png'),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-frames:v',str(case['frames']),'-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(master)])
 assert stream_hash(audio,'0:a:0')==stream_hash(master,'0:a:0')
 run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-i',str(master),'-map','0','-c','copy','-movflags','+faststart',str(dest)])
 assert stream_hash(master)==stream_hash(dest)
 videos.append({'asset':str(dest.relative_to(ROOT)),'source':str(master.relative_to(REPO)),'audio_source':str(audio.relative_to(REPO)),'bytes':dest.stat().st_size,'seconds':case['seconds'],'pixels':'1278x720','audio_packet_hash_equal':True,'delivery_stream_hash_equal':True,'source_encode':'H.264 CRF16, yuv420p, native PC frames at 30fps; no resizing. Approved matching SFX/music audio stream copied. Delivery MP4 remux preserves both streams.','sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
old=json.loads((ROOT/'reports/image-assets.json').read_text());names={x['asset'] for x in images};old=[r for r in old if r['asset'] not in names];(ROOT/'reports/image-assets.json').write_text(json.dumps(old+images,ensure_ascii=False,indent=2)+'\n')
report={'date':'2026-11-04','guard':visual['guard'],'capture_scope':visual['scope'],'layout_errors':visual['errors'],'images':images,'videos':videos,'source':'actual/core/critical_cinema.gd and actual/data/critical_cinema.json','user_saves_touched':False}
(ROOT/'reports/critical-assets-20261104.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'images':len(images),'image_bytes':sum(x['bytes'] for x in images),'largest_image':max(x['bytes'] for x in images),'videos':len(videos),'video_bytes':sum(x['bytes'] for x in videos),'source_audio_preserved':True,'delivery_streams_preserved':True}))
