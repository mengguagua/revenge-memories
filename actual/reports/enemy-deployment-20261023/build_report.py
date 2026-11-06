"""Build the offline review page from saved checks and capture metadata. No fetch needed."""
from pathlib import Path
import json, html, os
from PIL import Image
R=Path(__file__).resolve().parent
A=R.parents[1]
REPO=A.parent
ART=REPO/'art-review/enemy-deployment-20261023'
def read(name,default=None):
 p=R/name
 return json.loads(p.read_text()) if p.exists() else default
def esc(x):return html.escape(str(x),quote=True)
def href(p):return os.path.relpath(p,R)
def link(p,label=None):return f'<a href="{esc(href(p))}">{esc(label or p.name)}</a>'
def count(d):return len(d['checks']) if isinstance(d['checks'],list) else int(d['checks'])
suites=[('deployment','部署与目标静态核对','40场职业覆盖、替换单位、地图与目标不变'),('role','受限AI与存档规则','移形、生成上限、召唤归属、存读档和重试'),('innate','身体攻击与回收物','距离选择、费用、命中结算、装备隔离和掉落'),('integration','当前战役集成','12份真实部署检查点重开当前地图，再验证存读档、重试和受控交锋')]
checks=[]
for name,title,scope in suites:
 d=read(name+'-checks.json');checks.append(dict(name=name,title=title,scope=scope,count=count(d),passed=d.get('passed',not bool(d.get('errors'))),errors=d.get('errors',[])))
play=read('play/S11-play.json');battle=play['battles'][0]
manifest=read('art-manifest.json',[])
artrows=[]
for m in manifest:
 p=A/m['file'];im=Image.open(p).convert('RGBA');colors=len({v[:3] for v in im.getdata() if v[3]>0})
 artrows.append({**m,'actual_bytes':p.stat().st_size,'actual_size':f'{im.width}×{im.height}','visible_colors':colors})
captures=read('captures.json',{})
shots=captures if isinstance(captures,list) else captures.get('shots',captures.get('captures',[]))
if isinstance(shots,dict):shots=[dict(name=k,**v) if isinstance(v,dict) else dict(name=k,path=v) for k,v in shots.items()]
def shot_path(x):
 raw=x if isinstance(x,str) else x.get('path',x.get('file',''))
 if raw.startswith('res://'):return A/raw[6:]
 p=Path(raw)
 return p if p.is_absolute() else R/p
validshots=[x for x in shots if shot_path(x).is_file()]
source_records=sorted({p for p in ART.rglob('*') if p.is_file() and p.suffix in ['.json','.md','.txt']} | ({R/'art-generation.json'} if (R/'art-generation.json').exists() else set()))
rows=[('14 断路匪','S11_e4／e5','矿道侧路的两名劫掠者'),('4 骑士','M32_e1／e2','军需大道护送骑士；移动8、抗性5'),('9 剑士','F32_e1／e2','盐路剑兵；移动5、抗性6'),('13 狙击手','M33_e9','石堡高地射手；移动5、抗性2'),('17 骸卫','F33_e9／e10','提炼院遗迹骨质守卫'),('16 隙行术师','F42_e3','第2回合起，至多4格短移，占整次行动、间隔三回合'),('19 驭魔师','F43_e8','第3回合起至多两次，每次至多两只骸卫、合计2HP、间隔三回合'),('18 裂目兽','F43_e3','至多一次分裂一只，子代不再分裂'),('5 骸翼兽','S42_e1','第3回合压近；HP30、力量9、速度4、抗性12、移动8'),('10 剑豪','J53_e14／e15','神宫前庭近卫；速度9、移动7、抗性15'),('21 神躯','J54_boss','乌库布来源169、112HP；独立日冠／翼喙攻击')]
checks_html=''.join(f'<tr><td>{link(R/(x["name"]+"-checks.json"),x["title"])}</td><td>{x["count"]} 项断言</td><td class="ok">'+('通过' if x['passed'] else '未通过')+f'</td><td>{esc(x["scope"])}</td></tr>' for x in checks)
deployment_html=''.join('<tr>'+''.join('<td>'+esc(c)+'</td>' for c in row)+'</tr>' for row in rows)
asset_html=''.join(f'<tr><td>{link(A/x["file"])}</td><td>{x["actual_size"]}</td><td>{x["actual_bytes"]:,} B</td><td>{x["visible_colors"]}／{x["palette_limit"]}</td><td>{link(REPO/x["source"],"生成源图")}</td></tr>' for x in artrows)
poses=''
for cid,label in [('3','石翼兽 · 无持械石质身体'),('5','骸翼兽 · 低饱和灰骨身体'),('21','神躯 · 乌库布鸟形日冠')]:
 path=A/f'assets/innate-enemies-20261023/class-{cid}-battle.png'
 poses+=f'<h3>{esc(label)}</h3><div class="poses">'+''.join(f'<figure><div class="pose" style="background-image:url(\'{esc(href(path))}\');background-position:{i*100/7:.6f}% 0"></div><figcaption>姿态 {i+1}</figcaption></figure>' for i in range(8))+'</div>'
