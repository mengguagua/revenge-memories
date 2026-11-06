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

for group,size,anchor in [('battle',[96,112],[48,104]),('maps',[40,48],[20,44]),('battle-broken',[96,112],[48,104]),('maps-broken',[40,48],[20,44])]:
    frames=manifest['frames'][group]
    pid='water-monkey-'+group
    profile={'id':pid,'actor':'water-monkey','actorName':'敌方水猴傀儡','classId':'new-mechanical-puppet',
        'className':'水猴傀儡'+('（背炮损坏）' if 'broken' in group else '（完整）'),'context':'battle' if group.startswith('battle') else 'tactical-walk',
        'contextName':'战斗场景' if group.startswith('battle') else '地图与撤离','side':'enemy',
        'mapping':PREFIX+'action-effect-mapping.json','mappingStatus':'review_candidate',
        'revision':'water-monkey-v1-20261104','sourceAtlas':PREFIX+'assets/'+group+'-reference.png',
        'sourceFrameSize':size,'sourceColumns':len(frames),'sourceFrameCount':len(frames),'sourceAtlasSize':[size[0]*len(frames),size[1]],
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
        'context':'battle' if group.startswith('battle') else 'tactical-walk','frames':rows,'fps':60,
        'duration':len(rows)/60,'origin':[190,132] if group.startswith('battle') else [128,116],
        'viewport':[0,0,256,160],'closeCamera':{'offset':[-80,-116],'size':[160,132]},
        'neededFrames':needed,'effectIds':sorted({e['sprite'] for r in rows for e in r['effects']}),
        'contactTick':contact,'ready':True,'missingFrames':[],
        'referenceLabel':'新增角色 · 形象基准（无原作）',
        'notes':'设计预览，未接入游戏。'+note}
    actions.append(action)

for i,sz in enumerate([[16,16],[26,26],[36,24],[30,20]]):
    effects['water-monkey-effect-'+str(i)]={'path':PREFIX+f'assets/effects-{i:02d}.png','anchor':[sz[0]/2,sz[1]/2],'frame_size':sz}

def cannon_fx(i,row):
    if 45<=i<62:
        t=(i-45)/17
        row['effects']=[{'sprite':'water-monkey-effect-0','position':[185-129*t,62-36*4*t*(1-t)+42*t],'flip':False}]
    elif 62<=i<68:row['effects']=[{'sprite':'water-monkey-effect-1','position':[56,104],'flip':False}]
    elif 68<=i<75:row['effects']=[{'sprite':'water-monkey-effect-2','position':[56,108],'flip':False}]
    elif 75<=i<82:row['effects']=[{'sprite':'water-monkey-effect-3','position':[56,110],'flip':False}]

action('idle','战斗待机','battle',[(0,60)],note='本体22，背炮10；空手，背炮完整。')
action('melee','机械掌击 · 近战','battle',[(0,10),(1,14),(2,10),(3,14),(0,16)],26,
       '抬掌准备→单次前推→收掌回位。射程1，威力5，攻速8；动画不附送额外连击。')
action('cannon','水炸弹投掷炮 · 1–3格','battle',[(0,10),(4,12),(5,20),(6,3),(7,30),(0,15)],62,
       '撑地→背炮仰角瞄准→单枚水弹→溅水。一次命中，速度－1至目标下一次行动结束，不叠加。',fx=cannon_fx)
action('hit','本体受击','battle',[(0,8),(8,10),(9,10),(0,20)],note='普通受击反应，不表示新增防御或减伤。')
action('part-break','背炮破坏 · 本体存活','battle',[(8,10),(9,10),(10,14),(11,36)],20,
       '第21帧炮管损坏并漏水，立即禁用水炮；保留掌击与移动，不触发额外爆炸伤害。')
action('part-break-aftermath','背炮破坏后 · 停留','battle',[(11,60)],note='损坏炮体保留在背部，状态清楚可辨，不恢复耐久。')
def death_motion(i,row,total):
    if i>=34:row['alpha']=max(0,1-(i-34)/(total-35))
action('defeat','本体击败 · 倒地退场','battle',[(8,8),(15,50)],8,
       '只在本体生命归零时倒地退场；副部位破坏不算击杀。',motion=death_motion)
action('map-idle','地图待机','maps',[(1,18),(0,6),(1,18),(2,6)],note='面对下方的机械待机，背炮完整。')
for direction,label,start in [('down','向下行走',0),('right','向右行走',4),('up','向上行走',8),('left','向左行走',12)]:
    action('walk-'+direction,label,'maps',[(start+i,8) for i in range(4)],note='四相交替迈步，头身与背部装置保持登记；地图帧40×48像素。')
