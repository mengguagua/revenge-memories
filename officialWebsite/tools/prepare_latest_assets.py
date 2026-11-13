"""Publish lossless PC stills and compact click-to-play native renderer reels."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent
SOURCE=ROOT/'source/latest-20261113'; FFMPEG='/opt/homebrew/bin/ffmpeg'; MAGICK='/opt/homebrew/bin/magick'
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def probe(p):return json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
d=json.loads((SOURCE/'capture.json').read_text());assert d['passed'] and d['background_guard'] and not d['errors']
assert 'SCRIPT ERROR' not in Path('/private/tmp/website-latest-capture.log').read_text()
assert [x['profile']['climate'] for x in d['movies'][:3]]==['snow','coast','cave']
assert d['movies'][1]['shore_edges']>0 and d['movies'][2]['fires']>0
assert all(x['contact_count']==1 and x['target_hp']==x['expected_hp'] for x in d['movies'][3:])
images=[];videos=[]
def still(source,key,purpose):
 dest=ROOT/'assets/images'/f'latest-{key}-20261113.webp'
 run([MAGICK,str(source),'-strip','-define','webp:lossless=true','-define','webp:method=6',str(dest)])
 diff=subprocess.run([MAGICK,'compare','-metric','AE',str(source),str(dest),'null:'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
 size=subprocess.check_output([MAGICK,'identify','-format','%wx%h',str(dest)],text=True)
 images.append({'asset':str(dest.relative_to(ROOT)),'source':str(source.relative_to(REPO)),'pixels':size,'bytes':dest.stat().st_size,'pixel_identical':True,'purpose':purpose,'method':'Lossless WebP; no resizing'})
for shot in d['shots']:still(SOURCE/(shot['id']+'.png'),shot['id'],'Fresh production PC capture; staged presentation fixture')
for model,file in [('water_monkey','mechanical_puppets_art.json'),('pseudo_titan','pseudo_titan_art.json'),('cyclops','story_puppets_art.json'),('owl','story_puppets_art.json'),('prometheus','story_puppets_art.json')]:
 spec=json.loads((REPO/'actual/data'/file).read_text())
 path=spec['models'][model]['portraits']['intact'] if 'models' in spec else spec.get('portrait','res://assets/mechanical-puppets-20261104/portrait.png')
 still(REPO/'actual'/path.removeprefix('res://'),'portrait-'+model,'Current in-game mechanical enemy portrait')
for movie in ['environment','combat','puppets']:
 records=[x for x in d['movies'] if x['movie']==movie];count=sum(x['frames'] for x in records);audio=[c for r in records for c in r['audio'] if c['path'] and c['at']>=0]
 master=SOURCE/(movie+'-pc.mp4');dest=ROOT/'assets/video'/f'latest-{movie}-20261113.mp4'
 args=[FFMPEG,'-y','-loglevel','error','-framerate','30','-i',f'/private/tmp/website-latest-pc-frames/{movie}/frame-%04d.png']
 for cue in audio:args+=['-i',str(REPO/'actual'/cue['path'].removeprefix('res://'))]
 if audio:
  filters=[f'[{i+1}:a]atrim=duration={c["duration"]},asetpts=PTS-STARTPTS,volume={c["gain"]},adelay={round(c["at"]*1000)}:all=1[a{i}]' for i,c in enumerate(audio)]
  filters+=[''.join(f'[a{i}]' for i in range(len(audio)))+f'amix=inputs={len(audio)}:normalize=0,apad,atrim=duration={count/30},alimiter=limit=0.95:level=false[audio]']
  args+=['-filter_complex',';'.join(filters),'-map','0:v:0','-map','[audio]','-c:a','aac','-b:a','160k']
 args+=['-frames:v',str(count),'-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(master)]
 run(args)
 run([FFMPEG,'-y','-loglevel','error','-i',str(master),'-map','0','-c','copy','-movflags','+faststart',str(dest)])
 def streamhash(p):return subprocess.check_output([FFMPEG,'-v','error','-i',str(p),'-map','0','-c','copy','-f','streamhash','-hash','sha256','-'],text=True)
 assert streamhash(master)==streamhash(dest)
 info=probe(dest);seconds=float(info['format']['duration']);assert abs(seconds-count/30)<.1
 videos.append({'id':movie,'asset':str(dest.relative_to(ROOT)),'source':str(master.relative_to(REPO)),'bytes':dest.stat().st_size,'seconds':seconds,'pixels':'1278x720','audio_cues':len(audio),'delivery_streams_preserved':True,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'method':'H.264 CRF16 yuv420p, native 3x PC viewport, 30fps; reviewed in-game audio cues mixed where registered. Delivery remux is stream-identical. Environment and puppet reels have no added soundtrack.'})
# Keep the runtime duration labels in the same manifest as the verified exports.
p=ROOT/'content.js';s=p.read_text()
for v in videos:s=s.replace('"id": "'+v['id']+'",\n    "title":', '"id": "'+v['id']+'",\n    "duration": "00:'+str(round(v['seconds'])).zfill(2)+'",\n    "title":')
p.write_text(s)
p=ROOT/'reports/image-assets.json';old=json.loads(p.read_text());names={r['asset'] for r in images};p.write_text(json.dumps([r for r in old if r['asset'] not in names]+images,ensure_ascii=False,indent=2)+'\n')
report={'date':'2026-11-13','capture_scope':d['scope'],'background_guard':True,'user_saves_touched':False,'gameplay_code_modified':False,'layout_errors':d['errors'],'images':images,'videos':videos,'sources':['actual/core/map_ambient.gd','actual/assets/map-ambient-20261112/profiles.json','actual/core/reviewed_battle_fx.gd','actual/data/battle_fx.json','actual/core/mechanical_puppets.gd','actual/core/mechanical_art.gd','actual/core/innate_attacks.gd'],'attack_contacts':[{'id':x['id'],'count':x['contact_count']} for x in d['movies'][3:]]}
(ROOT/'reports/latest-assets-20261113.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'images':len(images),'image_bytes':sum(x['bytes'] for x in images),'largest_image':max(x['bytes'] for x in images),'videos':[(x['id'],x['seconds'],x['bytes'],x['audio_cues']) for x in videos]}))
