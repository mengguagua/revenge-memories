extends "res://tests/round3.gd"
const OUT="/Users/gcc/gaocc/project/revenge-memories/officialWebsite/source/captures/"
var website_shots=[]
var combat_shot=false
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func checkpoint(path:String):
	ui.game.save_path=path
	if not ui.game.load_game():record_failure("Missing website checkpoint: "+path);return
	ui.game.save_path="/private/tmp/revenge-website-capture-working.json"
	ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu();ui.notice_time=0;ui.phase_time=0
	ui.world_actor=Vector2(ui.world.nodes[str(ui.game.world_node)].position[0],ui.world.nodes[str(ui.game.world_node)].position[1])*16
	if ui.view=="hub":ui.hub_controller.resume()
	if ui.view=="battle":ui._focus_battle(ui.game.cursor,true)
func snap(name:String,source:String):
	ui.layout_errors.clear();ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	website_shots.append({"name":name,"source":source,"view":ui.view,"size":[1278,720],"layout_errors":ui.layout_errors.duplicate()})
	print("WEBSITE_CAPTURE ",name," ",ui.layout_errors)
func watch_combat():
	if ui!=null and ui.view=="combat" and not combat_shot:
		combat_shot=true;capture_combat()
func capture_combat():
	for i in range(32):await process_frame
	await snap("combat","Live legal combat reached by ordinary game input from the S12 checkpoint")
	ui.instant_mode=true
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.instant_mode=true;ui.game.slot_directory="/private/tmp/revenge-website-isolated";ui.game.save_path="/private/tmp/revenge-website-capture-working.json"
	ui.set_process(false);ui.elapsed=2.0;await snap("title","Current PC title screen")
	ui.game.new_game();ui.game.save_path="/private/tmp/revenge-website-capture-working.json"
	ui.story_intro.start();ui.story_intro.index=0;ui.story_intro.reveal=999;ui.story_intro.fade=1
	await snap("story","Current PC opening narration")
	ui.view="hub";ui.hub_controller.enter_room("P00");await process_frame
	ui.prologue_scene.start();ui.prologue_scene._enter(2);ui.dialogue_reveal=999;await process_frame
	await snap("prologue","Current PC prologue scene and dialogue")
	ui.prologue_scene.active=false;ui.game.flags.erase("prologue_scene")
	var plan=[
		["tactics","res://reports/chapter1-redesign-20261022/play/continuous-main-final/continuous-main-final-M12-field.json"],
		["prison","res://reports/chapter1-redesign-20261022/play/continuous-main-final/continuous-main-final-M13-field.json"],
		["harbor","res://reports/chapter2-redesign-20261022/play/continuous-final/continuous-final-F25-field.json"],
		["snow","res://reports/chapter4/play/round2-M41-field.json"],
		["world","res://reports/campaign/natural-world-start-save.json"]]
	for item in plan:
		checkpoint(item[1])
		if item[0]=="tactics":
			ui.game.cursor=ui.GameState.pos(ui.game.find_unit("hunapu"));ui._focus_battle(ui.game.cursor,true);key(KEY_Z)
		await snap(item[0],item[1])
	checkpoint("res://reports/campaign/natural-S12-deployment-save.json")
	ui.instant_mode=false;ui.set_process(true);process_frame.connect(watch_combat)
	for pass_ in range(3):
		if combat_shot or abort:break
		var turn_=ui.game.turn
		for id in ui.game.party.duplicate():
			if combat_shot or abort or ui.game.turn!=turn_:break
			await act(str(id))
		if not combat_shot and not abort and ui.game.turn==turn_:key(KEY_S);choose("end_turn");await settle()
	process_frame.disconnect(watch_combat)
	for i in range(5):await process_frame
	var f=FileAccess.open(OUT+"capture-report.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"shots":website_shots,"failures":failures,"combat_captured":combat_shot,"background_guard":true,"visible_windows":false,"user_saves_touched":false,"scope":"Fresh Godot PC viewport captures; existing development checkpoints; current renderer; isolated save path"},"  "));f.close()
	ui.queue_free();await process_frame;quit(0 if not abort and combat_shot else 1)
