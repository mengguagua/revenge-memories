extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Info=preload("res://core/spell_info.gd")
const OUT="res://reports/spell-bandits-20261025/"
var checks=[]
var failures=[]
var shots=[]
var cache=""
var visual=false
var ui
var phone
var screen
var presentation_complete=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path=cache+"save.json";g.world_node=int(g.stages[111].node);g.start_battle(111);return g
func domain():
	var g=fresh();var changes=g.EnemyBalance.data().updates[0].stages["111"]
	for id in changes:
		var unit=g.find_unit(id);var expected=changes[id].after
		check(int(unit.strength)==int(expected.strength) and int(unit.speed)==int(expected.speed),"exact requested strength and speed: "+id)
	check(int(g.find_unit("S11_e6").strength)==9 and int(g.find_unit("S11_e6").speed)==3,"S11 archer is unchanged")
	# Revision-1 saves and retry snapshots upgrade in order without changing HP.
	for actors in [g.units,g.battle_start_snapshot.units]:
		for u in actors:
			if not changes.has(str(u.id)):continue
			for field in changes[str(u.id)].before:u[field]=changes[str(u.id)].before[field]
			u.enemy_balance_revision=1
	g.find_unit("S11_boss").hp=11;g.turn=4;g.rng_state=99;var at=g.pos(g.find_unit("S11_boss"))
	check(g.save_game(),"save isolated revision-1 checkpoint")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game(),"revision-1 checkpoint loads")
	var boss=loaded.find_unit("S11_boss")
	check(int(boss.strength)==13 and int(boss.speed)==9 and int(boss.hp)==11 and loaded.pos(boss)==at and loaded.turn==4 and loaded.rng_state==99,"upgrade preserves wounds, position, turn and RNG")
	check(loaded.save_game() and loaded.load_game() and int(loaded.find_unit("S11_boss").strength)==13 and int(loaded.find_unit("S11_boss").speed)==9,"repeat load does not stack bonuses")
	check(loaded.retry_battle() and int(loaded.find_unit("S11_boss").strength)==13 and int(loaded.find_unit("S11_e1").speed)==4,"retry snapshot has current balance exactly once")
	var legacy=loaded.find_unit("S11_e1");legacy.erase("enemy_balance_revision")
	for field in g.EnemyBalance.data().stages["111"].S11_e1.before:legacy[field]=g.EnemyBalance.data().stages["111"].S11_e1.before[field]
	legacy.speed=3;loaded.EnemyBalance.prepare(111,[legacy])
	check(int(legacy.class_id)==14 and int(legacy.strength)==10 and int(legacy.speed)==4,"pre-first-tuning unit receives profession correction then both balance revisions")
	legacy.enemy_balance_revision=1;legacy.strength=19;legacy.speed=12;loaded.EnemyBalance.prepare(111,[legacy])
	check(int(legacy.strength)==19 and int(legacy.speed)==12,"unknown custom stats are preserved")
	# Current-position spell reach is independent of the movement envelope.
	var mage=g._initial_character("hervi");mage.position=[10,10];mage.item_id=0;mage.weapon_index=27
	var target=g.find_unit("S11_e1").duplicate(true);target.position=[12,10];g.units=[mage,target]
	check(Rules.attack_range(mage)==Vector2i(1,2) and g.targets(mage).has(target) and not g.plan_combat("hervi",str(target.id)).is_empty(),"wind at straight-line distance two is targetable and produces a combat plan")
	target.position=[11,11];check(g.targets(mage).has(target),"diagonal one plus one equals distance two")
	target.position=[13,10];check(g.targets(mage).is_empty(),"two empty intervening cells are distance three and outside wind reach")
	var before=mage.duplicate(true);var info=Info.describe(g,mage,27);var cells=Info.attack_cells(g,mage,27)
	check(str(info.range).contains("1～2") and cells.has(Vector2i(12,10)) and cells.has(Vector2i(11,11)) and not cells.has(Vector2i(13,10)) and mage==before,"description and green spell overlay use actual combat reach without mutation")
	mage.item_id=57;check(Info.attack_cells(g,mage,27).has(Vector2i(15,10)) and str(Info.describe(g,mage,27).range).contains("1～5"),"range accessory is reflected in description and overlay")
	mage.item_id=66;check(Info.describe(g,mage,27).stats.contains("威力"+str(Rules.Items.weapon_profile(mage,27).might)),"legal focus is reflected in the described might")
	mage.hp=3;check(Info.attack_cells(g,mage,27).is_empty() and str(Info.describe(g,mage,27).availability).contains("高于3"),"HP equal to wind cost cannot cast and explains the strict HP requirement")
	check(str(Info.describe(g,mage,40).effect).contains("恢复") and str(Info.describe(g,mage,40).range).contains("1格") and Info.attack_cells(g,mage,40).is_empty(),"healing has a support effect and adjacent range without an attack overlay")
