extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/m15-story-20261101/"
const TEMP="/private/tmp/m15-story-20261101/"
var checks=[]
var failures=[]
var observed=[]
var shots=[]
var visual=false
var screen
var phone
var ui

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append({"label":label,"passed":ok})
	if not ok:failures.append(label);push_error(label)
func same(a,b)->bool:
	# JSON loads integral numbers as floats; compare canonical saved values.
	return JSON.stringify(JSON.parse_string(JSON.stringify(a)))==JSON.stringify(JSON.parse_string(JSON.stringify(b)))
func battle()->RefCounted:
	var g=State.new();g.new_game();g.save_path=TEMP+"working.json";g.world_node=6;g.previous_world_node=5;g.route_positions.alm=6
	check(g.start_battle(105),"M15 starts through the ordinary stage entry")
	return g
func texts(g)->String:
	var lines=[]
	for event in g.story_events:
		for page in event.pages:lines.append(str(page.speaker)+"："+str(page.text))
	return "／".join(lines)
func death(g):
	g.commit_strike({"attacker":"hunapu","defender":"M15_boss","hp_after":0})
func logic():
	var g=battle()
	check(g.story_events[0].get("m15_scene")=="opening" and texts(g).contains("海峡城的旧塔堡") and texts(g).contains("胡纳普：科兰！／科兰：谁？"),"opening scene uses the current manually approved script")
	check(g.stages[105].name_zh=="海峡城·旧塔堡","battle title identifies the fort within strait city")
	var before=g.units.duplicate(true);g.story_events.clear();var boss=g.find_unit("M15_boss")
	for sample in [[5,1,false],[6,20,false],[6,19,true],[8,40,true]]:
		g.turn=sample[0];boss.hp=sample[1]
		check(g.M15Story.escaping(g,boss)==sample[2],"existing escape timing remains exact: "+str(sample))
	g.turn=6;boss.hp=19;g.ai_action(boss)
	check(g.story_events.size()==1 and g.story_events[0].get("m15_scene")=="escape" and texts(g)=="科兰：趁现在，从北门走。","first escape queues only the approved whisper")
	g.ai_action(boss);check(g.story_events.size()==1,"repeat AI planning cannot repeat escape scene")
	check(same(g.units.map(func(u):return u.position),before.map(func(u):return u.position)),"planning a cinematic never moves units")
	g=battle();g.story_events.clear()
	var door=g.battle_data.objects[0]
	var leader=g.find_unit("hunapu");leader.position=[door.position[0],door.position[1]+1];g.selected_id=leader.id
	check(g.interact(str(door.id)) and texts(g)=="劳工：门开了！后面的跟上。","opening the first cell does not trigger the confrontation")
	g.story_events.clear();g.M15Story.first_exchange(g,{"attacker":"M15_boss","defender":"hunapu"})
	check(texts(g).contains("凭什么处决他！") and texts(g).contains("他放走的是村民！"),"first exchange also works when Korlan initiates combat")
	g.M15Story.first_exchange(g,{"attacker":"hunapu","defender":"M15_boss"});check(g.story_events.size()==1,"first exchange is one-time")
	g=battle();g.story_events.clear();g.flags.quest.escape_announced=true;g.M15Story.first_exchange(g,{"attacker":"hunapu","defender":"M15_boss"})
	check(g.story_events.is_empty(),"first contact during escape skips the face-the-enemy challenge")
	g=battle();g.story_events.clear();var snapshot=g.units.duplicate(true);death(g)
	check(g.story_events.size()==1 and g.story_events[0].get("m15_scene")=="death" and not g.flags.quest.get("escape_announced",false),"fatal damage immediately queues the farewell before any rescue or escape")
	check(texts(g).contains("旁白：胡纳普挥下最后一击。／科兰：不……我不能死在这里……／胡纳普：哥哥……"),"the narrator, Korlan and Hunapu speak in the approved order")
	g.M15Story.first_exchange(g,{"attacker":"hunapu","defender":"M15_boss"});check(g.story_events.size()==1,"fatal first hit never adds a challenge after the farewell")
	check(g.check_outcome().is_empty(),"Korlan's death alone cannot bypass locked labor rescue")
	check(g.save_game(),"pending cinematic queue is a valid resumable battle save")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and same(loaded.units,g.units) and loaded.story_events[0].get("m15_scene")=="death","pending death scene survives load without changing combat or rescue data")
	g.story_events.clear();g.find_unit("M15_workers0").locked=false;g.find_unit("M15_workers1").hp=0
	check(g.check_outcome()=="victory" and g.complete_battle(),"one real surviving rescued group still permits victory")
	check(not g.story_events.any(func(e):return e.key=="D13") and texts(g).contains("剩下的粮食分给附近几个村子。"),"victory after the farewell adds the separate field cleanup")
	var convoy=g.convoy.duplicate(true);check(not g.complete_battle() and same(convoy,g.convoy),"repeat settlement cannot duplicate equipment rewards")
	g=battle();g.story_events.clear();g.find_unit("M15_boss").position=g.battle_data.exit.duplicate();check(g.check_outcome()=="defeat","live Korlan reaching the north exit remains failure")
	g=battle();g.find_unit("M15_workers0").hp=0;g.find_unit("M15_workers1").hp=0;check(g.check_outcome()=="defeat","both labor groups dying remains failure")
	g=State.new();g.new_game();g.save_path=TEMP+"missing.json";g.roster.otto.hp=0;g.world_node=6;g.start_battle(105)
	check(texts(g).contains("村民：粮车往北门走了。守军堵在前面。") and not texts(g).contains("奥托："),"unavailable Otto has the approved opening substitute")
	g.story_events.clear();g.story_on_victory()
	check(texts(g).contains("村民：缴械的人不要为难。") and not texts(g).contains("奥托："),"unavailable Otto also retains the approved field-cleanup substitute")
	g=battle();g.story_events.clear();g.flags.erase("seen_D13");g.find_unit("M15_boss").hp=0;g.find_unit("M15_workers0").locked=false;g.check_outcome();g.complete_battle()
	check(g.story_events[0].get("m15_scene")=="death","old pending victory without a farewell receives one compatible ending")
	g=battle();g.story_events.clear();g.flags.active_plot={"pages":[{"speaker":"胡纳普","text":"凯尔回营的时候，你答应过放人。"},{"speaker":"科兰","text":"他已经把人放走了。他让整支军队看见，命令可以不听。"}],"index":0,"return":"battle","callback":""}
	g.M15Story.restore(g)
	check(g.flags.get("m15_scene",{}).get("scene")=="death" and not g.flags.has("active_plot"),"legacy active D13 becomes the current resumable farewell")
	g=battle();g.battle_start_snapshot.story_events[0].erase("m15_scene");g.battle_start_snapshot.story_events[0].pages=[{"speaker":"胡纳普","text":"这里就是旧塔堡。凯尔被押回营那天，我只走到过这道门。"}]
	check(g.retry_battle() and g.story_events[0].get("m15_scene")=="opening" and texts(g).contains("海峡城的旧塔堡"),"retrying an old entry checkpoint also receives current prose and staging")

