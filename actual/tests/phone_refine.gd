extends SceneTree
const OUT="res://reports/iphone-refine-20261022/"
var checks=[]
var errors=[]
var shots=[]
var phone
var ui
var screen
var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func point(key:int)->Vector2:
	for b in phone.buttons:
		if b.key==key:return phone.safe_area.position+b.rect.get_center()*phone.pixel_scale
	return Vector2.ZERO
func button(key:int)->Dictionary:
	for b in phone.buttons:
		if b.key==key:return b
	return {}
func tap(key:int):
	var p=point(key);phone._finger(90,p,true);phone._finger(90,p,false)
func key(code:int):
	var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e);e=InputEventKey.new();e.physical_keycode=code;e.pressed=false;ui._input(e)
func capture(name:String):
	phone._sync_controls();phone.queue_redraw();ui.queue_redraw()
	for i in range(8):
		phone.queue_redraw();ui.queue_redraw();await process_frame
	if not visual:return
	await RenderingServer.frame_post_draw
	check(phone.layout_errors.is_empty(),name+" control text and touch safe regions")
	check(ui.layout_errors.is_empty(),name+" content text stays inside panels")
	var rendered=screen.get_texture().get_image()
	for code in phone.DIRECTION_KEYS:
		var center=point(code);var has_arrow=false
		for y in range(int(center.y)-12,int(center.y)+12):
			for x in range(int(center.x)-12,int(center.x)+12):
				var color=rendered.get_pixel(x,y)
				if color.r>.85 and color.g>.85 and color.b>.85:has_arrow=true
		check(has_arrow,name+" visible direction arrow "+str(code))
	rendered.save_png(OUT+name+".png")
	shots.append({"file":name+".png","buttons":phone.buttons.duplicate(true),"game_rect":phone.game_rect,"map":ui.overview_audit.duplicate(true),"errors":phone.layout_errors.duplicate()+ui.layout_errors.duplicate()})
