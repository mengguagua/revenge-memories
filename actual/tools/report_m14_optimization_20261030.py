# -*- coding: utf-8 -*-
from pathlib import Path
from html import escape as e
from PIL import Image
import json, subprocess
R=Path(__file__).resolve().parents[2]; O=R/'actual/reports/m14-optimization-20261030'
def read(p):return json.loads(p.read_text())
logic=read(O/'logic.json');visual=read(O/'visual.json');assert not logic['errors'] and not visual['errors']
stage=read(R/'actual/data/stages/M14.json');ledger=read(O/'enemy-changes.json');buildings=read(O/'buildings.json')
rules=read(R/'actual/data/legacy/rules_full.json');tune=read(R/'actual/data/campaign_promotions_20261030.json');names=read(R/'actual/data/class_names.json')
for k,v in tune['bases'].items():rules['promotion_bases'][k].update(v)
for c in tune['levels']:
 for p in rules['promotions']:
  if p['from_class']==c['from_class'] and p['to_class']==c['to_class']:p['level']=c['level']
base_names=read(R/'actual/data/legacy/campaign.json')['classes']
def name(cid):return names.get(str(cid),{}).get('name_zh',base_names[str(cid)]['name_zh'])
def table(head,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+e(str(x))+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+e(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
images=[]
def fig(n,title):
 p=O/(n+'.png');q=p.with_suffix('.webp');subprocess.run(['/opt/homebrew/bin/magick',str(p),'-define','webp:lossless=true',str(q)],check=True)
 with Image.open(q) as im:size=list(im.size)
 images.append({'file':q.name,'pixels':size,'bytes':q.stat().st_size,'purpose':title,'quality':'原尺寸引擎截图，无损 WebP；超过参考体积时保留文字清晰度。'})
 return f'<figure><a href="{q.name}"><img loading="lazy" src="{q.name}" alt="{e(title)}"></a><figcaption>{e(title)}</figcaption></figure>'
change_rows=[['1','教堂墙体','南墙两侧禁止通行，中央门道保留；旧档墙内位置移到门道。'],['2','进阶数值','重装兵：生命32、力量13、物防10；壁垒卫士：力量19、物防16；女法师所需等级12。'],['3','教堂出口','回到南岗押送所右上阶梯下方，主角面朝正面。'],['4','装备行囊','相同装备按道具身份合并显示数量；领取或换装只处理其中一件。'],['5','拒阵枪','重量3→2，命中85→90，与普通枪基础命中一致。'],['6','台词','删除“塔里的劳工也得有路出来。”，保留“那就拿下哨卡。”。'],['7','敌军详情','敌军详情增加职业一行，并保留实际装备数值与远反说明。'],['8','指挥官','等级1、骑士；生命28、力量12、技巧5、速度8、幸运0、物防8、魔防2、移动8。'],['9','建筑区分','文书帐使用独立蓝顶亮门造型；其它访问点统一加开放入口。访问建筑显示地点名称，封闭军帐/粮库显示具体类型。'],['10','其余敌军','全部4级；每人合计随机分配5点至生命、力量、技巧、速度、物防、魔防。排除幸运与移动，分配固定保存。'],['11','兵种构成','中部的 M14_e6 士兵换成魔道士。总数12：指挥官1、骑兵3、士兵4、弓手2、魔道士2。']]
fields=['max_hp','strength','skill','speed','luck','defence','resistance','move'];labels=['生命','力量','技巧','速度','幸运','物防','魔防','移动']
enemytable=table(['单位','职业','等级']+labels,[[u['id'],u['class_name_zh'],u['level']]+[u[k] for k in fields] for u in stage['enemies']])
gaintable=table(['单位']+['生命','力量','技巧','速度','物防','魔防']+['合计'],[[u['id']]+[u['bonus'][k] for k in ledger['fields']]+[u['total']] for u in ledger['bonus']])
paths=rules['promotions']+[{'from_class':14,'to_class':t,'level':3} for t in rules['villager_options']]
promotable=table(['路线','等级']+labels[:6]+['魔防','移动'],[[name(p['from_class'])+' → '+name(p['to_class']),p['level']]+[rules['promotion_bases'][str(p['to_class'])][k] for k in fields[:6]]+['+15职业加成' if p['to_class']==10 else '-15职业加成' if p['from_class']==10 else '个人值保留',str(rules['class_move'][p['from_class']-1])+' → '+str(rules['class_move'][p['to_class']-1])] for p in paths])
benefits=table(['进阶路线','除补足下限以外的收益（当前已实现）'],[
 ['骑兵→骑士→大骑士','移动7→8→9，后续进阶路线。'],['士兵→重装兵→壁垒卫士','强化攻防定位；移动保持4。士兵原有限制的投枪、骑士杀手在进阶后可用。'],['弓箭手→狙击手→弓骑士','移动4→5→8；弓骑士射程固定1～5。'],['佣兵→剑士→剑豪','移动4→5→7；剑豪额外15魔防，并可继续转乡勇。'],['术法师→博学术师','获得恢复法术，所属阶段自疗5生命；已有法术训练继续累计。'],['疗愈师→济世术师','移动4→5；所属阶段为相邻同伴恢复5生命，新增圣光。'],['女法师→女魔剑士','可用剑与法术，新增恢复；本轮门槛20→12。'],['天马骑士→隼骑士','移动7→8，保留飞行，并获得对指定魔物的职业特效。']])
shots1=fig('chapel-wall','南墙前停止，不再站入墙体')+fig('chapel-exit','从教堂返回：阶梯下方、朝向正面')
shots2=fig('grouped-inventory','同名同种装备合并为一行，显示数量')+fig('repulsion-lance','拒阵枪：速度－2、命中基础不下降')
shots3=fig('commander-status','指挥官详情显示骑士；实际攻速包含投枪影响')+fig('promotion-rebalanced','按红框目标值计算的新进阶预览')
shots4=fig('visitable-tent','蓝顶文书帐：地点名称与可访问提示一致')+fig('closed-store','封闭粮料库：外观和说明不再与访问建筑混淆')
more=''.join(fig(n,t) for n,t in [('new-mage','M14中部新增魔道士'),('visit-M11','M11：雪原村舍'),('visit-M13','M13：文书帐同步更新'),('visit-S12','S12：林村诊所'),('visit-F21','F21：船员休息舱'),('visit-M31','M31：街边医舍')])
assets=[]
for p in (R/'actual/assets/visit-buildings-20261030').glob('*.png'):
 with Image.open(p) as im:size=list(im.size)
 assets.append({'path':str(p.relative_to(R)),'pixels':size,'bytes':p.stat().st_size,'purpose':'可访问文书帐32×40逻辑像素' if 'tent' in p.name else '开放入口16×20逻辑像素','quality':'保持透明边缘与原始比例，oxipng无损压缩'})
(R/'actual/assets/visit-buildings-20261030/manifest.json').write_text(json.dumps({'assets':assets,'originals':'source/m14-optimization-20261030/','generator':'built-in imagegen'},ensure_ascii=False,indent=2))
(O/'image-sizes.json').write_text(json.dumps({'assets':assets,'screenshots':images},ensure_ascii=False,indent=2))
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M14 · 旧塔外营优化</title><style>
*{box-sizing:border-box}body{margin:0;background:#101c25;color:#e0e6e7;font:16px/1.85 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1280px;margin:auto;padding:42px 24px 70px}h1{font-size:40px;line-height:1.3;color:#eddbaf}h2{font-size:26px;color:#eddbaf;margin-top:42px}h3{color:#c9b481;margin-top:28px}p{max-width:1000px}a{color:#dfc68b;text-underline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:22px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:18px 0;background:#0b131b;border-radius:10px;overflow:hidden}img{display:block;width:100%;height:auto}figcaption{padding:12px 18px;font-size:14px;color:#adbecb}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:12px 14px;border-bottom:1px solid #33434e;text-align:left;white-space:nowrap}th{color:#ddc78f;background:#1b303b}td:last-child{white-space:normal;min-width:80px}.note{padding:18px 24px;background:#223a32;border-radius:10px;margin:20px 0}.muted{color:#aebdca}details{background:#1a2b36;padding:18px 24px;border-radius:10px;margin:20px 0}summary{cursor:pointer;color:#dfc68b}li{margin:6px 0}a:focus-visible,summary:focus-visible{outline:0;box-shadow:0 0 12px #dec98d88}@media(max-width:760px){main{padding:24px 14px}.grid{grid-template-columns:1fr}h1{font-size:30px}}
</style><main><p class="muted">复仇与回忆 · 2026-10-30 · 本地运行验收</p><h1>M14 · 旧塔外营<br>地图、装备与职业调整</h1><p>本轮对应11项反馈。进阶参数采用补充图中的红字；全部游戏截图来自修改后的 Godot 运行视口。</p><nav><a href="#changes">修改清单</a><a href="#promotion">进阶与外传对比</a><a href="#enemies">敌军数值</a><a href="#visits">建筑访问</a><a href="#checks">验证记录</a></nav>'''
page+='<section id="changes"><h2>修改清单</h2>'+table(['项','内容','结果'],change_rows)+'<div class="grid">'+shots1+shots2+shots3+'</div></section>'
page+='''<section id="promotion"><h2>进阶究竟有什么收益？</h2><div class="note">结论：补足职业下限是即时属性收益；移动、射程、武器/法术权限和职业能力构成另一部分收益。等级归1提供继续成长的空间。高于下限的角色进阶时少涨数值，符合这套机制。</div><p>对照的是1992年FC《外传》。原版重装兵下限本来就是生命34、力量16、物防12，壁垒卫士力量22、物防18；本轮按你的指定降低，属于本作平衡调整。原作职业表与进阶机制可见 <a href="https://serenesforest.net/gaiden/classes/base-stats/">职业基础值</a>、<a href="https://serenesforest.net/gaiden/classes/promotion/">进阶规则</a>；进阶入口和基本玩法另对照 <a href="https://www.nintendo.co.jp/data/software/manual/man_FCNJ_00.pdf">任天堂官方说明书</a>。</p><p>“目标下限低”不会让现有属性变低：例如已有10技巧，目标下限为1，结果仍为10。以你截图里的奥托为例，新规则将生命26→32、力量10→13、物防6→10；已有的技巧、速度、幸运与个人魔防继续保留。</p>'''+benefits+'''<p>原版的弓骑士射程、博学术师自疗、济世术师邻格恢复和隼骑士对魔物能力，参考 <a href="https://serenesforest.net/gaiden/classes/introduction/">职业能力说明</a>；本作同时核对了 combat_rules.gd、item_rules.gd、unit_progression.gd 的实际实现。</p><p>等级归1不等于必然升级更快：经验仍受职业和等级系数共同影响；进阶本身也不提高个人成长率。普通进阶若六项属性都无需补足，当前实现会给生命上限+1（最多52）。</p><p>赫维的预览是用<strong>当前5级属性</strong>模拟进阶，不预估到12级之前的随机成长；真正达到12级时应再次查看预览。对于已经高于下限的法师，恢复法术与每阶段自疗5点往往比即时加点更重要。</p><h3>本轮后的完整普通进阶下限</h3><p>这些是最低保证值，不是固定加点。魔防列沿用你图中规则：个人魔防保留，剑豪职业加成单列。已获得的角色属性不会因目标下限调低而倒扣。</p>'''+promotable+'</section>'
page+='<section id="enemies"><h2>M14 敌军最终数值</h2><p>下表是裸属性。指挥官力量12、速度8；携带投枪后，状态页显示攻击15、实战速度6，这是投枪威力+3和重量2的结果。</p>'+enemytable+'<details><summary>查看每名非首领敌人的5点分配</summary><p>使用固定种子一次分配；每项最多获得2点，总和恰好5。魔道士替换先采用该兵种模板，再分配这5点。</p>'+gaintable+'</details><p>旧M14战斗存档按一次性版本迁移更新敌军；保持伤害缺口、阵亡状态、单位ID和战斗位置，同步更新重试快照，重复读取不会叠加。</p></section>'
page+='<section id="visits"><h2>访问建筑统一辨识</h2><p>检查了全战役15个访问点。M13、M14文书帐换成独立蓝色高顶帐；其它访问点使用亮灯开放入口。访问说明覆盖完整建筑占地，纯障碍军帐与粮库保持封闭外观和明确名称。</p><div class="grid">'+shots4+more+'</div>'+table(['场景','访问点','门口'],[[b['stage'],b['name'],str(b['fronts'])] for b in buildings])+'</section>'
page+=f'<section id="checks"><h2>验证记录</h2><div class="note">无窗口逻辑检查 {logic["checks"]} 项通过；后台运行与布局检查 {visual["checks"]} 项通过。</div><p>覆盖墙体阻挡与旧位置迁移、教堂出口朝向、进阶目标值、数量合并与单件领取、敌军旧存档加载和重试快照、访问奖励不可重复领取、两处哨卡控制，以及15个访问建筑的名称和素材路径。代表性运行界面已检查文字与边框间距。</p><p>本轮为功能与数据针对性验证，没有重跑完整战役，也未安装或更新 iPhone。后台截图使用不激活窗口保护。HTML进行了文件与链接检查。</p><p><a href="logic.json">逻辑检查明细</a> · <a href="visual.json">运行检查明细</a> · <a href="enemy-changes.json">敌军迁移与增幅原始记录</a> · <a href="buildings.json">全访问点清单</a> · <a href="image-sizes.json">图片尺寸与体积</a></p><details><summary>新增素材</summary>'+table(['素材','尺寸','字节','用途'],[[a['path'].split('/')[-1],str(a['pixels']),a['bytes'],a['purpose']] for a in assets])+'</details></section></main></html>'
(O/'index.html').write_text(page)
print('Report saved:',O/'index.html')
