extends SceneTree
const State=preload("res://core/game_state.gd")
const Mechanical=preload("res://core/mechanical_puppets.gd")
const FIXTURE="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F21-deployment.json"
const OUT="res://reports/mechanical-puppets-20261104/"
var ui
var viewport
var checks=[]
var errors=[]
var shots=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":push_error("Background guard required");quit(1);return
	call_deferred("run")
func check(value:bool,label:String):
	checks.append(label)
	if not value:errors.append(label);push_error(label)
func fresh():
	ui.game=State.new();ui.game.save_path=FIXTURE
	check(ui.game.load_game(),"Real F21 checkpoint loads in actual controller")
	ui.game.save_path="/private/tmp/revenge-mechanical-ui.json"
	check(ui.game.start_battle(201),"Actual F21 fresh deployment")
	ui.game.story_events.clear();ui.game.flags.erase("active_plot")
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.instant_mode=true
	ui.phase_time=0;ui.notice_time=0;ui.held_direction=Vector2i.ZERO;ui._clear_menu()
	ui.mechanical_target_confirmed=false;ui.mechanical_target_part=""
	ui.battle_animation.reset();ui.combat.clear();ui._focus_battle(Vector2i(21,14),true)
func shot(name:String):
	ui.notice_time=0;ui.phase_time=0;ui.queue_redraw()
	for i in range(4):await process_frame
	await RenderingServer.frame_post_draw
	var image=viewport.get_texture().get_image()
	check(image!=null and not image.is_empty(),"Rendered "+name)
	if image==null or image.is_empty():return
	image.save_png(OUT+name+".png")
	check(ui.layout_errors.is_empty(),"Text safe areas "+name+": "+str(ui.layout_errors))
	shots.append({"file":name+".png","size":[image.get_width(),image.get_height()],"layout_errors":ui.layout_errors.duplicate(),"audit":ui.presentation_audit.duplicate(true),"preview":ui.battle_preview_audit.duplicate(true)})
func stage_combat(attacker:String,defender:String,distance:int,broken:bool=false):
	fresh()
	var enemy=ui.game.find_unit("F21_water_monkey_1");var player=ui.game.find_unit("eileen")
	enemy.position=[21,14];player.position=[21-distance,14]
	if broken:enemy.parts.back_cannon.hp=0
	ui.game.rng_state=0
	var plan=ui.game.plan_combat(attacker,defender)
	check(not plan.is_empty(),"Real combat plan for "+attacker+" distance "+str(distance))
	ui.combat=plan;ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_hp.clear();ui.combat_fades.clear()
	for id in [attacker,defender]:
		var u=ui.game.find_unit(id);ui.combat_poses[id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_hp[id]=int(u.hp);ui.combat_fades[id]=1.0
	ui.view="combat"
	return plan.events.filter(func(e):return str(e.attacker)==attacker)[0]
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(406,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);fresh()
	await shot("01-f21-deployment")
	ui.status_id="F21_water_monkey_1";ui.ui_mode="status";await shot("02-intact-status")
	var enemy=ui.game.find_unit("F21_water_monkey_1");var player=ui.game.find_unit("eileen")
	player.position=[19,14];player.weapon_index=23;player.strength=40;player.skill=40;player.hp=52;player.max_hp=52
	ui.game.selected_id="eileen";ui.target_ids=["F21_water_monkey_1"];ui.target_index=0;ui.game.cursor=Vector2i(21,14);ui.ui_mode="target"
	ui._accept();check(ui.menu_context=="mechanical_part","Actual confirm opens body/part choice")
	await shot("03-part-choice")
	var rng_before=ui.game.rng_state
	ui._cancel()
	check(ui.game.rng_state==rng_before and not player.acted and not ui.mechanical_target_confirmed,"Cancel part menu does not spend action or random state")
	ui._accept()
	ui.menu_selected=1;ui._accept()
	check(ui.mechanical_target_confirmed and ui.mechanical_target_part==Mechanical.PART,"Actual menu input selects back cannon")
	await shot("04-part-preview")
	check(ui.battle_preview_audit.get("mechanical_target",{}).get("part","")==Mechanical.PART,"Battle preview displays selected part HP")
	ui._direction(Vector2i.RIGHT)
	check(not ui.mechanical_target_confirmed,"Cycling targets clears stale part confirmation")
	ui._accept();ui.menu_selected=1;ui._accept()
	ui._accept()
	for i in range(12):await process_frame
	check(Mechanical.cannon_hp(enemy)==0 and int(enemy.hp)==22,"Actual confirm commits only back-cannon damage")
	check(ui.game.kills==0,"Actual part attack does not count kill")
	ui.view="battle";ui.ui_mode="status";ui.status_id=str(enemy.id);ui.busy=false;ui._clear_menu();await shot("05-broken-status")
	var event=stage_combat("F21_water_monkey_1","eileen",3)
	check(ui.battle_animation.show_frame(event,53),"Runtime water flight frame selectable")
	await shot("06-water-flight")
	check(not ui.battle_animation.effects.is_empty(),"Water flight uses actual loaded bitmap effect")
	check(ui.battle_animation.show_frame(event,68),"Runtime water impact frame selectable")
	ui.combat_hit_id="eileen";ui.combat_hit_time=.5;ui.elapsed=0
	await shot("07-water-impact")
	for broken in [false,true]:
		event=stage_combat("F21_water_monkey_1","eileen",1,broken)
		for tick in [35,82,190]:
			check(ui.battle_animation.show_frame(event,tick),"Runtime palm frame "+str(tick)+" broken="+str(broken))
			await shot(("broken-" if broken else "intact-")+"palm-"+str(tick))
		var art=ui.battle_animation.MechanicalArt.reaction(ui.game.find_unit("F21_water_monkey_1"),"hit")
		ui.battle_animation._source_frame({"attacker":"F21_water_monkey_1"},art.frames[0],0,false)
		await shot(("broken-" if broken else "intact-")+"hit-flash")
	fresh();enemy=ui.game.find_unit("F21_water_monkey_1")
	for u in ui.game.units:
		if u.side=="enemy" and not Mechanical.is_puppet(u):u.hp=0
	Mechanical.refresh(ui.game);ui.status_id=str(enemy.id);ui.ui_mode="status";await shot("08-retreat-status")
	check(enemy.move==8,"Actual retreat status shows move8")
	viewport.size=Vector2i(256,240);fresh();ui.status_id="F21_water_monkey_1";ui.ui_mode="status";await shot("09-narrow-status")
	var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"shots":shots,"labels":checks,"scope":"Protected offscreen actual Godot controller and viewport. Controlled part attack and frame captures; not a full natural F21 victory or phone installation."}
	var file=FileAccess.open(OUT+"visual-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"));file.close()
	print("MECHANICAL_VISUAL ",checks.size()," shots=",shots.size()," errors=",errors)
	ui.queue_free();await process_frame
	viewport.queue_free();await process_frame
	quit(0 if errors.is_empty() else 1)
