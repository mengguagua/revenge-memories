extends "res://tests/map_polish_play.gd"
## Resume genuine victories in isolated files, then use the ordinary result
## and travel menus. A new UI per map prevents pending result coroutines from
## crossing over into the next checkpoint. No game flags or wins are assigned.
const RETURN_REPORT="res://reports/map-polish-20261022/return-flow.json"
const RETURN_WORK="/private/tmp/revenge-map-polish-return-flow-20261022/"
const RETURN_ORDER=["M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","F26","S21","S22"]
const RETURN_SOURCES={
 "M12":"polish-west-a2","M13":"polish-west-a2","M14":"polish-west-camp-fort","M15":"polish-tower-formation",
 "S11":"polish-mine-formation","S12":"polish-west-side","F21":"polish-ships","F22":"polish-f22-continued",
 "F23":"polish-islands","F24":"polish-islands","F25":"polish-harbor","F26":"polish-harbor",
 "S21":"polish-ships","S22":"polish-seacave"}
var return_records={}
var return_requested:PackedStringArray=[]
var return_current={}
var return_source_overrides={}

func _initialize() -> void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--codes="):return_requested=arg.split("=")[1].split(",")
  if arg.begins_with("--source="):
   var pair=arg.trim_prefix("--source=").split(":")
   if pair.size()==2:return_source_overrides[str(pair[0])]=str(pair[1])
 call_deferred("run_return_flow")

func expect(ok:bool,message:String) -> void:
 return_current.checks.append({"passed":ok,"check":message})
 if not ok:record_failure(message)

func settled_ui_release() -> void:
 await settle()
 if not abort:
  # Consecutive released frames include the _resume_journey and _show_result
  # continuation boundaries, before the result menu accepts normal input.
  for i in range(4):
   await process_frame
   if ui.result_sequence_running or ui.busy or ui.batch_running:
    await settle()

func write_return_report() -> void:
 var records=[];var pending=[];var keys=0;var check_count=0
 for code in RETURN_ORDER:
  if return_records.has(code):
   records.append(return_records[code]);keys+=int(return_records[code].key_inputs);check_count+=return_records[code].checks.size()
  else:pending.append(code)
 var passed=not records.is_empty()and records.all(func(r):return bool(r.passed))
 var record={"passed":passed,"complete":passed and pending.is_empty(),"maps":records.size(),"checks":check_count,"key_inputs":keys,"pending":pending,"results":records,
  "scope":"Genuine current-run victory checkpoints resumed into isolated /private/tmp copies; ordinary result Continue and one legal world-road round trip per map. This verifies post-battle continuation, not a new battle playthrough.",
  "source_saves_modified":false,"user_saves_written":false,"state_flags_overridden":false,"forced_victories":false,"result_coroutines_isolated":true}
 var f=FileAccess.open(RETURN_REPORT,FileAccess.WRITE);f.store_string(JSON.stringify(record,"  "));f.close()

