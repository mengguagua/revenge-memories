from pathlib import Path
import json,hashlib,shutil,subprocess,html
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'actual/reports/chapter-feedback-20261103'
RAW=ROOT/'source/chapter-feedback-20261103/screenshots';RAW.mkdir(parents=True,exist_ok=True)
logic=json.loads((OUT/'logic.json').read_text());visual=json.loads((OUT/'visual.json').read_text())
images=[]
for name in visual['screenshots']:
    source=OUT/name;original=RAW/name
    if source.exists():shutil.copy2(source,original)
    dest=OUT/(Path(name).stem+'.webp')
    subprocess.run(['/opt/homebrew/bin/magick',str(original),'-define','webp:lossless=true',str(dest)],check=True)
    size=subprocess.check_output(['/opt/homebrew/bin/magick','identify','-format','%wx%h',str(dest)],text=True)
    images.append({'file':dest.name,'usage':'后台实际运行截图','pixels':size,'bytes':dest.stat().st_size,'reason':'原尺寸无损WebP，保留像素文字与材质' if dest.stat().st_size>=200000 else ''})
    if source.exists():source.unlink()
old=json.loads((OUT/'combat-rules-before.json').read_text())
verified={k:{'before':v,'after':hashlib.sha256((ROOT/k).read_bytes()).hexdigest()} for k,v in old.items()}
assert all(v['before']==v['after'] for v in verified.values())
assert not logic['errors'] and not visual['errors']
(OUT/'verification.json').write_text(json.dumps({'headless_checks':logic['checks'],'background_checks':visual['checks'],'errors':[], 'combat_rules_unchanged':verified,'images':images,'scope':'定向逻辑与后台运行截图；宽屏2556×1179（刘海安全区）和窄屏1334×750；未运行完整战役，未安装iPhone。'},ensure_ascii=False,indent=2)+'\n')
E=html.escape

def img(name,caption):
 return f'<figure><a href="{name}.webp"><img loading="lazy" src="{name}.webp" alt="{E(caption)}"></a><figcaption>{E(caption)}</figcaption></figure>'

