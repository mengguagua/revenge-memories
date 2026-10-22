#!/usr/bin/env python3
"""Record the spatial correction without rewriting story or earlier chapters."""
from pathlib import Path
import json, hashlib, re
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter5-spatial-20261022'
DOC=R.parent/'docs2/完整游戏流程.md'
CODES=['M51','M52','F51','F52','S51','J53','J54']
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def point(p):return '('+','.join(str(int(v)) for v in p)+')'
def points(ps):return '、'.join(map(point,ps))
TEXT={
 'M51':[
  '王都内廷 · 室外宫院与可进入病房',
  '王都内廷保留室外院落与北殿；两病房采用去顶剖面呈现床位、内墙和真实南门，伤兵从门内候位走到救护横廊。',
  '从南侧照护院向北进入横廊，在病房门前确认接应，护送伤兵经实际门洞走向南侧后撤口。',
  '两病房外侧廊与宫前横廊可换线，室内床位和墙体不作为穿行捷径。',
  '王都内廷是室外宫院；可进入的病房用剖面显示内部，北殿仍为不进入的建筑外观。',
 ],
 'M52':[
  '登天桥 · 两端接岸的三段桥',
  '三段桥与中间承台维持连续，补清两端岸侧衔接及桥体支撑，使桥面跨越水域、承台承接通行的关系可见。',
  '从西端接岸处向东依次确认三个桥锁，在中间承台换队后继续抵达神宫入口。',
  '中间承台用于展开和接应，飞行支援仍不能替代桥锁顺序。',
  '原剧情明确为分三段的室外桥，桥边不可步行；不是漂在水中的独立房间。',
 ],
 'F51':[
  '祭所底层 · 地下水工与层间阶梯',
  '地下水渠和两处修复区保留，补清北侧上行阶梯的可走踏步与落脚处，以及南侧返回入口，使水工维修层和神宫通道有实际联系。',
  '由南侧进入维修层，交接第一工班后跨检修桥前往第二工班，完成保护并击败守卫。',
  '南维护桥与主桥形成两条跨渠路线；上行阶梯与设备操作面保持独立，不能踩设备代替走阶梯。',
  '“这一层得继续修”和进入神宫通道对应地下水工维修层，设备与水渠在室内设施中成立。',
 ],
 'F52':[
  '日宫下层 · 室内控制厅与双阵',
  '取消下层地坪中的整栋屋顶宫殿，改为去顶门厅与通廊；连续室内铺地、墙体、两翼阵台和人工水池共同表达神宫下层。',
  '从南侧入口进入下层控制厅，分别到两座阵台南面确认，再向北侧神官与门厅推进。',
  '中央池上通道较直接，两翼侧廊可换线；不同门洞与阵台纵深保留战术选择。',
  '祭所通道接入日宫下层，再分向书库和前庭；本图采用统一去顶室内表达，不在厅内再放一栋室外房屋。',
 ],
 'S51':[
  '神宫旧书库 · 北档案室与南楼梯间',
  '统一去顶室内：连续木地板与石质中厅由实体厚墙分隔，北档案室、错位阅览翼和南楼梯间均在同一建筑内部。原件由档案家具呈现，完整屋顶建筑已移除。',
  '从南楼梯平台进入中厅，到北档案台南面取回原件；击败守卫后回到南端下行楼梯交接，表达撤回下层。',
  '西阅览翼可从南门或东侧门进入，东翼的错位门洞提供另一侧路线；封存侧室不放任务目标。',
  '原台词明确提到相连的房间和撤回下层，应为室内书库；不沿用上轮新增的档案院或档案楼解释。',
 ],
 'J53':[
  '神宫前庭 · 室外两翼与同层石桥',
  '前庭保留室外宫殿、两翼庭路和人工内池；中央跨池连接改用同层石桥，使通路与水庭关系一致，不再用单向楼梯暗示无依据的高差。',
  '两军分别由南侧两翼推进，完成阵台确认后经横廊和中央石桥共同接近统领。',
  '两条横向联络路线支持跨翼接应；屋顶宫殿在室外前庭北缘，作为建筑外观成立。',
  '原剧情称神宫前庭，室外院落与北殿外观合理；本轮修正的是跨池高差表达。',
 ],
 'J54':[
  '神座终战 · 三阶口与连续高台边界',
  '神座保留露天祭坛构图，三座阶口之间补连续台基挡墙，人工池岸与高台边界一致；地面单位须经实际踏步上台。',
  '两军在南侧展开，处理侧翼敌军后由中央或两侧阶口进入上层攻击平台。',
  '后方横廊用于换翼与后撤，侧阶提供分进选择；普通地面单位不能从草地直接穿过高台立面。',
  '原剧情未要求封闭屋顶，露天神座可成立；高差必须由连续台基和可走阶梯共同表达。',
 ],
}
def run():
 old=DOC.read_text();baseline=(O/'baseline/flow-before.md').read_text()
 prior={d['code']:d for d in read(R/'reports/chapter5-redesign-20261022/design-notes.json')['maps']}
 notes=[];stages={c:read(R/f'data/stages/{c}.json') for c in CODES}
 for c,d in stages.items():
  n=prior[c].copy();title,composition,main,side,meaning=TEXT[c]
  n.update(title=title,composition=composition,main_route=main,side_route=side,
   spatial_interpretation=meaning,routes=d.get('tactical_routes',[]),
   size=[d['map']['width'],d['map']['height']],map_sha256=sha(R/f'data/stages/{c}.json'))
  if c=='S51':n['tradeoff']='北侧取档和南楼梯交接必须分别完成；书架与厚墙真实阻挡，封存侧室没有额外任务或奖励。合军后支线关闭，规则保持。'
  if c=='M51':n['tradeoff']='确认病房只解除伤兵锁定；真实门洞本来可通行。两病房都须确认，至少一组撤离并击败首领，规则保持。'
  n.pop('source_reports',None);notes.append(n)
 write(O/'design-notes.json',{'revision':'0.10.10-spatial','maps':notes})
 text=old.replace('版本：流程同步稿1.14；','版本：流程同步稿1.15；')
 materials_note='本轮地面材质复查覆盖全部40图，逐图核对草/雪、沙/盐、船板、户外木栈、室外石铺、室内木地/石地和神宫大理石；前四章仅修正9图的材质及开门后贴图，布局、单位和规则保持，详见[40图材质复查与对照](../actual/reports/chapter5-spatial-20261022/index.html#materials)。'
 if materials_note not in text:text=text.replace('\n## 一、沿用设定与需要新做的部分','\n'+materials_note+'\n\n## 一、沿用设定与需要新做的部分')

 text=text.replace('### 第5章〔已实现 · 地图修订0.10.9-ch5〕','### 第5章〔已实现 · 空间修订0.10.10-spatial〕')
 announcement='2026-10-22第五章空间复查：旧书库按原剧情重做为去顶室内，取消整栋屋顶建筑；同步复查病房、桥头、地下维修层、日宫下层、前庭和神座的空间关系。当前地图与实机验证见[第五章空间逻辑修订](../actual/reports/chapter5-spatial-20261022/index.html)。剧情、规则与人物动画保持。'
 if announcement not in text:text=text.replace('\n## 一、沿用设定与需要新做的部分','\n'+announcement+'\n\n## 一、沿用设定与需要新做的部分')
 for c,d in stages.items():
  match=re.search(rf'(#### {c} [^\n]+\n)(.*?)(?=\n#### |\n## |\Z)',text,re.S);assert match,c
  card=match[2].replace('../actual/reports/chapter5-redesign-20261022/index.html','../actual/reports/chapter5-spatial-20261022/index.html')
  def paragraph(label,value):
   nonlocal card
   block='**'+label+'：**'+value;pattern=r'\*\*'+re.escape(label)+r'：\*\*[^\n]*'
   if re.search(pattern,card):card=re.sub(pattern,block,card,count=1)
   else:card=card.replace('**目标与失败：**',block+'\n\n**目标与失败：**',1)
  n=next(n for n in notes if n['code']==c)
  paragraph('空间判定',n['spatial_interpretation'])
  paragraph('地图调整',' '.join(d['tactical_notes']))
  paragraph('路线与战术',n['main_route']+' '+n['side_route']+' '+n['tradeoff'])
  boss=next(u for u in d['enemies'] if u['id']==d['boss_id'])
  paragraph('地点与空间',f'世界节点{d["node"]}；{d["map"]["width"]}×{d["map"]["height"]}格，16像素一格。首领{point(boss["position"])}。')
  deploy=('西队：'+points(d['player_positions_by_route']['alm'])+'；东队：'+points(d['player_positions_by_route']['celica'])) if c.startswith('J') else points(d['player_positions'])
  paragraph('部署与空间',deploy+'。出口字段G '+point(d['exit'])+'；targets：'+points(d['targets'])+'。是否参与判定以本关规则为准。')
  if d['npc_units']:paragraph('任务NPC','；'.join(u['name_zh']+'（'+u['id']+'）'+point(u['position']) for u in d['npc_units'])+'。身份、生死判定与锁定规则保持。')
  if d['reinforcements']:paragraph('增援落点',f'第{d["reinforcement_turn"]}敌回合：'+'；'.join(u['id']+'／'+u['name_zh']+point(u['position']) for u in d['reinforcements'])+'。沿用原预告与落点占用处理。')
  operations=[]
  for obj in d['objects']:
   place='指定南面格'+point(obj['approach'])+'确认' if 'approach' in obj else '站在目标格确认'
   operations.append(obj['label']+'：对象'+point(obj['position'])+'，'+place)
  paragraph('门、接应与操作位置','；'.join(operations)+'。' if operations else '无新增交互；固定半血召唤源(16,10)与近邻落脚格保持，出口字段不参与击败本体判定。')
  if d['objects']:
   table='| 实际对象 | 对象格 | 操作位置 |\n|---|---|---|\n'
   for obj in d['objects']:
    place='指定南面格'+point(obj['approach'])+'确认' if 'approach' in obj else '站在目标格'
    table+='| '+obj['label']+' | '+point(obj['position'])+' | '+place+' |\n'
   card,count=re.subn(r'\| 实际对象 \| 对象格 \| 操作位置 \|\n(?:\|[^\n]*\n)+',table,card,count=1);assert count==1,c
  text=text[:match.start(2)]+card+text[match.end(2):]
 assert baseline[baseline.index('### 第1章'):baseline.index('### 第5章')]==text[text.index('### 第1章'):text.index('### 第5章')]
 assert baseline[baseline.index('## 七、'):]==text[text.index('## 七、'):]
 DOC.write_text(text)
 write(O/'document-sync.json',{'passed':True,'version':'1.15','document':'docs2/完整游戏流程.md','document_sha256':sha(DOC),'maps':{n['code']:n['map_sha256'] for n in notes},'previous_chapters_unchanged':True,'global_rules_after_chapter5_unchanged':True})
 print('Spatial descriptions and flow v1.15 synchronized.')
if __name__=='__main__':run()
