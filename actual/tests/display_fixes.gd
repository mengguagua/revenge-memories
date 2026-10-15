extends SceneTree
## Targeted display/input fixtures, not a replacement for the recorded natural wins.
var ui
var viewport: SubViewport
var checks: Array=[]
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func key(code: int,pressed: bool=true) -> void:
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=pressed;ui._input(event)
func tap(code: int) -> void:key(code);key(code,false)
func run() -> void:
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false)
	ui.game.save_path="res://reports/campaign/display-fixtures-save.json";ui._new_game()
	check(ProjectSettings.get_setting("display/window/handheld/orientation")==DisplayServer.SCREEN_SENSOR_LANDSCAPE,"mobile orientation allows landscape directions only")
	var hub=ui.hub_controller;var start=Vector2(ui.game.hub_position)*16
	tap(KEY_LEFT)
	check(ui.game.hub_position==Vector2i(5,7) and hub.render_position==start,"walk begins at previous rendered location")
	check(is_equal_approx(hub.motion_left,16.0/60.0988),"walking retains reference 16 ticks per tile")
	tap(KEY_Z);tap(KEY_UP)
	check(ui.view=="hub" and ui.game.hub_position==Vector2i(5,7),"interaction and direction cannot interrupt a moving tile")
	var samples=[]
	for i in range(4):
		hub.process(hub.STEP/4.0);samples.append(hub.render_position)
		check(hub.render_position.is_equal_approx(start+Vector2(-4*(i+1),0)),"walk interpolates quarter "+str(i+1)+" without vertical bounce")
	key(KEY_UP);hub.process(hub.STEP)
	check(ui.game.hub_position==Vector2i(5,5) and hub.render_position==Vector2(5,6)*16,"held direction chains exactly at tile boundary")
	key(KEY_UP,false);hub.process(hub.STEP)
	check(ui.game.hub_position==Vector2i(5,5) and hub.render_position==Vector2(5,5)*16,"release stops after current tile")
	ui.game.hub_position=Vector2i(1,7);hub.enter_room("P00",true);tap(KEY_LEFT)
	check(ui.game.hub_position==Vector2i(1,7) and hub.motion_left==0.0,"extended surroundings remain outside hub walk bounds")
	for speaker in ui.NPC_PORTRAITS:
		var face=ui._speaker_portrait(speaker)
		check(not face.is_empty() and ResourceLoader.exists(str(face.get("path",""))),"portrait available: "+str(speaker))
	for scene in ui.game.campaign.scenes.values():
		for page in scene:
			if str(page.speaker) not in ui.NARRATOR_SPEAKERS:check(not ui._speaker_portrait(str(page.speaker)).is_empty(),"story character portrait: "+str(page.speaker))
	for label in ui.NARRATOR_SPEAKERS:check(ui._speaker_portrait(label).is_empty(),"narration/system text has no portrait: "+str(label))
	var sample="胡纳普挡住法术。神幕显出倾斜的屋顶与撤离的船。她来自同一个世界的另一岸。".repeat(3)
	ui.play_pages([{"speaker":"胡纳普","text":sample}],"hub")
	var sizes=[Vector2i(256,240),Vector2i(426,240),Vector2i(384,240),Vector2i(560,240),Vector2i(562,260)]
	for dimensions in sizes:
		viewport.size=dimensions;await process_frame;ui._reflow_plot()
		var recovered=""
		for page in ui.plot_pages:recovered+=str(page.text).replace("\n","")
		check(recovered==sample,"resize preserves every dialogue character: "+str(dimensions))
		for who in ["旁白","胡纳普","管理员"]:
			var layout=ui._plot_layout(who);var panel: Rect2=layout.panel
			check(Rect2(Vector2.ZERO,Vector2(dimensions)).encloses(Rect2(panel.position+ui._canvas_offset(),panel.size)),"dialogue remains inside viewport: "+who+str(dimensions))
			check(panel.grow(-10).encloses(layout.text),"dialogue text content safe: "+who+str(dimensions))
			if who=="旁白":check(is_equal_approx(layout.text.position.x-panel.position.x,16.0),"narration reclaims portrait space: "+str(dimensions))
			else:check(not layout.text.intersects(layout.portrait),"portrait does not overlap text: "+who+str(dimensions))
	var old_path=ui.game.save_path;ui.game.save_path="res://reports/campaign/display-plot-resume-save.json"
	check(ui.game.save_game(),"resized active dialogue can be saved")
	var restored=ui.GameState.new();restored.save_path=ui.game.save_path
	check(restored.load_game(),"resized active dialogue is compatible with save validation")
	var saved_text=""
	for page in restored.flags.get("active_plot",{}).get("pages",[]):saved_text+=str(page.text).replace("\n","")
	check(saved_text==sample,"active dialogue retains exact text through save reload")
	ui.game.save_path=old_path
	while ui.view=="plot":ui.dialogue_reveal=9999;tap(KEY_Z)
	await process_frame
	viewport.size=Vector2i(560,240);await process_frame
	ui.game.world_node=2;ui.game.start_battle(101);ui.view="battle";ui.busy=false;ui.ui_mode="inspect";ui._clear_menu();ui._focus_battle(Vector2i(5,5),true)
	var target=Vector2i(23,10);var local=ui._battle_cell_screen(target)+Vector2(8,8)
	check(local.x>256,"pointer target is in newly visible side area")
	ui._mouse_accept(local+ui._canvas_offset())
	check(ui.game.cursor==target,"expanded battlefield supports actual pointer selection")
	var before=ui.game.cursor;ui._clear_menu();ui._mouse_accept(ui._battle_cell_screen(Vector2i(-1,10))+ui._canvas_offset()+Vector2(8,8))
	check(ui.game.cursor==before,"padding pointer cannot select impassable outside map")
	check(ui.game.battle_data.map.width==24 and ui.game.formal_world.nodes.size()==39,"responsive rendering does not enlarge playable maps")
	var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"walk_samples":samples,"canvas_sizes":sizes,"scope":"Targeted resize, actual key walking, portrait coverage and pointer fixtures; no battle outcomes modified"}
	var f=FileAccess.open("res://reports/campaign/display-fixes.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("DISPLAY_FIXES ",JSON.stringify(report))
	ui.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
