extends SceneTree
const Renderer=preload("res://tools/map_catalog_canvas.gd")
var errors=[]
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var out=ProjectSettings.globalize_path("res://reports/m41-redesign-20261022/")
 DirAccess.make_dir_recursive_absolute(out+"images")
 var viewport=SubViewport.new();viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 var canvas=Renderer.new();viewport.add_child(canvas);await process_frame
 var ids=[401];var records=[]
 for id in ids:
  canvas.prepare(int(id));var d=canvas.game.battle_data
  viewport.size=Vector2i(int(d.map.width)*16+64,int(d.map.height)*16+64)
  canvas.size=Vector2(viewport.size)
  for i in range(3):await process_frame
  canvas.queue_redraw();await RenderingServer.frame_post_draw
  var image=viewport.get_texture().get_image();var file=out+"images/"+str(d.code)+".png"
  if image.save_png(file)!=OK:errors.append(str(d.code)+" failed screenshot")
  var info=canvas.info();records.append(info)
  print("MAP_CATALOG ",d.code," ",viewport.size)
 var f=FileAccess.open(out+"runtime-info.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"maps":records,"errors":errors,"background_guard":true,"render":"current Godot scenery, initial closed objects, no character or UI overlays","save_files_written":false},"  "));f.close()
 canvas.queue_free();await process_frame;viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
