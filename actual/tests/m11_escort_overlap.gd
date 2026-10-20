extends SceneTree
## Regression for danger-shortened escort routes and existing stacked saves.
const State=preload("res://core/game_state.gd")
const IDS=["M11_refugees0","M11_refugees1"]
var checks: Array=[]
var errors: Array=[]
var details: Dictionary={}

func _initialize():call_deferred("run")
func check(ok: bool,label: String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh(id: int=101):
	var g=State.new();g.new_game();g.world_node=int(g.stages[id].node)
	g.save_path="/private/tmp/m11-overlap-regression.json"
	check(g.start_battle(id),"start "+str(id));g.story_events.clear();return g
func active(g):
	return g.units.filter(func(u):return int(u.hp)>0 and u.side!="evacuated" and not u.get("hidden",false))
func unique(g):
	var cells={}
	for u in active(g):
		if cells.has(State.pos(u)):return false
		cells[State.pos(u)]=true
	return true
func corridor():
	var g=fresh();var a=g.find_unit(IDS[0]);var b=g.find_unit(IDS[1]);var e=g.find_unit("M11_e1")
	for enemy in g.living("enemy"):enemy.hp=0
	e.hp=20;e.position=[10,7]
	a.position=[10,13];a.hp=14;b.position=[10,12]
	return g
func no_position(u: Dictionary):
	var data=u.duplicate(true);data.erase("position");return data
func run():
	var g=corridor();var a=g.find_unit(IDS[0]);var b=g.find_unit(IDS[1])
	var before=g.units.duplicate(true);var action=g.ai_action(a)
	check(action.destination==State.pos(a) and g.can_stop(a,action.destination),"danger after occupied ally keeps the last legal landing cell")
	check(g.units==before,"route selection never mutates real actors")
	details.danger_route={"origin":a.position,"occupied":b.position,"destination":[action.destination.x,action.destination.y]}
	g.find_unit("M11_e1").hp=0
	action=g.ai_action(a)
	check(action.destination!=State.pos(a) and action.destination!=State.pos(b) and g.can_stop(a,action.destination),"clear route still crosses allies and lands on an empty cell")
	check(g.path_to(a,action.destination).has(State.pos(b)),"friendly traversal remains allowed")
	# The chapter-two branch previously copied the same truncation bug.
	g=corridor();g.stage_id=202;g.find_unit(IDS[0]).quest_kind="prisoner"
	action=g.ai_action(g.find_unit(IDS[0]))
	check(g.can_stop(g.find_unit(IDS[0]),action.destination),"prisoner route uses the same safe landing check")
	g=fresh();a=g.find_unit(IDS[0]);b=g.find_unit(IDS[1]);b.position=a.position.duplicate()
	check(not g.can_stop(a,State.pos(a)) and not g.can_stop(b,State.pos(b)),"all occupants are checked even when unit_at returns self")
	check(g.save_game(),"write independent stacked checkpoint fixture")
	var restored=State.new();restored.save_path=g.save_path
	check(restored.load_game() and unique(restored),"load_game repairs a persisted stacked checkpoint")
	check(JSON.parse_string(JSON.stringify(restored.flags))==JSON.parse_string(JSON.stringify(g.flags)) and restored.turn==g.turn and restored.phase==g.phase and restored.rng_state==g.rng_state,"persisted repair preserves quest, turn, phase and RNG")
	var restored_units=JSON.parse_string(JSON.stringify(restored.units))
	check(restored.save_game(),"persist repaired stacked checkpoint")
	check(restored.load_game() and JSON.parse_string(JSON.stringify(restored.units))==restored_units,"repaired stacked checkpoint reloads without further displacement")
	var stacked=g.units.duplicate(true);g._repair_overlapped_escorts()
	check(unique(g) and a.position==stacked[-2].position,"repair preserves earlier unit and separates the later escort")
	for i in range(g.units.size()):check(no_position(g.units[i])==no_position(stacked[i]),"repair preserves actor identity, HP and action state "+str(g.units[i].id))
	var repaired=g.units.duplicate(true);g._repair_overlapped_escorts()
	check(g.units==repaired,"repair is idempotent")
	g=fresh();before=g.units.duplicate(true);g._repair_overlapped_escorts()
	check(g.units==before,"ordinary deployment is untouched")
	g=fresh();g.find_unit(IDS[0]).hp=0
	check(g.check_outcome()=="defeat","either escort dying still causes defeat")
	g=fresh();g.find_unit(str(g.battle_data.boss_id)).hp=0
	for id in IDS:
		var u=g.find_unit(id);u.position=g.battle_data.exit.duplicate();g.mark_wait(id)
		check(u.side=="evacuated" and u.hidden and int(u.hp)>0,"arrival hides only a living evacuated escort "+id)
	check(g.check_outcome()=="victory" and g.flags.quest.evacuated.size()==2,"two arrivals plus captain defeat still win")
	# Read the user's checkpoint only. All writes target an independent temp file.
	var checkpoint=OS.get_environment("M11_OVERLAP_CHECKPOINT")
	if not checkpoint.is_empty():
		var original=FileAccess.get_file_as_string(checkpoint);var saved=JSON.parse_string(original)
		var snapshot=FileAccess.open("/private/tmp/m11-overlap-user-snapshot.json",FileAccess.WRITE);snapshot.store_string(original);snapshot.close()
		g=State.new();g.save_path="/private/tmp/m11-overlap-user-snapshot.json"
		check(g.load_game(),"existing gameplay checkpoint loads")
		check(unique(g),"existing checkpoint has distinct living positions after load")
		for i in range(g.units.size()):check(no_position(g.units[i])==no_position(saved.units[i]),"checkpoint recovery preserves actor fields "+str(g.units[i].id))
		for key in ["turn","phase","rng_state","kills","battle_outcome","flags","roster","cleared_stages"]:check(g.get(key)==saved[key],"checkpoint recovery preserves "+key)
		details.checkpoint=[]
		for id in IDS:
			var u=g.find_unit(id);var old=saved.units.filter(func(actor):return actor.id==id)[0]
			details.checkpoint.append({"id":id,"before":old.position,"after":u.position,"hp":u.hp})
		var recovered=g.units.duplicate(true);g.save_path="/private/tmp/m11-overlap-regression.json"
		check(g.save_game(),"recovered checkpoint saves to independent file")
		var loaded=State.new();loaded.save_path=g.save_path
		check(loaded.load_game() and JSON.parse_string(JSON.stringify(loaded.units))==JSON.parse_string(JSON.stringify(recovered)),"recovered checkpoint reloads without further movement")
		check(FileAccess.get_file_as_string("/private/tmp/m11-overlap-user-snapshot.json")==original,"checkpoint snapshot bytes remain untouched")
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.game=corridor();ui.view="battle";ui.ui_mode="inspect";ui.instant_mode=true
	ui.busy=true;ui.batch_running=true
	await ui._run_ai_unit(ui.game.find_unit(IDS[0]))
	check(unique(ui.game) and ui.game.find_unit(IDS[0]).acted,"real automatic controller waits without stacking")
	# Exercise both automatic escorts repeatedly on the real map, with the
	# fixed exit guard only. This validates movement, waiting and evacuation.
	ui.game=fresh();ui.game.flags.quest.reinforced=true
	for e in ui.game.living("enemy"):
		if not e.get("objective_boss",false):e.hp=0
	for turn_index in range(6):
		for id in IDS:
			var u=ui.game.find_unit(id)
			if u.side=="evacuated":continue
			u.acted=false;await ui._run_ai_unit(u)
			check(unique(ui.game),"automatic escort landing remains unique "+str(turn_index)+" "+id)
	ui.queue_free();await process_frame
	var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"details":details,"scope":"Danger-shortened route, allied traversal, chapter-two branch, read-only real checkpoint migration, actual automatic controller, death and victory"}
	var f=FileAccess.open("res://reports/m11-overlap-20261020/regression.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("M11_OVERLAP ",JSON.stringify(report));quit(0 if errors.is_empty() else 1)
