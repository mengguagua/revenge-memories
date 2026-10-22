#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync final chapter-five spatial facts, preserving earlier chapter cards."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-redesign-20261022';DOC=R.parent/'docs2/完整游戏流程.md'
CODES=['M51','F51','M52','F52','J53','J54','S51']
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def point(p):return '('+','.join(str(int(n))for n in p)+')'
def points(ps):return '、'.join(point(p)for p in ps)
CONTENT={
'M51':dict(title='王都内廷 · 双病房与南向撤离',composition='北殿与东西病房围成内廷，南照护院位于横向院墙后；宫前中轴、病房南门横廊与后撤门形成可理解的救护线路。',main_route='从南院沿中轴进入病房前横廊，接应东西门槛的伤兵，再护送穿过两道院墙中央口抵达南出口。',side_route='东西病房侧廊可换线，东外侧通道连接固定援军入口；宫前横廊可接近守卫长侧面。',tradeoff='开病房只解除伤兵锁定，不拆除建筑碰撞；先压住门外守军再放行，更容易保护两组。两病房都须确认，至少一组撤离并击败首领。',story='神军拘押赫兰带来的伤兵。D51中赫兰违令打开南侧后撤门，留下照护与受审；他不成为可攻击单位，也不加入正式队伍。蕾娜濒死或缺席时由投降军官协助。'),
'F51':dict(title='祭所底层 · 双防护院与检修水渠',composition='地下主渠分开两处错位修复院，连续石墙与双格南门保护地方工班；完整调节器、工作面、北值守阶与检修物资明确设施用途。',main_route='从西南接应处进入第一修复院，交接后保护工班，再经中段两格检修桥和东院南廊前往第二修复区。',side_route='南端一格维护桥距离更长，可绕开中央守军；东西渠边上廊连接北值守区，桥头石台留出转向空间。',tradeoff='每处交接分别计算等待回合，确认当回合还不能离开防护责任；两工班都必须存活。南桥绕行与主桥集中推进各有代价，第3回合东南援军保持。',story='艾琳把两处地方循环交到工班手中。未开始和已接通的工班由防护区接应，交接中的作业面需要护卫保护到下一己方回合；不依赖唯一正式术士，也不把队员永久留在装置上。'),
'M52':dict(title='登天桥 · 三段窄桥与落脚承台',composition='三段真实跨水石桥连接东西岸与两处中间承台，桥面各有三格净宽，完整石柱和通行带外护栏说明支撑与边界。',main_route='西岸出发沿错位桥段逐个抵达三个桥锁，依西到东解除后继续攻向东岸桥卫统领。',side_route='两处承台南侧设整队支台，西岸和东岸各有回廊；飞行者可以越水侧援，但不能代替桥锁确认。',tradeoff='桥口便于集中防守，也会限制大队展开；可在承台换队和等待后卫，避免所有人挤进同一狭口。第4回合援军由西岸落脚平台进入。',story='桥仍连接两岸，西队要分段解除控制并向神宫入口推进。桥外水域不可步行，没有随机坠落；飞行绕侧翼也不能跳过从西到东的解锁步骤。'),
'F52':dict(title='日宫下层 · 错位翼院与中央水庭',composition='完整院墙、两组错位门阵和中央水庭构成下层宫院，北主殿、四根完整石柱与南横廊建立前后层次。',main_route='从西南门先接近较近的西门阵，沿南横廊进入更深的东翼，确认两处后沿中央石桥推进神官前庭。',side_route='两翼内侧窄巡廊连到主殿侧面；西翼门前较宽，东翼需穿两格隔墙口，接敌距离与换线条件不同。',tradeoff='门阵必须在各装置南面分别确认，走过不会自动完成；两处确认都不能由击败神官替代。中央石桥直接，但两侧水庭限制横向展开。',story='艾琳先核对两座门阵与祭所的联系，解除集中控制而保留供给居民的一端；两翼完成后打开东门，可先探索旧书库，也可前往前庭整备。'),
'J53':dict(title='神宫前庭 · 双入口与会合横廊',composition='两军分别从西南、东南柱列入口进入左右庭，两座内池分开中央阶口与两翼阵台；北殿构成共同推进方向。',main_route='双方先沿本侧庭路确认门阵，再在中层横廊会合，经过中央阶梯或上层侧廊接近统领。',side_route='后方联络廊允许跨翼支援，上层侧廊可绕过中央阶口；两条横向联络线让一侧受压时可以重新分配队员。',tradeoff='两翼各有守军，分头推进较快但需要照顾弱领队；确认后不用永久站点。双主角必须存活，双方原队归属与各最多十人部署保持。',story='胡纳普与艾琳从两处入口进入同一前庭，各自处理本翼，再共同接应。伤者留在整备处，战后可返回检查装备与剩余救治，再向神座推进。'),
'J54':dict(title='神座终战 · 三阶口与回转攻击台',composition='神座位于北端上层中轴，中央仪道与东西阶廊汇入攻击平台；池水、柱脚和后方横廊组织前进与撤退空间。',main_route='两军从南侧入口展开，沿中央阶梯接近神座，或先处理两翼飞行敌与术士后从侧阶进入上层。',side_route='东西上层回廊可以换位，后方池旁横廊连通两军入口，为治疗者、弱领队和后撤单位留出通路。',tradeoff='阶梯只有踏步可走，栏柱真实阻挡；首领周围留出近战、法术和半血援军空间。普通武器与法术始终有效，半血仅一次强化与召唤，不回血。',story='D52保留神记得救人、两岸仍失去家人的对峙；对话结束后真正作战。实体沿用现有法术角色动作与独立战役身份，败北后晨光和地方循环继续，不触发旧多玛专属终结规则。'),
'S51':dict(title='神宫旧书库 · 双阅览翼与北原件',composition='北侧档案楼朝南，两侧木地板阅览室布置完整书架与阅览桌，石廊连接南门；北封闭旁室保留不能进入全部房间的叙事。',main_route='从南门沿中轴到北档案楼南面取回原件，击败守卫后沿同一条可辨认的中轴回南门交接。',side_route='西阅览室有南门和东门，东阅览室有南门和西门，书架前后的通道允许从两翼换线接近守军。',tradeoff='完整书架占三乘三格，不是可穿行背景；封闭旁室没有任务目标或额外宝物。支线可在合军前完成，错过仍可完成主线，不要求清空所有敌人或角落。',story='把早年救援、失败试验与后来的强迁命令一起带回，不只抄对己方有利的部分。北侧取原件与南门交接是两项操作，合流后不再折返，也不补发未取得的记录。')}
def details(c,d):
 o={x['id']:x for x in d['objects']};at=lambda k:point(o[k]['position']);front=lambda k:point(o[k]['approach']);out=point(d['exit'])
 npc=lambda k:point(next(u['position']for u in d['npc_units']if u['id']==k))
 if c=='M51':return f'西病房对象{at("ward_1")}从{front("ward_1")}确认，西伤兵在{npc("royal_wounded0")}门槛；东病房对象{at("ward_2")}从{front("ward_2")}确认，东伤兵在{npc("royal_wounded1")}。ward只解除NPC锁定，不修改opens或建筑碰撞。y=20与y=26两道院墙均仅在x=15—17留出三格中轴口，实际撤离格为{out}。'
 if c=='F51':return f'第一修复区对象{at("repair_1")}、南面交接格{front("repair_1")}，工班在{npc("repair_team0")}；第二区对象{at("repair_2")}、交接格{front("repair_2")}，工班在{npc("repair_team1")}。西院南口为(8,15)、(9,15)，东院南口为(26,21)、(27,21)；桥头留石质转向廊。出口字段{out}仅为南侧接应位置，不是工班撤离目标。'
 if c=='M52':return '三个桥锁依次位于'+points([o[k]['position']for k in ['bridge_1','bridge_2','bridge_3']])+f'，须同格确认。三段净通行带为x=7—12/y=12—14、x=16—22/y=10—12、x=26—32/y=13—15，护栏位于通行带外；东岸出口{out}不替代桥锁与首领条件。'
 if c=='F52':return f'西门阵对象{at("lower_west")}须在南面{front("lower_west")}确认；东门阵对象{at("lower_east")}须在南面{front("lower_east")}确认。中央双格石桥沿x=17—18贯通水庭，南出口字段{out}不是撤离任务。'
 if c=='J53':return f'西门阵对象{at("court_west")}、南面操作格{front("court_west")}；东门阵对象{at("court_east")}、南面操作格{front("court_east")}。中层横廊与后方横廊均连接双军入口；出口字段{out}不作为单队先行通关条件，中央阶梯两侧栏柱不可通行。'
 if c=='J54':return f'本图没有可交互对象。实体首领位于'+point(next(u['position']for u in d['enemies']if u['id']==d['boss_id']))+f'，固定半血召唤源(16,10)及邻近攻击平台保留合法落脚格。targets记录首领目标，不新增站点任务；南出口字段{out}不参与击败本体判定。'
 return f'原件对象{at("old_record")}须从档案楼南面{front("old_record")}取回；击败守卫后在南门{at("archive_exit")}同格交接，该格也与exit{out}一致。西阅览室南口(7,20)/(8,20)、东口(12,13)/(12,14)；东阅览室南口(22,21)/(23,21)、西口(19,16)/(19,17)。北封闭旁室及墙后夹层不放任何任务锚点。'
