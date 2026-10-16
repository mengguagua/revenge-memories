extends "res://tests/round3.gd"
## Actual keyboard play, beginning with the recorded chapter-one completion.
## Tactical helper reads normal state; all movement/actions and story use input.
const OUT="res://reports/chapter2/play/"
const ORDER=[201,202,203,211,212,204,205,206]
var initial_west: Dictionary={}
var run_number=1
var resume_code=""
var resume_checkpoint=""
var resume_record: Dictionary={}

func _hub_route(at: Vector2i) -> Array:
 var hub=ui.hub_controller;var start=ui.game.hub_position
 var q: Array=[start];var seen={start:start}
 while not q.is_empty() and not seen.has(at):
  var p=q.pop_front()
  for d in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
   var n=p+d
   if n.x<1 or n.x>12 or n.y<1 or n.y>7 or seen.has(n):continue
   if not hub.east_walkable(n):continue
   if hub.objects.any(func(o):return Vector2i(o.position[0],o.position[1])==n):continue
   seen[n]=p;q.append(n)
 if not seen.has(at):return []
 var path: Array=[at];var p=at
 while p!=start:p=seen[p];path.push_front(p)
 return path

func walk_to(at: Vector2i) -> void:
 var path=_hub_route(at)
 if path.is_empty():record_failure("Hub walk destination blocked: "+str(at));return
 path.pop_front()
 for n in path:
  var d=n-ui.game.hub_position;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP)
  if ui.game.hub_position!=n:record_failure("Hub visual walk differs from input at "+str(n));return

func hub_action(action: String) -> void:
 if abort:return
 var object={}
 for o in ui.hub_controller.objects:
  if str(o.action)==action:object=o;break
 if object.is_empty():
  if action in ["lord","roan","shia"]:
   operations.append({"kind":"recruit unavailable from real battle outcome","id":action});return
  record_failure("Hub object absent: "+action);return
 var at=Vector2i(object.position[0],object.position[1]);var path: Array=[]
 for d in [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]:
  var candidate=_hub_route(at+d)
  if not candidate.is_empty() and (path.is_empty() or candidate.size()<path.size()):path=candidate
 if path.is_empty():record_failure("No facing space for "+action);return
 walk_to(path[-1]);if abort:return
 var facing=at-ui.game.hub_position;key(KEY_RIGHT if facing.x>0 else KEY_LEFT if facing.x<0 else KEY_DOWN if facing.y>0 else KEY_UP)
 key(KEY_Z);await settle()
 operations.append({"kind":"facing confirmation","room":ui.game.hub_record,"action":action})

func go(node: int) -> void:
 if abort:return
 var start=ui.game.world_node;var queue: Array=[start];var seen={start:start};var allowed=ui.game.allowed_world_nodes()
 while not queue.is_empty() and not seen.has(node):
  var at=queue.pop_front()
  for n in ui.world.nodes[str(at)].neighbors:
   n=int(n)
   if seen.has(n) or not allowed.has(n):continue
   seen[n]=at;queue.append(n)
 if not seen.has(node):record_failure("No unlocked road to "+str(node));return
 var path: Array=[];var at=node
 while at!=start:path.push_front(at);at=seen[at]
 for n in path:
  await travel(n)
  if abort:return

func distance_map(unit: Dictionary,goals: Array) -> Dictionary:
 var q: Array=[];var seen={}
 for p in goals:
  if ui.game.in_bounds(p) and ui.game.movement_cost(unit,p)<255 and not seen.has(p):seen[p]=0;q.append(p)
 while not q.is_empty():
  var p=q.pop_front()
  for d in ui.game.DIRECTIONS:
   var n=p+d
   if not ui.game.in_bounds(n) or seen.has(n) or ui.game.movement_cost(unit,n)>=255:continue
   seen[n]=int(seen[p])+1;q.append(n)
 return seen

func rank(unit: Dictionary) -> int:
 if str(unit.id)==ui.game.leader_id():return 3
 if int(unit.class_id) in [17,18]:return 2
 return 0 if int(unit.class_id) in [1,2,3,4,5,6,7,8,9,10,21,22] else 1

func refresh_threats() -> void:
 threats.clear()
 for enemy in ui.game.living("enemy"):
  threats.append({"unit":enemy,"cells":[State.pos(enemy)] if enemy.get("behavior","")=="guard" else ui.game.reachable(enemy).costs.keys()})

