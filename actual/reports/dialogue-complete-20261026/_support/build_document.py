from pathlib import Path
import json,re,collections,hashlib,sys,html
from events import catalog,literals
R=Path(__file__).resolve().parents[4];O=R/'actual/reports/dialogue-complete-20261026';DOC=R/'docs2/完整台词汇总.md'
D=json.loads((O/'runtime-capture.json').read_text());ST={s['code']:s for s in [json.loads(p.read_text()) for p in (R/'actual/data/stages').glob('*.json')]};ROOM=json.loads((O/'room-order.json').read_text())
assert len({r['code'] for r in D['battle']})==40 and len(D['battle'])==164 and len(D['endings'])==19
log=Path('/private/tmp/dialogue-full-capture.stdout').read_text();assert 'DIALOGUE_CAPTURE_COMPLETE' in log and 'SCRIPT ERROR' not in log and 'Cannot capture battle' not in log
EVENTS=catalog();rendered_stages=[];rendered_hubs=set();claimed_static=set();lines=[];quotes=[]
def out(s=''):lines.append(s)
def quote(speaker,text):
 if not text:return
 out('> '+str(speaker)+'：'+str(text).replace('\n','\n> '));out();quotes.append(str(speaker)+'：'+str(text))
def pages(ps):
 for p in ps:quote(p.get('speaker','旁白'),p['text'])
def text(s):
 for part in s.split('／'):
  if not part:continue
  a,b=part.split('：',1) if '：' in part else ('旁白',part)
  if '或' in a:
   names=a.split('或');out(f'说话者：{names[0]}；无法现场参与时由{names[-1]}说同一句。\n');a=names[0]
  quote(a,b)
def flat(events):return [p for e in events for p in e.get('pages',[])]
def sig(ps):return tuple((p.get('speaker','旁白'),p['text']) for p in ps)
def h(n,t):
 anchors={'序章：海峡城庆典':'prologue','第一章：雪下的名字':'chapter-1','第二章：没有归来的船':'chapter-2','第三章：另一种胜利':'chapter-3','第四章：故人的另一面':'chapter-4','第五章：完整的天空':'chapter-5','终局与十八人后日谈':'endings','附录一：通用照护、变量与剧情提示':'common','附录二：来源与收录核对':'sources'}
 if n==2 and t in anchors:out('<a id="'+anchors[t]+'"></a>');out()
 out('#'*n+' '+t);out()
