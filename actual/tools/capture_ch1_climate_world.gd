extends "res://tests/ch1_climate_play.gd"
const PHOTO_FOLDER="res://reports/chapter1-climate-20261022/world/screenshots/"
var vp:SubViewport
var photos=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func picture(name:String,source:String):
 ui.queue_redraw()
 for i in range(4):await process_frame
 await RenderingServer.frame_post_draw
 var path=PHOTO_FOLDER+name+".png";vp.get_texture().get_image().save_png(path)
 photos.append({"name":name,"path":path,"source":source,"chapter":ui.game.chapter,"chapter1_complete":ui.game.flags.get("chapter1_complete",false),"winter":ui._first_chapter_winter(),"view":ui.view,"world_node":ui.game.world_node,"layout_errors":ui.layout_errors.duplicate(),"overview_audit":ui.overview_audit.duplicate(true)})
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PHOTO_FOLDER))
 vp=SubViewport.new();vp.size=Vector2i(562,320);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var jobs=[
 {"name":"snow-village-world","source":"res://reports/chapter1-climate-20261022/side/hubs/H07.json"},
 {"name":"snow-grain-world","source":"res://reports/chapter1-climate-20261022/side/hubs/H02.json"},
 {"name":"snow-camp-world","source":"res://reports/chapter1-climate-20261022/side/hubs/H05.json"},
 {"name":"snow-coast-world","source":"res://reports/chapter1-climate-20261022/side/hubs/H06.json"},
 {"name":"spring-after-ceremony","source":"res://reports/chapter1-climate-20261022/play/continuous-recruits/continuous-recruits-chapter-end.json"}]
 for job in jobs:
  ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame;ui.instant_mode=true
  var original=FileAccess.get_file_as_string(job.source).sha256_text();ui.game.save_path=job.source
  if not ui.game.load_game():record_failure("Cannot load "+job.source)
  ui.game.save_path=PHOTO_FOLDER+"working.json"
  if not abort:ui._resume_journey();await settle()
  if ui.view=="chapter_end":key(KEY_Z);choose("new:world");await settle()
  for i in range(4):
   if abort or ui.view!="hub":break
   await leave_hub()
  if ui.view!="world":record_failure("World entry failed "+job.name)
  if not abort:
   await picture(job.name,job.source)
   key(KEY_S);choose("new:overview");await settle();await picture(job.name+"-overview",job.source)
   key(KEY_EQUAL);await picture(job.name+"-overview-zoom",job.source)
  if FileAccess.get_file_as_string(job.source).sha256_text()!=original:record_failure("Original source changed")
  ui.queue_free();await process_frame;ui=null
  if abort:break
 var errors=[]
 for p in photos:errors.append_array(p.layout_errors)
 var f=FileAccess.open(PHOTO_FOLDER+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort and errors.is_empty(),"shots":photos,"failures":failures,"layout_errors":errors,"inputs":inputs,"background_guard":true,"scope":"Native engine viewport. Genuine hub and ceremony checkpoint copies; normal leave-hub/world/overview input only, no season/position/flag edits."},"  "));f.close()
 vp.queue_free();await process_frame;quit(1 if abort or not errors.is_empty()else 0)
