extends "res://tests/play_base.gd"
## Fresh new-campaign input playthrough. No stat edits, direct deaths or victory flags.
var checkpoints: Array=[]
var captures: Array=[]
var viewport
var natural_capture := false

func _initialize() -> void:call_deferred("run")
func settle() -> void:
	for i in range(10000):
		if abort:return
		if ui.view in ["plot","reward"]:key(KEY_Z)
		elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
		if not ui.busy and not ui.batch_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
		await process_frame
	record_failure("Input did not release: "+ui.view)

func plan(unit: Dictionary) -> Dictionary:
	var best=super.plan(unit);var graph=ui.game.reachable(unit)
	var important="M15_boss" if ui.game.stage_id==105 else ""
	if ui.game.stage_id==102:
		for enemy in ui.game.living("enemy"):
			if enemy.get("burner",false):important=str(enemy.id)
	var focus=ui.game.find_unit(important)
	if ui.game.stage_id in [101,111,112]:
		var distance_=99999
		for e in ui.game.living("enemy"):
			for npc in ui.game.living("player"):
				if npc.get("quest_kind","") not in ["escort","medicine"]:continue
				var d=distance(State.pos(e),State.pos(npc))
				if d<distance_:distance_=d;focus=e;important=str(e.id)
	for cell in graph.costs:
		if not ui.game.can_stop(unit,cell):continue
		var candidate: Dictionary=unit.duplicate(true);candidate.position=[cell.x,cell.y]
		var options=ui.game.interactions_for(candidate)
		for obj in options:
			var score=250.0-risk(candidate,cell)
			if score>best.score:best={"kind":"interact","cell":cell,"score":score,"target":str(obj.id),"spell":-1}
		if focus.is_empty() or int(focus.hp)<=0:continue
		# Race objectives need a plan, rather than an extermination-only helper.
		var before=distance(State.pos(unit),State.pos(focus));var after=distance(cell,State.pos(focus))
		var walking=12.0*(before-after)-risk(candidate,cell)
		if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
		var weapons: Array=[-1]
		for spell in Items.spells(unit):
			if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
		for weapon in weapons:
			candidate.erase("weapon_index")
			if weapon>=0:candidate.weapon_index=weapon
			if not ui.game.targets(candidate).has(focus):continue
			var stats=Rules.attack_stats(candidate,focus,ui.game.terrain_avoid(State.pos(focus)))
			var score=120.0+float(stats.damage)*2-risk(candidate,cell)
			if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":important,"spell":weapon}
	return best

func act(id: String) -> void:
	var unit: Dictionary=ui.game.find_unit(id)
	if unit.is_empty() or int(unit.hp)<=0 or bool(unit.acted) or abort:return
	refresh_threats();var action=plan(unit)
	if action.kind!="interact":await super.act(id);return
	var before={"unit":id,"turn":ui.game.turn,"kind":"objective interaction","target":action.target,"origin":unit.position.duplicate()}
	cursor_to(State.pos(unit));key(KEY_Z);cursor_to(action.cell);key(KEY_Z);await settle()
	if not abort:choose("interact:"+str(action.target));await settle()
	before.after=unit.position.duplicate();operations.append(before)

func walk_to(at: Vector2i) -> void:
	var start=ui.game.hub_position;var blocked={}
	for o in ui.hub_controller.objects:blocked[Vector2i(o.position[0],o.position[1])]=true
	for d in ui.hub_controller.scenery:
		for y in range(d.rect.position.y,d.rect.end.y):
			for x in range(d.rect.position.x,d.rect.end.x):blocked[Vector2i(x,y)]=true
	var q: Array[Vector2i]=[start];var seen={start:start}
	while not q.is_empty() and not seen.has(at):
		var p=q.pop_front()
		for d in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			var n=p+d
			if n.x<1 or n.x>12 or n.y<1 or n.y>7 or blocked.has(n) or seen.has(n):continue
			seen[n]=p;q.append(n)
	if not seen.has(at):record_failure("Hub destination blocked: "+str(at));return
	var path: Array=[];var p=at
	while p!=start:path.push_front(p);p=seen[p]
	for n in path:
		var d=n-ui.game.hub_position;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP)
		if ui.game.hub_position!=n:record_failure("Hub input disagrees with room walk path");return

