extends "res://tests/chapter2_play.gd"
## Round 1 continuous real-key play from the unchanged authentic chapter2 checkpoint.
## Round 2 resumes recorded real deployments; fixtures are confined to chapter3_state.gd.
const THIRD_OUT="res://reports/chapter4/play/"
var pass_id="round1"
var source_checkpoint=""
var sample_only=false
var started_inputs=0

func plan(unit: Dictionary) -> Dictionary:
 if ui.game.stage_id==405 and ui.game.turn<=6 and unit.id=="lord" and ui.game.living("enemy").any(func(e):return e.has("well_target")):
  var healing=combat_plan(unit)
  if healing.kind=="heal":return healing
  return well_plan(unit)
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
 var protect=ui.game.stage_id in [203,204,401] and not enemies.is_empty()
 var camp=ui.game.find_unit("fishers")
 var defence_point=State.pos(camp) if ui.game.stage_id==203 and not camp.is_empty() else Vector2i(ui.game.battle_data.targets[0][0],ui.game.battle_data.targets[0][1])
 if ui.game.stage_id==401:defence_point=Vector2i(13,10)
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
 write_progress();print("CH4_PLAY_RESULT ",pass_id," ",JSON.stringify({"passed":not abort,"inputs":inputs,"battles":battles.size(),"failures":failures}))
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
func switch_team() -> void:
 if abort:return
 key(KEY_S);choose("new:switch");await settle()
 operations.append({"kind":"switch route via menu","route":ui.game.route,"node":ui.game.world_node,"previous":ui.game.previous_world_node})
func post_battle(stage: int) -> void:
 if abort:return
 enter_hub();await settle()
 match stage:
  401:await hub_action("fourth_snow_settle");await hub_action("fourth_s41")
  402:await hub_action("fourth_transfer_report");await hub_action("fourth_letters")
  403:await hub_action("fourth_tower_shutdown")
  404:await hub_action("fourth_herlan")
  405:await hub_action("fourth_well_report")
  406:await hub_action("fourth_obs_report")
  407:await hub_action("fourth_marsh_report");await hub_action("fourth_s42")
  408:await hub_action("fourth_island_verify");await hub_action("fourth_d42")
  411:await hub_action("fourth_black_report")
  412:
   await hub_action("fourth_celine")
   if ui.menu_actions.has("hub:fourth_recruit_celine"):choose("hub:fourth_recruit_celine");await settle()
   await hub_action("fourth_vya")
 await snapshot("after-"+str(stage))
 if not abort:await leave_hub()
func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(THIRD_OUT))
 var resume=""
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--round="):pass_id=arg.substr(8)
  if arg.begins_with("--resume="):resume=arg.substr(9)
  if arg=="--sample":sample_only=true
 source_checkpoint="res://reports/chapter3/play/round1final-chapter-end.json" if resume.is_empty() else resume
 var slots=THIRD_OUT+pass_id+"-slots/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(slots))
 var copy_path=slots+"journey-slot-1.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(copy_path))
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.slot_directory=slots;ui.game.save_path=copy_path
 key(KEY_DOWN);key(KEY_Z);key(KEY_Z);await settle()
 if ui.view=="title" or ui.view=="journal":record_failure("title continuation failed");finish_report();return
 if ui.game.chapter==3:
  key(KEY_Z);choose("new:chapter4");await settle();await snapshot("opening")
  # Spend the two genuinely remaining sources through the camp's normal confirmation.
  for route_ in ["alm","celica"]:
   if ui.game.route!=route_:await switch_team()
   enter_hub();await settle();await hub_action("treatment")
   var member="fula" if route_=="alm" else "lisa"
   if ui.menu_actions.has("hub:treat_choose_"+member):choose("hub:treat_choose_"+member);choose("hub:treat_confirm_"+member);await settle()
   elif not ui.menu_items.is_empty():key(KEY_X)
   await leave_hub()
 if not sample_only and ui.view=="victory":
  var settled_stage=ui.game.stage_id;key(KEY_Z);choose("continue_world");await settle();await post_battle(settled_stage)
 if not sample_only and ui.view=="hub":await leave_hub()
 if sample_only:
  await battle(ui.view!="battle")
  if not abort:await post_battle(ui.game.stage_id)
  finish_report();return
 for id in [401,411,402,403,405,406,407,412,404,408]:
  if abort:break
  if ui.game.stage_cleared(id):continue
  var wanted=ui.game.stages[id].route
  if ui.game.route!=wanted:await switch_team()
  if id==404 and not ui.game.flags.get("west_tower_safe",false):
   await go(12);enter_hub();await settle();await hub_action("fourth_tower_shutdown");await leave_hub()
  if ui.view=="battle" and ui.game.stage_id==id:await battle(false)
  else:
   await go(int(ui.game.stages[id].node))
   if not abort:await battle()
  if not abort:await post_battle(id)
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await hub_action("third_messenger");choose("hub:fourth_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter4_closed",false):record_failure("fourth chapter did not complete")
 finish_report()

func well_plan(unit: Dictionary) -> Dictionary:
 var origin=State.pos(unit);var target=[5,6] if str(unit.id) in ["shia","roan","lisa"] else [19,20];var goal=Vector2i(target[0],target[1]);var field=distance_map(unit,[goal]);var graph=ui.game.reachable(unit)
 var before=int(field.get(origin,99999));var defender=str(unit.id) in ["lord","shia"]
 var best={"kind":"wait","cell":origin,"score":-risk(unit,origin),"target":"","spell":-1}
 var weapons: Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell);var progress=before-int(field.get(cell,99999))
  var walking=progress*(24.0 if defender else 10.0)-danger*1.1
  if defender and cell==goal:walking+=60.0
  if danger>=int(unit.hp)-2:walking-=120.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var reply=Rules.default_counter(enemy,distance(cell,State.pos(enemy)))
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var count=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var damage=float(stats.damage*count)*stats.hit/100.0;var kill=damage>=int(enemy.hp)*.95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*response.hit/100.0 if Rules.can_attack(reply,distance(cell,State.pos(enemy))) else 0.0
    var score=walking+minf(damage,enemy.hp)*2+(35.0 if kill else 0.0)-counter-Items.cost(weapon)
    if enemy.has("well_target"):score+=70.0 if distance(State.pos(enemy),goal)<=5 else 25.0
    if defender and distance(cell,goal)>distance(origin,goal):score-=100.0
    if counter>=int(unit.hp)-Items.cost(weapon):continue
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best
