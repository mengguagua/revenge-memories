extends "res://tests/battlefield_redesign_play.gd"
## Re-enter the current maps through real preparation/world menus, then play
## with the established input driver. No gameplay state or random outcomes edited.
func _initialize() -> void:
 var label="polish-west"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):label=arg.split("=")[1]
 review_out="res://reports/map-polish-20261022/play/"+label+"/"
 call_deferred("run")

func settle() -> void:
 for i in range(10000):
  if abort:return
  if ui.view in ["plot","reward"]:key(KEY_Z)
  elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
  if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:
   await process_frame
   if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
  await process_frame
 record_failure("Current result/dialogue input did not release: "+ui.view)

func go(node:int) -> void:
 await super.go(node)
 if not abort and ui.game.mode=="world" and ui.game.stage_id==111:
  # This genuine checkpoint already owns M11's iron sword in the convoy.
  # Equip it through the same preparation menus a player uses before rescue.
  await equip_from_convoy("hunapu",60)

func plan(unit:Dictionary) -> Dictionary:
 if ui.game.stage_id==111 and not ui.game.living("enemy").is_empty():
  # Defend the moving miners first; the tools can be collected after the lane is safe.
  return combat_plan(unit)
 return super.plan(unit)

func tower_plan(unit:Dictionary) -> Dictionary:
 if str(unit.id)=="lance":return super.tower_plan(unit)
 # Use the normal combat preview and lethal-counter checks rather than the
 # old runner policy, which sent a wounded commander alone into the boss guard.
 return combat_plan(unit)

func equip_from_convoy(id:String,item:int) -> void:
 var member=ui.game.roster.get(id,{})
 if member.is_empty() or member.get("dead",false) or int(member.get("item_id",0))!=0:return
 var stored=ui.game.convoy[ui.game.route];var index=-1
 for i in range(stored.size()):
  if int(stored[i])==item:index=i;break
 if index<0:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index))
 if abort:return
 if ui.view!="equipment_members" or not ui.equipment_screen.members.has(id):record_failure("Current equipment member list absent");return
 for i in range(ui.equipment_screen.members.size()):
  if str(ui.equipment_screen.members[ui.equipment_screen.selected])==id:break
  key(KEY_DOWN)
 key(KEY_Z)
 if ui.view!="equipment_preview" or not ui.equipment_screen.preview().can_equip:record_failure("Equipment comparison rejected "+id);return
 key(KEY_Z);await settle()
 if int(ui.game.roster[id].item_id)!=item:record_failure("Equipment confirmation failed "+id);return
 operations.append({"kind":"actual convoy equipment comparison and confirmation","unit":id,"item":item,"node":ui.game.world_node})
 if not ui.menu_items.is_empty():key(KEY_X)

func write_review() -> void:
 super.write_review()
 var file=review_out+review_label+"-play.json"
 var record=State.read_json(file)
 record.map_hashes={}
 for battle in review_battles:
  var path="res://data/stages/"+str(battle.code)+".json"
  record.map_hashes[battle.code]=FileAccess.get_file_as_string(path).sha256_text()
 record.revision="map-polish-20261022"
 record.verification="Ordinary input and actual checkpoint rosters; no attributes, RNG, positions or win conditions overridden. Separate geometry fixtures are not playthroughs."
 var f=FileAccess.open(file,FileAccess.WRITE);f.store_string(JSON.stringify(record,"  "));f.close()
