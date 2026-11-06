import csv, hashlib, json, statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent.parent
load=lambda p:json.loads((ROOT/p).read_text())
campaign=load('actual/data/campaign.json')
rules=load('data/rules_full.json')
legacy=load('actual/data/legacy/rules_full.json')
runtime=json.loads((OUT/'_support/runtime.json').read_text())
names=load('actual/data/class_names.json')
stages=sorted([load(x['path'].replace('res://','actual/')) for x in campaign['stages'].values()],key=lambda s:s['id'])
original=sorted([json.loads(p.read_text()) for p in (ROOT/'data/stages').glob('*.json')],key=lambda s:s['map_id'])
source_chars=original[0]['characters']
old_templates=defaultdict(list)
for s in original:
    for u in s['enemies']:
        old_templates[tuple(u.get('raw_template',[]))].append((s['id'],u))
stat_keys=['level','max_hp','strength','skill','speed','luck','defence','resistance','move']
attr={'level':'等级','max_hp':'最大生命','strength':'力量','skill':'技巧','speed':'速度','luck':'幸运','defence':'物防','resistance':'魔防','move':'移动','class_id':'职业ID','magic_flags':'法术位标志','item_id':'初始装备ID'}
route_names={'alm':'西队','celica':'东队','joint':'合流','both':'合流'}
fallback_class={1:'骑兵',2:'重甲兵',3:'飞马骑士',4:'骑士',5:'猎隼骑士',6:'士兵',7:'大骑士',8:'佣兵',9:'剑士',10:'剑豪',11:'女魔剑士',12:'弓箭手',13:'狙击手',14:'乡勇',15:'术法师',16:'女法师',17:'济世术师',18:'疗愈师',19:'博学术师',20:'弓骑士',21:'战士',22:'壁垒卫士',23:'原版勇者基底'}
def cls(cid,enemy=False):
    return names.get(str(cid),{}).get('enemy_name_zh' if enemy else 'name_zh',fallback_class.get(cid,str(cid)))
def source_ref(u):
    raw=u.get('raw_template')
    if not raw:return None,'无原始敌军模板；有独立角色映射时另查角色表',''
    matches=old_templates.get(tuple(raw),[])
    if not matches:return None,'本地原版部署未找到此模板',''
    unique={tuple(x[1].get(k) for k in ['class_id']+stat_keys+['item_id']) for x in matches}
    if len(unique)!=1:return None,'原版模板存在多组属性，未取任意一组',''
    stage,uold=matches[0]
    ref=f'data/stages/{stage}.json:enemies[raw_template={raw}]'
    if int(u['class_id'])!=int(uold['class_id']):return None,'继承模板后已换职业；不可按同职业逐值比较',ref
    return uold,('同一原始模板；等级已改，差值不是同级成长差' if u['level']!=uold['level'] else '同一原始模板且等级相同'),ref

