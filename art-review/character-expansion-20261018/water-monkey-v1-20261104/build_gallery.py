# -*- coding: utf-8 -*-
"""Create a small gallery extension and reorganize the existing review HTML."""
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PREFIX=ROOT.name+'/'
manifest=json.loads((ROOT/'asset-manifest.json').read_text())
profiles=[]
actions=[]
effects={}

for group,size,anchor in [('battle',[56,64],[28,60]),('maps',[40,48],[20,44]),('battle-broken',[56,64],[28,60]),('maps-broken',[40,48],[20,44])]:
    frames=manifest['frames'][group]
    source_columns=max(f['id'] for f in frames)+1
    pid='water-monkey-'+group
    profile={'id':pid,'actor':'water-monkey','actorName':'敌方水猴傀儡','classId':'new-mechanical-puppet',
        'className':'水猴傀儡'+('（背炮损坏）' if 'broken' in group else '（完整）'),'context':'battle' if group.startswith('battle') else 'tactical-walk',
        'contextName':'战斗场景' if group.startswith('battle') else '地图与撤离','side':'enemy',
        'mapping':PREFIX+'action-effect-mapping.json','mappingStatus':'runtime_integrated',
        'revision':'water-monkey-motion-v2-20261104','sourceAtlas':PREFIX+'assets/'+group+'-reference.png',
        'sourceFrameSize':size,'sourceColumns':source_columns,'sourceFrameCount':source_columns,'sourceAtlasSize':[size[0]*source_columns,size[1]],
        'anchor':anchor,'sourceOamCutoff':0,'flipOriginOffset':[0,0],'outputFrameSize':[v*4 for v in size],
        'newFrames':{str(f['id']):PREFIX+f['path'] for f in frames},
        'reviewFrameSources':{str(f['id']):0 for f in frames},
        'reviewFrameLabels':{str(f['id']):'设计姿势 '+str(f['id']+1) for f in frames},
        'links':[{'label':'数值、F21投放与交互示例','href':PREFIX+'index.html'},
                 {'label':'生成提示词与来源','href':PREFIX+'source/prompts.json'},
                 {'label':'尺寸与字节记录','href':PREFIX+'asset-manifest.json'}]}
    profiles.append(profile)

def action(key,name,group,segments,contact=None,note='',motion=None,fx=None):
    rows=[]
    for frame,duration in segments:
        rows.extend({'frame':frame,'offset':[0,0],'flip':group.startswith('battle'),'effects':[]} for _ in range(duration))
    for i,row in enumerate(rows):
        if motion:motion(i,row,len(rows))
        if fx:fx(i,row)
    needed=sorted({r['frame'] for r in rows})
    action={'id':'water-monkey-'+key,'key':key,'name':name,'profile':'water-monkey-'+group,
        'context':'battle' if group.startswith('battle') else 'tactical-walk','frames':rows,'fps':60.0988,
        'duration':len(rows)/60.0988,'origin':[176,128] if group.startswith('battle') else [128,116],
        'viewport':[0,0,256,160],'closeCamera':{'offset':[-48,-72],'size':[96,80]},
        'neededFrames':needed,'effectIds':sorted({e['sprite'] for r in rows for e in r['effects']}),
        'contactTick':contact,'ready':True,'missingFrames':[],
        'referenceLabel':'新增角色 · 形象基准（无原作）',
        'notes':'已接入运行工程；此处为美术对照。'+note}
    actions.append(action)
    return action

for i,sz in enumerate([[52,24],[52,24],[42,44],[46,26]]):
    effects['water-monkey-water-'+str(i)]={'path':PREFIX+f'assets/water-v2-{i:02d}.png','anchor':[sz[0]/2,sz[1]/2],'frame_size':sz}
effects['water-monkey-water-muzzle']={'path':PREFIX+'assets/water-v2-00.png','anchor':[18,7],'frame_size':[24,14]}
companion={'path':PREFIX+'assets/soldier-reference.png','origin':[64,128],'size':[80,64],'anchor':[40,64],'flip':True}
hit_source=json.loads((ROOT/'source/motion-v2-20261104/soldier-hit-reference.json').read_text())
melee_source=json.loads((ROOT/'source/motion-v2-20261104/soldier-melee-reference.json').read_text())

