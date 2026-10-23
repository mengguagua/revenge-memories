extends "res://tests/ch3_environment_play.gd"
const HUB_OUT="res://reports/chapter3-environment-20261023/hubs/"
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(HUB_OUT))
 var old="res://reports/chapter3-redesign-20261022/play/round2/round2-after-"
 var jobs=[
 {"room":"H30","source":"res://reports/chapter2-environment-20261023/play/continuous-after-lighthouse/continuous-after-lighthouse-chapter3-start.json"},
 {"room":"H31","source":old+"301.json"},{"room":"H32","source":old+"302.json"},{"room":"H33","source":old+"303.json"},
 {"room":"H34","source":old+"305.json"},{"room":"H35","source":old+"306.json"},{"room":"H36","source":old+"311.json"},{"room":"H37","source":old+"312.json"},
 {"room":"H10","source":"res://reports/chapter3-redesign-20261022/play/continuous-retry/continuous-retry-chapter-end.json"}]
 var records=[]
 for job in jobs:
  abort=false;var before=inputs;var source_hash=FileAccess.get_file_as_string(job.source).sha256_text()
  var working=HUB_OUT+"working-"+job.room+".json"
  DirAccess.copy_absolute(ProjectSettings.globalize_path(job.source),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Hub source missing "+job.room)
  if not abort:ui._resume_journey();await settle()
  if ui.view=="chapter_end":key(KEY_Z);choose("new:world");await settle();enter_hub();await settle()
  if not abort and (ui.view!="hub"or ui.game.hub_record!=job.room):record_failure("Wrong hub "+ui.view+" "+ui.game.hub_record)
  if not abort:
   walk_to(Vector2i(6,7));await settle();ui.game.save_path=HUB_OUT+job.room+".json";ui.game.save_game()
  if FileAccess.get_file_as_string(job.source).sha256_text()!=source_hash:record_failure("Source modified")
  records.append({"room":job.room,"source":job.source,"source_sha256":source_hash,"inputs":inputs-before,"passed":not abort})
  ui.queue_free();await process_frame;ui=null
 var f=FileAccess.open(HUB_OUT+"input-review.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"inputs":inputs,"records":records,"failures":failures,"position_or_flags_edited":false},"  "));f.close();quit(0 if failures.is_empty()else 1)
