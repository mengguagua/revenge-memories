from pathlib import Path
from PIL import Image, ImageChops
import json, math, os, shutil, collections, hashlib, statistics

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent.parent
OUT=BASE/'full-battle-20261107'
FPS=60
FX=json.loads((OUT/'assets/fx/manifest.json').read_text())['effects']
ART=json.loads((ROOT/'runtime-snapshot/data/reviewed_animations.json').read_text())['battle']
FAMILY={'sword':'剑击','lance':'枪击','javelin':'投枪','archery':'弓箭','lightning-sword':'雷剑','magic':'法术','support':'治疗与支援','monster':'魔物固有攻击','mechanical':'机械怪','reaction':'受击／闪避／退场','cinema':'主角必杀','map':'地图技能','approved':'已有对照'}
WEAPONS={1:'弓箭',4:'投枪',14:'魔剑',15:'雷剑',22:'银弓',23:'火球',24:'雷电',25:'诸神黄昏',26:'圣光',27:'风刃',28:'箭雨',29:'光环',30:'盖亚',31:'鬼火',32:'史莱姆',33:'死亡',34:'美杜莎',35:'恢复',36:'全体恢复',37:'召唤',38:'眼光',39:'眼球',40:'恢复',41:'远程恢复',42:'吸血',43:'传送',44:'全体恢复',45:'幻影',46:'驱邪',1001:'裂石爪',1002:'碎岩喷吐',1003:'骸颚撕咬',1004:'蚀息',1005:'翼喙重击',1006:'日冠聚光',1007:'机械掌击',1008:'水炮',1009:'重臂锤击'}
TREATMENTS={
 'hit':'命中处出现短促的暖白火花，少量碎屑沿攻击方向落下。',
 'fire':'原火焰释放与飞行保持一致，命中后补上琥珀色焰舌和迅速冷却的余烬。',
 'holy':'在原圣光结束处补一束细小亮芒，光屑逐渐散开，不新增治疗效果。',
 'wind':'风刃命中后散成三道灰青色气流，留下很短的空气涟漪。',
 'lightning':'原落雷保留，接触处出现细小电弧和快速熄灭的余电。',
 'void':'暗色能量在命中处短暂收束，再散成少量紫灰碎光。',
 'slime':'保留原覆盖动作，补上低饱和绿色溅滴；不增加中毒等状态。',
 'drain':'吸血接触处加入暗红碎光，生命变化仍使用原动画的真实结算。',
 'heal':'恢复结算时，脚下浅绿光瓣展开，细环上升后淡出。',
 'warp':'在原传送表现周围补上收拢的细环和向上消散的微光。',
 'stone':'石质接触点增加少量棱角碎片，沿重力方向落下。',
 'blunt':'重击保留原来的身体动作，增加小范围冲击形状与落尘。'
}

def read_js(path):
    s=path.read_text();return json.loads(s[s.index('=')+1:].rstrip(';\n'))

