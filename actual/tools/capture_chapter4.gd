extends "res://tests/chapter4_play.gd"
## Guarded SubViewport screenshots. Fixture and genuine saved play are labeled separately.
var shots=[]
var fixture_mode=true
var output_dir="res://reports/chapter4/visual/"
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	fixture_mode=OS.get_environment("CH4_REAL_CAPTURE")!="1"
	if not fixture_mode:output_dir="res://reports/chapter4/screenshots/"
	call_deferred("run")
func load_checkpoint(path: String):
	ui.game.save_path=path
	if not ui.game.load_game():record_failure("capture checkpoint failed "+path);return
	ui.game.save_path="res://reports/chapter4/capture-working.json"
	ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.notice_time=0;ui.phase_time=0;ui.view=ui.game.mode
	if ui.view=="hub":ui.hub_controller.resume()
	if ui.view=="battle":ui._focus_battle(ui.game.cursor,true)
	if ui.game.flags.has("active_plot"):ui._resume_plot()
	await settle()
func shot(name: String,description: String):
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path=output_dir+name+".png"
	viewport.get_texture().get_image().save_png(path)
	shots.append({"path":path,"description":description,"fixture":fixture_mode,"canvas":[viewport.size.x,viewport.size.y],"view":ui.view,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"text_checks":ui.text_checks.duplicate(true),"layout_errors":ui.layout_errors.duplicate()})
	print("CH4_CAPTURE ",name," errors ",ui.layout_errors)
func focus(p):
	ui.game.cursor=Vector2i(p[0],p[1]);ui._focus_battle(ui.game.cursor,true)
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output_dir))
	viewport=SubViewport.new();viewport.size=Vector2i(768,448);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	if fixture_mode:
		for id in [401,402,403,404,405,406,407,408,411,412]:
			viewport.size=Vector2i(768,448)
			await load_checkpoint("res://reports/chapter3/play/round1final-chapter-end.json")
			ui.game.begin_chapter_four();ui.game.flags.M41_confirmed=true;ui.game.flags.F41_confirmed=true;ui.game.flags.F43_confirmed=true;ui.game.flags.S41_invited=true;ui.game.flags.S42_invited=true;ui.game.flags.obs_steps_ready=true;ui.game.flags.west_tower_safe=true;ui.game.cleared_stages.append_array([402,403,406]);ui.game.cleared_stages.erase(id);ui.game.route=ui.game.stages[id].route;ui.game.party=ui.game.parties[ui.game.route].duplicate();ui.game.world_node=int(ui.game.stages[id].node)
			ui.game.start_battle(id);ui.game.story_events.clear();ui.game.flags.erase("active_plot");ui.view="battle";ui.busy=false;ui._clear_menu()
			await process_frame
			ui.battle_camera=ui._clamp_map_camera(Vector2.ZERO,Vector2(ui.game.battle_data.map.width,ui.game.battle_data.map.height)*16)
			await shot(str(ui.game.battle_data.code)+"-whole","地图全景；定向部署视觉夹具")
			viewport.size=Vector2i(426,240);await process_frame;focus(ui.game.battle_data.objects[0].position)
			await shot(str(ui.game.battle_data.code)+"-objective","任务目标与周边道路；定向视觉夹具")
			key(KEY_S);choose("new:goal");await process_frame
			key(KEY_Z);await shot(str(ui.game.battle_data.code)+"-goal-text","实际目标菜单，检查完整文字安全区")
			await settle()
		for room in ui.game.ChapterFour.ROOMS:
			viewport.size=Vector2i(426,240);ui.game.mode="hub";ui.hub_controller.enter_room(room)
			await shot(room,"可行走据点，固定房间视觉夹具")
	else:
		# The manifest is populated from successful play evidence by the delivery builder.
		var manifest=State.read_json("res://reports/chapter4/real-capture-plan.json")
		for item in manifest.shots:
			viewport.size=Vector2i(item.get("size",[426,240])[0],item.get("size",[426,240])[1]);await load_checkpoint(str(item.save))
			if abort:break
			if item.has("focus") and ui.view=="battle":cursor_to(Vector2i(item.focus[0],item.focus[1]))
			if item.get("action","")=="goal":
				key(KEY_S);choose("new:goal");await process_frame;key(KEY_Z)
			await shot(str(item.name),str(item.description));await settle()
	var bad=[]
	for s in shots:bad.append_array(s.layout_errors)
	var f=FileAccess.open(output_dir+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":bad.is_empty() and not abort,"shots":shots,"errors":bad,"failures":failures,"background_guard":true,"visible_windows":false},"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if bad.is_empty() and not abort else 1)
