extends "res://tests/tactical_review_play.gd"
## Two rounds of normal keyboard play on current maps; historic saves are read only.
var polish_round:=1
var polish_label:=""
var polish_codes: PackedStringArray=[]
var shot_records: Array=[]
var stage_source:=""
var allow_capture:=false
var captured_levels: Dictionary={}
var path_cache: Dictionary={}
var risk_cache: Dictionary={}

func distance_map(unit: Dictionary,goals: Array) -> Dictionary:
	var stamp=str(ui.game.stage_id)+":"+str(unit.class_id)+":"+str(unit.get("item_id",0))+":"+JSON.stringify(goals)+":"+JSON.stringify(ui.game.flags.quest.objects)
	if not path_cache.has(stamp):path_cache[stamp]=super.distance_map(unit,goals)
	return path_cache[stamp]

func refresh_threats() -> void:
	risk_cache.clear();super.refresh_threats()

func risk(unit: Dictionary,cell: Vector2i,skip: String="") -> float:
	var stamp=str(unit.id)+":"+str(unit.hp)+":"+str(unit.get("weapon_index",-1))+":"+str(cell)+":"+skip
	if not risk_cache.has(stamp):risk_cache[stamp]=super.risk(unit,cell,skip)
	var danger=float(risk_cache[stamp])
	if str(unit.id)==ui.game.leader_id():danger*=2.4
	if danger>=float(unit.hp)-2:danger+=250.0
	return danger

func plan(unit: Dictionary) -> Dictionary:
	if ui.game.stage_id==101 and ui.game.turn>=3 and not ui.game.flags.quest.objects.get("M11_visit_0",false):
		for cell in ui.game.reachable(unit).costs:
			if not ui.game.can_stop(unit,cell) or risk(unit,cell)>float(unit.hp)*.45:continue
			var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
			for object in ui.game.interactions_for(candidate):
				if object.id=="M11_visit_0":return {"kind":"interact","cell":cell,"score":300.0,"target":str(object.id),"spell":-1}
	# The automated player preserves the protagonist and uses real recovery
	# terrain when critically hurt; this changes only the input planner.
	if not ui.game.living("enemy").is_empty() and int(unit.hp)*100<int(unit.max_hp)*40:
		var goals=[];var map=ui.game.battle_data.map
		for y in range(map.height):
			for x in range(map.width):
				var point=Vector2i(x,y)
				if ui.game.category(point)==15:goals.append(point)
		if not goals.is_empty():
			var field=distance_map(unit,goals);var before=int(field.get(State.pos(unit),99999))
			var best={"kind":"wait","cell":State.pos(unit),"score":-99999.0,"target":"","spell":-1}
			for cell in ui.game.reachable(unit).costs:
				if not ui.game.can_stop(unit,cell):continue
				var score=18.0*(before-int(field.get(cell,99999)))-risk(unit,cell)*1.5
				if goals.has(cell):score+=100.0
				if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
			return best
	return super.plan(unit)

func _hub_route(target: Vector2i) -> Array:
	var hub=ui.hub_controller;var start=ui.game.hub_position;var blocked={}
	for object in hub.objects:blocked[Vector2i(object.position[0],object.position[1])]=true
	for decor in hub.scenery:
		if not decor.get("blocking",true):continue
		for y in range(decor.rect.position.y,decor.rect.end.y):
			for x in range(decor.rect.position.x,decor.rect.end.x):blocked[Vector2i(x,y)]=true
	var queue=[start];var previous={start:start}
	while not queue.is_empty() and not previous.has(target):
		var point=queue.pop_front()
		for direction in ui.game.DIRECTIONS:
			var next=point+direction
			if next.x<1 or next.x>12 or next.y<1 or next.y>7 or previous.has(next) or blocked.has(next) or not hub.east_walkable(next):continue
			previous[next]=point;queue.append(next)
	if not previous.has(target):return []
	var path=[target];var point=target
	while point!=start:point=previous[point];path.push_front(point)
	return path

