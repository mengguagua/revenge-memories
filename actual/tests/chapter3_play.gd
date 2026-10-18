extends "res://tests/chapter2_play.gd"
## Round 1 continuous real-key play from the unchanged authentic chapter2 checkpoint.
## Round 2 resumes recorded real deployments; fixtures are confined to chapter3_state.gd.
const THIRD_OUT="res://reports/chapter3/play/"
var pass_id="round1"
var source_checkpoint=""
var sample_only=false
var started_inputs=0

func plan(unit: Dictionary) -> Dictionary:
 var enemies=ui.game.living("enemy").filter(func(e):return e.id!="german");var origin=State.pos(unit);var graph=ui.game.reachable(unit)
 var best=combat_plan(unit)
 if best.get("target","")=="german":best={"kind":"wait","cell":origin,"score":0,"target":"","spell":-1}
 # Do not voluntarily accept a lethal counter in the hope of a second strike.
 if best.kind=="attack":
  var target=ui.game.find_unit(str(best.target));var candidate=unit.duplicate(true);candidate.position=[best.cell.x,best.cell.y]
  if int(best.spell)>=0:candidate.weapon_index=int(best.spell)
  var reply=Rules.default_counter(target,distance(best.cell,State.pos(target)))
  var attack=Rules.attack_stats(candidate,target,ui.game.terrain_avoid(State.pos(target)))
  var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(best.cell))
  if int(unit.hp)>Items.cost(int(best.spell))+int(response.damage) or int(attack.damage)>=int(target.hp):return best
 elif best.kind=="heal":return best
 # Resolve necessary interaction through the real action menu after a safe move.
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  for object in ui.game.interactions_for(candidate):
   if object.get("optional",false) and not (ui.game.stage_id==305 and not ui.game.ChapterThree.alive(ui.game,"salt_guide")):continue
   if (object.kind=="inspect" or str(object.id) in ["prison_door","hideout"]) and not enemies.is_empty():continue
   var danger=risk(candidate,cell)
   if danger>=int(unit.hp)-4 and not enemies.is_empty():continue
   return {"kind":"interact","cell":cell,"score":250.0-danger,"target":str(object.id),"spell":-1}
 # Apply formation penalties to the current cell too. A zero baseline can
 # strand a healthy mage more than one move behind a distant front line.
 best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var frontline={};var healer={}
 for ally in ui.game.living("player"):
  if ally.get("neutral",false) or not ally.get("controllable",true):continue
  if int(ally.class_id) in [17,18]:healer=ally
  elif frontline.is_empty() or int(ally.defence)>int(frontline.defence) or (int(ally.defence)==int(frontline.defence) and int(ally.max_hp)>int(frontline.max_hp)):frontline=ally
 var goals: Array=[];var healing_role=int(unit.class_id) in [17,18]
 var protect=ui.game.stage_id in [203,204] and not enemies.is_empty()
 var camp=ui.game.find_unit("fishers")
 var defence_point=State.pos(camp) if ui.game.stage_id==203 and not camp.is_empty() else Vector2i(ui.game.battle_data.targets[0][0],ui.game.battle_data.targets[0][1])
 var low_hp=int(unit.hp)<int(unit.max_hp)*.45
 if not healer.is_empty() and low_hp and str(healer.id)!=str(unit.id):
  for d in ui.game.DIRECTIONS:goals.append(State.pos(healer)+d)
 elif healing_role:
  var injured={};var missing=0
  for ally in ui.game.living("player"):
   if str(ally.id)==str(unit.id) or ally.get("event_object",false):continue
   var amount=int(ally.max_hp)-int(ally.hp)
   if amount>missing:missing=amount;injured=ally
  var ally=injured if not injured.is_empty() else ui.game.find_unit("fishers") if ui.game.stage_id==203 else frontline
  if not ally.is_empty():
   for d in ui.game.DIRECTIONS:goals.append(State.pos(ally)+d)
 else:
  var focus={};var near=99999;var anchor=defence_point if protect else State.pos(frontline) if not frontline.is_empty() else origin
  for enemy in enemies:
   var dist=distance(anchor,State.pos(enemy))
   if dist<near:near=dist;focus=enemy
  if not focus.is_empty():
   var p=State.pos(focus)
   for d in ui.game.DIRECTIONS:goals.append(p+d)
  if goals.is_empty():
   for object in ui.game.battle_data.objects:
    if object.get("optional",false) and not (ui.game.stage_id==305 and not ui.game.ChapterThree.alive(ui.game,"salt_guide")):continue
    if ui.game.flags.quest.objects.get(str(object.id),false):continue
    var p=Vector2i(object.position[0],object.position[1])
    if object.has("approach"):goals.append(Vector2i(object.approach[0],object.approach[1]))
    elif not object.get("adjacent",true):goals.append(p)
    else:
     for d in ui.game.DIRECTIONS:goals.append(p+d)
 if enemies.is_empty() and ui.game.stage_id==303 and ui.game.flags.quest.german_decision=="" and ui.game.ChapterThree.alive(ui.game,"german"):
  var at=State.pos(ui.game.find_unit("german"))
  for d in ui.game.DIRECTIONS:goals.append(at+d)
 if enemies.is_empty() and goals.is_empty():
  var exit=Vector2i(ui.game.battle_data.exit[0],ui.game.battle_data.exit[1])
  for cell in graph.costs:
   if not ui.game.can_stop(unit,cell) or distance(cell,exit)<3:continue
   var nearby=0
   for npc in ui.game.units:
    if npc.get("quest_kind","") in ["prisoner","patient","sailor","escort","guide"] and not npc.get("hidden",false) and distance(cell,State.pos(npc))<2:nearby+=1
   var score=3.0-nearby*10.0-float(graph.costs[cell])*.1
   if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
  return best
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 # Early flying assaults are met as a group; deck edges do not shield healers.
 var hold_line=ui.game.stage_id==211 and ui.game.turn<=3
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var danger=risk(unit,cell);var score=-danger*(3.0 if healing_role or low_hp else 2.0)
  if before<99999 and field.has(cell):score+=(5.0 if protect else 2.0)*(before-int(field[cell]))
  if not protect and not frontline.is_empty() and str(frontline.id)!=str(unit.id):score-=maxi(0,distance(cell,State.pos(frontline))-3)*4.0
  if not protect and not healer.is_empty() and str(healer.id)!=str(unit.id):score-=maxi(0,distance(cell,State.pos(healer))-4)*3.0
  if hold_line:score-=maxi(0,12-cell.y)*9.0+maxi(0,cell.x-8)*9.0
  if danger>=int(unit.hp)-3:score-=200.0
  if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return best


