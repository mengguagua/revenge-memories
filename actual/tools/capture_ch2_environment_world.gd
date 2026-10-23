extends "res://tests/ch2_redesign_play.gd"
const PHOTO_FOLDER="res://reports/chapter2-environment-20261023/world/screenshots/"
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
 var tint=ui._second_chapter_world_tint(Vector2(ui.world.nodes[str(ui.game.world_node)].position[0],ui.world.nodes[str(ui.game.world_node)].position[1]))
 photos.append({"name":name,"path":path,"source":source,"chapter":ui.game.chapter,"F22_confirmed":ui.game.flags.get("F22_confirmed",false),"blackday":ui._second_chapter_blackday(),"western_winter":ui._world_uses_winter(),"view":ui.view,"world_node":ui.game.world_node,"node_tint":[tint.r,tint.g,tint.b],"layout_errors":ui.layout_errors.duplicate(),"overview_audit":ui.overview_audit.duplicate(true)})
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PHOTO_FOLDER))
 vp=SubViewport.new();vp.size=Vector2i(562,320);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var hub="res://reports/chapter2-environment-20261023/hubs/"
 var jobs=[
 {"name":"H21-windlamp-before","source":hub+"H21.json","node":17},
 {"name":"H22-flotilla-before","source":hub+"H22.json","node":18},
 {"name":"H23-escort-after","source":hub+"H23.json","node":19},
 {"name":"H24-reef-after","source":hub+"H24.json","node":20},
 {"name":"H25-beacon-after","source":hub+"H25.json","node":21},
 {"name":"H26-harbor-after","source":hub+"H26.json","node":22},
 {"name":"ancient-passage-light","source":hub+"H26.json","node":23}]
 for job in jobs:
  ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame;ui.instant_mode=true
  var original=FileAccess.get_file_as_string(job.source).sha256_text();ui.game.save_path=job.source
  if not ui.game.load_game():record_failure("Cannot load "+job.source)
  ui.game.save_path=PHOTO_FOLDER+"working.json"
  if not abort:ui._resume_journey();await settle()
  if not abort and ui.game.hub_record=="H21":await hub_action("east_departure")
  if not abort:await leave_hub()
  if not abort and ui.game.world_node!=job.node:await go(job.node)
  if not abort and ui.view!="world":record_failure("World entry failed "+job.name)
  if not abort:
   await picture(job.name,job.source)
   key(KEY_S);choose("new:overview");await settle();await picture(job.name+"-overview",job.source)
   key(KEY_EQUAL);await picture(job.name+"-overview-zoom",job.source)
  if FileAccess.get_file_as_string(job.source).sha256_text()!=original:record_failure("Original source changed")
  ui.queue_free();await process_frame;ui=null
  for cleanup_frame in range(3):await process_frame
  if abort:break
 var errors=[]
 for p in photos:errors.append_array(p.layout_errors)
 var f=FileAccess.open(PHOTO_FOLDER+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort and errors.is_empty(),"shots":photos,"failures":failures,"layout_errors":errors,"inputs":inputs,"background_guard":true,"scope":"Native viewport from genuine six hub checkpoints (H27 is story-locked; node23 reached from H26 by ordinary travel). Departure/dialogue/world/overview input only; no flags, position or statistics edited."},"  "));f.close()
 vp.queue_free();await process_frame;vp=null
 for cleanup_frame in range(3):await process_frame
 quit(1 if abort or not errors.is_empty()else 0)
