extends SceneTree
## Independent phone HUD geometry and real battle-menu save/resume checks.
const State=preload("res://core/game_state.gd")
const OUT="res://reports/iphone-layout-20261022/phone-hud-menu-checks.json"
const CACHE="/private/tmp/revenge-phone-hud-menu-20261022/"
var ui
var viewport
var checks=[]
var errors=[]
var probe_count=0
var room_results=[]
var representative=[]

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func key(code:int):
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true;ui._input(event)
	event=InputEventKey.new();event.physical_keycode=code;event.pressed=false;ui._input(event)
func normal(value):return JSON.parse_string(JSON.stringify(value))
func stance(cell:Vector2i,facing:Vector2i):
	ui._clear_menu()
	ui.game.hub_position=cell;ui.hub_controller.render_position=Vector2(cell)*16
	ui.hub_controller.motion_left=0.0;ui.hub_controller.facing=facing
	ui.notice_time=0.0;ui.held_direction=Vector2i.ZERO
func reachable_cells()->Array:
	var queue=[ui.game.hub_position];var visited={ui.game.hub_position:true};var index=0
	while index<queue.size():
		var at:Vector2i=queue[index];index+=1
		for move in [[Vector2i.UP,KEY_UP],[Vector2i.DOWN,KEY_DOWN],[Vector2i.LEFT,KEY_LEFT],[Vector2i.RIGHT,KEY_RIGHT]]:
			stance(at,Vector2i.UP);key(move[1])
			var next:Vector2i=ui.game.hub_position
			if next!=at and not visited.has(next):visited[next]=true;queue.append(next)
	return queue
func sprite_bounds(sprite:Dictionary,at:Vector2)->Rect2:
	# Follow actual _draw_frame dimensions, independently of caption exclusions.
	var size=Vector2(sprite.frame_size[0],sprite.frame_size[1])/maxf(1.0,float(sprite.get("native_density",1)))
	return Rect2((at-Vector2(sprite.tile_origin[0],sprite.tile_origin[1])).round(),size)
func actual_actor_rects()->Array:
	var hub=ui.hub_controller;var shapes=[]
	var arrow=ui._tex(ui.cursors.arrows.down.path).get_size()
	for object in hub.objects:
		var at=hub.ORIGIN+Vector2(object.position[0],object.position[1])*16
		if object.sprite=="actor":
			var sprite=ui._party_hub_sprite(object,ui.graphics.village_sprites.get(str(int(object.source)),ui.graphics.village_sprites["1"]))
			shapes.append({"name":str(object.name),"rect":sprite_bounds(sprite,at).grow(2)})
		else:
			var texture=ui._tex(str(object.get("sprite_path","res://assets/battle_tiles/modules/"+str(object.sprite)+".png")))
			shapes.append({"name":str(object.name),"rect":Rect2(at-Vector2(0,texture.get_height()-16),texture.get_size()).grow(2)})
		if ui.game.hub_position+hub.facing==Vector2i(object.position[0],object.position[1]):
			shapes.append({"name":"interaction arrow "+str(object.name),"rect":Rect2((at+Vector2(4,-8)).round(),arrow)})
	var hero=ui._personal_hub_sprite(ui.graphics.village_sprites["2" if ui.game.route=="celica" else "1"])
	var body=sprite_bounds(hero,hub.render_position+hub.ORIGIN)
	if hub.motion_left>0.0:body=body.merge(sprite_bounds(hero,hub.motion_origin+hub.ORIGIN)).merge(sprite_bounds(hero,hub.motion_target+hub.ORIGIN))
	shapes.append({"name":"hero and movement sweep","rect":body.grow(2)})
	shapes.append({"name":"exit arrow","rect":Rect2(hub.ORIGIN+Vector2(6,8)*16+Vector2(4,-2),arrow)})
	return shapes
func audit_caption(label:String,record:bool=false)->bool:
	ui.presentation_audit.erase("hub_caption");ui.queue_redraw()
	for i in range(2):await process_frame
	probe_count+=1
	var caption:Rect2=ui.presentation_audit.get("hub_caption",Rect2())
	var failures=[]
	if not caption.has_area() or not ui._visible_native_rect().grow(-8).encloses(caption):failures.append("caption outside safe canvas or absent")
	var actors=actual_actor_rects()
	for actor in actors:
		if caption.intersects(actor.rect):failures.append("caption covers "+str(actor.name))
	for error in ui.layout_errors:failures.append(str(error))
	if not failures.is_empty():errors.append({"probe":label,"caption":str(caption),"failures":failures})
	if record:representative.append({"label":label,"caption":str(caption),"actors":actors,"errors":failures,"texts":ui.text_checks.duplicate(true)})
	return failures.is_empty()