NAMES={
'grave':'D11 · 凯尔墓前','otto':'奥托作证','daan':'达恩决定同行','prologue':'D00 · 庆典上的拘押与冲突','guard':'广场教团守卫','altar':'传光台',
'grain':'确认分粮','fula':'芙拉：邀请前与入队后','crown':'救济牌与七羽日冠','orders':'军令箱','lena':'蕾娜：邀请与照护','cooperate':'D12 · 赫兰正式合作','lance':'兰斯说明通路','treatment':'伤员照护与救治入口',
'camp':'当地人的证言','treat':'安置内院伤者','ceremony':'确认日返仪式','ceremony_confirm':'日返、显灵与庆典前夜','invite':'两条支线的求助','beck':'贝克：邀请与照护','mine_survivor':'老矿工的经历','mine_apprentice':'年轻矿工的家人','tools':'工具是否找回','staff':'药车送达与诊所交接','hervi':'赫维：交接与邀请','transport':'运药员的经历','delivery':'送达的药物',
'recruit_fula':'芙拉接受邀请','recruit_lena':'蕾娜接受邀请','recruit_beck':'贝克接受邀请','recruit_hervi':'赫维接受邀请',
'east_departure':'D21 · 卡洛的船牌与出航','east_mireille':'米蕾与伤者','east_lisa':'莉莎与残图','east_chart_start':'薇娅的残图','sea_route':'确认押送舰航路','invite_s21':'漂泊渔船求救','s21_report':'漂泊渔船救援报告','prisoners_treat':'照护俘虏与敌我伤者','lord':'洛德的邀请与后续交谈','captives_route':'引航者与神教箱','reef_route':'渔村岸线','roan':'罗恩的邀请与后续交谈','invite_s22':'海洞遗物的消息','holy_sword':'领取圣剑','holy_bow':'领取圣弓','islanders_settle':'安置岛民与开放救治','shia':'希雅的邀请与留守安排','r05':'R05 · 卡洛与希雅：报酬、旧事与承诺','east_training':'训练台','east_magic_info':'学舍导师说明法术','resistance_spring':'抗性泉','chart_recover':'取回薇娅航图','harbor_patients':'军港撤离者安置','ancient_departure':'古道西渡前确认支线','east_sail_confirm':'确认西渡','east_finale':'D26 · 抵达西岸，回到庆典','arrival_captain':'广场外的船长','arrival_altar':'认出传光台的封印','east_recruit_lord':'洛德接受邀请','east_recruit_roan':'罗恩接受邀请','east_recruit_shia':'希雅接受邀请',
 'third_prologue':'D31 · 接回庆典，神确认转移','third_altar':'仍在运作的传光台','third_reunion':'D32 · 旧街重逢与分别调查','third_people':'留守医者说明照护','third_supply':'清点转运站','third_s31':'山村地牢求援','third_records_w':'确认投送记录','third_german':'格曼：邀请、证言与问责','third_route_e':'向导的去向与提炼院后门','third_s32':'盐原营地求援','third_records_e':'确认调节记录','third_families':'获救家属与蕾娜旧誓','third_noya':'诺娅：泄密、邀请与责任','third_brother':'诺娅弟弟的生死记录','third_recruit_german':'邀请格曼的选项结果','third_recruit_noya':'邀请诺娅的选项结果','third_council':'D33 · 营站会谈','third_messenger':'确认本章支线与收束','third_relations':'R01／R04／R07／R08 · 营火谈话','third_training':'共同训练与物资交接',
 'fourth_snow_settle':'安置雪峡居民，奥托的旧事','fourth_s41':'黑钟村名册求助','fourth_transfer_report':'投送站停用后的军情','fourth_letters':'R02／R06 · 布、家书与旧同袍','fourth_tower_shutdown':'等待观测步骤、停塔与胡纳普进阶','fourth_progress':'核对两岸进度','fourth_herlan':'赫兰的伤兵与军令','fourth_well_report':'井台取水与古道路线','fourth_obs_report':'将观测步骤送往西队','fourth_marsh_report':'沼泽获救者交接','fourth_s42':'赛琳与孤岛病人的消息','fourth_island_verify':'局部隔离、艾琳进阶与引光剑','fourth_d42':'D42 · 两岸验证与最后一份救治','fourth_ring_keeper':'续愿戒交付','fourth_black_report':'名册是否保住','fourth_celine':'赛琳的邀请或遇难记录','fourth_recruit_celine':'赛琳接受邀请','fourth_vya':'维娅旧航行的另一面','fourth_spring':'祭所力量泉',
 'fifth_ward_report':'D51后续 · 赫兰留守照护与问责','fifth_shield_keeper':'护途盾交付','fifth_west_report':'西门阵与另一队的路线','fifth_repair_report':'地方循环与东门','fifth_east_report':'旧书库支路与镇关枪','fifth_archive_invite':'决定是否查阅旧书库','fifth_archive_report':'旧事记录的责任','fifth_prepare':'确认两队出阵名册','fifth_ready':'本队名单确认','fifth_merge':'合军前的最后确认','fifth_relationship':'R03 · 靠路的店与诊室'
}
NOTES={
 'grave':'首次与墓碑交谈播放D11；确认后再看墓碑，按林路是否完成、科兰是否败北改用短句。',
 'prologue':'玩家在传光台与赫兰或艾琳确认后播放。结束时显示两句旁白，再转入半年前雪原村；这里的挡法术由旁白交代，不另补写代码没有的动作分镜。',
 'fula':'先确认分粮才出现邀请。押送所尚未完成与已经完成使用不同对白；已入队改为同行短句，正式成员濒死时改由医者说明照护。未入队即遇难则不再生成芙拉交谈对象。',
 'hervi':'先完成S12送药，再请管理员交接；交接前赫维不接受邀请。正式成员濒死时使用医者短句，未获救时不提供邀请。',
 'staff':'S12获胜后首次交谈播放运药员、管理员的交接；赫维可参与时追加其回应。确认结束才记为诊所已有人员接手；之后再谈只保留安抚短句。',
 's21_report':'S21尚未完成时医者说明如何护送；完成后回此处确认安置和备用泊位。','invite_s22':'S22尚未完成时提供旧船员求助；S22完成后回此处改为遗物登记短句。','third_brother':'按诺娅弟弟的实际生死选择；与诺娅本人是否加入、是否存活分别判断。','third_route_e':'按向导实际存活状态报告；向导遇难也可凭其路线册继续。','cooperate':'查看军令后进入教堂，与赫兰确认。D12之后追加两句医者说明；确认结束后兰斯入队。合作已经完成时不重复整场。',
 'ceremony':'须先安置伤者。S11或S12未完成时先出现收束确认；举行后关闭本章未完成支线。',
 'ceremony_confirm':'确认举行后依次播放赫兰、乌库布·卡基、胡纳普、达恩及胡纳普的回应。达恩不能参与时省略其提醒。结束后进入第一章完成页。',
 'invite':'两条支线均可稍后返回。各句会按S11、S12是否已经完成分别选择，不要求两条都处于同一状态。',
 'mine_survivor':'贝克已入队后由老矿工接替战后位置；贝克未能获救时使用遇难分支。',
 'tools':'按本次是否实际取得工具选择，工具不是主线开路条件。',
 'east_departure':'首次播放D21；确认出航之后再谈使用短句。卡洛无法出场时由船长确认航线。',
 'prisoners_treat':'是F22战后继续前进的确认。米蕾不能参与则由地方医者说明；莉莎不能参与时省略她的催促。',
 'lord':'须先安置F22伤者，且洛德已被实际救出，才可邀请。',
 'shia':'先让留守骑士安置岛民，再邀请已获救的希雅；岛上的留守责任继续存在。',
 'islanders_settle':'首次安置时追加东队一份救治资源说明。岛民未能全部获救时用搜救中的报告，不假定全员安全；再次确认省去重复资源说明。',
 'r05':'卡洛与希雅都可现场参与时有完整谈话。海洞承诺未完成、完成后首次、已看过三种状态独立判断；只有卡洛可参与则用护送短句，两人均不能参与则用旁白。',
 'chart_recover':'首次确认神教箱播放F25_MYTH四页；已经取回后再看改用艾琳短句。',
 'ancient_departure':'先取回航图、确认伤者上船。S21／S22未完成的名称按实际列表提醒；确认西渡后关闭未完成的第二章支线。',
 'east_finale':'F26完成后与广场外守卫交涉，播放D26_ARRIVAL。结束后进入章节完成页，随后第三章回到同一场庆典。',
 'third_reunion':'M31与F31都完成才播放完整D32；只有一队脱围时由留守医者提示切队。米蕾正常时追加她等候艾琳的一句；濒死且仍在队时改为艾琳去照护处探望。',
 'third_german':'仅堡主败北后实际接受格曼投降、格曼存活，才有招募谈话；只解除武装或未获救不补出邀请。投降不等于免除押送责任。',
 'third_noya':'诺娅与弟弟生死分别记录。诺娅未获救时取消招募，留守医者说明；她获救时先交代泄密，再由玩家决定是否邀请。',
 'third_families':'获救组数为当场实际生还数，可为1或2；蕾娜不能参与时由家属说明旧日护送，不让家属借她身份作个人承诺。',
 'third_council':'第三章要求两队都在营站才播放D33；会谈后再谈改用计划短句。第四章同一对象改为两岸进度说明，见第四章末。',
 'third_relations':'D33确认后检查四组独立关系：R01达恩与米蕾；R04芙拉与赫维且S12完成；R08奥托与格曼；R07莉莎与诺娅。均须相应人物可参与、该事件未看过；多个事件同时满足则依此顺序播放。第四章同一交互改为R02／R06。',
 'fourth_snow_settle':'获救组数按M41实际名单填入。奥托正常时讲自己封路的经历，否则由村民提供旧军令消息；确认后开放铁骑关方向。',
 'fourth_tower_shutdown':'M43只是夺取控制室。未收到F42完整步骤时可以等待，不必重打；收到后回此处确认安全停用，首次成功推进胡纳普进阶。已停用后再谈只报告结果。',
 'fourth_letters':'R02在M42后由可参与的达恩送布与纸，按米蕾在队正常、濒死、未入队分别处理。R06要求蕾娜与兰斯均已入队；两人正常有完整交谈，一人濒死则由另一人代送家书并说明照护；事件看过后不再重复。',
 'fourth_d42':'西塔安全停用与祭所局部隔离均确认后，首次播放两岸验证。莉莎与米蕾分别由地方技术员、船团医者替代。验证后开放第四份共享救治；若引光剑此前未领，此时补交，已领取则不重复。',
 'fourth_island_verify':'确认局部隔离结果，艾琳首次进阶为引光剑使，并在符合条件且未领取时交付引光剑；已进阶后用保留训练的短说明。',
 'fourth_black_report':'按本次名册是否真正保住选择；不能在战后交谈时补回已经烧毁的记录。',
 'fourth_celine':'两组病人已安置、赛琳存活才可邀请；未能获救改为固定医者的交接记录。',
 'fourth_ring_keeper':'完整名册在烧毁前保护、避难院已确认且击败焚毁队长并获胜，回H49才能领取。资格只认当场记录。',
 'fifth_shield_keeper':'M51两处病房开门，两组伤兵均存活并撤到南口，击败队长并胜利，回H51领取。仅一组获救仍可通关，但不符合盾的交付条件；合流后不能折返领取。',
 'fifth_merge':'两队分别抵达前庭、各自出阵名单确认后才可合流。合流前提醒S51与护途盾；合流后旧书库关闭。前庭战完成后提示通往神座，否则仍指向前庭战场。',
 'fifth_relationship':'R01、R02已完成，达恩与米蕾均可参与且两队都在前庭时，首次播放R03六句。已看过后用短句；之后有人濒死改用照护者回应。'
}
# Static battle events that are not emitted just by entry/victory.
META={
'M15-ESCAPE':(['M15'],'科兰开始撤离时'), 'M12-BURN':(['M12'],'首次在粮仓门前点火之后'), 'M12-FIRE-WARNING':(['M12'],'焚毁兵出发前一己方回合'),
'S11-BECK-DUTY':(['S11'],'读取早期记录、补入贝克护送职责时的一次提示'), 'S12-CLINIC-DUTY':(['S12'],'读取早期记录、补入诊所职责时的一次提示'),
'F26-BOAT-HIT':(['F26'],'居民船遭岸上敌军攻击时'), 'F24-BEACON-WARNING':(['F24'],'敌方占住航灯、仍有夺回机会时'),
'F31-MID':(['F31'],'一组码头伤者上船时'), 'F32-MID':(['F32'],'向导接近盐路指定路段时'),
'M33-SURRENDER':(['M33'],'堡主败北后，邻接格曼选择接纳投降或只解除武装时'), 'M33-OFFER':(['M33'],'堡主败北，格曼仍存活并首次提出投降时'),
'M31-MID':(['M31'],'打开拘押院时'), 'M32-MID':(['M32'],'控制任一运输站时'), 'M32-RELEASE':(['M32'],'打开工匠运输车锁时'), 'F33-MID':(['F33'],'打开术士工房时'), 'F33-RECORD':(['F33'],'复制调节记录时'),
'S32-BROTHER':(['S32'],'打开居民营房，按弟弟存活／遇难分别播放'),
'M42-PARLEY':(['M42'],'兰斯邻接旧同袍，选择交涉后'), 'F42-ORDER':(['F42'],'未先保护东楼记录便调查中央设备时'), 'F43-ORDER':(['F43'],'尚未确认前一处干地便继续开路时'),
'M42-CUT':(['M42'],'切断投送站时'), 'M43-CONTROL':(['M43'],'夺取控制室时'), 'F42-RECORD':(['F42'],'保住东楼观测记录时'), 'F42-MYTH':(['F42'],'按顺序核对中央设备时'), 'F42-NOYA':(['F42'],'核对设备后，诺娅可参与时追加'), 'S41-TRUTH':(['S41'],'保护黑钟村名册、读到凯尔前后军令时'), 'S42-TRUTH':(['S42'],'查看孤岛诊疗记录时'),
'CH4-FIRE-FIRST':(['F42','S41'],'焚毁兵第一次达到门前点火计数时'), '-FIRE-WARNING':(['F42','S41'],'各关焚毁兵出发前一己方回合'), 'F43-SUMMON':(['F43'],'第3回合起神官仍在时，一次召唤波次出现'), 'M44-MID':(['M44'],'赫兰生命降至一半或以下时'), 'M44-SURRENDER':(['M44'],'赫兰被击败后存活投降，首次交出指挥权时'), 'F44-TEST':(['F44'],'三处调节点都确认后，开始等待局部隔离试验'),
'M52-ORDER':(['M52'],'尚未解开前段桥锁便尝试后段时'), 'S51-ORDER':(['S51'],'未取得记录或守卫未被击败便尝试南门交接时'), 'S51-TRUTH':(['S51'],'取回旧书库原始记录时'), 'J54-PHASE':(['J54'],'实体半血后，一次强化与三名援军出现时')
}
# The unidentified keys below are generated from object IDs rather than a named scene.
for e in EVENTS:
 if not e['key'] and e['file']=='chapter3_rules':e['key']='S31-OLD-UNIT';META[e['key']]=(['S31'],'蕾娜邻接旧部，选择劝其放下武器时')
 if e['key']=='-OPEN':
  e['key']=e['file']+'-OPEN';META[e['key']]=(['M13','M15'] if e['file']=='game_state' else ['M51'],'打开对应牢门／病房门时')
 if e['key']=='-WORK':e['key']='REPAIR-WORK';META[e['key']]=(['F51'],'与装置南侧工班开始交接时')
 if e['key']=='-COMPLETE':e['key']='REPAIR-COMPLETE';META[e['key']]=(['F51'],'保护到下一己方回合，工班交接完成时')
