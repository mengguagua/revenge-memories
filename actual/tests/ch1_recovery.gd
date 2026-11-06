extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/ch1-recovery-20261025/"
const SITES={101:Vector2i(4,14),102:Vector2i(3,16),111:Vector2i(9,19),112:Vector2i(10,20)}
var checks=[]
var failures=[]
var shots=[]
var cache=""
var visual=false
var ui
var phone
var screen
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func fresh(id:int):
	var g=State.new();g.new_game();g.save_path=cache+str(id)+".json";g.world_node=int(g.stages[id].node)
	check(g.start_battle(id),"enter "+str(id));return g
func connected(g,unit:Dictionary,start:Vector2i,goal:Vector2i)->bool:
	var pending=[start];var seen={start:true}
	while not pending.is_empty():
		var cell:Vector2i=pending.pop_front()
		if cell==goal:return true
		for direction in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			var next=cell+direction
			if seen.has(next) or not g.in_bounds(next) or g.movement_cost(unit,next)>=255:continue
			seen[next]=true;pending.append(next)
	return false
func domain():
	for id in SITES:
		var g=fresh(id);var at:Vector2i=SITES[id];var actor=g.find_unit("otto")
		check(g.unit_at(at).is_empty() and g.can_stop(actor,at) and g.category(at)==15,"new recovery cell is unoccupied and standable: "+str(id))
		check(connected(g,actor,g.pos(actor),at) and connected(g,actor,at,Vector2i(g.battle_data.exit[0],g.battle_data.exit[1])),"recovery connects to deployment and objective: "+str(id))
		actor.position=[at.x,at.y];actor.item_id=0;actor.hp=10
		g.mark_wait(str(actor.id));check(int(actor.hp)==10,"occupying and waiting do not instantly heal: "+str(id))
		g.next_phase();check(g.phase=="enemy" and int(actor.hp)==10,"ending player phase does not heal player: "+str(id))
		g.next_phase();check(g.phase=="player" and int(actor.hp)==15,"next player phase restores exactly five HP: "+str(id))
		actor.hp=int(actor.max_hp)-2;g.next_phase();g.next_phase()
		check(int(actor.hp)==int(actor.max_hp),"healing caps at maximum HP: "+str(id))
		actor.hp=7;var turn=g.turn;var rng=g.rng_state;var positions=g.units.map(func(u):return g.pos(u))
		check(g.save_game(),"save isolated in-progress recovery checkpoint: "+str(id))
		var loaded=State.new();loaded.save_path=g.save_path
		check(loaded.load_game() and loaded.category(at)==15 and int(loaded.find_unit("otto").hp)==7 and loaded.turn==turn and loaded.rng_state==rng and loaded.units.map(func(u):return loaded.pos(u))==positions,"load adopts canonical recovery map without changing wounds or formation: "+str(id))
		check(loaded.retry_battle() and loaded.category(at)==15,"retry retains recovery terrain: "+str(id))
	var g=fresh(101);var enemy=g.find_unit("M11_e1");enemy.position=[4,14];enemy.hp=6
	g.next_phase();check(int(enemy.hp)==11,"enemy occupying recovery terrain also heals on its own phase")
	var dead=g.find_unit("otto").duplicate(true);dead.hp=0
	check(g.Items.phase_effect(dead,218,15).hp_after==0,"terrain cannot revive a fallen member")
	dead.hp=5;dead.item_id=53
	check(g.Items.phase_effect(dead,218,15,true).hp_after==10,"terrain, recovery gear and adjacent healer do not stack")
	g=fresh(112)
	check(g.Medicine.is_staff(g.find_unit("hervi")) and g.pos(g.find_unit("hervi"))==Vector2i(24,5) and g.category(Vector2i(22,5))!=15 and g.category(Vector2i(22,6))!=15,"clinic duty, visit door and medicine delivery remain separate")
	g=fresh(111);check(g.MineEscort.applies(g,g.find_unit("beck")),"Beck keeps automatic miner escort duty")
func frame(name:String):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text and controls fit measured safe areas: "+str(ui.layout_errors))
	var expected="下次己方阶段恢复5生命" if name.begins_with("M11") else "己方阶段开始恢复5生命"
	check(ui.text_checks.any(func(t):return str(t.text)==expected),name+" displays exact healing trigger")
	screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	for id in SITES:
		ui.game.new_game();ui.game.save_path=cache+"ui.json";ui.game.world_node=int(ui.game.stages[id].node);ui.game.start_battle(id);ui.game.story_events.clear()
		ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
		ui.game.cursor=SITES[id]
		if id==101:
			var actor=ui.game.find_unit("otto");actor.position=[SITES[id].x,SITES[id].y];actor.hp=10
		ui._focus_battle(ui.game.cursor,true)
		await frame(str(ui.game.battle_data.code)+"-recovery")
	phone.queue_free();await process_frame;screen.queue_free();await process_frame
func run():
	cache="/private/tmp/ch1-recovery-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	if visual:await presentation()
	else:domain()
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"screenshots":shots,"device_updated":false},"  "));f.close()
	print("CH1_RECOVERY ",checks.size()," checks ",failures.size()," failures");quit(0 if failures.is_empty() else 1)
