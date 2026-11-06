extends "res://tests/assessment_ch2.gd"
class ObservedState extends "res://core/game_state.gd":
	var tactical_events=[]
	func commit_strike(event:Dictionary)->void:
		tactical_events.append({"kind":"strike","turn":turn,"event":event.duplicate(true)})
		if not event.get("cover",{}).is_empty():tactical_events.append({"kind":"cover_hit","turn":turn,"event":event.duplicate(true)})
		super.commit_strike(event)
	func apply_ai_special(actor:Dictionary,action:Dictionary)->Dictionary:
		var result=super.apply_ai_special(actor,action)
		if action.get("special","")=="battlefield_release":tactical_events.append({"kind":"release","turn":turn,"result":result.duplicate(true)})
		return result
var round_name="round1"
var extras=[]
var crossed=false
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--round="):round_name=arg.trim_prefix("--round=")
	late_folder="res://reports/tactical-expansion-20261025/rescue-play/"+round_name+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
	source_checkpoint="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F22-deployment.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--retry-source="):source_checkpoint=arg.trim_prefix("--retry-source=")
	var digest=FileAccess.get_file_as_string(source_checkpoint).sha256_text()
	var working=late_folder+"working.json"
	DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
	ui=load("res://scenes/main.tscn").instantiate();ui.game=ObservedState.new();ui.game.slot_directory=late_folder;ui.game.save_path=working
	root.add_child(ui);await process_frame;ui.instant_mode=true
	if not ui.game.load_game():record_failure("F22 genuine checkpoint failed to load")
	if not abort:
		ui._resume_journey();await settle();var node=ui.game.world_node
		if ui.view=="defeat":key(KEY_Z);choose("retry");await settle();extras.append({"kind":"ordinary retry from preserved failed attempt"})
		key(KEY_S);choose("new:prepare");await settle();await go(node)
		await prepare_current()
		if not abort:
			key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:deposit");choose("camp:deposit_member:mireille");await settle()
			if not ui.menu_items.is_empty():key(KEY_X)
			extras.append({"kind":"ordinary deposit of healer focus to receive cabin shield"})
		if not abort:key(KEY_Z);choose("new:battle");await settle()
		if not abort:await battle(false)
	if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=digest:record_failure("Source modified")
	var report={"round":round_name,"passed":not abort and ui.game.battle_outcome=="victory","battles":battles,"inputs":inputs,"errors":failures,
		"source":source_checkpoint,"source_sha256":digest,"extra_actions":extras,"events":ui.game.tactical_events,"operations":operations,
		"scope":"Genuine historical party; normal UI preparation, reentry and play. No unit/attribute/RNG/outcome injection; not a full-campaign or phone test."}
	var f=FileAccess.open(late_folder+"report.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("RESCUE_PLAY ",round_name," ",ui.game.battle_outcome," turn=",ui.game.turn," ",failures)
	ui.queue_free();await process_frame;ui=null;quit(0 if report.passed else 1)
func snapshot(name:String)->void:
	if abort or not (name.ends_with("deployment") or name.ends_with("victory")):return
	var old=ui.game.save_path;ui.game.save_path=late_folder+name+".json";ui.game.save_game();ui.game.save_path=old
func write_progress()->void:pass
func act(id:String)->void:
	var unit=ui.game.find_unit(id)
	if not unit.is_empty() and not unit.get("acted",false) and int(unit.hp)>0:
		# Use optional demolition only when the rescue can be approached safely.
		if ui.game.living("enemy").is_empty() and ui.game.Battlefield.can_break(unit):
			for obstacle in ui.game.battle_data.get("breakable_obstacles",[]):
				if ui.game.flags.quest.battlefield.broken.get(str(obstacle.id),false):continue
				var at=Vector2i(obstacle.position[0],obstacle.position[1])
				for delta in ui.game.DIRECTIONS:
					var cell=at+delta
					if ui.game.can_stop(unit,cell) and ui.game.reachable(unit).costs.has(cell):
						await extra_action(unit,cell,"interact:"+str(obstacle.id),"breakable:commit:"+str(obstacle.id));return
		refresh_threats()
		var base_plan=plan(unit)
		if base_plan.get("kind","")=="wait" and ui.game.Cover.eligible(unit):
			var at:Vector2i=base_plan.cell
			for ally in ui.game.living("player"):
				if ally.id!=unit.id and ally.get("acted",false) and distance(at,State.pos(ally))==1 and risk(ally,State.pos(ally))>0:
					await extra_action(unit,at,"cover:choose","cover:target:"+str(ally.id),"cover:commit:"+str(ally.id));return
	await super.act(id)

func refresh_threats()->void:
	risk_cache.clear();threats.clear()
	for enemy in ui.game.living("enemy"):
		threats.append({"unit":enemy,"cells":ui.game.reachable(enemy).costs.keys()})

func risk(u:Dictionary,cell:Vector2i,skip:String="")->float:
	var value=super.risk(u,cell,skip)
	for intent in ui.game.flags.quest.get("battlefield",{}).get("intents",{}).values():
		for p in intent.cells:
			if cell==Vector2i(p[0],p[1]):value+=float(intent.power)+10.0
	return value

func plan(u:Dictionary)->Dictionary:
	var g=ui.game;var origin=State.pos(u);var graph=g.reachable(u)
	# Recover the existing cabin shield through its normal visit. Emptying the
	# healer's slot in preparation lets automatic delivery equip it immediately.
	if u.id=="carlo" and not g.flags.quest.objects.get("F22_visit_0",false):
		var field=distance_map(u,[Vector2i(4,18)]);var best={"kind":"wait","cell":origin,"target":"","spell":-1,"score":-1.0e9}
		for cell in graph.costs:
			if not g.can_stop(u,cell):continue
			var score=-float(field.get(cell,99999))*8.0-risk(u,cell)*5.0
			if score>best.score:best={"kind":"interact" if cell==Vector2i(4,18) else "wait","cell":cell,"target":"F22_visit_0","spell":-1,"score":score}
		return best
	# Healing is considered before the inherited terrain-retreat heuristic.
	var support=combat_plan(u)
	if support.kind=="heal":return Tactics.safe_plan(self,u,support)
	if g.turn>=8 and not g.living("enemy").any(func(e):return State.pos(e).x<=15):crossed=true
	if crossed:
		if g.living("enemy").is_empty():return super.plan(u)
		return assault_plan(u,support)
	# Establish a compact bridgehead around the two authored recovery squares.
	# This is a driver decision, not a unit position/attribute override.
	var anchors={"mireille":Vector2i(5,20),"lisa":Vector2i(5,21),"eileen":Vector2i(6,20),"carlo":Vector2i(6,19)}
	var goal:Vector2i=anchors.get(str(u.id),Vector2i(6,20));var field=distance_map(u,[goal])
	var best={"kind":"wait","cell":origin,"target":"","spell":-1,"score":-1.0e9}
	var weapons:Array=[-1]
	for spell in Items.spells(u):
		if not Items.is_support(spell) and Items.can_use(u,spell):weapons.append(spell)
	for cell in graph.costs:
		if not g.can_stop(u,cell):continue
		var danger=risk(u,cell);var score=-float(field.get(cell,99999))*4.0-danger*4.0
		if g.category(cell)==15 and int(u.hp)<int(u.max_hp):score+=15
		if danger>=float(u.hp)-2:score-=1000
		if score>best.score:best={"kind":"wait","cell":cell,"target":"","spell":-1,"score":score}
		if distance(cell,Vector2i(6,20))>5:continue
		for weapon in weapons:
			var actor=u.duplicate(true);actor.position=[cell.x,cell.y];actor.erase("weapon_index")
			if weapon>=0:actor.weapon_index=weapon
			for target in g.targets(actor):
				var d=distance(cell,State.pos(target));var reply=Rules.default_counter(target,d)
				var stats=Rules.attack_stats(actor,reply,g.terrain_avoid(State.pos(target)))
				var count=Rules.strike_sequence(actor,reply,d).count("attacker")
				var cost=Rules.magic_cost(actor)*count
				var response=Rules.attack_stats(reply,actor,g.terrain_avoid(cell))
				var counter=int(response.damage)*Rules.strike_sequence(actor,reply,d).count("defender")
				if cost+counter>=int(u.hp)-2:continue
				var expected=float(stats.damage*count)*float(stats.hit)/100.0
				var kill=expected>=float(target.hp)
				var certain_kill=int(stats.hit)==100 and int(stats.damage)>=int(target.hp)
				if str(u.id)=="eileen" and float(cost+counter)+Tactics.threat_loss(self,actor,cell,str(target.id) if certain_kill else "")>=float(u.hp)-3:continue
				var attack_score=minf(expected,float(target.hp))*3.0+(35.0 if kill else 0.0)-float(cost+counter)*2.0-risk(u,cell,str(target.id) if kill else "")*2.5-float(distance(cell,goal))
				if attack_score>best.score:best={"kind":"attack","cell":cell,"target":str(target.id),"spell":weapon,"score":attack_score}
	return best

func rank(u:Dictionary)->int:
	return int({"eileen":0,"lisa":1,"mireille":2,"carlo":3}.get(str(u.id),4))

func assault_plan(u:Dictionary,attack:Dictionary)->Dictionary:
	var g=ui.game;var origin=State.pos(u)
	var boss=g.find_unit("F22_boss")
	var preserve_leader=u.id=="eileen" and int(boss.get("hp",0))>0
	if not preserve_leader and attack.kind in ["attack","heal"] and Tactics.exposed_cost(self,u,attack)<float(u.hp)-1:return attack
	var healer=g.find_unit("mireille");var front=g.find_unit("carlo")
	if front.is_empty() or int(front.hp)<=0:front=g.find_unit("eileen")
	var goals=[]
	if preserve_leader or (int(u.hp)<int(u.max_hp)*.55 and u.id!="mireille" and int(healer.get("hp",0))>0):
		for d in g.DIRECTIONS:goals.append(State.pos(healer)+d)
	elif u.id=="mireille":
		for d in g.DIRECTIONS:goals.append(State.pos(front)+d)
	else:
		var enemy=g.living("enemy")[0];var nearest=99999
		for other in g.living("enemy"):
			var gap=distance(State.pos(front),State.pos(other))
			if gap<nearest:nearest=gap;enemy=other
		for d in g.DIRECTIONS:goals.append(State.pos(enemy)+d)
	var field=distance_map(u,goals)
	var best={"kind":"wait","cell":origin,"target":"","spell":-1,"score":-1.0e9}
	for cell in g.reachable(u).costs:
		if not g.can_stop(u,cell):continue
		var danger=risk(u,cell)
		var score=-float(field.get(cell,99999))*12.0-danger*1.0
		if preserve_leader:score=-float(field.get(cell,99999))*3.0-danger*12.0+minf(float(distance(cell,State.pos(boss))),7.0)*2.0
		if danger>=float(u.hp)-2:score-=200
		if u.id=="mireille" and danger>0:score-=80
		if int(u.hp)<int(u.max_hp) and g.category(cell)==15:score+=25
		if score>best.score:best={"kind":"wait","cell":cell,"target":"","spell":-1,"score":score}
	return best
func extra_action(unit:Dictionary,cell:Vector2i,first:String,second:String,third:String="")->void:
	cursor_to(State.pos(unit));key(KEY_Z);cursor_to(cell);key(KEY_Z);await settle()
	if abort:return
	choose(first);await settle();if abort:return
	choose(second);await settle();if abort:return
	if not third.is_empty():choose(third);await settle()
	extras.append({"turn":ui.game.turn,"actor":str(unit.id),"action":first,"cell":[cell.x,cell.y]})
