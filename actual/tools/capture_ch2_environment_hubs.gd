extends "res://tests/ch2_redesign_play.gd"
const HUB_PHOTOS="res://reports/chapter2-environment-20261023/hubs/"
var hub_vp:SubViewport
var hub_photos=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var phase=OS.get_environment("CH2_HUB_PHOTO_PHASE")
 if phase.is_empty():phase="after"
 var folder=HUB_PHOTOS+phase+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
 hub_vp=SubViewport.new();hub_vp.size=Vector2i(562,320);hub_vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(hub_vp)
 for room in ["H21","H22","H23","H24","H25","H26","H27"]:
  var source=HUB_PHOTOS+room+".json";var source_hash=FileAccess.get_file_as_string(source).sha256_text()
  ui=load("res://scenes/main.tscn").instantiate();hub_vp.add_child(ui);await process_frame;ui.instant_mode=true
  ui.game.save_path=source
  if not ui.game.load_game():record_failure("Photo source missing: "+room)
  ui.game.save_path=folder+"capture-working.json"
  if not abort:ui._resume_journey();await settle()
  ui.queue_redraw();for i in range(4):await process_frame
  await RenderingServer.frame_post_draw
  var path=folder+room+".png";hub_vp.get_texture().get_image().save_png(path)
  hub_photos.append({"room":room,"path":path,"source":source,"source_sha256":source_hash,"layout_errors":ui.layout_errors.duplicate(),"size":[562,320],"chapter":ui.game.chapter,"chapter1_complete":ui.game.flags.get("chapter1_complete",false)})
  print("CLIMATE_HUB_PHOTO ",phase," ",room," ",ui.layout_errors)
  ui.queue_free();await process_frame;ui=null
 var f=FileAccess.open(folder+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"background_guard":true,"shots":hub_photos,"failures":failures,"note":"Native engine viewport from genuine input-reached hub saves; no live character/camera/flags edits."},"  "));f.close()
 hub_vp.queue_free();await process_frame;quit(1 if abort else 0)
