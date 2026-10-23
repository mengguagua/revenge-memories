extends "res://tests/ch3_environment_play.gd"
const PHOTO_FOLDER="res://reports/chapter3-environment-20261023/world/screenshots/"
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
 photos.append({"name":name,"path":path,"source":source,"chapter":ui.game.chapter,"F22_confirmed":ui.game.flags.get("F22_confirmed",false),"blackday":ui._world_has_eastern_blackday(),"western_winter":ui._world_uses_winter(),"view":ui.view,"world_node":ui.game.world_node,"node_tint":[tint.r,tint.g,tint.b],"layout_errors":ui.layout_errors.duplicate(),"overview_audit":ui.overview_audit.duplicate(true)})
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PHOTO_FOLDER))
 vp=SubViewport.new();vp.size=Vector2i(562,320);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var hub="res://reports/chapter3-environment-20261023/hubs/"
 var jobs=[
 {"name":"west-city","source":hub+"H31.json","node":6},
 {"name":"supply-road","source":hub+"H32.json","node":7},
 {"name":"coastal-fort","source":hub+"H33.json","node":8},
 {"name":"meeting-camp","source":hub+"H10.json","node":9},
 {"name":"salt-road","source":hub+"H34.json","node":24},
 {"name":"refinery","source":hub+"H35.json","node":25},
 {"name":"village","source":hub+"H36.json","node":35},
 {"name":"salt-camp","source":hub+"H37.json","node":36}]
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
 var f=FileAccess.open(PHOTO_FOLDER+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort and errors.is_empty(),"shots":photos,"failures":failures,"layout_errors":errors,"inputs":inputs,"background_guard":true,"scope":"Native viewport from genuine input-reached chapter-three hubs. Ordinary leave-hub/world/overview/zoom input only; no flag, position or statistic edits."},"  "));f.close()
 vp.queue_free();await process_frame;vp=null
 for cleanup_frame in range(3):await process_frame
 quit(1 if abort or not errors.is_empty()else 0)
