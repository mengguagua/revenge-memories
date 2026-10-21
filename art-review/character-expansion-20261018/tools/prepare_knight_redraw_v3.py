#!/usr/bin/env python3
"""Extract native references/specs for a full redraw; do not publish candidates."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from export_gallery import font as review_font

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'knight-redraw-v3-20261021'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def sheet(name,source,size,indices,columns,scale):
    atlas=Image.open(source).convert('RGBA');native_columns=atlas.width//size[0]
    cell=(size[0]*scale+24,size[1]*scale+52)
    board=Image.new('RGBA',(columns*cell[0],((len(indices)+columns-1)//columns)*cell[1]),(218,223,226,255))
    draw=ImageDraw.Draw(board);font=review_font(18)
    records=[]
    for n,i in enumerate(indices):
        x=i%native_columns*size[0];y=i//native_columns*size[1]
        frame=atlas.crop((x,y,x+size[0],y+size[1]))
        px=(n%columns)*cell[0]+12;py=(n//columns)*cell[1]+36
        draw.text((px,py-27),f'原作姿势 {i}',font=font,fill=(25,35,47,255))
        board.alpha_composite(frame.resize((size[0]*scale,size[1]*scale),Image.Resampling.NEAREST),(px,py))
        records.append({'frame':i,'native_bounds':list(frame.getbbox()) if frame.getbbox() else None,
            'source_crop':[x,y,x+size[0],y+size[1]],'sheet_cell':[px-12,py-36,px-12+cell[0],py-36+cell[1]]})
    p=OUT/'reference'/name;p.parent.mkdir(parents=True,exist_ok=True);board.save(p,optimize=True)
    return {'path':p.relative_to(ROOT).as_posix(),'source':source.relative_to(ROOT).as_posix(),
        'source_sha256':sha(source),'size':list(board.size),'bytes':p.stat().st_size,'frames':records}

def prepare():
    OUT.mkdir(exist_ok=True)
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        data=json.loads((ROOT/'demos/gallery-data.json').read_text())
        paths=[ROOT/f'professions/class-4-{side}/{kind}/frame_mapping.json' for side in ['ally','enemy'] for kind in ['maps','battle']]
        write(baseline,{'status':'preparation_only','mappings':{str(p.relative_to(ROOT)):json.loads(p.read_text()) for p in paths},
            'mapping_hashes':{str(p.relative_to(ROOT)):sha(p) for p in paths},
            'action_digests':{a['id']:a['contentDigest'] for a in data['actions']}})
    refs=[]
    refs.append(sheet('native-map-idle.png',ROOT/'source-input/legacy-assets/assets/original/graphics/map_units/class_4_ally.png',(24,24),[0,1,2],3,8))
    refs.append(sheet('native-map-up-down.png',ROOT/'source-input/corrected-tactical-walk/class-4-ally.png',(32,24),[0,1,4,5],2,6))
    atlas=ROOT/'source-input/original-motion/class-4.png'
    refs.append(sheet('native-battle-ground.png',atlas,(80,64),[0,1,2,3,4,5],3,4))
    refs.append(sheet('native-battle-special.png',atlas,(80,64),[6,7,8,9,41,43],3,4))
    timelines=[]
    for side,filename in [('ally','original-motion/full-original-motion.json'),('enemy','enemy-motion/full-enemy-motion.json')]:
        d=json.loads((ROOT/'source-input'/filename).read_text())
        for key,v in d['variants'].items():
            if str(v['source_class_id'])!='4':continue
            runs=[]
            for tick,row in enumerate(v['frames']):
                f=row['frame']
                if not runs or runs[-1]['frame']!=f:runs.append({'frame':f,'start':tick,'ticks':1})
                else:runs[-1]['ticks']+=1
            timelines.append({'side':side,'key':key,'ticks':len(v['frames']),'fps':v['native_fps'],
                'contact_tick':v['contact_tick'],'source_item_id':v['source_item_id'],
                'first_effect_tick':next((i for i,row in enumerate(v['frames']) if row['effects']),None),'pose_runs':runs,
                'native_rows_sha256':hashlib.sha256(json.dumps(v['frames'],sort_keys=True).encode()).hexdigest()})
    write(OUT/'native-reference-audit.json',{'status':'prepared_not_visually_reviewed','class_id':4,
        'display_name':'骑士','progression':['骑兵','骑士','大骑士'],'reference_sheets':refs,
        'map_idle':{'order':[0,1,2,1],'ticks':[14,8,14,8]},
        'map_walk':{'up':[0,1],'right':[2,3],'down':[4,5],'left':[6,7],'ticks_per_phase':16},
        'side_walk_whole_pose_reuse':{'left':[0,2],'right':'mirror of complete left poses'},'battle':timelines})
    spec={
      'status':'awaiting_permission_for_automatic_image_tool_attachments',
      'revision':'knight-redraw-v3-20261021','runtime_integrated':False,'gallery_updated':False,
      'requirements':{'center':'One stable saddle/torso reference per orientation; register complete poses. Preserve explicit original battle trajectory without adding image-to-image jitter.',
        'motion':'Native class4 pose order, repeats, flips, offsets, projectile release and hit timings.',
        'palette':'At most16 purposeful colors per side. Ally soft blue and ivory/white dominant, small warm skin and natural wood/steel. Enemy dark blue-violet with readable cool highlights. Slightly muted, never graywashed.',
        'anatomy':'Complete continuous rider, cloak, saddle, horse barrel and four anatomically joined legs in every pose. No horizontal body swaps, row compression, synthetic knee warps or disconnected armor.',
        'validation':'Inspect actual whole-pose sheets, full-speed and slow loops at intended size on dark/light backgrounds; numeric connectivity and timing checks supplement visual inspection.'},
      'batches':[
        {'id':'map-idle','references':['reference/native-map-idle.png'],'poses':[0,1,2],'purpose':'Three complete compact left-facing map poses. Reuse whole0/2 for side walk; mirror whole sprites for opposite facing.'},
        {'id':'map-up-down','references':['reference/native-map-up-down.png'],'poses':[0,1,4,5],'purpose':'Rear and front full horse+rider pairs; same helmet, clothing and palette as accepted new map idle.'},
        {'id':'battle-ground','references':['reference/native-battle-ground.png'],'poses':[0,1,2,3,4,5],'purpose':'Six full battle-scale ground/gallop poses; native leg positions and single continuous lance.'},
        {'id':'battle-special','references':['reference/native-battle-special.png'],'poses':[6,7,8,9,41,43],'purpose':'Rear/leap/return/throw/release. Native grip and empty-hand release. Projectile kept external.'}],
      'prohibited_shortcuts':['Republish the failed v1/v2 sprites as a new drawing','Crop and splice clothing from different poses','Replace actual visual inspection with pixel counts','Quietly use paid API generation','Claim automatic chat images are hidden or folded']}
    write(OUT/'redraw-spec.json',spec)
    (OUT/'README.md').write_text('''# 双方骑士完整重绘 · 准备稿

状态：已核对原作姿势与时间轴，尚未生成新美术，尚未替换「角色重绘 · 全动作对照」。

本轮按骑士编号4重新绘制完整姿势。7个独立地图姿势（待机3、向上2、向下2），左右行走直接复用并镜像完整待机0／2姿势；12个独立战斗姿势，双方分别映射自身原作槽位与时序。盟军蓝白与更多柔白，敌军蓝紫，少量降低饱和度，最多16个有明确材质用途的颜色。

完整人物与马匹在各帧独立成立，使用稳定鞍心／躯干参照点登记。原作战斗的冲锋与跃起保留；素材自身不额外跳位。逐帧目视核对马腿、腹部、鞍具、衣甲、手持枪及投枪释放，再以原速与慢速检查循环。像素连通和帧数通过不等于美术通过。

`reference/` 是只由原作图集提取的参考板；`native-reference-audit.json` 记录原作脚相和双方14条战斗时间轴；`redraw-spec.json` 记录四组重绘范围、配色与验收方法。旧稿和当前对照页保持在原处，避免把尚未完成的重绘发布成新结果。

当前等待用户明确允许本轮内置绘图／看图工具可能自动附图。项目AGENTS.md默认禁止工具预览与回合记录附图，不能把模型切换理解为取消该限制，也不能声称已经隐藏或折叠。
''')
    print(json.dumps({'status':'prepared_only','references':len(refs),'battle_variants':len(timelines),'map_unique_poses':7,'battle_unique_poses':12,'gallery_updated':False}))

if __name__=='__main__':prepare()