func beacon_plan(unit: Dictionary) -> Dictionary:
 var origin=State.pos(unit);var target=ui.game.battle_data.targets[0];var goal=Vector2i(target[0],target[1]);var field=distance_map(unit,[goal]);var graph=ui.game.reachable(unit)
 var before=int(field.get(origin,99999));var defender=str(unit.id)=="lord"
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
    if enemy.get("objective_role","")=="seize_beacon":score+=70.0 if distance(State.pos(enemy),goal)<=5 else 25.0
    if defender and distance(cell,goal)>distance(origin,goal):score-=100.0
    if counter>=int(unit.hp)-Items.cost(weapon):continue
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best

func plan(unit: Dictionary) -> Dictionary:
 if ui.game.stage_id==204 and ui.game.living("enemy").any(func(e):return e.get("objective_role","")=="seize_beacon"):return beacon_plan(unit)
 var enemies=ui.game.living("enemy");var origin=State.pos(unit);var graph=ui.game.reachable(unit)
 var best=combat_plan(unit)
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
   if object.get("optional",false):continue
   if (object.kind=="inspect" or str(object.id) in ["prison_door","hideout"]) and not enemies.is_empty():continue
   var danger=risk(candidate,cell)
   if danger>=int(unit.hp)-4:continue
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
    if object.get("optional",false):continue
    if ui.game.flags.quest.objects.get(str(object.id),false):continue
    var p=Vector2i(object.position[0],object.position[1])
    if not object.get("adjacent",true):goals.append(p)
    else:
     for d in ui.game.DIRECTIONS:goals.append(p+d)
 if enemies.is_empty() and goals.is_empty():
  var exit=Vector2i(ui.game.battle_data.exit[0],ui.game.battle_data.exit[1])
  for cell in graph.costs:
   if not ui.game.can_stop(unit,cell) or distance(cell,exit)<3:continue
   var nearby=0
   for npc in ui.game.units:
    if npc.get("quest_kind","") in ["prisoner","patient","sailor"] and not npc.get("hidden",false) and distance(cell,State.pos(npc))<2:nearby+=1
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

func snapshot(name: String) -> void:
 if abort:return
 var file=OUT+"natural-"+name+"-save.json";var old=ui.game.save_path;ui.game.save_path=file
 if not ui.game.save_game():record_failure("Checkpoint save failed: "+name)
 var archive=OUT+"attempt-"+str(run_number)+"-checkpoints/"
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(archive))
 DirAccess.copy_absolute(ProjectSettings.globalize_path(file),ProjectSettings.globalize_path(archive+"natural-"+name+"-save.json"))
 ui.game.save_path=old
 checkpoints.append({"name":name,"save":file,"view":ui.view,"stage":ui.game.stage_id,"turn":ui.game.turn})

func equip_from_convoy(id: String,item: int) -> void:
 var member=ui.game.roster.get(id,{})
 if member.is_empty() or member.get("dead",false) or int(member.get("item_id",0))!=0:return
 var stored=ui.game.convoy[ui.game.route];var index=-1
 for i in range(stored.size()):
  if int(stored[i])==item:index=i;break
 if index<0:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index));choose("camp:withdraw_member:"+id);await settle()
 if int(ui.game.roster[id].item_id)!=item:record_failure("Actual equipment menu did not equip "+id);return
 operations.append({"kind":"actual convoy equipment","unit":id,"item":item,"node":ui.game.world_node})
 if not ui.menu_items.is_empty():key(KEY_X)

func prepare_east() -> void:
 if ui.game.roster.has("roan") and not ui.game.roster.roan.get("dead",false):
  for id in ui.game.party:
   if id=="roan" or ui.game.roster[id].get("dead",false) or int(ui.game.roster[id].get("item_id",0))!=21:continue
   key(KEY_S);choose("new:camp");choose("camp:trade");choose("camp:trade_first:"+id);choose("camp:trade_second:roan");await settle()
   if int(ui.game.roster.roan.item_id)!=21:record_failure("Actual trade did not give holy bow to archer")
   operations.append({"kind":"actual equipment trade","first":id,"second":"roan","item_to_roan":21})
   if not ui.menu_items.is_empty():key(KEY_X)
 await equip_from_convoy("lord",4)
 await equip_from_convoy("carlo",49)
 await equip_from_convoy("roan",21 if ui.game.flags.get("F25_holy_bow_taken",false) else 49)

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
  var members=ui.game.party.duplicate()
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
 key(KEY_Z);choose("continue_world");await settle()

func invite(id: String) -> void:
 await hub_action(id)
 if ui.menu_actions.has("hub:east_recruit_"+id):choose("hub:east_recruit_"+id);await settle()

