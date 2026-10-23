extends "res://tests/ch4_environment_play.gd"
const HUB_OUT="res://reports/chapter4-environment-20261023/hubs/"
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(HUB_OUT))
 var jobs=[{"room": "H41", "source": "res://reports/chapter4-redesign-20261022/play/round2-M41/round2-M41-after-401.json"}, {"room": "H42", "source": "res://reports/chapter4-redesign-20261022/play/round2-west/round2-west-after-402.json"}, {"room": "H43", "source": "res://reports/chapter4-redesign-20261022/play/round2-west/round2-west-after-403.json"}, {"room": "H44", "source": "res://reports/chapter4-redesign-20261022/play/final-M44-two/final-M44-two-after-404.json"}, {"room": "H45", "source": "res://reports/chapter4-redesign-20261022/play/final-east-two/final-east-two-after-405.json"}, {"room": "H46", "source": "res://reports/chapter4-redesign-20261022/play/final-east-two/final-east-two-after-406.json"}, {"room": "H47", "source": "res://reports/chapter4-redesign-20261022/play/round2-rescue/round2-rescue-after-407.json"}, {"room": "H48", "source": "res://reports/chapter4-redesign-20261022/play/final-east-two/final-east-two-after-408.json"}, {"room": "H49", "source": "res://reports/chapter4-redesign-20261022/play/round2-west/round2-west-after-411.json"}, {"room": "H50", "source": "res://reports/chapter4-redesign-20261022/play/round2-rescue/round2-rescue-after-412.json"}, {"room": "H10", "source": "res://reports/chapter3-environment-20261023/play/chapter-transition/chapter-transition-chapter4-start.json"}]
 var records=[]
 for job in jobs:
  abort=false;var before=inputs;var source_hash=FileAccess.get_file_as_string(job.source).sha256_text()
  var working=HUB_OUT+"working-"+job.room+".json"
  DirAccess.copy_absolute(ProjectSettings.globalize_path(job.source),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Hub source missing "+job.room)
  if not abort:ui._resume_journey();await settle()
  if ui.view in ["chapter_end","world"]:
   if ui.view=="chapter_end":key(KEY_Z);choose("new:world");await settle()
   enter_hub();await settle()
  if not abort and (ui.view!="hub"or ui.game.hub_record!=job.room):record_failure("Wrong hub "+ui.view+" "+ui.game.hub_record)
  if not abort:
   walk_to(Vector2i(6,7));await settle();ui.game.save_path=HUB_OUT+job.room+".json";ui.game.save_game()
  if FileAccess.get_file_as_string(job.source).sha256_text()!=source_hash:record_failure("Source modified")
  records.append({"room":job.room,"source":job.source,"source_sha256":source_hash,"inputs":inputs-before,"passed":not abort})
  ui.queue_free();await process_frame;ui=null
 var f=FileAccess.open(HUB_OUT+"input-review.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"inputs":inputs,"records":records,"failures":failures,"position_or_flags_edited":false},"  "));f.close();quit(0 if failures.is_empty()else 1)
