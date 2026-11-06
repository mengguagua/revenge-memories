extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/full-assessment-20261025/story/"
var ui
var screen
var checks=[]
var failures=[]
var layouts=[]
var shots=[]
var visual=false
var cache=""
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func source(code:String)->String:
	if code=="M15":return "res://reports/campaign/natural-M15-deployment-save.json"
	if code in ["F31","F32"]:return State.read_json("res://reports/chapter3-environment-20261023/sources.json")[code]
	return "res://reports/full-playtest-20261023/ch%d/current/current-%s-deployment.json"%[4 if code in ["S41","S42"] else 3,code]
func setup(code:String):
	var g=State.new();g.save_path=source(code)
	check(g.load_game() and g.retry_battle(),code+" source copy enters current map")
	g.save_path=cache.path_join(code+".json");g.story_events.clear();ui.game=g
	ui.view="battle";ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu()
func inspect_pages(label:String,width:int):
	var count=0
	while ui.view=="plot" and count<30:
		ui.dialogue_reveal=99999;ui.queue_redraw();await process_frame;await process_frame
		if visual:await RenderingServer.frame_post_draw
		check(ui.view=="plot" and ui.plot_index<ui.plot_pages.size(),label+" valid page "+str(count))
		if visual:
			check(ui.layout_errors.is_empty(),label+" glyph/background safe area "+str(width)+" page "+str(count))
			layouts.append({"label":label,"width":width,"page":count,"text":ui.plot_pages[ui.plot_index],"errors":ui.layout_errors.duplicate(),"audit":ui.text_checks.duplicate()})
			if width==364 and count==0:
				var name=label+".png";screen.get_texture().get_image().save_png(OUT+name);shots.append(name)
		ui._advance_plot();await process_frame;count+=1
	check(count>0 and count<30 and ui.view=="battle",label+" completes all dialogue pages without truncation")
func run():
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	cache="/private/tmp/revenge-story-visual-"+str(Time.get_ticks_usec());DirAccess.make_dir_recursive_absolute(cache)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	screen=SubViewport.new();screen.size=Vector2i(364,240);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=cache;screen.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.elapsed=4;ui.instant_mode=true
	for width in [256,364]:
		screen.size=Vector2i(width,240);ui.set_meta("phone",width==364)
		for code in ["M15","F31","F32","M33","S41"]:
			setup(code);ui._menu_action("new:goal","system")
			await inspect_pages("goal-"+code,width)
		for code in ["S32","S42"]:
			setup(code);ui.game.find_unit("noya" if code=="S32" else "celine").hp=0
			if code=="S32":ui.game.ChapterThree.on_victory(ui.game)
			else:ui.game.ChapterFour.on_victory(ui.game)
			var pages=[]
			for event in ui.game.story_events:pages.append_array(event.pages)
			ui.game.story_events.clear();ui.play_pages(pages,"battle")
			await inspect_pages("casualty-"+code,width)
	var f=FileAccess.open(OUT+("visual-checks.json" if visual else "visual-logic-checks.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"visual":visual,"layouts":layouts,"screenshots":shots,"scope":"Actual objective menu and survival-branch dialogue rendering at 256/364 native pixels, backed by isolated controlled states; not device gameplay."},"  "));f.close()
	print("STORY_VISUAL ",checks.size()," failures: ",failures)
	ui.queue_free();screen.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)
