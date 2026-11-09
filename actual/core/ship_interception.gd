extends RefCounted
## F21 escort duty, deck terrain and a one-time, ordinary-growth event reward.
const PASSENGER="injured_passengers"
const DUTY="战场提示：受伤护卫只在己方左侧甲板移动并谨慎助战。低于半血会停止主动攻击并后退。护卫存活通关，本队全体正式成员额外获得20经验。两条跳板回避＋20，无需交互。"
const REWARD="战场提示：受伤护卫平安获救。本队全体正式成员额外获得20点经验，未出阵成员也可获得，满级成员除外。"

static func applies(g,u:Dictionary)->bool:
	return g.stage_id==201 and str(u.get("id",""))==PASSENGER and u.get("neutral",false) and u.get("temporary",false)

static func left_deck(g,cell:Vector2i)->bool:
	if not g.in_bounds(cell):return false
	var zones:Array=g.battle_data.get("deck_zones",[])
	# Pre-redesign journals retain their genuine28/44-column ship layouts.
	var bounds:Array=zones[0].bounds if not zones.is_empty() else [0,0,{28:10,44:18}.get(int(g.battle_data.map.width),11),int(g.battle_data.map.height)-1]
	return cell.x>=int(bounds[0]) and cell.y>=int(bounds[1]) and cell.x<=int(bounds[2]) and cell.y<=int(bounds[3])

static func plank(g,cell:Vector2i)->bool:
	if g.stage_id!=201:return false
	for connection in g.battle_data.get("boarding_connections",[]):
		var b:Array=connection.bounds
		if cell.x>=int(b[0]) and cell.y>=int(b[1]) and cell.x<=int(b[2]) and cell.y<=int(b[3]):
			# Compatible artwork must never turn an old sea/wall cell into land.
			var category=g.category(cell)
			var costs:Array=g.battle_data.terrain.movement_by_class_and_category["11"]
			return category>=0 and category<costs.size() and int(costs[category])<255
	return false

static func prepare(g,actors:Array,initial:bool=false)->void:
	for u in actors:
		if not applies(g,u):continue
		u.name_zh="受伤护卫"
		u.no_counter=false
		# Only a genuine deployment/retry checkpoint gets the new starting HP.
		# An active old save keeps its wound, action and position unchanged.
		if initial:u.hp=mini(int(u.hp),roundi(int(u.max_hp)*0.8))

static func restore(g)->void:
	if g.stage_id!=201:return
	if not g.battle_data.has("boarding_connections"):
		g.battle_data.boarding_connections=[]
		for o in g.battle_data.objects:
			if str(o.id) in ["plank_1","plank_2"]:g.battle_data.boarding_connections.append({"bounds":[int(o.position[0])-1,int(o.position[1]),int(o.position[0])+1,int(o.position[1])]})
	# Inspections used to own the plank artwork. Keep that exact artwork as
	# scenery when removing their menu entries, including compatible old maps.
	for o in g.battle_data.objects:
		if str(o.id) not in ["plank_1","plank_2"]:continue
		var position=[int(o.position[0])*16+int(o.get("sprite_offset",[0,0])[0]),int(o.position[1])*16+int(o.get("sprite_offset",[0,0])[1])]
		if not g.battle_data.art_props.any(func(p):return p.path==o.get("sprite_path","") and p.position==position):
			g.battle_data.art_props.append({"path":str(o.sprite_path),"position":position,"tag":"boarding_plank"})
	g.battle_data.objects=g.battle_data.objects.filter(func(o):return str(o.id) not in ["plank_1","plank_2"])
	for id in ["plank_1","plank_2"]:g.flags.get("quest",{}).get("objects",{}).erase(id)
	for y in range(int(g.battle_data.map.height)):
		for x in range(int(g.battle_data.map.width)):
			if plank(g,Vector2i(x,y)):g.battle_data.map.tiles[y*int(g.battle_data.map.width)+x]=208
	# Text is independent of an ongoing legacy battle's preserved geometry.
	for field in ["before","during","after","tactical_notes"]:g.battle_data[field]=g.stages[201][field]
	for o in g.battle_data.objects:
		if o.id=="F21_visit_0":o.dialogue=g.stages[201].objects[0].dialogue
	prepare(g,g.units)
	g.story_events=g.story_events.filter(func(event):return event.get("key","")!="F21-MID")
	for event in g.story_events:
		var key=str(event.get("key",""))
		match key:
			"F21-BEGIN","F21-END","F21_visit_0-VISIT":event.pages=preload("res://core/late_battle_dialogue.gd").resolve(g,event.pages,key)
			"F21-PASSENGER-DUTY":event.pages=g.dialogue_pages(DUTY)
			"F21-PASSENGER-REWARD":event.pages=g.dialogue_pages(REWARD)

static func hurt(u:Dictionary)->bool:return int(u.hp)*2<int(u.max_hp)

static func hint(u:Dictionary)->String:
	return "低于半血 · 后退休整" if hurt(u) else "左侧甲板 · 谨慎助战"

static func queue_duty(g)->void:
	if g.stage_id!=201 or g.mode!="battle" or g.battle_settled:return
	g.queue_lines(DUTY,"F21-PASSENGER-DUTY")

static func action(g,u:Dictionary,gather:bool=false)->Dictionary:
	if int(u.hp)<=0 or u.get("acted",false):return {"destination":g.pos(u),"target":""}
	if not hurt(u) and not gather:
		var shot=g.RefugeeTactics.safe_attack(g,u,0.5)
		if not shot.is_empty():return shot
	var anchor=Vector2i(6,17)
	if not hurt(u):
		var formation=g.living("player").filter(func(a):return not a.get("temporary",false) and not a.get("neutral",false) and left_deck(g,g.pos(a)))
		if not formation.is_empty():
			var center=Vector2.ZERO
			for a in formation:center+=Vector2(g.pos(a))
			anchor=Vector2i((center/formation.size()).round())
	var graph=g.reachable(u);var best=g.pos(u);var score=INF
	for cell in graph.costs:
		if not left_deck(g,cell) or not g.can_stop(u,cell):continue
		var risk=g.RefugeeTactics.evaluate(g,u,cell)
		var distance=absi(cell.x-anchor.x)+absi(cell.y-anchor.y)
		var value=float(risk.incoming)*100+distance*3+float(graph.costs[cell])*.1
		if value<score:score=value;best=cell
	return {"destination":best,"target":"","reason":"passenger_retreat" if hurt(u) else "passenger_follow"}

static func award_survival(g)->void:
	if g.stage_id!=201 or g.flags.get("F21_passenger_survival_reward",false) or g.stage_cleared(201):return
	var passenger=g.find_unit(PASSENGER)
	if passenger.is_empty() or int(passenger.hp)<=0:return
	for id in g.party:
		var member:Dictionary=g.roster.get(str(id),{})
		if member.is_empty() or member.get("dead",false) or int(member.level)>=20 or member.get("no_experience",false):continue
		if g.Casualties.owner({"parties":g.parties},str(id)).is_empty():continue
		var injured=int(member.hp)<=0
		var receipt=g.CampaignExperience.award(g,member,20)
		if injured:member.hp=0
		receipt.passenger_survival_bonus=20;g.victory_rewards.append(receipt)
		var deployed=g.find_unit(str(id))
		if not deployed.is_empty():
			for field in ["level","exp","max_hp","hp","strength","skill","speed","luck","defence","magic_level","magic_flags"]:
				if member.has(field):deployed[field]=member[field]
	g.flags.F21_passenger_survival_reward=true
	g.queue_lines(REWARD,"F21-PASSENGER-REWARD")