MID_NOTES={'M11':'流民抵达出口时；多个护送组共用一次途中事件键。','M12':'正式成员占领粮仓前庭时。','M13':'打开第一处劳工牢门后；蕾娜不能参与时省去她的私人发言。','M14':'守将半血并提出投降时。','M15':'首次与科兰交战时。','S11':'矿工抵达出口时。','S12':'药车抵达诊所交付点时。','F21':'第3回合敌方阶段开始时。','F22':'打开囚舱／救援门时；洛德不可参与时由引航者替代。','F23':'正式成员推进至北侧路段时。','F24':'第4己方回合时；按岛民与希雅的实际状态分支。','F25':'开牢救人时；首次攻击裴萨另播放D22_FIRST。','F26':'居民船抵达路线中段时。','S21':'病人受伤、需要前排护住跳板时。','S22':'打开藏身岩室营救旧船员时；按卡洛是否可参与分支。'}
EQUIVALENT={}

def battle(code):
 s=ST[code];rendered_stages.append(code);out('<a id="'+code+'"></a>');out();h(3,code+' · '+s['name_zh']+('〔支线〕' if code.startswith('S') else '〔主线〕'))
 out(f'任务目标：{s["goal"]}');out()
 records=[r for r in D['battle'] if r['code']==code];base=next(r for r in records if r['variant']=='normal')
 for field,label in [('start','开场与入场说明'),('mid','战中推进')]:
  if field=='mid' and not any(r[field] for r in records):continue
  h(4,label)
  if field=='mid':out('触发：'+MID_NOTES.get(code,'按当前关卡交互／推进触发。'));out()
  if field=='after' and code=='M15':out('顺序：先D13科兰败北，再进入现场安置；日返在H06另行确认。');out()
  if field=='after' and code=='F25':out('顺序：先D22_DEFEAT败北段，再交代引航者撤离；航图在H26主动调查神教箱时取得。');out()
  original=flat(base[field]);pages(original)
  seen={sig(original)}
  for r in records:
   ps=flat(r[field]);key=sig(ps)
   if key in seen:continue
   seen.add(key);new=[p for p in ps if (p.get('speaker','旁白'),p['text']) not in set(sig(original))];removed=[p for p in original if (p.get('speaker','旁白'),p['text']) not in set(key)]
   if not new and not removed:continue
   condition={'npc_dead_care':'旧船员遇难且卡洛无法参与时','shia_unavailable':'岛民存活、希雅未能参与时','care':'相应正式同伴濒死／无法现场参与时','npc_dead':'本关相关未入队人物或任务NPC遇难时','no_survivors':'敌方没有存活缴械者时','transfer_cut':'进入祭所战前西队已切断投送站时','record_lost':'名册已被焚毁、仅保留证言时'}[r['variant']]
   if r['variant']=='no_survivors' and code!='M14':continue
   if r['variant']=='npc_dead' and code not in ['M13','F22','F23','F24','S22','S32','S42']:continue
   out('**条件分支：'+condition+'。以下为替换／追加的原句，未列部分沿用上文。**');out();pages(new)
   if removed:
    out('此分支省去以下常规发言：'+ '、'.join('“'+p.get('speaker','旁白')+'：'+p['text']+'”' for p in removed)+'。');out()
  if field=='mid' and code=='F25':
   h(4,'D22_FIRST · 首次与裴萨交锋');out('触发：首次攻击裴萨；同场不重复播放。');out();pages(json.loads((R/'actual/data/campaign.json').read_text())['scenes']['D22_FIRST'])
 # Interactions and timed events are listed in the order the player encounters them.
 extra=[e for e in EVENTS if e['key'] in META and code in META[e['key']][0]]
 if extra:
  h(4,'战中交互、警告与特殊事件')
  for e in extra:
   claimed_static.add((e['file'],e['line']));out('**'+META[e['key']][1]+'**');out()
   for i,t in enumerate(e['texts']):
    if len(e['texts'])>1:out('人物存活分支：' if i==0 else '人物遇难分支：');out()
    text(t)
 for obj in s['objects']:
  if obj.get('dialogue'):
   h(4,'战场访问 · '+str(obj.get('label',obj.get('name_zh','交谈／调查'))));out('触发：在对应访问点确认；与开场、胜利对白分开。');out();text(obj['dialogue'])
 # Attack warnings are authored data; numerical intent fields depend on the live attacker.
 tactics=s.get('battlefield_tactics',{})
 if tactics.get('command'):
  h(4,'协同命令');out('触发：统领与投送站仍有效，达到指挥开始回合；只首次宣布。');out();text(tactics['command']['warning'])
 for attack in tactics.get('attacks',[]):
  h(4,'特殊攻击预告 · '+attack['name']);actor=next(u for u in s['enemies'] if u['id']==attack['actor']);quote(actor['name_zh'],attack['warning'])
  out('随后显示动态攻击提示，完整模板见附录“特殊攻击”。');out()
 for obstacle in s.get('breakable_obstacles',[]):
  h(4,'障碍破坏 · '+obstacle['name_zh']);quote('战场提示',obstacle['name_zh']+'已破坏。'+obstacle['effect_text'])
 h(4,'胜利后自动对白与交付')
 if code=='M15':out('顺序：D13科兰败北→现场安置；日返在H06另行确认。');out()
 if code=='F25':out('顺序：D22_DEFEAT败北段→引航者撤离；航图在H26神教箱处另行取得。');out()
 original=flat(base['after']);pages(original);seen={sig(original)}
 for r in records:
  ps=flat(r['after']);key=sig(ps)
  if key in seen:continue
  seen.add(key)
  if r['variant']=='no_survivors' and code!='M14':continue
  if r['variant']=='npc_dead' and code not in ['M13','F22','F23','F24','S22','S32','S42']:continue
  new=[p for p in ps if (p.get('speaker','旁白'),p['text']) not in set(sig(original))];removed=[p for p in original if (p.get('speaker','旁白'),p['text']) not in set(key)]
  condition={'npc_dead_care':'旧船员遇难且卡洛无法参与时','shia_unavailable':'岛民存活、希雅未能参与时','care':'相关正式同伴无法参与时','npc_dead':'相关未入队人物遇难时','no_survivors':'没有存活的缴械者时','transfer_cut':'西队事先切断投送站时','record_lost':'名册焚毁时'}[r['variant']]
  out('**条件分支：'+condition+'。下列句替换常规段，其余沿用。**');out();pages(new)
  if removed:out('此分支不播放：'+'、'.join('“'+p.get('speaker','旁白')+'：'+p['text']+'”' for p in removed)+'。');out()
 out(f'来源：[本关数据](../actual/data/stages/{code}.json)及第{s["chapter"]}章实际事件控制器。');out()

