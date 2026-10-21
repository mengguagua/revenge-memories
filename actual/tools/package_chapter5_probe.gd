extends SceneTree
var checks=[]
var errors=[]
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
 var State=load("res://core/game_state.gd");var g=State.new()
 check(str(ProjectSettings.get_setting("application/config/version"))=="0.10.0","embedded version")
 check(g.stages.size()==40,"forty embedded battle maps")
 for id in g.ChapterFive.STAGES:
  var d=g.stages[id];check(int(d.chapter)==5 and ResourceLoader.exists(d.art_atlas),str(id)+" new map and terrain")
  for prop in d.art_props:check(ResourceLoader.exists(prop.path),str(id)+" complete architecture "+str(prop.path))
 check(ResourceLoader.exists("res://assets/chapter5/ending-coast.png"),"dedicated ending panorama embedded")
 check(not FileAccess.file_exists("res://source/chapter5/architecture-original.png"),"offline source art excluded")
 g.save_path=OS.get_environment("CH5_SOURCE");check(g.load_game(),"real chapter4 checkpoint loads outside project")
 var roster=g.roster.duplicate(true);var convoy=g.convoy.duplicate(true)
 g.save_path="/private/tmp/ch5-package-state.json";check(g.begin_chapter_five(),"exported chapter transition")
 check(g.roster==roster and g.convoy==convoy,"no growth injury inventory reset")
 check(g.start_battle(501),"exported initial battle entry");g.save_game();check(g.load_game() and g.retry_battle(),"exported battle reload retry")
 g.save_path=OS.get_environment("CH5_FINAL");check(g.load_game(),"real completed ending loads")
 check(g.chapter==5 and g.stage_cleared(534) and g.flags.ending_done,"completion flag and ending persistence")
 var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path=OS.get_environment("CH5_FINAL");check(ui.game.load_game(),"exported controller loads ending");ui.game.save_path="/private/tmp/ch5-package-ui.json";ui._resume_journey();await process_frame
 check(ui.view=="ending" and not ui.ending_pages.is_empty(),"ending controller resumes saved page")
 var after=ui.game.roster.duplicate(true);var items=ui.game.convoy.duplicate(true)
 ui._accept();check(ui.menu_actions.has("new:replay_ending"),"completed ending exposes concrete replay menu")
 ui._clear_menu();ui._menu_action("new:replay_ending","ending")
 check(ui.ending_index==0 and ui.game.roster==after and ui.game.convoy==items,"replay does not repeat rewards or heal")
 ui.queue_free();await process_frame;ui=null
 var f=FileAccess.open(OS.get_environment("CH5_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"external_pck":true},"  "));f.close()
 print("CH5_PACKAGE ",checks.size()," ",errors);quit(0 if errors.is_empty() else 1)
