#!/usr/bin/env python3
"""Synchronize final chapter-four spatial facts without inventing play verdicts."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter4-redesign-20261022';DOC=R.parent/'docs2/完整游戏流程.md'
CODES=['M41','M42','M43','M44','F41','F42','F43','F44','S41','S42']
read=lambda p:json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def point(p):return '('+','.join(str(int(n))for n in p)+')'
def points(ps):return '、'.join(point(p)for p in ps)
CONTENT={
'M41':dict(title='雪峡撤离 · 斜谷与双桥',composition='保留已确认样板：西北村街、东北至西南的融雪河、东岸医舍与南口山肩构成一条连续撤离谷地。',main_route='从北村街过中央宽桥，接应山道伤者，再沿医舍前主路护送至南口。',side_route='东北林缘一格小桥较长且窄，可绕到桥头守军侧后，最后与主线在医舍前汇合。',tradeoff='北口第4敌方回合有两名骑兵追来；前排开路与后排接应必须兼顾，南村居民也需保护。至少两组撤离、疏通南口、确认停靠点和击败指挥官缺一不可。',story='西队在雪峡发现居民再次遭到封路，保护北村居民、山道伤者和南村居民撤离；奥托面对自己过去参与的行动，不能仅靠击败新指挥官结束救援。'),
'M42':dict(title='铁骑封锁线 · 围栅投送营与西林旧营',composition='西北岩坡和中央林带分开军道与旧营，东侧木栅投送营有南北主门和西侧门，北关堡成为远端指挥点。',main_route='从西南集结区沿两格军道接近投送营南门，控制装置后继续北上击败统领。',side_route='西林旧营的一格路可先与旧同袍交涉，再接营侧门；东骑兵营支路连接东南援军入口。',tradeoff='兰斯可先邻接旧同袍使两名骑兵中立，缺席时按战斗路线推进。控制投送站立即切断后续投送；是否影响祭所援军由F44入场快照决定。',story='西队查明铁骑关仍在把兵力投送到东岸。兰斯可劝旧同袍停手，但仍须取得装置与关口的实际控制，才能保护后续船队。'),
'M43':dict(title='北境日塔 · 院墙与双门',composition='连续院墙与雪崖围住日塔庭院，北端主楼和塔身、东南控制室、西南医舍分区明确。',main_route='从西南集结处沿铺石主路穿三格南门，控制外院，再转入东南控制室南门。',side_route='西侧雪林窄路穿两格侧门，可避开正面门前重装，从院侧接近北塔。',tradeoff='正门接近快但正面压力较大，侧门路窄更长；病人与工匠留在医舍后方。夺塔可先完成，安全停塔必须战后收到F42步骤后另行确认。',story='西队先夺下日塔的控制权，同时保护依赖设施的病人与工匠；胡纳普决定等待东岸完整观测步骤，不直接拆毁村庄仍在使用的光源。'),
'M44':dict(title='王都城门 · 双塔正门与医舍后撤线',composition='双塔夹出四格正门，连续城墙分开城外住区与城内指挥堡；西医舍设完整护院，南军需街承担另一侧集结与增援。',main_route='从靠近西后撤门的部署区先接住医舍防线，再沿城外主街或墙内街接近双塔门楼。',side_route='西侧一格巷经过城墙后撤门和医舍护院唯一南口，可绕开正门重装；东南支街是第4回合援军来路。',tradeoff='队伍需要在推进门楼时兼顾伤兵通道。赫兰败北会解除武装、余兵中立并取消后续援军，取得门楼即可结算，不要求消灭投降者。',story='西队在王都城门面对赫兰，留出伤兵后撤通道并接受解除武装；战胜统领不等于抹去责任，也不以屠尽守军证明胜利。'),
'F41':dict(title='沙城守井 · 双井住区与后巷',composition='北住区和南取水院围绕两口实体井展开，民居、小仓院与取水巷形成紧凑沙城，沙地延续到地图外缘。',main_route='从南井接应区沿生活街推进北井，北井主街继续通向东北城关。',side_route='西住户窄巷能侧接北井，东后巷可绕守军街换线，但两者都比中央主巷更窄。',tradeoff='可稳守南井后夺回北井，也可分兵争取两井；不能让两井同时失守。敌人持续追井、连续占井一轮才失守与第6回合门槛全部保留。',story='东队保护沙城仍可供水的两口井，为居民争取通往盐原古道的时间；先守住一井是有效方案，不把一时丢失北井当成已经失败。'),
'F42':dict(title='盐原观测台 · 东楼抢救与设备核对',composition='南抄录住区、中央设备台、东楼记录室和北值守楼沿盐原旧路分布，裸盐地与小块石台区分生活和设备用途。',main_route='从南住区沿东侧抢救线抵达记录楼南门，保护记录后返回中央设备南面复制参数。',side_route='西岩脊旧维护路更长、更窄，可绕到北庭；东楼外侧防火巡查路连接焚毁兵方向。',tradeoff='需要按保护记录、复制设备的顺序行动；第5回合预告，第6回合焚毁兵出发，连续两次到门前点火才毁记录。清守军与抢救资料须分配优先级。',story='东队取得完整调节步骤，确认先隔离远端、再分段降流、最后核对村庄照明的办法；副本由固定信使送西岸，让夺塔之后能够安全停用。'),
'F43':dict(title='亡潮沼泽 · 三段干岛护送',composition='南船口、中央转运岛和东北古道高地由真正水沟分开，两段木栈接起干岸，毒沼集中在护送线外侧。',main_route='居民从护卫后方出发，沿南岸便桥、中央岛和东北高木栈前进，按顺序确认三处干地并撤到古道口。',side_route='西湿地窄桥可供小队压制术士并接近北祭台，离开干线会承担毒沼和孤军风险。',tradeoff='护卫应保留后卫照顾慢行居民，不能全队只追神官。第3回合最多三个指定召唤物保留；神官败北只移除指定召唤物，天然敌人仍需处理。',story='东队分段确认真实可走的干地，把居民从亡潮沼泽送至船团接应方向；固定船团负责后续分批转运，不能以传送或击杀神官代替护送。'),
'F44':dict(title='沉没祭所 · 五块石台与调节网络',composition='西、中央、东调节台和北神门以残存风化石台立在水中，南接应台容纳工匠棚与泊船，木桥只跨实际水隙。',main_route='从南接应台经双格便桥进入中央作业台，再接东调节平台与北神门。',side_route='西侧长桥通旧石拱，单格短桥侧接中央；东北维护桥提供另一条接近北神门的路线。',tradeoff='三点可自行安排交接顺序，但全部完成后仍须保护至少一名工匠到下一己方回合。东平台是否在第5回合收到援军取决于入场时投送站状态。',story='东队把观测记录用于祭所现场，逐点交接、保护工匠完成局部隔离试验，验证地方循环仍可继续；胜利不使旧伤、濒死或灾难后果自动消失。'),
'S41':dict(title='黑钟村名册 · 钟楼街与东坡拦截',composition='钟楼主街串起雪山住屋，东侧名册屋朝南，西南医舍与避难院在队伍后方；林带和岩坡围住村缘。',main_route='从南村口沿主街到名册屋支路，在南门前保护名册，再向钟楼守军推进。',side_route='东坡进村路与名册南门相接，是焚毁兵真实来路；西医舍与南住屋支线提供后方回撤空间。',tradeoff='第4回合预告、第5回合焚毁兵出发，连续两次点火才毁册。名册已毁仍能击败队长结束支线，但不会恢复烧毁资料或发完整名册奖励。',story='西队保存凯尔先执行迁徙、后来违令救人的完整记录；成功与失败分别保留书面事实或在场证言，不把过去只改写成英雄传闻。'),
'S42':dict(title='沼泽孤岛 · 诊疗院与南岸接应',composition='南岸诊疗屋、井台、药车和照护住屋组成医疗院，北驻军岛与诊疗院之间有真实水沟，西南船口接连续转运路。',main_route='先守诊疗院与主桥南端，让两组病人沿院南干路撤到西南船口，再推进北岛守军。',side_route='东侧一格窄栈可绕到北端守军侧面，主木桥则便于集中兵力保护医疗院。',tradeoff='北端飞行敌第3回合压近，应先保护病人再分兵追敌。两组病人都须撤离，赛琳生死独立记录；招募仍要战后明确邀请。',story='东队接应孤岛病人，地方医者保留维娅当年准备不足便出航、后来反复救人的两面记录；救援不能只留下成功航次，也不能用招募代替安置病人。')}

def spatial_details(c,d):
 o={a['id']:a for a in d['objects']};at=lambda k:point(o[k]['position']);front=lambda k:point(o[k]['approach']);out=point(d['exit'])
 npc=lambda k:point(next(u['position']for u in d['npc_units']if u['id']==k))
 if c=='M41':return f'南口路障{at("south_gate")}和医舍停靠点{at("rest_station")}均须同格确认，居民实际撤离格为{out}。北村、山道、南村三组分别从'+points([u['position']for u in d['npc_units']])+'出发；护卫应让开出口与相邻落脚格。本图保留已确认构图及全部坐标。'
 if c=='M42':return f'投送站{at("transfer_station")}须同格控制；营地登记{at("cavalry_camp")}可选。旧同袍位于西营后方{npc("old_comrade")}，仅兰斯本人健康且四邻接时可交涉。出口字段{out}不是撤离条件。'
 if c=='M43':return f'外院旗位{at("outer_court")}同格确认，控制室对象{at("tower_control")}须在南门前{front("tower_control")}操作。三格南门和两格西门均为真实院墙开口；场景出口{out}不代替两项控制。'
 if c=='M44':return f'门楼旗位{at("gatehouse")}须同格占领，后撤门控制点{at("wounded_gate")}可选；西后撤门与医舍相连，护院唯一南口在(5,8)、(6,8)，两名伤兵位于'+points([u['position']for u in d['npc_units']])+f'。赫兰投降后不需要追击已中立单位，出口字段{out}不参与占门楼判定。'
 if c=='F41':return f'北井控制点{at("well_n")}、南井控制点{at("well_s")}各位于实体井南一格；井口本身阻挡，正式队员站回控制点可以夺回水井。地图城关出口{out}不是守井任务的撤离点。'
 if c=='F42':return f'东楼记录对象{at("observatory_record")}须在南门前{front("observatory_record")}保护，焚毁目标也为该门前格；中央设备{at("observation_device")}须在南面{front("observation_device")}复制。两项操作有先后顺序，北出口{out}仅为场景字段。'
 if c=='F43':return '三处干地须依次确认：'+points([o[k]['position']for k in ['dry_1','dry_2','dry_3']])+f'；居民实际撤离格{out}位于东北古道口。至少两组须存活撤离，固定召唤源(26,6)保留在北侧祭台附近。'
 if c=='F44':return '中央、东、西调节点分别为'+points([o[k]['position']for k in ['regulator_1','regulator_2','regulator_3']])+f'，均站在可走石台上交接，顺序不强制。两工匠在{npc("repairer0")}、{npc("repairer1")}；北出口{out}不是工匠撤离点。'
 if c=='S41':return f'名册对象{at("black_register")}必须从南门前{front("black_register")}读取，此格与焚毁目标相同；避难院{at("refuge_court")}可选。钟楼出口字段{out}不作为护送目标。'
 return f'船边确认点{at("landing")}与实际病人撤离格{out}相邻且用途不同，护卫不能占住撤离格。诊疗屋记录对象{at("clinic_note")}从南门前{front("clinic_note")}读取，为可选调查；两组病人必须全部到船，赛琳不要求走到出口。'

def run():
 stages={c:read(R/f'data/stages/{c}.json')for c in CODES};notes=[]
 for c,d in stages.items():
  folder='west'if c in ['M42','M43','M44','S41']else'rescue'if c in ['F43','S42']else'east'
  report='../m41-redesign-20261022/design.json'if c=='M41'else f'{folder}/{c}-design.json';p=O/report;assert p.exists(),report
  sha=hashlib.sha256((R/f'data/stages/{c}.json').read_bytes()).hexdigest();detail=read(p)
  if c!='M41':assert detail.get('map_sha256',detail.get('stage_sha256'))==sha,('stale report',c)
  else:assert (R/f'data/stages/{c}.json').read_bytes()==(O/f'baseline/{c}.json').read_bytes(),'M41 should remain unchanged'
  n={k:v for k,v in CONTENT[c].items()if k!='story'};n.update(code=c,source_reports=[report],name=d['name_zh'],size=[d['map']['width'],d['map']['height']],routes=d.get('tactical_routes',[]),map_sha256=sha,change_status='retained_approved_reference'if c=='M41'else'redesigned');notes.append(n)
 write(O/'design-notes.json',{'date':'2026-10-22','revision':'0.10.8-ch4','reference':'保留M41已确认样板；按整体地理、主次路线和剧情任务重设计其余九图','maps':notes})
 old=DOC.read_text();text=old.replace('版本：流程同步稿1.12；','版本：流程同步稿1.13；')
 announcement='2026-10-22第四章重新构图（地图修订0.10.8-ch4）：M41保留已确认雪峡样板并复查；M42—M44、F41—F44、S41、S42九图重做关营、院墙、医舍后撤线、沙城双井、观测院、沼泽干岛和沉没石台。部署、守军、NPC、门前操作格和撤离口按实际空间重排；身份、数量、数值、AI、剧情、时机及胜败规则保持，人物动画沿用。当前布局说明见[第四章十图设计与复查](../actual/reports/chapter4-redesign-20261022/index.html)；本段只同步设计，实机结论由独立验收报告记录。'
 if announcement not in text:text=text.replace('\n## 一、沿用设定与需要新做的部分','\n'+announcement+'\n\n## 一、沿用设定与需要新做的部分')
 text=text.replace('地形、部署和道路经过可达检查；图像见[第四章实际截图与验收](../actual/docs/第四章交付与两轮验收.md)。原关卡布局/M4x等PNG仅为历史蓝图。','本轮地形、部署和道路以[第四章十图设计与复查](../actual/reports/chapter4-redesign-20261022/index.html)及当前stage为准；早期实现记录保留在[第四章交付与验收](../actual/docs/第四章交付与两轮验收.md)。原关卡布局/M4x等PNG仅为历史蓝图。')
 for c,d in stages.items():
  pattern=rf'(#### {c} [^\n]+\n)(.*?)(?=\n#### |\n### |\Z)';match=re.search(pattern,text,re.S);assert match,c;card=match.group(2)
  def paragraph(label,value):
   nonlocal card
   block='**'+label+'：**'+value
   if re.search(r'\*\*'+re.escape(label)+r'：\*\*[^\n]*',card):card=re.sub(r'\*\*'+re.escape(label)+r'：\*\*[^\n]*',block,card,count=1)
   else:card=card.replace('**目标与判定：**',block+'\n\n**目标与判定：**',1)
  if c!='M41':paragraph('地图调整',' '.join(d.get('visual_notes',d.get('tactical_notes',[]))))
  card,n=re.subn(r'(运行文件：[^\n]*?地图)\d+×\d+(；)',rf'\g<1>{d["map"]["width"]}×{d["map"]["height"]}\g<2>',card,count=1);assert n==1,c
  paragraph('剧情推动',CONTENT[c]['story'])
  paragraph('路线与战术',CONTENT[c]['main_route']+' '+CONTENT[c]['side_route']+' '+CONTENT[c]['tradeoff'])
  boss=next(u for u in d['enemies']if u['id']==d['boss_id'])
  paragraph('部署与空间',f'{len(d["player_positions"])}个候选格：{points(d["player_positions"])}。首领{boss["name_zh"]}（{boss["id"]}）{point(boss["position"])}；出口字段G {point(d["exit"])}；targets：{points(d["targets"])}。G是否用于撤离以本关判定为准。')
  paragraph('任务NPC','；'.join(u['name_zh']+'（'+u['id']+'）'+point(u['position'])for u in d['npc_units'])+'。任务NPC生死单独记录，不按正式名册的濒死救治处理。')
  if d['reinforcements']:paragraph('增援落点',f'第{d["reinforcement_turn"]}敌回合：'+'；'.join(u['id']+'／'+u['name_zh']+point(u['position'])for u in d['reinforcements'])+'。按原规则提前一回合预告；占格时由原控制器寻找合法落点。'+('F44入场时投送已切断则取消本波，入场后快照不随旗标变化。'if c=='F44'else''))
  paragraph('门、接应与操作位置',spatial_details(c,d))
  table='| 实际对象 | 对象格 | 操作位置／性质 |\n|---|---|---|\n'
  for o in d['objects']:
   op='指定门前格'+points(o.get('approaches',[o['approach']]if 'approach'in o else[]))+'确认'if o.get('approach')or o.get('approaches')else'站在目标格'
   if o.get('optional'):op+='；可选'
   table+='| '+o['label']+' | '+point(o['position'])+' | '+op+' |\n'
  card,n=re.subn(r'\| 实际对象 \| 对象格 \| 操作位置／性质 \|\n(?:\|[^\n]*\n)+',table,card,count=1);assert n==1,c
  if c=='M41':paragraph('目标与判定','三组居民逐个记录生死，至少两组到'+point(d['exit'])+'，并确认南口路障、伤者停靠点及击败指挥官；失去两组失败。居民近敌时只沿安全撤离方向走，不因护送等待重叠或复活。')
  if c=='F44':paragraph('目标与判定','三点全部交接后工匠接手，交接顺序不强制，正式成员不用永久站点。保护至下一己方回合、至少一名修复工匠存活、击败守兽才胜。胜利写island_loop_safe，不自动治疗伤者。')
  text=text[:match.start(2)]+card+text[match.end(2):]
 for chapter,nextchapter in [(1,2),(2,3),(3,4)]:
  a=re.search(r'### 第'+str(chapter)+r'章.*?(?=### 第'+str(nextchapter)+r'章)',old,re.S).group();b=re.search(r'### 第'+str(chapter)+r'章.*?(?=### 第'+str(nextchapter)+r'章)',text,re.S).group();assert a==b,('other chapter modified',chapter)
 assert old[old.index('### 第5章'):]==text[text.index('### 第5章'):],'chapter five or later modified'
 for c,d in stages.items():
  card=re.search(r'#### '+c+r' .*?(?=\n#### |\n### |\Z)',text,re.S).group()
  assert f'地图{d["map"]["width"]}×{d["map"]["height"]}；'in card
  for u in d['npc_units']:assert '（'+u['id']+'）'+point(u['position'])in card
  for o in d['objects']:assert '| '+o['label']+' | '+point(o['position'])+' |'in card
  assert '出口字段G '+point(d['exit'])in card
 DOC.write_text(text)
 write(O/'document-sync.json',{'document':'docs2/完整游戏流程.md','version':'1.13','revision':'0.10.8-ch4','design_only_no_new_play_claims':True,'maps':[{'code':n['code'],'map_sha256':n['map_sha256'],'size':n['size'],'change_status':n['change_status']}for n in notes],'checks':['Ten chapter-four map sizes, deployments, bosses, NPCs, reinforcement positions, targets, exits and operation cells synchronized with current stages.','M41 map bytes remain identical to approved baseline; its original sample description is retained.','M41 complete victory requirements and F44 arbitrary regulator order clarified from existing chapter4_rules.gd; no rule changed.','Chapter-one/two/three cards and chapter-five onward text unchanged.','Design source report hashes match final map files.'],'document_sha256':hashlib.sha256(DOC.read_bytes()).hexdigest()})
 print('Chapter-four design notes and flow v1.13 synchronized; no new play verdicts added.')
if __name__=='__main__':run()
