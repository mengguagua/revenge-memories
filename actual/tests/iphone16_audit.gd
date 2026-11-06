extends SceneTree
## Incremental phone QA: real touch routing, current text and changed menus only.
const OUT="res://reports/iphone16-audit-20261024/"
const CACHE="/private/tmp/revenge-iphone16-audit-20261024/"
var phone
var ui
var screen
var checks=[]
var errors=[]
var pages=[]
var shots=[]
var geometry=[]
var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func point(key:int)->Vector2:
	for b in phone.buttons:
		if int(b.key)==key:return phone.safe_area.position+b.rect.get_center()*phone.pixel_scale
	return Vector2.ZERO
func touch_at(p:Vector2):
	var e=InputEventScreenTouch.new();e.index=71;e.position=p;e.pressed=true;phone._input(e)
	e=InputEventScreenTouch.new();e.index=71;e.position=p;e.pressed=false;phone._input(e)
func tap(key:int):touch_at(point(key))
func content_tap(p:Vector2):touch_at(phone.game_rect.position+(p+ui._canvas_offset())*phone.pixel_scale)
func visible_selection()->bool:return ui.menu_selected>=ui.menu_scroll and ui.menu_selected<ui.menu_scroll+ui._menu_capacity()
func load_battle(source:String)->bool:
	var f=FileAccess.open(CACHE+"working.json",FileAccess.WRITE);f.store_buffer(FileAccess.get_file_as_bytes(source));f.close()
	ui.game.save_path=CACHE+"working.json"
	if not ui.game.load_game():return false
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0;ui.game.story_events.clear();ui._clear_menu()
	ui._focus_battle(ui.game.cursor,true);phone._sync_controls()
	return true
func frame(label:String,photo:bool=false):
	phone._sync_controls();phone.queue_redraw();ui.queue_redraw()
	for i in range(3):await process_frame
	if visual:await RenderingServer.frame_post_draw
	check(phone.layout_errors.is_empty(),label+" control material/text safe area")
	check(ui.layout_errors.is_empty(),label+" game content safe area")
	var audit=ui.equipment_screen.audit.duplicate(true) if ui.equipment_screen.active() else ui.journey.audit.duplicate(true) if ui.view in ["title","journal","journal_confirm"] else ui.text_checks.duplicate(true)
	pages.append({"label":label,"view":ui.view,"audit":audit,"errors":phone.layout_errors.duplicate()+ui.layout_errors.duplicate()})
	if visual and photo:
		var path=OUT+label+".png";screen.get_texture().get_image().save_png(path)
		shots.append({"path":path,"size":[screen.size.x,screen.size.y],"logical_size":phone.game_view.size_2d_override,"errors":phone.layout_errors.duplicate()+ui.layout_errors.duplicate()})
func open_equipment(id:int,member:String):
	ui.view="world";ui.game.mode="world";ui._clear_menu();ui.game.convoy[ui.game.route]=[id]
	ui._camp_action("withdraw_item:0");ui.equipment_screen.selected=ui.equipment_screen.members.find(member)
	ui.equipment_screen.accept();phone._sync_controls()
