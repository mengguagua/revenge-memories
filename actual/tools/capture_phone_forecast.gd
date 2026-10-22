extends SceneTree
const OUT="res://reports/iphone-layout-20261022/"
var viewport
var ui
var shots=[]
var errors=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var audit=ui.battle_preview_audit.duplicate(true)
	var bars=ui.health_checks.filter(func(row):return row.get("forecast",false)).duplicate(true)
	var text=ui.text_checks.filter(func(row):return row.get("native_digits",false)).duplicate(true)
	var issues=ui.layout_errors.duplicate()
	if not audit.get("valid",false):issues.append("preview not placed")
	if bars.size()!=2:issues.append("both HP bars required")
	elif bars[0].cell_size!=bars[1].cell_size:issues.append("HP cells differ across opponents")
	if audit.get("combatants_protected",false):
		for actor in audit.combatants:
			if audit.panel.intersects(actor):issues.append("forecast covers a protected combatant")
	elif int(viewport.size_2d_override.x)>=406:issues.append("phone forecast failed to clear both combatants")
	for line in text:
		if line.font_px!=12:issues.append("small font in forecast")
		for bar in bars:
			if line.bounds.intersects(bar.bounds):issues.append("text intersects HP bar: "+line.text)
	for i in range(text.size()):
		for j in range(i):
			if text[i].bounds.intersects(text[j].bounds):issues.append("text lines overlap")
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	shots.append({"name":name,"size":[viewport.size.x,viewport.size.y],"preview":audit,"health":bars,"text":text,"errors":issues})
	for issue in issues:errors.append(name+": "+str(issue))
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.set_meta("phone",true);ui.game.slot_directory="/private/tmp/forecast-unused-records";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/forecast-unused.json";ui.game.world_node=2;ui.game.start_battle(101);ui.game.story_events.clear()
	ui._clear_menu();ui.notice_time=0;ui.phase_time=0;ui.busy=false;ui.batch_running=false;ui.ui_mode="target";ui.view="battle"
	var hero=ui.game.find_unit("hunapu");var enemy=ui.game.find_unit("M11_e1");var hero_class=int(hero.class_id)
	enemy.max_hp=13;enemy.hp=13
	hero.position=[8,11];enemy.position=[8,10];ui.game.selected_id="hunapu";ui.target_ids=[enemy.id];ui.target_index=0;ui.game.cursor=ui.game.pos(enemy)
	for width in [406,256]:
		viewport.size=Vector2i(width*4,960);viewport.size_2d_override=Vector2i(width,240)
		for target_y in [56,120,184]:
			ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(128,target_y)
			await shot("forecast-"+str(width)+"-target-"+str(target_y))
		enemy.max_hp=255;enemy.hp=183
		ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(128,122)
		await shot("forecast-"+str(width)+"-large-hp")
		enemy.max_hp=13;enemy.hp=13;hero.position=[8,12];hero.class_id=12;hero.item_id=64
		await shot("forecast-"+str(width)+"-no-counter")
		hero.position=[8,11];hero.class_id=15;hero.weapon_index=34;enemy.max_hp=255;enemy.hp=255;enemy.resistance=0
		await shot("forecast-"+str(width)+"-three-digit-damage")
		hero.class_id=hero_class;hero.erase("weapon_index");hero.item_id=59;enemy.max_hp=13;enemy.hp=13
		hero.position=[6,12];hero.class_id=12;hero.item_id=20
		if not ui.Rules.can_attack(hero,4):errors.append("ranged preview fixture must use a legal four-cell attack")
		ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(130,118)
		await shot("forecast-"+str(width)+"-separated-ranged")
		hero.position=[8,11];hero.class_id=hero_class;hero.item_id=59
	var f=FileAccess.open(OUT+"forecast-visual.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"background_guard":true,"visible_windows":false,"fixture":true,"user_saves_touched":false},"  "));f.close()
	print("PHONE_FORECAST_VISUAL ",shots.size()," screenshots; errors: ",errors)
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
