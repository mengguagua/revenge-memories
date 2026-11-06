extends "res://tests/assessment_ch5.gd"
## Genuine M51 reward branch -> M52 -> J53 -> J54, with ordinary input only.
## J54 deliberately advances only Eileen after a legal adjacent shield exchange.
class WatchedState extends "res://core/game_state.gd":
 var observed_strikes=[]
 var observed_recovery=[]
 func commit_strike(event:Dictionary)->void:
  if stage_id==534:observed_strikes.append({"turn":turn,"phase":phase,"event":event.duplicate(true)})
  super.commit_strike(event)
 func next_phase()->void:
  var previous={}
  for u in living("player"):previous[u.id]=int(u.hp)
  super.next_phase()
  if stage_id==534 and phase=="player":
   for u in living("player"):
    if int(u.hp)>int(previous.get(u.id,u.hp)):observed_recovery.append({"turn":turn,"unit":u.id,"before":previous[u.id],"after":u.hp,"item_id":u.item_id})
var shield_exchanged=false
var solo_probe=true
var branch_source_hash=""
func run()->void:
 late_label="shield"
 solo_probe=not OS.get_cmdline_user_args().has("--shield-party")
 late_folder="res://reports/full-assessment-20261025/ai/shield-play/"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--shield-label="):late_folder="res://reports/full-assessment-20261025/ai/shield-"+arg.trim_prefix("--shield-label=").validate_filename()+"/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/full-playtest-20261023/ch5/current/current-after-501.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--shield-source="):source_checkpoint=arg.trim_prefix("--shield-source=")
 branch_source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text()
 ui=load("res://scenes/main.tscn").instantiate();ui.game=WatchedState.new();ui.game.slot_directory=late_folder;ui.game.save_path=source_checkpoint
 root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine rewarded M51 branch does not load")
 ui.game.save_path=late_folder+"working.json"
 if not abort:ui._resume_journey();await settle();await snapshot("source")
 if ui.view.begins_with("hub"):await leave_hub()
 if not ui.game.stage_cleared(502):
  await go(int(ui.game.stages[502].node));await prepare_current();await continuous_battle("M52")
 if not abort and not ui.game.flags.get("chapter5_merged",false):
  for side in ["alm","celica"]:
   if ui.game.route!=side:await switch_team()
   await go(15);enter_hub();await settle()
   if side=="celica":await treat_normally("shia")
   await hub_action("fifth_prepare")
   for member in ui.game.parties[side]:
    if ui.game.can_deploy(ui.game.roster[member]) and not ui.game.ChapterFive.selection(ui.game,side).has(member) and ui.game.ChapterFive.selection(ui.game,side).size()<10:
     choose("hub:fifth_toggle_"+str(member));await settle()
   choose("hub:fifth_ready");await settle();await snapshot("ready-"+side);await leave_hub();await prepare_current()
  enter_hub();await settle();await hub_action("fifth_relationship");await hub_action("fifth_merge");choose("hub:fifth_confirm_merge");await settle();await snapshot("merged");await leave_hub()
 for code in ["J53","J54"]:
  if abort:break
  var stage=533 if code=="J53" else 534
  if ui.game.stage_cleared(stage):continue
  await go(int(ui.game.stages[stage].node));await prepare_current()
  if not abort:await continuous_battle(code)
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=branch_source_hash:record_failure("Source reward branch changed")
 write_progress()
 ui.queue_free();await process_frame;ui=null
 quit(1 if abort else 0)
func snapshot(name:String)->void:
 if abort:return
 var old=ui.game.save_path;var path=late_folder+late_label+"-"+name+".json";ui.game.save_path=path
 if not ui.game.save_game():record_failure("Shield branch checkpoint failed")
 ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn})
 write_progress()