def flee_motion(i,row,total):
    row['offset']=[80-i*2,0]
    if i>=104:row['alpha']=0
action('escape','失控撤离 · 到边缘消失','maps',[(12+i%4,6) for i in range(20)],None,
       '同阵营无非机械战斗单位时移动5→8。这里只演示向左边界移动，到达即消失；真实目标按最近合法路径选择，逃脱无击败经验。',motion=flee_motion)

broken_note='背炮全程保持弯折与漏水，未用完整炮体替代。'
action('broken-idle','破损 · 战斗待机','battle-broken',[(0,60)],note=broken_note+'本体存活，水炮禁用，掌击可用。')
action('broken-melee','破损 · 普通掌击','battle-broken',[(0,10),(1,14),(2,10),(3,14),(0,16)],26,
       broken_note+'与完整状态同为射程1、威力5、攻速8，单次掌击，不新增伤害。')
action('broken-hit','破损 · 本体受击','battle-broken',[(0,8),(4,12),(5,10),(0,20)],note=broken_note+'普通受击后回到破损待机。')
action('broken-defeat','破损 · 击败退场','battle-broken',[(4,8),(6,12),(7,38)],8,
       broken_note+'倒地时仍保留损坏装置，不发射、不爆炸。',motion=death_motion)
action('broken-battle-run','破损 · 战斗跑动与停止','battle-broken',[(8,8)]+[(9 if i%2==0 else 10,8) for i in range(6)]+[(11,12),(0,12)],
       note=broken_note+'交替迈步、收势站定，双手仍为空手。')
action('broken-map-idle','破损 · 地图待机','maps-broken',[(1,18),(0,6),(1,18),(2,6)],note=broken_note)
for direction,label,start in [('down','向下行走',0),('right','向右行走',4),('up','向上行走',8),('left','向左行走',12)]:
    action('broken-walk-'+direction,'破损 · '+label,'maps-broken',[(start+i,8) for i in range(4)],note=broken_note+'四方向分别制作，破损不改变移动数值。')
action('broken-escape','破损 · 撤离至边缘','maps-broken',[(12+i%4,6) for i in range(20)],None,
       broken_note+'移动仍为5＋3＝8，到边缘立即消失；部位已坏不会解除公共撤离特性。',motion=flee_motion)

