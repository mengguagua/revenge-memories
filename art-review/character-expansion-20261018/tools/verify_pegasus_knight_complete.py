#!/usr/bin/env python3
"""Targeted class3 center, anatomy preservation, palette and playback checks."""
import ast,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,matched_export,relative,pack_frame
from export_gallery import render_frame
from export_knight_complete import export_one
from import_pegasus_knight_complete import REV,OUT,SRC,C,map_anchor
from import_sniper_complete import helper

def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def verify(export=False):
    d=json.loads((ROOT/'demos/gallery-data.json').read_text());b=json.loads((OUT/'baseline.json').read_text());pp={p['id']:p for p in d['profiles']};now={a['id']:a for a in d['actions']}
    assert len(d['profiles'])==97 and len(now)==775 and not d['validation']['structuralIssues']
    actions=[a for a in now.values()if a['profile'].startswith('professions-class-3-ally-')];assert len(actions)==20 and all(a['ready']for a in actions)
    changed={k for k,a in now.items()if a['contentDigest']!=b['actions'][k]['contentDigest']}
    assert changed=={a['id']for a in actions}
    for key,a in b['actions'].items():
        n=now[key]
        for field in['frames','fps','origin','contactTick','duration']:assert n.get(field)==a.get(field),(key,field)
    audits=json.loads((OUT/'native-reference-audit.json').read_text())
    for f in audits['assets']:assert file_hash(ROOT/f['path'])==f['sha256']
    assets=[];images={}
    for kind,count,size in [('tactical-walk',8,(128,96)),('tactical-idle',6,(96,96)),('battle',12,(320,384))]:
        files=sorted((OUT/f'ally/{kind}').glob('frame-*.png'));assert len(files)==count
        for path in files:
            im=Image.open(path).convert('RGBA');assert im.size==size
            colors={p[:3]for p in im.getdata()if p[3]};assert colors<=set(C)and set(im.getchannel('A').getdata())=={0,255}
            assert path.stat().st_size<50000
            images[kind,int(path.stem.split('-')[1])]=im
            assets.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'colors':len(colors),'binary_alpha':True,'bounds':im.getbbox()})
    headchecks=[]
    for kind,groups in [('tactical-idle',[[0,1,2]]),('tactical-walk',[[0,1],[2,3],[4,5],[6,7]])]:
        for ids in groups:
            mirrored=kind=='tactical-walk'and ids==[2,3]
            anchors=[map_anchor(images[kind,i].transpose(Image.Transpose.FLIP_LEFT_RIGHT)if mirrored else images[kind,i])for i in ids];assert len({tuple(x)for x in anchors})==1
            assert len({images[kind,i].tobytes()for i in ids})==len(ids)
            headchecks.append({'kind':kind,'slots':ids,'stationary_head_anchor':[127-anchors[0][0],anchors[0][1]]if mirrored else anchors[0],'exact_mirror_of_registered_left':mirrored,'wing_and_leg_poses_distinct':True})
    for i,j in[(2,6),(3,7)]:assert images['tactical-walk',i].tobytes()==images['tactical-walk',j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
    for i,j in enumerate([0,1,2,1,0,1]):assert images['tactical-idle',i].tobytes()==images['tactical-idle',j].tobytes()
    for i in[16,33]:assert images['battle',i].tobytes()==images['battle',0].tobytes()
    # Combat art only changes material indices: all alpha silhouettes stay in
    # the existing native-registered anatomical positions, including wing tips,
    # knees, hooves, arms and both ends of the held spear.
    for i,im in[(i,x)for(k,i),x in images.items()if k=='battle']:
        oldpath=(ROOT/'professions/class-3-ally/battle'/b['ally_battle']['frame_mapping'][str(i)]).resolve();old=Image.open(oldpath).convert('RGBA')
        assert old.getchannel('A').point(lambda a:255 if a>=128 else 0).tobytes()==im.getchannel('A').tobytes()
    projectile=Image.open(OUT/'ally/flying-javelin.png').convert('RGBA');native=Image.open(ROOT/'source-input/effects/3d558f7aa86343.png').convert('RGBA')
    assert projectile.getchannel('A').tobytes()==native.getchannel('A').tobytes()
    p=pp['professions-class-3-ally-battle'];effect=p['revisedEffects']['3d558f7aa86343']
    for k,v in d['effects']['3d558f7aa86343'].items():
        if k!='path':assert effect[k]==v
    schedules=[]
    for a in actions:
        if a['kind']=='attack':
            v=b['variants']['ally'][a['key']];assert a['frames']==[pack_frame(f)for f in v['frames']]and v['contact_count']==1
            schedules.append({'actor_id':'ally-pegasus-rider','source_action':a['key'],'class_action':'普通长枪攻击'if a['key']=='original_class_3_normal'else'投枪','program':v['source_program_address'],'release_tick':next((i for i,f in enumerate(a['frames'])if f['effects']),None),'contact_tick':a['contactTick'],'contact_count':1,'hero_card_binding':None,'note':'职业动画样板；不新增卡牌／觉醒特性或运行效果'})
    write(OUT/'action-effect-mapping.json',{'class_id':3,'scope':'ally only; enemy deferred by user','actions':schedules})
    manifest=json.loads((OUT/'asset-manifest.json').read_text())
    for a in manifest['assets']:assert file_hash(ROOT/a['path'])==a['sha256']and (ROOT/a['path']).stat().st_size==a['bytes']
    for name in['prepare_pegasus_knight_complete.py','import_pegasus_knight_complete.py','verify_pegasus_knight_complete.py']:ast.parse((ROOT/'tools'/name).read_text())
    captures=[]
    for a in actions:
        p=pp[a['profile']]
        ticks=([0,14,22]if a['key']=='idle-cycle'else[0,16]if a['kind']=='map_walk'else[])
        if a['key']=='original_class_3_normal':ticks=[next(n for n,f in enumerate(a['frames'])if f['frame']==i)for i in range(8)]+[a['contactTick']]
        if a['key']=='class_3_ally_javelin':ticks=[0,18,21,22,51,54]
        for tick in ticks:
            path=OUT/f'{a["key"]}-tick-{tick:03}.png';render_frame(d,p,a,tick,6,True,a['context']=='battle').save(path,optimize=True);captures.append(relative(path))
    report={'status':'assets_passed','profiles':3,'actions':20,'unrelated_actions_unchanged':755,'enemy_work_deferred_by_user':True,'palette':['172638','3976b5','e4e1c8','dda77d','b96369'],'native_frames_timing_positions_contacts_unchanged':True,'combat_alpha_geometry_unchanged':True,'stable_map_centers':headchecks,'asset_checks':assets,'offline_captures':captures,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
    write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','actions':20,'unchanged':755,'stationary_map_centers':True}),flush=True)
    if not export:return
    exports=[]
    for a in actions:
        exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
        if a['key']in['original_class_3_normal','class_3_ally_javelin']:exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
        print('Exported '+a['key'],flush=True)
    decoded=[]
    for e in exports:
        result=subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True)
        info=json.loads(result.stdout)['streams'][0];assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['frames']/e['fps'])<1/e['fps'];decoded.append({'path':e['video'],**info})
    for a in actions:
        for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
            path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
        assert a['video']and a['still']
    (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
    report.update(status='passed',decoded_videos=len(exports));write(OUT/'verification.json',report)
    write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded})
    print(json.dumps({'status':'passed','videos':len(exports)}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');a=p.parse_args();verify(a.export)
