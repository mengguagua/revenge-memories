extends "res://tests/full_audit_ch1.gd"
func run()->void:
 late_label="failure-recovery";late_folder=LATE_OUT+late_label+"/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var source="res://reports/full-playtest-20261023/ch1/audit/working-S11.json"
 var source_hash=FileAccess.get_file_as_string(source).sha256_text()
 var working=late_folder+"working-S11.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine failed S11 checkpoint does not load")
 if not abort:
  ui._resume_journey();await settle()
  if ui.view!="defeat":record_failure("Failure did not resume defeat UI")
 if not abort:
  key(KEY_Z);choose("retry");await settle()
  if ui.view!="battle" or ui.game.turn!=1 or not ui.game.battle_outcome.is_empty():record_failure("Normal Retry did not reenter initial battle")
  elif int(ui.game.find_unit("S11_miners0").hp)<=0 or int(ui.game.find_unit("S11_miners1").hp)<=0:record_failure("Retry retained failed escort death")
  else:await snapshot("S11-retry-entry")
 if not abort:
  key(KEY_S);choose("new:prepare");await settle()
  if ui.view!="world" or ui.game.mode!="world":record_failure("Return to preparation did not release the failed battle")
  else:await snapshot("after-failure-recovery")
 if FileAccess.get_file_as_string(source).sha256_text()!=source_hash:record_failure("Original defeat evidence changed")
 late_records.append({"code":"S11","outcome":"victory","scope":"No repeated combat; genuine defeat -> Retry -> current battle -> preparation","source":source,"source_sha256":source_hash,"failures":failures.duplicate(),"final_view":ui.view,"inputs":inputs})
 write_progress();print("FAILURE_RECOVERY ",JSON.stringify({"passed":failures.is_empty(),"failures":failures,"inputs":inputs}))
 ui.queue_free();await process_frame;ui=null;quit(0 if failures.is_empty() else 1)
