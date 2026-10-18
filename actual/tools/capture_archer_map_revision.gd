extends SceneTree
var ui
var viewport
var out = "res://reports/archer-map-test-20261018/visual/"
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
	ui.set_process(false);ui.game.save_path="/private/tmp/archer-map-capture-unused-save.json"
	ui._new_game();ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	ui.hub_controller.enter_room("H01")
	await shot("story-daan-static")
	ui.game.new_game();ui.game.world_node=int(ui.game.stages[101].node)
	if not ui.game.start_battle(101):errors.append("M11 fixture failed");quit(1);return
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	var ally: Dictionary=ui.game.find_unit("daan")
	var enemy: Dictionary={}
	for actor in ui.game.units:
		if actor.side=="enemy" and int(actor.class_id)==12:enemy=actor;break
	if ally.is_empty() or enemy.is_empty():errors.append("M11 archers missing");quit(1);return
	# Fixture positions only: keep both faction silhouettes visible on real ground.
	ally.position=[5,5];enemy.position=[7,5];ui.game.cursor=Vector2i(6,5)
	ui._focus_battle(Vector2i(6,5),true)
	ui.elapsed=22.1/60.0988;await shot("M11-both-archers-idle")
	for actor in [ally,enemy]:
		ui.moving_id=actor.id;ui.moving_position=Vector2(ui.game.pos(actor))*16
		for phase in [0,1]:
			ui.moving_direction=Vector2i.DOWN;ui.moving_frame=phase
			await shot(str(actor.side)+"-down-"+str(phase))
		ui.moving_direction=Vector2i.RIGHT;ui.moving_frame=0;await shot(str(actor.side)+"-right-neutral")
		ui.moving_direction=Vector2i.LEFT;ui.moving_frame=1;await shot(str(actor.side)+"-left-stride")
	var file=FileAccess.open(out+"checks.json",FileAccess.WRITE);file.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"fixture":true,"background_guard":true},"  "));file.close()
	print("ARCHER_MAP_VISUAL ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
