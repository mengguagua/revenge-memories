extends "res://tests/full_audit_ch5.gd"
## Normal hub/menu inputs from this audit's actual victory records; no battles repeated.
const FLOW_OUT="res://reports/full-playtest-20261023/ch5/flow/"
var flow_checks=[]
var flow_sources=[]
func load_current(name:String)->void:
 if is_instance_valid(ui):ui.queue_free();await process_frame;ui=null
 var source="res://reports/full-playtest-20261023/ch5/current/current-"+name+".json"
 flow_sources.append({"path":source,"sha256":FileAccess.get_file_as_string(source).sha256_text()})
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path=source
 if not ui.game.load_game():record_failure("Current victory checkpoint does not load: "+name);return
 ui.game.save_path=FLOW_OUT+"working.json";ui._resume_journey();await settle()
func verify(ok:bool,label:String)->void:
 flow_checks.append({"label":label,"passed":ok})
 if not ok:record_failure(label)
func run()->void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FLOW_OUT))
 late_folder=FLOW_OUT;late_label="flow"
 await load_current("after-502")
 if not abort:await leave_hub()
 for side in ["alm","celica"]:
  if abort:break
  if ui.game.route!=side:await switch_team()
  await go(15);enter_hub();await settle();await hub_action("fifth_prepare")
  if not abort:choose("hub:fifth_ready");await settle();await leave_hub()
 if not abort:
  enter_hub();await settle();await hub_action("fifth_relationship");await hub_action("fifth_merge")
  choose("hub:fifth_confirm_merge");await settle()
  verify(ui.game.flags.get("chapter5_merged",false),"both actual preparation lists allow joint departure")
  await snapshot("after-merge");await leave_hub()
  key(KEY_Z);choose("new:battle");await settle()
  verify(ui.view=="battle" and ui.game.stage_id==533,"joint departure enters J53 through normal battle menu")
  await snapshot("J53-deployment")
 if not abort:
  await load_current("after-533");await leave_hub();await go(16)
  key(KEY_Z);choose("new:battle");await settle()
  verify(ui.view=="battle" and ui.game.stage_id==534,"current J53 victory unlocks and enters J54")
  await snapshot("J54-deployment")
 if not abort:
  await load_current("ending-complete")
  verify(ui.view=="ending" and ui.game.flags.get("campaign_complete",false) and ui.game.flags.get("ending_done",false),"completed current ending reloads at its saved conclusion")
 for source in flow_sources:verify(FileAccess.get_file_as_string(source.path).sha256_text()==source.sha256,"source victory record unchanged: "+str(source.path))
 var f=FileAccess.open(FLOW_OUT+"checks.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not abort,"checks":flow_checks,"failures":failures,"inputs":inputs,"sources":flow_sources,"observed_content":audit_content,"scope":"Actual hub/menu progression from this audit's independent victory checkpoints. No repeated battles, no flags/stat/RNG edits; not a single continuous new-game campaign."},"  "));f.close()
 print("FULL_AUDIT_CH5_FLOW ",flow_checks.size()," inputs=",inputs," failures=",failures)
 if is_instance_valid(ui):ui.queue_free();await process_frame
 quit(1 if abort else 0)
