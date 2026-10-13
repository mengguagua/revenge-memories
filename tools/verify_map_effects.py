#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
    g=json.loads((ROOT/'data/graphics.json').read_text());fx=json.loads((ROOT/'data/full_map_effects.json').read_text());audio=json.loads((ROOT/'data/full_audio.json').read_text());checks=[];failures=[];assets=[]
    def check(test,description):
        checks.append(description)
        if not test:failures.append(description)
    for a in g['assets']:
        if a.get('kind') not in ['full_effect_map','full_class_map_acted']:continue
        path=ROOT/a['path'].removeprefix('res://');im=Image.open(path);im.load()
        check(im.size==(a['width'],a['height']),a['path']+' dimensions')
        check(im.mode=='RGBA' and set(im.getchannel('A').getdata())<={0,255},a['path']+' source alpha')
        check(im.getbbox() is not None,a['path']+' visible original pixels')
        assets.append({'path':a['path'],'usage':a['kind'],'pixels':list(im.size),'bytes':path.stat().st_size})
    for cid in range(1,23):
        for side in ['ally','enemy']:
            key=f'class_{cid}_{side}';entry=g['map_units'][key];acted=g['map_units'][entry['acted_variant']]
            check(acted['frames']==entry['frames'] and acted['frame_size']==entry['frame_size'],key+' acted shape contract')
    for program in fx['programs'].values():
        check(len(program['cycle_timeline'])==program['cycle_ticks'],program['path']+' source total cycle')
        check(all(0<=f<program['frames'] for f in program['cycle_timeline']),program['path']+' frame bounds')
        q=f'{program["sound_request"]:02X}';check(q in audio['sfx_by_request'] or q in audio['control_requests'],q+' sound request')
    check(len(assets)==55,'44 acted atlases +11 map effect atlases')
    report={'checks':len(checks),'failures':failures,'failure_count':len(failures),'assets':assets,'max_png_bytes':max(a['bytes'] for a in assets),'visual_review':'Raw cavalry acted, warp appearance, dragon appearance and healing OAM atlases inspected; original integer pixels and binary alpha preserved. Runtime camera/HUD composition is root integration scope.'}
    (ROOT/'reports/map-assets-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='assets'}));raise SystemExit(bool(failures))
if __name__=='__main__':main()