func run():
	visual=OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1" and DisplayServer.get_name()!="headless"
	DirAccess.make_dir_recursive_absolute("/private/tmp/revenge-phone-refine")
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.game.slot_directory="/private/tmp/revenge-phone-refine/slots";ui.game.save_path="/private/tmp/revenge-phone-refine/working.json";ui.journey.refresh()
	check(phone.game_view.size_2d_override==Vector2i(364,240) and phone.pixel_scale==4,"iPhone asymmetric rails retain integer 4x display")
	check(phone.game_rect.position.x==642,"content moves right by 176 physical pixels")
	check(button(KEY_LEFT).rect.size==Vector2(36,36),"direction keys enlarged from32x34 to36x36")
	check(button(KEY_RIGHT).rect.position.x-button(KEY_LEFT).rect.end.x==36,"left/right key gap increased from4 to36 logical pixels")
	check(phone._button_at((point(KEY_LEFT)+point(KEY_RIGHT))/2)==0,"center gap is a neutral area and cannot trigger either direction")
	var direction_center=(point(KEY_LEFT)+point(KEY_RIGHT))/2
	for direction in phone.DIRECTION_KEYS:
		check(is_equal_approx(point(direction).distance_to(direction_center),36*phone.pixel_scale),"all four directions equally distant from center "+str(direction))
	var cross=button(KEY_UP).rect.merge(button(KEY_DOWN).rect).merge(button(KEY_LEFT).rect).merge(button(KEY_RIGHT).rect)
	check(cross.size==Vector2(108,108),"equal cross has square108x108 outer bounds")
	await capture("01-title-controls")
	ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0
	ui.game.cursor=ui.game.pos(ui.game.find_unit("hunapu"));ui._focus_battle(ui.game.cursor,true);ui._clear_menu();phone._sync_controls()
	ui.game.turn=12;tap(KEY_S)
	check(not ui.menu_actions.has("save") and not ui.menu_actions.has("new:save"),"battle menu has no independent save action")
	check(ui.menu_actions.count("new:battle_title")==1,"battle menu retains exactly one save-and-return action")
	check(ui.menu_items[ui.menu_actions.find("end_turn")].contains("12"),"opened menu states current turn12")
	await capture("02-battle-turn-menu")
	ui._clear_menu();ui.game.turn=1234;await capture("03-long-turn-number")
	ui.game.turn=12;ui.game.find_unit("hunapu").hp=19;ui.game.find_unit("daan").acted=true
	ui._menu_action("new:battle_title","system")
	check(ui.view=="title" and ui.game.mode=="battle","save-and-return leaves battle checkpoint resumable")
	var state=load("res://core/game_state.gd").new();state.save_path=ui.game.save_path
	check(state.load_game(),"saved battle can be read back")
	check(state.turn==12 and state.find_unit("hunapu").hp==19 and state.find_unit("daan").acted,"return preserves round, injury and action status")
	ui.view="world";ui._clear_menu();ui._open_system_menu()
	check(ui.menu_actions.has("new:save"),"world save entry remains available")
	var saved_bytes=FileAccess.get_file_as_bytes(ui.game.save_path);var world_location=ui.game.world_node
	ui._clear_menu();ui._menu_action("new:overview","world_system");phone._sync_controls()
	check(ui.overview_zoom==1 and not phone._button_enabled(KEY_MINUS),"overview opens1x with zoom-out disabled")
	await capture("04-overview-1x")
	var middle=phone.game_rect.get_center();phone._finger(11,middle,true);phone._finger(11,middle,false)
	check(ui.view=="overview","tapping overview no longer accidentally exits")
	tap(KEY_EQUAL);check(ui.overview_zoom==2,"touch zoom-in advances to2x")
	await capture("05-overview-2x")
	tap(KEY_EQUAL);tap(KEY_EQUAL)
	check(ui.overview_zoom==3 and not phone._button_enabled(KEY_EQUAL),"zoom capped at3x and zoom-in disabled")
	await capture("06-overview-3x")
	phone._finger(21,point(KEY_RIGHT),true);var pressed_center=ui.overview_center;ui._process(.31)
	check(ui.overview_center.x>pressed_center.x,"holding direction continues panning after initial press")
	phone._finger(21,point(KEY_RIGHT),false);pressed_center=ui.overview_center;ui._process(.31)
	check(ui.overview_center==pressed_center,"releasing direction stops map motion")
	var before=ui.overview_center;tap(KEY_RIGHT);tap(KEY_DOWN)
	check(ui.overview_center.x>before.x and ui.overview_center.y>before.y,"direction keys pan enlarged map right and down")
	before=ui.overview_center
	phone._finger(13,middle,true);phone._finger(13,middle+Vector2(120,120),true,true);phone._finger(13,middle+Vector2(120,120),false)
	check(ui.overview_center.x<before.x and ui.overview_center.y<before.y,"map follows finger drag in both axes")
	before=ui.overview_center;phone._finger(14,point(KEY_RIGHT),true);var after_press=ui.overview_center;phone._finger(14,middle,true,true);phone._finger(14,middle,false)
	check(ui.overview_center==after_press,"control-origin drag cannot become a map gesture")
	for delta in [Vector2(-99999,-99999),Vector2(99999,99999),Vector2(99999,-99999),Vector2(-99999,99999)]:
		ui._overview_pan_pixels(delta);var g=ui._overview_geometry()
		check(Rect2(0,0,896,1024).grow(.01).encloses(g.source),"pan cannot leave texture bounds "+str(delta))
		check(g.area.grow(1).encloses(g.dest),"zoomed image cannot overlap footer "+str(delta))
	await capture("07-overview-panned-edge")
	tap(KEY_R);check(ui.overview_zoom==1 and ui.overview_center.is_equal_approx(Vector2(.5,.5)),"reset restores1x centered whole map")
	ui._overview_pan_pixels(Vector2(999,999));check(ui.overview_center.is_equal_approx(Vector2(.5,.5)),"1x map has no unnecessary pan")
	key(KEY_EQUAL);key(KEY_EQUAL);key(KEY_EQUAL);check(ui.overview_zoom==3,"desktop plus respects3x cap")
	key(KEY_MINUS);check(ui.overview_zoom==2,"desktop minus zooms out")
	var mouse=InputEventMouseButton.new();mouse.button_index=MOUSE_BUTTON_WHEEL_UP;mouse.pressed=true;ui._input(mouse);check(ui.overview_zoom==3,"desktop wheel zooms in")
	phone._finger(16,middle,true);phone._notification(MainLoop.NOTIFICATION_APPLICATION_FOCUS_OUT)
	before=ui.overview_center;phone._finger(16,middle+Vector2(100,100),true,true)
	check(ui.overview_center==before and phone.map_contacts.is_empty(),"focus loss cancels map dragging")
	phone._finger(16,middle,false);tap(KEY_X);check(ui.view=="world" and ui.game.world_node==world_location,"back returns to same world location")
	check(FileAccess.get_file_as_bytes(ui.game.save_path)==saved_bytes,"map viewing does not rewrite saved progress")
	ui._menu_action("new:overview","world_system");check(ui.overview_zoom==1,"reopening overview starts whole map")
	for spec in [[Vector2i(1334,750),Rect2()],[Vector2i(1136,640),Rect2()]]:
		screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout();ui._overview_change_zoom(2);ui._overview_pan_pixels(Vector2(-9999,9999))
		await capture("08-small-map-"+str(spec[0].x))
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"shots":shots,"background_render":visual,"actual_device_touch_playtested":false,"user_saves_touched":false}
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "logic-checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("PHONE_REFINE ",checks.size()," checks, errors: ",errors)
	phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