# Human-readable action labels, branch conditions and chronological hub placement.
def branch_label(action,rows,ps):
 blob=''.join(p['text'] for p in ps)
 if action=='s21_report':return 'S21完成后回来报告' if '获救的人已经' in blob else 'S21尚未完成时'
 if action=='invite_s22':return 'S22完成后再谈' if '海洞的遗物已经登记' in blob else 'S22尚未完成时'
 if action=='invite':return '两条支线都完成后再谈' if '矿工们都回来了' in blob and '药已经送到' in blob else '尚未完成时的求助（两句各自按对应支线判断）'
 if action=='third_brother':return '弟弟生还时' if '已经交给照护处' in blob else '弟弟遇难时'
 if action=='third_route_e':return '向导生还时' if '向导已把' in blob else '向导遇难、已取回路线册时'
 if action=='third_german' and '石堡的投降者和伤亡' in blob:return '只解除武装或格曼未能获救时'

 if action=='fourth_black_report':return '名册保住时' if '完整名册已经存档' in blob else '名册未保住时'
 if action in ['third_noya','fourth_celine'] and ('没有活着' in blob or '没能活着' in blob):return '人物未获救时'
 if action=='fourth_celine' and '两组病人都安置好了' in blob:return '病人已安置、赛琳尚未入队时'
 if action in ['fourth_ring_keeper','fifth_shield_keeper']:
  return '已经领取后再谈' if '已经交付' in blob else '当场记录符合条件，首次交付' if '已收入西队行囊' in blob else '尚不符合交付条件'
 if action=='third_families':return '一组家庭获救时' if '1组家庭' in blob else '蕾娜无法参与时' if '请告诉她' in blob else '两组家庭获救、蕾娜正常时'
 if action=='fourth_d42':
  if '日塔那边停了' in blob:return '首次两岸确认；莉莎／米蕾正常' if ps[0]['speaker']=='莉莎' else '首次两岸确认；相应人物由固定人员替代'
  return '已确认后再谈' if '两岸验证已完成' in blob else '仍缺西塔回信时'
 if action=='fifth_relationship':
  if len(ps)>=6:return 'R01、R02完成后首次R03'
  if '伤情与未完成' in blob:return 'R03前置条件尚未满足'
  if '照护者'==ps[0].get('speaker'):return 'R03已经完成，之后有人需要照护'
 if action=='r05':
  if '承诺已经兑现' in blob:return '完成海洞承诺后首次交谈'
  if '你收了钱' in blob:return '海洞承诺尚未完成时首次交谈'
  if '岛上的船仍有人修' in blob:return '关系谈话已看过后再谈'
  if ps[0].get('speaker')=='卡洛':return '卡洛可参与、希雅不能参与'
  return '卡洛不能现场参与时'
 custom=[r['label'] for r in rows if r['label'] not in ['首次／常规条件','相关事项完成后再谈','相关同伴濒死时','支线／前置事项尚未完成']]
 if custom:return custom[0]
 return '常规交谈' if rows[0]['label']=='首次／常规条件' else rows[0]['label']