func run():
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT));DirAccess.make_dir_recursive_absolute(CACHE+"slots")
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.game.slot_directory=CACHE+"slots";ui.game.save_path=CACHE+"working.json";ui.journey.refresh()
	# iPhone 16: 2556 x 1179 physical pixels, 3 physical pixels per UIKit point.
	# Safe-area fixture comes from the existing device screenshot report.
	for safe in [Rect2(177,0,2202,1116)]:
		phone.safe_area_override=safe;phone._layout()
		check(phone.game_view.size_2d_override==Vector2i(364,240) and phone.pixel_scale==4,"iPhone16 safe viewport stays364x240 at4x")
		for view in ["world","battle","combat","overview"]:
			ui.view=view;phone._sync_controls()
			for b in phone.buttons:
				var physical=Rect2(phone.safe_area.position+b.hit_rect.position*phone.pixel_scale,b.hit_rect.size*phone.pixel_scale)
				check(phone.safe_area.encloses(physical),view+" touch target stays within notch/home-indicator safe area "+str(b.key))
				check(not physical.intersects(phone.game_rect),view+" controls remain outside gameplay "+str(b.key))
				check(physical.size.x/3>=44 and physical.size.y/3>=44,view+" iPhone16 rail touch target at least44pt "+str(b.key))
		geometry.append({"screen":[2556,1179],"safe_area":safe,"logical":phone.game_view.size_2d_override,"game_rect":phone.game_rect,"physical_pixels_per_point":3})
	# The app declares sensor-landscape; no supported portrait gameplay is claimed.
	check(int(ProjectSettings.get_setting("display/window/handheld/orientation"))==4,"phone presentation is sensor-landscape, not a portrait layout")
	ui.view="title";phone._sync_controls();await frame("title-mobile-hints")
	check(ui.journey.art.control_hint().contains("确认") and not ui.journey.art.control_hint().contains("Z"),"mobile homepage/records describe on-screen controls")
	check(load_battle("res://reports/full-playtest-20261023/ch5/current/current-J54-deployment.json"),"current final-battle checkpoint copy loads")
	for id in ["hunapu","eileen"]:
		ui.status_id=id;ui.ui_mode="status"
		check(ui.game.HeroProfessions.advanced(ui.game.find_unit(id)),"current checkpoint has advanced hero "+id)
		await frame("battle-advanced-status-"+id)
	var hero=ui.game.find_unit("hunapu");var boss=ui.game.find_unit(str(ui.game.battle_data.boss_id))
	hero.position=[8,11];boss.position=[8,10]
	ui.game.selected_id=hero.id;ui.game.cursor=ui.game.pos(boss);ui.target_ids=[boss.id];ui.target_index=0;ui.ui_mode="target"
	ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(128,120)
	await frame("new-hero-final-boss-forecast")
	check(not ui.battle_preview_audit.is_empty(),"current364px phone renders real final-boss forecast")
	ui.ui_mode="inspect";ui.game.selected_id=""
	tap(KEY_S)
	check(ui.menu_items.size()>5 and ui._menu_capacity()>=ui.menu_items.size(),"ordinary phone battle menu fits on one compact page")
	check(ui._visible_native_rect().grow(-8).encloses(ui._menu_rect()),"tall battle menu stays within native safe canvas")
	for slot in range(ui._menu_capacity()):
		var row=ui._menu_row_rect(slot)
		check(row.size.y==20,"compact battle row is20 logical pixels "+str(slot))
		check(ui._menu_pointer_index(row.get_center())==slot,"row tap resolves actual visible row "+str(slot))
	for step in [-1,1]:
		check(ui._menu_page_arrow_rect(step).size.x>=24 and ui._menu_page_arrow_rect(step).size.y>=20,"overflow pager keeps a distinct compact target "+str(step))
	for i in range(ui.menu_items.size()-1):tap(KEY_DOWN);check(visible_selection(),"battle rail selection scrolls into view "+str(i))
	check(ui.menu_actions[ui.menu_selected]=="new:battle_title","last battle menu action reachable using phone rail")
	await frame("01-final-battle-menu",true)
	var before=ui.game.units.duplicate(true)
	content_tap(ui._menu_rect().position+Vector2(3,3))
	check(ui.view=="battle" and not ui.menu_items.is_empty() and ui.game.units==before,"frame tap cannot select or mutate battle")
	check(ui._menu_pointer_index(ui._menu_rect().position+Vector2(3,3))==-1,"menu frame tap cannot confirm hidden item")
	while ui.menu_actions[ui.menu_selected]!="new:goal":tap(KEY_DOWN)
	tap(KEY_Z)
	check(ui.view=="plot","phone menu enters current objective guidance")
	for i in range(100):
		if ui.view!="plot":break
		ui.dialogue_reveal=99999
		var text=str(ui.plot_pages[ui.plot_index].text)
		check(not text.contains("S菜单"),"phone goal page uses on-screen Menu label "+str(i))
		await frame("goal-page-"+str(i),i==0)
		tap(KEY_Z)
	check(ui.view=="battle","all goal pages dismiss back to same battle")
	# Actual hero professions and eight newly added armament/accessory descriptions.
	ui.game.new_game();ui.game.save_path=CACHE+"working.json";ui.game.mode="world";ui.view="world"
	ui.game.cleared_stages.append(112);ui.game.flags.clinic_staffed=true # Complete clinic recruitment prerequisites in this fixture.
	for id in ["fula","lena","lance","beck","hervi"]:ui.game.recruit(id)
	ui.game.HeroProfessions.apply(ui.game.roster.hunapu,true)
	ui.status_id="hunapu";ui.view="camp_status";ui.camp_context="world";await frame("promoted-hunapu-status")
	ui.view="world";ui._camp_members("status");phone._sync_controls()
	for i in range(ui.menu_items.size()-1):tap(KEY_DOWN);check(visible_selection(),"eight-member roster scrolls into view "+str(i))
	await frame("long-profession-roster")
	ui.view="hub";ui.hub_controller.enter_room("P00",false,false);ui.busy=false;ui.hub_controller.motion_left=0
	ui._camp_members("status")
	for i in range(ui.menu_items.size()-1):tap(KEY_DOWN);check(visible_selection(),"hub roster scrolls into view "+str(i))
	check(ui.menu_selected==ui.menu_items.size()-1,"hub direction path reaches final member")
	var ids=ui.Items.armaments().items.keys().map(func(id):return int(id));ids.append_array([53,55])
	for item in ids:
		open_equipment(int(item),"hunapu");await frame("equipment-"+str(item)+"-comparison")
		tap(KEY_TAB);check(ui.equipment_screen.more,"phone Status control opens equipment details "+str(item))
		var count=ui.equipment_screen.details_page_count()
		for page in range(count):
			check(ui.equipment_screen.details_page==page,"all special-effect pages reachable "+str(item)+"/"+str(page))
			await frame("equipment-"+str(item)+"-details-"+str(page),int(item)==55 and page==0)
			if page+1<count:tap(KEY_DOWN)
		tap(KEY_X);check(ui.view=="equipment_members","phone Back returns from comparison "+str(item))
		await frame("equipment-"+str(item)+"-members")
	# Exercise a tall menu through the hub touch router, then verify desktop geometry is unchanged.
	ui.view="world";ui._open_menu("probe",["一","二","三","四","五","六","七","八","九","十","十一"],range(11),Vector2(64,32))
	ui.set_meta("phone",false)
	check(ui._menu_capacity()==10 and ui._menu_row_height()==16,"desktop keeps original10-row16px layout")
	check(ui._menu_rect().size==Vector2(120,204),"desktop eleven-item menu retains original120x204 dimensions")
	ui.set_meta("phone",true);ui._clear_menu()
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"geometry":geometry,"pages":pages,"shots":shots,"background_render":visual,"device_touch_playtested":false,"user_saves_touched":false,"scope":"Incremental iPhone16 UI audit only; current checkpoint copies; no campaign replay; desktop10/22 screenshots not repeated."}
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "logic-checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("IPHONE16_AUDIT ",checks.size()," checks; ",pages.size()," pages; errors: ",errors)
	phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
