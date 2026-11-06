import os,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for x in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[x]='1'
sys.path.insert(0,str(R.parents[1]/'actual/tools'));import review_audio_content as q
q.REPORT=R/'checks/v5/audio-semantic';tasks=[]
for t in json.loads((R/'source/revision5/audio-manifest.json').read_text())['stems']:
 if t['revision']==5:tasks.append({'id':t['key'],'kind':'short_weapon_or_lightning','paths':[str(R/t['path'])],'hashes':[t['sha256']],'prompt':'Describe the audible timbre and gesture. Is the onset sharp or soft, tail short or long? Identify any speech or musical melody, if actually audible. Under 40 words. Short sounds repeat with gaps.','max_tokens':80,'repeat_short':True})
for t in json.loads((R/'source/revision5/music.json').read_text())['tracks']:
 tasks.append({'id':'music-'+t['hero'],'kind':'original_music','paths':[str(R/t['path'])],'hashes':[t['sha256']],'prompt':'Describe ONLY the actually audible music: main instruments, rhythm speed, energy, any singing or speech. Is it fast intense battle music or slow sparse ambience? Be critical. Under 60 words.','max_tokens':100})
rows=q.run(tasks);q.dump(R/'checks/v5/audio-review.json',{'human_listening':False,'model':'local Qwen2-Audio7B4bit','results':rows})