def room(room,ch=None,actions=None):
 info=ROOM[room];chapter=ch if ch is not None else info['chapter']
 title={'P00':'序章 · 海峡城庆典','H01':'半年前 · 雪原村','H02':'丘堡粮站 · 战后','H03':'南岗押送所 · 战后','H04':'旧塔教堂 · 合作','H05':'旧塔外营 · 战后','H06':'旧塔内院 · 安置与日返','H07':'林路营地 · 支线消息','H08':'旧矿道 · 战后','H09':'林村诊所 · 交接'}
 for n in [2,3,4,5]:
  data=json.loads((R/f'actual/data/chapter{n}_hubs.json').read_text())['rooms']
  if room in data:title[room]=data[room]['title']
 h(3,room+' · '+title[room]+('〔第四章重访〕' if room=='H10' and chapter==4 else ''))
 records=[r for r in D['hub'] if r['room']==room and int(r['chapter'])==max(1,chapter)]
 ordered=actions or info['actions']
 for action in ordered:
  rows=[r for r in records if r['action']==action]
  if not rows:continue
  rendered_hubs.add((room,int(max(1,chapter)),action));h(4,NAMES.get(action,action))
  if action in NOTES:out('触发与条件：'+NOTES[action]);out()
  elif action.startswith(('recruit_','east_recruit_','third_recruit_','fourth_recruit_')):out('触发：在对应人物的邀请菜单中确认同行；未满足救援、交接或存活条件时不补发招募。成功入队播放入队短乐，随后恢复场景音乐。');out()
  else:out('触发：在此据点面对对应人物／物件确认。以下分组互斥，不会连续全播。');out()
  groups=collections.OrderedDict()
  for row in rows:
   ps=[p for e in row['played'] for p in e['pages']]
   if ps:groups.setdefault(sig(ps),[]).append(row)
  for key,group in groups.items():
   ps=[p for e in group[0]['played'] for p in e['pages']];out('**'+branch_label(action,group,ps)+'**');out();pages(ps)
  # Story options and gate notices belong with the conversation, not in the character's mouth.
  menus=[];notices=[]
  for row in rows:
   for m in row['menus']:
    if m['id'] in ['recruit','side_closure','east_closure','third_end','fourth_end','fifth_merge']:
     val='／'.join(m['labels'])
     if val not in menus:menus.append(val)
   for v in row['notices']:
    if v not in notices:notices.append(v)
  if menus:out('玩家选项：'+'；'.join('“'+m+'”' for m in menus)+'。');out()
  if notices:
   out('相关门槛／结果提示（界面显示，不是人物对白）：');out()
   for v in notices:quote('界面提示',v)
  if not groups and not menus and not notices:out('此操作只改变记录或打开菜单，没有额外剧情句。');out()
 if room=='H05':out('实现说明：此据点的投降兵对象目前固定存在，其交谈原文如上；战场结束的无人存活分支另见M14，不在文档中擅自改写据点。');out()
 out('演绎：普通交谈后回到据点。带剧情确认的事件依上方说明切换章节、开放道路或记录邀请；完成交接后由玩家返回大地图。');out()

# ----- Single current script, in player order -----
h(1,'《复仇与回忆》完整台词汇总')
out('现行全流程台本｜2026-10-26｜对应当前 actual 工作区，全五章。');out()
out('本文从序章到终局按游玩流程编排，收录31场主线、9场支线、战中交互、战后自动对白、战后据点、招募、8组关系事件、兵装与饰品交付、主角进阶及18人后日谈。正文只保留当前代码实际调用的台词；旧设计样段、未被调用的字段和重复聚合场景不再与现行台本混排。');out()
out('这次以当前本地代码为准，包含刚完成的第一章改稿，不回退到10月25日已安装的旧手机包。文本保持运行原文，不借整理改写人物语气。');out()
h(2,'阅读方式与全流程路线')
out('同一事件的常规、已完成、濒死、未招募、NPC遇难、救援成败等分支放在一起；它们互斥，不会在一次游玩中连续全播。分支只替换列出的句子，其余沿用常规段。正式同伴濒死仍在队接受照护，未入队人物及任务NPC的遇难按真实结果处理。');out()
out('“演绎”只说明当前转场、旁白与交互结果，不添加尚无运行实现的动作分镜。对话框分页会随设备宽度变化，本文按完整句记录，不把显示分页误算为额外台词。装备数字格、伤害数值和普通按钮标签不作为剧情台词混入正文；剧情门槛、选择与转场提示仍保留。');out()
out('主线、支线交错顺序可由玩家选择。下表采用一条包含全部支线的阅读路线，两队可互换行动先后；支线不会因此变成强制主线。');out()
out('|章节|阅读路线（含全部支线）|\n|---|---|\n|序章|海峡城庆典 → D00 → 半年前雪原村|\n|第一章|M11 → M12 → M13／教堂合作 → S11 → S12 → M14 → M15 → 日返|\n|第二章|D21 → F21 → S21 → F22 → F23 → S22 → F24 → F25 → F26 → 抵岸|\n|第三章|D31 → M31与F31 → D32 → M32 → S31 → M33 → F32 → S32 → F33 → D33与营火关系|\n|第四章|M41 → S41 → M42 → M43夺塔 → F41 → F42 → 回西塔确认停用 → M44 → F43 → S42 → F44 → 两岸验证 → 营站收束|\n|第五章|M51 → M52 → F51 → F52 → S51 → 两军整备／R03／合流 → J53 → J54 → 结局|');out()
out('目录：[序章](#prologue) · [第一章](#chapter-1) · [第二章](#chapter-2) · [第三章](#chapter-3) · [第四章](#chapter-4) · [第五章](#chapter-5) · [结局](#endings) · [通用分支](#common) · [收录核对](#sources)');out()