func run():
	DirAccess.make_dir_recursive_absolute(CACHE)
	viewport=SubViewport.new();viewport.size=Vector2i(406,240);root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.set_meta("phone",true);ui.game.slot_directory=CACHE;viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.busy=false
	ui.game.new_game();ui.game.save_path=CACHE+"hub-working.json"
	for width in [256,406,426]:
		viewport.size=Vector2i(width,240)
		for room in ["P00","H09"]:
			ui.hub_controller.enter_room(room,false,false)
			var spawn=ui.game.hub_position
			check(await audit_caption(str(width)+"/"+room+"/spawn",true),"unobstructed spawn caption "+str(width)+"/"+room)
			var cells=reachable_cells();var start=probe_count;var failures=errors.size()
			check(cells.size()>30,"actual movement reaches room floor "+str(width)+"/"+room)
			for cell in cells:
				for face in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
					stance(cell,face)
					await audit_caption(str(width)+"/"+room+"/"+str(cell)+"/"+str(face))
			check(errors.size()==failures,"all reachable standing/facing states avoid actors and markers "+str(width)+"/"+room)
			room_results.append({"width":width,"room":room,"reachable_cells":cells.size(),"probes":probe_count-start,"passed":errors.size()==failures})
			stance(spawn,Vector2i.UP)
			if room=="P00":
				for i in range(4):key(KEY_UP)
				key(KEY_RIGHT);key(KEY_UP)
				check(ui.game.hub_position==Vector2i(7,3) and ui.hub_controller.facing==Vector2i.UP,"real input walks beside Helan "+str(width))
				check(await audit_caption(str(width)+"/P00/Helan",true),"shortened Helan interaction caption remains clear "+str(width))
				check(ui.text_checks.any(func(t):return str(t.text).contains("确认:赫兰")),"nearby character prompt names Helan "+str(width))
				ui.instant_mode=false;key(KEY_LEFT)
				check(ui.hub_controller.motion_left>0,"real movement starts an interpolated step "+str(width))
				ui.hub_controller.process(ui.hub_controller.STEP/2.0)
				check(await audit_caption(str(width)+"/P00/moving",true),"caption avoids entire moving hero sweep "+str(width))
				ui.hub_controller.process(ui.hub_controller.STEP);ui.instant_mode=true
	# Battle return must preserve the current checkpoint, not retry the battle.
	ui.game.new_game();ui.game.slot_directory=CACHE;ui.game.world_node=2;ui.game.hub_record="H01"
	check(ui.game.start_battle(101),"battle fixture enters first stage")
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui._clear_menu()
	ui.game.flags.hud_menu_marker="neighbour";check(ui.game.save_to_slot(1),"seed neighbouring independent slot")
	var neighbour=FileAccess.get_file_as_bytes(State.Journals.path_for(CACHE,1))
	check(ui.game.save_to_slot(3),"choose third slot before battle menu")
	ui.game.turn=4;ui.game.phase="player";ui.game.find_unit("hunapu").hp=16;ui.game.find_unit("daan").acted=true
	ui.game.find_unit("M11_e1").hp=6;ui.game.selected_id="hunapu";ui.game.flags.hud_menu_marker="current"
	var units=normal(ui.game.units);var snapshot=normal(ui.game.battle_start_snapshot);var cleared=ui.game.cleared_stages.duplicate();var rng=ui.game.rng_state
	for width in [256,406,426]:
		viewport.size=Vector2i(width,240);ui._clear_menu();key(KEY_S)
		check(ui.menu_actions.has("new:battle_title") and ui.menu_actions.has("save"),"battle menu exposes save and return separately "+str(width))
		while ui.menu_actions[ui.menu_selected]!="new:battle_title":key(KEY_DOWN)
		ui.queue_redraw();await process_frame;await process_frame
		check(ui.layout_errors.is_empty() and ui.text_checks.any(func(t):return t.text=="保存并返回主菜单"),"selected main-menu entry fits visible battle menu "+str(width))
		key(KEY_X)
	var path=ui.game.save_path;var old=FileAccess.get_file_as_bytes(path)
	key(KEY_S);while ui.menu_actions[ui.menu_selected]!="new:battle_title":key(KEY_DOWN)
	key(KEY_Z)
	check(ui.view=="title" and ui.game.mode=="battle" and ui.game.active_slot==3 and ui.game.save_path==path,"successful save returns to title and retains active battle slot")
	var saved=State.read_json(path)
	check(int(saved.turn)==4 and saved.phase=="player" and saved.units==units and saved.battle_start_snapshot==snapshot and saved.cleared_stages==normal(cleared),"saved battle retains turn wounds actions and retry snapshot")
	check(FileAccess.get_file_as_bytes(State.Journals.path_for(CACHE,1))==neighbour,"return-to-title does not modify another record")
	ui.title_selected=1;key(KEY_Z);ui.journey.selected=2;key(KEY_Z)
	for i in range(3):await process_frame
	check(ui.view=="battle" and ui.game.turn==4 and ui.game.phase=="player" and ui.game.active_slot==3,"continue returns to exact saved turn in selected slot")
	check(normal(ui.game.units)==units and normal(ui.game.battle_start_snapshot)==snapshot and ui.game.rng_state==rng,"continue preserves wounds acted flags positions and random state without retry")
	old=FileAccess.get_file_as_bytes(path);ui.game.save_path=CACHE+"missing-parent/failed.json"
	ui._clear_menu();ui.ui_mode="inspect";key(KEY_S)
	while ui.menu_actions[ui.menu_selected]!="new:battle_title":key(KEY_DOWN)
	key(KEY_Z)
	check(ui.view=="battle" and ui.game.mode=="battle" and ui.notice.contains("保存失败"),"failed save stays in battle with visible feedback")
	check(normal(ui.game.units)==units and ui.game.turn==4 and ui.game.active_slot==3 and FileAccess.get_file_as_bytes(path)==old,"failed return leaves live battle and prior checkpoint intact")
	check(FileAccess.get_file_as_bytes(State.Journals.path_for(CACHE,1))==neighbour,"failure also preserves neighbouring record")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT.get_base_dir()))
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"caption_probes":probe_count,"rooms":room_results,"representative":representative,"actual_keyboard_input":true,"user_saves_touched":false,"independent_actual_sprite_bounds":true},"  "));f.close()
	print("PHONE_HUD_MENU ",checks.size()," checks; caption probes ",probe_count,"; errors ",errors.size())
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
