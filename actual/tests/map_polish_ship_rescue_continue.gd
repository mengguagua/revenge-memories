extends "res://tests/map_polish_ship_rescue.gd"
## Continue an actual unfinished attempt, preserving every combat outcome.
const RESCUE_SOURCE="res://reports/map-polish-20261022/play/polish-f22-formation/polish-f22-formation-F22-stopped.json"
const FIRST_REPORT="res://reports/map-polish-20261022/play/polish-f22-formation/polish-f22-formation-play.json"
func _initialize() -> void:
 review_label="polish-f22-continued";review_round=3
 review_out="res://reports/map-polish-20261022/play/"+review_label+"/"
 call_deferred("run")
func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path=RESCUE_SOURCE
 var loaded=ui.game.load_game();ui.game.save_path=review_out+"working-save.json"
 if not loaded:record_failure("Actual unfinished F22 checkpoint failed to load");quit(1);return
 ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.held_direction=Vector2i.ZERO;ui.phase_time=0;ui._focus_battle(ui.game.cursor,true)
 if not ui.game.battle_outcome.is_empty() or ui.game.stage_id!=202:record_failure("Source is not a continuing F22 battle");quit(1);return
 var record={"code":"F22","source":RESCUE_SOURCE,"initial_roster":ui.game.roster.duplicate(true),"turns":[],"tactical_actions":[],"scope":"Continuation of actual F22 formation attempt at turn66; normal load and input preserve its stats, positions, losses, and RNG. No reset or forced outcome."}
 await snapshot("F22-entry")
 key(KEY_S);choose("new:goal");await settle()
 for pass_ in range(65):
  if abort or not ui.game.battle_outcome.is_empty():break
  var turn_=ui.game.turn;var members=ui.game.party.duplicate()
  members.sort_custom(func(a,b):return rank(ui.game.roster[a])<rank(ui.game.roster[b]))
  for id in members:
   if abort or ui.game.turn!=turn_ or not ui.game.battle_outcome.is_empty():break
   var unit=ui.game.find_unit(str(id))
   if unit.is_empty() or int(unit.hp)<=0 or unit.acted:continue
   var start=State.pos(unit);var before_ops=operations.size();await act(str(id));var at=State.pos(unit)
   record.tactical_actions.append({"turn":turn_,"unit":id,"from":[start.x,start.y],"to":[at.x,at.y],"terrain":ui.game.category(at),"avoid":ui.game.terrain_avoid(at),"operations":operations.slice(before_ops)})
  if not abort and ui.game.battle_outcome.is_empty() and ui.game.turn==turn_:
   key(KEY_S);choose("end_turn");await settle()
  var players=[]
  for u in ui.game.living("player"):
   if u.get("controllable",true):players.append({"id":u.id,"hp":u.hp,"position":u.position.duplicate()})
  record.turns.append({"turn":ui.game.turn,"enemies":ui.game.living("enemy").size(),"outcome":ui.game.battle_outcome,"players":players,"quest":ui.game.flags.quest.duplicate(true)})
  print("F22_CONTINUED turn ",ui.game.turn," E ",ui.game.living("enemy").size()," P ",players," ",ui.game.battle_outcome)
  if pass_==2:await snapshot("F22-field")
  if pass_==7:await snapshot("F22-recovery")
 record.outcome=ui.game.battle_outcome;record.final_turn=ui.game.turn;record.key_inputs=inputs;record.failures=failures.duplicate();record.final_roster=ui.game.roster.duplicate(true);record.quest=ui.game.flags.quest.duplicate(true)
 await snapshot("F22-"+("victory" if record.outcome=="victory" else"stopped"))
 review_battles.append(record);write_review()
 if record.outcome=="victory":
  key(KEY_Z);choose("continue_world");await settle();await snapshot("F22-returned-world")
  var f=FileAccess.open(review_out+"continuation-chain.json",FileAccess.WRITE)
  f.store_string(JSON.stringify({"passed":not abort and ui.game.mode=="world" and ui.game.cleared_stages.has(202),"source":RESCUE_SOURCE,"source_sha256":FileAccess.get_file_as_string(RESCUE_SOURCE).sha256_text(),"first_segment":FIRST_REPORT,"continued_from_turn":66,"final_turn":record.final_turn,"world_node":ui.game.world_node,"cleared_stages":ui.game.cleared_stages,"objects":record.quest.objects,"evacuated":record.quest.evacuated,"key_inputs_in_continuation":inputs,"total_inputs":int(State.read_json(FIRST_REPORT).inputs)+inputs,"attributes_positions_rng_edited":false},"  "));f.close()
 write_review()
 ui.queue_free();await process_frame;ui=null;quit(0 if record.outcome=="victory" and not abort else 1)

func write_review() -> void:
 super.write_review()
 var file=review_out+review_label+"-play.json";var report=State.read_json(file)
 report.source_checkpoint=RESCUE_SOURCE;report.preceding_report=FIRST_REPORT
 report.total_inputs=int(State.read_json(FIRST_REPORT).inputs)+inputs
 report.continued_from_turn=66
 var f=FileAccess.open(file,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