func _initialize() -> void:
	if DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--round="):polish_round=int(argument.get_slice("=",1))
		if argument.begins_with("--codes="):polish_codes=argument.get_slice("=",1).split(",")
		if argument.begins_with("--label="):polish_label=argument.get_slice("=",1)
	if not OS.get_environment("REVENGE_POLISH_ROUND").is_empty():polish_round=int(OS.get_environment("REVENGE_POLISH_ROUND"))
	if not OS.get_environment("REVENGE_POLISH_CODES").is_empty():polish_codes=OS.get_environment("REVENGE_POLISH_CODES").split(",")
	if not OS.get_environment("REVENGE_POLISH_LABEL").is_empty():polish_label=OS.get_environment("REVENGE_POLISH_LABEL")
	if polish_label.is_empty():polish_label="round"+str(polish_round)
	review_out="res://reports/playtest-0.5.0/"+polish_label+"/"
	if polish_codes.is_empty():polish_codes=["M11","S12","M13","F21","F24"] if polish_round==1 else ["M11","S11","M14","F25","F26","S22"]
	call_deferred("run")

func shot(name: String) -> void:
	if not allow_capture:return
	while ui.view=="battle" and ui.phase_time>0:await process_frame
	ui.queue_redraw()
	for frame in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path=review_out+name+".png"
	viewport.get_texture().get_image().save_png(path)
	shot_records.append({"path":path,"source":stage_source,"stage":ui.game.battle_data.code,"view":ui.view,"turn":ui.game.turn,"cursor":[ui.game.cursor.x,ui.game.cursor.y],"fixture":false,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true),"card":ui.battle_card_audit.duplicate(true)})
	if not ui.layout_errors.is_empty():record_failure("Text safety: "+name+" "+str(ui.layout_errors))
	print("POLISH_SHOT ",polish_label," ",name)

func settle() -> void:
	for frame in range(15000):
		if abort:return
		if ui.view in ["plot","reward"]:
			if ui.view=="reward" and ui.reward.get("leveled",false):
				var key_=str(ui.game.stage_id)+":"+str(ui.reward.unit)+":"+str(ui.reward.get("level_after",0))
				if not captured_levels.has(key_):
					captured_levels[key_]=true
					await shot(str(ui.game.battle_data.code)+"-levelup-"+str(ui.reward.unit)+"-"+str(ui.reward.get("level_after",0)))
			key(KEY_Z)
		elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
		if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
		await process_frame
	record_failure("Input failed to release: "+ui.view)

