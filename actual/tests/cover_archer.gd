extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/cover-archer-20261025/"
var checks=[]
var errors=[]
var shots=[]
var cache=""
var visual=false
var ui
var phone
var screen
var ui_completed=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path=cache+"state.json";g.world_node=int(g.stages[111].node);g.start_battle(111);g.story_events.clear();return g
func adjacent(g):
	var actor=g.find_unit("hunapu");var target=g.find_unit("daan")
	actor.position=[10,16];target.position=[11,16];g.selected_id="hunapu";return [actor,target]
func domain():
	var g=fresh();var pair=adjacent(g);var actor=pair[0];var target=pair[1]
	check(g.cover_targets(actor).all(func(u):return u.acted) and not g.cover_targets(actor).has(target),"ready ally is absent from cover target list")
	check(not g.begin_cover("daan") and not actor.acted and not actor.has("cover_target"),"direct commit cannot cover a ready ally or spend actor action")
	target.acted=true
	check(g.cover_targets(actor).has(target) and g.begin_cover("daan") and actor.acted,"adjacent spent ally can be covered and consumes the guard action")
	check(not g.select_unit("daan"),"covered spent ally cannot start another action")
	check(g.Cover.split(g,target,0,{}).is_empty() and actor.has("cover_target"),"miss retains the committed cover")
	var hp_a=int(actor.hp);var hp_b=int(target.hp)
	g.apply_tactical_damage(g.find_unit("S11_e7"),target,9,"physical")
	check(int(actor.hp)==hp_a-5 and int(target.hp)==hp_b-4 and not actor.has("cover_target"),"one damaging hit shares five plus four and consumes cover exactly once")
	g.apply_tactical_damage(g.find_unit("S11_e7"),target,3,"physical")
	check(int(target.hp)==hp_b-7,"next hit is no longer shared")
	actor.acted=false;g.selected_id="hunapu";g.begin_cover("daan")
	check(g.save_game(),"valid active cover can be saved in isolation")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and not loaded.Cover.guard_for(loaded,loaded.find_unit("daan")).is_empty(),"load preserves valid cover of a spent target")
	# A pre-change save could cover a still-ready ally. Drop only that cover.
	var saved=State.read_json(g.save_path)
	for u in saved.units:
		if u.id=="daan":u.acted=false
	var f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(JSON.stringify(saved));f.close()
	check(loaded.load_game() and not loaded.find_unit("hunapu").has("cover_target") and int(loaded.find_unit("hunapu").hp)==int(actor.hp) and loaded.find_unit("hunapu").acted,"old invalid ready-target cover is cleared without refunding action or changing wounds")
	g=fresh();pair=adjacent(g);actor=pair[0];target=pair[1];target.acted=true;g.begin_cover("daan");g.next_phase()
	check(actor.has("cover_target"),"cover remains during enemy phase")
	g.next_phase();check(not actor.has("cover_target"),"next player phase expires cover")
	g=fresh();var bow=g.find_unit("S11_e7")
	check(g.living("enemy").size()==8 and int(bow.class_id)==12 and int(bow.strength)==9 and int(bow.speed)==3 and int(bow.hp)==22 and g.Rules.attack_range(bow)==Vector2i(1,3),"exactly one ordinary new archer joins the eight-enemy deployment")
	check(g.movement_cost(bow,g.pos(bow))<255 and g.units.filter(func(u):return g.pos(u)==g.pos(bow)).size()==1,"archer starts on a walkable unoccupied cell")
	var action=g.ai_action(bow)
	check(g.can_stop(bow,action.destination) and not g.path_to(bow,action.destination).is_empty(),"new archer has a legal normal AI route")
	# Simulate an old ongoing checkpoint with the old seven-enemy entry snapshot.
	g.units=g.units.filter(func(u):return u.id!="S11_e7")
	g.battle_start_snapshot.units=g.battle_start_snapshot.units.filter(func(u):return u.id!="S11_e7")
	g.turn=7;g.rng_state=99;g.find_unit("hunapu").hp=17
	check(g.save_game(),"old seven-enemy checkpoint remains valid")
	loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and loaded.find_unit("S11_e7").is_empty() and loaded.turn==7 and loaded.rng_state==99 and int(loaded.find_unit("hunapu").hp)==17,"continuing an old battle does not spawn an enemy or alter wounds and turn")
	check(loaded.retry_battle() and not loaded.find_unit("S11_e7").is_empty() and loaded.living("enemy").size()==8 and loaded.turn==1,"ordinary retry redeploys the new archer from the restored entry roster")
	check(loaded.retry_battle() and loaded.living("enemy").size()==8,"repeated retry never duplicates the added archer")
