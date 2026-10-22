extends SceneTree
const OUT="/Users/gcc/gaocc/project/revenge-memories/actual/reports/iphone-layout-20261022/"
const SOURCE="/private/tmp/revenge-iphone-layout-20261022/device-saves-before/journey-slot-2.json"
var errors=[]
var checks=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func run():
	var original=FileAccess.get_file_as_bytes(SOURCE)
	check(str(ProjectSettings.get_setting("application/config/version"))=="0.10.2","exported version is 0.10.2")
	var viewport=SubViewport.new();viewport.size=Vector2i(2556,1179);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	var phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);viewport.add_child(phone);await process_frame
	var ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.game.save_path=SOURCE
	check(ui.game.load_game(),"exported app loads a copy of the actual iPhone record")
	ui.game.save_path="/private/tmp/revenge-iphone-layout-20261022/package-unused.json";ui.game.slot_directory="/private/tmp/revenge-iphone-layout-20261022/package-slots"
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
	check(ui.game.stage_id==101 and ui.game.mode=="battle","actual first-battle record remains a battle")
	check(phone.game_view.size_2d_override==Vector2i(406,240) and phone.pixel_scale==4,"exported phone viewport uses wider integer layout")
	phone._sync_controls()
	check(phone.buttons.any(func(b):return int(b.key)==KEY_E),"exported tactical controls include ally cycle")
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);phone.queue_redraw();ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	errors.append_array(phone.layout_errors);errors.append_array(ui.layout_errors)
	viewport.get_texture().get_image().save_png(OUT+"11-exported-package-actual-record.png")
	ui._open_system_menu();check(ui.menu_actions.has("new:battle_title"),"exported battle menu contains return to main menu")
	check(ui.has_method("set_touch_fast_forward") and ui.has_method("effective_animation_speed"),"exported animation speed interface is present")
	check(FileAccess.get_file_as_bytes(SOURCE)==original,"actual iPhone record copy remains byte-identical")
	var f=FileAccess.open(OUT+"package-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"source":"copy of iPhone journey-slot-2.json","physical_device_gameplay":false,"background_guard":true,"player_records_written":false},"  "));f.close()
	print("IPHONE_PACKAGE ",checks.size()," checks; errors: ",errors)
	phone.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
