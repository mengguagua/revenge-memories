extends "res://tests/chapter2_play.gd"
## Both rounds use actual menu inputs from an unchanged chapter4 completion.
## No stat edits, scripted hits, forced wins, or modifications to source checkpoints.
const THIRD_OUT="res://reports/chapter5/play/"
var pass_id="round1"
var source_checkpoint=""
var sample_only=false
var started_inputs=0

func plan(unit: Dictionary) -> Dictionary:
 if ui.game.stage_id==534 and unit.id=="eileen" and not ui.game.living("enemy").is_empty():
  var graph=ui.game.reachable(unit);var boss=ui.game.find_unit("J54_boss");var best={"kind":"wait","cell":State.pos(unit),"score":-1.0e9,"target":"","spell":-1}
  # Keep the vulnerable mandatory leader behind the attacking line. Ordinary movement only.
  for cell in graph.costs:
   if not ui.game.can_stop(unit,cell):continue
   var score=-risk(unit,cell)*12.0+mini(9,distance(cell,State.pos(boss)))*2.0-float(graph.costs[cell])*.1
   if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
  return best
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
 write_progress();print("CH5_PLAY_RESULT ",pass_id," ",JSON.stringify({"passed":not abort,"inputs":inputs,"battles":battles.size(),"failures":failures}))
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
func switch_team() -> void:
 if abort:return
 key(KEY_S);choose("new:switch");await settle()
 operations.append({"kind":"switch route via menu","route":ui.game.route,"node":ui.game.world_node,"previous":ui.game.previous_world_node})
func post_battle(stage: int) -> void:
 if abort or stage==534:return
 enter_hub();await settle()
 match stage:
  501:await hub_action("fifth_ward_report")
  502:await hub_action("fifth_west_report")
  503:await hub_action("fifth_repair_report")
  504:await hub_action("fifth_east_report");await hub_action("fifth_archive_invite")
  511:await hub_action("fifth_archive_report")
  533:await hub_action("fifth_merge")
 await snapshot("after-"+str(stage))
 if not abort:await leave_hub()
func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(THIRD_OUT))
 var resume=""
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--round="):pass_id=arg.substr(8)
  if arg.begins_with("--resume="):resume=arg.substr(9)
  if arg=="--sample":sample_only=true
 source_checkpoint="res://reports/chapter4/play/round2-chapter-end.json" if resume.is_empty() else resume
 var slots=THIRD_OUT+pass_id+"-slots/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(slots))
 var copy_path=slots+"journey-slot-1.json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(copy_path))
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.game.slot_directory=slots;ui.game.save_path=copy_path
 key(KEY_DOWN);key(KEY_Z);key(KEY_Z);await settle()
 if ui.view=="title" or ui.view=="journal":record_failure("title continuation failed");finish_report();return
 if ui.game.chapter==4:
  key(KEY_Z);choose("new:chapter5");await settle();await snapshot("opening")
 if not sample_only and ui.view=="victory":
  var settled_stage=ui.game.stage_id;key(KEY_Z);choose("continue_world");await settle();await post_battle(settled_stage)
 if not sample_only and ui.view=="hub":await leave_hub()
 if sample_only:
  await battle(ui.view!="battle")
  if not abort:await post_battle(ui.game.stage_id)
  finish_report();return
 for id in ([503,504,511,501,502] if pass_id=="round2" else [501,502,503,504,511]):
  if abort:break
  if ui.game.stage_cleared(id):continue
  if ui.game.route!=ui.game.stages[id].route:await switch_team()
  if ui.view=="battle" and ui.game.stage_id==id:await battle(false)
  else:
   await go(int(ui.game.stages[id].node))
   if not abort:await battle()
  if not abort:await post_battle(id)
 if not abort and not ui.game.flags.get("chapter5_merged",false):
  for side in ["alm","celica"]:
   if ui.game.route!=side:await switch_team()
   await go(15);enter_hub();await settle()
   if side=="alm" and ui.game.treatment_remaining()>0 and ui.game.roster.beck.dying and int(ui.game.roster.beck.treatment_count)==0:
    await hub_action("treatment")
    if ui.menu_actions.has("hub:treat_choose_beck"):choose("hub:treat_choose_beck");choose("hub:treat_confirm_beck");await settle()
   await hub_action("fifth_prepare");choose("hub:fifth_ready");await settle();await snapshot("ready-"+side);await leave_hub()
  enter_hub();await settle();await hub_action("fifth_relationship");await hub_action("fifth_merge");choose("hub:fifth_confirm_merge");await settle();await snapshot("merged");await leave_hub()
 for id in [533,534]:
  if abort:break
  if ui.game.stage_cleared(id):continue
  if ui.view=="battle" and ui.game.stage_id==id:await battle(false)
  else:
   await go(int(ui.game.stages[id].node))
   if not abort:await battle()
  if not abort:await post_battle(id)
 if not abort:
  await snapshot("ending-first")
  if ui.view!="ending":record_failure("ending did not start")
  for i in range(120):
   if abort or ui.game.flags.get("ending_done",false):break
   key(KEY_Z);await process_frame
  await snapshot("ending-complete")
  if not ui.game.flags.get("ending_done",false):record_failure("ending did not complete")
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

