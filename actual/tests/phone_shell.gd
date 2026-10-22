extends SceneTree
var errors:Array=[]
var labels:Array=[]
var measurements:Array=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	labels.append(label)
	if not ok:errors.append(label);push_error(label)
func key_point(phone,key:int) -> Vector2:
	for button in phone.buttons:
		if int(button.key)==key:return phone.safe_area.position+button.rect.get_center()*phone.pixel_scale
	return Vector2.ZERO
func touch(phone,index:int,point:Vector2,pressed:bool):
	var e=InputEventScreenTouch.new();e.index=index;e.position=point;e.pressed=pressed;phone._input(e)
func drag(phone,index:int,point:Vector2):
	var e=InputEventScreenDrag.new();e.index=index;e.position=point;phone._input(e)
func tap(phone,key:int,index:int=0):
	var point=key_point(phone,key);touch(phone,index,point,true);touch(phone,index,point,false)
func run():
	var viewport=SubViewport.new();viewport.size=Vector2i(2556,1179);root.add_child(viewport)
	var phone=load("res://scenes/phone.tscn").instantiate();viewport.add_child(phone);await process_frame
	var ui=phone.game_ui
	ui.set_process(false);ui.set_physics_process(false)
	ui.game.slot_directory="/private/tmp/revenge-iphone-controls-20261022"
	ui.game.save_path="/private/tmp/revenge-iphone-controls-20261022/unused.json";ui.journey.refresh()
	check(ui.get_meta("phone",false),"phone presentation metadata is set before ready")
	for spec in [[Vector2i(2556,1179),Rect2()],[Vector2i(2556,1179),Rect2(177,0,2202,1116)],[Vector2i(1334,750),Rect2()],[Vector2i(1136,640),Rect2()]]:
		viewport.size=spec[0];phone.safe_area_override=spec[1];phone._layout()
		check(phone.pixel_scale>=1 and phone.game_view.size_2d_override.y==240,"integer native pixel scaling "+str(spec))
		check(phone.safe_area.encloses(phone.game_rect),"game fits safe screen "+str(spec))
		check(phone.game_rect.size==Vector2(phone.game_view.size),"game texture maps 1:1 to physical pixels "+str(spec))
		for i in range(phone.buttons.size()):
			var button=phone.buttons[i];var physical=Rect2(phone.safe_area.position+button.hit_rect.position*phone.pixel_scale,button.hit_rect.size*phone.pixel_scale)
			check(phone.safe_area.encloses(physical),"touch target in safe area "+str(button.key)+str(spec))
			check(not phone.game_rect.intersects(physical),"touch target does not cover gameplay "+str(button.key)+str(spec))
			check(button.hit_rect.size.x>=34 and button.hit_rect.size.y>=36,"touch size "+str(button.key)+str(spec))
			for j in range(i):check(not button.hit_rect.intersects(phone.buttons[j].hit_rect),"separate touch targets "+str(i)+"/"+str(j)+str(spec))
		measurements.append({"screen":spec[0],"safe":phone.safe_area,"logical_game":phone.game_view.size_2d_override,"physical_game":phone.game_rect,"scale":phone.pixel_scale})
		if spec[1].has_area():check(phone.game_view.size_2d_override.x==364,"notch fixture widens game from 406 to364 with a wider left control rail logical pixels")
		elif spec[0]==Vector2i(2556,1179):check(phone.game_view.size_2d_override.x==453,"full iPhone-sized frame widens game from495 to453 with a wider left control rail logical pixels")
		elif spec[0]==Vector2i(1334,750):check(phone.pixel_scale==3,"small landscape retains three-times rendering instead of shrinking to two")
	viewport.size=Vector2i(2556,1179);phone.safe_area_override=Rect2(177,0,2202,1116);phone._layout()
	ui.title_selected=0;tap(phone,KEY_Z)
	check(ui.view=="journal" and ui.journey.intent=="new","screen touch confirm opens slot picker")
	tap(phone,KEY_X);check(ui.view=="title","screen touch back returns from slot picker")
	ui.game.new_game();ui.game.save_path="/private/tmp/revenge-iphone-controls-20261022/unused.json"
	ui.hub_controller.enter_room("P00",false,false);ui.hub_controller.motion_left=0;ui.busy=false
	phone._sync_controls();var start=ui.game.hub_position;var point=key_point(phone,KEY_LEFT)
	touch(phone,1,point,true);var once=ui.game.hub_position
	check(once==start+Vector2i.LEFT,"direction button walks in actual prologue")
	touch(phone,1,point,true);touch(phone,2,point,true)
	check(ui.game.hub_position==once,"duplicate down and second finger never repeat initial movement")
	touch(phone,1,point,false);check(ui.held_direction==Vector2i.LEFT,"lifting one shared direction finger preserves the other")
	touch(phone,2,point,false);check(ui.held_direction==Vector2i.ZERO,"lifting last finger releases walking")
	ui.hub_controller.motion_left=0;tap(phone,KEY_S)
	check(not ui.menu_items.is_empty(),"touch system menu opens")
	var count=ui.menu_items.size();point=key_point(phone,KEY_S)
	touch(phone,3,point,true);drag(phone,3,key_point(phone,KEY_Z));touch(phone,3,key_point(phone,KEY_Z),false)
	check(ui.menu_items.size()==count,"dragging discrete menu touch onto confirm does not select an option")
	tap(phone,KEY_X);check(ui.menu_items.is_empty(),"touch back closes menu")
	ui.game.new_game();ui.game.world_node=2;ui.game.start_battle(101);ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.game.cursor=ui.game.pos(ui.game.find_unit("hunapu"));ui._clear_menu();phone._sync_controls()
	check(key_point(phone,KEY_E)!=Vector2.ZERO,"tactical battle exposes dedicated switch-ally button")
	tap(phone,KEY_E);check(ui.game.unit_at(ui.game.cursor).id=="daan","touch switch selects next ready formal ally")
	ui.game.find_unit("otto").acted=true;tap(phone,KEY_E)
	check(ui.game.unit_at(ui.game.cursor).id=="hunapu","switch skips acted ally and temporary escorts")
	for mode in ["move","target","action"]:
		ui.ui_mode=mode;ui.game.selected_id="hunapu";var cursor=ui.game.cursor;var units=ui.game.units.duplicate(true)
		tap(phone,KEY_E);check(ui.game.cursor==cursor and ui.game.selected_id=="hunapu" and ui.game.units==units,"switch disabled without changing tactical action "+mode)
	ui.ui_mode="status";ui.status_id="hunapu";tap(phone,KEY_E)
	check(ui.status_id=="daan" and ui.ui_mode=="status","switch cycles ally status without closing the status page")
	ui.ui_mode="inspect";ui.game.phase="enemy";var cursor=ui.game.cursor;tap(phone,KEY_E)
	check(ui.game.cursor==cursor,"switch disabled in enemy phase")
	ui.game.phase="player";ui.game.selected_id="";ui._clear_menu();ui.view="combat";phone._sync_controls()
	check(phone.buttons.size()==1 and phone.buttons[0].key==phone.FAST_KEY,"animation replaces inactive controls with dedicated hold-to-speed button")
	point=key_point(phone,phone.FAST_KEY);var battle=ui.game.units.duplicate(true)
	touch(phone,4,point,true);check(ui.touch_fast_forward and is_equal_approx(ui.effective_animation_speed(),3.0),"touch hold requests triple animation speed")
	touch(phone,4,point,true);touch(phone,5,point,true);touch(phone,4,point,false)
	check(ui.touch_fast_forward,"two held speed fingers do not release until last lift")
	touch(phone,5,point,false);check(not ui.touch_fast_forward,"last speed finger lift restores normal speed")
	touch(phone,6,point,true);drag(phone,6,phone.game_rect.get_center())
	check(not ui.touch_fast_forward and ui.game.units==battle and ui.view=="combat","dragging speed finger into gameplay releases speed without a map confirmation")
	drag(phone,6,point);check(ui.touch_fast_forward,"dragging same hold gesture back into speed resumes acceleration")
	ui.view="reward";phone._sync_controls();check(not ui.touch_fast_forward,"scene transition clears held acceleration")
	drag(phone,6,key_point(phone,KEY_Z));check(ui.view=="reward","held animation finger cannot turn into reward confirmation")
	touch(phone,6,point,false);ui.view="combat";phone._sync_controls();point=key_point(phone,phone.FAST_KEY)
	touch(phone,7,point,true);phone._notification(MainLoop.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(not ui.touch_fast_forward and phone.fingers.is_empty() and ui.held_direction==Vector2i.ZERO,"backgrounding releases acceleration and every held input")
	touch(phone,7,point,true);check(ui.touch_fast_forward,"a fresh touch after focus loss is accepted")
	touch(phone,7,point,false);ui.view="battle";phone._sync_controls()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/iphone-refine-20261022"))
	var data={"passed":errors.is_empty(),"checks":labels.size(),"labels":labels,"errors":errors,"measurements":measurements,"real_screen_touch_events":true,"user_saves_touched":false,"scope":"Phone viewport/rails, safe touch regions, actual prologue walk, ally navigation, gesture ownership, hold speed and release"}
	var f=FileAccess.open("res://reports/iphone-refine-20261022/phone-touch-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(data,"  "));f.close()
	print("PHONE_TOUCH ",JSON.stringify({"passed":errors.is_empty(),"checks":labels.size(),"errors":errors}))
	phone.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