func run_return_flow() -> void:
 DirAccess.make_dir_recursive_absolute(RETURN_WORK)
 if FileAccess.file_exists(RETURN_REPORT):
  var prior=State.read_json(RETURN_REPORT)
  for record in prior.get("results",[]):return_records[str(record.code)]=record
 for code in RETURN_ORDER:
  if not return_requested.is_empty()and not code in return_requested:continue
  var label=str(return_source_overrides.get(code,RETURN_SOURCES[code]));var folder="res://reports/map-polish-20261022/play/"+label+"/"
  var source=folder+label+"-"+str(code)+"-victory.json"
  if not FileAccess.file_exists(source):continue
  var source_raw=FileAccess.get_file_as_string(source);var source_hash=source_raw.sha256_text();var state=State.read_json(source)
  var run_record=State.read_json(folder+label+"-play.json")
  var real_battles=run_record.get("battles",[]).filter(func(b):return str(b.code)==code)
  abort=false;var before_failures=failures.size();var before_inputs=inputs
  return_current={"code":code,"source":source,"source_sha256":source_hash,"checks":[],"key_inputs":0,"passed":false}
  # Loading is performed on a byte-for-byte temporary copy. Source evidence is
  # never selected as the active save path, even during error handling.
  var working=RETURN_WORK+str(code)+".json"
  var copied=DirAccess.copy_absolute(ProjectSettings.globalize_path(source),working)==OK
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  expect(copied,"Victory checkpoint copied into an isolated work path")
  expect(not real_battles.is_empty()and str(real_battles[0].outcome)=="victory"and real_battles[0].failures.is_empty(),"Source battle has a genuine clean victory record")
  expect(str(state.get("battle_outcome",""))=="victory"and str(state.get("mode",""))=="victory","Source checkpoint is an actual victory/result state")
  if not abort:
   expect(ui.game.load_game(),"Victory checkpoint loads through normal game validation")
  if not abort:
   var stage=int(ui.game.stage_id);var side=str(ui.game.route);var node=int(ui.game.world_node)
   var roster_before=JSON.stringify(ui.game.roster).sha256_text();var convoy_before=JSON.stringify(ui.game.convoy).sha256_text()
   return_current.stage_id=stage;return_current.route=side;return_current.world_node=node
   # This is the same resume routine invoked by the save-load interface.
   ui._resume_journey()
   await settled_ui_release()
   if not abort:
    expect(ui.view=="victory"and not ui.result_sequence_running,"Result dialogue/reward sequence releases input ownership")
    expect(ui.game.battle_settled and ui.game.stage_cleared(stage),"Battle is settled and appears in the cleared-stage list")
    expect(bool(ui.game.flags.get("clear_"+str(code),false)),"This map's clear flag is retained")
   if not abort:
    key(KEY_Z)
    expect(ui.menu_context=="result"and ui.menu_actions.has("continue_world"),"Normal result menu exposes Continue")
   if not abort:
    choose("continue_world");await settled_ui_release()
    expect(ui.view=="world"and ui.game.mode=="world","Continue returns to the playable world map")
    expect(not ui.busy and not ui.batch_running and not ui.result_sequence_running,"World input has no pending result/battle owner")
    expect(ui.game.stage_cleared(stage)and bool(ui.game.flags.get("clear_"+str(code),false)),"Clear records survive the result-to-world transition")
    expect(str(ui.game.route)==side,"Correct army route is preserved")
    expect(JSON.stringify(ui.game.roster).sha256_text()==roster_before and JSON.stringify(ui.game.convoy).sha256_text()==convoy_before,"Resuming the settled result does not repeat growth or equipment rewards")
   if not abort:
    var neighbors: Array=ui.game.world_neighbors();return_current.available_neighbors=neighbors.duplicate()
    expect(not neighbors.is_empty(),"At least one world road remains available")
    if not abort:
     var destination=int(neighbors[0])
     if neighbors.has(int(ui.game.previous_world_node)):destination=int(ui.game.previous_world_node)
     var route=ui.game.route_between(node,destination)
     expect(not route.is_empty()and route.get("cells",[]).size()>1,"Available road has a complete visible route")
     if not abort:
      await travel(destination)
      expect(ui.view=="world"and int(ui.game.world_node)==destination,"Normal world menu input travels along the road")
      if not abort:
       expect(ui.game.world_neighbors().has(node),"The return road remains available")
       if not abort:
        await travel(node)
        expect(ui.view=="world"and int(ui.game.world_node)==node,"Normal menu input returns to the cleared battle node")
        key(KEY_Z)
        expect(not ui.menu_items.is_empty(),"World menu accepts input after the round trip")
        if not abort:key(KEY_X)
      return_current.road_sample={"from":node,"to":destination,"back_to":ui.game.world_node}
   return_current.final_view=ui.view;return_current.final_mode=ui.game.mode;return_current.final_node=ui.game.world_node
  expect(FileAccess.get_file_as_string(source).sha256_text()==source_hash,"Original victory evidence is unchanged")
  return_current.key_inputs=inputs-before_inputs;return_current.failures=failures.slice(before_failures)
  return_current.passed=return_current.failures.is_empty()and return_current.checks.all(func(c):return bool(c.passed))
  return_records[code]=return_current.duplicate(true);write_return_report()
  print("MAP_RETURN ",code," ",return_current.passed," inputs ",return_current.key_inputs," ",return_current.get("final_view","not_loaded"))
  # All successful UI work has settled. On failure, destroy this isolated UI
  # entirely rather than clearing a live asynchronous result flag by hand.
  ui.queue_free();await process_frame;await process_frame;ui=null
 write_return_report()
 quit(0 if failures.is_empty()else 1)
