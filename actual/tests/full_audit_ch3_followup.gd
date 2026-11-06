extends "res://tests/full_audit_ch3.gd"
var flow_checks=[]
func load_followup(path:String,label:String)->void:
 source_checkpoint=path
 var copy=late_folder+label+"-working.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(path),ProjectSettings.globalize_path(copy))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=copy;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Followup load failed: "+path)
 if not abort:ui._resume_journey();await settle()
func close_followup()->void:
 ui.queue_free();await process_frame;await process_frame;ui=null
func run()->void:
 late_label="followup";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 for code in ["M31","M32","M33","F31","F32","F33","S31","S32"]:
  var path=LATE_OUT+"current/current-"+code+"-entry.json";await load_followup(path,code)
  if not abort:
   key(KEY_S);choose("new:goal");await settle()
   flow_checks.append({"kind":"current objective menu","code":code,"source":path,"view_after":ui.view,"notes":ui.game.battle_data.tactical_notes,"status":ui.game.objective_status()})
  await close_followup()
  if abort:break
 if not abort:
  var path=LATE_OUT+"current/current-after-303.json";await load_followup(path,"chapter-boundary")
  if ui.view=="hub":await leave_hub()
  await go(9);enter_hub();await settle();await hub_action("third_council");await leave_hub()
  await switch_team();await go(9);enter_hub();await settle();await hub_action("third_council");await snapshot("D33-council")
  await hub_action("third_relations");await hub_action("third_messenger");choose("hub:third_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter3_complete",false):record_failure("Third chapter did not complete")
  if not abort:
   key(KEY_Z);choose("new:chapter4");await settle()
   if ui.game.chapter!=4:record_failure("Fourth chapter did not open")
   else:await snapshot("chapter4-start")
  flow_checks.append({"kind":"third-to-fourth chapter boundary","source":path,"chapter":ui.game.chapter,"view":ui.view,"passed":not abort})
  await close_followup()
 var f=FileAccess.open(late_folder+"followup.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"failures":failures,"checks":flow_checks,"checkpoints":checkpoints,"content":observed_content,"inputs":inputs,"source_saves_modified":false,"stat_edits":false,"forced_victories":false},"  "));f.close()
 print("CH3_FOLLOWUP ",JSON.stringify({"passed":not abort,"checks":flow_checks.size(),"failures":failures}));quit(0 if not abort else 1)