def chapter_end(ch,title,body):
 h(3,'章节收束画面');quote('画面标题',f'第{ch}章完成');quote('画面副标题',title);quote('画面说明',body);quote('保存提示','成长与伤亡已保存' if ch=='一' else '两队成长与伤情已保存');quote('操作提示','确认打开菜单')

h(2,'序章：海峡城庆典');room('P00');out('演绎接续：D00末尾旁白结束后转到半年前的雪原村。');out()
h(2,'第一章：雪下的名字');room('H01');battle('M11');room('H07');out('支线消息此时已可取得；以下阅读路线先处理粮站与押送所，再回营地前往矿道和诊所。');out();battle('M12');room('H02');battle('M13');room('H03');room('H04');battle('S11');room('H08');battle('S12');room('H09');battle('M14');room('H05');battle('M15');room('H06');chapter_end('一','庆典前夜','科兰已败，日光重返西大陆。')
h(2,'第二章：没有归来的船');quote('旁白','半年前，东群岛的风灯岛。艾琳守着船团的航灯，等待一条没有归来的船的消息。');room('H21');battle('F21');room('H22');battle('S21');battle('F22');room('H23');battle('F23');room('H24');battle('S22');out('接续：海洞完成后回H24旧船员处报告；H24已列完成前后的两个分支。卡洛与希雅的R05在H25或H26触发。');out();battle('F24');room('H25');battle('F25');room('H26');battle('F26');room('H27');chapter_end('二','没有归来的船','船团抵达西岸。\n艾琳被带往庆典广场。')
h(2,'第三章：另一种胜利');room('H30');battle('M31');battle('F31');room('H31');battle('M32');room('H32');battle('S31');room('H36');battle('M33');room('H33');battle('F32');room('H34');battle('S32');room('H37');battle('F33');room('H35');room('H10',3);chapter_end('三','另一种胜利','两队已会合，记录得到互证。\n下一步是验证安全停用方案。')
h(2,'第四章：故人的另一面');battle('M41');room('H41');battle('S41');room('H49');battle('M42');room('H42');battle('M43');room('H43');battle('F41');room('H45');battle('F42');room('H46');h(3,'回到西塔：完成安全停用');out('此时返回H43控制台，接续“已收到观测步骤，首次安全停塔”分支：先隔离远端、分段降流、核对村庄光源，再开放王都道路与胡纳普进阶。完整原文已放在H43，不重复整场。');out();battle('M44');room('H44');battle('F43');room('H47');battle('S42');room('H50');battle('F44');room('H48');room('H10',4,actions=['third_council','third_messenger','third_relations']);chapter_end('四','故人的另一面','两岸验证成功，村庄保住了日光。\n下一步，两队分别向神宫进发。')
h(2,'第五章：完整的天空');battle('M51');room('H51');battle('M52');room('H52');battle('F51');room('H53');battle('F52');room('H54');battle('S51');room('H56');room('H55');battle('J53');out('接续：回H55整备。此时合流确认点采用“已合流／前庭战已完成”分支，沿北方道路进入神座；R03与伤员照护仍按各自条件判断。');out();battle('J54')
h(2,'终局与十八人后日谈');out('演绎顺序：先播放J54胜利后三句，再进入结局阅读页。依次显示两段共同收束、18名人物结果、“仍会相见”和“全篇结束”。真实招募、濒死、救治次数、关系与亲属生死决定文字；没有把所有分支同时播放。');out()
profiles={'care_used':'最终仍濒死，此前已用过一次救治','care_used_romance':'最终仍濒死且已用过救治，三段关系完成','care_used_truths':'最终仍濒死且已用过救治，弟弟生还／海洞承诺完成','normal':'在队、正常；无附加关系／特殊结果','romance':'在队正常，R01／R02／R03均完成','unrecruited':'未加入本次同行名册，未记录遇难','npc_death':'未加入本次名册，且确有遇难记录','care':'最终仍濒死，未用过救治','care_romance':'最终仍濒死，三段关系均完成','healed':'接受过一次救治后正常抵达','healed_romance':'救治后正常抵达，三段关系均完成','truths':'诺娅弟弟生还；卡洛完成海洞承诺','truths_romance':'上述特殊结果与三段关系均完成','care_truths':'最终仍濒死，弟弟生还／海洞承诺完成','healed_truths':'救治后正常，弟弟生还／海洞承诺完成','fula_care':'赫维正常同行，芙拉最终仍需照护','beck_archer':'贝克最终为弓手／弓骑兵','beck_rider':'贝克最终为游骑兵','beck_soldier':'贝克最终为士兵'}
normal=D['endings'][0]['pages']
for index,entry in enumerate(normal):
 h(3,entry['title']);variants=collections.OrderedDict()
 for r in D['endings']:
  p=r['pages'][index]
  if entry['title'] in ['胡纳普','艾琳','达恩','奥托','米蕾','莉莎','卡洛','兰斯'] and r['profile'] in ['unrecruited','npc_death']:continue
  variants.setdefault(p['text'],[]).append(r['profile'])
 for body,states in variants.items():
  meaningful=[v for v in states if v not in ['truths_romance','healed_romance','healed_truths','care_romance','care_truths']]
  selected=meaningful[0] if meaningful else states[0]
  if len(variants)>1:out('**'+profiles[selected]+'**');out()
  quote('结局文字',body)
out('拼接说明：救治后正常者会在其个人基础后日谈前追加“接受救治后，{姓名}活着走到了旅程终点。”；最终濒死但曾用过救治者，照护段中加入“此前已经使用过一次救治，”。卡洛、诺娅及关系结果再按本节对应句追加。弟弟遇难、船员遇难等事实不会因角色招募或救治而自动改变。');out()
h(2,'附录一：通用照护、变量与剧情提示')
h(3,'正式同伴濒死、救治与据点照护')
out('正式成员生命归零时显示：');out();quote('战场提示','{姓名}濒死，已撤至照护处，暂时不能出阵。')
out('在据点向已入队且濒死的同伴交谈，通用照护句为：');out();quote('医者','{姓名}仍在队伍中，由我们照护，暂时不能出阵。可在部队状态查看伤情。')
out('救治菜单条件与结果按实际记录显示；以下是界面原句模板，不由普通人物朗读。');out()
for t in ['请到本队救治泉接受救治','只能救治本队正式同伴','该成员无需濒死救治','已接受过一次救治，无法再次救治','本队救治份额已用尽','保存失败，未消耗救治份额','先完成教堂合作或安置岛民，开放本队救治份额','没有可救治的濒死成员；份额可以保留','救治完成，可以重新出阵；剩余{份数}份']:
 quote('界面提示',t)
