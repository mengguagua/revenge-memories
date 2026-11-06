extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const OUT="res://reports/opening-feedback-20261026/"
const CACHE="/private/tmp/revenge-opening-feedback-20261026/"
var checks=[]
var errors=[]
var shots=[]
var screen
var phone
var ui
var ticks=0
var domain_completed=false
var presentation_completed=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path=CACHE+"battle.json";g.world_node=3;g.start_battle(102);g.story_events.clear();return g
func at_distance(g,u,d:int):
	var origin=g.pos(u);g.units=[u]
	var graph=g.reachable(u,true)
	for cell in graph.costs:
		if absi(cell.x-origin.x)+absi(cell.y-origin.y)==d and g.can_stop(u,cell):return cell
	return Vector2i(-1,-1)
func domain():
	var g=fresh();var boss=g.find_unit("M12_boss")
	check(boss.defence==6 and boss.resistance==2,"M12 commander defence 4→6 and resistance 0→2")
	for d in range(1,5):
		g=fresh();boss=g.find_unit("M12_boss");var at=at_distance(g,boss,d)
		check(at!=Vector2i(-1,-1),"authored legal approach at distance "+str(d))
		var archer=g.characters.daan.duplicate(true);archer.id="daan";archer.side="player";archer.item_id=22;archer.position=[at.x,at.y];archer.acted=false;g.units=[boss,archer]
		var idle=g.ai_action(boss)
		check(idle.destination==g.pos(boss) and str(idle.target).is_empty(),"proximity does not activate guard at distance "+str(d))
		check(Rules.can_attack(Rules.default_counter(boss,d),d)==(d<=3),"counter respects 1–3 boundary at "+str(d))
		var exchange=g.plan_combat("daan","M12_boss")
		check(not exchange.is_empty() and exchange.stats["M12_boss"].can_strike==(d<=3),"real preview counter at "+str(d))
		check(not boss.get("guard_alerted",false),"planning does not trigger guard at "+str(d))
		# Commit a real attack event as a miss: a miss still provokes pursuit.
		var event=exchange.events[0].duplicate(true);event.hp_after=boss.hp;event.hit=false;event.damage=0;g.commit_strike(event)
		check(bool(boss.guard_alerted),"committed miss alerts guard at "+str(d))
		var response=g.ai_action(boss)
		check(response.destination!=g.pos(boss) or not str(response.target).is_empty(),"attacked guard responds at "+str(d))
	check(Rules.attack_range(boss).y==1,"counter bonus does not extend active spear range")
	var original=State.read_json("res://reports/ch1-story-20261026/before/actual/data/stages/M12.json").enemies[0].duplicate(true)
	original.id="M12_boss";original.defence=4;original.resistance=0;original.hp=9;original.enemy_balance_revision=4;original.guard_alerted=true
	g.EnemyBalance.prepare(102,[original]);check(original.defence==6 and original.resistance==2 and original.hp==9,"old wounded commander receives only the new defence patch")
	var once=original.duplicate(true);g.EnemyBalance.prepare(102,[original]);check(original==once,"migration is idempotent")
	original.hp=0;original.dead=true;original.defence=4;original.resistance=0;original.enemy_balance_revision=4;g.EnemyBalance.prepare(102,[original]);check(original.hp==0 and original.dead,"defence migration cannot revive defeated commander")
	var sentry=fresh().find_unit("M12_boss").duplicate(true);sentry.erase("guard_ai_revision");sentry.guard_alerted=true;sentry.hp=sentry.max_hp
	g.EnemyBalance.prepare(102,[sentry]);check(not sentry.guard_alerted,"old full-health proximity alert resets once")
	for s in g.stages.values():
		for enemy in s.enemies:
			if str(enemy.get("behavior","")) not in ["guard","guard_exit"]:continue
			for d in [1,2,3]:
				check(Rules.attack_range(Rules.default_counter(enemy,d)).y>=3,str(enemy.id)+" counter reach includes "+str(d))
	g=fresh();g.mode="world";g.cleared_stages=[101,102];g.flags.village_ready=true
	check(not g.world_neighbors().has(4),"east road remains gated before grain distribution")
	g.flags.grain_shared=true;check(g.world_neighbors().has(4),"grain distribution opens east road without mandatory recruitment")
	domain_completed=true
