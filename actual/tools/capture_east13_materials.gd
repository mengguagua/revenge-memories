extends SceneTree
const Renderer=preload("res://tools/map_catalog_canvas.gd")
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var out="res://reports/chapter5-spatial-20261022/material-audit/east13-images/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
 var vp=SubViewport.new();vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var canvas=Renderer.new();vp.add_child(canvas);await process_frame;var metadata=[]
 for id in [205,304,306,311,312]:
  canvas.prepare(id);var d=canvas.game.battle_data;vp.size=Vector2i(d.map.width*16+64,d.map.height*16+64);canvas.size=Vector2(vp.size)
  for i in range(4):await process_frame
  canvas.queue_redraw();await RenderingServer.frame_post_draw
  vp.get_texture().get_image().save_png(out+str(d.code)+".png");metadata.append(canvas.info())
 var f=FileAccess.open(out+"runtime-info.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":true,"maps":metadata},"  "));f.close()
 canvas.queue_free();await process_frame;vp.queue_free();await process_frame;quit()
