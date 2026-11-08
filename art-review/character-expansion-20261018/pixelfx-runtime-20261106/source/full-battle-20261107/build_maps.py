from pathlib import Path
import json
from PIL import Image
import build_gallery as G

def clean_flash(d,folder):
    """Reverse the recorded RGB emphasis on the same rendered frame (<=1 RGB step).
    The phone controls are outside the modulated game viewport and stay exact.
    """
    paths=[];by_image={}
    for f in d['frames']:
        mode=f.get('modulate',[1,1,1,1])
        if f['image'] in by_image and by_image[f['image']]!=mode:raise ValueError('Ambiguous flash state')
        by_image[f['image']]=mode
    opened={};images=[]
    for idx in range(d['unique_frames']):
        p=folder/d['atlases']['current'][idx//16]
        if p not in opened:opened[p]=Image.open(p).convert('RGBA')
        cell=idx%16;x=cell%4*592;y=cell//4*240;im=opened[p].crop((x,y,x+592,y+240));mode=by_image[idx]
        if any(v<.99 for v in mode[:3]):
            part=im.crop((116,0,522,240));channels=list(part.split())
            for k in range(3):channels[k]=channels[k].point([min(255,round(v/mode[k])) for v in range(256)])
            im.paste(Image.merge('RGBA',channels),(116,0))
        images.append(im)
    for start in range(0,len(images),16):
        group=images[start:start+16];atlas=Image.new('RGBA',(592*4,240*((len(group)+3)//4)))
        for i,im in enumerate(group):atlas.paste(im,((i%4)*592,(i//4)*240))
        p=folder/f'clean-flash-{start//16:03d}.png';atlas.save(p,compress_level=6);paths.append(p.name)
    d['atlases']['clean']=paths
    factors=[list(v) for v in sorted({tuple(f.get('modulate',[1,1,1,1])[:3]) for f in d['frames']})]
    (folder/'clean-flash-method.json').write_text(json.dumps({'method':'Inverse of the frame-recorded RGB emphasis, restricted to the game viewport. Current/reference images remain untouched.','recorded_factors':factors,'rounding_bound_per_channel':1,'frames':len(images)},indent=2))

catalog=[]
for path in sorted((G.ROOT/'map-captures').glob('*/capture.json')):
    d=json.loads(path.read_text());j=d['job'];rows=G.make_timeline(d['frames'],d['duration']);key=d['id']
    if j.get('suppress_flash'):clean_flash(d,path.parent)
    layers=G.compact_layers(d,path.parent,['current','clean'] if j.get('suppress_flash') else ['current']);plan=[];contact=d['contact_time']
    actor=d.get('receipt',{}).get('actor_unit',{})
    if actor.get('id')=='eileen':j['profile']='eileen_promoted' if actor.get('hero_profession')=='light_guide' else 'eileen'
    if actor.get('id')=='hunapu':j['profile']='23_ally' if actor.get('hero_profession')=='dawn_warrior' else '21_ally'
    if j.get('bow'):j['label']+='（持弓）';j['move']+='（持弓）'
    treatment=''
    if j['kind']=='hero-map':
        for target in j['targets']:
            track=[]
            for r in rows:
                pt=next((p['at'] for p in r['points'] if p['id']==target['id']),None)
                track.append([pt[0],pt[1]+2] if pt else None)
            plan.append({'effect':'map-heal' if j['support'] else 'map-hit','start':target['time'],'track':track,'flip':False,'alpha':.9})
        contact=min(t['time'] for t in j['targets'])
        treatment=('保留治疗者的施法动作、实际恢复量和强身反馈，增加一圈轻微上升的浅绿微光。' if j['support'] else '保留原范围、所有真实受击目标与原动作；每个实际命中点补一个小型像素亮点，不增加攻击次数。')
    else:
        segments=[];last_cell=None;active=False
        for f in d['frames']:
            if f['map_active'] and (not active or f['map_cell']!=last_cell):segments.append((f['t'],f['map_cell']))
            active=f['map_active'];last_cell=f['map_cell']
        for start,cell in segments:
            track=[]
            last=None
            for f in rows:
                if f['map_active'] and f['map_cell']==cell:last=f['effect_point']
                track.append([last[0],last[1]+2] if last else None)
            effect='map-heal' if int(j['program'])==10 else 'map-hit' if int(j['program'])==9 else 'map-warp'
            plan.append({'effect':effect,'start':start,'track':track,'flip':False,'alpha':.85})
        if segments:contact=segments[0][0]
        treatment=('原单位离场与落点出现保持同步，两处各补一圈细小紫灰微光。' if j['kind']=='teleport' else '原地震与地图震动保持一致，只在原伤害反馈开始时补上微小接触亮点。' if j['kind']=='quake' else '保留原地图恢复反馈，增加一圈清楚但克制的绿色微光。' if int(j['program'])==10 else '原地图伤害表现上增加小型像素火花。' if int(j['program'])==9 else '保留该单位实际使用的入场／退场图形程序，补上短暂收束的紫灰微光。')
        if j.get('suppress_flash'):
            flash=next(f['t'] for f in d['frames'] if any(v<.99 for v in f.get('modulate',[1,1,1])[:3]));track=[]
            for r in rows:
                pt=next((p['at'] for p in r['points'] if p['id']==j['caster']),None);track.append([pt[0],pt[1]+2] if pt else None)
            plan.insert(0,{'effect':'map-warp','start':flash,'track':track,'alpha':.9,'flip':False})
            treatment='用施法者与目标附近的紫灰短光环替换整屏蓝／红交替强调。保留原施法结果、所有实际入场／退场单位与原时间顺序。'
    c={'key':key,'title':j['label'],'subtitle':'地图实际布局 · '+('治疗与强身' if j.get('support') else '范围攻击' if j['kind']=='hero-map' else '地图反馈程序'),'family':'map','group':'地图技能','profile':j['profile'],'side':j['side'],'move':j['move'],'far':'','heavy':False,'reaction':'','duration':d['duration'],'contact':contact,'fps':60,'size':[592,240],'crop':[116,0,406,240],'field':[116,0,406,240],'timeline':[r['image'] for r in rows],'atlasFrames':16,'atlasCols':4,'atlases':layers['paths'],'layerSpecs':layers['spec'],'layerMap':layers['map'],'fxPlan':plan,'treatment':treatment,'source':{'program':'hero_map_animation/'+j.get('key',key) if j['kind']=='hero-map' else 'map_effects/program_'+str(j['program']),'contacts':j.get('contacts',0),'engine':'当前 Godot 手机地图渲染器 · 受控测试配置 · '+('按实际 MAP 结算回执采样' if j['kind']=='hero-map' else '调用原地图反馈程序，非新增战斗结算')},'actionTime':max(0,contact-.15),'impactTime':min(d['duration'],contact+.1)}
    pts=[p['at'][0] for r in rows for p in r['points']]
    if pts:
        center=(min(pts)+max(pts))/2;c['crop']=[round(max(116,min(266,center-128))),0,256,240]
    if j['kind']=='hero-map':c['source']['targets']=j['targets']
    c['atlasFrames']=layers.get('atlasFrames',16);c['atlasCols']=layers.get('atlasCols',4)
    if j.get('suppress_flash'):
        c['suppressFlash']=True;c['source']['engine']='当前 Godot 支援法术规则生成回执，原地图控制器完整播放；候选侧仅替换画面强调方式。'
        review_flash=next(f['t'] for f in d['frames'] if f['t']>=flash+.14 and any(v<.99 for v in f.get('modulate',[1,1,1])[:3]))
        c['actionTime']=G.math.ceil(review_flash*60)/60
        c['source']['facts']=['施法者生命 '+str(j['caster_hp_before'])+' → '+str(j['caster_hp_after']),'实际入场 '+str(len(d['receipt'].get('spawned',[])))+' 名' if d['receipt'].get('spawned') else '实际退场 '+str(len(d['receipt'].get('changed',[])))+' 名']
    c['impactTime']=contact+(.26 if j.get('support') or int(j.get('program',0))==10 else .035 if j['kind']=='hero-map' or int(j.get('program',0))==9 else .18)
    (G.OUT/'cases'/f'{key}.js').write_text('window.PIXELFX_CASES=window.PIXELFX_CASES||{};window.PIXELFX_CASES['+json.dumps(key)+']='+json.dumps(c,ensure_ascii=False,separators=(',',':'))+';\n')
    catalog.append({k:c[k] for k in ['key','title','subtitle','family','group','profile','side','move','far','heavy','reaction','duration']})
(G.ROOT/'map-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
print('Map cases',len(catalog))
