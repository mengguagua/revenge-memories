extends "res://tests/polish_play.gd"
var maps=[]
func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	review_out="res://reports/playtest-0.5.0/maps/";call_deferred("run")
func capture_map(name: String,whole: bool=false) -> void:
	ui.queue_redraw()
	for frame in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var path=review_out+name+".png";viewport.get_texture().get_image().save_png(path)
	maps.append({"name":name,"stage":ui.game.battle_data.code,"source":stage_source,"fixture":false,"whole_map":whole,"path":path,"layout_errors":ui.layout_errors.duplicate(),"card":ui.battle_card_audit.duplicate(true)})
	if not ui.layout_errors.is_empty():record_failure("Map text safety: "+name)
func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	for code in ["M11","M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","F26","S21","S22"]:
		stage_source=("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
		ui.game.save_path=stage_source;var loaded=ui.game.load_game();ui.game.save_path="res://.cache/playtest-0.5.0/maps.json"
		if not loaded:record_failure("Map checkpoint cannot load: "+code);continue
		ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.phase_time=0;ui.notice_time=0
		var node=ui.game.world_node;key(KEY_S);choose("new:prepare");await settle();await go(node);key(KEY_Z);choose("new:battle");await settle();ui.phase_time=0;ui.notice_time=0
		var map=ui.game.battle_data.map;viewport.size=Vector2i((map.width+4)*16,(map.height+4)*16);await process_frame
		cursor_to(Vector2i.ZERO);ui._focus_battle(ui.game.cursor,true);ui.ui_mode="whole_capture";await capture_map(code+"-whole",true)
		viewport.size=Vector2i(426,240);await process_frame;ui.ui_mode="inspect";cursor_to(State.pos(ui.game.find_unit(ui.game.leader_id())));ui._focus_battle(ui.game.cursor,true);await capture_map(code+"-entry")
		if code=="F21":cursor_to(Vector2i(25,13));ui._focus_battle(ui.game.cursor,true);await capture_map("F21-medic-point")
		if code in ["M11","F22","S22"]:key(KEY_S);choose("new:focus_exit");await capture_map(code+"-exit")
		print("POLISH_MAP ",code)
	var report={"passed":failures.is_empty(),"failures":failures,"maps":maps,"background_guard":true,"visible_windows":false,"scope":"All 15 current battlefields entered through ordinary keys from genuine old checkpoints. Full-field plates enlarge viewport and hide inspection card only; normal landscape and objective details use real camera/UI."}
	var f=FileAccess.open(review_out+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	ui.hub_controller.dispose();ui.hub_controller=null;ui.free();viewport.queue_free();await process_frame;quit(0 if report.passed else 1)