enemy_headers=['章节','关卡','阶段','数量上限','单位ID','名称','职业','职业ID','等级','生命','力量','技巧','速度','幸运','裸物防','实际物防','实际魔防','移动','携带装备','可用攻击','对双防10最大单击','攻击速度范围','射程最大格','攻击HP费用范围','能力/行为','原版比较口径','原模板等级','原模板生命','生命差','原模板力量','力量差','原模板物防','物防差','原模板速度','速度差','原模板魔防','魔防差','原模板移动','移动差','原版来源','当前来源']
enemy_rows=[]
stage_entities={}
for s in stages:
    entities=[]
    for phase,key in [('初始','enemies'),('固定增援','reinforcements')]:
        for u in s.get(key,[]):entities.append((phase,1,u,runtime['enemies'][s['code']+':'+u['id']],f'actual/data/stages/{s["code"]}.json:{key}[id={u["id"]}]'))
    if s['code'] in ['F43','J54']:
        entities.append(('事件波次',3,s['summon_template'],runtime['enemies'][s['code']+':summon_template'],f'actual/data/stages/{s["code"]}.json:summon_template; actual/core/chapter{4 if s["code"]=="F43" else 5}_rules.gd'))
    if s['code']=='F43':
        for cid,count in [(17,4),(18,1)]:
            entry=runtime['minions'][str(cid)]
            u=entry['unit']|{'id':f'F43_bounded_{cid}','name_zh':'受限召唤骸卫' if cid==17 else '分裂子代','class_name_zh':cls(cid,True)}
            entities.append(('能力召唤',count,u,entry['combat'],'actual/core/campaign_enemy_roles.gd:action; actual/core/summon_rules.gd:spawn_unit(campaign_minion)'))
    stage_entities[s['code']]=entities
    for phase,count,u,c,source in entities:
        old,comparison,oldsource=source_ref(u)
        opts=c['options']; damage=max([p['damage_def10'] for p in opts],default=None)
        def span(key):
            vals=[p[key] for p in opts]
            return '' if not vals else str(min(vals)) if min(vals)==max(vals) else f'{min(vals)}–{max(vals)}'
        role=u.get('campaign_role',u.get('behavior','普通'))
        if role=='bounded_summoner':role='召唤最多2次，每次2名骸卫；保持岗位'
        elif role=='bounded_divider':role='最多分裂1次、1名子代；本体可近战'
        elif role=='short_blink':role='移形≤4格，与玩家间隔≥3格，占用行动，间隔3回合'
        if u.get('advance_after'):role+=f'；第{u["advance_after"]}回合起推进'
        if u.get('campaign_final_boss'):role+='；半血力量+3且一次3名援军，伤害列为强化前'
        row=[s['chapter'],s['code'],phase,count,u['id'],u.get('name_zh',cls(u['class_id'],True)),cls(u['class_id'],True),u['class_id'],u['level'],u['max_hp'],u['strength'],u['skill'],u['speed'],u.get('luck',0),u['defence'],c['physical_defence'],c['magic_defence'],c['movement'],c['item_name'] or '无携带', '；'.join(p['name']+('（魔）' if p['magic'] else '（物）') for p in opts) or '无攻击',damage,span('attack_speed'),max([p['range_max'] for p in opts],default=0),span('hp_cost'),role,comparison]
        for k in ['level','max_hp','strength','defence','speed','resistance','move']:
            row.append(old.get(k) if old else None)
            if k!='level':row.append(u.get(k,0)-old.get(k,0) if old else None)
        row += [oldsource,source]
        assert len(row)==len(enemy_headers),(len(row),len(enemy_headers))
        enemy_rows.append(row)

stage_headers=['章节','关卡','名称','路线','主支线','初始敌军数','固定增援上限','事件/能力增援上限','敌军累计上限','初始平均等级','初始平均生命','初始总生命','初始平均力量','初始平均实际物防','初始平均魔防','初始平均速度','初始平均移动','最大单击(双防10)','最大射程(格)','地图宽(格)','地图高(格)','增援触发','主目标','压力与条件','原版比较口径','实玩回合','实玩濒死人数','实玩重试次数','实玩结果','数值来源']
stage_rows=[]
for s in stages:
    initial=[r for r in enemy_rows if r[1]==s['code'] and r[2]=='初始']
    dynamic=sum(r[3] for r in enemy_rows if r[1]==s['code'] and r[2] in ['事件波次','能力召唤'])
    note=s.get('ai_and_timing','')
    if s['code']=='F43':note+=' 原波次3只；新驭魔师最多4骸卫、裂目兽最多1子代。未计成必然全部出现。'
    if s['code']=='F44':note+=' 西队已切断投送时取消2名增援；表中保留未切断上限。'
    if s['code']=='M44':note+=' 首领投降后取消未到援军。'
    if s['code']=='J54':note+=' 半血增3力量、仅一波3援军；不回血。'
    avg=lambda i:round(statistics.mean(r[i] for r in initial),2)
    damage=max((r[20] or 0 for r in initial),default=0)
    row=[s['chapter'],s['code'],s['name_zh'],route_names.get(s['route'],s['route']),'支线' if s.get('optional',False) else '主线',len(initial),len(s.get('reinforcements',[])),dynamic,len(initial)+len(s.get('reinforcements',[]))+dynamic,avg(8),avg(9),sum(r[9] for r in initial),avg(10),avg(15),avg(16),avg(12),avg(17),damage,max(r[22] for r in initial),s['map']['width'],s['map']['height'],f'第{s["reinforcement_turn"]}敌回合' if s.get('reinforcement_turn',0)>0 else '见压力条件/无固定波次',s['goal'],note,'自定义遭遇；无一对一原版关卡',None,None,None,'待实玩结果',f'actual/data/stages/{s["code"]}.json; actual/core/combat_rules.gd; actual/core/innate_attacks.gd']
    stage_rows.append(row)