func prepare_east() -> void: pass
func settle() -> void:
 for i in range(10000):
  if abort:return
  if ui.view in ["plot","reward"]:key(KEY_Z)
  elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
  if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:
   await process_frame
   if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
  await process_frame
 record_failure("Third chapter input did not release: "+ui.view)

func snapshot(name: String) -> void:
 if abort:return
 var old=ui.game.save_path;var path=THIRD_OUT+pass_id+"-"+name+".json";ui.game.save_path=path
 if not ui.game.save_game():record_failure("checkpoint write failed "+name)
 ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn,"view":ui.view})
func write_progress() -> void:
 var f=FileAccess.open(THIRD_OUT+pass_id+".json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not abort,"failures":failures,"inputs":inputs,"battles":battles,"operations":operations,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source":source_checkpoint,"round":pass_id,"final_roster":ui.game.roster},"  "));f.close()
func finish_report() -> void:
 write_progress();print("CH3_PLAY_RESULT ",pass_id," ",JSON.stringify({"passed":not abort,"inputs":inputs,"battles":battles.size(),"failures":failures}))
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
func switch_team() -> void:
 if abort:return
 key(KEY_S);choose("new:switch");await settle()
 operations.append({"kind":"switch route via menu","route":ui.game.route,"node":ui.game.world_node,"previous":ui.game.previous_world_node})
func post_battle(stage: int) -> void:
 if abort:return
 enter_hub();await settle()
 match stage:
  301,304:await hub_action("third_reunion")
  302:await hub_action("third_supply");await hub_action("third_s31")
  303:
   await hub_action("third_records_w");await hub_action("third_german")
   if ui.menu_actions.has("hub:third_recruit_german"):choose("hub:third_recruit_german");await settle()
  305:await hub_action("third_route_e");await hub_action("third_s32")
  306:await hub_action("third_records_e")
  311:await hub_action("third_families")
  312:
   await hub_action("third_noya")
   if ui.menu_actions.has("hub:third_recruit_noya"):choose("hub:third_recruit_noya");await settle()
   await hub_action("third_brother")
 await snapshot("after-"+str(stage))
 if not abort:await leave_hub()
func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(THIRD_OUT))
 var resume=""
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--round="):pass_id=arg.substr(8)
  if arg.begins_with("--resume="):resume=arg.substr(9)
  if arg=="--sample":sample_only=true
 source_checkpoint="res://reports/chapter2/play/natural-chapter-end-save.json" if resume.is_empty() else resume
 var copy_path=THIRD_OUT+pass_id+"-working.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(copy_path))
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.save_path=copy_path;key(KEY_Z);key(KEY_DOWN);key(KEY_Z);await settle()
 if ui.view=="title":record_failure("title continuation failed");finish_report();return
 if ui.game.chapter==2:
  key(KEY_Z);choose("new:chapter3");await settle();await snapshot("celebration")
  await hub_action("third_prologue");await snapshot("D31-finished")
 if not sample_only and ui.view=="victory":
  var settled_stage=ui.game.stage_id
  key(KEY_Z);choose("continue_world");await settle();await post_battle(settled_stage)
 if not sample_only and ui.view=="hub":await leave_hub()
 if sample_only:
  await battle(ui.view!="battle")
  if not abort:await post_battle(ui.game.stage_id)
  finish_report();return
 # Opening escape order, then genuine independent routes. No direct travel/state edits.
 for id in [301,304,305,312,306,302,311,303]:
  if abort:break
  if ui.game.stage_cleared(id):continue
  var wanted=ui.game.stages[id].route
  if ui.game.route!=wanted:await switch_team()
  if ui.view=="battle" and ui.game.stage_id==id:await battle(false)
  else:
   await go(int(ui.game.stages[id].node))
   if not abort:await battle()
  if not abort:await post_battle(id)
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await leave_hub()
  await switch_team();await go(9);enter_hub();await settle();await hub_action("third_council")
  await snapshot("D33-council")
  await hub_action("treatment")
  var member="mireille" if ui.game.route=="celica" else "fula"
  if ui.menu_actions.has("hub:treat_choose_"+member):
   choose("hub:treat_choose_"+member);choose("hub:treat_confirm_"+member);await settle()
  elif not ui.menu_items.is_empty():key(KEY_X)
  await hub_action("third_relations");await hub_action("third_messenger");choose("hub:third_finish");await settle()
  await snapshot("chapter-end")
  if not ui.game.flags.get("chapter3_complete",false):record_failure("third chapter did not complete")
 finish_report()
