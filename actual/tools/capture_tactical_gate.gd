extends "res://tools/capture_tactical_review.gd"
func run() -> void:
 capture_viewport=SubViewport.new();capture_viewport.size=Vector2i(426,240);capture_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(capture_viewport)
 ui=load("res://scenes/main.tscn").instantiate();capture_viewport.add_child(ui);await process_frame;ui.instant_mode=true
 var source="res://reports/review-0.2.1/round2-tower-M15-field.json";load_checkpoint(source)
 var observed=false
 for step in range(5):
  if abort or not ui.game.battle_outcome.is_empty():break
  var turn_=ui.game.turn
  for id in ui.game.party.duplicate():
   if abort or ui.game.turn!=turn_ or not ui.game.battle_outcome.is_empty():break
   await act(str(id))
   var rider=ui.game.find_unit("lance")
   if int(rider.hp)>0 and State.pos(rider)==Vector2i(28,3):observed=true;break
  if observed:break
  key(KEY_S);choose("end_turn");await settle()
 if observed:
  var checkpoint="res://reports/review-0.2.1/round2-north-gate-observed.json"
  ui.game.save_path=checkpoint;ui.game.save_game();ui.game.save_path=SHOT_OUT+"working-save.json"
  cursor_to(Vector2i(28,3));ui._focus_battle(ui.game.cursor,true);ui.phase_time=0;ui.notice_time=0
  await shot("M15-real-north-gate",checkpoint,"Actual continuation from round-two field via normal input: cavalry occupies the north retreat gate; no position/stat/RNG edits")
 var sample={"observed":observed,"source":source,"actual_keys":inputs,"stat_edits":false,"forced_victories":false,"failures":failures,"image_created":not shots.is_empty(),"scope":"Optional capture continuation; separate from the completed play suites and required layout acceptance"}
 var f=FileAccess.open("res://reports/review-0.2.1/optional-gate-capture-attempt.json",FileAccess.WRITE);f.store_string(JSON.stringify(sample,"  "));f.close()
 if observed:
  var path=SHOT_OUT+"captures.json";var report=State.read_json(path)
  report.shots.append_array(shots)
  for item in shots:report.layout_errors.append_array(item.layout_errors)
  report.passed=report.passed and not abort and report.layout_errors.is_empty()
  f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 await settle();ui.queue_free();await process_frame;ui=null;capture_viewport.queue_free();await process_frame;quit(0 if observed and not abort else 1)