char_headers=['角色','角色ID','原版角色','原版角色键','指标','单位','外传初始值','当前初始值','差值','比较说明','来源']
char_rows=[]
for key,mapping in campaign['mapping'].items():
    u=campaign['characters'][key]; old=source_chars[mapping['source_character']]
    for k in ['class_id']+stat_keys+['magic_flags','item_id']:
        note='角色首次入队/新档定义；不是同等级培养后的实战值'
        if k=='item_id':note='一人一携带槽；0为无专属携带物，仍有默认攻击'
        if k=='magic_flags':note='位标志仅记录解锁状态，数值差不代表法术强弱'
        char_rows.append([u['name_zh'],key,old['name_zh'],mapping['source_character'],attr[k],'格' if k=='move' else 'ID/标志' if k in ['class_id','item_id','magic_flags'] else '点',old[k],u[k],u[k]-old[k],note,f'actual/data/campaign.json:characters.{key}; mapping.{key}; data/stages/stage_001.json:characters.{mapping["source_character"]}.{k}'])
    for k in ['hp','strength','skill','speed','luck','defence']:
        char_rows.append([u['name_zh'],key,old['name_zh'],mapping['source_character'],('生命' if k=='hp' else attr[k])+'成长率','百分比',old['growths'][k]/100,u['growths'][k]/100,(u['growths'][k]-old['growths'][k])/100,'个人成长概率；无独立职业成长表。续愿戒影响成功项增量，不改此概率。',f'actual/data/campaign.json:characters.{key}.growths.{k}; data/stages/stage_001.json:characters.{mapping["source_character"]}.growths.{k}'])

class_headers=['职业ID','当前玩家职业','当前敌军名称','生命基底','力量基底','技巧基底','速度基底','幸运基底','物防基底','源表移动','源表敌军魔防','与外传数值不同字段数','适用范围','来源']
class_rows=[]
for cidstr,base in rules['promotion_bases'].items():
    cid=int(cidstr);cur=legacy['promotion_bases'][cidstr]
    diff=sum(cur[k]!=v for k,v in base.items())
    class_rows.append([cid,cls(cid),cls(cid,True),base['max_hp'],base['strength'],base['skill'],base['speed'],base['luck'],base['defence'],rules['class_move'][cid-1],rules['class_resistance'][cid-1] if cid<=len(rules['class_resistance']) else None,diff,'原始共用基底表。当前关卡敌军常覆盖；角色初始看角色表。21号182HP为敌方神躯基底，不是胡纳普生命。' if cid==21 else '职业共用基底/转职最低值；敌军与玩家同ID可异名。个人魔防和成长另查角色表。',f'data/rules_full.json 与 actual/data/legacy/rules_full.json:promotion_bases.{cidstr}; class_move[{cid-1}]; class_resistance[{cid-1}]'])

hero_headers=['角色','当前进阶职业','指标','单位','外传参考值','当前值','差值','原版口径','当前规则','来源']
hero_rows=[]
for key,spec in runtime['heroes'].items():
    for k,value in spec['bases'].items():
        old=rules['promotion_bases']['23'].get(k) if key=='hunapu' else None
        hero_rows.append([campaign['characters'][key]['name_zh'],spec['name'],attr[k],'点',old,value,value-old if old is not None else None,'阿尔姆剧情转职23号最低基底' if key=='hunapu' else '赛莉卡源实现仅重置等级并标记公主，无对应最低属性，留空', '只补足到最低值，较高值保留；不回当前HP', 'actual/core/hero_professions.gd:DEFINITIONS; data/rules_full.json:promotion_bases.23; core/hub_controller.gd:_special'])
    original_move=5 if key=='hunapu' else 4
    hero_rows.append([campaign['characters'][key]['name_zh'],spec['name'],'基础移动','格',original_move,spec['move'],spec['move']-original_move,'本地原版运行保留源职业21/11的移动','进阶覆盖基础移动','actual/core/hero_professions.gd; core/unit_progression.gd; core/hub_controller.gd'])
    hero_rows.append([campaign['characters'][key]['name_zh'],spec['name'],'等级重置目标','级',1,None,None,'原版剧情进阶重置到1级','当前保留进阶前等级与经验，不能把1级差值作属性收益','actual/core/hero_professions.gd:apply; core/unit_progression.gd:promote; core/hub_controller.gd:_special'])
