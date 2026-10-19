extends SceneTree
var viewport
var ui
var shots=[]
var errors=[]
var out="res://reports/playtest-fixes-20261019/screenshots/"
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func shot(name:String):
 ui.queue_redraw()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 viewport.get_texture().get_image().save_png(out+name+".png")
 shots.append({"name":name,"layout_errors":ui.layout_errors.duplicate(),"preview":ui.battle_preview_audit.duplicate(),"text_checks":ui.text_checks.duplicate(true),"health_checks":ui.health_checks.duplicate(true)})
 errors.append_array(ui.layout_errors)
func fresh():
 ui.game.new_game();ui.game.save_path="/private/tmp/playtest-fixes-capture-unused.json";ui.game.world_node=2;ui.game.start_battle(101);ui.game.story_events.clear();ui._clear_menu();ui.notice_time=0;ui.phase_time=0;ui.busy=false;ui.batch_running=false;ui.ui_mode="whole_capture";ui.view="battle"
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
 viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false);fresh()
 for actor in ui.game.living("enemy"):actor.acted=true
 ui.game.cursor=Vector2i(9,10);ui._focus_battle(ui.game.cursor,true)
 await shot("01-enemy-rest-red")
 fresh();var actor=ui.game.find_unit("daan");var action=ui.game.ai_action(actor)
 if str(action.get("target","")).is_empty():push_error("No legal attack fixture");quit(1);return
 ui.game.select_unit(str(actor.id));var moved=ui.game.move_selected(action.destination)
 if not moved:push_error("Illegal fixture movement");quit(1);return
 ui.target_ids=ui.game.targets(actor).map(func(target):return str(target.id));ui.target_index=ui.target_ids.find(str(action.target));ui.game.cursor=ui.game.pos(ui.game.find_unit(str(action.target)));ui.ui_mode="target"
 for row in [[56,"02-target-top"],[120,"03-target-middle"],[184,"04-target-bottom"]]:
  ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(128,row[0])
  await shot(row[1])
 viewport.size=Vector2i(1024,960);viewport.size_2d_override=Vector2i(256,240);ui.battle_camera=Vector2(ui.game.cursor)*16-Vector2(128,120)
 await shot("05-compact-forecast")
 ui.game.find_unit(str(action.target)).max_hp=255
 await shot("06-compact-large-hp")
 viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);fresh()
 var civilian=ui.game.find_unit("M11_refugees0");var enemy=ui.game.find_unit("M11_e1")
 ui.game.units=[civilian,enemy];ui.combat={"attacker":civilian.id,"defender":enemy.id,"distance":1,"initiative_side":"player"};ui.view="combat";ui.combat_hp.clear();ui.combat_poses.clear();ui.combat_offsets.clear();ui.battle_animation.reset();ui.battle_animation.active_event={"attacker":civilian.id,"defender":enemy.id,"weapon_index":0}
 await shot("07-civilian-spear-pixels")
 var f=FileAccess.open("res://reports/playtest-fixes-20261019/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"shots":shots,"background_guard":true,"visible_windows":false,"fixture":true},"  "));f.close()
 print("PLAYTEST_CAPTURE ",shots.size()," errors ",errors)
 ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
