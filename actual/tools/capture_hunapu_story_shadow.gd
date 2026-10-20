extends "res://tools/capture_hunapu_map_revision.gd"
## Three representative frames only; keep the existing no-focus capture guard.
func run():
	out="res://reports/hunapu-story-shadow-20261018/visual/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240)
	viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/hunapu-shadow-capture-unused.json"
	ui.game.new_game();ui._new_journey_in_slot();ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	for phase in [0,1]:
		ui.hub_controller.facing=Vector2i.DOWN;ui.hub_controller.clock=(phase*16+0.1)/60.0988;ui.hub_controller.motion_left=0.1
		await shot("story-down-"+str(phase))
	ui.hub_controller.facing=Vector2i.RIGHT
	await shot("story-right-1")
	var file=FileAccess.open(out+"checks.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"fixture":true,"background_guard":true},"  "));file.close()
	print("STORY_SHADOW_VISUAL ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
