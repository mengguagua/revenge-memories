extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Stats=preload("res://core/equipment_comparison.gd")
const Art=preload("res://core/party_sprites.gd")
const OUT="res://reports/combat-balance-20261025/"
var checks=[]
var errors=[]
var shots=[]
var cache=""
var ui
var phone
var screen
var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh(stage:int):
	var g=State.new();g.new_game();g.save_path=cache+"save.json";g.world_node=int(g.stages[stage].node);check(g.start_battle(stage),"enter stage "+str(stage));return g
func domain():
	var g=fresh(112);var boss=g.find_unit("S12_boss")
	check(int(boss.strength)==11 and int(boss.defence)==6,"S12 commander gains exactly two strength and two defence")
	var tank=g.find_unit("otto");tank.defence=6;tank.item_id=48
	check(Stats.stats(tank).defence==9 and int(tank.defence)==6,"leather shield adds three displayed physical defence without changing base stats")
	var spell=g._initial_character("hervi");spell.strength=10;spell.item_id=0;spell.weapon_index=23
	var target=tank.duplicate(true);target.defence=20;target.resistance=2;target.item_id=0
	check(Rules.attack_stats(spell,target,0).damage==11,"Gaiden fire: strength10 plus might3 minus resistance2, independent of physical defence20")
	target.item_id=48
	check(Rules.attack_stats(spell,target,0).damage==11 and Stats.stats(target).defence==23 and Stats.stats(target).resistance==2,"leather shield affects only physical damage and its displayed physical defence")
	target.item_id=53
	check(Rules.attack_stats(spell,target,0).damage==6 and Stats.stats(target).resistance==7,"rebalanced dual-defence shield adds five resistance and uses the ordinary damage formula")
	spell.item_id=66;spell.weapon_index=28;var snapshot=spell.duplicate(true);var shown=Stats.stats(spell)
	check(shown.power==15 and spell==snapshot,"status uses the default fire plus legal focus, ignores stale selected spell without mutating the actor")
	var swift=tank.duplicate(true);swift.item_id=56
	check(Stats.stats(swift).move==int(swift.move)+5 and Stats.stats(swift).speed==40,"status includes speed-ring movement and effective attack speed")
	var bow=g._initial_character("daan");bow.item_id=20
	check(Stats.stats(bow).power==int(bow.strength)+3 and Stats.stats(bow).range==5,"status includes equipped weapon might and range")
	# Known legacy values migrate once; live HP/turn/RNG and arbitrary edits stay.
	var tuning=g.EnemyBalance.data();var old=tuning.stages["112"].S12_boss.before
	for field in old:boss[field]=old[field]
	boss.erase("enemy_balance_revision");boss.hp=11;g.turn=4;g.rng_state=99
	for u in g.battle_start_snapshot.units:
		if u.id=="S12_boss":
			for field in old:u[field]=old[field]
			u.erase("enemy_balance_revision")
	var at=g.pos(boss);check(g.save_game(),"save isolated legacy balance checkpoint")
	var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"legacy balance checkpoint remains loadable")
	boss=loaded.find_unit("S12_boss")
	check(int(boss.strength)==11 and int(boss.defence)==6 and int(boss.hp)==11 and loaded.pos(boss)==at and loaded.turn==4 and loaded.rng_state==99,"balance migration preserves live wounds, position, turn and RNG")
	check(loaded.save_game() and loaded.load_game() and int(loaded.find_unit("S12_boss").strength)==11,"save and reload do not stack commander bonuses")
	check(loaded.retry_battle() and int(loaded.find_unit("S12_boss").strength)==11,"retry snapshot retains exactly one balance update")
	boss=loaded.find_unit("S12_boss");boss.erase("enemy_balance_revision");boss.strength=17;loaded.EnemyBalance.prepare(112,loaded.units)
	check(int(boss.strength)==17,"unrecognized custom or scripted strength is not overwritten")
	g=fresh(111);var beck=g.find_unit("beck")
	for id in ["S11_e1","S11_e2","S11_e3","S11_e4","S11_e5"]:
		var enemy=g.find_unit(id);check(int(enemy.class_id)==14 and int(enemy.strength)==10 and int(enemy.speed)==4 and str(Art.sprite("map",enemy,1).get("reviewed_profile","")).contains("class-14-enemy"),"bandit has intended profession, new artwork and strength: "+id)
	check(not g.select_unit("beck") and g.MineEscort.applies(g,beck),"Beck remains a prospective companion with automatic escort duty")
	for enemy in g.living("enemy"):enemy.hp=0
	g.find_unit("S11_miners0").position=[7,16];g.find_unit("S11_miners1").position=[8,16]
	var action=g.ai_action(beck);check(action.destination!=g.pos(beck) and g.can_stop(beck,action.destination) and not g.path_to(beck,action.destination).is_empty(),"Beck follows advancing miners on a legal route instead of remaining a witness")
	beck.position=g.battle_data.exit.duplicate();g.mark_wait("beck")
	check(not g.flags.quest.evacuated.has("beck"),"Beck never counts as either required miner group")
	g.flags.quest.evacuated=["S11_miners0","beck"];g.battle_outcome=""
	check(g.check_outcome().is_empty(),"one miner plus Beck cannot complete rescue")
	g.flags.quest.evacuated.append("S11_miners1");check(g.check_outcome()=="victory","both miner groups plus defeated chief complete the stage")
	g=fresh(111);g.find_unit("beck").quest_kind="witness"
	var brigand=g.find_unit("S11_e1")
	for key in tuning.stages["111"].S11_e1.before:brigand[key]=tuning.stages["111"].S11_e1.before[key]
	brigand.erase("enemy_balance_revision");brigand.hp=13
	check(g.save_game(),"save isolated old bandit and stationary Beck checkpoint")
	loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"old S11 checkpoint loads after profession correction")
	check(int(loaded.find_unit("S11_e1").class_id)==14 and int(loaded.find_unit("S11_e1").strength)==10 and int(loaded.find_unit("S11_e1").hp)==13 and loaded.find_unit("beck").quest_kind=="mine_guard","old S11 save adopts bandit profession and Beck duty without healing damage")
	check(loaded.flags.get("seen_S11-BECK-DUTY",false),"old S11 save explains Beck's new escort duty once")