for i in [23,24,26,27,25]:
    item=rules['items'][i];base=item['hp_cost'];now=max(1,base-1)
    hero_rows.append(['艾琳','引光剑使',item['name_zh']+'每次施法费用','HP',base,now,now-base,'已学攻击法术；辅助法术不减','主动/反击/追击逐次付费；正费用最低1；本表不等于施法次数','actual/core/item_rules.gd:cost_for; data/rules_full.json:items'])

equipment_headers=['物品ID','当前名称','外传名称','类别','原威力','现威力','威力差','原重量','现重量','重量差','原命中','现命中','命中差','原必杀','现必杀','必杀差','当前射程(格)','数值与效果','使用者变化','当前取得条件','来源']
equipment_rows=[]
armaments=load('actual/data/story_armaments.json')['items'];accessories=load('actual/data/story_accessories.json')['items']
effects={7:'原→现：阶段恢复5→5HP；射程1–2→1–2。士兵不能用。',9:'原→现：阶段恢复5→5HP；威力20→20。两者都没有吸血，不能套用其他作品太阳效果。',10:'原→现：合法枪击命中100→100；阶段恢复5→5HP。两者都不无视防御。',15:'原→现：总攻击力固定15→15，按魔防结算，不叠加自身力量。',17:'原→现：阶段恢复5→5HP；魔物特效倍率3→3。本作终战无需此剑，神躯不在特效组。',18:'原→现：阶段恢复5→5HP；武器必杀20→20，结算必杀仍按战斗公式。',53:'原→现：物防加成13→13、魔防加成13→13、阶段恢复5→5HP；占用唯一携带槽。',55:'原→现：有效幸运40→40；成功成长项增量倍率2→2；阶段恢复5→5HP。'}
for sid,spec in list(armaments.items())+list(accessories.items()):
    i=int(sid);o=rules['items'][i];n=runtime['items'][i]
    row=[i,spec['name_zh'],o['name_zh'],'兵装' if sid in armaments else '饰品']
    for k in ['might','weight','hit','critical']:
        ov=o.get(k);nv=n.get(k);row += [ov,nv,nv-ov if ov is not None and nv is not None else None]
    row += ['1–2' if i in [7,15] else '1' if i not in [53,55] else '不适用',effects[i], '阿尔姆专用→艾琳专用' if i==17 else '阿尔姆专用→胡纳普专用' if i==18 else '沿用源物品职业限制',f'{spec.get("stage_code",spec.get("stage"))}；'+spec.get('story_description',''),f'data/rules_full.json:items[{i}]; actual/data/{"story_armaments" if sid in armaments else "story_accessories"}.json:items.{i}; actual/core/item_rules.gd']
    equipment_rows.append(row)
for n in load('actual/data/equipment_progression.json')['items']:
    equipment_rows.append([n['id'],n['name_zh'],'原版无同ID对应','新增基础装备',None,n['might'],None,None,n['weight'],None,None,n['hit'],None,None,n['critical'],None,'弓1–3；近战1；法器跟随法术','法器只提升已学攻击法术；新增装备数值不冒称外传原值',n['family'],'初始/固定奖励/普通掉落池','actual/data/equipment_progression.json:items'])

old_headers=['原地图ID','名称','章节标签','路线','初始敌军数','平均等级','平均生命','总生命','平均力量','平均物防','平均魔防','平均速度','平均移动','最高等级','最高生命','地图宽(格)','地图高(格)','部署敌群ID','源地图','比较口径','来源']
old_rows=[]
for s in original:
    es=s['enemies'];mean=lambda k:round(statistics.mean(e[k] for e in es),2) if es else None
    old_rows.append([s['map_id'],s['name_zh'],s.get('chapter'),route_names.get(s.get('route'),s.get('route','')),len(es),mean('level'),mean('max_hp'),sum(e['max_hp'] for e in es),mean('strength'),mean('defence'),mean('resistance'),mean('speed'),mean('move'),max([e['level'] for e in es],default=None),max([e['max_hp'] for e in es],default=None),s['map']['width'],s['map']['height'],','.join(map(str,s.get('enemy_group_ids',[]))),s['map'].get('source',''),'本地80份地图默认部署快照；不含游军再组合/重复遭遇/所有动态召唤，不与当前40关一一对应',f'data/stages/{s["id"]}.json:enemies; battle_identity'])

