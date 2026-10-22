extends SceneTree
const OUT="res://reports/chapter5-redesign-20261022/ui-preview/"
const SOURCE="res://reports/chapter5-redesign-20261022/play/continuous-final/continuous-final-F52-turn-6.json"
var viewport
var ui
var checks=[]
var errors=[]
var shots=[]
func check(ok:bool,label:String):
 checks.append({"passed":ok,"label":label})
 if not ok:errors.append(label)
func _initialize():
 if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 call_deferred("run")
func key(code):
 var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
 e=InputEventKey.new();e.physical_keycode=code;ui._input(e)
func open_attack():
 ui._unit_action_menu()
 check(ui.menu_actions.has("attack"),"real unit menu offers attack")
 if not ui.menu_actions.has("attack"):return
 for i in range(ui.menu_actions.size()):
  if ui.menu_actions[ui.menu_selected]=="attack":break
  key(KEY_DOWN)
 key(KEY_Z)
 check(ui.ui_mode=="target" and not ui.target_ids.is_empty(),"physical menu keys enter ordinary target preview")
func render_case(label:String,valid:bool,save:bool=false):
 ui.queue_redraw()
 for i in range(3):await process_frame
 await RenderingServer.frame_post_draw
 var audit=ui.battle_preview_audit.duplicate(true)
 var bars=ui.health_checks.filter(func(row):return row.get("forecast",false)).duplicate(true)
 check(audit.get("valid",false) if valid else audit.is_empty(),label+" preview validity")
 check(bars.size()==(2 if valid else 0),label+" HP bar count")
 check(ui.layout_errors.is_empty(),label+" content-safe UI layout")
 if valid:
  for line in ui.text_checks.filter(func(row):return row.get("native_digits",false)):
   for bar in bars:check(not line.bounds.intersects(bar.bounds),label+" text clear of HP bars: "+str(line.text))
 if save:
  viewport.get_texture().get_image().save_png(OUT+label+".png")
  shots.append(label+".png")
 return {"case":label,"expected_valid":valid,"preview":audit,"health":bars,"layout_errors":ui.layout_errors.duplicate()}
func run():
 viewport=SubViewport.new();viewport.size=Vector2i(1704,960);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
 ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/ch5-preview-unused-records";ui.game.save_path="/private/tmp/ch5-preview-unused.json";viewport.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false)
 ui.game.save_path=SOURCE;check(ui.game.load_game(),"load genuine continuous F52 turn 6 checkpoint");ui.game.save_path="/private/tmp/ch5-preview-unused.json"
 ui.game.story_events.clear();ui._clear_menu();ui.notice_time=0;ui.phase_time=0;ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui.view="battle"
 var best={};var best_cost=999
 for actor in ui.game.living("player"):
  if not actor.get("controllable",true) or actor.get("acted",false):continue
  var graph=ui.game.reachable(actor)
  for cell in graph.costs:
   if not ui.game.can_stop(actor,cell):continue
   var candidate=actor.duplicate(true);candidate.position=[cell.x,cell.y];candidate.erase("weapon_index")
   if not ui.game.targets(candidate).is_empty() and int(graph.costs[cell])<best_cost:
    best={"id":actor.id,"from":actor.position.duplicate(),"to":cell};best_cost=int(graph.costs[cell])
 check(not best.is_empty(),"real current stats and reachable cells offer normal attack")
 if best.is_empty():quit(1);return
 check(ui.game.select_unit(best.id),"select genuine active unit")
 check(ui.game.move_selected(best.to),"move legally through actual reachable API")
 open_attack();ui._focus_battle(ui.game.cursor,true)
 var cases=[];cases.append(await render_case("normal-menu-preview",true,true))
 var selected=ui.game.selected_id;var ids=ui.target_ids.duplicate();var index=ui.target_index
 for invalid in [{"case":"empty-selected","selected":"","ids":ids,"index":index},{"case":"removed-actor","selected":"__removed_actor__","ids":ids,"index":index},{"case":"removed-target","selected":selected,"ids":["__removed_target__"],"index":0},{"case":"index-past-end","selected":selected,"ids":ids,"index":ids.size()},{"case":"index-negative","selected":selected,"ids":ids,"index":-1},{"case":"empty-target-list","selected":selected,"ids":[],"index":0}]:
  ui.game.selected_id=invalid.selected;ui.target_ids=invalid.ids.duplicate();ui.target_index=invalid.index
  cases.append(await render_case(invalid.case,false,invalid.case=="empty-selected"))
 ui.game.selected_id=selected;open_attack();cases.append(await render_case("restored-menu-preview",true,true))
 var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"assertions":checks,"cases":cases,"shots":shots,"source":SOURCE,"actual_menu_key_input":true,"legal_move":best,"movement_cost":best_cost,"source_stats_changed":false,"combat_resolution_changed":false,"background_guard":true,"user_saves_touched":false}
 var f=FileAccess.open(OUT+"preview-guard-regression.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("PREVIEW_GUARD_REGRESSION ",JSON.stringify({"passed":report.passed,"checks":checks.size(),"errors":errors,"legal_move":best}))
 ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
