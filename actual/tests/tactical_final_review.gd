extends "res://tests/play_base.gd"
## Independent bounded review probes. Controlled fixtures, not playthroughs.
var findings=[]
var review_checks=[]
func _initialize():call_deferred("run")
func verify(ok:bool,label:String):
	review_checks.append({"label":label,"passed":ok})
	if not ok:record_failure(label)
func settle()->void:
	for i in range(1000):
		if ui.view in ["plot","reward"]:key(KEY_Z)
		if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward"]:return
		await process_frame
func make_ui(g):
	var node=load("res://scenes/main.tscn").instantiate();node.game=g
	root.add_child(node);await process_frame;node.instant_mode=true
	node.audio.set_music_enabled(false);node.audio.set_sfx_enabled(false)
	return node
func run():
	var g=State.new();g.new_game();g.world_node=2;g.start_battle(101);g.save_path="/private/tmp/tactical-final-review.json"
	g.find_unit("daan").acted=true
	ui=await make_ui(g);ui._begin_existing_battle();await settle()
	var actor=g.find_unit("hunapu");var origin=State.pos(actor)
	cursor_to(origin);key(KEY_Z);cursor_to(Vector2i(7,14));key(KEY_Z);await settle()
	choose("cover:choose");key(KEY_X)
	findings.append({"probe":"cancel cover target picker","menu":ui.menu_context,"ui_mode":ui.ui_mode,"selected":g.selected_id,"issue":ui.menu_items.is_empty() and ui.ui_mode=="action"})
	verify(ui.menu_context=="unit_action" and g.selected_id=="hunapu","X returns cover targets to the existing unit action menu")
	choose("cover:choose")
	var cover_choices=ui.menu_actions.filter(func(action):return str(action).begins_with("cover:target:"))
	if not cover_choices.is_empty():choose(str(cover_choices[0]))
	await settle()
	verify(ui.menu_context=="cover_confirm","cover explanation opens its confirmation")
	key(KEY_X);verify(ui.menu_context=="unit_action" and not actor.acted,"X cancels cover confirmation without spending action")
	# Isolated context fixture for the same shared cancel branch; obstacle
	# destruction itself is covered by the separate real-input battlefield run.
	ui._open_menu("breakable_confirm",["确认破坏","返回"],["breakable:commit:fixture","cover:cancel"],Vector2(48,92))
	key(KEY_X);verify(ui.menu_context=="unit_action" and not actor.acted,"X cancels obstacle confirmation into action menu")
	# Recover the known empty action UI only to inspect the independent reload
	# boundary. The actor's movement, HP, action and RNG are not altered here.
	ui._unit_action_menu();var saved_before=FileAccess.get_file_as_bytes(g.save_path);choose("tactics:unit_info")
	await process_frame
	verify(FileAccess.get_file_as_bytes(g.save_path)==saved_before,"opening tactical explanation never checkpoints tentative movement")
	var state=State.read_json(g.save_path)
	var saved_actor=state.get("units",[]).filter(func(u):return u.id=="hunapu")
	findings.append({"probe":"tactical explanation checkpoint","view":ui.view,"saved_position":saved_actor[0].position if not saved_actor.is_empty() else [],"saved_acted":saved_actor[0].acted if not saved_actor.is_empty() else null,"saved_plot":state.get("flags",{}).has("active_plot")})
	var old_ui=ui
	var loaded=State.new();loaded.save_path=g.save_path
	var loaded_ok=loaded.load_game()
	ui=await make_ui(loaded);ui._resume_journey();await settle()
	var recovered=loaded.find_unit("hunapu")
	findings.append({"probe":"resume explanation in fresh UI","loaded":loaded_ok,"view":ui.view,"ui_mode":ui.ui_mode,"menu":ui.menu_context,"position":recovered.position,"acted":recovered.acted,"issue":State.pos(recovered)!=origin and not recovered.acted and ui.ui_mode=="inspect"})
	verify(loaded_ok and State.pos(recovered)==origin and not loaded.flags.has("active_plot"),"fresh UI reload resumes before the uncommitted move")
	cursor_to(origin);key(KEY_Z);cursor_to(Vector2i(7,14));key(KEY_Z);await settle()
	verify(State.pos(recovered)!=origin and ui.menu_context=="unit_action","system-menu probe begins after ordinary tentative movement")
	key(KEY_S)
	verify(State.pos(recovered)==origin and loaded.selected_id=="" and ui.ui_mode=="inspect","opening S rolls tentative movement back before offering save")
	choose("new:battle_title");await settle()
	verify(ui.view=="title","save-and-title command completes")
	var resumed=State.new();resumed.save_path=loaded.save_path
	verify(resumed.load_game() and State.pos(resumed.find_unit("hunapu"))==origin and not resumed.find_unit("hunapu").acted,"system-menu save/reload grants no extra movement")
	var z=State.new();z.new_game();z.world_node=2;z.start_battle(101)
	var a=z.find_unit("hunapu");var b=z.find_unit("otto");var foe=z.living("enemy")[0]
	a.position=[6,13];b.position=[7,13];b.acted=true;z.selected_id=a.id;z.begin_cover(b.id)
	var zero=z.Cover.split(z,b,0,{})
	var miss_preserved=a.has("cover_target")
	z.selected_id=b.id;verify(not z.begin_cover(a.id),"spent covered target cannot reciprocate with another cover action")
	var ahp=int(a.hp);var bhp=int(b.hp)
	z.apply_tactical_damage(foe,b,9,"physical")
	var first={"a_loss":ahp-int(a.hp),"b_loss":bhp-int(b.hp)}
	z.apply_tactical_damage(foe,a,9,"physical")
	findings.append({"probe":"zero damage and non-reciprocal cover","zero_empty":zero.is_empty(),"zero_preserves_cover":miss_preserved,"first":first,"total_loss":ahp+bhp-int(a.hp)-int(b.hp),"both_consumed":not a.has("cover_target") and not b.has("cover_target")})
	verify(zero.is_empty() and miss_preserved,"zero damage does not consume cover")
	verify(first.a_loss==5 and first.b_loss==4 and ahp+bhp-int(a.hp)-int(b.hp)==18,"one cover conserves both hits without a damage-transfer loop")
	verify(not a.has("cover_target") and not b.has("cover_target"),"single guard is consumed only once")
	var report={"passed":failures.is_empty(),"scope":"Independent UI/state review probes; no shared implementation edits.","checks":review_checks,"findings":findings,"driver_failures":failures}
	var out="res://reports/tactical-expansion-20261025/final-review-probes.json"
	var f=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	print(JSON.stringify(report));ui.queue_free();old_ui.queue_free();quit(0 if failures.is_empty() else 1)