func key(code:int):
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true;ui._input(event);event=InputEventKey.new();event.physical_keycode=code;event.pressed=false;ui._input(event)
func frame(name:String,capture:bool=true):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
	for i in range(4):await process_frame
	if not visual:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text and controls remain in safe bounds: "+str(ui.layout_errors))
	if capture and (OS.get_environment("SPELL_CLARITY_ONLY")!="1" or name=="01-wind-menu"):
		screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func setup_ui():
	ui.game.new_game();ui.game.save_path=cache+"ui.json"
	# Isolated rendering/combat fixture: make a formal mage available without
	# bypassing or editing the real clinic recruitment controller.
	ui.game.roster.hervi=ui.game._initial_character("hervi");ui.game.party.append("hervi");ui.game.parties.alm.append("hervi")
	ui.game.world_node=int(ui.game.stages[111].node);ui.game.start_battle(111);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="action";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
	var mage=ui.game.find_unit("hervi");mage.position=[10,10];mage.hp=28;mage.item_id=0
	ui.game.find_unit("S11_e1").position=[12,10];ui.game.selected_id="hervi";ui.game.cursor=Vector2i(10,10);ui._focus_battle(ui.game.cursor,true)
	ui._menu_action("magic","unit_action")
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4;setup_ui()
	key(KEY_DOWN);await frame("01-wind-menu")
	check(not ui.menu_actions.is_empty() and ui.menu_actions[ui.menu_selected]=="spell:27","direction key selects wind in the ordinary magic menu")
	if visual:
		check(ui.presentation_audit.spell_info.id==27 and ui.presentation_audit.spell_attack.has(Vector2i(12,10)),"wind details and two-tile green overlay render together")
		check(not ui.text_checks.any(func(t):return str(t.text).begins_with("距离=")),"removed distance-calculation copy stays absent")
		check(ui.text_checks.any(func(t):return str(t.text)==str(ui.presentation_audit.spell_info.effect) and t.bounds.size.y>=12),"spell details use the clearer twelve-pixel type")
		check(ui.presentation_audit.spell_layout.side_by_side,"iPhone landscape keeps list and description alongside without extra pagination")
		var selected_sprite=Rect2(ui._battle_cell_screen(ui.game.pos(ui.game.find_unit("hervi")))+Vector2(-4,-13),Vector2(24,29))
		check(not ui.presentation_audit.spell_layout.menu.intersects(selected_sprite) and not ui.presentation_audit.spell_layout.detail.intersects(selected_sprite),"magic menu leaves caster sprite and cursor visible")
		check(ui._menu_pointer_index(ui.presentation_audit.spell_layout.detail.get_center())==-1,"description tap cannot confirm a spell")
	key(KEY_Z);await process_frame
	check(ui.ui_mode=="target" and ui.target_ids.has("S11_e1") and int(ui.game.find_unit("hervi").weapon_index)==27,"confirming wind selects a real enemy two tiles away")
	await frame("02-wind-target")
	if not visual:
		var before_hp=int(ui.game.find_unit("hervi").hp)
		key(KEY_Z)
		for i in range(200):
			await process_frame
			if not ui.busy:break
		check(int(ui.game.find_unit("hervi").hp)<before_hp and int(ui.game.find_unit("S11_e1").hp)<int(ui.game.find_unit("S11_e1").max_hp),"ordinary confirm commits wind combat and consumes caster HP at distance two")
	setup_ui();var mage=ui.game.find_unit("hervi");mage.magic_flags=255;ui._menu_action("magic","unit_action")
	for profession in [15,17]:
		mage.class_id=profession;ui._menu_action("magic","unit_action")
		for id in Rules.Items.spells(mage):
			ui.menu_selected=ui.menu_actions.find("spell:"+str(id));await frame("all-spells-"+str(id),false)
	# The minimum desktop canvas must still keep details, rows and page controls safe.
	ui.get_parent().remove_child(ui);var desktop=SubViewport.new();desktop.size=Vector2i(256,240);desktop.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(desktop);ui.set_meta("phone",false);desktop.add_child(ui)
	for profession in [15,17]:
		mage.class_id=profession;ui._menu_action("magic","unit_action")
		for id in Rules.Items.spells(mage):
			ui.menu_selected=ui.menu_actions.find("spell:"+str(id));ui.queue_redraw()
			for i in range(2):await process_frame
			if visual:check(ui.layout_errors.is_empty(),"minimum desktop spell details fit: "+str(id)+" "+str(ui.layout_errors))
	screen.remove_child(phone);phone.queue_free();ui.queue_free();desktop.queue_free();screen.queue_free();await process_frame
	presentation_complete=true
func run():
	cache="/private/tmp/spell-bandits-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	if not visual:domain()
	await presentation()
	check(presentation_complete,"UI input and layout test completed without aborting")
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"screenshots":shots,"device_updated":false},"  "));f.close()
	print("SPELL_BANDITS ",checks.size()," checks ",failures.size()," failures");quit(0 if failures.is_empty() else 1)
