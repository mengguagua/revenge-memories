extends SceneTree
## Explicit renderer fixtures, separate from the two keyboard play rounds.
const Art=preload("res://core/hunapu_sprites.gd")
const OUT="res://reports/clarity-0.5.2/visual/"
var ui
var viewport
var records=[]
var failures=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func capture(label: String,sprite: Dictionary,frame: int,at: Vector2,flip: bool=false):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var image=viewport.get_texture().get_image()
	var source=ui._tex(sprite.path).get_image().get_region(Rect2i(frame*int(sprite.frame_size[0]),0,int(sprite.frame_size[0]),int(sprite.frame_size[1])))
	if flip:source.flip_x()
	var origin=Vector2i(at.round()+ui._canvas_offset());var compared=0;var differences=0
	for y in range(source.get_height()):
		for x in range(source.get_width()):
			var expected=source.get_pixel(x,y)
			if expected.a!=1:continue
			var native_point=at.round()+Vector2(x,y)
			if ui.view=="combat" and (native_point.x<0 or native_point.x>=256 or native_point.y<0 or native_point.y>=128):continue
			compared+=1
			var actual=image.get_pixelv(origin+Vector2i(x,y))
			if absf(actual.r-expected.r)>.005 or absf(actual.g-expected.g)>.005 or absf(actual.b-expected.b)>.005:differences+=1
	var path=OUT+label+".png";image.save_png(path)
	var record={"path":path,"frame":frame,"flip":flip,"opaque_pixels":compared,"different_pixels":differences,"layout_errors":ui.layout_errors.duplicate(),"fixture":true}
	records.append(record)
	if differences>0 or compared==0 or not ui.layout_errors.is_empty():failures.append(record)
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="res://reports/clarity-0.5.2/visual/working.json"
	ui.game.new_game();ui.hub_controller.enter_room("H01");ui.game.hub_position=Vector2i(6,5)
	if ui.graphics.village_sprites["1"].path==Art.sprite("hub").path:failures.append("Personal hub art changed shared NPC source")
	var original_hub=ui.graphics.village_sprites["1"]
	ui.game.route="celica"
	if ui._personal_hub_sprite(original_hub)!=original_hub:failures.append("East-route hub override")
	ui.game.route="alm";ui.game.roster.hunapu.promoted=true
	if ui._personal_hub_sprite(original_hub)!=original_hub:failures.append("Promoted hub fallback")
	ui.game.roster.hunapu.erase("promoted")
	var hub=ui.hub_controller;hub.render_position=Vector2(ui.game.hub_position)*16;hub.motion_left=.1
	for f in range(6):
		hub.facing=Vector2i.DOWN if f<2 else Vector2i.UP if f<4 else Vector2i.RIGHT;hub.clock=(16.1 if f%2 else 0.0)/60.0988
		await capture("hub-"+str(f),Art.sprite("hub"),f,hub.render_position+Vector2(16,8)-Vector2(8,8))
	hub.facing=Vector2i.LEFT;hub.clock=0
	await capture("hub-left",Art.sprite("hub"),4,hub.render_position+Vector2(16,8)-Vector2(8,8),true)
	ui.game.save_path="res://reports/campaign/natural-M11-deployment-save.json";var loaded=ui.game.load_game();ui.game.save_path="res://reports/clarity-0.5.2/visual/working.json"
	if not loaded:failures.append("Historical M11 fixture fails to load");quit(1);return
	ui.view="battle";ui.ui_mode="whole_capture";ui.phase_time=0;ui.notice_time=0;ui.busy=false;ui._clear_menu()
	var hero=ui.game.find_unit("hunapu");ui._focus_battle(ui.game.pos(hero),true)
	ui.moving_id="hunapu";ui.moving_position=Vector2(ui.game.pos(hero))*16;hero.acted=false
	for f in range(6):
		ui.moving_direction=Vector2i.DOWN if f<2 else Vector2i.UP if f<4 else Vector2i.RIGHT;ui.moving_frame=f%2
		await capture("map-"+str(f),ui._map_unit_sprite(hero),f,ui._battle_cell_screen(ui.game.pos(hero))-Vector2(4,4)+ui.map_offset)
	ui.moving_direction=Vector2i.LEFT;ui.moving_frame=0
	await capture("map-left",ui._map_unit_sprite(hero),4,ui._battle_cell_screen(ui.game.pos(hero))-Vector2(4,4)+ui.map_offset,true)
	hero.acted=true;ui.moving_id=""
	await capture("map-rest",ui._map_unit_sprite(hero),0,ui._battle_cell_screen(ui.game.pos(hero))-Vector2(4,4)+ui.map_offset)
	hero.acted=false
	var foe=ui.game.living("enemy")[0];ui.combat={"attacker":"hunapu","defender":foe.id,"distance":1,"initiative_side":"player"}
	ui.view="combat";ui.combat_message="";ui.combat_shake=0;ui.combat_hit_id="";ui.combat_fades={foe.id:0.0};ui.battle_animation.reset()
	var art=ui._battle_sprite(hero);var at=ui.battle_animation.origin(hero,ui.combat)-Vector2(40,64)
	for f in Art.data().active_battle_frames:
		ui.combat_poses={"hunapu":int(f)};ui.combat_offsets={"hunapu":Vector2.ZERO}
		await capture("battle-"+str(int(f)),art,int(f),at)
	for width in [256,384,560]:
		viewport.size=Vector2i(width,240);await process_frame
		for phase in ["present","memory","victory"]:
			ui.game.flags.erase("korlan_defeated")
			ui.hub_controller.enter_room("P00" if phase=="present" else "H01")
			if phase=="victory":ui.game.flags.korlan_defeated=true
			ui.view="plot";ui.plot_return="hub";ui.plot_pages=[{"speaker":"胡纳普","text":"你先告诉我发生了什么。"}];ui.plot_index=0;ui.dialogue_reveal=999
			var face=ui._speaker_portrait("胡纳普");var layout=ui._plot_layout("胡纳普")
			await capture("portrait-"+phase+"-"+str(width),{"path":face.path,"frame_size":[48,48]},0,layout.portrait.position)
	var report={"passed":failures.is_empty(),"background_guard":true,"visible_windows":false,"scope":"Explicit frozen-pose engine renderer fixtures, not natural battles. Opaque sprite RGB compared at native 1:1 screen coordinates; background alpha excluded. Actual text safety checked on every image.","records":records,"failures":failures}
	var file=FileAccess.open(OUT+"pixel-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("HUNAPU_PIXEL_CHECK ",report.passed," poses ",records.size()," failures ",failures)
	ui.hub_controller.dispose();ui.hub_controller=null;viewport.remove_child(ui);ui.free();ui=null
	viewport.queue_free();await process_frame;viewport=null
	quit(0 if failures.is_empty() else 1)
