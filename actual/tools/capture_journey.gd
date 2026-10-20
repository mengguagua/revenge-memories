extends SceneTree
var runtime := OS.get_cmdline_user_args().has("--runtime")
var viewport
var ui
var shots=[]
var errors=[]
var designs="res://../art-review/character-expansion-20261018/journey-home-20261019/designs/"
var out="res://reports/journey-home-20261019/screenshots/"
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func mock_records() -> Array:
 var result=[]
 var places=["海峡城庆典","雪原村","海灯岛灯屋","西街脱围","营站会谈"]
 for i in range(5):result.append({"slot":i+1,"exists":true,"valid":true,"legacy":false,"chapter":"序章" if i==0 else "第一章" if i<2 else "第二章" if i<3 else "第三章","location":places[i],"time":"2026-10-19 22:%02d"%(10+i*7),"seconds":i*3671.0,"route":"西队" if i<2 else "东队","path":"fixture"})
 return result
func shot(name: String,design: bool=true):
 ui.queue_redraw()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 var img=viewport.get_texture().get_image();img.save_png(out+name+".png")
 if design and not runtime:img.save_png(designs+name+".png")
 shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate(),"audit":ui.journey.audit.duplicate(true),"size":[viewport.size.x,viewport.size.y]})
 errors.append_array(ui.layout_errors)
func run():
 for path in [out,designs]:DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path))
 viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);ui.elapsed=2.0;ui.game.slot_directory="res://.cache/journey-capture-unused"
 ui.journey.records=mock_records();ui.title_selected=0
 await shot("01-home")
 ui.view="journal";ui.journey.intent="new";ui.journey.selected=0
 for entry in ui.journey.records:entry.exists=false;entry.valid=false
 await shot("02-new-empty")
 ui.journey.records=mock_records();ui.journey.intent="load";ui.journey.selected=3
 await shot("03-continue")
 ui.journey.intent="save";ui.journey.selected=2;ui.journey.records[4].exists=false;ui.journey.records[4].valid=false
 await shot("04-save")
 ui.view="journal_confirm";ui.journey.confirm_choice=0
 await shot("05-overwrite")
 ui.view="journal";ui.journey.intent="load";ui.journey.records[2].valid=false;ui.journey.message="记录无法读取，原件已保留"
 await shot("06-corrupt-record")
 viewport.size=Vector2i(1024,960);viewport.size_2d_override=Vector2i(256,240);ui.view="title";ui.journey.message="";ui.journey.records=mock_records();ui.title_selected=1
 await shot("07-home-compact")
 ui.view="journal";ui.journey.intent="load"
 await shot("08-continue-compact")
 ui.view="journal_confirm"
 await shot("09-overwrite-compact")
 viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240)
 ui.game.new_game();ui.game.save_path="/private/tmp/journey-toast-capture.json";ui.game.active_slot=3;ui.view="world";ui.world_actor=Vector2(ui.world.nodes["1"].position[0],ui.world.nodes["1"].position[1])*16;ui.journey.saved_left=3;ui.journey.saved_time="2026-10-19 22:24"
 await shot("10-saved-feedback")
 # Capture a fresh rendered pass against the frozen design images.
 var report={"passed":errors.is_empty(),"errors":errors,"shots":shots,"background_guard":true,"visible_windows":false,"fixtures":true,"user_saves_touched":false}
 var f=FileAccess.open("res://reports/journey-home-20261019/"+("round2-visual.json" if runtime else "round1-visual.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 if runtime:await animation()
 print("JOURNEY_DESIGNS ",shots.size()," errors ",errors)
 ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

func animation():
 var frames="res://.cache/journey-animation/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(frames))
 viewport.size=Vector2i(852,480);viewport.size_2d_override=Vector2i(426,240)
 ui.journey.records=mock_records();ui.journey.message="";ui.journey.saved_left=0
 var previous=-1
 for i in range(144):
  var scene=i/24;ui.elapsed=10.0+i/12.0
  if scene!=previous:ui.journey.opened_at=ui.elapsed;previous=scene
  if scene==0 or scene==5:
   ui.view="title";ui.title_selected=0 if i%24<12 else 1
  elif scene==1:
   ui.view="journal";ui.journey.intent="load";ui.journey.selected=mini(4,(i%24)/5)
  elif scene==2:
   ui.view="journal";ui.journey.intent="new";ui.journey.selected=4
   ui.journey.records[4].exists=false;ui.journey.records[4].valid=false
  elif scene==3:
   ui.view="journal_confirm";ui.journey.intent="save";ui.journey.selected=2;ui.journey.confirm_choice=0 if i%24<12 else 1
  elif scene==4:
   ui.view="world";ui.journey.saved_left=3;ui.journey.saved_time="2026-10-19 22:24"
  ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
  viewport.get_texture().get_image().save_png(frames+"frame-%04d.png"%i)