def run():
 stages={c:read(R/f'data/stages/{c}.json')for c in CODES};notes=[]
 for c,d in stages.items():
  folder='west'if c.startswith('M')else'finale'if c.startswith('J')else'east';report=f'{folder}/{c}-design.json';detail=read(O/report);sha=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest();assert detail.get('map_sha256',detail.get('stage_sha256'))==sha,('stale design',c)
  n={k:v for k,v in CONTENT[c].items()if k!='story'};n.update(code=c,source_reports=[report],name=d['name_zh'],size=[d['map']['width'],d['map']['height']],routes=d.get('tactical_routes',[]),map_sha256=sha);notes.append(n)
 write(O/'design-notes.json',{'date':'2026-10-22','revision':'0.10.9-ch5','reference':'沿用已确认M41与前四章的整体空间、主次路线、任务位置协同设计；第五章低饱和原生建筑与石材','maps':notes})
 old=DOC.read_text();text=old.replace('版本：流程同步稿1.13；','版本：流程同步稿1.14；')
 announcement='2026-10-22第五章重新构图（地图修订0.10.9-ch5）：七图重做病房内廷、分段登天桥、双修复防护院、错位门阵、书库阅览翼与双军前庭/神座平台。按完整建筑、真实踏步、石桥落脚和两队调动空间重排部署、守军、NPC、操作格与出口，身份数值、剧情、时机、胜败规则和人物动画保持。当前地图与说明见[第五章七图设计与复查](../actual/reports/chapter5-redesign-20261022/index.html)；本段同步设计，实机通关与连续流程结果由独立验收报告记录。'
 if announcement not in text:text=text.replace('\n## 一、沿用设定与需要新做的部分','\n'+announcement+'\n\n## 一、沿用设定与需要新做的部分')
 text=text.replace('### 第5章〔已实现 · 0.10.0〕','### 第5章〔已实现 · 地图修订0.10.9-ch5〕')
 for c,d in stages.items():
  pattern=rf'(#### {c} [^\n]+\n)(.*?)(?=\n#### |\n## |\Z)';match=re.search(pattern,text,re.S);assert match,c;card=match.group(2)
  card=card.replace('[实际地图与试玩截图](../actual/reports/chapter5/index.html)','[当前地图与设计复查](../actual/reports/chapter5-redesign-20261022/index.html)')
  def paragraph(label,value):
   nonlocal card
   block='**'+label+'：**'+value
   if re.search(r'\*\*'+re.escape(label)+r'：\*\*[^\n]*',card):card=re.sub(r'\*\*'+re.escape(label)+r'：\*\*[^\n]*',block,card,count=1)
   else:card=card.replace('**目标与失败：**',block+'\n\n**目标与失败：**',1)
  boss=next(u for u in d['enemies']if u['id']==d['boss_id'])
  paragraph('地点与空间',f'世界节点{d["node"]}；{d["map"]["width"]}×{d["map"]["height"]}格，16像素一格。首领{point(boss["position"])}；'+('西／东各10个部署候选。'if c.startswith('J')else f'单队{len(d["player_positions"])}个部署候选。'))
  paragraph('剧情与地图',CONTENT[c]['story']);paragraph('地图调整',' '.join(d['tactical_notes']))
  paragraph('路线与战术',CONTENT[c]['main_route']+' '+CONTENT[c]['side_route']+' '+CONTENT[c]['tradeoff'])
  dep='西队：'+points(d['player_positions_by_route']['alm'])+'；东队：'+points(d['player_positions_by_route']['celica'])+'。'if c.startswith('J')else points(d['player_positions'])+'。'
  paragraph('部署与空间',dep+f'出口字段G {point(d["exit"])}；targets：{points(d["targets"])}。G或targets是否参与判定，以本关规则为准。')
  if d['npc_units']:paragraph('任务NPC','；'.join(u['name_zh']+'（'+u['id']+'）'+point(u['position'])+('〔初始锁定〕'if u.get('locked')else'')for u in d['npc_units'])+'。任务NPC生死独立记录，未成为正式成员前不套用濒死救治。')
  if d['reinforcements']:paragraph('增援落点',f'第{d["reinforcement_turn"]}敌回合：'+'；'.join(u['id']+'／'+u['name_zh']+point(u['position'])for u in d['reinforcements'])+'。提前一回合预告，按原控制器处理落点占用。')
  paragraph('门、接应与操作位置',details(c,d))
  if d['objects']:
   table='| 实际对象 | 对象格 | 操作位置 |\n|---|---|---|\n'
   for o in d['objects']:
    op='指定南面格'+point(o['approach'])+'确认'if 'approach'in o else'站在目标格'
    table+='| '+o['label']+' | '+point(o['position'])+' | '+op+' |\n'
   card,n=re.subn(r'\| 实际对象 \| 对象格 \| 操作位置 \|\n(?:\|[^\n]*\n)+',table,card,count=1);assert n==1,c
  if c=='M51':card=re.sub(r'南口实际位于[^\n]*',f'南口实际位于{point(d["exit"])}，伤兵经病房南横廊与两道院墙中央缺口沿铺道后撤。',card,count=1)
  if c=='F51':paragraph('目标与失败','分别站在装置南面交接，每个工班各自保护到下一己方回合，且首领败北。两工班均须存活；未交接与已完成的工班处于防护状态，交接中需要护卫。所有战场在场主角濒死立即失败。')
  text=text[:match.start(2)]+card+text[match.end(2):]
 assert old[old.index('### 第1章'):old.index('### 第5章')]==text[text.index('### 第1章'):text.index('### 第5章')],'chapter1-4 modified'
 assert old[old.index('## 七、'):]==text[text.index('## 七、'):],'later global flow sections modified'
 for c,d in stages.items():
  card=re.search(r'#### '+c+r' .*?(?=\n#### |\n## |\Z)',text,re.S).group()
  assert f'{d["map"]["width"]}×{d["map"]["height"]}格'in card
  for p in d['player_positions']:assert point(p)in card
  for u in d['npc_units']:assert '（'+u['id']+'）'+point(u['position'])in card
  for u in d['reinforcements']:assert u['id']+'／'+u['name_zh']+point(u['position'])in card
  for o in d['objects']:
   assert '| '+o['label']+' | '+point(o['position'])+' |'in card
   if 'approach'in o:assert '指定南面格'+point(o['approach'])+'确认'in card
  assert '出口字段G '+point(d['exit'])in card
 DOC.write_text(text)
 write(O/'document-sync.json',{'passed':True,'document':'docs2/完整游戏流程.md','version':'1.14','revision':'0.10.9-ch5','design_only_no_new_play_claims':True,'maps':[{'code':n['code'],'map_sha256':n['map_sha256'],'size':n['size']}for n in notes],'checks':['Seven final map hashes match their agent design reports.','All deployments, route-specific joint deployments, bosses, NPCs, fixed reinforcements, object/approach coordinates, targets and exits synchronized.','M51 ward confirmation only unlocks NPCs; no invented wall opens. M52 three-cell bridge lanes and sequence recorded.','F51 separate per-crew next-player-turn handoff, F52 south-facing operations, S51 north record/south handoff and closed annexes clarified.','J54 fixed(16,10) one-wave summon remains existing behavior, not a new control objective.','Chapter1-4 text and section7 onward retained exactly.'],'document_sha256':hashlib.sha256(DOC.read_bytes()).hexdigest()})
 print('Chapter-five design notes and flow v1.14 synchronized; no new play claims.')
if __name__=='__main__':run()
