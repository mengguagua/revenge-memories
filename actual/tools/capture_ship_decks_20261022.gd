extends SceneTree
const Renderer=preload("res://tools/map_catalog_canvas.gd")
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var out=ProjectSettings.globalize_path("res://reports/map-polish-20261022/ship-decks/")
 var viewport=SubViewport.new();viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 var canvas=Renderer.new();viewport.add_child(canvas);await process_frame
 for id in [201,202,211]:
  canvas.prepare(id);var d=canvas.game.battle_data
  viewport.size=Vector2i(int(d.map.width)*16+64,int(d.map.height)*16+64);canvas.size=Vector2(viewport.size)
  for i in range(3):await process_frame
  canvas.queue_redraw();await RenderingServer.frame_post_draw
  viewport.get_texture().get_image().save_png(out+str(d.code)+".png")
 canvas.queue_free();await process_frame;viewport.queue_free();await process_frame;quit()