mechanic_headers=['机制','外传/本地源复现','当前改编','对难度的影响','比较限制','来源']
mechanic_rows=[
['关卡结构','本地80地图默认部署；存在游军、洞窟与敌群组合','40个固定剧情关，含支线与双线目标','关卡数量、通关目标和战线结构不同','不能用总敌数比例声称总体难度升降','data/stages/*.json; actual/data/campaign.json; actual/core/world_armies.gd'],
['濒死与救治','源复现以dead持久化；神像复活依对应机制','正式同伴0HP进入濒死；不能出阵，每人最多救治1次；四来源总上限4份','损失从永久死亡改成有限救治，但仍消耗名额并可能失去战力','主角濒死仍失败；不是无限复活','actual/core/casualty_rules.gd:SOURCES,treat; actual/core/legacy_game_state.gd'],
['战后恢复','源复现开战时存活成员回满HP','结算/整备时即回满可出阵正式成员；濒死不恢复','战前生命与原版同为满值；提早在UI可见，不额外创造连续战损惩罚','不能把战后回满误判成相对外传的新回血增益','actual/core/game_state.gd:_restore_preparation_hp,start_battle; actual/core/legacy_game_state.gd:start_battle'],
['成长概率','角色各有六项成长，成功+1，天使戒成功项+2，属性有上限','17人源映射成长不变；诺娅6项概率调整；续愿戒沿用成功项+2','诺娅更偏力量，速度/幸运等期望成长更低','概率不同于单次实际随机成长，不能当作必增','data/stages/stage_001.json:characters.*.growths; actual/data/campaign.json:characters; actual/core/combat_rules.gd:growth_result'],
['新主角进阶','阿尔姆转职采用23号基底；赛莉卡仅重置等级/标记','胡纳普移动6；艾琳移动5+属性最低值+已学攻击术费-1；等级经验保留','移动与法术续航提升；保留等级也保留经验倍率/等级20上限','艾琳基底无等价原版公主基底，不造差值','actual/core/hero_professions.gd; core/hub_controller.gd:_special; core/unit_progression.gd'],
['装备供给','源原生物品及事件/概率掉落','新增8种铜/铁基础装备；入队供应、固定通关奖励、持物100%掉落、空手普通掉落10%','降低装备供应的不确定性；剧情兵装奖励更可预测','数值相同的六兵装/两饰品也会因取得时间影响难度','actual/data/equipment_progression.json; actual/data/story_armaments.json; actual/data/story_accessories.json'],
['单携带槽','每人一件携带物','继续一槽，武器与护盾/戒指相互排斥','强武器与强饰品不能同时叠加','邻接交换可在合流战场跨队交接','actual/core/item_rules.gd; actual/core/battle_inventory.gd'],
['任务压力','源遭遇多以战斗清敌为主体，另有特殊脚本','护送、连续守井、记录焚毁、工班接通、运输船受击等','敌军相同伤害也可能造成任务失败；击破速度不是唯一难度','每关具体条件以40关表及实玩报告为准','actual/core/chapter2_rules.gd; actual/core/chapter4_rules.gd; actual/core/chapter5_rules.gd'],
['F42移形','源witch传送行为来自原AI','最多移动4格；落点离玩家≥3格；占一次行动；间隔3回合','限制突然贴后排的压力，仍能改变站位','不拿原全图传送当当前行为','actual/core/campaign_enemy_roles.gd:blink_landing,action'],
['F43召唤/分裂','源敌方召唤数量由力量和模板决定，可重复','旧事件3只；新驭魔师最多2次×2只；裂目兽最多1只；新子代24HP/力量9/速度4','总量有限，新生体当回合已行动，召唤不提供经验和掉落','事件/容量/提前击败召唤者可减少；上限不是实出现数','actual/core/campaign_enemy_roles.gd; actual/core/summon_rules.gd; actual/core/chapter4_rules.gd'],
['终战门槛','源多玛HP<52会屏蔽非17号且ID<40攻击','J54普通武器与法术始终有效；半血力量+3，援军3，只触发1次','去掉专属剑终结门槛；更依赖保护双线队伍和目标','神躯ID/身份已改，不能按原多玛182HP直接算同首领削弱','actual/core/combat_rules.gd:attack_blocked; actual/core/chapter5_rules.gd:check_outcome; actual/data/stages/J54.json'],
['护途盾终战组合','龙盾源效果双防+13、阶段恢复5','唯一可选双组伤兵救援奖励；最低进阶艾琳持盾为物防21/魔防23','J54首领半血总威力21，两类单击均只1点，单体威胁显著降低','这不是整关必胜证明；AI、其他队员和目标压力须与实玩并看','actual/data/story_accessories.json; actual/core/item_rules.gd; actual/reports/balance-audit-20261023/scenario-summary.json'],
['本表伤害口径','不把武器威力直接当扣血','当前引擎对生命52、双防10、速度/幸运/地形回避0的标准目标计算','用于横向看攻击强度与射程','无暴击/克制/追击/命中期望；不等于实战平均损失；J54列为半血强化前','actual/core/combat_rules.gd:attack_stats; difficulty/_support/export_runtime.gd'],
]

