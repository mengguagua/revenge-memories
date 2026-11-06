"""Local waveform-conditioned QA; never plays audio through speakers."""
import sys,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for key in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','PYTHONDONTWRITEBYTECODE']:os.environ[key]='1'
sys.path.insert(0,str(ROOT.parents[1]/'actual/tools'))
import review_audio_content as reviewer
reviewer.REPORT=ROOT/'checks/v4/audio-semantic'
manifest=json.loads((ROOT/'source/revision4/audio-manifest.json').read_text())
tasks=[{'id':s['key'],'kind':'new_cinema_sfx_blind','paths':[str(ROOT/s['path'])],'hashes':[s['sha256']],'prompt':'Describe only the audible timbre and sound gesture. Say whether intelligible speech, singing, or a musical melody is audible. Do not infer a visual scene or named game. Under 35 words. Short sounds may repeat with silent gaps.','max_tokens':65,'repeat_short':True} for s in manifest['stems']]
rows=reviewer.run(tasks)
reviewer.dump(ROOT/'checks/v4/audio-review.json',{'local_model':'Qwen2-Audio7B4bit','human_listening':False,'scope':'Waveform-conditioned semantic evidence, alongside level and decode checks; not a human listening certificate.','results':rows})