def link(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():return
    os.link(src,dst)

def compact_layers(capture,folder,layers):
    """Keep exact pixels, deduplicate the mostly-static UI separately from motion."""
    dest=OUT/'assets/runtime'/capture['id'];dest.mkdir(parents=True,exist_ok=True)
    cache=dest/'layers.json';digest=hashlib.sha256((folder/'capture.json').read_bytes()).hexdigest()
    wide=capture['job']['family'] in ['cinema','map'];revision=3 if wide else 2;cells=2 if wide else 16;columns=2 if wide else 4
    if cache.exists():
        saved=json.loads(cache.read_text())
        if saved.get('sourceHash')==digest and saved.get('revision')==revision and saved.get('requested')==layers:return saved
    rect=(116,0,522,240) if wide else (191,0,447,128)
    spec={};mapping={};paths={};frames={};seen={}
    for layer in layers+['plate']:
        w,h=(592,240) if layer=='plate' else (rect[2]-rect[0],rect[3]-rect[1]);x,y=(0,0) if layer=='plate' else rect[:2]
        spec[layer]={'size':[w,h],'at':[x,y]};mapping[layer]=[];frames[layer]=[];seen[layer]={}
    opened={}
    for idx in range(capture['unique_frames']):
        images={}
        for layer in layers:
            p=folder/capture['atlases'][layer][idx//16]
            if p not in opened:opened[p]=Image.open(p).convert('RGBA')
            x=idx%16%4*592;y=idx%16//4*240;images[layer]=opened[p].crop((x,y,x+592,y+240))
        plate=images['current'].copy();plate.paste((0,0,0,0),rect)
        for layer in layers+['plate']:
            im=plate if layer=='plate' else images[layer].crop(rect)
            sha=hashlib.sha256(im.tobytes()).digest()
            if sha not in seen[layer]:seen[layer][sha]=len(frames[layer]);frames[layer].append(im)
            mapping[layer].append(seen[layer][sha])
        if idx%16==15:opened.clear()
    for layer,ims in frames.items():
        paths[layer]=[];w,h=spec[layer]['size']
        for start in range(0,len(ims),cells):
            group=ims[start:start+cells];atlas=Image.new('RGBA',(w*columns,h*math.ceil(len(group)/columns)))
            for k,im in enumerate(group):atlas.paste(im,((k%columns)*w,(k//columns)*h))
            p=dest/f'{layer}-compact-{start//cells:03d}.png';atlas.save(p,compress_level=6);paths[layer].append(str(p.relative_to(OUT)))
    saved={'revision':revision,'sourceHash':digest,'requested':layers,'spec':spec,'map':mapping,'paths':paths,'unique':{k:len(v) for k,v in frames.items()},'atlasFrames':cells,'atlasCols':columns}
    cache.write_text(json.dumps(saved,separators=(',',':')));return saved

def frame_at(frames,t):
    index=0
    while index+1<len(frames) and frames[index+1]['t']<=t+1e-8:index+=1
    return frames[index]

def make_timeline(frames,duration):
    rows=[];idx=0
    for n in range(math.ceil(duration*FPS)+1):
        t=n/FPS
        while idx+1<len(frames) and frames[idx+1]['t']<=t+1e-8:idx+=1
        rows.append(frames[idx])
    return rows

def projectile_boxes(capture,folder):
    cache={};opened={}
    for f in capture['frames']:
        if not f['effects'] or f['t']>=capture['contact_time']:continue
        idx=int(f['image'])
        if idx in cache:continue
        tile=[]
        for layer in ['current','clean']:
            path=folder/capture['atlases'][layer][idx//16]
            if path not in opened:opened[path]=Image.open(path).convert('RGB')
            x=idx%16%4*592;y=idx%16//4*240
            tile.append(opened[path].crop((x+191,y,x+447,y+128)))
        rgb=ImageChops.difference(*tile).split()
        mask=ImageChops.lighter(ImageChops.lighter(rgb[0],rgb[1]),rgb[2]).point(lambda p:255 if p>14 else 0)
        box=mask.getbbox()
        cache[idx]=[box[0]+191,box[1],box[2]+191,box[3]] if box else None
    return cache

def target_height(job):
    target=job['target'];key=str(int(target['class_id']))+('_enemy' if target['side']=='enemy' else '_ally')
    if target.get('id')=='eileen':key='eileen_promoted' if target.get('promoted') else 'eileen'
    g=job.get('target_graphic') or ART.get(key)
    if not g:return 40
    p=ROOT/'runtime-snapshot'/g['path'].removeprefix('res://')
    try:
        im=Image.open(p).convert('RGBA');w,h=map(int,g['frame_size']);f=int(g['sequences']['idle'][0]);cols=int(g.get('columns',g.get('frames',1)))
        box=im.crop((f%cols*w,f//cols*h,f%cols*w+w,f//cols*h+h)).getbbox()
        return (box[3]-box[1])*(float(g['logical_frame_size'][1])/h if 'logical_frame_size' in g else 1/float(g.get('native_density',1))) if box else 40
    except (OSError,KeyError):return 40

def target_offset(capture,folder,which='target'):
    """Measure the actual idle silhouette; roots differ between the two armies."""
    f=capture['frames'][0];tx,ty=f[which];ax=f['actor' if which=='target' else 'target'][0]
    height=target_height(capture['job'] if which=='target' else {'target':capture['job']['actor'],'target_graphic':capture['job'].get('graphic')});radius=min(66,max(30,abs(tx-ax)/2-3))
    x0=max(192,int(tx-radius));x1=min(446,int(tx+radius));y0=max(5,int(ty-height-6));y1=126
    im=Image.open(folder/capture['atlases']['current'][0]).convert('RGB').crop((0,0,592,240));tile=im.crop((x0,y0,x1,y1));back=im.crop((191,y0,192,y1)).resize(tile.size,Image.Resampling.NEAREST)
    r,g,b=ImageChops.difference(tile,back).split();mask=ImageChops.lighter(ImageChops.lighter(r,g),b);coords=[(i%tile.width+x0,i//tile.width+y0) for i,v in enumerate(mask.getdata()) if v>24]
    if len(coords)<12:return [0,-max(20,height*.48)]
    return [statistics.median(p[0] for p in coords)-tx,statistics.median(p[1] for p in coords)-ty]

def effect_style(job):
    w=int(job['weapon']);f=job['family']
    if int(job['event'].get('self_damage',0))>0:return 'void'
    if f=='support':return 'warp' if w==43 else 'heal'
    if f=='monster' and int(job['class_id'])==17 and w==0:return 'hit'
    if f=='monster' and int(job['class_id'])==18 and w==0:return 'void'
    if w==15:return 'lightning'
    return {23:'fire',24:'lightning',25:'fire',26:'holy',27:'wind',28:'wind',29:'holy',30:'stone',31:'void',32:'slime',33:'void',34:'void',38:'void',39:'void',42:'drain',1001:'stone',1002:'stone',1003:'blunt',1004:'void',1005:'blunt',1006:'holy',1007:'blunt',1008:'water',1009:'blunt'}.get(w,'blunt' if f=='monster' else 'hit')

def build_case(path):
    d=json.loads(path.read_text());j=d['job'];key=d['id'];folder=path.parent;contact=d['contact_time'];rows=make_timeline(d['frames'],d['duration']);event=j['event'];family=j['family'];style=effect_style(j);sample=frame_at(d['frames'],contact)
    actor=sample['actor'];target=sample['target'];direction=1 if target[0]>actor[0] else -1;flip=direction<0
    offset=target_offset(d,folder);body_x=target[0]+offset[0]
    impact_y=max(64,min(111,target[1]+offset[1]));impact_x=max(203,min(435,body_x-direction*2))
    if style=='wind':impact_y=min(107,impact_y)
    if int(event.get('self_damage',0))>0:
        own=target_offset(d,folder,'actor');impact_x=actor[0]+own[0];impact_y=max(64,min(111,actor[1]+own[1]))
    anchor=[impact_x,impact_y+(0 if style in ['core','lightning'] else 16 if style=='hit' else 20)]
    if style in ['heal','slime','water','warp']:anchor=[body_x,120]
    if style=='blunt':anchor=[impact_x,min(127,impact_y+18)]
    if style=='hit':anchor[1]=min(127,anchor[1])
    if style in ['heal','slime','water','warp']:flip=False
    plan=[{'effect':style,'start':contact-(.05 if style=='lightning' else .26 if style=='heal' else 0),'anchor':anchor,'flip':flip,'alpha':.86}]
    treatment=TREATMENTS.get(style,'沿用已确认的低饱和灰青水色与落点水冠。')
    blade=(family=='sword' or (family=='monster' and int(j['class_id'])==17 and int(j['weapon'])==0)) and not int(event.get('self_damage',0))
    if blade:
        plan.insert(0,{'effect':'slash','start':contact-.06,'anchor':actor,'flip':direction<0,'alpha':.82})
        treatment='真实挥剑动作上增加灰青刀光；快速前冲时留下两道很淡的角色残影。'+treatment
    if family=='lance':
        plan=[{'effect':'thrust','start':contact-.07,'anchor':[impact_x-direction*32,impact_y+20],'flip':direction<0,'alpha':.85}]
        treatment='枪尖的前刺方向用短促亮线强调，命中处只有一次穿刺火花。'
    if family=='mechanical':treatment='机械本体的起手、重量和破损姿态保持一致。'+treatment
    reaction=j.get('reaction','')
    if reaction=='miss':
        plan=[{'effect':'dust','start':contact+.04,'anchor':[target[0],124],'flip':False,'alpha':.65}]
        treatment='闪避动作脚下增加轻微尾尘；不出现命中光点，也不扣除生命。'
    elif reaction=='exit':treatment+='退场仍使用该角色当前的倒地／消失动作，不增加灵魂或爆炸。'
    if int(event.get('reflection_damage',0))>0:
        reflective=next((f for f in d['frames'] if '反伤' in f.get('message','')),None)
        if reflective is not None:
            own=target_offset(d,folder,'actor');plan.append({'effect':'core','start':reflective['t']-.05,'anchor':[reflective['actor'][0]+own[0],reflective['actor'][1]+own[1]],'flip':False,'alpha':.7})
            treatment+='核心反伤的细小余电只在实际反伤反馈时出现。'
    move=WEAPONS.get(int(j['weapon']),FAMILY.get(family,'攻击'))
    if family=='monster' and int(j['weapon'])==0:move='剑击' if int(j['class_id'])==17 else '普通攻击'
    if family=='cinema' and int(j['weapon'])==0:move='剑击'
    if family=='reaction':move={'hit':'受击','miss':'闪避','exit':'退场'}.get(reaction,'受击')
    title=j.get('label') or str(j['actor'].get('name_zh','角色'))+' · '+move
    if family=='cinema':title+=' · '+move
    if j['profile'] in ['eileen_promoted','23_ally'] and family!='cinema':title=title.replace(' · ','（进阶） · ',1)
    context=('敌方' if j['side']=='enemy' else '己方')+' · '+('远距布局·己方侧' if j.get('far')=='ally' else '远距布局·敌方侧' if j.get('far')=='enemy' else '常规布局')+(' · 骑士目标' if j.get('heavy') else '')
    c={'key':key,'title':title,'subtitle':context,'family':family,'group':FAMILY.get(family,family),'profile':j['profile'],'side':j['side'],'move':move,'far':j.get('far',''),'heavy':j.get('heavy',False),'reaction':reaction,'duration':d['duration'],'contact':contact,'fps':FPS,'size':[592,240],'crop':[191,0,256,240],'field':[191,0,256,128],'timeline':[int(r['image']) for r in rows],'atlasFrames':16,'atlasCols':4,'atlases':{},'fxPlan':plan,'treatment':treatment,'source':{'program':j['program'],'contacts':d['contact_calls'],'event':event,'actor':j['actor'].get('name_zh'),'target':j['target'].get('name_zh'),'engine':'Godot 后台渲染 · 当前生产控制器 · 受控测试配置'},'actionTime':max(0,contact-.18),'impactTime':min(d['duration'],contact+.08)}
    c['impactTime']=contact+{'hit':1/60,'blunt':1/60,'holy':.035,'fire':.11,'heal':.14,'wind':.15,'lightning':.02,'slime':.15}.get(style,.1)
    if family=='reaction':c['side']='enemy' if str(j['profile']).endswith('_enemy') else 'ally';c['subtitle']=('敌方' if c['side']=='enemy' else '己方')+' · 该角色的实际'+move+'动作'
    layers=['current']+(['clean'] if family in ['archery','cinema'] else [])+(['actor'] if blade else [])
    compact=compact_layers(d,folder,layers);c['atlases']=compact['paths'];c['layerSpecs']=compact['spec'];c['layerMap']=compact['map'];c['atlasFrames']=compact.get('atlasFrames',16);c['atlasCols']=compact.get('atlasCols',4)
    if family in ['archery','javelin']:
        boxes=projectile_boxes(d,folder);anchors=[];flight=[]
        for r in rows:
            box=boxes.get(int(r['image'])) if r['effects'] and r['t']<contact else None
            point=None
            if box:
                point=[box[2]-1 if direction>0 else box[0],round((box[1]+box[3]-1)/2)] if family=='archery' else [box[0] if direction>0 else box[2]-1,round((box[1]+box[3]-1)/2)]
            anchors.append(point)
        c['projectile']={'kind':'arrow' if family=='archery' else 'wake','anchors':anchors,'flip':direction<0}
        flight=[i/FPS for i,p in enumerate(anchors) if p]
        if flight:c['actionTime']=(flight[0]+flight[-1])/2;c['projectile']['start']=flight[0]
        treatment=('按原箭矢的实际尖端轨迹替换为 PixelFX 木杆、箭镞和羽尾，画面始终只有一支箭。' if family=='archery' else '原投枪保持完整，仅在枪尾加少量灰青风迹；不增加第二支投枪。')+TREATMENTS['hit'];c['treatment']=treatment
    if blade and 'actor' in c['atlases']:c['actorPositions']=[r['actor'] for r in rows]
    if family=='cinema':
        tracks=[]
        for r in rows:
            v=r.get('cinema');pt=None
            if v and v.get('target') and v['show']>.9:
                pt=[round(v['origin'][0]+v['target'][0]*v['scale']),round(v['origin'][1]+v['target'][1]*v['scale'])]
            tracks.append(pt)
        c['cinemaTargets']=tracks;c['crop']=[116,0,406,240];c['field']=[124,35,390,180];c['fxPlan']=[]
        c['cinemaEffect']='cinema-'+style;c['cinemaReplacement']=d.get('clean_cinema_version')==1
        c['treatment']='沿用真实必杀镜头、人物和数值，命中层改为 PixelFX 的'+{'fire':'琥珀火焰与冷却余烬','holy':'浅金亮芒与扩散光屑','wind':'灰青弧风与消散风迹','lightning':'单次落电与分叉余弧','hit':'定向火花与落下的金属碎屑'}.get(style,'命中反馈')+'。避免大块光效持续盖住目标。'
    dest=OUT/'cases'/f'{key}.js';dest.write_text('window.PIXELFX_CASES=window.PIXELFX_CASES||{};window.PIXELFX_CASES['+json.dumps(key)+']='+json.dumps(c,ensure_ascii=False,separators=(',',':'))+';\n')
    return {k:c[k] for k in ['key','title','subtitle','family','group','profile','side','move','far','heavy','reaction','duration']}

def legacy_cases():
    old=read_js(BASE/'data.js');result=[]
    # Preserve all six completed previews, including the exact approved water palette.
    for c in old['cases']:
        key='approved-'+c['key'];out={'key':key,'title':c['title'],'subtitle':c['description'],'family':'approved','group':'已有对照','profile':'已确认与首批方案','side':'','move':c['title'],'far':'','heavy':False,'reaction':'','legacy':c['key'],'duration':c['duration']}
        result.append(out)
    return result

def main():
    catalog=[];errors=[]
    for p in sorted((ROOT/'captures').glob('*/capture.json')):
        try:catalog.append(build_case(p))
        except Exception as e:errors.append({'path':str(p),'error':str(e)})
    # Map cases use the same gallery schema and are generated separately.
    if (ROOT/'map-catalog.json').exists():catalog+=json.loads((ROOT/'map-catalog.json').read_text())
    catalog=legacy_cases()+catalog
    standard=json.loads((ROOT/'inventory.json').read_text());special=json.loads((ROOT/'inventory-special.json').read_text())
    family_order={k:i for i,k in enumerate(['approved','sword','lance','archery','javelin','lightning-sword','magic','support','monster','mechanical','cinema','map','reaction'])}
    catalog.sort(key=lambda c:(family_order.get(c['family'],99),c['profile'],c['move'],c['far'],c['heavy'],c['key']))
    profile_labels={'已确认与首批方案':'原来的六项对照'}
    for j in standard['jobs']+special['jobs']:
        profile=j['profile'];u=j['target'] if j['family']=='reaction' else j['actor'];name=str(u.get('name_zh','角色'))
        if profile in ['eileen_promoted','23_ally']:name+='（进阶）'
        side='敌方' if profile.endswith('_enemy') else '己方'
        profile_labels[profile]=name+' · '+side
    expected=len(standard['jobs'])+len(special['jobs'])
    by_family=collections.Counter(c['family'] for c in catalog)
    profiles=sorted({c['profile'] for c in catalog if c['family']!='approved'})
    # A focused tour of distinct directions, followed by the full searchable inventory.
    featured=['approved-water','approved-archery','approved-dash-strike','approved-cannon-break','approved-core-break']
    selections=[('lance',None),('javelin',None),('magic','火球'),('magic','雷电'),('magic','圣光'),('magic','风刃'),('magic','诸神黄昏'),('magic','鬼火'),('magic','史莱姆'),('magic','死亡'),('magic','美杜莎'),('magic','吸血'),('support','恢复'),('support','传送'),('monster','碎岩喷吐'),('monster','蚀息'),('monster','日冠聚光'),('mechanical',None),('cinema',None),('map',None),('reaction',None)]
    for family,move in selections:
        candidates=[c for c in catalog if c['family']==family and (not move or c['move']==move)]
        if candidates:
            choice=sorted(candidates,key=lambda c:(bool(c['far']),bool(c['heavy']),c['profile']!='eileen',c['key']))[0]
            if choice['key'] not in featured:featured.append(choice['key'])
    for key in ['map-hunapu-base','map-hunapu-bow','map-eileen-advanced','map-heal-18','map-warp']:
        if any(c['key']==key for c in catalog) and key not in featured:featured.append(key)
    data={'generated':'2026-11-07','fps':FPS,'cases':catalog,'effects':FX,'featured':featured,'familyNames':FAMILY,'profiles':profiles,'profileLabels':profile_labels,'coverage':{'profiles':47,'source':len(standard['jobs']),'special':len(special['jobs']),'recorded':len([c for c in catalog if c['family'] not in ['approved','map']]),'map':by_family.get('map',0),'approved':6,'expectedCloseups':expected,'families':dict(by_family),'excludedAliases':len(standard['skipped'])},'defaultCase':'approved-water'}
    (OUT/'catalog.js').write_text('window.PIXELFX_CATALOG='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    (OUT/'qa/build-report.json').write_text(json.dumps({'cases':len(catalog),'expectedCloseups':expected,'capturedCloseups':data['coverage']['recorded'],'errors':errors,'families':dict(by_family)},ensure_ascii=False,indent=2))
    print(json.dumps({'cases':len(catalog),'expectedCloseups':expected,'capturedCloseups':data['coverage']['recorded'],'errors':errors},ensure_ascii=False))

if __name__=='__main__':main()
