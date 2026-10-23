extends SceneTree
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func run():
 var out="res://reports/chapter2-environment-20261023/ships/images/"
 var vp=SubViewport.new();vp.size=Vector2i(562,320);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
 var ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame
 var source="res://reports/chapter2-environment-20261023/play/round1-ships-hold/round1-ships-hold-F22-object-prison_door.json"
 var source_hash=FileAccess.get_file_as_string(source).sha256_text();ui.game.save_path=source
 if not ui.game.load_game():quit(1);return
 ui.game.save_path=out+"working-photo.json";ui.view=ui.game.mode;ui.instant_mode=true;ui._clear_menu();ui._focus_battle(Vector2i(26,9),true)
 ui.queue_redraw();for i in range(4):await process_frame
 await RenderingServer.frame_post_draw
 vp.get_texture().get_image().save_png(out+"F22-gates-open.png")
 var f=FileAccess.open(out+"gate-open-capture.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":ui.layout_errors.is_empty()and FileAccess.get_file_as_string(source).sha256_text()==source_hash,"source":source,"source_sha256":source_hash,"background_guard":true,"turn":ui.game.turn,"quest":ui.game.flags.quest,"layout_errors":ui.layout_errors,"camera_only":true},"  "));f.close()
 ui.queue_free();await process_frame;vp.queue_free();await process_frame;quit()