def add_companion(a,hit_tick=None):
    a['reviewCompanions']=[companion]
    if hit_tick is not None:
        a['soundEvents']=[{'tick':hit_tick,'path':PREFIX+'assets/hit.ogg','volume':.45}]
        for i,row in enumerate(a['frames']):
            j=i-hit_tick
            if 0<=j<len(hit_source['frames']):
                ref=hit_source['frames'][j]
                row['companionTint']=ref.get('tint',1)
                row['companionShake']=ref.get('shake',0)

def melee(key,name,group):
    run_start=16 if group=='battle' else 12
    a=action(key,name,group,[(0,len(melee_source['frames']))],82,
        '按普通士兵的跑近→出手→收势→跑回阶段编排，共219帧，第83帧单次命中；空手接触位移88，主体约32像素，与士兵同脚底基线。')
    for i,row in enumerate(a['frames']):
        ref=melee_source['frames'][i]
        row['offset']=[round(float(ref.get('offset',[0,0])[0])*88/72),0]
        if i<5 or i>=216:row['frame']=0
        elif i<64 or 153<=i<216:row['frame']=run_start+min(3,int(ref['frame']))
        elif i<80:row['frame']=1
        elif i<133:row['frame']=2
        elif i<149:row['frame']=3
        else:row['frame']=0
        row['flip']=not (153<=i<216)
    a['neededFrames']=sorted({r['frame'] for r in a['frames']})
    add_companion(a,82)
    return a

def hit_feedback(key,name,group):
    a=action(key,name,group,[(0,len(hit_source['frames']))],note='与普通士兵一致：同一张待机姿势配合明暗闪烁、轻微位移和命中音；不播放后仰受伤连帧。')
    for row,ref in zip(a['frames'],hit_source['frames']):
        row['tint']=ref.get('tint',1);row['shake']=ref.get('shake',0)
    a['soundEvents']=[{'tick':0,'path':PREFIX+'assets/hit.ogg','volume':.45}]
    return a

