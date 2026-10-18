extends SceneTree
## Review-only: replace textures in this temporary process, never runtime files.
const Party = preload("res://core/party_sprites.gd")
var ui
var viewport
var base = "/Users/gcc/gaocc/project/revenge-memories/art-review/character-expansion-20261018/body-volume-static-20261018/"
var previous: Dictionary = {}
var art_paths: Dictionary = {}
var shots: Array = []
var errors: Array = []
var positions: Array = []
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":quit(1);return
	call_deferred("run")
func shot(name: String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(base+"reviews/"+name+".png")
	shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"shot":name,"errors":ui.layout_errors.duplicate()})
func samples(enabled: bool):
	for key in art_paths:
		if enabled:
			var image=Image.load_from_file(base+"deliverables/"+key+".png")
			if image==null or image.is_empty():errors.append("missing sample "+key);continue
			ui.textures[art_paths[key]]=ImageTexture.create_from_image(image)
		else:ui.textures[art_paths[key]]=previous[key]
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240)
	viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/body-volume-static-preview.json";ui.game.new_game()
	ui.game.world_node=int(ui.game.stages[101].node)
	if not ui.game.start_battle(101):errors.append("M11 fixture failed");quit(1);return
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false;ui.elapsed=0;ui.moving_id=""
	for kind in ["archer","spearman"]:
		for side in ["ally","enemy"]:
			var actor={"class_id":12 if kind=="archer" else 6,"side":"player" if side=="ally" else "enemy"}
			var art=Party.sprite("map",actor,1);var key=kind+"-"+side
			art_paths[key]=art.path;previous[key]=ui._tex(art.path)
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true)
	await shot("battle-current")
	samples(true);await shot("battle-sample");samples(false)
	var specs=[["archer-ally",12,"player",7],["spearman-ally",6,"player",9],["hero",21,"player",11],["archer-enemy",12,"enemy",13],["spearman-enemy",6,"enemy",15]]
	var actors=[]
	for spec in specs:
		var actor: Dictionary=ui.game.find_unit("hunapu").duplicate(true)
		actor.id=spec[0];actor.class_id=spec[1];actor.side=spec[2];actor.acted=false;actor.position=[spec[3],5]
		actors.append(actor)
	ui.game.units=actors;ui.game.selected_id="";ui.game.cursor=Vector2i(11,5);ui._focus_battle(Vector2i(11,5),true)
	for actor in actors:
		var pos=ui._battle_cell_screen(ui.game.pos(actor))+ui._canvas_offset()+Vector2(8,16)
		positions.append({"name":actor.id,"cell":actor.position,"foot_pixel":[pos.x*4,pos.y*4]})
	await shot("lineup-current");samples(true);await shot("lineup-sample");samples(false)
	var report={"passed":errors.is_empty(),"errors":errors,"shots":shots,"positions":positions,"scene":"M11 actual map and renderer","native_viewport":[426,240],"render_size":[1704,960],"temporary_texture_override_only":true,"runtime_assets_modified":false,"background_guard":true,"static_pose":0}
	var file=FileAccess.open(base+"capture.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("BODY_VOLUME_STATIC ",JSON.stringify(report))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