func on_tick(key:String):
	if key=="story_type":ticks+=1
func frame(name:String,save:bool=false):
	if ui.view=="plot":ui.dialogue_reveal=999
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	for n in range(3):await process_frame
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph and border safety audit")
	if ui.view=="plot":
		var layout=ui.plot_layout_audit;var safe:Rect2=layout.panel.grow(-8)
		for text in ui.text_checks:check(safe.encloses(text.bounds),name+" actual dialogue glyph safety inset")
		if layout.has_portrait:check(not layout.portrait.intersects(layout.text),name+" portrait separated from text")
	if save:
		screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func close_plot():
	var guard=0
	while ui.view=="plot" and guard<30:ui.dialogue_reveal=999;ui._accept();guard+=1;await process_frame
func presentation():
	DirAccess.make_dir_recursive_absolute(CACHE+"slots")
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=5
	ui.audio.sfx_played.connect(on_tick)
	ui.journey.intent="new";ui.journey.selected=0;ui.journey.commit()
	check(ui.view=="story_intro" and ui.game.flags.story_intro_pending,"real new-journal flow enters introduction before P00")
	ui.story_intro.process(1);await frame("intro-start",true)
	check(ui.story_intro.index==-1,"introduction waits for first confirmation")
	ui._accept();ui.story_intro.process(.1);check(ticks>0 and ui.story_intro.reveal>0,"letter reveal emits mechanical typing cue")
	await frame("intro-typing",true)
	var saved_offset=ui.game.flags.story_intro_offset;var save_path=ui.game.save_path
	var resumed=State.new();resumed.save_path=save_path;check(resumed.load_game() and resumed.flags.story_intro_pending and resumed.flags.story_intro_offset==saved_offset,"introduction has a valid resumable journal checkpoint")
	ui.game=resumed;ui._resume_journey();check(ui.view=="story_intro","continue returns to unfinished introduction")
	var seen={};var emitted="";var limit=0
	while ui.view=="story_intro" and limit<80:
		if ui.story_intro.index>=0:
			var row=ui.story_intro.rows[ui.story_intro.index];emitted+=str(row.text)
			if ui.story_intro.fade<1.0 and ui.story_intro.previous_scene>=0:
				ui.story_intro.process(.325);check(ui.story_intro.fade>0 and ui.story_intro.fade<1,"background transition has an intermediate blend")
				if int(row.scene)==1:await frame("intro-transition",true)
			ui.story_intro.process(3)
			await frame("intro-row-"+str(ui.story_intro.index))
			if not seen.has(row.scene):seen[row.scene]=true;await frame("intro-scene-"+str(row.scene),true)
		ui._accept();limit+=1
	check(ui.view=="hub" and ui.game.hub_record=="P00" and not ui.game.flags.has("story_intro_pending"),"last confirmation enters prologue once")
	var source=""
	for entry in State.read_json("res://data/story_intro.json").scenes:source+=str(entry.text)
	check(emitted==source,"display rows preserve every source character in order")
	await frame("prologue-after-intro",true)
	ui.game.new_game();ui.game.save_path=CACHE+"hub.json";ui.game.world_node=3;ui.game.cleared_stages=[101,102];ui.game.flags.village_ready=true
	ui._continue_world();ui._direction(Vector2i.RIGHT);check(ui.view=="plot" and ui.plot_pages[0].speaker=="胡纳普" and str(ui.plot_pages[0].text).contains("粮"),"blocked right movement gives protagonist guidance")
	await frame("grain-east-guidance",true);await close_plot()
	ui.hub_controller.enter_room("H02");var fula=ui.hub_controller.objects.filter(func(o):return o.action=="fula")[0]
	var art=ui._party_hub_sprite(fula,{})
	check(art==ui.PartySprites.Reviewed.metadata().maps["18_ally"]["tactical-idle"],"Fula hub uses current healing profession art")
	ui.hub_controller.action("fula");check(ui.view=="plot" and ui.plot_pages[0].speaker=="芙拉","Fula speaks the grain guidance herself")
	await frame("fula-grain-guidance",true);await close_plot()
	ui.hub_controller.action("grain");await close_plot();check(ui.game.flags.grain_shared and ui.game.world_neighbors().has(4),"actual grain interaction opens next destination")
	ui.hub_controller.action("fula");await close_plot();check(ui.menu_context=="recruit","Fula invitation still follows grain distribution")
	ui._clear_menu();ui.game.new_game();ui.game.save_path=CACHE+"status.json";ui.game.world_node=3;ui.game.start_battle(102);ui.game.story_events.clear();ui.view="battle";ui.ui_mode="status";ui.status_id="M12_boss";ui.busy=false;ui.notice_time=0;ui.phase_time=0
	await frame("commander-status",true)
	ui.ui_mode="inspect"
	for d in [1,2,3]:
		var b=ui.game.find_unit("M12_boss");var at=at_distance(ui.game,b,d);var a=ui.game.characters.daan.duplicate(true);a.position=[at.x,at.y];a.side="player";a.item_id=22;ui.game.units=[b,a];ui.game.selected_id="daan";ui.target_ids=["M12_boss"];ui.target_index=0;ui.ui_mode="target";ui._focus_battle(ui.game.pos(b),true)
		await frame("commander-counter-"+str(d),true)
	for context in ["general","battle","overview"]:
		phone.last_context=context;phone._build_buttons()
		for button in phone.buttons:
			if int(button.key) in [KEY_Z,KEY_X]:check(button.rect.size.y==42,"confirm/back taller touch surface in "+context)
	# Width fixtures include a compact phone and both button state variants.
	ui.view="hub";ui.hub_controller.enter_room("H02")
	for spec in [[Vector2i(2202,1116),Rect2(0,0,2202,1116)],[Vector2i(1334,750),Rect2(0,0,1334,750)]]:
		screen.size=spec[0];phone.safe_area_override=spec[1];phone._layout();await frame("controls-"+str(spec[0].x),true)
		phone.fingers[99]=KEY_Z;await frame("controls-pressed-"+str(spec[0].x));phone.fingers.clear()
	ui.view="story_intro";ui.game.flags.story_intro_pending=true;ui.game.flags.story_intro_offset=0;ui.story_intro.start();ui.story_intro.process(3);await frame("intro-compact",true)
	check(ui.audio._get_stream("sfx","story_type")!=null,"typing audio imports and resolves through audio service")
	ui.story_intro.scene=3;ui._new_journey_in_slot()
	check(ui.story_intro.scene==0 and ui.story_intro.index==-1,"starting another new game resets the opening illustration and first confirmation")
	screen.queue_free();await process_frame
	presentation_completed=true
func run():
	DirAccess.make_dir_recursive_absolute(CACHE);DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	domain()
	check(domain_completed,"all domain assertions reached completion")
	if not OS.get_cmdline_user_args().has("--domain-only"):
		await presentation()
		check(presentation_completed,"all presentation assertions reached completion")
	var report={"checks":checks.size(),"errors":errors,"labels":checks,"screenshots":shots,"typing_ticks":ticks,"scope":"Targeted opening/journal, guard counter and migration, M12 world/hub progression, two phone layouts. Isolated temporary journals. No device update or full-campaign playthrough."}
	var f=FileAccess.open(OUT+("domain.json" if OS.get_cmdline_user_args().has("--domain-only") else "verification.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("OPENING_FEEDBACK checks=",checks.size()," errors=",errors);quit(0 if errors.is_empty() else 1)
