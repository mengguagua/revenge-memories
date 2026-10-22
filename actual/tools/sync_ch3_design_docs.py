#!/usr/bin/env python3
"""Synchronize approved chapter-three spatial descriptions, never play verdicts."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter3-redesign-20261022';DOC=R.parent/'docs2/完整游戏流程.md'
CODES=['M31','M32','M33','F31','F32','F33','S31','S32']
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def point(p):return '('+','.join(str(int(n))for n in p)+')'
def points(ps):return '、'.join(point(p)for p in ps)
CONTENT={
'M31':{
 'title':'西街撤离 · 街坊与西门',
 'composition':'西门横街、医舍主巷和南街围成住区，东街拘押院设唯一南门；街边民宅与仓房各有朝向道路的门前空间。',
 'main_route':'从南街部署区向东打开拘押院，再护送居民沿南街、医舍主巷和横街抵达西门内圈接应口。',
 'side_route':'仓房之间的一格侧街须移开路障，能够缩短南街与西门横街之间的联络距离。',
 'tradeoff':'可先清理撤离走廊再开院门，也可分兵接应；第4敌回合东南追兵仍会抵达，护卫应让开接应格。两名拘押居民必须存活撤离，街上第三名居民另行记录。',
 'story':'庆典骚乱后，西队从住区带走被拘押居民。必须先打开东街拘押院，再打通队长控制的西门；西队脱围后才能切往码头接应东队。'},
'M32':{
 'title':'军需大道截运 · 双站与北撤车道',
 'composition':'贯通南北的军需大道串起车场、北运输站与北口仓库；西运输站位于林带边的独立装卸坪。',
 'main_route':'西南部署区先接西运输站，再向东截住运输车，沿两格大道推进到北运输站与护送长。',
 'side_route':'西坡一格林缘路绕过西站前方，通向北站侧面；大道东侧保留骑兵调动与装卸空间。',
 'tradeoff':'控制任一站或解开车锁即可停车，随后仍要确认两站和车锁并击败护送长；抢先截停与分兵向北各有取舍，运输车不能被当成可摧毁的敌目标。',
 'story':'西队发现北运车上押着修塔工匠，沿军需大道截运，保住人和工具，再从运输站确认物资流向沿海石堡。'},
'M33':{
 'title':'沿海石堡 · 堡门、工房与投送栈桥',
 'composition':'连续北墙、西墙、东墙、南墙与海蚀崖围住旧石内庭，北端主楼、南侧外院和东侧工房码头形成明确内外分区。',
 'main_route':'两格堡前主道穿过南墙三格正门进入内庭；东南两格港门连接工房卸货路和伸入海面的投送栈桥。',
 'side_route':'一格西崖林缘路经西侧门进入内庭，堡后联络路接东北内圈出口；医舍东侧小路避开屋体接回外院。',
 'tradeoff':'攻堡与控制码头可分工进行；取记录必须走到工房南门，格曼存活时还须在堡主败北后邻接交涉，不能用清场取代投降处理。',
 'story':'沿运输记录抵达海崖石堡，西队同时追查投送码头与工房。堡主败北后，格曼可交出记录并投降；是否接纳与其真实生死分别保留。'},
'F31':{
 'title':'码头脱围 · 双院救援与己船接应',
 'composition':'西侧海湾、错落码头和仓街形成港口工作区，西南己船接应伤者；南北拘留院各自围合，门前广场接仓街。',
 'main_route':'护卫从西南跳板岸侧展开，沿仓街清理门前威胁，分别打开南北两处封锁，让伤者沿街回到己船。',
 'side_route':'东侧巡逻街连接两院后方，仓库间短街用于换线；靠海木码头与内街分开呈现，装卸货物避开转运路。',
 'tradeoff':'分路救援能更快打开两院，但还要控制回撤街区与第3敌回合增援；两门均须解锁，全部存活伤者都要回船，不能仅接走其中一组便结束。',
 'story':'东队的船上伤者被扣在码头南北两院。艾琳带护卫守住西南跳板、逐处开路，把存活伤者送回己方船，再到城外与西队会合。'},
'F32':{
 'title':'盐路解围 · 旧井干道与暴露盐盘',
 'composition':'盐池和低岩脊围出西侧干道，中央旧井成为路标；东侧盐盘开阔，北端关口控制离开方向。',
 'main_route':'向导从护卫后方出发，经南侧住屋、中央井院和盐池西岸干道抵达北关出口。',
 'side_route':'旧井北侧的丘脊小路可绕行，东盐盘另有较直的暴露支路和可移开的路障；固定弓手与术士压住东侧接近线。',
 'tradeoff':'护卫可沿干道逐步清威胁，或冒险从开阔侧路接近守军；向导近敌等待，护卫不能只顾追首领。向导死亡时，南住屋旁路线册仍支持原替代分支。',
 'story':'旧水路已经成为盐原，井台也受封锁。东队保护熟悉路线的向导穿过干道，确认盐原营地与提炼院后门的线索。'},
'F33':{
 'title':'提炼院后庭 · 工房、档案与调节水院',
 'composition':'南侧工房、西北档案屋、北控制楼和中央调节水院形成围合设施；石廊、裸盐地、种植槽与水面区分用途。',
 'main_route':'从南后门先控制工房前庭，再沿主廊接近档案屋和北控制楼；工房唯一南门与部署区直接相接。',
 'side_route':'中央石岛由东西两座维修桥接岸，外围环廊连接两侧守军与阵台；可沿外环换线后再进入水院。',
 'tradeoff':'两名维持设施的术士必须存活，打开工房后仍需保护后方；复制记录和稳定阵台是分别执行的操作，击败控制神官不能代替两项调查。',
 'story':'艾琳先调查控制设施的人，不贸然拆除中央阵。工房术士说明旧循环与集中转移的差异；取得调节记录后，东队要先验证，再与西队核对停塔步骤。'},
'S31':{
 'title':'山村地牢 · 村街与双拘押院',
 'composition':'住屋、井台、医舍和粮仓组成山村，北侧山肩分置两座拘押院，狱卒哨楼面向两院间勤务道。',
 'main_route':'南村口进入主街，经过井台和山肩勤务道抵达东院；西侧住户巷可先接西院南门。',
 'side_route':'粮仓后巷绕向东山肩，连接守军侧面；两院之间有横路，便于开门前重新分配护卫。',
 'tradeoff':'两扇门都须打开，至少一组家属存活并击败首领；家属不要求撤到出口。蕾娜劝降旧部是可选手段，缺席时仍有战斗路线。',
 'story':'被允许回家的家庭再次遭到拘押，西队进入山村查明并救人。蕾娜若在场可与旧部交涉，但家属获救不等于赦免狱卒责任。'},
'S32':{
 'title':'盐原营地 · 双营房与后勤环路',
 'composition':'西术士营房、东居民营房和北指挥帐分区明确，井台、粮仓与木障构成营地生活和勤务空间。',
 'main_route':'从南营口经井台推进中央驻军，分别打开两间营房，再接近北侧营长前庭。',
 'side_route':'东西外侧巡查路通向两扇南门，东后勤路继续连到指挥院侧面，两条救援线可以重新汇合。',
 'tradeoff':'可先清门前守军再开营房，也可分兵救援；两门和营长是任务条件，诺娅、弟弟与居民的生死分别记录，战后问责与接纳不被地图改写。',
 'story':'诺娅因弟弟遭挟持而泄露船队位置。艾琳先救出营房中的人，再追问经过；弟弟的真实生死与是否接纳诺娅各自记录。'}}
def spatial_details(c,d):
 o={a['id']:a for a in d['objects']};at=lambda k:point(o[k]['position']);front=lambda k:point(o[k]['approach']);out=point(d['exit'])
 if c=='M31':return f'拘押院南门{at("court")}只打开本门格并解除两名居民锁定；获释居民从南街转入医舍主巷，最终接应格为{out}。医舍对象{at("street_clinic")}须在指定门前格{front("street_clinic")}访问；侧街路障{at("barricade")}可选。护卫守路时应为接应格及其邻格留出空间。'
 if c=='M32':return f'运输车初始位于{at("cart_release")}，车道沿x=20由y=15逐格向北到出口{out}，共13步；车锁对象随车移动，表中为开局坐标。西站{at("station_w")}和北站{at("station_n")}均须同格确认；控制任一站或解锁车体即可截停，再完成另两项。'
 if c=='M33':return f'南墙在y=12，正门保留x=14—16三格、靠港侧门保留x=23—24两格；西墙x=11在y=8—9留迂回门。投送码头旗位{at("dock_control")}须同格控制；工房记录对象{at("workshop")}只能在南门前格{front("workshop")}读取。格曼位于'+point(next(u['position']for u in d['enemies']if u['id']=='german'))+'，堡主败北后可邻接选择接纳或解除武装；东北联络出口'+out+'位于可达的墙内通路，仅为场景出口字段，不替代记录、码头或投降条件。'
 if c=='F31':return f'北院南门{at("ship_lock")}解锁dock_patients0，南院南门{at("mooring")}解锁dock_patients1，两个opens均与各自可见门格一致。伤者从门前路回到西南己船接应格{out}；存活者必须全部撤离，护卫不能占住接应落脚点。'
 if c=='F32':return f'中央井在(12,11)，既有台词仍由向导接近(14,12)三格以内触发，干道经过这一带。可选路障{at("salt_barrier")}打开本格；路线册{at("guide_notes")}位于南住屋旁。向导从(7,24)跟在部署后方，北关撤离格为{out}；向导遇难时必须确认路线册。'
 if c=='F33':return f'工房唯一南门{at("workers_gate")}打开本格并解除两名术士锁定；两人不需要护送到出口，但必须存活。档案对象{at("regulation_record")}须在指定南侧格{front("regulation_record")}复制；阵台{at("control_array")}须站上石岛目标格确认。场景北口{out}不是撤离任务。'
 if c=='S31':return f'西院门{at("family_w")}解锁family0，东院门{at("family_e")}解锁family1，均为各院唯一南门。两组家属位于各自围院内；本关不要求家属前往山后出口{out}，但两门都必须开启。'
 return f'西术士营房南门{at("mage_barrack")}解锁诺娅；东居民营房南门{at("civilian_barrack")}解锁弟弟和盐原居民。外侧后勤路可由两院通向北指挥区；出口字段{out}不替代开门与击败营长条件，三名NPC不要求撤离。'
def run():
 stages={c:read(R/f'data/stages/{c}.json')for c in CODES}
 assert stages['M31']['exit'][0]>0,'Await final inner-circle M31 evacuation point before publishing coordinates.'
 notes=[]
 for c in CODES:
  d=stages[c];folder='west'if c[0]=='M'else'sides'if c[0]=='S'else'east';report=f'{folder}/{c}-'+('geometry.json'if folder=='east'else'design.json')
  assert (O/report).exists(),report
  n={k:v for k,v in CONTENT[c].items()if k!='story'};n.update(code=c,source_reports=[report],name=d['name_zh'],size=[d['map']['width'],d['map']['height']],routes=d.get('tactical_routes',[]),map_sha256=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest())
  if c=='F32':n['routes']=[{'name':label,'waypoints':p,'width':width,'surface':','}for label,p,width in [('旧井干道与北关',[[7,25],[7,21],[10,18],[11,16],[11,14],[14,13],[14,11],[15,9],[15,7],[18,6],[22,5],[25,4],[27,3]],2),('旧井北侧丘脊旁路',[[11,14],[10,11],[9,8],[10,6],[14,5],[18,6]],1),('东盐盘暴露支路',[[12,17],[16,17],[19,18],[23,18],[24,15],[23,11],[23,8],[22,5]],1)]]
  notes.append(n)
 write(O/'design-notes.json',{'date':'2026-10-22','revision':'0.10.7-ch3','reference':'已确认的M41与第一、二章整体构图方法','maps':notes})
 old=DOC.read_text();text=old
 text=text.replace('版本：流程同步稿1.11；','版本：流程同步稿1.12；')
 announcement='2026-10-22第三章重新构图（地图修订0.10.7-ch3）：重做M31—M33、F31—F33、S31、S32八图的城街、拘押院、运输大道、海崖石堡、港口、盐路与提炼院。部署、单位、门、接应口和车道按整体空间重新安排；身份、数量、属性、装备、AI、剧情、时机和胜败判定保持，人物动画沿用。当前设计与坐标以各卡及[第三章八图重构](../actual/reports/chapter3-redesign-20261022/index.html)为准；本段只同步已确认设计，试玩结论由独立验收报告记录。'
 if announcement not in text:text=text.replace('\n## 一、沿用设定与需要新做的部分','\n'+announcement+'\n\n## 一、沿用设定与需要新做的部分')
 for c in CODES:
  d=stages[c];pattern=rf'(#### {c} [^\n]+\n)(.*?)(?=\n#### |\n### |\Z)';match=re.search(pattern,text,re.S);assert match,c
  card=match.group(2)
  def paragraph(label,value):
   nonlocal card
   card,n=re.subn(r'\*\*'+re.escape(label)+r'：\*\*[^\n]*','**'+label+'：**'+value,card,count=1);assert n==1,(c,label)
  paragraph('剧情推动',CONTENT[c]['story'])
  card,n=re.subn(r'(\*\*地点与地图：\*\*[^\n]*?；)\d+×\d+格',rf'\g<1>{d["map"]["width"]}×{d["map"]["height"]}格',card,count=1);assert n==1
  paragraph('地图调整',' '.join(d['visual_notes']))
  tactical='**路线与战术：**'+CONTENT[c]['main_route']+' '+CONTENT[c]['side_route']+' '+CONTENT[c]['tradeoff']+'\n\n**门、接应与操作位置：**'+spatial_details(c,d)+'\n\n'
  card=re.sub(r'\*\*路线与战术：\*\*.*?(?=\*\*部署与空间：)', '',card,flags=re.S)
  card=card.replace('**部署与空间：**',tactical+'**部署与空间：**',1)
  boss=next(u for u in d['enemies']if u['id']==d['boss_id'])
  paragraph('部署与空间',f'{len(d["player_positions"])}个实际部署位置：{points(d["player_positions"])}。首领{boss["id"]} {point(boss["position"])}；出口字段G {point(d["exit"])}；targets清单：{points(d["targets"])}。G是否参与胜利或失败，以本卡下述判定为准。')
  for u in d['enemies']:
   row=re.search(r'^\|'+re.escape(u['id'])+r'\|.*$',card,re.M);assert row,(c,u['id'])
   cols=row.group().split('|');assert len(cols)==8;cols[5]=point(u['position']);card=card[:row.start()]+'|'.join(cols)+card[row.end():]
  if d['reinforcements']:paragraph('增援',f'第{d["reinforcement_turn"]}敌回合一次：'+'；'.join(u['id']+'／'+u['name_zh']+point(u['position'])for u in d['reinforcements'])+'。单位身份各自独立，进入位置被占时按控制器寻找合法落点。')
  paragraph('任务NPC','；'.join(u['name_zh']+'（'+u['id']+'）'+point(u['position'])+('〔初始锁定〕'if u.get('locked')else'')for u in d['npc_units'])+'。任务NPC、被救者与正式名册分开；正式招募前的真实死亡不会变为濒死救治对象。')
  for o in d['objects']:
   row=re.search(r'^\|'+re.escape(o['id'])+r'／.*$',card,re.M);assert row,(c,o['id'])
   if o.get('approaches')or o.get('approach'):op='指定门前格'+points(o.get('approaches',[o['approach']]if o.get('approach')else[]))+'确认'
   elif o['kind']=='door':op='四邻接确认；开启本门格'
   elif o.get('follows_unit'):op='邻接车体确认；对象随车移动'
   elif o.get('adjacent'):op='同格或四邻接确认'
   else:op='目标格确认'
   newrow='|'+o['id']+'／'+o['label']+'|'+point(o['position'])+'|'+op+'|';card=card[:row.start()]+newrow+card[row.end():]
  text=text[:match.start(2)]+card+text[match.end(2):]
 # Keep other chapter cards exact; the overview's current-dimension column
 # was stale after the prior two redesigns and is approved for factual sync.
 dimension_updates=[]
 for c in re.findall(r'^\|([MFS]\d\d)\|\d+×\d+\|\d+×\d+\|已实现\|$',text,re.M):
  d=read(R/f'data/stages/{c}.json');size=f'{d["map"]["width"]}×{d["map"]["height"]}'
  text,n=re.subn(r'(^\|'+c+r'\|\d+×\d+\|)\d+×\d+(\|已实现\|$)',r'\g<1>'+size+r'\g<2>',text,flags=re.M);assert n==1;dimension_updates.append({'code':c,'current_size':size})
 for chapter,nextchapter in [(1,2),(2,3),(4,5)]:
  a=re.search(r'### 第'+str(chapter)+r'章.*?(?=### 第'+str(nextchapter)+r'章)',old,re.S).group();b=re.search(r'### 第'+str(chapter)+r'章.*?(?=### 第'+str(nextchapter)+r'章)',text,re.S).group();assert a==b,('other chapter modified',chapter)
 a=old[old.index('### 第5章'):];b=text[text.index('### 第5章'):];assert a==b,'chapter five or later sections modified'
 for c,d in stages.items():
  card=re.search(r'#### '+c+r' .*?(?=\n#### |\n### |\Z)',text,re.S).group()
  for u in d['enemies']:
   assert '|'+u['id']+'|'in card and re.search(r'^\|'+re.escape(u['id'])+r'\|[^\n]*\|'+re.escape(point(u['position']))+r'\|',card,re.M)
  for u in d['npc_units']:assert '（'+u['id']+'）'+point(u['position'])in card
  for o in d['objects']:assert '|'+o['id']+'／'+o['label']+'|'+point(o['position'])+'|'in card
  assert '出口字段G '+point(d['exit'])in card
 DOC.write_text(text)
 write(O/'document-sync.json',{'document':'docs2/完整游戏流程.md','version':'1.12','revision':'0.10.7-ch3','design_only_no_new_play_claims':True,'maps':[{ 'code':n['code'],'map_sha256':n['map_sha256'],'size':n['size']}for n in notes],'checks':['Eight chapter-three card sizes/deployments/enemies/reinforcements/NPCs/objects/approach cells/targets/exits synchronized with current stages.','M32 transport path and turn>5 movement rule described without changing rules.','Other chapter cards and chapter-five onward sections unchanged.','Overview current-dimension column also corrected for prior chapter-one/two redesigns.'],'dimension_index_updates':dimension_updates,'document_sha256':hashlib.sha256(DOC.read_bytes()).hexdigest()})
 print('Chapter-three design notes and flow v1.12 synchronized; no gameplay verdicts added.')
if __name__=='__main__':run()