func frame(name:String,capture:bool=true):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
	for i in range(4):await process_frame
	if not visual:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text and controls remain within safe bounds "+str(ui.layout_errors))
	if capture and OS.get_environment("COMBAT_SKIP_CAPTURE")!="1":screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func stage(id:int):
	ui.game.new_game();ui.game.save_path=cache+"ui.json";ui.game.world_node=int(ui.game.stages[id].node);ui.game.start_battle(id);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	stage(111);var tank=ui.game.find_unit("otto");tank.defence=6;tank.item_id=48
	ui.status_id="otto";ui.ui_mode="status";ui.game.cursor=ui.game.pos(tank);ui._focus_battle(ui.game.cursor,true)
	await frame("01-status-equipment")
	if visual:check(ui.presentation_audit.status_stats.defence==9 and ui.text_checks.any(func(t):return str(t.text)=="魔防"),"ordinary battlefield status actually renders equipment-inclusive defence and a separate magic defence")
	ui.ui_mode="inspect";var bandit=ui.game.find_unit("S11_e1");ui.game.cursor=ui.game.pos(bandit);ui._focus_battle(ui.game.cursor,true)
	check(int(ui.battle_animation.sprite(bandit).get("reviewed_class_id",0))==14,"bandit combat body also resolves the approved brigand rather than heavy infantry")
	await frame("02-bandit-profession")
	ui.game.cursor=ui.game.pos(ui.game.find_unit("beck"));ui._focus_battle(ui.game.cursor,true)
	await frame("03-beck-duty")
	# Advanced hero branch also has to render equipment-inclusive values.
	var hero=ui.game.find_unit("hunapu");check(ui.game.HeroProfessions.apply(hero),"prepare actual advanced hero branch");hero.item_id=53
	ui.status_id="hunapu";ui.ui_mode="status";ui.game.cursor=ui.game.pos(hero);ui._focus_battle(ui.game.cursor,true)
	await frame("advanced-status",false)
	if visual:check(ui.presentation_audit.status_stats.defence==int(hero.defence)+5,"advanced status renders equipped physical defence")
	phone.queue_free();await process_frame;screen.queue_free();await process_frame
func run():
	cache="/private/tmp/combat-feedback-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	if not visual:domain()
	await presentation()
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"failures":errors,"screenshots":shots,"device_updated":false},"  "));f.close();print("COMBAT_FEEDBACK ",checks.size()," checks ",errors.size()," failures");quit(0 if errors.is_empty() else 1)
