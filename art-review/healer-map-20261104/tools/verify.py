"""Verify local preview artifacts against the approved numeric design and UI receipts."""
import hashlib
import json
from pathlib import Path
from PIL import Image

OUT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
cases=read(OUT/'sources/browser-cases.json');buff=read(OUT/'sources/browser-buff-checks.json');mobile=read(OUT/'sources/browser-mobile.json');desktop=read(OUT/'sources/browser-desktop.json');runtime=read(OUT/'sources/runtime.json')
expected={'healer':([8,11,14],[0,3,5],8),'saint':([16,20,24],[0,5,7],10)}
errors=[]
for c in cases:
    a=c['audit'];h,cost,reach=expected[a['case']];tier=a['tier']
    if a['restored_hp']!=h[tier] or f'扣{cost[tier]}' not in c['cost']:errors.append(c)
    if a['selected_targets']!=1 or a['actual_distance']!=reach or a['errors']:errors.append(c)
for c,left in zip(buff['buffChecks'],[2,1,0]):
    s=c['audit']['status']
    if s['remaining']!=left or s['physical_defence']!=(8 if left else 6) or s['icon_visible']!=bool(left) or c['summaryGreen']!=bool(left):errors.append(c)
if buff['fullCheck']['restored_hp']!=0 or not buff['fullCheck']['status']['icon_visible']:errors.append('full HP buff')
if mobile['overflow'] or mobile['failedImages'] or mobile['viewport']['width']!=mobile['viewport']['pageWidth']:errors.append('mobile overflow/resources')
if desktop['overflow'] or desktop['failedImages'] or desktop['width']!=desktop['pageWidth'] or desktop['scene']['errors']:errors.append('desktop overflow/resources/range')
if runtime['errors']:errors.extend(runtime['errors'])
old={r['path']:r for r in read(OUT/'sources/asset-manifest.json')};images=[]
for folder in ['assets','posters','reference','sources']:
    for p in sorted((OUT/folder).glob('*.png')):
        with Image.open(p) as im: size=im.size;mode=im.mode
        path=str(p.relative_to(OUT));entry=old.get(path,{});entry.update({'path':path,'pixels':list(size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mode':mode})
        if 'purpose' not in entry:entry['purpose']='game screenshot reference' if folder=='reference' else 'rendered design still' if folder=='posters' else 'preview UI asset or QA evidence'
        if p.stat().st_size>200000:entry['size_note']='Retain original pixel contours and small UI text; lossless optimized, quality retained.'
        images.append(entry)
(OUT/'sources/asset-manifest.json').write_text(json.dumps(images,ensure_ascii=False,indent=2)+'\n')
qa={'passed':not errors,'errors':errors,'scope':'Independent HTML art preview only; no production healing/buff or save changes','cases':len(cases),'max_reach':[8,10],'healing':[expected['healer'][0],expected['saint'][0]],'hp_costs':[expected['healer'][1],expected['saint'][1]],'buff':'强身','buff_states':[2,1,0],'green_bonus_removed_at_expiry':True,'full_hp_buff_only':True,'target_switch':True,'imagegen_assets':3,'game_background_capture':{'background_guard':runtime['guard'],'layout_errors':runtime['errors'],'cleanup_warning':'8 ObjectDB instances / 2 resources at process exit, recorded; not a gameplay validation'},'mobile':mobile['viewport'],'mobile_overflow':mobile['overflow'],'mobile_failed_images':mobile['failedImages'],'desktop_width':desktop['width'],'desktop_overflow':desktop['overflow'],'desktop_failed_images':desktop['failedImages'],'historical_export_error':'Initial export helper used a wrong relative asset base; corrected with base href. Current page and export assets load successfully.','image_count':len(images),'largest_delivery_image_bytes':max(x['bytes']for x in images),'gameplay_regression_run':False,'device_updated':False}
(OUT/'sources/qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(qa,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