func settle()->void:
	for i in range(500):
		if ui.view=="plot":
			var page=ui.plot_pages[ui.plot_index];var line=str(page.text).replace("\n","")
			if not observed.has(line):observed.append(line)
			ui.dialogue_reveal=10000;ui._accept()
		await process_frame
		if not ui.m15_scene.active and ui.view!="plot" and not ui.busy:return
	check(false,"cinematic releases input: "+str(ui.m15_scene.state))

func start_events(g)->void:
	ui.game=g;ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false;ui.instant_mode=true
	ui._play_story_events()

func runtime():
	var g=battle();var starting=g.units.duplicate(true);start_events(g);await settle()
	check(observed.has("这里就是海峡城的旧塔堡，凯尔……") and ui.view=="battle" and not g.flags.has("m15_scene"),"actual opening pager plays all groups and returns battle control")
	check(same(g.units,starting),"opening never mutates combat formation")
	g.story_events.clear();death(g);var after_hit=g.units.duplicate(true);start_events(g);await settle()
	check(g.flags.get("korlan_dead",false) and not g.flags.has("m15_scene") and ui.view=="battle","actual farewell visibly ends death and permits remaining rescue")
	check(same(g.units,after_hit),"death animation performs no extra attack, damage, healing or movement")
	check(observed.has("胡纳普挥下最后一击。") and observed.has("哥哥……"),"actual pager plays the narrated strike and the final response")
	for cell in [[20,10],[28,3],[28,6]]:
		g.find_unit("M15_boss").position=cell
		var staged=ui.m15_scene.hero_cell();var hero=g.find_unit("hunapu")
		check(g.in_bounds(staged) and g.movement_cost(hero,staged)<255 and g.can_stop(hero,staged),"farewell stages Hunapu on real free ground near "+str(cell))
	# A genuine planned combat drives the normal contact, death hook, cinematic
	# and EXP flow. Only this isolated fixture gives the boss one remaining HP.
	g=battle();g.story_events.clear();ui.game=g;ui.view="battle";ui.busy=false;ui.instant_mode=true
	var hero=g.find_unit("hunapu");hero.position=[19,10];hero.strength=30;hero.skill=30;g.find_unit("M15_boss").hp=1
	ui._play_combat("hunapu","M15_boss")
	for i in range(700):
		if ui.view=="plot":ui.dialogue_reveal=10000;ui._accept()
		elif ui.view=="reward":ui._accept()
		await process_frame
		if ui.view=="battle" and not ui.busy and not ui.m15_scene.active:break
	check(g.find_unit("M15_boss").hp==0 and g.flags.get("korlan_dead",false) and ui.view=="battle","normal combat contact plays the farewell and returns to unfinished rescue")
	check(float(ui.combat_fades.get("M15_boss",1.0))==1.0,"fatal combat never fades Korlan out before the kneeling scene")
	check(g.kills==1,"the animation adds no second killing blow")
	for checkpoint in [3,4,5]:
		g=battle();g.story_events.clear();death(g);var event=g.story_events.pop_front();ui.game=g;ui.view="battle";ui.busy=false
		ui.set_process(false);ui.m15_scene.start(event,"battle");ui.m15_scene._enter(checkpoint);ui.m15_scene.state.time=0.5;ui.dialogue_reveal=10000
		if checkpoint==3:ui.game.flags.active_plot.index=0
		ui.m15_scene._persist();g.save_path=TEMP+"checkpoint-"+str(checkpoint)+".json";check(g.save_game(),"save current farewell step "+str(checkpoint))
		var invalid=State.read_json(g.save_path);invalid.flags.m15_scene.step=99
		check(not g.SaveValidation.campaign_valid(g,invalid,g.SAVE_FIELDS),"invalid scene checkpoint cannot enter an endless replay "+str(checkpoint))
		var saved_units=g.units.duplicate(true);var saved_rng=g.rng_state
		var restored=State.new();restored.save_path=g.save_path
		check(restored.load_game() and same(restored.units,saved_units) and restored.rng_state==saved_rng,"load farewell step preserves units and RNG "+str(checkpoint))
		ui.m15_scene.active=false;ui.plot_finished=true;await process_frame;await process_frame
		ui.game=restored;ui.busy=false;ui.set_process(true);ui._resume_journey();await settle()
		check(restored.flags.get("korlan_dead",false) and not restored.flags.has("m15_scene") and not restored.flags.has("active_plot"),"resumed farewell finishes without a duplicate or orphan page "+str(checkpoint))
		check(same(restored.units,saved_units),"resumed ending leaves rescue state and formation intact "+str(checkpoint))
	# UI interception owns the scene before the ordinary AI movement begins.
	g=battle();g.story_events.clear();g.turn=8;ui.game=g;ui.view="battle";ui.busy=true;ui.instant_mode=true
	var boss=g.find_unit("M15_boss");var at=boss.position.duplicate();ui._run_ai_unit(boss)
	check(ui.m15_scene.active and same(boss.position,at),"escape tableau starts before actual northbound movement")
	for i in range(200):
		if ui.view=="plot":ui.dialogue_reveal=10000;ui._accept()
		await process_frame
		if not ui.m15_scene.active and boss.acted:break
	check(not ui.m15_scene.active and boss.acted and not same(boss.position,at),"ordinary AI movement follows the completed escape cue")
	ui.busy=false

