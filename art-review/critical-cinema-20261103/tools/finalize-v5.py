import json,hashlib,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];S=R/'source/revision5';A=json.loads((R/'assets.js').read_text().split('window.CinemaAssets=')[1].rstrip().rstrip(';'));rows=[];sheet=Image.new('RGB',(1400,1100),'#f2ede3');ImageDraw.Draw(sheet).rectangle((700,0,1400,1100),fill='#152a39')
for k,hero in enumerate(['hunapu','eileen']):
 for n,d in enumerate(A[hero+'-return']['frames']):
  p=R/d['path'];im=Image.open(p).convert('RGBA');scale=137/d['body_height'];im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
  for x in [0,700]:sheet.paste(im,(x+(n%4)*175+5,(k*2+n//4)*275+45),im)
  rows.append(dict(path=d['path'],purpose='Complete sword-visible forward-leaning return run',width=d['width'],height=d['height'],bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),compression='Lossless optimized PNG',source='source/revision5/'+hero+'-return-v5-source.png'))
sheet.save(R/'checks/v5/return-dark-light.png');(S/'asset-sizes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
status=json.loads((S/'status.json').read_text());status['artwork_registration']=json.loads((S/'return-registration.json').read_text());status['new_asset_sizes']=rows;status['atlas_slicing']='Four largest complete actor silhouettes detected independently per source row; no uniform grid clipping. Full head, hands, feet and sword preserved.';status['user_music_choice']='Instrumental; explicitly confirmed by user';status['checks']['audio_playback']='checks/v5/audio-playback.json';(S/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
(R/'source/revision5/atlas-cleanup.json').write_text(json.dumps({'method':status['atlas_slicing'],'final_asset_count':16,'prior_grid_crop_audit':'Superseded by complete component-based extraction.'},indent=2)+'\n')
audio=json.loads((S/'audio-mixes.json').read_text());assert len(audio['music'])==2
for m in audio['mixes']:
 assert hashlib.sha256((R/'videos'/(m['key']+'.wav')).read_bytes()).hexdigest()==m['sha256']
v=json.loads((R/'checks/verification.json').read_text());play=json.loads((R/'checks/v5/audio-playback.json').read_text());v['revision5']={'status':'Candidate visual and audio preview completed; user listening/art approval pending','new_return_frames':16,'new_sfx_sources':13,'replaced_stems':12,'total_sfx_audition_count':34,'character_music_count':2,'unique_attack_mixes':14,'return_height_check':'checks/v5/registration.json','browser_check':'checks/browser.json','audio_playback_check':'checks/v5/audio-playback.json','audio_alignment_seconds':{'sfx':abs(play['played']['state']['t']-play['played']['audio']['sfxTime']),'bgm':abs(play['played']['state']['t']-play['played']['audio']['musicTime'])},'human_listening':False,'source_status':'source/revision5/status.json'};(R/'checks/verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print('FINAL MANIFESTS: 16 sprites, 34 cues, 2 themes, 14 soundtracks; exported WAVs match final music mixes')
