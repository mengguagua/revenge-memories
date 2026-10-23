extends RefCounted
## Independent route progress and explicit chapter-three objective contracts.
const STAGES := [301,302,303,304,305,306,311,312]
const ROOMS := ["H30","H31","H32","H33","H34","H35","H36","H37","H10"]

static func begin(g) -> bool:
	if g.chapter!=2 or not g.flags.get("chapter2_complete",false) or not g.stage_cleared(206):return false
	g.parties.celica=g.party.duplicate()
	g.chapter=3;g.route="alm";g.party=g.parties.alm.duplicate()
	g.world_node=6;g.previous_world_node=6;g.route_positions={"alm":6,"celica":6}
	g.flags.chapter3_started=true;g.flags.chapter3_pending=false;g.flags.chapter3_previous={"alm":6,"celica":6}
	g.flags.chapter3_recruits={"german":false,"noya":false};g.flags.quest={};g.flags.erase("active_plot")
	_reset(g,301);g.mode="hub";g.hub_record="H30";g.hub_position=Vector2i(6,7)
	return true

static func _reset(g,id: int) -> void:
	g.stage_id=id;g.battle_data=g.stages[id].duplicate(true);g.units.clear();g.battle_start_snapshot.clear();g.battle_return.clear();g.victory_rewards.clear();g.story_events.clear()
	g.battle_settled=false;g.battle_outcome="";g.selected_id="";g.phase="player";g.turn=1;g.flags.quest={}

static func can_switch(g) -> bool:
	return g.chapter==3 and g.mode in ["world","hub","chapter_end"] and not g.flags.has("active_plot") and g.flags.get("D31_done",false) and g.stage_cleared(301)

static func switch_route(g) -> bool:
	if not can_switch(g):return false
	g.parties[g.route]=g.party.duplicate();g.route_positions[g.route]=g.world_node
	g.flags.chapter3_previous[g.route]=g.previous_world_node
	g.route="celica" if g.route=="alm" else "alm";g.party=g.parties[g.route].duplicate()
	g.world_node=int(g.route_positions[g.route]);g.previous_world_node=int(g.flags.chapter3_previous[g.route])
	_reset(g,stage_for_node(g,g.world_node) if stage_for_node(g,g.world_node)>0 else 303 if g.route=="alm" else 306)
	g.mode="world";g.hub_record=room_for(g);g.flags.world_previous=g.previous_world_node
	return true

static func stage_for_node(g,node: int) -> int:
	var west={6:301,7:302,8:303,35:311};var east={6:304,24:305,25:306,36:312}
	return int((west if g.route=="alm" else east).get(node,0))

static func allowed_nodes(g) -> Array[int]:
	var result: Array[int]=[6]
	if not g.flags.get("D32_done",false):return result
	if g.route=="alm":
		result.append(7)
		if g.stage_cleared(302) and g.flags.get("M32_confirmed",false):result.append(8)
		if g.flags.get("S31_invited",false) and (not g.flags.get("chapter3_complete",false) or g.stage_cleared(311)):result.append(35)
	else:
		result.append(24)
		if g.stage_cleared(305) and g.flags.get("F32_confirmed",false):result.append(25)
		if g.flags.get("S32_invited",false) and (not g.flags.get("chapter3_complete",false) or g.stage_cleared(312)):result.append(36)
	if g.stage_cleared(303) and g.stage_cleared(306) and g.flags.get("M33_confirmed",false) and g.flags.get("F33_confirmed",false):result.append(9)
	return result

static func room_for(g) -> String:
	return str({6:"H31",7:"H32",8:"H33",24:"H34",25:"H35",35:"H36",36:"H37",9:"H10"}.get(g.world_node,"H31"))

static func transfer_supply(g,index: int) -> Dictionary:
	if g.chapter not in [3,4] or g.mode!="hub" or g.hub_record!="H10" or not g.flags.get("D33_done",false) or int(g.route_positions.alm)!=9 or int(g.route_positions.celica)!=9:
		return {"valid":false,"reason":"两队都在营站时才能当面交接"}
	var other="alm" if g.route=="celica" else "celica"
	if index<0 or index>=g.convoy[other].size() or g.convoy[g.route].size()>=40:return {"valid":false,"reason":"物品已取走，或本队行囊已满"}
	var previous=g.convoy.duplicate(true);var item=int(g.convoy[other][index])
	g.convoy[other].remove_at(index);g.convoy[g.route].append(item)
	if not g.save_game():
		g.convoy=previous;return {"valid":false,"reason":"保存失败，物品仍留在原队"}
	return {"valid":true,"item_id":item}

