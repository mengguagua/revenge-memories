extends "res://tests/assessment_ch5.gd"
## Independent authentic checkpoints. All gameplay and equipment use UI inputs.
const SOURCES={
 "M13":"res://reports/full-assessment-20261025/campaign-final-r1/ch1/chain-M13-deployment.json",
 "M33":"res://reports/chapter3/play/round1final-M33-before-entry.json",
 "M52":"res://reports/chapter5/play/round2-M52-before-entry.json",
 "J53":"res://reports/chapter5/play/round2-J53-before-entry.json"
}
class WatchedState extends "res://core/game_state.gd":
 var displacements:Array=[]
 var cover_hits:Array=[]
 var elite_attacks:Array=[]
 func finish_exchange(e:Dictionary)->Dictionary:
  var target=find_unit(str(e.get("defender","")));var before=target.get("position",[]).duplicate()
  var actor=find_unit(str(e.get("attacker","")))
  var is_elite=Knockback.innate(self,actor)
  var result=super.finish_exchange(e)
  if not target.is_empty() and before!=target.position:
   displacements.append({"turn":turn,"attacker":e.attacker,"defender":e.defender,"from":before,"to":target.position.duplicate(),"side":actor.side,"events":e.events.duplicate(true)})
  if is_elite:elite_attacks.append({"turn":turn,"attacker":e.attacker,"events":e.events.duplicate(true)})
  return result
 func commit_strike(e:Dictionary)->void:
  if not e.get("cover",{}).is_empty():cover_hits.append({"turn":turn,"event":e.duplicate(true)})
  super.commit_strike(e)
var audit_round="round1"
var asked_codes:PackedStringArray=["M13","M33","M52","J53"]
var active_record:Dictionary={}
func run()->void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--round="):audit_round=arg.trim_prefix("--round=")
  if arg.begins_with("--codes="):asked_codes=arg.trim_prefix("--codes=").split(",")
 late_label=audit_round
 late_folder="res://reports/tactical-expansion-20261025/knockback-play/"+audit_round+"/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 for code in asked_codes:
  abort=false;path_cache.clear();risk_cache.clear();var fail_start=failures.size();var input_start=inputs
  source_checkpoint=SOURCES[code];var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text()
  var working=late_folder+"working-"+code+".json"
  DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game=WatchedState.new();ui.game.slot_directory=late_folder;ui.game.save_path=working
  root.add_child(ui);await process_frame;ui.instant_mode=true
  active_record={"code":code,"round":audit_round,"source":source_checkpoint,"source_sha256":source_hash,"outcome":"incomplete"}
  if not ui.game.load_game():record_failure("Authentic checkpoint did not load: "+code)
  if not abort:
   ui._resume_journey();await settle();var node=ui.game.world_node
   if ui.game.mode=="battle":key(KEY_S);choose("new:prepare");await settle()
   await go(node)
   if not abort:await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle()
   if not abort and str(ui.game.battle_data.code)!=code:record_failure("Wrong stage entered")
   var count=battles.size()
   if not abort:await battle(false)
   if battles.size()>count:active_record.merge(battles[-1],true)
   if not abort and code=="M13":
    if ui.game.convoy.alm.filter(func(id):return int(id)==67).size()!=1:record_failure("M13 did not grant one rejecting lance")
    else:active_record.reward_verified=true
  active_record.displacements=ui.game.displacements.duplicate(true)
  active_record.cover_hits=ui.game.cover_hits.duplicate(true)
  active_record.elite_attacks=ui.game.elite_attacks.duplicate(true)
  active_record.key_inputs=inputs-input_start;active_record.final_turn=ui.game.turn
  if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source checkpoint changed")
  active_record.failures=failures.slice(fail_start);late_records.append(active_record.duplicate(true));write_progress()
  print("KNOCKBACK_PLAY ",audit_round," ",code," ",active_record.outcome," pushes=",active_record.displacements.size()," errors=",active_record.failures)
  ui.queue_free();await process_frame;ui=null
 write_progress();quit(0 if late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()) else 1)

func snapshot(name:String)->void:
 if abort or not (name.ends_with("deployment") or name.ends_with("victory")):return
 var old=ui.game.save_path;ui.game.save_path=late_folder+name+".json"
 if not ui.game.save_game():record_failure("Checkpoint save failed: "+name)
 ui.game.save_path=old

func write_progress()->void:
 if late_folder.is_empty():return
 var f=FileAccess.open(late_folder+"report.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"round":audit_round,"passed":not late_records.is_empty() and late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()),"records":late_records,"inputs":inputs,"failures":failures,"operations":operations,"scope":"Independent historical genuine checkpoints, normal preparation return/reentry, equipment menus and gameplay inputs. No party/stat/RNG/position/outcome injection. Headless controller play, not phone or full new-game campaign."},"  "));f.close()

func prepare_current()->void:
 await super.prepare_current()
 if abort:return
 for id in ui.game.party:
  var member=ui.game.roster.get(str(id),{})
  if not member.is_empty() and ui.game.can_deploy(member) and Items.can_use(member,67):
   await equip_rejecting_lance(str(id));break

func equip_rejecting_lance(id:String)->void:
 if int(ui.game.roster[id].item_id)==67:return
 var index=-1
 for i in range(ui.game.convoy[ui.game.route].size()):
  if int(ui.game.convoy[ui.game.route][i])==67:index=i;break
 if index<0:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index))
 if abort:return
 if ui.view!="equipment_members" or not ui.equipment_screen.members.has(id):record_failure("Rejecting lance recipient unavailable");return
 for i in range(ui.equipment_screen.members.size()):
  if str(ui.equipment_screen.members[ui.equipment_screen.selected])==id:break
  key(KEY_DOWN)
 key(KEY_Z)
 if ui.view!="equipment_preview" or not ui.equipment_screen.preview().can_equip:record_failure("Rejecting lance preview rejected legal infantry");return
 key(KEY_Z);await settle()
 if int(ui.game.roster[id].item_id)!=67:record_failure("Rejecting lance not equipped")
 operations.append({"kind":"ordinary equipment choice for tactical utility","unit":id,"item":67,"code":active_record.code})
 if not ui.menu_items.is_empty():key(KEY_X)

func rank(u:Dictionary)->int:
 if audit_round=="round2" and int(u.get("item_id",0))==67:return -2
 return super.rank(u)
