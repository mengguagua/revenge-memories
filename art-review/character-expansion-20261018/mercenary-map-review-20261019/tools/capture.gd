extends SceneTree
## Review process only: temporary cached textures and metadata, no runtime file writes.
const Party=preload("res://core/party_sprites.gd")
const Reviewed=preload("res://core/reviewed_animations.gd")
var ui
var viewport
var base="/Users/gcc/gaocc/project/revenge-memories/art-review/character-expansion-20261018/mercenary-map-review-20261019/"
var shots:Array=[]
var errors:Array=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(base+"reviews/"+name+".png")
	shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"shot":name,"errors":ui.layout_errors.duplicate()})
func override_art(previous:Dictionary,side:String,walking:bool)->Dictionary:
	var art=previous.duplicate(true)
	var image=Image.load_from_file(base+"deliverables/class-8-"+side+("/walk-atlas.png"if walking else"/idle-atlas.png"))
	ui.textures[art.path]=ImageTexture.create_from_image(image)
	art.frame_size=[128,96]if walking else[96,96];art.frames=8 if walking else 6;art.columns=art.frames
	art.anchor=[16,24]if walking else[12,20];art.tile_origin=[8,8]if walking else[4,4];art.native_density=4
	art.static_facing=not walking;art.source_oam_frame_count=0;art.oam_flip_origin_offset=[0,0]
	art.directions={"up":[0,1],"right":[2,3],"down":[4,5],"left":[6,7],"side":[2,3]}if walking else{"up":[0,0],"right":[0,0],"down":[0,0],"left":[0,0],"side":[0,0]}
	art.ground_shadow={"path":"res://assets/reviewed-animation-20261018/archer-ground-shadow.png","size":[11,3],"offset":[0,-1],"alpha":0.38}
	if not walking:art.native_cycle=[0,1,2,1];art.cycle_ticks=[14,8,14,8]
	else:art.erase("native_cycle");art.erase("cycle_ticks")
	return art
func samples():
	var data=Reviewed.data()
	for side in ["ally","enemy"]:
		for context in ["tactical-idle","tactical-walk"]:data.maps["8_"+side][context]=override_art(data.maps["8_"+side][context],side,context=="tactical-walk")
	var party=Party.data()
	for group in ["classes","chapter1_classes","frozen_classes"]:
		if not party.has(group)or not party[group].has("civilian"):continue
		for context in ["map","map_move"]:
			if party[group].civilian.has(context):party[group].civilian[context]=override_art(party[group].civilian[context],"neutral",context=="map_move")
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/mercenary-review-unused-save.json";ui.game.new_game();ui.game.world_node=int(ui.game.stages[101].node)
	if not ui.game.start_battle(101):errors.append("M11 fixture failed");quit(1);return
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false;ui.elapsed=0;ui.moving_id=""
	ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);await shot("M11-before")
	samples();await shot("M11-mercenary-refugees-sample")
	var refugees:Dictionary=ui.game.find_unit("M11_refugees0").duplicate(true)
	var specs=[["hunapu",21,"player",7],["archer",12,"player",9],["spearman",6,"player",11],["mercenary-ally",8,"player",13],["M11_refugees0",14,"player",15],["mercenary-enemy",8,"enemy",17]]
	var actors=[]
	for spec in specs:
		var actor:Dictionary=(refugees if spec[0]=="M11_refugees0"else ui.game.find_unit("hunapu")).duplicate(true)
		actor.id=spec[0];actor.class_id=spec[1];actor.side=spec[2];actor.acted=false;actor.position=[spec[3],5];actors.append(actor)
	ui.game.units=actors;ui.game.selected_id="";ui.game.cursor=Vector2i(12,5);ui._focus_battle(Vector2i(12,5),true)
	for tick in [0,14,22]:ui.elapsed=(tick+0.1)/60.0988;await shot("lineup-idle-"+str(tick))
	for actor in actors:
		if actor.id not in ["mercenary-ally","mercenary-enemy","M11_refugees0"]:continue
		ui.moving_id=actor.id;ui.moving_position=Vector2(ui.game.pos(actor))*16
		for direction in {"up":Vector2i.UP,"right":Vector2i.RIGHT,"down":Vector2i.DOWN,"left":Vector2i.LEFT}:
			ui.moving_direction={"up":Vector2i.UP,"right":Vector2i.RIGHT,"down":Vector2i.DOWN,"left":Vector2i.LEFT}[direction]
			for phase in [0,1]:ui.moving_frame=phase;await shot(actor.id+"-"+direction+"-"+str(phase))
	var f=FileAccess.open(base+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"background_guard":true,"review_only_in_memory_overrides":true,"runtime_integrated":false,"M11_refugee_class_id_retained":14},"  "));f.close()
	print("MERCENARY_REVIEW ",shots.size()," screenshots; errors ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty()else 1)