func snapshot(name: String) -> void:
	var path=review_out+name+".json";var old=ui.game.save_path
	ui.game.save_path=path;ui.game.save_game();ui.game.save_path=old
	checkpoints.append({"name":name,"save":path,"view":ui.view,"stage":ui.game.stage_id,"turn":ui.game.turn})

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
	allow_capture=DisplayServer.get_name()!="headless"
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	var capture_density=maxi(1,int(OS.get_environment("REVENGE_CAPTURE_DENSITY")))
	if capture_density>1:
		viewport.size=Vector2i(426,240)*capture_density
		viewport.size_2d_override=Vector2i(426,240)
		viewport.size_2d_override_stretch=true
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	for code in polish_codes:
		abort=false;var before_failures=failures.size();var before_keys=inputs
		path_cache.clear();risk_cache.clear()
		if code=="M11" and polish_round==2:
			stage_source="Fresh new game through title, prologue, D11 and normal world travel"
			ui.game.save_path=review_out+"working.json";ui.view="title";ui.title_menu=false;ui.title_selected=0;ui.busy=false;ui._clear_menu()
			key(KEY_Z);key(KEY_Z);await settle();await hub_action("prologue");await hub_action("grave")
			walk_to(Vector2i(6,7));key(KEY_DOWN);choose("new:world");await settle();await go(2)
			key(KEY_Z);choose("new:battle");await settle()
		else:
			stage_source=("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
			ui.game.save_path=stage_source;var loaded=ui.game.load_game();ui.game.save_path=review_out+"working.json"
			if not loaded:record_failure("Historical source fails to load: "+code);continue
			ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.held_direction=Vector2i.ZERO;ui.notice_time=0;ui.phase_time=0
			var node=ui.game.world_node
			key(KEY_S);choose("new:prepare");await settle();await go(node)
			if code=="M15":await equip_from_convoy("hunapu",11);await equip_from_convoy("otto",2)
			key(KEY_Z);choose("new:battle");await settle()
		await snapshot(code+"-entry");await shot(code+"-entry")
		if code=="M11":
			key(KEY_S);choose("new:focus_exit");await shot(code+"-visible-exit")
			key(KEY_S);choose("new:focus_boss");key(KEY_TAB);await shot(code+"-captain-portrait");key(KEY_X)
			var archer=ui.game.units.filter(func(u):return u.side=="enemy" and int(u.class_id)==12)[0]
			cursor_to(State.pos(archer));key(KEY_TAB);await shot(code+"-archer-portrait");key(KEY_X)
		var initial=ui.game.roster.duplicate(true);var turn_records=[];var action_records=[];var opening_attack=0
		for step in range(55):
			if abort or not ui.game.battle_outcome.is_empty():break
			var turn_=ui.game.turn;var hp_before={};var attacks=0
			for actor in ui.game.units:hp_before[actor.id]=int(actor.hp)
			var members=ui.game.party.duplicate()
			if ui.game.chapter==2:members.sort_custom(func(a,b):return rank(ui.game.roster[a])<rank(ui.game.roster[b]))
			for id in members:
				if abort or ui.game.turn!=turn_ or not ui.game.battle_outcome.is_empty():break
				var actor=ui.game.find_unit(str(id))
				if actor.is_empty() or int(actor.hp)<=0 or actor.acted:continue
				var before_ops=operations.size();await act(str(id))
				for op in operations.slice(before_ops):
					if op.has("action"):
						action_records.append({"turn":turn_,"unit":id,"kind":op.action.kind,"target":op.action.get("target","")})
						if op.action.kind=="attack":attacks+=1
			if not abort and ui.game.battle_outcome.is_empty() and ui.game.turn==turn_:key(KEY_S);choose("end_turn");await settle()
			var damaged=false
			for actor in ui.game.units:
				if hp_before.has(actor.id) and int(actor.hp)<hp_before[actor.id]:damaged=true
			if opening_attack==0 and (attacks>0 or damaged):opening_attack=turn_
			var escorts=[]
			for npc in ui.game.units:
				if npc.has("quest_kind"):escorts.append({"id":npc.id,"position":npc.position.duplicate(),"move":npc.move,"locked":npc.get("locked",false),"side":npc.side})
			turn_records.append({"turn":turn_,"enemies":ui.game.living("enemy").size(),"player_attacks":attacks,"hp_decreased":damaged,"outcome":ui.game.battle_outcome,"escorts":escorts,"objects":ui.game.flags.quest.objects.duplicate(true)})
			if step==1:await snapshot(code+"-field");await shot(code+"-field")
			print("POLISH_PLAY ",polish_label," ",code," turn ",ui.game.turn," enemies ",ui.game.living("enemy").size()," ",ui.game.battle_outcome)
		var upgrades=[]
		for id in ui.game.party:
			if initial.has(id) and int(ui.game.roster[id].level)>int(initial[id].level):upgrades.append({"id":id,"before":initial[id].level,"after":ui.game.roster[id].level})
		var record={"code":code,"source":stage_source,"outcome":ui.game.battle_outcome,"final_turn":ui.game.turn,"first_combat_turn":opening_attack,"turns":turn_records,"actions":action_records,"levelups":upgrades,"objects":ui.game.flags.quest.objects.duplicate(true),"key_inputs":inputs-before_keys,"failures":failures.slice(before_failures),"scope":"Normal keyboard return to preparation, world re-entry, movement, attacks and objectives. No HP/stat/position/RNG edits and no forced victory."}
		if code=="M11" and record.outcome=="victory" and upgrades.is_empty():record_failure("M11 completed without any level-up")
		await snapshot(code+"-"+("victory" if record.outcome=="victory" else "stopped"));await shot(code+"-result")
		review_battles.append(record);write_review();ui.busy=false;ui.batch_running=false;ui._clear_menu()
	write_review();ui.set_process(false);viewport.remove_child(ui);ui.hub_controller.dispose();ui.hub_controller=null;ui.free();ui=null;viewport.queue_free();await process_frame
	quit(0 if review_battles.all(func(b):return b.outcome=="victory") and failures.is_empty() else 1)

func write_review() -> void:
	var report={"round":polish_round,"passed":not review_battles.is_empty() and review_battles.all(func(b):return b.outcome=="victory") and failures.is_empty(),"battles":review_battles,"key_inputs":inputs,"failures":failures,"shots":shot_records,"background_guard":OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1","visible_windows":false,"captures":allow_capture,"stat_edits":false,"forced_victories":false,"checkpoints":checkpoints}
	var f=FileAccess.open(review_out+"play-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