payload={'profiles':profiles,'actions':actions,'effects':effects}
(ROOT/'gallery-extension.js').write_text("'use strict';\n(() => {\nconst extra = "+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+";\nconst d=window.GALLERY_DATA; d.profiles.push(...extra.profiles); d.actions.push(...extra.actions); Object.assign(d.effects,extra.effects); d.summary.profiles=d.profiles.length; d.summary.actions=d.actions.length; d.summary.ready=d.actions.filter(a=>a.ready).length; d.summary.pending=d.actions.length-d.summary.ready;\n})();\n")
(ROOT/'action-effect-mapping.json').write_text(json.dumps({'status':'review_only','unit':'water_monkey',
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
<div class="heading"><h2>水猴傀儡 · 机械傀儡基础型</h2><p>2026-11-04 · 设计与动作预览 · 待确认</p></div>
<div class="water-monkey-intro"><img src="water-monkey-v1-20261104/assets/concept.webp" alt="水猴傀儡：旧黄铜与灰青装甲、空手、背部水罐和投掷炮的四向形象" width="1000" height="1000">
<div><p class="lead">低攻击、高速度，背炮可单独破坏。</p><p class="action-note">等级3 · 本体22 · 背炮耐久10<br>力量5 · 技巧4 · 速度8 · 防御3 · 魔防1 · 移动5<br>机械掌击1格；水炮1–3格，命中速度－1，不叠加。</p><p class="action-note">机械傀儡经验×1.5。同阵营只剩机械傀儡时移动＋3，逐回合向最近可达边缘撤离；逃脱无击败经验。</p><p class="action-note">完整／损坏两套动作：破坏后，地图与战斗的待机、四向行走、掌击、受击、撤离和击败持续保留弯折炮管与漏水水罐。</p><p class="action-note">F21拟新增1只，放在敌船中段（第22列、第15行）。原胜利目标保留；本轮未修改游戏代码、关卡数据或安装包。</p><nav class="links" aria-label="水猴详细设计"><a href="water-monkey-v1-20261104/index.html">数值、F21投放与交互示例 →</a><a href="water-monkey-v1-20261104/source/prompts.json">内置ImageGen · 提示词与来源</a></nav></div></div>
<nav class="links" aria-label="水猴傀儡动作入口"><a href="?action=water-monkey-idle#motion-player">待机</a><a href="?action=water-monkey-walk-up#motion-player">向上</a><a href="?action=water-monkey-walk-right#motion-player">向右</a><a href="?action=water-monkey-walk-down#motion-player">向下</a><a href="?action=water-monkey-walk-left#motion-player">向左</a><a href="?action=water-monkey-melee#motion-player">机械掌击</a><a href="?action=water-monkey-cannon#motion-player">水炮投掷</a><a href="?action=water-monkey-part-break#motion-player">背炮破坏</a><a href="?action=water-monkey-escape#motion-player">边缘撤离</a><a href="?action=water-monkey-broken-idle#motion-player">破损 · 战斗待机</a><a href="?action=water-monkey-broken-melee#motion-player">破损 · 普通掌击</a><a href="?action=water-monkey-broken-walk-up#motion-player">破损 · 四向行走</a><a href="?action=water-monkey-broken-escape#motion-player">破损 · 撤离</a></nav>
</section>
'''
history_wrap='\n<!-- 后续修订记录统一追加在 revision-history-content 内；当前角色预览保持简洁。 -->\n<details class="revision-history" id="revision-history"><summary>历史修订记录<span>展开查看历次修改与测试包</span></summary>\n<div class="revision-history-content">'+history+'\n<!-- 后续修订记录追加位置 -->\n</div>\n</details>\n'
result=old[:main_open]+header+current+history_wrap+old[player_start:player_tag_end]+'\n'+old[selectors:]
result=re.sub(r'data-default-action="[^"]+"','data-default-action="water-monkey-idle"',result,count=1)
result=result.replace('<span class="badge">骸翼兽 · 蓝紫骨龙</span>','<span class="badge">水猴傀儡 · 新类别设计</span>')
result=result.replace('保留身体比例、四肢动作和原作节奏，重绘服饰、发型与眼睛。新旧同步播放，逐帧检查遮挡、手持武器和衣甲结构。','角色形象与地图、战斗动作集中验收。既有角色保留原作对照；新增角色以形象基准对照新动作。')
result=result.replace('构建时已核对资源路径、帧尺寸与时间线；浏览器视觉检查受环境访问限制，尚未执行。','本轮水猴预览与历史收纳已完成后台浏览器检查，覆盖桌面与390像素窄屏；其它既有角色未全量复验。')
extra_css='''
.water-monkey-intro{display:grid;grid-template-columns:minmax(240px,420px) minmax(0,1fr);gap:28px;align-items:center;margin:18px 0 24px}.water-monkey-intro>img{width:100%;height:auto;border-radius:12px;background:#24343b}.water-monkey-intro .action-note{margin:14px 0}.water-monkey-current .links a{min-height:44px;display:inline-flex;align-items:center;justify-content:center;text-align:center;padding:10px 16px}.links a:focus-visible,button:focus-visible,select:focus-visible{outline:none;box-shadow:0 0 0 5px #a8d6c829,0 5px 24px #a8d6c83a}.revision-history-content{padding:22px 0 0}.revision-history>summary{min-height:54px;padding:14px 18px}.revision-history>summary span{display:inline-block}@media(max-width:700px){.water-monkey-intro{grid-template-columns:1fr;gap:18px}.water-monkey-intro>img{max-width:420px;justify-self:center}.revision-history>summary span{display:block;margin-left:0}.water-monkey-current .heading{align-items:flex-start;gap:8px;flex-wrap:wrap}}
'''
result=result.replace('</style>',extra_css+'</style>',1)
result=result.replace('<script src="tools/gallery.js?', '<script src="water-monkey-v1-20261104/gallery-extension.js?v=1"></script><script src="tools/gallery.js?',1)
result=result.replace('</body>', '''<script>function revealHistoricalAnchor(){const id=decodeURIComponent(location.hash.slice(1));if(!id)return;const el=document.getElementById(id);if(!el)return;for(let p=el.parentElement;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}}revealHistoricalAnchor();addEventListener('hashchange',revealHistoricalAnchor);</script></body>''')
(BASE/'index.html').write_text(result)
print(json.dumps({'profiles':len(profiles),'actions':len(actions),'history_closed':True,'game_changed':False}))
