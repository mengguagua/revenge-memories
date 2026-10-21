extends "res://tests/chapter5_play.gd"
## Guarded SubViewport screenshots. Fixture and genuine saved play are labeled separately.
var shots=[]
var fixture_mode=true
var output_dir="res://reports/chapter5/visual/"
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	fixture_mode=OS.get_environment("CH5_REAL_CAPTURE")!="1"
	if not fixture_mode:output_dir="res://reports/chapter5/screenshots/"
	call_deferred("run")
func load_checkpoint(path: String):
	ui.game.save_path=path
	if not ui.game.load_game():record_failure("capture checkpoint failed "+path);return
	ui.game.save_path="res://reports/chapter5/capture-working.json"
	ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.notice_time=0;ui.phase_time=0;ui.view=ui.game.mode
	if ui.view=="hub":ui.hub_controller.resume()
	if ui.view=="ending":ui._start_ending()
	if ui.view=="battle":ui._focus_battle(ui.game.cursor,true)
	if ui.game.flags.has("active_plot"):ui._resume_plot()
	await settle()
func shot(name: String,description: String):
	ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path=output_dir+name+".png"
	viewport.get_texture().get_image().save_png(path)
	if ui.view=="hub" and ui.menu_context=="fifth_selection":
		var caption=ui.presentation_audit.get("hub_caption",Rect2())
		if caption.has_area() and caption.intersects(ui._menu_rect()):ui.layout_errors.append("Preparation menu overlaps hub caption")
	shots=shots.filter(func(s):return s.path!=path)
	shots.append({"path":path,"description":description,"fixture":fixture_mode,"canvas":[viewport.size.x,viewport.size.y],"view":ui.view,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"text_checks":ui.text_checks.duplicate(true),"layout_errors":ui.layout_errors.duplicate()})
	print("CH5_CAPTURE ",name," errors ",ui.layout_errors)
func focus(p):
	ui.game.cursor=Vector2i(p[0],p[1]);ui._focus_battle(ui.game.cursor,true)
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output_dir))
	if OS.get_environment("CH5_APPEND_CAPTURE")=="1":shots=State.read_json(output_dir+"captures.json").get("shots",[])
	viewport=SubViewport.new();viewport.size=Vector2i(768,448);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	if fixture_mode:
		for id in [501,502,503,504,511,533,534]:
			viewport.size=Vector2i(768,576)
			await load_checkpoint("res://reports/chapter4/play/round2-chapter-end.json")
			ui.game.begin_chapter_five();ui.game.flags.M51_confirmed=true;ui.game.flags.east_network_ready=true;ui.game.flags.S51_invited=true;ui.game.flags.west_palace_gate=true;ui.game.flags.east_palace_gate=true
			ui.game.cleared_stages.append_array([501,502,503,504]);ui.game.cleared_stages.erase(id)
			if id in [533,534]:
				ui.game.route_positions={"alm":15,"celica":15};ui.game.flags.chapter5_ready={"alm":true,"celica":true};ui.game.ChapterFive.merge(ui.game)
				if id==534:ui.game.cleared_stages.append(533);ui.game.flags.final_access=true
			else:ui.game.route=ui.game.stages[id].route;ui.game.party=ui.game.parties[ui.game.route].duplicate()
			ui.game.world_node=int(ui.game.stages[id].node);ui.game.start_battle(id);ui.game.story_events.clear();ui.game.flags.erase("active_plot");ui.view="battle";ui.busy=false;ui._clear_menu()
			await process_frame
			ui.battle_camera=ui._clamp_map_camera(Vector2.ZERO,Vector2(ui.game.battle_data.map.width,ui.game.battle_data.map.height)*16)
			await shot(str(ui.game.battle_data.code)+"-whole","地图全景；定向部署视觉夹具")
			viewport.size=Vector2i(426,240);await process_frame;focus(ui.game.battle_data.targets[0])
			await shot(str(ui.game.battle_data.code)+"-objective","任务目标与周边道路；定向视觉夹具")
			key(KEY_S);choose("new:goal");await process_frame;key(KEY_Z);await shot(str(ui.game.battle_data.code)+"-goal-text","目标菜单文字安全区")
			await settle()
		for room in ui.game.ChapterFive.ROOMS:
			viewport.size=Vector2i(426,240);ui.game.mode="hub";ui.hub_controller.enter_room(room)
			await shot(room,"可行走据点，固定房间视觉夹具")
	else:
		# The manifest is populated from successful play evidence by the delivery builder.
		var manifest=State.read_json("res://reports/chapter5/real-capture-plan.json")
		for item in manifest.shots:
			viewport.size=Vector2i(item.get("size",[426,240])[0],item.get("size",[426,240])[1]);await load_checkpoint(str(item.save))
			if abort:break
			if item.has("focus") and ui.view=="battle":cursor_to(Vector2i(item.focus[0],item.focus[1]))
			if item.get("action","")=="selection":
				await hub_action("fifth_prepare")
			if item.get("action","")=="goal":
				key(KEY_S);choose("new:goal");await process_frame;key(KEY_Z)
			if item.has("ending_target"):
				for step in range(ui.ending_pages.size()):
					if ui.ending_pages[ui.ending_index].title==item.ending_target:break
					key(KEY_Z);await process_frame
			await shot(str(item.name),str(item.description));ui._clear_menu();await settle()
	var bad=[]
	for s in shots:bad.append_array(s.layout_errors)
	var f=FileAccess.open(output_dir+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":bad.is_empty() and not abort,"shots":shots,"errors":bad,"failures":failures,"background_guard":true,"visible_windows":false},"  "));f.close()
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if bad.is_empty() and not abort else 1)