func frame(name:String):
	ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
	if visual:
		await RenderingServer.frame_post_draw
		check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text stays inside bitmap content safe areas "+str(ui.layout_errors)+str(phone.layout_errors))
		screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")

func tableau(scene:String,step:int,time:float,pages:Array,name:String):
	ui.m15_scene.state={"version":1,"scene":scene,"step":step,"time":time,"clock":time,"return":"battle","pages":pages}
	ui.m15_scene.steps=ui.m15_scene._steps(scene,pages);ui.m15_scene.active=true;ui.view="m15_scene";ui.busy=true
	var shot=ui.m15_scene.steps[step]
	if str(shot.kind)=="dialogue":
		ui.plot_pages.clear()
		for page in shot.pages:ui.plot_pages.append_array(ui._paginate_plot(page))
		ui.plot_index=0;ui.dialogue_reveal=10000;ui.view="plot"
	await frame(name)

func visuals():
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=false
	ui.game=battle();var opening=ui.game.story_events[0].pages.duplicate(true);ui.game.story_events.clear()
	await tableau("opening",0,1.25,opening,"01-grain-northbound")
	await tableau("opening",3,0.0,opening,"02-korlan-command")
	await tableau("escape",1,0.0,ui.game.campaign.scenes.M15_ESCAPE,"03-quiet-departure")
	ui.game.find_unit("M15_boss").hp=0
	var pages=ui.game.campaign.scenes.D13
	await tableau("death",1,0.0,pages,"04-last-confrontation")
	await tableau("death",3,0.0,pages,"05-last-words")
	await tableau("death",4,0.65,pages,"06-arm-gives-way")
	await tableau("death",5,0.0,pages,"07-death-pause")
	await tableau("death",6,0.0,pages,"08-revenge-confirmed")
	check(not visual or ui.m15_scene.audit.get("corpse_still",false),"corpse remains visibly still during revenge confirmation")
	if visual:
		screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout()
		await tableau("death",3,0.0,pages,"09-compact-last-words")
		await tableau("death",6,0.0,pages,"10-compact-revenge")
		ui.game.find_unit("M15_boss").position=[28,3]
		await tableau("death",6,0.0,pages,"11-northgate-farewell")
	ui.m15_scene.active=false

func run():
	DirAccess.make_dir_recursive_absolute(TEMP+"slots")
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	logic()
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=TEMP+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.instant_mode=true;ui.game.save_path=TEMP+"ui.json"
	await runtime();await visuals()
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	await create_timer(0.25).timeout
	var f=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"checks":checks,"failures":failures,"observed":observed,"screenshots":shots,"fixture_tests":true,"iphone_updated":false},"  "));f.close()
	print("M15_STORY ",checks.size()," checks; failures=",failures);quit(0 if failures.is_empty() else 1)
