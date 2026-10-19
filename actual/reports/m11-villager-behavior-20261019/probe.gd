extends SceneTree
var ui
var report={"cases":[]}
var waiting=false
func _initialize():call_deferred("run")
func snapshot()->Array:
 var rows=[]
 for u in ui.game.units:
  rows.append({"id":u.id,"position":u.position.duplicate(),"hp":u.hp,"acted":u.acted,"side":u.side})
 return rows
func start():
 ui.game.new_game();ui.game.world_node=int(ui.game.stages[101].node);ui.game.start_battle(101)
 ui.game.story_events.clear();ui.view="battle";ui.busy=false;ui.batch_running=false;ui.ui_mode="inspect";ui._clear_menu()
func observe():
 while is_instance_valid(ui):
  if ui.view=="plot":ui._accept()
  if waiting and Time.get_ticks_msec()>60000:push_error("probe exceeded time");quit(2);return
  await process_frame
func run():
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
 ui.set_process(false);ui.set_physics_process(false)
 report.existing_save={"path":ProjectSettings.globalize_path(ui.game.save_path)}
 if FileAccess.file_exists(ui.game.save_path):
  var save=JSON.parse_string(FileAccess.get_file_as_string(ui.game.save_path))
  if save is Dictionary:
   for key in ["stage_id","turn","phase","mode","battle_outcome"]:report.existing_save[key]=save.get(key)
   report.existing_save.escorts=[]
   for u in save.get("units",[]):
    if str(u.get("id","")).begins_with("M11_refugees"):report.existing_save.escorts.append(u)
 ui.game.save_path="/private/tmp/m11-behavior-probe-unused.json";ui.instant_mode=true
 observe()
 report.version=ProjectSettings.get_setting("application/config/version")
 report.code={}
 for path in ["core/game_state.gd","core/legacy_main.gd","core/tactical_ai.gd","data/stages/M11.json"]:
  report.code[path]=FileAccess.get_sha256("res://"+path)
 for scenario in ["initial","clear_route","adjacent_enemy"]:
  start()
  if scenario=="clear_route":
   for e in ui.game.living("enemy"):
    if not e.get("objective_boss",false):e.hp=0
  if scenario=="adjacent_enemy":
   var e=ui.game.living("enemy")[0];e.position=[8,11]
  var row={"scenario":scenario,"before":snapshot(),"actions":[]}
  for id in ["M11_refugees0","M11_refugees1"]:
   var u=ui.game.find_unit(id)
   var a=ui.game.ai_action(u)
   row.actions.append({"id":id,"destination":str(a.destination),"target":a.target,"path":str(ui.game.path_to(u,a.destination))})
  ui.batch_running=true;ui.busy=true
  for id in ["M11_refugees0","M11_refugees1"]:await ui._run_ai_unit(ui.game.find_unit(id))
  row.after=snapshot();row.busy=ui.busy;row.moving_id=ui.moving_id
  report.cases.append(row)
 # Real timers and sprite controller, without instant-mode bypass.
 start()
 for e in ui.game.living("enemy"):
  if not e.get("objective_boss",false):e.hp=0
 ui.instant_mode=false;ui.batch_running=true;ui.busy=true;ui.set_process(true)
 var timed_before=snapshot();var timed_start=Time.get_ticks_msec()
 for id in ["M11_refugees0","M11_refugees1"]:await ui._run_ai_unit(ui.game.find_unit(id))
 report.normal_speed_movement={"before":timed_before,"after":snapshot(),"elapsed_ms":Time.get_ticks_msec()-timed_start,"moving_id":ui.moving_id}
 ui.instant_mode=true;ui.set_process(false)
 # Full real end-turn controller, from genuine initial stage.
 start();var before=snapshot()
 waiting=true
 await ui._enemy_phase()
 waiting=false
 report.full_phase={"before":before,"after":snapshot(),"turn":ui.game.turn,"phase":ui.game.phase,"busy":ui.busy,"batch_running":ui.batch_running,"view":ui.view}
 var path=OS.get_environment("M11_PROBE_REPORT")
 var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("M11_PROBE ",JSON.stringify(report))
 ui.queue_free();await process_frame;quit()
