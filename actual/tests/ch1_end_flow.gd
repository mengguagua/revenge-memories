extends "res://tests/ch1_redesign_play.gd"
func run()->void:
 late_label="continuous-main-completion-final";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=LATE_OUT+"continuous-main/continuous-main-M15-victory.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Continuous victory snapshot failed")
 if not abort:ui._resume_journey();await settle();key(KEY_Z);choose("continue_world");await settle();await post_battle(105)
 var completed=ui.game.flags.get("chapter1_complete",false)
 if not abort and ui.view!="chapter_end":record_failure("Chapter end screen absent")
 if not abort:key(KEY_Z);choose("new:chapter2");await settle()
 if not abort and (ui.game.chapter!=2 or not ui.game.flags.get("chapter2_started",false)):record_failure("Chapter 2 transition did not open")
 if not abort:await snapshot("chapter2-start")
 var report={"passed":not abort,"source":source_checkpoint,"source_sha256":source_hash,"source_unchanged":FileAccess.get_file_as_string(source_checkpoint).sha256_text()==source_hash,"chapter1_complete":completed,"chapter":ui.game.chapter,"view":ui.view,"key_inputs":inputs,"failures":failures,"checkpoints":checkpoints,"scope":"Continue the first continuous M11→M15 genuine-input run from its exact victory snapshot; normal optional-side closure confirmation and chapter transition. No state edits."}
 var f=FileAccess.open(late_folder+"result.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("CH1_END_FLOW ",JSON.stringify(report))
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
