extends SceneTree
var checks=[]
var errors=[]
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
 var State=load("res://core/game_state.gd")
 check(str(ProjectSettings.get_setting("application/config/version"))=="0.8.13","Embedded 0.8.13 version")
 var g=State.new();g.slot_directory="/private/tmp/revenge-journey-package-slots";DirAccess.make_dir_recursive_absolute(g.slot_directory);g.new_game()
 check(g.stages.size()==23,"All 23 existing campaign maps embedded")
 for slot in range(1,6):
  g.flags.package_marker=slot
  check(g.save_to_slot(slot),"Pack writes independent slot "+str(slot))
 for slot in range(1,6):check(g.load_slot(slot) and int(g.flags.package_marker)==slot,"Pack resumes independent slot "+str(slot))
 for name in ["snow-coast.png","journal-panel.png"]:
  var texture=load("res://assets/journey-home/"+name)
  check(texture!=null and texture.get_width()>0,"Generated production bitmap embedded: "+name)
 var ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=g.slot_directory;root.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);ui.journey.prepare_art()
 check(ui.view=="title" and ui.title_menu and ui.journey.records.size()==5,"Pack homepage immediately offers title choices and five records")
 ui.title_selected=1;ui._accept();ui.journey.selected=3;ui._accept()
 check(ui.view=="hub" and ui.game.active_slot==4 and int(ui.game.flags.package_marker)==4,"Pack UI resumes fourth journal through real menu path")
 var unchanged=FileAccess.get_file_as_bytes(ui.game.save_path);ui._show_title();ui.title_selected=0;ui._accept();ui.journey.selected=3;ui._accept()
 check(ui.view=="journal_confirm" and ui.journey.confirm_choice==0,"Pack new-game overwrite defaults to return")
 ui._accept();check(ui.view=="journal" and FileAccess.get_file_as_bytes(ui.game.save_path)==unchanged,"Pack cancellation preserves exact record bytes")
 var f=FileAccess.open(OS.get_environment("JOURNEY_PACKAGE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks.size(),"labels":checks,"errors":errors,"external_pack":true,"user_saves_touched":false},"  "));f.close()
 print("JOURNEY_PACK ",checks.size()," errors ",errors)
 ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
