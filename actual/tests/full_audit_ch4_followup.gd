extends "res://tests/full_audit_ch4.gd"
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
 late_label="boundary-retry" if OS.get_cmdline_user_args().has("--boundary-only") else "followup";late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 for code in ([] if OS.get_cmdline_user_args().has("--boundary-only") else ["M41","M42","M43","M44","F41","F42","F43","F44","S41","S42"]):
  var path=LATE_OUT+"current/current-"+code+"-entry.json";await load_followup(path,code)
  if not abort:
   key(KEY_S);choose("new:goal");await settle()
   flow_checks.append({"kind":"current objective menu","code":code,"source":path,"view_after":ui.view,"notes":ui.game.battle_data.tactical_notes,"status":ui.game.objective_status()})
  await close_followup()
  if abort:break
 if not abort and not OS.get_cmdline_user_args().has("--boundary-only"):
  var path=LATE_OUT+"current/current-after-411.json";await load_followup(path,"ring-ineligible")
  var count_before=ui.game.convoy.alm.count(55)
  await hub_action("fourth_ring_keeper")
  if ui.game.Accessories.claimed(ui.game,55) or ui.game.convoy.alm.count(55)!=count_before:record_failure("Incomplete refuge granted ring")
  flow_checks.append({"kind":"ring ineligible actual dialogue","source":path,"facts":ui.game.flags.get("story_accessory_results",{}),"claimed":ui.game.Accessories.claimed(ui.game,55),"passed":not abort})
  await snapshot("ring-ineligible");await close_followup()
 if not abort:
  var path=LATE_OUT+"current/current-after-408.json";await load_followup(path,"chapter-boundary")
  var before_swords=ui.game.convoy.celica.filter(func(i):return int(i)==17).size()
  await hub_action("fourth_island_verify")
  if not ui.game.flags.get("chapter4_promoted_eileen",false) or ui.game.roster.eileen.get("hero_profession","")!="light_guide":record_failure("Eileen profession absent after normal verification")
  if ui.game.convoy.celica.filter(func(i):return int(i)==17).size()!=before_swords or before_swords<1:record_failure("Light sword absent or duplicated")
  flow_checks.append({"kind":"F44 promotion and light sword persisted; second conversation idempotent","source":path,"profession":ui.game.roster.eileen.get("hero_profession",""),"light_swords":ui.game.convoy.celica.filter(func(i):return int(i)==17).size(),"passed":not abort})
  if ui.view=="hub":await leave_hub()
  await go(9);enter_hub();await settle();await hub_action("third_council");await hub_action("third_messenger");choose("hub:fourth_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter4_closed",false):record_failure("Fourth chapter did not complete")
  if not abort:
   key(KEY_Z);choose("new:chapter5");await settle()
   if ui.game.chapter!=5:record_failure("Fifth chapter did not open")
   else:await snapshot("chapter5-start")
  flow_checks.append({"kind":"fourth-to-fifth chapter boundary","source":path,"chapter":ui.game.chapter,"view":ui.view,"passed":not abort})
  await close_followup()
 var f=FileAccess.open(late_folder+"followup.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"failures":failures,"checks":flow_checks,"checkpoints":checkpoints,"content":observed_content,"inputs":inputs,"source_saves_modified":false,"stat_edits":false,"forced_victories":false},"  "));f.close()
 print("CH4_FOLLOWUP ",JSON.stringify({"passed":not abort,"checks":flow_checks.size(),"failures":failures}));quit(0 if not abort else 1)