func battle(enter_encounter: bool=true) -> void:
 if enter_encounter:
  await prepare_east()
  var next_code=str(ui.game.stages[ui.game.stage_for_node(ui.game.world_node)].code)
  await snapshot(next_code+"-before-entry")
  key(KEY_Z);choose("new:battle");await settle()
 if abort:return
 var record={"stage":ui.game.stage_id,"code":ui.game.battle_data.code,"initial_party":ui.game.party.duplicate(),"turns":[],"initial_players":ui.game.living("player").duplicate(true),"initial_enemies":ui.game.living("enemy").duplicate(true)}
 await snapshot(str(record.code)+"-deployment")
 # Open the actual objective menu and read its paginated progress.
 key(KEY_S);choose("new:goal");await settle()
 var captured_objects={}
 var boats_captured=false
 for pass_ in range(90):
  if abort or ui.game.battle_outcome!="":break
  var turn_=ui.game.turn
  var members=ui.game.units.filter(func(u):return u.side=="player" and not u.get("temporary",false) and not u.get("neutral",false)).map(func(u):return str(u.id))
  members.sort_custom(func(a,b):return rank(ui.game.roster[a])<rank(ui.game.roster[b]))
  for id in members:
   if ui.game.turn!=turn_ or ui.game.battle_outcome!="" or abort:break
   await act(str(id))
  if not abort and ui.game.battle_outcome.is_empty() and ui.game.phase=="player" and ui.game.turn==turn_:
   key(KEY_S);choose("end_turn");await settle()
  record.turns.append({"turn":ui.game.turn,"enemies":ui.game.living("enemy").size(),"players":ui.game.living("player").size(),"quest":ui.game.flags.quest.duplicate(true)})
  print("CHAPTER2_PLAY ",record.code," turn ",ui.game.turn," enemies ",ui.game.living("enemy").size()," allies ",ui.game.living("player").size()," ",ui.game.battle_outcome)
  if pass_==2:await snapshot(str(record.code)+"-field")
  for object in ui.game.flags.quest.objects:
   if not captured_objects.has(object):
    captured_objects[object]=true;await snapshot(str(record.code)+"-object-"+str(object))
  if ui.game.stage_id==206 and not boats_captured:
   for boat in ui.game.flags.quest.get("boats",[]):
    if int(boat.get("path_index",0))>=6 and not boat.get("arrived",false):
     boats_captured=true;await snapshot("F26-boats-moving");break
 record.outcome=ui.game.battle_outcome;record.final_turn=ui.game.turn;record.final_roster=ui.game.roster.duplicate(true)
 battles.append(record);write_progress()
 if ui.game.battle_outcome!="victory":record_failure("Natural battle failed: "+str(record.code)+" "+str(ui.game.flags.quest));return
 await snapshot(str(record.code)+"-victory")
 if ui.game.stage_id!=534:key(KEY_Z);choose("continue_world");await settle()


func act(id: String) -> void:
 await super.act(id)
 if not abort and ui.game.stage_id==534 and ui.game.flags.quest.get("final_phase",false) and ui.game.battle_outcome.is_empty() and not checkpoints.any(func(c):return c.name=="J54-half-health"):
  await snapshot("J54-half-health")
