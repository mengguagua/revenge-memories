extends "res://tests/ch4_environment_play.gd"
const FLOW_PHOTOS="res://reports/chapter4-environment-20261023/flow/"
var flow_viewport:SubViewport
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FLOW_PHOTOS))
 flow_viewport=SubViewport.new();flow_viewport.size=Vector2i(562,320);flow_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(flow_viewport)
 var shots=[];var errors=[]
 for name in ["chapter-end","chapter5-start"]:
  var source="res://reports/chapter4-environment-20261023/play/chapter-transition/chapter-transition-"+name+".json"
  var source_hash=FileAccess.get_file_as_string(source).sha256_text()
  ui=load("res://scenes/main.tscn").instantiate();flow_viewport.add_child(ui);await process_frame;ui.instant_mode=true
  ui.game.save_path=source
  if not ui.game.load_game():record_failure("Cannot load final continuation checkpoint: "+name);break
  ui.game.save_path=FLOW_PHOTOS+"capture-working.json"
  ui._resume_journey();await settle()
  ui.queue_redraw()
  for i in range(6):await process_frame
  await RenderingServer.frame_post_draw
  var path=FLOW_PHOTOS+name+".png";flow_viewport.get_texture().get_image().save_png(path)
  errors.append_array(ui.layout_errors)
  shots.append({"name":name,"path":path,"source":source,"source_sha256":source_hash,"chapter":ui.game.chapter,"mode":ui.game.mode,"view":ui.view,"hub_record":ui.game.hub_record,"chapter4_complete":ui.game.flags.get("chapter4_complete",false),"layout_errors":ui.layout_errors.duplicate(),"size":[562,320],"source_unchanged":FileAccess.get_file_as_string(source).sha256_text()==source_hash})
  if FileAccess.get_file_as_string(source).sha256_text()!=source_hash:record_failure("Final source modified")
  print("CH2_FLOW_NATIVE ",name," chapter ",ui.game.chapter," mode ",ui.game.mode," errors ",ui.layout_errors)
  ui.queue_free();await process_frame;ui=null
  for i in range(3):await process_frame
 var f=FileAccess.open(FLOW_PHOTOS+"captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort and errors.is_empty()and shots.size()==2,"shots":shots,"layout_errors":errors,"failures":failures,"inputs":inputs,"background_guard":true,"scope":"Genuine final chapter-end and chapter5-start checkpoints, normal resume and dialogue settle. No flags, coordinates, stats or source saves edited."},"  "));f.close()
 flow_viewport.queue_free();await process_frame;quit(1 if abort or not errors.is_empty()else 0)
