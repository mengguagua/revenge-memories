extends "res://tests/ch5_environment_play.gd"
const HUB_OUT="res://reports/chapter5-environment-20261023/hubs/"
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(HUB_OUT))
 var jobs=[{"room": "H51", "source": "res://reports/chapter5-spatial-20261022/play/west-two/west-two-after-501.json"}, {"room": "H52", "source": "res://reports/chapter5-spatial-20261022/play/west-two/west-two-after-502.json"}, {"room": "H53", "source": "res://reports/chapter5-spatial-20261022/play/east-two/east-two-after-503.json"}, {"room": "H54", "source": "res://reports/chapter5-spatial-20261022/play/east-two/east-two-after-504.json"}, {"room": "H55", "source": "res://reports/chapter5-spatial-20261022/play/finale-two/finale-two-after-533.json"}, {"room": "H56", "source": "res://reports/chapter5-spatial-20261022/play/east-two/east-two-after-511.json"}]
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
