extends "res://tests/ch5_environment_play.gd"
const FOLDER="res://reports/chapter5-environment-20261023/hubs/"
var records=[]
func run():
 for room in ["H51","H52","H53","H54","H55","H56"]:
  var source=FOLDER+room+".json";var source_hash=FileAccess.get_file_as_string(source).sha256_text()
  var actions=[]
  ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true;ui.game.save_path=source
  if not ui.game.load_game():record_failure("Missing source "+room)
  ui.game.save_path=FOLDER+"input-working.json"
  if not abort:ui._resume_journey();await settle()
  for obj in ui.hub_controller.objects:actions.append(str(obj.action))
  ui.queue_free();await process_frame;ui=null
  for action in actions:
   var start=inputs;abort=false
   ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true;ui.game.save_path=source
   if not ui.game.load_game():record_failure("Missing source "+room)
   ui.game.save_path=FOLDER+"input-working.json"
   if not abort:ui._resume_journey();await settle();await hub_action(action)
   records.append({"room":room,"action":action,"inputs":inputs-start,"result_view":ui.view,"passed":not abort})
   print("CH2_HUB_ACTION ",room," ",action," ",not abort)
   ui.queue_free();await process_frame;ui=null
  if FileAccess.get_file_as_string(source).sha256_text()!=source_hash:record_failure("Source changed")
 var f=FileAccess.open(FOLDER+"interaction-review.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"failures":failures,"records":records,"inputs":inputs,"source_saves_modified":false,"scope":"Each object approached and confirmed by ordinary inputs from a separate genuine hub checkpoint; no position/flag/stat edits. Recruitment/reward confirmation after opening a menu belongs to two battle rounds."},"  "));f.close()
 quit(0 if failures.is_empty()else 1)
