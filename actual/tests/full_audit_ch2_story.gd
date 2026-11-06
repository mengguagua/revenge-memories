extends "res://tests/full_audit_ch2.gd"
const Ch2Rules=preload("res://core/chapter2_rules.gd")
# Resume this audit's genuine victory checkpoints. No battles are replayed.
func run()->void:
 late_label="story-verify";late_folder=LATE_OUT+late_label+"/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 for code in ["F24","F26"]:
  abort=false
  var source="res://reports/full-playtest-20261023/ch2/audit/audit-"+code+"-victory.json"
  var source_hash=FileAccess.get_file_as_string(source).sha256_text()
  var working=late_folder+"working-"+code+".json"
  DirAccess.copy_absolute(ProjectSettings.globalize_path(source),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Current victory checkpoint failed: "+code)
  if not abort:ui._resume_journey();await settle()
  var stage=ui.game.stage_id
  if not abort and code=="F26":
   var ending=Ch2Rules._end_lines(ui.game)
   if ending!=str(ui.game.battle_data.after):record_failure("F26 authored ending and live ending disagree")
   if not ending.contains("等候海峡城准许入港") or ending.contains("已经安全靠岸"):record_failure("F26 landing timeline remains contradictory")
   operations.append({"kind":"runtime ending source check; completed battle not replayed","code":code,"text":ending})
  if not abort:
   key(KEY_Z);choose("continue_world");await settle();await post_battle(stage)
  var row={"code":code,"outcome":"victory","scope":"Normal post-victory hub replay only, no repeated battle","source":source,"source_sha256":source_hash,"failures":failures.duplicate(),"view":ui.view,"chapter":ui.game.chapter}
  if FileAccess.get_file_as_string(source).sha256_text()!=source_hash:record_failure("Source victory changed: "+code)
  late_records.append(row);write_progress()
  ui.queue_free();await process_frame;await process_frame;ui=null
 var report=State.read_json(late_folder+late_label+"-play.json")
 report.runtime_ending_checks=operations.filter(func(o):return o.get("kind","")=="runtime ending source check; completed battle not replayed")
 var f=FileAccess.open(late_folder+late_label+"-play.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("STORY_VERIFY ",JSON.stringify({"passed":failures.is_empty(),"failures":failures,"pages":observed_texts.size()}))
 quit(0 if failures.is_empty() else 1)
