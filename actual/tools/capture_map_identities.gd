extends SceneTree
const Party=preload("res://core/party_sprites.gd")
var OUT="res://reports/current-art/visual/"
var ui
var viewport
var shots=[]
var errors=[]
var pixel_checks=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	if not OS.get_environment("MAP_IDENTITY_CAPTURE_OUT").is_empty():OUT=OS.get_environment("MAP_IDENTITY_CAPTURE_OUT").trim_suffix("/")+"/"
	call_deferred("run")
func shot(name: String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	shots.append({"path":OUT+name+".png","fixture":true,"layout_errors":ui.layout_errors.duplicate()})
	if not ui.layout_errors.is_empty():errors.append({"shot":name,"layout":ui.layout_errors})
func sprite_check(art: Dictionary,index: int,at: Vector2):
	var image=ui._tex(art.path).get_image();var w=int(art.frame_size[0]);var h=int(art.frame_size[1]);var cols=int(art.get("columns",art.frames))
	var src=image.get_region(Rect2i(index%cols*w,index/cols*h,w,h));var actual=viewport.get_texture().get_image()
	var origin=Vector2i((at.round()+ui._canvas_offset())*4);var different=0;var count=0
	for y in range(h):
		for x in range(w):
			var c=src.get_pixel(x,y)
			if c.a!=1:continue
			var p=origin+Vector2i(x,y)
			if p.x<0 or p.y<0 or p.x>=actual.get_width() or p.y>=actual.get_height():continue
			count+=1
			if actual.get_pixelv(p)!=c:different+=1
	var r={"path":art.path,"frame":index,"pixels":count,"different":different};pixel_checks.append(r)
	if count==0 or different>0:errors.append(r)
func dialogue_shot(name: String,speaker: String,text: String):
	ui.plot_pages=ui._paginate_plot({"speaker":speaker,"text":text})
	ui.plot_index=0;ui.plot_return="hub";ui.dialogue_reveal=1000;ui.view="plot"
	await shot(name)
	ui.view="hub";ui.plot_pages=[]
func world_capture(id: String,chapter: int,node: int,name: String):
	ui.game.chapter=chapter;ui.game.route="alm"if id=="hunapu"else"celica";ui.game.world_node=node;ui.game.mode="world";ui.view="world"
	var p=ui.world.nodes[str(node)].position;ui.world_actor=Vector2(p[0],p[1])*16;ui.world_path=[];ui.world_facing=Vector2i.DOWN;ui.busy=false
	await shot(name+"-world-idle")
	for f in [0,1]:
		ui.world_facing=Vector2i.RIGHT;ui.world_path=[[p[0],p[1]],[p[0]+1,p[1]]];ui.elapsed=(f*16+.5)/60.0988
		await shot(name+"-world-walk-"+str(f))
	ui.world_path=[]
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.set_process(false);ui.game.new_game();ui.game.save_path=OUT+"unused.json"
	ui.hub_controller.enter_room("P00");ui.game.hub_position=Vector2i(6,4);ui.hub_controller.render_position=Vector2(96,64);ui.hub_controller.facing=Vector2i.DOWN
	await shot("P00-guard-heroes")
	await dialogue_shot("P00-guard-dialogue","教团守卫","这里刚收完日光。请沿着广场正线走。")
	await dialogue_shot("P00-hunapu-dialogue","胡纳普","……艾琳？把绳子解开。")
	await dialogue_shot("P00-eileen-dialogue","艾琳","胡纳普，退开。")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"input-walk/"))
	ui.hub_controller.clock=0;ui.instant_mode=false
	var start_cell=ui.game.hub_position
	var key=InputEventKey.new();key.physical_keycode=KEY_RIGHT;key.pressed=true;ui._input(key)
	for tick in range(32):
		ui.hub_controller.process(1.0/60.0988);ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png(OUT+"input-walk/"+str(tick).pad_zeros(3)+".png")
	key=InputEventKey.new();key.physical_keycode=KEY_RIGHT;key.pressed=false;ui._input(key)
	if ui.game.hub_position.x<=start_cell.x:errors.append("Normal direction input did not walk")
	ui.game.hub_position=start_cell;ui.hub_controller.render_position=Vector2(start_cell)*16
	for f in [0,1,2,3,4,5]:
		ui.hub_controller.facing=Vector2i.DOWN if f<2 else Vector2i.UP if f<4 else Vector2i.RIGHT;ui.hub_controller.motion_left=ui.hub_controller.STEP*.5;ui.hub_controller.clock=(f%2*16+.5)/60.0988
		await shot("hunapu-story-walk-"+str(f))
		var art=Party.sprite("hub",ui.game.roster.hunapu,1);await sprite_check(art,f,ui.hub_controller.render_position+ui.hub_controller.ORIGIN-Vector2(art.tile_origin[0],art.tile_origin[1]))
	ui.hub_controller.motion_left=0;ui.hub_controller.enter_room("H01");ui.game.hub_position=Vector2i(6,5);await shot("H01-daan-otto")
	await dialogue_shot("H01-daan-dialogue","达恩","我带着弓。先把林路上的人赶出去。")
	await dialogue_shot("H01-otto-dialogue","奥托","我们会一起走。")
	await world_capture("hunapu",1,2,"hunapu")
	ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101);ui.game.story_events.clear();ui.game.flags.erase("active_plot");ui.view="battle";ui.ui_mode="whole_capture";ui._clear_menu();ui.busy=false;ui.notice_time=0;ui.phase_time=0
	var actor=ui.game.find_unit("hunapu");ui._focus_battle(ui.game.pos(actor),true);ui.game.cursor=ui.game.pos(actor);await shot("M11-hunapu-idle")
	ui.moving_id="hunapu";ui.moving_position=Vector2(ui.game.pos(actor))*16
	for f in [0,1,2,3,4,5]:
		ui.moving_direction=Vector2i.DOWN if f<2 else Vector2i.UP if f<4 else Vector2i.RIGHT;ui.moving_frame=f%2
		await shot("M11-hunapu-walk-"+str(f));var art=ui._map_unit_sprite(actor)
		await sprite_check(art,f,ui.moving_position-ui.battle_camera-Vector2(art.tile_origin[0],art.tile_origin[1]))
	ui.moving_id=""
	ui.game.new_game();ui.game.world_node=int(ui.game.stages[111].node);ui.game.start_battle(111);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.busy=false;ui._focus_battle(ui.game.pos(ui.game.find_unit("hunapu")),true);await shot("S11-current-maps")
	ui.game.chapter=2;ui.game.route="celica";ui.game.roster.eileen=ui.game.characters.eileen.duplicate(true);ui.game.party=["eileen"]
	ui.hub_controller.enter_room("H21");ui.game.hub_position=Vector2i(6,4);ui.hub_controller.render_position=Vector2(96,64);ui.hub_controller.facing=Vector2i.DOWN;await shot("eileen-story")
	await world_capture("eileen",2,17,"eileen")
	var sea=Vector2i.ZERO
	for y in range(ui.world.height):
		for x in range(ui.world.width):
			if x>30 and y>45 and ui.world.ground[y][x]=="sea":sea=Vector2i(x,y);break
		if sea!=Vector2i.ZERO:break
	ui.world_actor=Vector2(sea)*16;ui.world_facing=Vector2i.DOWN;ui.world_path=[];await shot("eileen-world-sea")
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"pixel_checks":pixel_checks,"errors":errors,"version":ProjectSettings.get_setting("application/config/version")},"  "));f.close()
	print("MAP_IDENTITY_VISUAL ",shots.size()," captures, ",pixel_checks.size()," native pixel checks; errors ",errors)
	ui.hub_controller.dispose();ui.hub_controller=null;viewport.remove_child(ui);ui.free();ui=null;viewport.queue_free();viewport=null;await process_frame
	call_deferred("quit",0 if errors.is_empty()else 1)
