extends RefCounted
## Evidence from a single new-game lineage. Never edits gameplay values.
static var build_hashes={}
static func output_root()->String:
 var suffix=""
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--run="):suffix="-"+arg.trim_prefix("--run=").validate_filename()
 return "res://reports/full-assessment-20261025/campaign"+suffix+"/"

static func snapshot(driver, name:String)->void:
 if driver.abort:return
 if driver.checkpoints.any(func(c):return c.name==name):return
 var g=driver.ui.game
 var old=g.save_path
 var path=driver.late_folder+driver.late_label+"-"+name+".json"
 g.save_path=path
 var ok=g.save_game()
 g.save_path=old
 if not ok:driver.record_failure("Assessment checkpoint failed: "+name);return
 var row={"name":name,"path":path,"sha256":FileAccess.get_file_as_string(path).sha256_text(),"stage":g.stage_id,"turn":g.turn,"view":driver.ui.view,"chapter":g.chapter,"route":g.route,"roster":g.roster.duplicate(true),"convoy":g.convoy.duplicate(true),"treatment_remaining":g.treatment_remaining(),"cleared":g.cleared_stages.duplicate()}
 driver.checkpoints.append(row)
 write(driver)

static func write(driver)->void:
 if driver.late_folder.is_empty() or driver.ui==null:return
 if build_hashes.is_empty():
  for directory in ["res://core/","res://data/stages/"]:
   for file in DirAccess.get_files_at(directory):
    if file.ends_with(".gd") or file.ends_with(".json"):build_hashes[directory+file]=FileAccess.get_sha256(directory+file)
 var g=driver.ui.game
 var summary=[]
 for b in driver.battles:
  var item=b.duplicate(true)
  item.new_casualties=[]
  var before={}
  for u in b.get("initial_players",[]):before[str(u.id)]=u
  for id in b.get("final_roster",{}):
   var unit=b.final_roster[id]
   if g.is_dying(unit) and before.has(id) and not g.is_dying(before[id]):item.new_casualties.append(id)
  summary.append(item)
 var report={"passed":not driver.abort and driver.failures.is_empty(),"chapter":g.chapter,"view":driver.ui.view,"source":driver.source_checkpoint,"failures":driver.failures,"inputs":driver.inputs,"battles":summary,"records":driver.late_records,"checkpoints":driver.checkpoints,"operations":driver.operations,"final_roster":g.roster.duplicate(true),"convoy":g.convoy.duplicate(true),"campaign_complete":g.flags.get("campaign_complete",false),"ending_done":g.flags.get("ending_done",false),"scope":"One fresh campaign lineage continued across chapters with ordinary keyboard input; no attributes, positions, RNG, reward or outcome edits. Instant presentation used. Desktop headless, not human/iPhone play.","stat_edits":false,"forced_victories":false}
 report.source_sha256=FileAccess.get_sha256(driver.source_checkpoint) if FileAccess.file_exists(driver.source_checkpoint) else "new-game"
 report.runtime_hashes=build_hashes
 var f=FileAccess.open(driver.late_folder+"report.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(report,"  "));f.close()
