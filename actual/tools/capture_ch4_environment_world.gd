extends "res://tests/ch4_environment_play.gd"
const PHOTO_FOLDER="res://reports/chapter4-environment-20261023/world/screenshots/"
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
 photos.append({"name":name,"path":path,"source":source,"chapter":ui.game.chapter,"F22_confirmed":ui.game.flags.get("F22_confirmed",false),"blackday":ui._world_has_eastern_blackday(),"western_winter":ui._world_uses_winter(),"local_trial":ui.game.flags.get("island_loop_safe",false),"verified":ui.game.flags.get("D42_done",false),"view":ui.view,"world_node":ui.game.world_node,"node_tint":[tint.r,tint.g,tint.b],"layout_errors":ui.layout_errors.duplicate(),"overview_audit":ui.overview_audit.duplicate(true)})
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PHOTO_FOLDER))
 vp=SubViewport.new();vp.size=Vector2i(562,320);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var hub="res://reports/chapter4-environment-20261023/hubs/"
 var jobs=[{"name": "snow-village", "source": "res://reports/chapter4-environment-20261023/hubs/H41.json", "node": 10}, {"name": "cavalry-pass", "source": "res://reports/chapter4-environment-20261023/hubs/H42.json", "node": 11}, {"name": "north-tower", "source": "res://reports/chapter4-environment-20261023/hubs/H43.json", "node": 12}, {"name": "capital", "source": "res://reports/chapter4-environment-20261023/hubs/H44.json", "node": 13}, {"name": "sand-city", "source": "res://reports/chapter4-environment-20261023/hubs/H45.json", "node": 26}, {"name": "observatory", "source": "res://reports/chapter4-environment-20261023/hubs/H46.json", "node": 27}, {"name": "marsh-before", "source": "res://reports/chapter4-environment-20261023/hubs/H47.json", "node": 28}, {"name": "shrine-verified", "source": "res://reports/chapter4-environment-20261023/hubs/H48.json", "node": 29}, {"name": "blackbell", "source": "res://reports/chapter4-environment-20261023/hubs/H49.json", "node": 37}, {"name": "island-clinic", "source": "res://reports/chapter4-environment-20261023/hubs/H50.json", "node": 38}, {"name": "meeting-camp", "source": "res://reports/chapter4-environment-20261023/hubs/H10.json", "node": 9}, {"name": "shrine-before", "source": "res://reports/chapter4-environment-20261023/play/round1-east/round1-east-F44-entry.json", "node": 29}, {"name": "shrine-trial", "source": "res://reports/chapter4-environment-20261023/play/round1-east/round1-east-F44-victory.json", "node": 29}, {"name": "marsh-verified", "source": "res://reports/chapter4-environment-20261023/play/round2-east/round2-east-after-408.json", "node": 28}]
 for job in jobs:
  ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame;ui.instant_mode=true
  var original=FileAccess.get_file_as_string(job.source).sha256_text();ui.game.save_path=job.source
  if not ui.game.load_game():record_failure("Cannot load "+job.source)
  ui.game.save_path=PHOTO_FOLDER+"working.json"
  if not abort:ui._resume_journey();await settle()
  if not abort and ui.view=="battle":key(KEY_S);choose("new:prepare");await settle()
  if not abort and ui.view=="victory":key(KEY_Z);choose("continue_world");await settle()
  if not abort and ui.view=="hub":await leave_hub()
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