func write_progress()->void:
 if ui==null or late_folder.is_empty():return
 var report={"passed":not abort and ui.game.flags.get("ending_done",false),"failures":failures,"inputs":inputs,"source":source_checkpoint,"source_sha256":branch_source_hash,"battles":battles,"records":late_records,"operations":operations,"checkpoints":checkpoints,"shield_exchanged":shield_exchanged,"solo_probe":solo_probe,"strikes":ui.game.observed_strikes,"recovery":ui.game.observed_recovery,"scope":"Genuine historical M51 post-battle state with legitimately earned shield; all following movement, equipment, team preparation, exchange and combat use normal UI inputs. No HP, attributes, RNG, positions, acquired items or outcome injections. This is a separate historical branch, not the fresh full campaign."}
 var f=FileAccess.open(late_folder+"report.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
func prepare_current()->void:
 if int(ui.game.roster.hunapu.item_id)==53:return
 var index=-1
 for n in range(ui.game.convoy.alm.size()):
  if int(ui.game.convoy.alm[n])==53:index=n;break
 if index<0:return
 if ui.game.route!="alm":await switch_team()
 if abort:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index))
 if abort:return
 for step in range(ui.equipment_screen.members.size()):
  if str(ui.equipment_screen.members[ui.equipment_screen.selected])=="hunapu":break
  key(KEY_DOWN)
 key(KEY_Z);key(KEY_Z);await settle()
 if int(ui.game.roster.hunapu.item_id)!=53:record_failure("Earned shield was not equipped through camp")
 operations.append({"kind":"ordinary earned-shield equipment","unit":"hunapu","item":53})
 if not ui.menu_items.is_empty():key(KEY_X)
func rank(u:Dictionary)->int:
 if ui.game.stage_id==534:
  if u.id=="hunapu":return -2
  if u.id=="eileen":return -1
 return super.rank(u)
func act(id:String)->void:
 if ui.game.stage_id==534 and not shield_exchanged and id in ["hunapu","eileen"]:
  var u=ui.game.find_unit(id)
  if u.is_empty() or u.acted or int(u.hp)<=0:return
  var other=ui.game.find_unit("eileen" if id=="hunapu" else "hunapu")
  var best=State.pos(u);var gap=99999
  var goals=[]
  for step in ui.game.DIRECTIONS:goals.append(State.pos(other)+step)
  var field=distance_map(u,goals)
  for cell in ui.game.reachable(u).costs:
   if ui.game.can_stop(u,cell) and int(field.get(cell,99999))<gap:best=cell;gap=int(field.get(cell,99999))
  cursor_to(State.pos(u));key(KEY_Z);cursor_to(best);key(KEY_Z);await settle()
  if abort:return
  if distance(State.pos(u),State.pos(other))==1:
   choose("exchange");choose("exchange:"+str(other.id));await settle()
   shield_exchanged=int(ui.game.find_unit("eileen").item_id)==53
   if not shield_exchanged:record_failure("Normal adjacent shield exchange failed")
   else:operations.append({"kind":"ordinary adjacent cross-party shield exchange","turn":ui.game.turn,"initiator":u.id,"counterpart":other.id,"item_from":"hunapu","item_to":"eileen","eileen_item":53})
  else:choose("wait");await settle()
  return
 await super.act(id)
func plan(u:Dictionary)->Dictionary:
 if ui.game.stage_id!=534 or not solo_probe:return super.plan(u)
 var origin=State.pos(u)
 if u.id!="eileen" or not shield_exchanged:return {"kind":"wait","cell":origin,"target":"","spell":-1,"score":0.0}
 # Deliberately simple default-sword advance; no active healing or offensive magic.
 var enemies=ui.game.living("enemy");var goals=[]
 for enemy in enemies:
  for step in ui.game.DIRECTIONS:goals.append(State.pos(enemy)+step)
 var field=distance_map(u,goals);var graph=ui.game.reachable(u);var best={"kind":"wait","cell":origin,"target":"","spell":-1,"score":-1.0e9}
 for cell in graph.costs:
  if not ui.game.can_stop(u,cell):continue
  var actor=u.duplicate(true);actor.position=[cell.x,cell.y];actor.erase("weapon_index")
  var walking=-float(field.get(cell,99999))*2.0-risk(actor,cell)*.3-float(graph.costs[cell])*.01
  if walking>best.score:best={"kind":"wait","cell":cell,"target":"","spell":-1,"score":walking}
  for enemy in ui.game.targets(actor):
   var stats=Rules.attack_stats(actor,enemy,ui.game.terrain_avoid(State.pos(enemy)))
   var count=Rules.strike_sequence(actor,Rules.default_counter(enemy,distance(cell,State.pos(enemy))),distance(cell,State.pos(enemy))).count("attacker")
   var damage=float(stats.damage)*float(stats.hit)/100.0*count
   var score=walking+minf(damage,float(enemy.hp))*3.0+(40.0 if damage>=int(enemy.hp) else 0.0)
   if score>best.score:best={"kind":"attack","cell":cell,"target":str(enemy.id),"spell":-1,"score":score}
 return best