func post_battle(stage: int) -> void:
 if abort:return
 enter_hub()
 match stage:
  201:
   await hub_action("sea_route");await hub_action("invite_s21")
  211:await hub_action("s21_report")
  202:
   await hub_action("prisoners_treat");await hub_action("captives_route");await invite("lord")
  203:
   await hub_action("reef_route");await invite("roan");await hub_action("holy_sword");await hub_action("invite_s22")
  212:await hub_action("invite_s22")
  204:
   await hub_action("islanders_settle");await invite("shia")
   await hub_action("resistance_spring");choose("hub:east_spring_eileen");await settle()
   await hub_action("east_training");choose("hub:east_magic_info");await settle();await hub_action("r05")
  205:
   await hub_action("chart_recover");await hub_action("holy_bow");await hub_action("harbor_patients");await hub_action("r05")
   await hub_action("ancient_departure");choose("hub:east_sail_confirm");await settle()
  206:
   await snapshot("arrival-hub");await hub_action("arrival_captain");await hub_action("east_finale");await snapshot("chapter-end")
 await snapshot("after-"+str(stage))
 if stage!=206 and not abort:await leave_hub()

func run() -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--attempt="):run_number=int(arg.split("=")[1])
  if arg.begins_with("--resume="):resume_code=arg.split("=")[1]
  if arg.begins_with("--checkpoint="):resume_checkpoint=arg.split("=")[1]
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 if resume_code.is_empty():
  var source="res://reports/campaign/natural-chapter-end-save.json"
  var initial=OUT+"initial-west-save.json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source),ProjectSettings.globalize_path(initial))
  ui.game.save_path=initial;key(KEY_Z);key(KEY_DOWN);key(KEY_Z)
  if ui.view!="chapter_end":record_failure("Cannot continue actual first chapter completion");finish_report();return
  for id in ui.game.parties.alm:initial_west[id]=ui.game.roster[id].duplicate(true)
  ui.game.save_path=OUT+"progress-save.json"
  key(KEY_Z);choose("new:chapter2");await settle();await snapshot("east-start")
  await hub_action("east_chart_start");await hub_action("east_mireille");await hub_action("east_lisa");await hub_action("east_departure")
  await snapshot("departure-dialogue-finished");await leave_hub()
 else:
  resume_record=State.read_json(OUT+"attempt-"+str(run_number-1)+".json")
  initial_west=resume_record.get("initial_west",{});battles=resume_record.get("battles",[]).filter(func(b):return b.outcome=="victory" and str(b.code)!=resume_code)
  operations=resume_record.get("operations",[]);checkpoints=resume_record.get("checkpoints",[]);inputs=int(resume_record.get("inputs",0))
  ui.game.save_path=OUT+"natural-"+(resume_checkpoint if not resume_checkpoint.is_empty() else resume_code+"-deployment")+"-save.json"
  if not ui.game.load_game():record_failure("Failed to load actual chapter2 checkpoint "+resume_code);finish_report();return
  ui.game.save_path=OUT+"progress-save.json";ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui._focus_battle(ui.game.cursor,true)
 if (OS.get_cmdline_user_args().has("--postpone-side") and resume_code=="S21") or OS.get_cmdline_user_args().has("--restart-entry"):
  key(KEY_S);choose("new:prepare");await settle();resume_code=""
  operations.append({"kind":"returned to preparation through actual menu before a fresh deployment","node":ui.game.world_node})
  await snapshot("side-postponed")
 for stage in ORDER:
  if abort:break
  if ui.game.stage_cleared(stage):continue
  if not resume_code.is_empty() and str(ui.game.stages[stage].code)==resume_code:
   resume_code="";await battle(false)
  else:
   await go(int(ui.game.campaign.stages[str(stage)].node));if not abort:await battle()
  if not abort:await post_battle(stage)
 if not abort:
  if not ui.game.flags.get("chapter2_complete",false) or ui.game.chapter!=2:record_failure("Second chapter did not settle")
  for id in initial_west:
   if ui.game.roster[id]!=initial_west[id]:record_failure("West party state changed during independent east chapter: "+id)
 finish_report()

func write_progress() -> void:
 var report={"round":3,"passed":not abort,"failures":failures,"inputs":inputs,"battles":battles,"operations":operations,"checkpoints":checkpoints,"initial_west":initial_west,"final_roster":ui.game.roster.duplicate(true),"stat_edits":false,"forced_victories":false,"scope":"Chapter2 actual keyboard control from genuine chapter1 completion; directed scenario tests reported separately","attempt":run_number}
 var f=FileAccess.open(OUT+"attempt-"+str(run_number)+".json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
func finish_report() -> void:
 write_progress();print("CHAPTER2_RESULT ",JSON.stringify({"passed":not abort,"inputs":inputs,"battles":battles.size(),"failures":failures,"attempt":run_number}))
 ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