shots_html=''
for shot in validshots:
 x={'name':Path(shot).stem} if isinstance(shot,str) else shot;p=shot_path(shot)
 title=x.get('title',x.get('name',p.stem));notes=[]
 if 'native_width' in x or 'width' in x:notes.append('逻辑宽度 '+str(x.get('native_width',x.get('width'))))
 if 'view' in x:notes.append(str(x['view']))
 if x.get('errors'):notes.append('待修：'+str(x['errors']))
 shots_html+=f'<figure><a href="{esc(href(p))}"><img loading="lazy" src="{esc(href(p))}" alt="{esc(title)}"></a><figcaption><strong>{esc(title)}</strong><br>{esc(" · ".join(notes))}</figcaption></figure>'
shot_status=f'已收录 {len(validshots)} 张后台运行截图。' if validshots else '后台截图尚未合入本页；待 captures.json 落盘后重新运行本目录 build_report.py。'
if captures and isinstance(captures,dict):shot_status+=' 元数据结果：'+('通过。' if captures.get('passed') else '请查看记录。')
source_html='<ul>'+''.join('<li>'+link(p)+'</li>' for p in source_records)+'</ul>' if source_records else '<p>生成提示词与来源记录尚待合入；此处不反推或补造工具提示词。</p>'
source_html+='<ul>'+''.join('<li>'+link(p,p.name+' · 保留生成源图')+'</li>' for p in sorted((ART/'source').glob('*.png')))+'</ul>'
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>敌军职业投放与身体演出 · 2026-10-23</title><style>
:root{color-scheme:dark;--bg:#121820;--panel:#1b2631;--ink:#e1e7eb;--muted:#a8b5be;--accent:#b6d0d8;--line:#34434e;--pose:#14212d}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 system-ui,-apple-system,sans-serif}main{max-width:1240px;margin:auto;padding:46px 28px 80px}h1{font-size:clamp(28px,4vw,44px);line-height:1.3;margin:8px 0 20px}h2{font-size:26px;margin:0 0 18px}h3{font-size:20px;margin-top:25px}.eyebrow{color:var(--muted);letter-spacing:.12em;font-size:13px}p{max-width:96ch}a{color:var(--accent);text-underline-offset:.2em}section{margin:28px 0;padding:28px;background:var(--panel);border-radius:18px;box-shadow:0 8px 25px #0002}nav{display:flex;flex-wrap:wrap;gap:12px;margin:26px 0}nav a,button{padding:9px 17px;background:#283846;border:0;border-radius:10px;color:var(--ink);font:inherit;text-decoration:none}button{cursor:pointer}a:focus-visible,button:focus-visible{outline:none;box-shadow:0 0 0 4px #91b7d255}.scroller{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:13px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);white-space:nowrap}.ok{color:#a8d3b2}.note{color:var(--muted)}.stats{display:flex;gap:18px;flex-wrap:wrap;margin-top:26px}.stat{background:#23313d;padding:14px 22px;border-radius:12px;min-width:130px}.stat strong{font-size:27px;display:block}.stat small{color:var(--muted)}figure{margin:0;background:#131d27;border-radius:12px;overflow:hidden}figcaption{padding:12px 16px;color:var(--muted);font-size:14px}.poses{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.pose{aspect-ratio:1;background-size:800% 100%;background-repeat:no-repeat;background-color:var(--pose);image-rendering:pixelated}.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.shots img{display:block;width:100%;image-rendering:pixelated;background:#0d1218}.light-poses{--pose:#e5e5de}details{margin:14px 0}summary{cursor:pointer;color:var(--accent)}li{margin:7px 0}@media(max-width:760px){main{padding:25px 14px 50px}section{padding:19px}.shots{grid-template-columns:1fr}.poses{grid-template-columns:repeat(2,minmax(0,1fr))}td,th{padding:10px}}
</style><main><header><div class="eyebrow">复仇与回忆 · 源码接入验收 · 2026-10-23</div><h1>敌军职业投放与身体演出</h1><p>按剧情补齐此前缺失的11种有效敌军职业，40场地图现覆盖1—22号职业。同步10个敌军新名、受限特殊AI、三类非人形身体攻击和独立回收物。勇者23、公主24继续保留。</p><div class="stats"><div class="stat"><strong>11</strong><small>补齐的敌军职业</small></div><div class="stat"><strong>22</strong><small>实际投放职业</small></div><div class="stat"><strong>40</strong><small>既有战斗地图</small></div></div><nav><a href="#deployment">剧情与投放</a><a href="#checks">验证证据</a><a href="#art">身体与配色</a><a href="#captures">运行截图</a><a href="#sources">来源记录</a></nav></header>
<section id="deployment"><h2>按剧情补齐敌军</h2><p>全部采用既有单位替换，保持初始敌人数、地形、任务NPC和胜败条件。新增召唤与分裂后代有次数、容量和落点限制，入场当回合不行动，不发经验或掉落。</p><div class="scroller"><table><thead><tr><th>职业</th><th>单位／战场</th><th>剧情与规则</th></tr></thead><tbody>DEPLOYMENT</tbody></table></div><p>F43原召唤神官仍是15号执令术师，原一次士兵波次独立处理；新19号驭魔师死亡只清自己召出的后代。J54保留来源169与半血一次强化／援军，普通物理与法术全程有效。</p></section>
<section id="checks"><h2>验证证据与实际范围</h2><div class="scroller"><table><thead><tr><th>检查记录</th><th>计数</th><th>结果</th><th>范围</th></tr></thead><tbody>CHECKS</tbody></table></div><p class="note">上表是各套检查内部断言数，不相加冒充独立场景、战斗数或自然通关次数。</p><h3>S11真实输入通关</h3><p>从真实战役部署存档正常重新进场，以键盘输入完成旧矿道救援：<strong>PLAYTURNS回合、PLAYINPUTS次输入</strong>，结果PLAYOUTCOME；记录未修改HP、属性、随机数或位置，也未强制设为胜利。PLAYLINK</p><p>其余集成检查由12份真实历史部署记录重开当前战场，再进行受控交锋、存读档和重试；它们不是12场自然通关。尚未完成本次修改后的五章40场自然实玩、完整难度曲线复核或移动真机验收。<strong>未更新安装包。</strong></p></section>
<section id="art"><h2>身体动作与低饱和配色</h2><p>石翼兽、骸翼兽和神躯各接入8个无持械关键姿态，地图小像同步；源图使用内置imagegen生成，按追加要求降低饱和度、减少颜色，向男主角灰蓝配色靠拢。骸翼兽使用新生成灰骨身体，独立编排沉重咬击／吐息节奏。演出采用关键姿态、位移和特效组合，不宣称所有动作逐帧重绘。</p><p>日冠聚光早期设计为光束，本次实际初版是纯金白集中光球（聚光弹），一次命中且不使用虫形效果。石翼兽／骸翼兽头像同步新形象，骸卫／裂目兽头像由自身原地图帧裁出。每次攻击只在对应命中时刻结算一次；普通反击、追击仍由真实交锋序列决定。裂石爪接触tick 26、骸颚撕咬tick 38，其余身体攻击tick 34（时间轴50fps）。S21投枪、S22钢盾作为独立回收物，身体不持枪或盾，同一击杀不追加随机奖励。</p><button onclick="document.body.classList.toggle('light-poses')">切换姿态深／浅背景</button>POSES<div class="scroller"><table><thead><tr><th>运行素材</th><th>尺寸</th><th>实际字节</th><th>可见RGB颜色／上限</th><th>源图</th></tr></thead><tbody>ASSETS</tbody></table></div><p class="note">颜色数只统计非透明像素的不同RGB值；原始生成源图保存在工程外层art-review目录，运行文件采用优化副本。素材详情见MANIFEST。</p></section>
<section id="captures"><h2>后台运行截图</h2><p>SHOTSTATUS</p><p class="note">截图通过不激活、不抢焦点的后台保护运行取得。地图／状态页来自重新部署后的隔离存档；战斗接触与收势画面使用受控show_frame展示，不能当作自然交锋数据或通关证据。代表性文字安全区按capture记录核对；截图不代替完整实玩。</p><div class="shots">SHOTS</div></section>
<section id="sources"><h2>提示词、来源与复核文件</h2><p>art-generation.json保存石翼初版、最终调色修订与灰骨骸翼姿态生成的提示词记录；鸟形初版仅保存明确标注的摘要，完整原文仍在本次聊天的imagegen工具调用记录中，摘要不冒充原文。下方另列原图与修订图、切图、姿态对应及优化记录。</p>SOURCES<ul><li>MANIFEST</li><li>ARTCONFIG</li><li>BUILDER</li><li>README</li><li>SPEC</li><li>FLOW</li></ul><p class="note">本页为静态HTML；build_report.py从落盘JSON生成内容，不依赖浏览器fetch，本地文件可以直接打开。captures.json变化后重新生成即可。</p></section></main></html>'''
replace={'DEPLOYMENT':deployment_html,'CHECKS':checks_html,'PLAYTURNS':str(battle['final_turn']),'PLAYINPUTS':str(play['inputs']),'PLAYOUTCOME':esc(battle['outcome']),'PLAYLINK':link(R/'play/S11-play.json','查看输入与通关记录'),'POSES':poses,'ASSETS':asset_html,'MANIFEST':link(R/'art-manifest.json','素材清单'),'SHOTSTATUS':esc(shot_status),'SHOTS':shots_html,'SOURCES':source_html,'ARTCONFIG':link(A/'data/innate_attack_art.json','姿态与地图小像绑定'),'BUILDER':link(A/'tools/build_innate_enemy_art.py','切图与压缩脚本'),'README':link(R/'README.md','验收说明'),'SPEC':link(REPO/'docs2/完整游戏设定.md','docs2完整游戏设定'),'FLOW':link(REPO/'docs2/完整游戏流程.md','docs2完整游戏流程')}
for key,value in replace.items():page=page.replace(key,value)
(R/'index.html').write_text(page)
md=['# 敌军职业投放与身体演出验收','', '日期：2026-10-23。当前源码已接入，未重新导出安装包。','', '[打开统一验收页面](index.html)','', '## 实现范围','', '原40场战斗通过替换既有单位补齐11种此前未投放的有效职业，覆盖敌方1—22号；23／24号继续保留。同步10个敌军现名、受限移形／召唤／分裂、六种身体攻击与S21／S22独立回收物。初始敌人数、地图地形、任务NPC与胜败目标保持。','', '| 职业 | 实际单位 | 剧情与规则 |','|---|---|---|']
md+=['| '+' | '.join(row)+' |' for row in rows]
md+=['','## 检查证据','', '| 记录 | 断言数 | 结果 | 范围 |','|---|---:|---|---|']
md += [f'| [{x["title"]}]({x["name"]}-checks.json) | {x["count"]} | '+('通过' if x['passed'] else '未通过')+f' | {x["scope"]} |' for x in checks]
md += ['', '这些数值是各套检查内的断言数，不相加冒充独立测试场景或战斗数。', '',f'[S11普通输入通关](play/S11-play.json)：{battle["final_turn"]}回合、{play["inputs"]}次键盘输入，从真实战役部署检查点正常重新入场；没有修改HP、属性、随机数、位置或强制胜利。', '', '集成检查使用12份真实历史部署记录，经当前start_battle重开后进行受控交锋、存读档与重试；不等于12场自然通关。未完成本次修改后的五章40场自然实玩、完整难度曲线复核或移动真机验收。', '', '## 身体演出与素材','', '石翼兽／骸翼兽／神躯各8个新无持械关键姿态及地图小像；骸翼兽采用灰骨身体，咬击／吐息独立编排。源图由内置imagegen生成，按追加要求降低饱和度、精简颜色；采用关键姿态与位移／特效组合，没有宣称所有动作逐帧重绘。', '', '日冠聚光早期设计为光束，本次实际初版为纯金白集中光球（聚光弹），一次命中；石翼兽／骸翼兽头像同步新形象，骸卫／裂目兽头像由自身原地图帧裁出。', '', '单次接触tick：裂石爪26、骸颚撕咬38、其余34，时间轴50fps；正常反击／追击来自交锋序列。', '', '| 运行素材 | 尺寸 | 实际字节 | 可见RGB色数／上限 |','|---|---|---:|---|']
md += [f'| [{Path(x["file"]).name}]({href(A/x["file"])}) | {x["actual_size"]} | {x["actual_bytes"]} | {x["visible_colors"]}／{x["palette_limit"]} |' for x in artrows]
md += ['', '[素材清单](art-manifest.json) · [实际姿态绑定](../../data/innate_attack_art.json) · [切图脚本](../../tools/build_innate_enemy_art.py)', '', '提示词与来源：art-generation.json包含石翼初版、最终调色修订与灰骨骸翼姿态生成的提示词记录；鸟形初版只有明确标注的摘要，原文保留在聊天工具调用记录，摘要不冒充原文。']
md += ['- ['+p.name+']('+href(p)+')' for p in source_records] or ['- 完整提示词记录待落盘，不能从图片反造历史工具调用。']
md += ['', '## 后台画面','', shot_status, '', '[截图元数据](captures.json)' if captures else '截图元数据尚未落盘。', '', '地图／状态页来自新部署后的隔离存档；演出接触与收势为受控show_frame帧展示，不是自然交锋或通关证据。', '', '本页静态HTML由本目录`build_report.py`读取已有JSON生成，无需浏览器fetch。截图元数据更新后运行`python3 actual/reports/enemy-deployment-20261023/build_report.py`重建页面。']
(R/'README.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'checks':{x['name']:x['count'] for x in checks},'screenshots':len(validshots),'source_records':len(source_records),'passed':all(x['passed'] for x in checks)},ensure_ascii=False))