table=''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td><td>{f}</td></tr>' for a,b,c,d,e,f in [
('剑','铜','1','95','0','1'),('剑','铁','2','90','0','1'),('剑','钢','4','80','1','1'),
('枪','铜','1','90','0','1'),('枪','铁','2','85','0','1'),('枪','钢','4','80','1','1'),
('弓','铜','1','80','0','1～3'),('弓','铁','2','75','0','1～3'),('弓','钢','3','70','1','1～5')])
shots=img('forecast-factions','攻击前预览：我方蓝底、敌方红底；保留完整原边框与内容内边距')+img('preparation-menu','整备菜单删除重复的保存入口，世界外层菜单保留保存进度')+img('sea-city-medic','推车变成不可交互的场景摆设；女医者使用疗愈师职业地图形象')+img('medic-dialogue-p1','面向女医者交谈，正常安置劳工并推进日返仪式前置条件')+img('chapter2-class-cast','卡洛：佣兵；米蕾：疗愈师；莉莎：女魔道士，按当前职业选择形象')+img('status-touch-safe','状态详情正文点击保持打开，箭头切换成员，确认／返回关闭')
extra=''.join(img(Path(name).stem,Path(name).stem) for name in visual['screenshots'] if Path(name).stem not in ['forecast-factions','preparation-menu','sea-city-medic','medic-dialogue-p1','chapter2-class-cast','status-touch-safe','worker-waits-for-clear-route','rescue-rules-p3','rescue-rules-p4','chapter2-intro-p1','chapter2-departure-task','chapter2-sea-task','compact-sea-task','compact-sea-task-p2'])
content=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>海峡城与第二章反馈 · 2026-11-03</title>
<style>body{{margin:0;background:#101820;color:#e6e7e8;font:16px/1.75 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:36px 24px 72px}}h1,h2,h3{{line-height:1.4;color:#ead6a5}}h1{{font-size:30px}}h2{{margin-top:46px;font-size:24px}}h3{{font-size:19px}}p{{max-width:960px}}a{{color:#8fc8ef}}nav{{display:flex;flex-wrap:wrap;gap:14px;padding:16px 0}}.card{{padding:20px 24px;background:#1b2834;border-radius:10px;margin:18px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:20px}}figure{{margin:16px 0}}img{{display:block;width:100%;height:auto;border-radius:6px}}figcaption,.muted{{font-size:14px;color:#b3bdc7}}table{{border-collapse:collapse;width:100%;margin:14px 0;background:#182530}}th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #35424d}}th{{color:#ead6a5}}.scroll{{overflow-x:auto}}select{{font:inherit;padding:5px 12px;color:#fff;background:#253749;border-radius:6px;margin-right:14px}}code{{background:#263542;padding:2px 5px}}.badge{{display:inline-block;color:#bde6c2;background:#203c31;padding:4px 12px;border-radius:20px}}details{{margin:20px 0}}summary{{cursor:pointer;color:#ead6a5}}@media(max-width:700px){{.grid{{display:block}}main{{padding:24px 14px}}td,th{{padding:7px}}}}</style>
<main><p class="muted">REVENGE MEMORIES · 本地修改与运行验收 · 2026-11-03</p><h1>海峡城与第二章：9项反馈</h1><span class="badge">已完成界面、人物、任务文案修改</span><p>劳工停步与全救奖励已按真实代码及现有存档副本核对。命中率仅分析，战斗公式、武器参数与成长奖励不变。</p>
<nav><a href="#workers">劳工与奖励</a><a href="#accuracy">命中率与钢武器</a><a href="#changes">界面与人物</a><a href="#tasks">任务与地名</a><a href="#validation">验证与文件</a></nav>
<h2 id="workers">1–2 · 劳工何时移动？全救有什么奖励？</h2>
<div class="card"><p><strong>开门即解除锁定，在我方阶段结束时自动行动。</strong>没有“开门后再等固定几回合”的规则。劳工会评估敌军下一步可移动并攻击到的范围；危险路线会停止，必要时向安全格退避。同伴占住落脚格也会影响前进。</p><p>在2026-11-02留存的第4回合存档副本中，第二队劳工位于(27,21)，已开门、尚未行动，计算结果是<strong>敌军可达，等待清路</strong>。这是路线风险判断，没有另设等待回合。</p><p>胜利条件是：<strong>至少一队开门解救且存活，击败或使科兰投降</strong>。劳工不必实际走到出口。救一队与救两队的通关经验、装备结算相同；两队全救目前没有单独的额外奖。正常通关仍有钢剑、钢弓；访问点与首领掉落独立于救援队数。救两队的直接区别是多保住一队劳工，并多一份存活保障。</p><p>本次增加劳工悬浮卡的开门／等待清路／自动前进状态，以及战斗菜单“战场目标”内的救援与奖励说明；没有改动劳工AI或奖励。</p></div>
<div class="grid">{img('worker-waits-for-clear-route','现有第4回合存档副本：已开门，敌军可达，等待清路')}{img('rescue-rules-p3','战场目标补充：至少救一队、存活、不要求走到出口；全救无额外奖励')}</div>
<h2 id="accuracy">3 · 命中率怎样计算？钢武器是否合理？</h2>
<div class="card"><p><strong>物理命中 = 武器基础命中 + 攻击者技巧 − 目标地形回避 − 目标攻速</strong>，最终限制在0～100。攻速 = max(0，有效速度 − 本次武器重量)。物理命中不额外加攻击者幸运。</p><p>自己的钢武器重量不直接扣自己的命中，而是降低自己的攻速：敌人更容易打中自己，也可能失去追击。只要攻速比对手高就能多攻击一次，低1点可能正好跨过门槛。</p><p>法术通常是<strong>法术基础命中 − 目标有效幸运 − 目标有效速度</strong>，不扣地形回避；魔法盾会令该类命中变成10。引霆剑使用物理命中公式，个人月枪合法使用时命中100。普通攻击按0～99的一次随机判定，命中值没有二次随机加成。</p></div>
<h3>当前铜、铁、钢参数</h3><div class="scroll"><table><thead><tr><th>类别</th><th>材质</th><th>威力</th><th>基础命中</th><th>重量</th><th>射程</th></tr></thead><tbody>{table}</tbody></table></div>
<h3>同一存档角色、同一目标的对照</h3><p>以下由引擎直接计算。角色取第4回合存档：胡纳普9级（力12／技9／速9），奥托2级（力14／技6／速4），达恩8级（力13／技7／速4）。地形回避可切换；这只是条件对照，不移动存档中的角色或敌人。</p>
<label>目标 <select id="target"><option>重装兵</option><option>骑士</option></select></label><label>目标地形回避 <select id="avoid"><option>0</option><option selected>20</option><option>40</option></select></label>
<div class="scroll"><table><thead><tr><th>角色</th><th>武器</th><th>命中</th><th>每击伤害</th><th>攻速</th><th>攻击次数</th><th>平均总伤害*</th></tr></thead><tbody id="sample"></tbody></table></div><p class="muted">*只按命中×伤害×攻击次数估算，忽略必杀、提前击杀与反击致死。用于比较条件，不代表一次战斗的保证伤害。</p>
<div class="card"><p><strong>判断：威力换命中的方向合理，但钢剑在前期的代价偏重。</strong>钢枪相对铁枪只少5点命中、多2威力；钢弓少5点命中、多1威力，同时扩到5格，取舍较清楚。钢剑少10点命中、多2威力，再叠加重量，会让低技巧角色感觉很不稳定。</p><p>例如胡纳普对回避20的重装兵，铁剑77%／每击5／两击，平均7.70；钢剑67%／每击7／两击，平均9.38。钢剑破甲收益存在，但两次中至少失误一次的概率由40.71%上升到55.11%，不适合要求稳定命中的收尾。</p><p>另一个临界例：速度6、对方攻速5，铁剑攻速6可追击；钢剑攻速5便失去追击。此时钢武器增加的单击伤害未必抵得过少打一击。</p><p>建议使用方向：铁武器负责稳定收尾，钢武器在能保住追击、确实需要破甲或钢弓远射时使用。若后续调整，优先单独评估钢剑基础命中80→85，保留重量与伤害；<strong>本次未实施任何数值调整</strong>。核心战斗文件及装备参数的修改前后SHA-256完全一致。</p></div>
<h2 id="changes">4–8 · 界面、人物与触控</h2>
<div class="card"><ul><li>攻击预览按阵营填充：我方蓝底、敌方红底；沿用原边框材质，文字与HP格保留安全内边距。</li><li>删除部队整备中的重复“保存进度”。外层世界菜单的保存入口保留。</li><li>海峡城推车变为非交互场景物，旁边增加女医者；与她交谈仍正常安置劳工。</li><li>风灯岛三人按当前职业显示：卡洛佣兵、米蕾疗愈师、莉莎女魔道士。死亡替代船长分支仍按既有NPC处理。</li><li>方向键中心按屏幕约10px左调，取最近的原生像素避免模糊：4倍显示为8px，3倍显示为9px。左侧空间较紧，同步收紧水平间距，按钮仍完整留在安全区内，右键远离中央游戏区。</li><li>状态详情、任务日记正文点击保持打开；左右箭头或方向键仍可切换／翻页，确认与返回可关闭。剧情对话仍保留点击继续的操作。</li></ul><p>状态页是阅读面板，不适合把正文当作关闭按钮。取消这个快捷关闭可以避免误触丢失阅读位置，又不影响明确的返回操作。</p></div>
<div class="grid">{shots}</div>
<h2 id="tasks">9 · 第二章背景与真实目的地</h2>
<p>根因是后续章节把当前关卡标题直接拼接成“前往＋名称”。现将第二至五章的26个主线阶段逐项写成“发生了什么／为什么去／去哪里做什么”；战后任务也补具体人物、线索和地点。</p><p>第二章开场明确：母亲薇娅两年前带伤者出航后失踪，艾琳追查旧船，先向卡洛问船牌。确认出航后，日记说明追查押送舰的线索、离开风灯岛并突破外海封锁。</p><p>世界节点18改名<strong>风灯岛外海</strong>；<strong>海上拦截</strong>继续作为战斗名称。剧情与任务不再把战斗动作标题当地点。主线顺序、解锁条件、关卡ID和路线均未改变。</p>
<div class="grid">{img('chapter2-intro-p1','第二章开场：说明母亲失踪与寻找旧船的背景')}{img('chapter2-departure-task','出航前任务：原因、人物、所在地点和下一步')}{img('chapter2-sea-task','确认出航后：驶向风灯岛外海，寻找押送舰线索')}{img('compact-sea-task','窄屏日记正常换行与分页，全部文字留在纸页安全区')}</div>
<h2 id="validation">验证与可复查文件</h2><p>{logic['checks']}项无窗口定向检查、{visual['checks']}项后台运行／布局检查通过。覆盖劳工开门与安全路线、救1/2队结算一致、旧据点位置避让、女医者真实交互、第二章开场流程、职业资源加载、状态与日记触控、全部26条主线任务在宽／窄屏下的分页与文字边框间距。未运行完整战役回归，未安装或更新iPhone。</p>
<p><a href="logic.json">逻辑结果与命中对照数据</a> · <a href="visual.json">后台检查结果</a> · <a href="verification.json">战斗文件校验与图片尺寸／体积</a> · <a href="../../data/current_tasks_20261103.json">全部新主线任务文案</a> · <a href="../../tests/chapter_feedback_20261103.gd">定向检查脚本</a></p>
<p class="muted">运行素材均复用现有资源。本页截图为原尺寸无损WebP，原始PNG保存在工程根目录 source/chapter-feedback-20261103/screenshots。</p><details><summary>其余实际运行截图</summary><div class="grid">{extra}</div></details></main>
<script>const rows={json.dumps(logic['evidence']['hit_comparisons'],ensure_ascii=False)};const target=document.querySelector('#target'),avoid=document.querySelector('#avoid');function render(){{document.querySelector('#sample').innerHTML=rows.filter(r=>r.target===target.value&&r.avoid===+avoid.value).map(r=>`<tr><td>${{r.actor}}</td><td>${{r.weapon}}</td><td>${{r.hit}}%</td><td>${{r.damage}}</td><td>${{r.attack_speed}}</td><td>${{r.strikes}}</td><td>${{r.expected.toFixed(2)}}</td></tr>`).join('')}};target.onchange=avoid.onchange=render;render();</script></html>'''
(OUT/'index.html').write_text(content)
readme=ROOT/'actual/README.md';s=readme.read_text();line='2026-11-03 海峡城与第二章反馈：补充劳工开门、阶段末自动行动与危险路线等待的提示，说明全救无额外奖励；攻击预览改我方蓝、敌方红，整备菜单删除重复保存，旧塔内院增加可交互女医者、推车改场景物，风灯岛三人按职业显示。方向键中心按屏幕约10px左调并保证安全区，状态/任务日记正文不再点击关闭。第二至五章26个主线任务补背景与实际目的地，世界“海上拦截”节点改为“风灯岛外海”。命中与钢武器只分析，公式和参数不变。[规则分析、实际截图与定向验证](reports/chapter-feedback-20261103/index.html)。未安装或更新iPhone。\n\n'
if not s.startswith('2026-11-03 海峡城与第二章反馈'):readme.write_text(line+s)
print(json.dumps({'images':len(images),'max_bytes':max(r['bytes'] for r in images),'over_200k':[(r['file'],r['bytes']) for r in images if r['bytes']>=200000],'headless_checks':logic['checks'],'background_checks':visual['checks'],'combat_files_unchanged':True},ensure_ascii=False))
