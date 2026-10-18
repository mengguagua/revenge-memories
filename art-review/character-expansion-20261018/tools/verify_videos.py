#!/usr/bin/env python3
"""Verify saved videos against timelines using ffprobe; reuse unchanged verified bytes."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'gallery-data.js').read_text().split('=',1)[1].strip().rstrip(';'))
report_path=ROOT/'demos/video-verification.json'
old=json.loads(report_path.read_text())if report_path.exists()else{}
prior={r['path']:r for r in old.get('checks',[])}
checks=[];probed=0
for action in data['actions']:
 for view in ['video','closeVideo']:
  if not action.get(view):continue
  rel=action[view];path=ROOT/rel;digest=hashlib.sha256(path.read_bytes()).hexdigest()
  previous=prior.get(rel)
  if previous and previous.get('pass') and previous.get('sha256')==digest and previous.get('contentDigest')==action['contentDigest']:
   record=dict(previous);record['reused_prior_verification']=True
  else:
   result=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,duration,nb_read_frames','-of','json',str(path)],capture_output=True,text=True,check=True)
   observed=json.loads(result.stdout)['streams'][0];n=len(action['frames']);fps=float(Fraction(observed['avg_frame_rate']))
   passed=int(observed['nb_read_frames'])==n and abs(fps-action['fps'])<1e-5 and abs(float(observed['duration'])-n/action['fps'])<1/action['fps'] and observed['width']%2==0 and observed['height']%2==0
   record={'action':action['id'],'view':view,'path':rel,'size_bytes':path.stat().st_size,'expected_frames':n,'observed':observed,'pass':passed,'reused_prior_verification':False,'sha256':digest,'contentDigest':action['contentDigest']};probed+=1
  checks.append(record)
report={'all_pass':all(r['pass']for r in checks),'videos_checked':len(checks),'new_or_updated_probes':probed,'prior_checks_retained':len(checks)-probed,'checks':checks,'visual_inspection':'Offline composited stills reviewed separately; browser playback not performed.'}
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='checks'},ensure_ascii=False))
if not report['all_pass']:raise SystemExit(1)
