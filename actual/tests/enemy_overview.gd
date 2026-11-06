extends SceneTree
const OUT="res://reports/enemy-overview-20261025/"
var checks=[]
var errors=[]
var shots=[]
var cache=""
var visual=false
var ui
var phone
var screen
var completed=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func key(code:int):
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true;ui._input(event)
	event=InputEventKey.new();event.physical_keycode=code;event.pressed=false;ui._input(event)
func frame(name:String,capture:bool=true):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
	for i in range(4):await process_frame
	if not visual:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text and controls remain within safe bounds: "+str(ui.layout_errors))
	if capture:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func fresh():
	ui.game.new_game();ui.game.save_path=cache+"unused.json";ui.game.world_node=int(ui.game.stages[111].node);ui.game.start_battle(111);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu();ui.game.cursor=ui.game.pos(ui.game.find_unit("hunapu"));ui._focus_battle(ui.game.cursor,true)
func choose_enemy():
	key(KEY_S);var index=ui.menu_actions.find("enemy_roster")
	check(index>=0,"system menu offers enemy overview")
	if index<0:return
	ui._mouse_accept(ui._menu_row_rect(index).get_center()+ui._canvas_offset())
func state_digest()->String:
	return JSON.stringify([ui.game.units,ui.game.roster,ui.game.flags,ui.game.turn,ui.game.phase,ui.game.rng_state,ui.game.selected_id]).sha256_text()
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4;ui.audio.set_music_enabled(false);ui.audio.set_sfx_enabled(false);fresh()
	var before=state_digest();key(KEY_S)
	check(ui.menu_items.has("敌军速览") and not ui.menu_items.has("集合队伍") and not ui.menu_actions.has("gather"),"enemy overview replaces gather in the existing row")
	await frame("01-battle-menu")
	var index=ui.menu_actions.find("enemy_roster");ui._mouse_accept(ui._menu_row_rect(index).get_center()+ui._canvas_offset())
	var members=ui._enemy_status_members();var first=str(members[0]);var second=str(members[1]);var last=str(members[-1])
	check(ui.menu_items.is_empty() and ui.ui_mode=="status" and ui.status_id==first,"tap opens the first living enemy detail directly")
	check(ui.game.cursor==ui.game.pos(ui.game.find_unit(first)) and ui._status_members()==members,"enemy details focus the map and stay within enemy roster")
	await frame("02-enemy-detail")
	if visual:
		check(ui.text_checks.any(func(t):return str(t.text)=="敌军 1/8"),"detail header identifies enemy index and living count")
		check(int(ui.presentation_audit.status_stats.power)==15,"commander detail includes current equipped attack")
	key(KEY_RIGHT);check(ui.status_id==second,"right direction moves to next living enemy")
	key(KEY_LEFT);check(ui.status_id==first,"left direction moves to previous living enemy")
	key(KEY_LEFT);check(ui.status_id==last,"left wraps from first to last")
	key(KEY_RIGHT);check(ui.status_id==first,"right wraps from last to first")
	ui._mouse_accept(Vector2(228,28)+ui._canvas_offset());check(ui.status_id==second,"tap on right header arrow switches details")
	ui._mouse_accept(Vector2(28,28)+ui._canvas_offset());check(ui.status_id==first,"tap on left header arrow switches back")
	check(not phone._can_cycle(),"switch-my-side control cannot change enemy inspection to a player")
	key(KEY_S);var previous=ui.menu_selected;key(KEY_DOWN)
	check(not ui.menu_items.is_empty() and ui.menu_selected==previous+1,"system menu direction keys work when opened over enemy details")
	key(KEY_X);check(ui.ui_mode=="status" and ui.status_id==first,"closing overlaid menu resumes the same enemy detail")
	key(KEY_X);check(ui.ui_mode=="inspect" and ui.menu_items.is_empty(),"back returns to battlefield inspection")
	check(state_digest()==before and not FileAccess.file_exists(cache+"unused.json"),"read-only overview does not spend actions, change HP or RNG, or save")
	# Prefer an already-hovered living enemy when entering from its map cell.
	ui.game.cursor=ui.game.pos(ui.game.find_unit(last));choose_enemy();check(ui.status_id==last,"overview starts with hovered living enemy")
	ui.game.find_unit(first).hp=0;ui.game.find_unit(second).hidden=true
	var active=ui._status_members();check(not active.has(first) and not active.has(second),"defeated and hidden enemies are excluded")
	# The merged fifth-chapter roster override must not block enemy cycling.
	ui.game.stage_id=534;check(ui._status_members()==active,"merged-party status branch still exposes enemy members only");ui.game.stage_id=111
	for unit in ui.game.living("enemy"):
		if str(unit.id)!=last:unit.hp=0
	ui.game.find_unit(last).hidden=false;key(KEY_RIGHT);key(KEY_LEFT)
	check(ui.status_id==last and ui._status_members()==[last],"single remaining enemy is stable under both directions")
	await frame("single-enemy",false)
	if visual:check(ui.text_checks.any(func(t):return str(t.text)=="敌军 1/1"),"single enemy keeps a correct one-of-one heading")
	# If an inspected unit becomes unavailable, the surviving member is selected.
	ui.status_id=first;key(KEY_RIGHT);check(ui.status_id==last,"cycling recovers from a no-longer-living inspected unit")
	key(KEY_X);ui.game.find_unit(last).hp=0;choose_enemy()
	check(ui.ui_mode=="inspect" and ui.notice.contains("没有存活敌军"),"zero enemies gives a short notice instead of an empty detail")
	fresh();ui.game.cursor=ui.game.pos(ui.game.find_unit("hunapu"));key(KEY_TAB);var allies=ui._status_members();key(KEY_RIGHT)
	check(allies==ui.game.party and ui.game.party.has(ui.status_id),"ordinary friendly status still cycles only the friendly party")
	await create_timer(.1).timeout;phone.queue_free();await process_frame;screen.queue_free();await process_frame;completed=true
func run():
	cache="/private/tmp/enemy-overview-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	await presentation();check(completed,"overview checks completed")
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"failures":errors,"screenshots":shots,"device_updated":false},"  "));f.close()
	print("ENEMY_OVERVIEW ",checks.size()," checks ",errors.size()," failures");quit(0 if errors.is_empty() else 1)