func hub_action(action: String) -> void:
	var object={}
	for o in ui.hub_controller.objects:
		if str(o.action)==action:object=o;break
	if object.is_empty():
		if action in ui.game.characters and bool(ui.game.roster.get(action,{}).get("dead",false)):
			operations.append({"kind":"dead NPC omitted","id":action});return
		record_failure("Hub object missing: "+action);return
	var at=Vector2i(object.position[0],object.position[1]);var destination=at+Vector2i.DOWN
	walk_to(destination)
	if abort:return
	key(KEY_UP);key(KEY_Z);await settle()
	operations.append({"kind":"facing hub confirmation","room":ui.game.hub_record,"action":action})

func leave_hub() -> void:
	var old_room=ui.game.hub_record
	walk_to(Vector2i(6,7));key(KEY_DOWN)
	if ui.game.hub_record!=old_room and ui.menu_items.is_empty():return
	choose("new:world");await settle()
func travel(node: int) -> void:
	key(KEY_Z);choose("travel:"+str(node));await settle()
	if ui.game.world_node!=node:record_failure("World route did not reach "+str(node))
	operations.append({"kind":"world route","node":node,"previous":ui.game.previous_world_node})
func enter_hub() -> void:key(KEY_Z);choose("new:hub")

func snapshot(name: String) -> void:
	var file="res://reports/campaign/natural-"+name+"-save.json"
	var old=ui.game.save_path;ui.game.save_path=file;ui.game.save_game();ui.game.save_path=old
	checkpoints.append({"name":name,"save":file,"view":ui.view,"stage":ui.game.stage_id,"turn":ui.game.turn})
	if natural_capture:
		ui.queue_redraw()
		for i in range(3):await process_frame
		await RenderingServer.frame_post_draw
		var path="res://reports/campaign/play-"+name+".png"
		viewport.get_texture().get_image().save_png(path);captures.append({"path":path,"view":ui.view,"layout_errors":ui.layout_errors.duplicate()})

func battle(enter_encounter: bool=true) -> void:
	if enter_encounter:key(KEY_Z);choose("new:battle");await settle()
	var stage=ui.game.stage_id;var record={"stage":stage,"code":ui.game.battle_data.code,"initial_party":ui.game.party.duplicate(),"turns":[],"initial_players":ui.game.living("player").duplicate(true),"initial_enemies":ui.game.living("enemy").duplicate(true)}
	await snapshot(str(ui.game.battle_data.code)+"-deployment")
	for pass_ in range(60):
		if abort or ui.game.battle_outcome!="":break
		var round_=ui.game.turn
		var members=ui.game.party.duplicate()
		for id in members:
			if ui.game.turn!=round_ or ui.game.battle_outcome!="" or abort:break
			await act(str(id))
		if not abort and ui.game.battle_outcome.is_empty() and ui.game.phase=="player" and ui.game.turn==round_:
			key(KEY_S);choose("end_turn");await settle()
		record.turns.append({"turn":ui.game.turn,"enemies":ui.game.living("enemy").size(),"players":ui.game.living("player").size(),"quest":ui.game.flags.quest.duplicate(true)})
		print("PLAY ",record.code," turn ",ui.game.turn," E ",ui.game.living("enemy").size()," P ",ui.game.living("player").size()," ",ui.game.battle_outcome)
		if natural_capture and pass_==2:await snapshot(str(record.code)+"-field")
	record.outcome=ui.game.battle_outcome;record.final_turn=ui.game.turn;record.final_players=ui.game.living("player").duplicate(true)
	record.final_roster=ui.game.roster.duplicate(true);battles.append(record)
	if ui.game.battle_outcome!="victory":record_failure("Natural battle failed: "+str(record.code)+" "+str(ui.game.flags.quest));return
	await snapshot(str(record.code)+"-victory")
	key(KEY_Z);choose("continue_world");await settle()

