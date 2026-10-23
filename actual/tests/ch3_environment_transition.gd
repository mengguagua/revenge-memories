extends "res://tests/ch3_environment_play.gd"
func run():
 late_label="chapter-transition";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/chapter3-environment-20261023/play/round2/round2-after-303.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Real M33 post-battle source failed")
 if not abort:ui._resume_journey();await settle();await leave_hub();await go(9);enter_hub();await settle();await hub_action("third_council");await leave_hub();await switch_team();await go(9);enter_hub();await settle();await hub_action("third_council");await snapshot("council")
 if not abort:await hub_action("third_relations");await hub_action("third_messenger");choose("hub:third_finish");await settle();await snapshot("chapter-end")
 if not abort and not ui.game.flags.get("chapter3_complete",false):record_failure("Chapter3 did not finish")
 if not abort:
  key(KEY_Z);choose("new:chapter4");await settle();await snapshot("chapter4-start")
  if ui.game.chapter!=4:record_failure("Chapter4 did not open")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source evidence changed")
 var f=FileAccess.open("res://reports/chapter3-environment-20261023/flow-continuation.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"source":source_checkpoint,"source_sha256":source_hash,"inputs":inputs,"chapter":ui.game.chapter,"chapter3_complete":ui.game.flags.get("chapter3_complete",false),"checkpoints":checkpoints,"failures":failures,"source_modified":false,"scope":"From this round's real M33 post-battle checkpoint, normal travel/team switching to shared camp, council, relations, chapter finish and fourth chapter entry. This is an isolated chapter-transition check, not a fresh continuous whole-chapter playthrough.","description":"两轮逐关通关之外，从本轮M33战后真实记录正常调动两队到营站，完成会谈与分兵并进入第四章。额外的整章连续尝试在继承多名濒死队员的M31处达到驾驶回合上限，未计作通关；不修改难度或伤情。"},"  "));f.close()
 ui.queue_free();await process_frame;ui=null;call_deferred("quit",0 if not abort else 1)
