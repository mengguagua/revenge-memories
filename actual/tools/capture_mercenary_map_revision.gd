extends SceneTree
var ui
var viewport
var out="res://reports/mercenary-map-test-20261019/visual/"
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
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/mercenary-pack-capture-unused-save.json";ui.game.new_game();ui.game.world_node=int(ui.game.stages[101].node)
	if not ui.game.start_battle(101):errors.append("M11 fixture failed");quit(1);return
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false;ui.elapsed=0;ui.moving_id=""
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true)
	await shot("M11-real-refugees-idle")
	var refugee:Dictionary=ui.game.find_unit("M11_refugees0")
	ui.moving_id=refugee.id;ui.moving_position=Vector2(ui.game.pos(refugee))*16;ui.moving_direction=Vector2i.LEFT
	for phase in [0,1]:ui.moving_frame=phase;await shot("M11-real-refugee-left-"+str(phase))
	ui.moving_id=""
	var specs=[["hunapu",21,"player",7],["archer",12,"player",9],["spearman",6,"player",11],["mercenary-ally",8,"player",13],["M11_refugees0",14,"player",15],["mercenary-enemy",8,"enemy",17]]
	var actors=[]
	for spec in specs:
		var actor:Dictionary=(refugee if spec[0]=="M11_refugees0"else ui.game.find_unit("hunapu")).duplicate(true)
		actor.id=spec[0];actor.class_id=spec[1];actor.side=spec[2];actor.acted=false;actor.position=[spec[3],5];actors.append(actor)
	ui.game.units=actors;ui.game.selected_id="";ui.game.cursor=Vector2i(12,5);ui._focus_battle(Vector2i(12,5),true)
	for tick in [0,22]:ui.elapsed=(tick+0.1)/60.0988;await shot("lineup-idle-"+str(tick))
	for actor in actors:
		if actor.id not in ["mercenary-ally","mercenary-enemy","M11_refugees0"]:continue
		ui.moving_id=actor.id;ui.moving_position=Vector2(ui.game.pos(actor))*16
		for direction in ["up","right","down","left"]:
			ui.moving_direction={"up":Vector2i.UP,"right":Vector2i.RIGHT,"down":Vector2i.DOWN,"left":Vector2i.LEFT}[direction]
			for phase in [0,1]:ui.moving_frame=phase;await shot(actor.id+"-"+direction+"-"+str(phase))
	var f=FileAccess.open(out+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"background_guard":true,"actual_exported_textures":true,"fixture_positions_for_lineup":true,"runtime_texture_overrides":false},"  "));f.close()
	print("MERCENARY_PACK_VISUAL ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty()else 1)
