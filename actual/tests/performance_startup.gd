extends SceneTree
var screen
var phone
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(2);return
	call_deferred("run")
func run():
	Engine.max_fps=60
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/revenge-performance-20261025/baseline-slots";screen.add_child(phone);await process_frame
	var ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all();ui.audio.set_process(false)
	ui.game.new_game();ui.game.save_path="/private/tmp/revenge-performance-20261025/baseline-save.json";ui.game.world_node=int(ui.game.stages[101].node);ui.game.start_battle(101);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui.elapsed=2;ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);ui.queue_redraw()
	for i in range(8):await process_frame
	await RenderingServer.frame_post_draw
	var result={"view":"M11 battle / inspect / new game / first map render","screen":[2556,1179],"logical":[phone.game_view.size_2d_override.x,phone.game_view.size_2d_override.y],"integer_scale":phone.pixel_scale,"godot_version":Engine.get_version_info().string,"renderer":RenderingServer.get_video_adapter_name(),"static_memory_bytes":int(Performance.get_monitor(Performance.MEMORY_STATIC)),"texture_memory_bytes":int(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)),"loaded_texture_entries":ui.textures.size(),"read_whole_json_in_test":false,"pid":OS.get_process_id()}
	var image=screen.get_texture().get_image();var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(image.get_data());result.render_rgba_sha256=hash.finish().hex_encode()
	var f=FileAccess.open(OS.get_environment("STARTUP_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close();print("STARTUP_PROBE ",JSON.stringify(result))
	phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit()