out('资源说明已在实际发生地点保留完整原文：H04教堂合作、H25岛民安置、H10第三章会谈、H48两岸验证；未用份额保留，D33之后合为两队共享。');out()
h(3,'说话者缺席与替代规则')
out('第一、二章战场字符串经通用队列筛选；第三章以后使用章节事件筛选。直接据点谈话还要看各事件自己的条件，不能把下面的表强加到没有使用该筛选器的场景。');out()
out('|位置|当前处理|\n|---|---|\n|第一章芙拉、蕾娜个人经历|相应人物不能参与时直接省去受限个人句；不借用管理员或胡纳普的身份重说|\n|第一章其他战场通用句|奥托→村民，芙拉／赫维→管理员，兰斯→教团兵；其他不可参与人物转胡纳普，并改为固定救援短句|\n|第二章战场|米蕾→地方医者，莉莎→甲板护卫，卡洛→固定舵手，洛德→引航者，罗恩→渔村长者，希雅→留守骑士；其余转艾琳|\n|第三至五章事件|蕾娜→城外军官，达恩→居民，奥托→工匠，兰斯→运输工，米蕾→船医，莉莎→艾琳，卡洛→船长，罗恩→舵手，希雅→留守骑士；其他未列人物用旁白|\n|源码写有“A或B”的事件|A可参与则A发言，否则B说同一句；并非把“或”显示成角色名|');out()
quote('胡纳普','路已查清。我们先把这里的人带回去。')
out('第二章卡洛不能参与，且原句涉及报酬或“这次我去送”时，使用以下照护句：');out();quote('固定舵手','卡洛正在接受照护。遗物由我们代为交给家属，等他恢复再继续履行承诺。')
h(3,'撤离、援军与物品整理')
out('第三章及以后护送组抵达出口，使用一次撤离事件：');out();quote('居民','接应的人到了。我们先到安全处等候。')
quote('斥候','后方路口有援军。下一回合抵达，只有这一队。')
out('上句在关卡的固定增援前一己方回合显示；没有这一增援的关卡不播放。');out()
quote('旁白','运输队已满。整理装备后，可以再来领取。')
quote('旁白','获得{物品名}，{接收成员名}装备。')
quote('旁白','获得{物品名}，收入运输队。')
quote('旁白','战后整理出{以“、”连接的本次物品名}，已收入本队行囊，可在部队整备中分配。')
out('守途兵装、拒阵枪、护途盾、续愿戒的逐关交付原文已放在对应战后与据点；同一事件领取一次，已领后不再发放。');out()
h(3,'进度、未完成支线与收束提醒的变量')
out('这些句子包含实际名单，不能固定为“全部获救”或“全部完成”。书中列出的具体1组／2组是相应结果例句；运行时按当前记录填入。');out()
for speaker,body in [('家属','这次回来的是{获救组数}组家庭。救援和伤亡都记在名单上，狱卒的责任不能就这样算了。'),('医者','登记了{获救组数}组存活居民。遇难的人另记姓名，不会从名册上划掉。铁骑关的道路已标出来。'),('船长','西渡后，我们暂时不能折返。尚未完成：{漂泊渔船／碎石海洞，实际未完成项以“、”连接}。可以先回去，准备好再来找我。'),('信使','尚未完成的支路：{山村地牢／盐原营地，按实际未完成项连接}。确认分兵后本章救援收束，准备好了再来找我。'),('信使','尚未完成：{黑钟村名册／沼泽孤岛救援（定潮枪尚未取得），按实际未完成项连接}。可先返回支路，再确认本章收束。')]:quote(speaker,body)
out('第四章进度句为“信使：{未完成事项以“；”连接}。”，每项按实际状态从下列原文选择：');out()
for t in ['西队：北境日塔控制室，确认安全停用','东队：盐原观测台，取得停用步骤；西队再到日塔控制室确认','西队：王都城门，击败赫兰并占领门楼','东队：沉没祭所，完成三点隔离试验','东队：沉没祭所调节庭，两岸确认信']:quote('进度项',t)
out('饰品收束提醒按是否符合交付资格、是否已经领取显示；已经领取则没有提醒：');out()
for t in ['护途盾尚未领取，可回王都内廷伤兵照护处找军械官；合流后无法折返。','续愿戒尚未领取，可回黑钟村避难院找保管人；进入第五章后无法折返。','护途盾尚未取得；领取需M51两处病房开门、两组伤兵存活撤离并胜利。合流后无法补做。不影响主线。','续愿戒尚未取得；领取需S41保住名册、确认避难院并胜利。进入第五章后无法补做。不影响主线。']:quote('守卫／信使',t)
h(3,'特殊攻击、掩护、击退与障碍提示')
out('F22封桥射击、J54聚光震荡的角色预告在本关正文。随后以当前敌人的实际属性填入如下提示；达到累计伤害打断阈值的攻击才插入第二个短语：');out()
quote('战场提示','{招式名}将在本回合敌方阶段攻击标记格；撤离可避开，掩护可分担。推动蓄力者可打断{，准备期间累计造成N点实际伤害也可打断}。标记格内必中；威力{实际威力}，按{物防／魔防}结算。')
for t in ['{招式名}被打断。敌方仍可正常反击，本次蓄力动作失效。','{招式名}准备被打乱，本次攻击取消。','{掩护者姓名}掩护分担{伤害}伤害。','{招式名}已释放。仅标记格承受直接攻击，掩护分担另行结算。','{目标姓名}被击退一格。','{障碍名}可在邻格消耗一次行动破坏。{本障碍的效果说明}','{障碍名}已破坏。{本障碍的效果说明}']:quote('战场提示',t)
quote('战场提示','掩护：放弃攻击，保护一名相邻且本回合已行动的队友至下次己方回合。首次命中时分担一半伤害；掩护者生命不足时，余量仍由原目标承担。')
h(3,'可选营地补练')
out('补练不属于40场主支线，也不推进剧情。8个章节／队伍演习点共用下列两种开场；每章每队最多成功2次，单场上限10回合，成功每名参训者60经验。');out()
quote('教习','这是营地对练，倒地会退出本场，不会留下新的伤势。')
quote('教习','抵达演习据点并结束行动，或击败全部对练者。 本场最多10回合；成功后每位参训者获得60经验，包括本场倒地者。')
quote('教习','守住演习据点，连续坚持3个敌方阶段；也可击败全部对练者。 本场最多10回合；成功后每位参训者获得60经验，包括本场倒地者。')
out('地点名称：西岸接应演习、海岸守望演习、山道轮防演习、盐路接应演习、城郊轮防演习、泉地守望演习、前线整备演习、修复区接应演习；每处有突破、护阵两种目标。战后进入奖励／回营流程，没有额外固定人物演出；保留的after字段不作为另一次已播放对白抄入。');out()
for t in ['领队退出演习；本次无收益，可重试或回营。','演习时限已到；本次无收益，可重试或回营。']:quote('失败提示',t)
h(3,'故事战败的界面原因')
out('以下只在相应失败条件成立时显示，不由人物朗读；重复原因去重。姓名、组名按当前目标填入。');out()
failures=[]
for name in ['game_state','chapter2_rules','chapter3_rules','chapter4_rules','chapter5_rules']:
 src=(R/f'actual/core/{name}.gd').read_text()
 for match in re.finditer(r'(?:g\.)?_fail\(([^\n]*)',src):
  chunk=match[1]
  for value in literals(chunk):
   if re.search('[\u4e00-\u9fff]',value) and len(value)>=4 and value not in failures:failures.append(value)
