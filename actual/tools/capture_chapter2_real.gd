extends "res://tests/chapter2_play.gd"
## Final delivery captures from actual play checkpoints and legal input.
var actual_shots: Array=[]
var duel_seen=false
func _initialize() -> void:
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func load_real(name: String) -> void:
 ui.game.save_path=OUT+"natural-"+name+"-save.json"
 if not ui.game.load_game():record_failure("Actual capture checkpoint unavailable: "+name);return
 ui.game.save_path="res://reports/chapter2/screenshots/working-save.json"
 ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu();ui.phase_time=0;ui.notice_time=0;ui.held_direction=Vector2i.ZERO
 ui.world_actor=Vector2(ui.world.nodes[str(ui.game.world_node)].position[0],ui.world.nodes[str(ui.game.world_node)].position[1])*16
 if ui.view=="hub":ui.hub_controller.resume()
 if ui.view in ["battle","victory","defeat"]:ui._focus_battle(ui.game.cursor,true)
 if ui.game.flags.has("active_plot"):ui._resume_plot()
func shot(name: String,source: String) -> void:
 if abort:return
 ui.queue_redraw()
 for i in range(4):await process_frame
 await RenderingServer.frame_post_draw
 var path="res://reports/chapter2/screenshots/"+name+".png"
 viewport.get_texture().get_image().save_png(path)
 actual_shots.append({"path":path,"source":source,"fixture":false,"view":ui.view,"chapter":ui.game.chapter,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"canvas":[viewport.size.x,viewport.size.y],"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true)})
 print("CHAPTER2_REAL_SHOT ",name," ",ui.layout_errors)
func watch_exchange() -> void:
 if ui!=null and ui.view=="combat" and not duel_seen:duel_seen=true;capture_exchange()
func capture_exchange() -> void:
 await shot("11-near-combat","Live legal exchange from actual F21 entry, actual keyboard movement and attack")
 ui.instant_mode=true
func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/chapter2/screenshots"))
 viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
 load_real("east-start");await shot("01-windlamp-harbor","Actual continuation from chapter-one complete save into H21")
 walk_to(Vector2i(8,6));key(KEY_UP);key(KEY_Z);await process_frame;key(KEY_Z)
 await shot("02-departure-dialogue","Actual facing interaction with Carlo, D21 opening portrait and dialogue")
 await settle()
 load_real("F21-field");cursor_to(Vector2i(14,11));await shot("03-naval-boarding","Actual F21 turn-four checkpoint, camera moved through cursor input")
 load_real("F22-object-reserve_bridge");cursor_to(Vector2i(18,13));await shot("04-prison-bridge","Actual rescued-ship checkpoint after lowering the reserve bridge through action menu")
 load_real("after-203");await shot("05-reef-village","Actual post-F23 village, recruitment and holy sword confirmation completed")
 load_real("S22-field");cursor_to(Vector2i(10,10));await shot("06-sea-cave","Actual S22 battle checkpoint, full rock silhouettes and tidal cave")
 load_real("F24-field");cursor_to(Vector2i(14,8));await shot("07-black-day-lighthouse","Actual F24 defense checkpoint and legal cursor view at the beacon")
 load_real("F25-field");cursor_to(Vector2i(18,13));await shot("08-military-harbor","Actual F25 combat checkpoint, warehouse/pier materials and objective area")
 viewport.size=Vector2i(562,260);await process_frame
 load_real("F26-boats-moving")
 var boats=ui.game.event_boats()
 for boat in boats:
  if not boat.arrived and boat.hp>0 and not boat.waiting:cursor_to(Vector2i(boat.position[0],boat.position[1]));break
 await shot("09-ancient-passage","Actual F26 boat progress checkpoint, wide landscape with real escort event position")
 viewport.size=Vector2i(426,266);await process_frame
 load_real("chapter-end");await shot("10-chapter-complete","Actual chapter-two arrival and detention completed, both party records saved")
 viewport.size=Vector2i(426,240);await process_frame
 load_real("F21-deployment");ui.instant_mode=false;process_frame.connect(watch_exchange)
 for pass_ in range(5):
  if duel_seen or abort:break
  var turn_=ui.game.turn
  for id in ui.game.party.duplicate():
   if duel_seen or abort or ui.game.turn!=turn_:break
   await act(str(id))
  if not duel_seen and not abort and ui.game.turn==turn_:key(KEY_S);choose("end_turn");await settle()
 process_frame.disconnect(watch_exchange)
 await settle()
 for i in range(6):await process_frame
 var bad=[]
 for item in actual_shots:bad.append_array(item.layout_errors)
 var report={"passed":not abort and bad.is_empty() and duel_seen,"shots":actual_shots,"failures":failures,"layout_errors":bad,"duel_captured":duel_seen,"background_guard":true,"visible_windows":false,"scope":"Actual Godot viewport captures from recorded keyboard-play checkpoints; no fixture victories or fabricated map screenshots"}
 var f=FileAccess.open("res://reports/chapter2/screenshots/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null;quit(0 if report.passed else 1)