static func initialize(g) -> void:
	if g.stage_id<300:return
	g.flags.quest.transport_index=0;g.flags.quest.transport_stopped=false;g.flags.quest.german_decision=""

static func before_lines(g) -> String:
	var text = str(g.battle_data.before)
	if g.stage_id==303:text+="／工匠：工房里还收着被押走的旧军械。先守住码头、取回记录，战后我们会一件件认领。"
	if g.stage_id==306:text+="／术士：工房里封存着看守者征用的旧魔剑。先救人、稳住阵台，再整理兵器。"
	return text

static func lines(g,text: String,key: String="") -> void:
	var pages=[]
	var replacements={"蕾娜":"城外军官","达恩":"居民","奥托":"工匠","兰斯":"运输工","米蕾":"船医","莉莎":"艾琳","卡洛":"船长","罗恩":"舵手","希雅":"留守骑士"}
	for fragment in text.split("／"):
		var parts=fragment.split("：",true,1)
		var who=str(parts[0]);var line=str(parts[1]) if parts.size()>1 else ""
		if who.contains("或"):
			var names=who.split("或");who=names[0] if g.speaker_alive(names[0]) else names[-1]
		elif not g.speaker_alive(who):who=replacements.get(who,"旁白")
		pages.append({"speaker":who,"text":line})
	g.queue_pages(pages,key)

static func held_captive(g,u: Dictionary) -> bool:
	return g.stage_id>=300 and bool(u.get("neutral",false)) and bool(u.get("locked",false))

static func ai_action(g,u: Dictionary) -> Dictionary:
	if u.get("quest_kind","")=="transport":return {"destination":g.pos(u),"target":""}
	if u.get("quest_kind","")=="guide":
		if g.living("enemy").any(func(e):return _distance(g.pos(e),g.pos(u))<=maxi(4,g.Rules.attack_range(e).y+1)):return {"destination":g.pos(u),"target":""}
		return g._toward(u,Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]))
	return {}

static func _distance(a: Vector2i,b: Vector2i) -> int:return absi(a.x-b.x)+absi(a.y-b.y)
static func alive(g,id: String) -> bool:
	var u=g.find_unit(id);return not u.is_empty() and int(u.hp)>0
static func done(g,id: String) -> bool:return bool(g.flags.quest.objects.get(id,false))
static func boss_down(g) -> bool:
	var u=g.find_unit(str(g.battle_data.boss_id));return not u.is_empty() and (int(u.hp)<=0 or bool(u.get("surrendered",false)))

static func after_wait(g,u: Dictionary) -> void:
	if g.stage_id==304 and u.get("quest_kind","")=="patient" and not u.get("locked",false) and g.pos(u)==Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]):
		lines(g,"罗恩或舵手：这一组已经上船，先照顾伤者。我们继续接应后面的人。","F31-MID")
	if g.stage_id==305 and u.id=="salt_guide" and _distance(g.pos(u),Vector2i(14,12))<=3:
		lines(g,"莉莎或艾琳：右边的术士在等我们走盐地。沿这边的干道过去。","F32-MID")
	if u.get("quest_kind","")=="guide" and g.pos(u)==Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]):
		if not g.flags.quest.evacuated.has(u.id):g.flags.quest.evacuated.append(u.id)
		u.side="evacuated";u.hidden=true

static func extra_interactions(g,u: Dictionary) -> Array:
	var result=[]
	if g.stage_id==303 and boss_down(g) and alive(g,"german") and str(g.flags.quest.german_decision).is_empty():
		if _distance(g.pos(u),g.pos(g.find_unit("german")))==1:
			result.append({"id":"german_accept","kind":"surrender","label":"接纳格曼投降"})
			result.append({"id":"german_disarm","kind":"surrender","label":"只解除格曼武装"})
	if g.stage_id==311 and u.id=="lena":
		for enemy in g.living("enemy"):
			if not enemy.get("objective_boss",false) and int(enemy.class_id)==6 and _distance(g.pos(u),g.pos(enemy))==1:result.append({"id":"old_unit:"+str(enemy.id),"kind":"surrender","label":"劝旧部放下武器"})
	return result

