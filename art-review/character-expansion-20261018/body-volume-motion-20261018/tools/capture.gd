extends SceneTree
## Capture actual exported textures with the real renderer; positions are test fixtures.
var ui
var viewport
var out="/Users/gcc/gaocc/project/revenge-memories/actual/reports/body-volume-map-test-20261018/visual/"
var shots:Array=[]
var errors:Array=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(out+name+".png")
	shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"shot":name,"errors":ui.layout_errors.duplicate()})
func run():
	DirAccess.make_dir_recursive_absolute(out)
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/body-volume-capture-unused-save.json";ui._new_game();ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false
	for room in ["H01","H07","H05"]:
		ui.hub_controller.enter_room(room);await shot("story-"+room)
	ui.game.new_game();ui.game.world_node=int(ui.game.stages[101].node)
	if not ui.game.start_battle(101):errors.append("M11 fixture failed");quit(1);return
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false;ui.elapsed=0;ui.moving_id=""
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);await shot("M11-actual-deployment")
	var specs=[["archer-ally",12,"player",7],["spearman-ally",6,"player",9],["hunapu",21,"player",11],["archer-enemy",12,"enemy",13],["spearman-enemy",6,"enemy",15]]
	var actors=[]
	for spec in specs:
		var actor:Dictionary=ui.game.find_unit("hunapu").duplicate(true)
		actor.id=spec[0];actor.class_id=spec[1];actor.side=spec[2];actor.acted=false;actor.position=[spec[3],5];actors.append(actor)
	ui.game.units=actors;ui.game.selected_id="";ui.game.cursor=Vector2i(11,5);ui._focus_battle(Vector2i(11,5),true)
	for tick in [0,14,22]:
		ui.elapsed=(tick+0.1)/60.0988;await shot("lineup-idle-"+str(tick))
	for actor in actors:
		if actor.id=="hunapu":continue
		ui.moving_id=actor.id;ui.moving_position=Vector2(ui.game.pos(actor))*16
		for direction in {"up":Vector2i.UP,"right":Vector2i.RIGHT,"down":Vector2i.DOWN,"left":Vector2i.LEFT}:
			ui.moving_direction={"up":Vector2i.UP,"right":Vector2i.RIGHT,"down":Vector2i.DOWN,"left":Vector2i.LEFT}[direction]
			for phase in [0,1]:
				ui.moving_frame=phase;await shot(actor.id+"-"+direction+"-"+str(phase))
	var f=FileAccess.open(out+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"background_guard":true,"actual_exported_textures":true,"fixture_positions":true},"  "));f.close()
	print("BODY_VOLUME_VISUAL ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