for t in failures:
 if t in ['濒死，无法继续作战','未能获救']:t='{姓名／目标名}'+t
 quote('失败提示',t)

h(2,'附录二：来源与收录核对')
out('本台本对应2026-10-26当前代码。整理时读取真实事件函数的对话队列，并在不保存的内存状态中分别提取正常、已完成、濒死、NPC遇难、投降、名册焚毁、兵装交付、关系及结局分支；这不是把模拟分支冒充一次全员生还的实玩，也没有重复宣称本轮重新打通40关。');out()
out('来源：当前场景配置、40张现行关卡数据、各章战场控制器、据点控制器、兵装与饰品交付、濒死照护、结局生成器、章节转场及特殊战术提示。已被控制器替换的before／during／after字段、兼容旧地图、原复刻台词与D22重复聚合数组不混入正文。');out()
out('当前没有额外独立播放的旧字段不再标为“待实现剧情”。等待观测步骤、交接未完成、人物不可招募等是已经实现的条件分支。原文中仍存在的运行措辞或分支表现按实记录；本次只重整文档，不顺带修改游戏行为。');out()
out('核对记录：[当前台本收录与源文件哈希](../actual/reports/dialogue-complete-20261026/coverage.json)。旧版文档已另存到本次记录目录，主文档不再保留两套相互矛盾的正文。');out()

assert len(rendered_stages)==40 and set(rendered_stages)==set(ST)
# All dialogue-emitting hub actions must be represented, including shared fourth-chapter H10 actions.
expected_hubs={(r['room'],int(r['chapter']),r['action']) for r in D['hub'] if r['played']}
assert expected_hubs<=rendered_hubs,expected_hubs-rendered_hubs
book='\n'.join(lines)+'\n';norm=lambda x:re.sub(r'\s+','',x)
# Coverage checks compare the complete spoken text, not authoring metadata or the obsolete document.
source_missing=[];body=norm(book)
for r in D['hub']:
 for e in r['played']:
  for p in e['pages']:
   if norm(p['text']) not in body:source_missing.append(('hub',r['room'],r['action'],p['text']))
for r in D['battle']:
 for field in ['start','mid','after']:
  for p in flat(r[field]):
   if norm(p['text']) not in body:source_missing.append(('battle',r['code'],field,p['text']))
for e in EVENTS:
 if e['key'] in META:
  for t in e['texts']:
   for part in t.split('／'):
    phrase=part.split('：',1)[-1]
    if norm(phrase) not in body:source_missing.append(('static',e['file'],e['line'],phrase))
assert not source_missing,source_missing[:20]
for entry in D['endings']:
 for page in entry['pages']:
  if entry['profile'] in ['unrecruited','npc_death'] and page['title'] in ['胡纳普','艾琳','达恩','奥托','米蕾','莉莎','卡洛','兰斯']:continue
  assert norm(page['text']) in body,('ending',entry['profile'],page['title'])
previous=json.loads((R/'actual/reports/dialogue-coverage-audit-20261026/audit.json').read_text());missing_fixed=[]
for item in previous['hub_literals']:
 if norm(item['literal'].split('：',1)[-1]) not in body:missing_fixed.append(item)
assert not missing_fixed,missing_fixed
for stale in ['〔待实现设计〕','状态：设计文本，尚未接入','chapter_limit=3','0.8.13','第四、五章与结局尚未实现']:
 assert stale not in book,stale
# Save the previous version once before replacing the authoritative document.
backup=O/'before-document.md'
if not backup.exists():backup.write_bytes(DOC.read_bytes())
DOC.write_text(book)
source_paths=[R/'actual/data/campaign.json',*[R/f'actual/data/stages/{code}.json' for code in ST],*[R/f'actual/core/{n}.gd' for n in ['game_state','story_hub','chapter2_rules','chapter3_rules','chapter3_hub','chapter4_rules','chapter4_hub','chapter5_rules','chapter5_hub','chapter5_endings','story_armaments','story_accessories','casualty_rules','battlefield_tactics','main','training_rules']],*[R/f'actual/data/{n}.json' for n in ['story_armaments','story_accessories','training_encounters','knockback_equipment']]]
coverage={'date':'2026-10-26','document':str(DOC),'stages':40,'main':31,'side':9,'rooms':42,'hub_probe_outputs':len(D['hub']),'battle_probe_states':len(D['battle']),'ending_profiles':len(D['endings']),'fixed_hub_phrases_checked':len(previous['hub_literals']),'missing_fixed_hub_phrases':missing_fixed,'missing_captured_spoken_text':source_missing,'unique_displayed_utterances':len(set(quotes)),'document_lines':len(book.splitlines()),'document_bytes':len(book.encode()),'runtime_modified':False,'phone_updated':False,'method':'Read-only authored source plus no-save headless event extraction; not a new full-campaign playthrough. Conditional endings/transitions documented from the actual generators.','source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'document_sha256':hashlib.sha256(DOC.read_bytes()).hexdigest()}
(O/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:coverage[k] for k in ['stages','main','side','hub_probe_outputs','battle_probe_states','ending_profiles','fixed_hub_phrases_checked','unique_displayed_utterances','document_lines','document_bytes']},ensure_ascii=False))
