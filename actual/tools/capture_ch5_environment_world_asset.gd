extends SceneTree
const Renderer=preload("res://tools/ch5_environment_world_canvas.gd")
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var folder="res://assets/chapter5-environment-20261023/world/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
 var vp=SubViewport.new();vp.size=Vector2i(896,1024);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var canvas=Renderer.new();vp.add_child(canvas);await process_frame
 canvas.size=Vector2(vp.size)
 for frame in range(4):await process_frame
 canvas.queue_redraw();await RenderingServer.frame_post_draw
 vp.get_texture().get_image().save_png(folder+"overview-"+OS.get_environment("CH5_WORLD_PHASE")+".png")
 canvas.queue_free();await process_frame;vp.queue_free();await process_frame;quit()