play_path=OUT/'_support/play_results.json'
if play_path.exists():
    play=json.loads(play_path.read_text())
    for row in stage_rows:
        result=play.get(row[1])
        if result:
            row[25]=result.get('turns');row[26]=result.get('dying');row[27]=result.get('retries');row[28]=result.get('result','已记录')

datasets={'40关难度':(stage_headers,stage_rows),'敌军明细':(enemy_headers,enemy_rows),'角色数值':(char_headers,char_rows),'职业基底':(class_headers,class_rows),'主角进阶':(hero_headers,hero_rows),'装备对比':(equipment_headers,equipment_rows),'外传80图':(old_headers,old_rows),'机制差异':(mechanic_headers,mechanic_rows)}
for name,(headers,rows) in datasets.items():
    with (OUT/'csv'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(headers);w.writerows(rows)
summary=[]
for chapter in range(1,6):
    ss=[s for s in stage_rows if s[0]==chapter]; es=[r for r in enemy_rows if r[0]==chapter and r[2]=='初始']
    summary.append([chapter,len(ss),sum(r[5] for r in ss),sum(r[6] for r in ss),sum(r[7] for r in ss),sum(r[8] for r in ss),round(statistics.mean(r[9] for r in es),2),round(statistics.mean(r[10] for r in es),2),max(r[20] or 0 for r in es)])
stats={'chapters':summary,'enemy_initial':sum(r[5] for r in stage_rows),'fixed_reinforcements':sum(r[6] for r in stage_rows),'dynamic_max':sum(r[7] for r in stage_rows),'all_max':sum(r[8] for r in stage_rows),'enemy_rows':len(enemy_rows),'char_changed':sum(r[8]!=0 for r in char_rows),'growth_changed':sum(r[8]!=0 and r[5]=='百分比' for r in char_rows),'raw_rule_tables_equal':rules==legacy,'rule_table_difference':'仅31号法术中文名 多拉→鬼火；数值字段相同','template_comparable':sum(r[26] is not None for r in enemy_rows),'original_map_count':len(old_rows)}
(OUT/'_support/datasets.json').write_text(json.dumps({'data':{k:{'headers':v[0],'rows':v[1]}for k,v in datasets.items()},'stats':stats},ensure_ascii=False,indent=2))
source_paths=['actual/data/campaign.json','data/rules_full.json','actual/data/legacy/rules_full.json','actual/data/story_armaments.json','actual/data/story_accessories.json','actual/data/equipment_progression.json','actual/core/hero_professions.gd','actual/core/combat_rules.gd','actual/core/item_rules.gd','actual/core/casualty_rules.gd','actual/core/campaign_enemy_roles.gd','actual/core/summon_rules.gd','actual/core/game_state.gd','actual/core/chapter2_rules.gd','actual/core/chapter4_rules.gd','actual/core/chapter5_rules.gd','actual/core/legacy_game_state.gd','core/hub_controller.gd','core/unit_progression.gd']+[f'actual/data/stages/{s["code"]}.json' for s in stages]+[f'data/stages/{s["id"]}.json' for s in original]
(OUT/'source-manifest.json').write_text(json.dumps({'date':'2026-10-23','files':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in source_paths},'statistics':stats},ensure_ascii=False,indent=2))
print(json.dumps(stats,ensure_ascii=False,indent=2))
