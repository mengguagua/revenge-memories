extends SceneTree
const OUT="res://reports/iphone-layout-20261022/"
var viewport
var phone
var ui
var shots=[]
var errors=[]
var checks=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func point(key:int) -> Vector2:
	for b in phone.buttons:
		if int(b.key)==key:return phone.safe_area.position+b.hit_rect.get_center()*phone.pixel_scale
	return Vector2.ZERO
func tap(key:int):
	var p=point(key);phone._finger(12,p,true);phone._finger(12,p,false)
func shot(name:String):
	phone._sync_controls();phone.queue_redraw();ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var issues=phone.layout_errors.duplicate()+ui.layout_errors.duplicate()
	var extra={}
	if ui.view=="hub":
		var caption:Rect2=ui.presentation_audit.get("hub_caption",Rect2())
		var protected=ui.presentation_audit.get("hub_protected",[])
		extra={"caption":caption,"protected":protected}
		if not caption.has_area():issues.append("Missing hub guidance")
		for actor in protected:
			if caption.intersects(actor):issues.append("Guidance covers an actor or interaction marker")
	if ui.view=="battle" and ui.ui_mode=="target":
		extra.preview=ui.battle_preview_audit.duplicate(true)
		extra.health=ui.health_checks.filter(func(bar):return bar.get("forecast",false)).duplicate(true)
		if extra.health.size()!=2:issues.append("Missing forecast health bars")
		elif extra.health[0].cell_size!=extra.health[1].cell_size:issues.append("Different forecast HP cell sizes")
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	shots.append({"name":name,"view":ui.view,"size":[viewport.size.x,viewport.size.y],"game_rect":phone.game_rect,"logical":phone.game_view.size_2d_override,"safe":phone.safe_area,"pixel_scale":phone.pixel_scale,"buttons":phone.buttons.duplicate(true),"audit":extra,"errors":issues})
	for issue in issues:errors.append(name+": "+str(issue))
func run():
	viewport=SubViewport.new();viewport.size=Vector2i(2556,1179);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);viewport.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.game.slot_directory="/private/tmp/revenge-iphone-layout-20261022/capture-slots";ui.game.save_path="/private/tmp/revenge-iphone-layout-20261022/capture.json";ui.journey.refresh()
	check(phone.game_view.size_2d_override.x==406 and phone.pixel_scale==4,"iPhone screenshot safe area expands play width from 326 to 406 at 4x")
	ui.game.new_game();ui.hub_controller.enter_room("P00",false,false);ui.game.hub_position=Vector2i(6,7);ui.hub_controller.render_position=Vector2(6,7)*16
	await shot("01-iphone-prologue-arrival")
	ui.game.hub_position=Vector2i(7,3);ui.hub_controller.render_position=Vector2(7,3)*16;ui.hub_controller.facing=Vector2i.UP
	await shot("02-iphone-prologue-near-herlan")
	ui.game.world_node=2;check(ui.game.start_battle(101),"first battle fixture begins")
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
	ui.game.cursor=ui.game.pos(ui.game.find_unit("hunapu"));ui._focus_battle(ui.game.cursor,true)
	await shot("03-iphone-battle-controls")
	var before=ui.game.cursor;tap(KEY_E)
	check(ui.game.cursor!=before,"touch cycle changes to next unacted ally")
	await shot("04-iphone-cycle-ally")
	var hero=ui.game.find_unit("hunapu");var enemy=ui.game.find_unit("M11_e1")
	hero.position=[8,11];enemy.position=[8,10];enemy.hp=18;enemy.max_hp=18
	ui.game.selected_id=hero.id;ui.game.cursor=ui.game.pos(enemy);ui.target_ids=[enemy.id];ui.target_index=0;ui.ui_mode="target"
	ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(128,120)
	await shot("05-iphone-attack-preview")
	ui.view="combat";ui.combat={"attacker":hero.id,"defender":enemy.id,"distance":1,"initiative_side":"player"};ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear()
	ui.battle_animation.reset();ui.battle_animation.active_event={"attacker":hero.id,"defender":enemy.id,"weapon_index":0}
	await shot("06-iphone-combat-speed-control")
	phone._finger(18,point(phone.FAST_KEY),true)
	check(ui.touch_fast_forward and ui.effective_animation_speed()==3.0,"dedicated touch hold really enables combat acceleration")
	await shot("07-iphone-combat-held")
	phone._finger(18,point(phone.FAST_KEY),false)
	check(not ui.touch_fast_forward and ui.effective_animation_speed()==1.0,"releasing touch returns to normal speed")
	ui.view="battle";ui.ui_mode="inspect";ui.game.selected_id="";ui._open_system_menu();ui.menu_selected=ui.menu_actions.find("new:battle_title")
	check(ui.menu_selected>=0,"battle menu exposes save and return to main menu")
	await shot("08-iphone-battle-menu")
	ui._clear_menu();ui._menu_action("new:battle_title","system")
	check(ui.view=="title" and ui.game.mode=="battle","return to main menu preserves battle checkpoint mode")
	ui.elapsed=4;await shot("09-iphone-main-menu")
	viewport.size=Vector2i(1334,750);phone.safe_area_override=Rect2();phone._layout()
	ui.hub_controller.enter_room("P00",false,false);await shot("10-small-phone-prologue")
	var f=FileAccess.open(OUT+"integration-visual.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"shots":shots,"background_guard":true,"visible_windows":false,"fixture":true,"user_saves_touched":false,"iphone_safe_area_inferred_from_supplied_screenshots":true},"  "));f.close()
	print("IPHONE_INTEGRATION ",shots.size()," screenshots; errors: ",errors)
	phone.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
