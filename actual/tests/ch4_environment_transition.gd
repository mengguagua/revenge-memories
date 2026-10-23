extends "res://tests/ch4_environment_play.gd"
func run():
 late_label="chapter-transition";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/chapter4-environment-20261023/play/round2-east/round2-east-after-408.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Real M33 post-battle source failed")
 if not abort:ui._resume_journey();await settle();await leave_hub();await go(9);enter_hub();await settle();await hub_action("third_council");await hub_action("third_messenger");choose("hub:fourth_finish");await settle();await snapshot("chapter-end")
 if not abort and not ui.game.flags.get("chapter4_complete",false):record_failure("Chapter4 did not finish")
 if not abort:
  key(KEY_Z);choose("new:chapter5");await settle();await snapshot("chapter5-start")
  if ui.game.chapter!=5:record_failure("Chapter5 did not open")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source evidence changed")
 var f=FileAccess.open("res://reports/chapter4-environment-20261023/flow-continuation.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"source":source_checkpoint,"source_sha256":source_hash,"inputs":inputs,"chapter":ui.game.chapter,"chapter4_complete":ui.game.flags.get("chapter4_complete",false),"checkpoints":checkpoints,"failures":failures,"source_modified":false,"scope":"Isolated chapter transition from this round real F44 post-battle record; ordinary travel, council, chapter finish and fifth chapter entry. Not a new-game continuous playthrough.","description":"十图两轮逐关通关之外，从本轮F44真实战后记录正常返回会合营站，完成第四章收束并进入第五章；不修改记录中的战果、伤情或剧情标记。"},"  "));f.close()
 ui.queue_free();await process_frame;ui=null;call_deferred("quit",0 if not abort else 1)
