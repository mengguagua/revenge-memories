extends SceneTree
var ui
var viewport
var out = "res://reports/hunapu-world-shadow-20261018/visual/"
var shots: Array = []
var errors: Array = []
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":quit(1);return
	call_deferred("run")
func shot(name: String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(out+name+".png")
	shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"shot":name,"errors":ui.layout_errors.duplicate()})
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240)
	viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/hunapu-map-capture-unused-save.json"
	ui.game.new_game();ui._new_journey_in_slot();ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	for direction in [Vector2i.RIGHT,Vector2i.LEFT]:
		for phase in [0,1]:
			ui.hub_controller.facing=direction;ui.hub_controller.clock=(phase*16+0.1)/60.0988;ui.hub_controller.motion_left=0.1
			await shot("story-"+("right"if direction.x>0 else"left")+"-"+str(phase))
	ui.game.mode="world";ui.view="world";ui.game.world_node=2
	ui.world_actor=Vector2(ui.world.nodes["2"].position[0],ui.world.nodes["2"].position[1])*16
	ui.world_path=[ui.world_actor+Vector2(16,0)]
	for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.RIGHT,Vector2i.LEFT]:
		ui.world_facing=direction;ui.elapsed=16.1/60.0988
		await shot("world-"+str(direction.x)+"-"+str(direction.y))
	var file=FileAccess.open(out+"checks.json",FileAccess.WRITE);file.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"fixture":true,"background_guard":true},"  "));file.close()
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