func key(code:int):
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true;ui._input(event)
	event=InputEventKey.new();event.physical_keycode=code;event.pressed=false;ui._input(event)
func choose(action:String):
	var index=ui.menu_actions.find(action);check(index>=0,"UI offers "+action)
	if index<0:return
	ui.menu_selected=index;key(KEY_Z)
func settle():
	for i in range(12):await process_frame
func frame(name:String):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await settle()
	if not visual:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" safe text and control bounds: "+str(ui.layout_errors))
	screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.audio.set_music_enabled(false);ui.audio.set_sfx_enabled(false)
	ui.game.new_game();ui.game.save_path=cache+"ui.json";ui.game.world_node=int(ui.game.stages[111].node);ui.game.start_battle(111);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
	# Spend the target's action through ordinary select/move-in-place/wait input.
	ui.game.cursor=ui.game.pos(ui.game.find_unit("daan"));ui._focus_battle(ui.game.cursor,true);key(KEY_Z);key(KEY_Z);await settle();choose("wait");await settle()
	check(ui.game.find_unit("daan").acted,"target spends its own action through ordinary wait input")
	ui.game.cursor=ui.game.pos(ui.game.find_unit("hunapu"));key(KEY_Z);key(KEY_Z);await settle();choose("cover:choose")
	check(ui.menu_actions.has("cover:target:daan") and ui.menu_actions.filter(func(a):return str(a).begins_with("cover:target:")).all(func(a):return ui.game.find_unit(str(a).trim_prefix("cover:target:")).acted),"picker lists only spent adjacent allies")
	choose("cover:target:daan")
	check(ui.view=="battle" and ui.menu_context=="cover_confirm" and ui.menu_items.size()==2 and not ui.game.flags.has("active_plot") and ui.game.story_events.is_empty(),"target selection opens only a two-choice confirmation without story pages")
	await frame("01-cover-confirm")
	key(KEY_X);check(ui.menu_context=="unit_action" and not ui.game.find_unit("hunapu").acted,"back cancels cover without spending the guard action")
	choose("cover:choose");choose("cover:target:daan");choose("cover:commit:daan");await settle()
	check(ui.game.find_unit("hunapu").acted and ui.game.Cover.guard_for(ui.game,ui.game.find_unit("daan")).get("id","")=="hunapu","ordinary confirmation commits cover exactly once")
	ui._clear_menu();ui.notice_time=0;ui.ui_mode="inspect";ui.game.cursor=ui.game.pos(ui.game.find_unit("S11_e7"));ui._focus_battle(ui.game.cursor,true)
	await frame("02-added-archer")
	# Let the dummy audio thread release any title-stream packets before exit.
	await create_timer(.1).timeout
	phone.queue_free();await process_frame;screen.queue_free();await process_frame;ui_completed=true
func run():
	cache="/private/tmp/cover-archer-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	if not visual:domain()
	await presentation();check(ui_completed,"UI test completed")
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"failures":errors,"screenshots":shots,"device_updated":false},"  "));f.close()
	print("COVER_ARCHER ",checks.size()," checks ",errors.size()," failures");quit(0 if errors.is_empty() else 1)
