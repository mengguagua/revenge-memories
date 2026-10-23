extends "res://tests/ch2_redesign_play.gd"
## Copy genuine playthrough checkpoints, then reach rooms only by normal inputs.
const HUB_OUT="res://reports/chapter2-environment-20261023/hubs/"
var hub_records=[]
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(HUB_OUT))
 var base="res://reports/chapter2/play/natural-after-"
 var jobs=[
  {"room":"H21","source":"res://reports/chapter1-climate-20261022/play/continuous-recruits/continuous-recruits-chapter2-start.json","node":-1},
  {"room":"H22","source":base+"201-save.json","node":-1},
  {"room":"H23","source":base+"202-save.json","node":-1},
  {"room":"H24","source":base+"203-save.json","node":-1},
  {"room":"H25","source":base+"204-save.json","node":-1},
  {"room":"H26","source":base+"205-save.json","node":-1},
  {"room":"H27","source":"res://reports/chapter2-redesign-20261022/play/round2-other/round2-other-arrival-hub.json","node":-1}]
 for job in jobs:
  abort=false;var start_inputs=inputs;var source_hash=FileAccess.get_file_as_string(job.source).sha256_text()
  var working=HUB_OUT+"working-"+job.room+".json"
  DirAccess.copy_absolute(ProjectSettings.globalize_path(job.source),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Source not loadable "+job.source)
  if not abort:ui._resume_journey();await settle()
  if not abort and ui.view=="victory":key(KEY_Z);choose("continue_world");await settle()
  if not abort and job.node>=0:
   if ui.view=="hub":await leave_hub()
   await go(job.node)
   if not abort:enter_hub();await settle()
  if not abort and (ui.view!="hub" or ui.game.hub_record!=job.room):record_failure("Wrong room: "+ui.view+" "+ui.game.hub_record)
  if not abort:
   # Position by ordinary walk inputs, so the south approach and every actor remain visible.
   walk_to(Vector2i(6,7));await settle()
   ui.game.save_path=HUB_OUT+job.room+".json";ui.game.save_game()
  if FileAccess.get_file_as_string(job.source).sha256_text()!=source_hash:record_failure("Source modified")
  hub_records.append({"room":job.room,"source":job.source,"source_sha256":source_hash,"save":HUB_OUT+job.room+".json","inputs":inputs-start_inputs,"mode":ui.game.mode,"position":[ui.game.hub_position.x,ui.game.hub_position.y],"passed":not abort})
  print("CLIMATE_HUB_INPUT ",job.room," ",not abort," ",inputs-start_inputs)
  ui.queue_free();await process_frame;ui=null
 var f=FileAccess.open(HUB_OUT+"input-review.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":failures.is_empty(),"failures":failures,"records":hub_records,"inputs":inputs,"source_saves_modified":false,"positions_flags_stats_edited":false},"  "));f.close()
 quit(0 if failures.is_empty() else 1)