static func interact(g,id: String) -> void:
	if id.begins_with("german_"):
		var u=g.find_unit("german");u.side="neutral";u.surrendered=true;u.no_counter=true
		g.flags.quest.german_decision="accepted" if id=="german_accept" else "disarmed"
		lines(g,"格曼：我带部下放下武器。工房的人不该再被带走。／胡纳普：先把押送记录交出来。接受投降，不等于免去责任。","M33-SURRENDER");return
	if id.begins_with("old_unit:"):
		var u=g.find_unit(id.substr(9));u.side="neutral";u.surrendered=true;u.no_counter=true
		lines(g,"蕾娜：这些家庭已经被准许回家。放下武器，交出押送记录。／投降兵：我愿意作证。狱卒首领还在北侧，不肯开门。",id);return
	for o in g.battle_data.objects:
		if str(o.id)!=id:continue
		g.flags.quest.objects[id]=true;g.ChapterTwo.open_object(g,o)
		match id:
			"court":lines(g,"达恩或居民：这里的人，刚才还在给我们送花。／胡纳普：先走西门。我们挡住追兵。","M31-MID")
			"station_w","station_n":lines(g,"工匠：运输站已被截住，车停下来了。沿海石堡还在收我们的工具。","M32-MID")
			"cart_release":
				g.find_unit("transport_cart").locked=false
				lines(g,"工匠：锁开了。我们留在已控制的站旁，等你们清出道路。","M32-RELEASE")
			"workers_gate":lines(g,"术士：不要强拆中央的阵。断裂以前，各地会互相调节；现在的庇护被集中送往神幕。","F33-MID")
			"regulation_record":lines(g,"艾琳：先复制调节记录。还需要观测数据，才能知道怎样安全停用。","F33-RECORD")
			"civilian_barrack":lines(g,"医者：诺娅的弟弟还活着，先把他交给照护处。" if alive(g,"noya_brother") else "医者：我们没能救下诺娅的弟弟。他的姓名会单独记在名单上。","S32-BROTHER")
		return

static func after_phase(g) -> void:
	if g.stage_id!=302 or g.phase!="player" or g.turn<=5:return
	var q: Dictionary=g.flags.quest;var cart=g.find_unit("transport_cart")
	q.transport_stopped=done(g,"station_w") or done(g,"station_n") or done(g,"cart_release")
	if q.transport_stopped:return
	var path: Array=g.battle_data.transport_path;var next=mini(int(q.transport_index)+1,path.size()-1);var p=Vector2i(path[next][0],path[next][1])
	if not g.unit_at(p).is_empty():return
	q.transport_index=next;cart.position=path[next].duplicate()
	for o in g.battle_data.objects:
		if o.get("follows_unit","")=="transport_cart":o.position=cart.position.duplicate()
	if next==path.size()-1:g._fail("工匠运输车已从北口离开")

