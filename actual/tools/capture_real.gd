extends "res://tests/round3.gd"
## Real engine screenshots from actual input-play saves, plus a legal live exchange.
var real_shots: Array=[]
var duel_seen := false
func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func load_checkpoint(name: String) -> void:
	ui.game.save_path="res://reports/campaign/natural-"+name+"-save.json"
	if not ui.game.load_game():record_failure("Screenshot checkpoint missing: "+name);return
	ui.game.save_path="res://reports/campaign/screenshot-working.json";ui.view=ui.game.mode
	ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu();ui.phase_time=0;ui.notice_time=0
	if ui.view=="hub":ui.hub_controller.resume()
	ui.world_actor=Vector2(ui.world.nodes[str(ui.game.world_node)].position[0],ui.world.nodes[str(ui.game.world_node)].position[1])*16
	if ui.view in ["battle","victory","defeat"]:ui._focus_battle(ui.game.cursor,true)
func real_shot(name: String,source: String) -> void:
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path="res://reports/campaign/screenshots/"+name+".png"
	viewport.get_texture().get_image().save_png(path)
	real_shots.append({"path":path,"source":source,"view":ui.view,"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(),"fixture":false})
	print("REAL_SHOT ",name," ",ui.layout_errors)
func watch_exchange() -> void:
	if ui!=null and ui.view=="combat" and not duel_seen:
		duel_seen=true;capture_exchange()
func capture_exchange() -> void:
	await real_shot("06-near-combat","Live legal exchange reached through actual input from S12 first-turn save")
	ui.instant_mode=true
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/campaign/screenshots"))
	viewport=SubViewport.new();viewport.size=Vector2i(256,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	load_checkpoint("prologue")
	walk_to(Vector2i(7,3));key(KEY_UP);key(KEY_Z);await process_frame;key(KEY_Z)
	await real_shot("01-prologue-dialogue","Actual prologue save and facing interaction")
	await settle();await real_shot("02-snow-village","Actual prologue transition into the flashback")
	load_checkpoint("world-start");await real_shot("03-world-map","Actual first departure save")
	load_checkpoint("M12-deployment");key(KEY_Z);await real_shot("04-movement","Actual M12 opening save, selected unit movement range")
	key(KEY_X);load_checkpoint("M13-deployment");cursor_to(Vector2i(5,4));await real_shot("05-prison-map","Actual M13 opening save, camera moved with cursor keys")
	load_checkpoint("chapter-end");await real_shot("07-chapter-complete","Actual chapter ceremony completion save")
	load_checkpoint("S12-deployment");ui.instant_mode=false;process_frame.connect(watch_exchange)
	for pass_ in range(4):
		if duel_seen or abort:break
		var turn_=ui.game.turn
		for id in ui.game.party.duplicate():
			if duel_seen or abort or ui.game.turn!=turn_:break
			await act(str(id))
		if not duel_seen and not abort and ui.game.turn==turn_:key(KEY_S);choose("end_turn");await settle()
	process_frame.disconnect(watch_exchange)
	for i in range(6):await process_frame
	var report={"scope":"Actual Godot screenshots, based on real play checkpoints and legal live input; no fabricated map mockups","shots":real_shots,"background_guard":true,"visible_windows":false,"duel_captured":duel_seen,"failures":failures}
	var f=FileAccess.open("res://reports/campaign/real-screenshots.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null
	quit(0 if not abort and duel_seen else 1)