func run() -> void:
	natural_capture=OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1" and not DisplayServer.get_name()=="headless"
	if natural_capture:
		viewport=SubViewport.new();viewport.size=Vector2i(256,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate()
	if natural_capture:viewport.add_child(ui)
	else:root.add_child(ui)
	await process_frame;ui.game.save_path="res://reports/campaign/round3-progress.json";ui.instant_mode=true
	if OS.get_cmdline_user_args().has("--resume-m14"):
		var previous=State.read_json("res://reports/campaign/round3-attempt6.json")
		battles=previous.battles.filter(func(b):return b.outcome=="victory");operations=previous.operations;checkpoints=previous.checkpoints;inputs=int(previous.inputs)
		ui.game.save_path="res://reports/campaign/natural-M14-deployment-save.json"
		if not ui.game.load_game():record_failure("Cannot resume real M14 opening")
		ui.game.save_path="res://reports/campaign/round3-progress.json";ui.view=ui.game.mode;ui._focus_battle(ui.game.cursor,true);await battle(false)
		if not abort:await travel(6);await battle()
		if not abort:
			enter_hub();await hub_action("treat");await snapshot("tower-altar");await hub_action("ceremony");await snapshot("chapter-end")
		finish_report();return
	if OS.get_cmdline_user_args().has("--resume-s12"):
		var previous=State.read_json("res://reports/campaign/round3-attempt4.json")
		battles=previous.battles.filter(func(b):return b.outcome=="victory");operations=previous.operations;checkpoints=previous.checkpoints;inputs=int(previous.inputs)
		ui.game.save_path="res://reports/campaign/natural-S12-deployment-save.json"
		if not ui.game.load_game():record_failure("Cannot resume actual S12 opening save")
		ui.game.save_path="res://reports/campaign/round3-progress.json";ui.view=ui.game.mode
		if ui.view=="hub":ui.hub_controller.resume();await leave_hub();await battle()
		else:ui._focus_battle(ui.game.cursor,true);await battle(false)
	else:
		key(KEY_Z);key(KEY_Z);await settle();await snapshot("prologue")
		await hub_action("prologue");await snapshot("snow-village")
		await hub_action("grave");await hub_action("otto");await leave_hub();await snapshot("world-start")
		await travel(2);await battle()
		if not abort:
			enter_hub();await hub_action("invite");await leave_hub();await travel(31);await battle()
		if not abort:
			enter_hub();await hub_action("beck")
			if ui.menu_actions.has("hub:recruit_beck"):choose("hub:recruit_beck");await settle()
			await leave_hub();await travel(2);await travel(32);await battle()
	if not abort:
		enter_hub();await hub_action("staff");await hub_action("hervi")
		if ui.menu_actions.has("hub:recruit_hervi"):choose("hub:recruit_hervi");await settle()
		await leave_hub();await travel(2);await travel(3);await battle()
	if not abort:
		enter_hub();await hub_action("grain");await hub_action("fula")
		if ui.menu_actions.has("hub:recruit_fula"):choose("hub:recruit_fula");await settle()
		await leave_hub();await travel(4);await battle()
	if not abort:
		enter_hub();await hub_action("orders");await hub_action("lena")
		if ui.menu_actions.has("hub:recruit_lena"):choose("hub:recruit_lena");await settle()
		await hub_action("church");await hub_action("cooperate");await leave_hub();await leave_hub();await travel(5);await battle()
	if not abort:await travel(6);await battle()
	if not abort:
		enter_hub();await hub_action("treat");await snapshot("tower-altar");await hub_action("ceremony");await snapshot("chapter-end")
		if not ui.game.flags.get("chapter1_complete",false):record_failure("Ceremony did not complete chapter")
	finish_report()

func finish_report() -> void:
	var report={"round":3,"scope":"Prologue and chapter1 main/side battles through actual key inputs, preserving real progression across checkpoint resumes","passed":not abort,"failures":failures,"inputs":inputs,"battles":battles,"operations":operations,"checkpoints":checkpoints,"captures":captures,"initial_preparation":[],"stat_edits":false,"forced_victories":false,"native_graphics":natural_capture,"resumed_actual_progress":OS.get_cmdline_user_args().has("--resume-s12") or OS.get_cmdline_user_args().has("--resume-m14")}
	var f=FileAccess.open("res://reports/campaign/round3.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("ROUND3 ",JSON.stringify({"passed":not abort,"battles":battles.size(),"inputs":inputs,"failures":failures}))
	ui.queue_free();await process_frame;ui=null
	if viewport!=null:viewport.queue_free();await process_frame;viewport=null
	quit(0 if not abort else 1)
