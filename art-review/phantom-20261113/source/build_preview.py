from pathlib import Path
import json,subprocess
from PIL import Image
review=Path(__file__).resolve().parents[1]
project=review.parents[1]
source=Path('/private/tmp/phantom-preview-20261113')
reports=project/'actual/reports/phantom-20261113'
media=review/'media';media.mkdir(exist_ok=True)
plays=[json.loads((reports/f'round{n}-play.json').read_text()) for n in [1,2]]
boundaries=json.loads((reports/'boundaries.json').read_text())
assert all(p['passed'] and p['source_unchanged'] for p in plays) and boundaries['passed']
clips=[c for p in plays for c in p['clips']]+[c for r in boundaries['records'] for c in r['clips']]
assets=[]
for clip in clips:
 name=clip['name'];folder=source/name
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(folder/'%04d.png'),'-frames:v',str(clip['frames']),'-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(media/(name+'.mp4'))],check=True)
 Image.open(folder/'0000.png').save(media/(name+'.webp'),format='WEBP',lossless=True,method=6)
 clip['seconds']=clip['frames']/12
 assets.append({'name':name,'kind':'Godot mobile-layout clip','size':clip['size'],'frames':clip['frames'],'video_bytes':(media/(name+'.mp4')).stat().st_size,'poster_bytes':(media/(name+'.webp')).stat().st_size})
for name in ['round1-spell','round1-summoned','round1-experience','round2-spell','round2-summoned','round2-experience','rank2-spell','rank2-summoned','rank3-capacity-spell','rank3-capacity-summoned','rank3-capacity-falcon']:
 im=Image.open(source/(name+'.png'));out=media/(name+'.webp');im.save(out,format='WEBP',lossless=True,method=6)
 row={'name':name,'kind':'Godot screenshot','size':list(im.size),'bytes':out.stat().st_size}
 if row['bytes']>=200000:row['quality_note']='Lossless native-pixel UI/terrain reference retained for clarity.'
 assets.append(row)
(review/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
summary={'passed':True,'capture':'Guarded offscreen Godot phone layout,1334x750; not iPhone footage','plays':[{'label':p['label'],'code':p['battles'][0]['code'],'turns':p['battles'][0]['final_turn'],'inputs':p['key_inputs'],'experience_receipts':len(p['receipts']),'source_unchanged':p['source_unchanged'],'newborn_wait':all(a['turn']>a['born'] for a in p['phantom_actions'])} for p in plays],'boundaries':[{'label':r['label'],'normal_friends':r['ordinary_friendly_count'],'phantom_count':len(r['phantoms']),'professions':[{'id':u['class_id'],'class':u['class'],'hp':u['max_hp'],'resistance':u['resistance']} for u in r['phantoms']],'layout_errors':r['layout_errors'],'phone_errors':r['phone_errors']} for r in boundaries['records']],'clips':clips}
(review/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('Encoded',len(clips),'clips; screenshot metadata and verification saved')