static func check_outcome(g) -> String:
	if g.battle_outcome=="defeat":return g.battle_outcome
	for id in ["hunapu","eileen"]:
		var u=g.find_unit(id)
		if not u.is_empty() and int(u.hp)<=0:return g._fail(str(u.name_zh)+"濒死，无法继续作战")
	var q: Dictionary=g.flags.quest;var ready=false
	match g.stage_id:
		301:
			if not alive(g,"detained0") or not alive(g,"detained1"):return g._fail("被拘押居民未能全部获救")
			ready=done(g,"court") and q.evacuated.has("detained0") and q.evacuated.has("detained1")
		302:
			if not alive(g,"transport_cart"):return g._fail("工匠运输车损毁")
			ready=done(g,"station_w") and done(g,"station_n") and done(g,"cart_release")
		303:
			var german=g.find_unit("german")
			if boss_down(g) and alive(g,"german") and not german.get("offering_surrender",false):
				german.offering_surrender=true;german.no_counter=true
				lines(g,"格曼：堡主已败。我愿意带部下投降，请到工房前听我说。","M33-OFFER")
			ready=done(g,"dock_control") and done(g,"workshop") and (not alive(g,"german") or not str(q.german_decision).is_empty())
		304:
			var ids=["dock_patients0","dock_patients1"];var survivors=ids.filter(func(id):return alive(g,id))
			if survivors.is_empty():return g._fail("两组码头伤者均未能获救")
			ready=done(g,"ship_lock") and done(g,"mooring") and survivors.all(func(id):return q.evacuated.has(id))
		305:ready=q.evacuated.has("salt_guide") or (not alive(g,"salt_guide") and done(g,"guide_notes"))
		306:
			if not alive(g,"ritual_worker0") or not alive(g,"ritual_worker1"):return g._fail("维持设施的术士遇难，无法安全取得记录")
			ready=done(g,"workers_gate") and done(g,"regulation_record") and done(g,"control_array")
		311:
			if not alive(g,"family0") and not alive(g,"family1"):return g._fail("两组家属均未能获救")
			ready=done(g,"family_w") and done(g,"family_e")
		312:ready=done(g,"mage_barrack") and done(g,"civilian_barrack")
	if ready and boss_down(g):g.battle_outcome="victory"
	return g.battle_outcome

static func on_victory(g) -> void:
	g.flags["clear_"+str(g.battle_data.code)]=true
	match g.stage_id:
		303:g.flags.chapter3_recruits.german=alive(g,"german") and g.flags.quest.german_decision=="accepted"
		305:g.flags.salt_guide_survived=alive(g,"salt_guide")
		311:g.flags.S31_families={"family0":alive(g,"family0"),"family1":alive(g,"family1")}
		312:
			g.flags.chapter3_recruits.noya=alive(g,"noya");g.flags.noya_brother_survived=alive(g,"noya_brother")
	var endings={301:"居民：西门外有医者接应。码头的人还没到，我们在旧街等他们。",302:"工匠：工具和修塔的人都留下了。先到转运站清点，再去沿海石堡。",303:"工匠：投送记录找到了。把它带到工房，与另一岸的调节记录核对。",304:"舵手：活着的伤者已经上船。我们去城外旧街，与西队会合。",305:"艾琳：盐路已打开。先确认向导的路线和盐原来信。",306:"艾琳：调节记录已经复制。我们先验证，再要求胡纳普停塔。",311:"家属：请把活着的人送回去，没能回家的也请记下姓名。",312:"艾琳：先安置居民。诺娅，你要把泄露船团位置的经过说清楚。"}
	lines(g,endings.get(g.stage_id,"旁白：战场已平息。"),str(g.battle_data.code)+"-END")

static func status(g) -> Array[String]:
	var result: Array[String]=[str(g.battle_data.goal)]
	var q: Dictionary=g.flags.quest
	match g.stage_id:
		301:result.append("拘押居民撤离：%d/2。西门在西侧绿旗处；必须救出两名被拘押者并击败队长。" % (["detained0","detained1"].filter(func(id):return q.evacuated.has(id)).size()))
		302:result.append("运输车第5回合起北撤，每轮一格。控制任一运输站使车停止；两站与车锁均需确认。车逃出北口或损毁即失败。")
		303:result.append("格曼："+("已处理" if not str(q.german_decision).is_empty() or not alive(g,"german") else "堡主败北后可邻接交涉；接受投降或只解除武装"))
		304:result.append("南北两组伤者各自记录。解除两处封锁后，让存活伤者全部抵达西南己方船；全灭失败。")
		305:result.append("向导已抵达。" if q.evacuated.has("salt_guide") else "向导仍在路上。" if alive(g,"salt_guide") else "向导遇难，请取回干道旁的路线册。")
		306:result.append("两名术士必须存活。打开工房、复制记录、稳定阵台，再击败神官。")
		311:result.append("两扇牢门分别开启，至少一组家庭存活。蕾娜可以邻接劝降部分旧部。")
		312:result.append("两间营房都须打开。诺娅和弟弟的生死分别记录，战后到安置处交谈。")
	for o in g.battle_data.objects:
		if not o.get("optional",false):result.append(str(o.label)+("：已完成" if done(g,str(o.id)) else "：未完成"))
	return result
