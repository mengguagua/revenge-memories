import json,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];rows=json.loads((R/'source/revision5/audio-mixes.json').read_text())['mixes']
for m in rows:
 dest=R/'videos'/(m['key']+'.mp4');tmp=R/'videos'/(m['key']+'-r5-remux.mp4');shutil.copy2(R/m['path'],R/'videos'/(m['key']+'.wav'))
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(dest),'-i',str(R/m['path']),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(tmp)],check=True);tmp.replace(dest)
print('REMUXED 14 final music and effect tracks',flush=True)
