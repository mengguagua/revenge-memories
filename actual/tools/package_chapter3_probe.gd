extends SceneTree
## Run this script outside the project against the exported PCK.
var checks=[]
var errors=[]
func check(ok,label):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
	var State=load("res://core/game_state.gd");var g=State.new()
	check(str(ProjectSettings.get_setting("application/config/version"))=="0.8.0","embedded application version")
	check(g.stages.size()==23,"embedded campaign contains 23 battle maps")
	for id in g.ChapterThree.STAGES:
		var d=g.stages[id]
		check(int(d.chapter)==3 and ResourceLoader.exists(d.art_atlas),str(id)+" map and atlas load")
		for prop in d.get("art_props",[]):check(ResourceLoader.exists(prop.path),str(id)+" complete architecture "+str(prop.path))
		for object in d.objects:
			if object.get("sprite_path","")!="":check(ResourceLoader.exists(object.sprite_path),str(id)+" object image")
	g.save_path=OS.get_environment("CH3_OLD_CHECKPOINT")
	check(g.load_game(),"external genuine second chapter checkpoint loads without project sources")
	var roster=g.roster.duplicate(true);var items=g.convoy.duplicate(true)
	g.save_path="/private/tmp/ch3-package-output.json"
	check(g.begin_chapter_three(),"exported second-to-third chapter transition")
	check(g.roster==roster and g.convoy==items,"transition preserves both actual parties and items")
	g.flags.D31_done=true;g.mode="world";check(g.start_battle(301),"exported west street battle entry")
	check(g.save_game(),"exported checkpoint write");check(g.load_game() and g.retry_battle(),"exported battle reload and retry")
	g.save_path=OS.get_environment("CH3_FINAL_CHECKPOINT");check(g.load_game(),"external real third-chapter completion loads")
	check(g.chapter==3 and g.flags.get("chapter3_complete",false) and g.treatment_remaining()==2,"meeting resource and completion persist")
	g.mode="world";check(g.switch_route() and g.units.is_empty() and g.battle_start_snapshot.is_empty(),"exported route switching clears stale encounter")
	check(ResourceLoader.exists("res://assets/original/graphics/portraits/portrait_41.png"),"existing Noya portrait is embedded")
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game.save_path=OS.get_environment("CH3_FINAL_CHECKPOINT");check(ui.game.load_game(),"exported controller loads final state")
	ui.game.save_path="/private/tmp/ch3-package-ui.json";ui.view="chapter_end"
	ui._accept();check(ui.menu_actions.has("new:world"),"chapter-end offers return to completed world")
	ui._clear_menu();ui.game.mode="world";ui.view="world";ui._show_result()
	check(ui.view=="world","stale result request cannot reopen completed battle")
	ui.result_sequence_running=true;ui.view="victory";ui._accept()
	check(ui.menu_items.is_empty(),"fast confirmation blocked until settlement finishes")
	ui.result_sequence_running=false;ui.view="world"
	ui.queue_free();await process_frame;ui=null
	var out=OS.get_environment("CH3_PACKAGE_REPORT");var f=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"external_pck":true},"  "));f.close()
	print("CH3_PACKAGE ",checks.size()," ",errors);quit(0 if errors.is_empty() else 1)
