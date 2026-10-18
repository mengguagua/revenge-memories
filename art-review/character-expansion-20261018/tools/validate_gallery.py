#!/usr/bin/env python3
"""Check real sprite extents/paths/timelines without launching a visible application."""
from functools import lru_cache
import ast,json,math,subprocess
from pathlib import Path
from PIL import Image
from build_gallery import ROOT,build

@lru_cache(maxsize=1024)
def image(path):return Image.open(ROOT/path).convert('RGBA')

def box_at(im,xy,logical_size,flip):
    bb=im.getbbox()
    if not bb:return None
    sx,sy=logical_size[0]/im.width,logical_size[1]/im.height
    bb=[bb[0]*sx,bb[1]*sy,bb[2]*sx,bb[3]*sy]
    if flip:bb=[logical_size[0]-bb[2],bb[1],logical_size[0]-bb[0],bb[3]]
    return [bb[0]+xy[0],bb[1]+xy[1],bb[2]+xy[0],bb[3]+xy[1]]

def outside(box,view):
    return box and(box[0]<view[0]or box[1]<view[1]or box[2]>view[0]+view[2]or box[3]>view[1]+view[3])

def main():
    data=build();profiles={p['id']:p for p in data['profiles']};errors=[];checks=0
    for action in data['actions']:
        profile=profiles[action['profile']];fw,fh=profile['sourceFrameSize'];atlas=image(profile['sourceAtlas']);columns=profile['sourceColumns']
        for ti,row in enumerate(action['frames']):
            f=row['frame'];flip=(profile['context']=='battle'and profile.get('side')=='enemy')!=row.get('flip',False);offset=row.get('offset',[0,0]);origin=action['origin'];view=action.get('viewport',data['viewport'])
            at=[origin[i]+offset[i]-profile['anchor'][i]for i in range(2)];at[0]+=row.get('shake',0)
            if flip and f<profile['sourceOamCutoff']:at=[at[i]+profile['flipOriginOffset'][i]for i in range(2)]
            x=f%columns*fw;y=f//columns*fh
            candidates=[('original',atlas.crop((x,y,x+fw,y+fh)))]
            if str(f)in profile['newFrames']:candidates.append(('redraw',image(profile['newFrames'][str(f)])))
            for kind,im in candidates:
                box=box_at(im,at,[fw,fh],flip);checks+=1
                if outside(box,view):errors.append({'action':action['id'],'tick':ti,'kind':kind,'mode':'scene','bounds':box,'viewport':view})
                if action.get('closeCamera'):
                    camera=action['closeCamera'];cv=[origin[i]+offset[i]+camera['offset'][i]for i in range(2)]+camera['size'];checks+=1
                    if outside(box,cv):errors.append({'action':action['id'],'tick':ti,'kind':kind,'mode':'close','bounds':box,'viewport':cv})
            for effect in row.get('effects',[]):
                meta=data['effects'][effect['sprite']];at=[effect['position'][i]-meta['anchor'][i]for i in range(2)]
                if effect.get('flip'):at=[at[i]+meta.get('flip_origin_offset',[0,0])[i]for i in range(2)]
                box=box_at(image(meta['path']),at,meta['frame_size'],effect.get('flip',False));checks+=1
                if outside(box,view):errors.append({'action':action['id'],'tick':ti,'kind':'effect','mode':'scene','bounds':box,'viewport':view})
    for script in(ROOT/'tools').glob('*.py'):ast.parse(script.read_text())
    for script in[ROOT/'tools/gallery.js',ROOT/'gallery-data.js']:subprocess.run(['node','--check',str(script)],check=True,capture_output=True)
    report={'schema':1,'real_alpha_extent_checks':checks,'geometry_errors':errors,'structural_errors':data['validation']['structuralIssues'],
      'source_and_new_follow_same_coordinates':True,'close_camera_follows_both_axes':True,
      'missing_art_is_explicit':[{a['id']:a['missingFrames']}for a in data['actions']if not a['ready']],
      'javascript_syntax':'passed','python_syntax':'passed','browser_visual_inspection':'not performed; environment file-URL policy not bypassed',
      'visual_art_acceptance':'not inferred from these checks','pass':not errors and not data['validation']['structuralIssues']}
    (ROOT/'demos/validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pass':report['pass'],'checks':checks,'geometry_errors':len(errors),'pending':len(report['missing_art_is_explicit'])},ensure_ascii=False))
    if errors:print(json.dumps(errors[:12],ensure_ascii=False,indent=2))
    return 0 if report['pass']else 1

if __name__=='__main__':raise SystemExit(main())
