from pathlib import Path
import os, subprocess, time, json
root=Path(__file__).resolve().parent
marker=root/'captures/batch-0-590.json'
while not marker.exists():
    time.sleep(5)
report=json.loads(marker.read_text())
if not report['passed']:
    raise SystemExit('Main capture reported errors; inspect before continuing.')
env=os.environ.copy()
env['PIXELFX_INVENTORY']=str(root/'inventory-special.json')
env['CAMPAIGN_CAPTURE_LOG']='/private/tmp/pixelfx-full-special.log'
subprocess.run(['bash',str(root/'runtime-snapshot/tools/capture_campaign.sh'),str(root/'capture_batch.gd')],env=env,check=True)