def cannon_fx(i,row):
    if 42<=i<45:
        row['effects']=[{'sprite':'water-monkey-water-muzzle','position':[184,91],'flip':False}]
    elif 45<=i<62:
        t=(i-45)/17
        row['effects']=[{'sprite':'water-monkey-water-'+str((i//3)%2),'position':[162-98*t,94+14*t],'flip':False}]
    elif 62<=i<73:row['effects']=[{'sprite':'water-monkey-water-2','position':[64,108],'flip':False}]
    elif 73<=i<84:row['effects']=[{'sprite':'water-monkey-water-3','position':[64,117],'flip':False}]

action('idle','战斗待机','battle',[(0,60)],note='本体22，背炮10；空手，背炮完整。')
melee('melee','机械掌击 · 跑近攻击后回位','battle')
cannon=action('cannon','水炮 · 高压水束 · 1–3格','battle',[(0,10),(4,12),(5,20),(7,30),(0,18)],62,
       '撑地→背炮发射有厚度的高压水束→目标处大水花→收势。一次命中，速度－1不叠加；水束与水花不增加攻击次数或范围伤害。',fx=cannon_fx)
add_companion(cannon,62)
hit_feedback('hit','受伤反馈 · 闪烁与命中音','battle')
action('part-break','背炮破坏 · 本体存活','battle',[(0,10),(0,10),(10,14),(11,36)],20,
       '第21帧炮管损坏并漏水，立即禁用水炮；保留掌击与移动，不触发额外爆炸伤害。')
action('part-break-aftermath','背炮破坏后 · 停留','battle',[(11,60)],note='损坏炮体保留在背部，状态清楚可辨，不恢复耐久。')
def death_motion(i,row,total):
    if i>=34:row['alpha']=max(0,1-(i-34)/(total-35))
action('defeat','本体击败 · 倒地退场','battle',[(0,8),(15,50)],8,
       '只在本体生命归零时倒地退场；副部位破坏不算击杀。',motion=death_motion)
action('map-idle','地图待机 · 慢节奏','maps',[(1,72),(0,18),(1,72),(2,18)],note='约3秒一轮，停留更长、动作放缓；只改待机，不拖慢四向行走。')
run=action('battle-run','战斗跑动与停止','battle',[(16+i%4,8) for i in range(8)]+[(0,16)],note='完整背炮，四相跑动、停止；主体尺寸与普通士兵一致。')
add_companion(run)
for direction,label,start in [('down','向下行走',0),('right','向右行走',4),('up','向上行走',8),('left','向左行走',12)]:
    action('walk-'+direction,label,'maps',[(start+i,8) for i in range(4)],note='四相交替迈步，头身与背部装置保持登记；地图帧40×48像素。')
def flee_motion(i,row,total):
    row['offset']=[80-i*2,0]
    if i>=104:row['alpha']=0
action('escape','失控撤离 · 到边缘消失','maps',[(12+i%4,6) for i in range(20)],None,
       '同阵营无非机械战斗单位时移动5→8。这里只演示向左边界移动，到达即消失；真实目标按最近合法路径选择，逃脱无击败经验。',motion=flee_motion)

broken_note='背炮全程保持弯折与漏水，未用完整炮体替代。'
action('broken-idle','破损 · 战斗待机','battle-broken',[(0,60)],note=broken_note+'本体存活，水炮禁用，掌击可用。')
melee('broken-melee','破损 · 跑近掌击后回位','battle-broken')
hit_feedback('broken-hit','破损 · 闪烁与命中音','battle-broken')
action('broken-defeat','破损 · 击败退场','battle-broken',[(0,8),(6,12),(7,38)],8,
       broken_note+'倒地时仍保留损坏装置，不发射、不爆炸。',motion=death_motion)
run=action('broken-battle-run','破损 · 战斗跑动与停止','battle-broken',[(12+i%4,8) for i in range(8)]+[(0,16)],
       note=broken_note+'交替迈步、收势站定，双手仍为空手。')
add_companion(run)
action('broken-map-idle','破损 · 地图待机 · 慢节奏','maps-broken',[(1,72),(0,18),(1,72),(2,18)],note=broken_note+'约3秒一轮，与完整状态同节奏。')
for direction,label,start in [('down','向下行走',0),('right','向右行走',4),('up','向上行走',8),('left','向左行走',12)]:
    action('broken-walk-'+direction,'破损 · '+label,'maps-broken',[(start+i,8) for i in range(4)],note=broken_note+'四方向分别制作，破损不改变移动数值。')
action('broken-escape','破损 · 撤离至边缘','maps-broken',[(12+i%4,6) for i in range(20)],None,
       broken_note+'移动仍为5＋3＝8，到边缘立即消失；部位已坏不会解除公共撤离特性。',motion=flee_motion)

payload={'profiles':profiles,'actions':actions,'effects':effects}
(ROOT/'gallery-extension.js').write_text("'use strict';\n(() => {\nconst extra = "+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+";\nconst d=window.GALLERY_DATA; d.profiles.push(...extra.profiles); d.actions.push(...extra.actions); Object.assign(d.effects,extra.effects); d.summary.profiles=d.profiles.length; d.summary.actions=d.actions.length; d.summary.ready=d.actions.filter(a=>a.ready).length; d.summary.pending=d.actions.length-d.summary.ready;\n})();\n")
(ROOT/'action-effect-mapping.json').write_text(json.dumps({'status':'runtime_integrated','unit':'water_monkey',
    'mapping':[{'action':a['id'],'name':a['name'],'frames':len(a['frames']),'contact_frame':a['contactTick']+1 if a['contactTick'] is not None else None,'poses':a['neededFrames'],'effect':a['notes']} for a in actions]},ensure_ascii=False,indent=2)+'\n')

old=(ROOT/'source/index-before.html').read_text()
main_open=old.index('<main>')+len('<main>')
player_start=old.index('<section class="panel" id="motion-player"')
player_tag_end=old.index('>',player_start)+1
selectors=old.index('<div class="selectors">',player_start)
before=old[main_open:player_start]
header=re.search(r'<header>.*?</header>',before,re.S).group(0)
history=before.replace(header,'')+old[player_tag_end:selectors]
history=history.replace('<details class="revision-history" id="revision-history"><summary>历史修订记录<span>展开查看历次修改与测试包</span></summary>\n<div class="revision-history-content">','',1)
assert history.rstrip().endswith('</div>\n</details>')
history=history.rstrip()[:-len('</div>\n</details>')]
current='''
<section class="panel water-monkey-current" id="water-monkey-review" aria-label="水猴傀儡设计预览">
<div class="heading"><h2>水猴傀儡 · 机械傀儡基础型</h2><p>2026-11-04 · V2已接入运行工程</p></div>
<div class="water-monkey-intro"><img src="water-monkey-v1-20261104/assets/concept.webp" alt="水猴傀儡：旧黄铜与灰青装甲、空手、背部水罐和投掷炮的四向形象" width="1000" height="1000">
<div><p class="lead">低攻击、高速度，背炮可单独破坏。</p><p class="action-note">等级3 · 本体22 · 背炮耐久10<br>力量5 · 技巧4 · 速度8 · 防御3 · 魔防1 · 移动5<br>机械掌击1格；水炮1–3格，命中速度－1，不叠加。</p><p class="action-note">机械傀儡经验×1.5。同阵营只剩机械傀儡时移动＋3，逐回合向最近可达边缘撤离；逃脱无击败经验。</p><p class="action-note">完整／损坏两套动作：破坏后，地图与战斗的待机、四向行走、掌击、受击、撤离和击败持续保留弯折炮管与漏水水罐。</p><p class="action-note">F21已新增1只，位于敌船中段（第22列、第15行）。本体／背炮选择、破损动作、减速、经验与撤离已接入。原胜利目标保留。</p><nav class="links" aria-label="水猴详细设计"><a href="water-monkey-v1-20261104/index.html">数值、F21投放与交互示例 →</a><a href="../../actual/reports/mechanical-puppets-20261104/index.html">运行截图与接入检查 →</a><a href="water-monkey-v1-20261104/source/prompts.json">内置ImageGen · 提示词与来源</a></nav></div></div>
<nav class="links" aria-label="水猴傀儡动作入口"><a href="?action=water-monkey-idle#motion-player">待机</a><a href="?action=water-monkey-walk-up#motion-player">向上</a><a href="?action=water-monkey-walk-right#motion-player">向右</a><a href="?action=water-monkey-walk-down#motion-player">向下</a><a href="?action=water-monkey-walk-left#motion-player">向左</a><a href="?action=water-monkey-melee#motion-player">机械掌击</a><a href="?action=water-monkey-cannon#motion-player">水炮投掷</a><a href="?action=water-monkey-part-break#motion-player">背炮破坏</a><a href="?action=water-monkey-escape#motion-player">边缘撤离</a><a href="?action=water-monkey-broken-idle#motion-player">破损 · 战斗待机</a><a href="?action=water-monkey-broken-melee#motion-player">破损 · 普通掌击</a><a href="?action=water-monkey-broken-walk-up#motion-player">破损 · 四向行走</a><a href="?action=water-monkey-broken-escape#motion-player">破损 · 撤离</a></nav>
<p class="action-note" style="margin-top:18px">V2：两种状态地图待机约3秒一轮；掌击跑近目标后出手并跑回；水炮改为粗水束与明显命中水花。主体按士兵约32像素校准，脚底统一。受伤沿用同姿势明暗闪烁、轻微位移与命中音，不再后仰；音效可手动开启。</p>
<nav class="links" style="margin-top:12px"><a href="?action=water-monkey-map-idle#motion-player">慢待机</a><a href="?action=water-monkey-hit#motion-player">受伤闪烁与命中音</a><a href="?action=water-monkey-broken-hit#motion-player">破损 · 受伤闪烁</a></nav>
</section>
'''
history='''<section class="panel" id="water-monkey-motion-v2-record"><div class="heading"><h2>水猴傀儡 · 动作修订V2</h2><p>2026-11-04 · 仅美术预览</p></div><p class="action-note">按反馈放慢地图待机、重制高压水炮效果；完整与破损近战按士兵219帧接近／出手／回位流程重排，主体高度与脚底统一。已核对士兵受伤为固定姿势闪烁、轻微位移和命中音，水猴同步采用该方式。采用的源图继续保留；被否决的独立素材于后续接入时清理。</p><nav class="links"><a href="water-monkey-v1-20261104/source/motion-v2-20261104/reference-audit.json">士兵动作与受伤核对</a><a href="water-monkey-v1-20261104/README.md">本轮制作与检查</a></nav></section><section id="water-monkey-v1-record" class="panel"><div class="heading"><h2>水猴傀儡 · V1设计记录</h2><p>2026-11-04</p></div><p class="action-note">初版完成机械傀儡分类、本体与背炮数值、1.5倍经验与撤离规则、F21单只投放示例和完整／破损两套姿势。原先原地掌击、小水滴和连续后仰受击已由上方V2修订替代。当时尚未接入游戏，后续已完成。</p></section>'''+history
history='<section class="panel" id="water-monkey-runtime-20261104"><div class="heading"><h2>水猴傀儡 · 运行接入与素材清理</h2><p>2026-11-04 · 用户确认后实施</p></div><p class="action-note">F21新部署9→10名敌军。新增机械傀儡类别，支持本体／背炮选择、独立耐久、破炮禁用远程与全场景破损表现、命中速度－1、1.5倍经验及合法路径撤离。沿用士兵闪烁与命中音。旧的进行中存档不强行插入敌人，重新部署／重试F21使用新编成。</p><p class="action-note">删除20项被否决且无当前动作引用的文件，并重建混合图集；生成脚本不再产出这些姿势。采用的源图及包含有效姿势的混合源图隔离保留。通过定向逻辑检查、既有敌军兼容检查与17张后台运行截图核对；未进行手机安装或整关自然实战平衡验收。</p><nav class="links"><a href="../../actual/reports/mechanical-puppets-20261104/index.html">运行截图与检查结果</a><a href="../../actual/reports/mechanical-puppets-20261104/cleanup-manifest.json">20项删除清单</a></nav></section>'+history
history_wrap='\n<!-- 后续修订记录统一追加在 revision-history-content 内；当前角色预览保持简洁。 -->\n<details class="revision-history" id="revision-history"><summary>历史修订记录<span>展开查看历次修改与测试包</span></summary>\n<div class="revision-history-content">'+history+'\n<!-- 后续修订记录追加位置 -->\n</div>\n</details>\n'
result=old[:main_open]+header+current+history_wrap+old[player_start:player_tag_end]+'\n'+old[selectors:]
result=re.sub(r'data-default-action="[^"]+"','data-default-action="water-monkey-melee"',result,count=1)
result=result.replace('<span class="badge">骸翼兽 · 蓝紫骨龙</span>','<span class="badge">水猴傀儡 · 新类别设计</span>')
result=result.replace('保留身体比例、四肢动作和原作节奏，重绘服饰、发型与眼睛。新旧同步播放，逐帧检查遮挡、手持武器和衣甲结构。','角色形象与地图、战斗动作集中验收。既有角色保留原作对照；新增角色以形象基准对照新动作。')
result=result.replace('构建时已核对资源路径、帧尺寸与时间线；浏览器视觉检查受环境访问限制，尚未执行。','本轮水猴预览与历史收纳已完成后台浏览器检查，覆盖桌面与390像素窄屏；其它既有角色未全量复验。')
extra_css='''
.water-monkey-intro{display:grid;grid-template-columns:minmax(240px,420px) minmax(0,1fr);gap:28px;align-items:center;margin:18px 0 24px}.water-monkey-intro>img{width:100%;height:auto;border-radius:12px;background:#24343b}.water-monkey-intro .action-note{margin:14px 0}.water-monkey-current .links a{min-height:44px;display:inline-flex;align-items:center;justify-content:center;text-align:center;padding:10px 16px}.links a:focus-visible,button:focus-visible,select:focus-visible{outline:none;box-shadow:0 0 0 5px #a8d6c829,0 5px 24px #a8d6c83a}.revision-history-content{padding:22px 0 0}.revision-history>summary{min-height:54px;padding:14px 18px}.revision-history>summary span{display:inline-block}@media(max-width:700px){.water-monkey-intro{grid-template-columns:1fr;gap:18px}.water-monkey-intro>img{max-width:420px;justify-self:center}.revision-history>summary span{display:block;margin-left:0}.water-monkey-current .heading{align-items:flex-start;gap:8px;flex-wrap:wrap}}
'''
result=result.replace('</style>',extra_css+'</style>',1)
result=result.replace('<script src="tools/gallery.js?', '<script src="water-monkey-v1-20261104/gallery-extension.js?v=motion-v2-20261104"></script><script src="tools/gallery.js?v=water-monkey-motion-v2-20261104&previous=',1)
result=result.replace('<button id="map-ground"', '<button id="review-sound" aria-pressed="false" hidden>音效：关</button><button id="map-ground"',1)
result=result.replace('</body>', '''<script>function revealHistoricalAnchor(){const id=decodeURIComponent(location.hash.slice(1));if(!id)return;const el=document.getElementById(id);if(!el)return;for(let p=el.parentElement;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}}revealHistoricalAnchor();addEventListener('hashchange',revealHistoricalAnchor);</script></body>''')
(BASE/'index.html').write_text(result)
print(json.dumps({'profiles':len(profiles),'actions':len(actions),'history_closed':True,'game_changed':True}))
