extends "res://tests/chapter4_play.gd"
# Fourth-chapter isolated real-input review; no live attributes or outcomes edited.

const LATE_OUT="res://reports/chapter4-redesign-20261022/play/"
var late_label="round1"
var late_codes:PackedStringArray=[]
var late_folder=""
var late_entry_only=false
var late_records=[]
var path_cache={}
var risk_cache={}
func _initialize():call_deferred("run")
func distance_map(unit:Dictionary,goals:Array)->Dictionary:
 var k=str(ui.game.stage_id)+":"+str(unit.class_id)+":"+str(unit.get("item_id",0))+":"+JSON.stringify(goals)+":"+JSON.stringify(ui.game.flags.quest.objects)
 if not path_cache.has(k):path_cache[k]=super.distance_map(unit,goals)
 return path_cache[k]
func refresh_threats()->void:
 risk_cache.clear();threats.clear()
 for e in ui.game.living("enemy"):
  var mobile=e.get("behavior","")!="guard" or int(e.class_id) in [12,13,15,16]
  threats.append({"unit":e,"cells":ui.game.reachable(e).costs.keys() if mobile else [State.pos(e)]})
func risk(unit:Dictionary,cell:Vector2i,skip:String="")->float:
 var k=str(unit.id)+":"+str(unit.hp)+":"+str(unit.get("weapon_index",-1))+":"+str(cell)+":"+skip
 if not risk_cache.has(k):risk_cache[k]=super.risk(unit,cell,skip)
 return float(risk_cache[k])
func snapshot(name:String)->void:
 if abort:return
 var old=ui.game.save_path;var path=late_folder+late_label+"-"+name+".json";ui.game.save_path=path
 if not ui.game.save_game():record_failure("Checkpoint write failed: "+name)
 ui.game.save_path=old;checkpoints.append({"name":name,"path":path,"stage":ui.game.stage_id,"turn":ui.game.turn,"view":ui.view})
func write_progress()->void:
 var f=FileAccess.open(late_folder+late_label+"-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":failures.is_empty() and not late_records.is_empty() and late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()),"entry_only":late_entry_only,"failures":failures,"total_inputs":inputs,"battles":late_records,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source_saves_modified":false,"operations":operations,"route_trace":operations.filter(func(a):return a.get("kind","")=="route trace"),"scope":"Independent genuine pre-battle world checkpoints, ordinary current-map entry, actual input battles and post-battle hub actions; no live attributes, RNG, positions or win conditions edited."},"  "));f.close()
func run()->void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
  if arg.begins_with("--codes="):late_codes=arg.trim_prefix("--codes=").split(",")
  if arg=="--entry-only":late_entry_only=true
 if OS.get_cmdline_user_args().has("--continuous"):
  await run_continuous();return
 if late_codes.is_empty():late_codes=["M41", "M42", "M43", "M44", "F41", "F42", "F43", "F44", "S41", "S42"]
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var sources=State.read_json("res://reports/chapter4-redesign-20261022/sources.json")
 for code in late_codes:
  abort=false;path_cache.clear();risk_cache.clear();var failures_before=failures.size();var inputs_before=inputs
  source_checkpoint=str(sources[code]);var raw=FileAccess.get_file_as_string(source_checkpoint);var source_hash=raw.sha256_text()
  var working=late_folder+"working-"+code+".json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
  ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
  if not ui.game.load_game():record_failure("Genuine checkpoint failed: "+code)
  if not abort:
   ui._resume_journey();await settle()
   var target_node=ui.game.world_node
   if ui.game.mode=="battle":
    key(KEY_S);choose("new:prepare");await settle()
   await go(target_node)
   if not abort:await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle()
   if not abort and str(ui.game.battle_data.code)!=code:record_failure("Wrong battle reentered: "+str(ui.game.battle_data.code))
   if not abort:await snapshot(code+"-entry")
  var entry_hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  var b={"entry_map_sha256":entry_hash,"code":code,"source":source_checkpoint,"source_sha256":source_hash,"outcome":"entry_only","failures":[],"key_inputs":0,"final_turn":0}
  if not abort and not late_entry_only:
   var battle_count=battles.size();await battle(false)
   if battles.size()>battle_count:
    b.merge(battles[-1],true);b.quest=ui.game.flags.quest.duplicate(true)
   if not abort:
    await post_battle(ui.game.stage_id)
    b.return_view=ui.view;b.return_node=ui.game.world_node
  if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Source evidence changed: "+code)
  b.failures=failures.slice(failures_before);b.key_inputs=inputs-inputs_before;b.final_turn=ui.game.turn
  b.map_sha256=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text();b.map_revision=ui.game.battle_data.get("tactical_review_version","")
  b.final_view=ui.view;late_records.append(b);write_progress()
  print("LATE_MAP_RESULT ",code," ",b.outcome," ",JSON.stringify(b.failures))
  ui.queue_free();await process_frame;await process_frame;ui=null
 write_progress();quit(0 if late_records.all(func(b):return (b.outcome=="victory" or late_entry_only)and b.failures.is_empty())else 1)

func act(id:String)->void:
 var u=ui.game.find_unit(id);var before=State.pos(u)if not u.is_empty()else Vector2i.ZERO
 await super.act(id)
 if abort:return
 u=ui.game.find_unit(id)
 if not u.is_empty():operations.append({"kind":"route trace","stage":ui.game.battle_data.code,"turn":ui.game.turn,"unit":id,"from":[before.x,before.y],"to":u.position.duplicate()})
 if ui.game.turn in [4,6,8,12]and not checkpoints.any(func(c):return c.name==str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn)):
  await snapshot(str(ui.game.battle_data.code)+"-turn-"+str(ui.game.turn))

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

func prepare_current()->void:
 if ui.game.route=="alm":
  await equip_from_convoy("hunapu",11)
  await equip_from_convoy("hunapu",60)
 else:
  await equip_from_convoy("eileen",16)
  await equip_from_convoy("eileen",60)


var flank=false
var flank_arrived={}
func m41_plan(unit:Dictionary)->Dictionary:
 if State.pos(unit).x>=26 and State.pos(unit).y<=8:flank_arrived[str(unit.id)]=true
 var regular=super.plan(unit)
 var riders=ui.game.living("enemy").filter(func(e):return str(e.id).begins_with("M41_r"))
 var rear=["hunapu","daan","beck"]
 if str(unit.id)in rear and(not ui.game.flags.quest.reinforced or not riders.is_empty()):
  if regular.kind=="heal":return regular
  var goals=[]
  if not riders.is_empty():
   for e in riders:
    for delta in ui.game.DIRECTIONS:goals.append(State.pos(e)+delta)
  else:goals=[{"hunapu":Vector2i(9,6),"daan":Vector2i(10,8),"beck":Vector2i(8,8)}[str(unit.id)]]
  if unit.id=="fula":
   var guard=ui.game.find_unit("german");goals=[State.pos(guard)+Vector2i(0,2)]
  return directed_plan(unit,goals,riders,14.0)
 if flank and str(unit.id)in ["lance","hervi"] and not flank_arrived.has(str(unit.id)) and ui.game.turn<12:
  if regular.kind in ["heal","interact"]:return regular
  var p=State.pos(unit);var goal=Vector2i(20,6)if p.x<20 else Vector2i(26,6)
  return directed_plan(unit,[goal],[],16.0)
 return regular
func directed_plan(unit:Dictionary,goals:Array,targets:Array,pace:float)->Dictionary:
 var origin=State.pos(unit);var graph=ui.game.reachable(unit);var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1};var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell)and Items.can_use(unit,spell):weapons.append(spell)
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell);var walking=pace*(before-int(field.get(cell,99999)))-danger*2.5
  if danger>=int(unit.hp)-2:walking-=180.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    if not targets.is_empty()and not targets.any(func(e):return e.id==enemy.id):continue
    var reply=Rules.default_counter(enemy,distance(cell,State.pos(enemy)));var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell));var count=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var damage=float(stats.damage*count)*stats.hit/100.0;var counter=float(response.damage)*response.hit/100.0 if Rules.can_attack(reply,distance(cell,State.pos(enemy)))else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon):continue
    var score=walking+minf(damage,enemy.hp)*3.0+(65.0 if damage>=int(enemy.hp)*.95 else 0.0)-counter-Items.cost(weapon)
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best

func well_plan(unit: Dictionary) -> Dictionary:
 var origin=State.pos(unit);var key="well_n" if str(unit.id) in ["shia","roan","lisa"] else "well_s";var target=ui.game.battle_data.objects.filter(func(o):return o.id==key)[0].position;var goal=Vector2i(target[0],target[1]);var field=distance_map(unit,[goal]);var graph=ui.game.reachable(unit)
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

func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id==401:return m41_plan(unit)
 if ui.game.stage_id==402 and unit.id=="lance" and not ui.game.flags.quest.old_comrades_talked:
  var friend=ui.game.find_unit("old_comrade")
  if not friend.is_empty()and int(friend.hp)>0:
   var graph=ui.game.reachable(unit)
   for cell in graph.costs:
    if not ui.game.can_stop(unit,cell):continue
    var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
    if ui.game.interactions_for(candidate).any(func(o):return o.id=="lance_parley"):
     return {"kind":"interact","cell":cell,"score":300.0,"target":"lance_parley","spell":-1}
   var goals=[]
   for d in ui.game.DIRECTIONS:goals.append(State.pos(friend)+d)
   return directed_plan(unit,goals,[],14.0)
 if ui.game.stage_id==404 and not ui.game.ChapterFour.boss_down(ui.game):
  var active=ui.game.living("enemy").filter(func(e):return e.get("behavior","")!="guard" or str(e.id) in ["M44_e9","M44_e10"])
  if str(unit.id) in ["lance","daan"] and not active.is_empty():
   var guard_cell=Vector2i(5,8)if unit.id=="lance"else Vector2i(6,8)
   return directed_plan(unit,[guard_cell],[],14.0)
  if active.is_empty() and int(unit.class_id) not in [17,18]:
   var regular=super.plan(unit)
   if regular.kind=="interact":return regular
   var boss=ui.game.find_unit(str(ui.game.battle_data.boss_id));var at=State.pos(boss);var goals=[];var reach=Rules.attack_range(unit)
   for y in range(-reach.y,reach.y+1):
    for x in range(-reach.y,reach.y+1):
     var gap=absi(x)+absi(y)
     if gap>=reach.x and gap<=reach.y:goals.append(at+Vector2i(x,y))
   if int(unit.hp)*3<int(unit.max_hp):
    var graph=ui.game.reachable(unit);var safest={"kind":"wait","cell":State.pos(unit),"score":-1.0e9,"target":"","spell":-1}
    for cell in graph.costs:
     if not ui.game.can_stop(unit,cell):continue
     var score=-risk(unit,cell)*8.0-float(graph.costs[cell])*.1
     if score>safest.score:safest={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
    return safest
   return directed_plan(unit,goals,[],20.0)
 # Preserve a rear guard on the marsh's western pursuit route instead of
 # letting the whole formation chase the summoner ahead of slow civilians.
 if ui.game.stage_id==407 and str(unit.id) in ["shia","roan"]:
  var pursuers=ui.game.living("enemy").filter(func(e):return str(e.id) in ["F43_e4","F43_e8"])
  if not pursuers.is_empty():
   var focus=pursuers[0];var goals=[];var at=State.pos(focus)
   var reach=Rules.attack_range(unit)
   for y in range(-reach.y,reach.y+1):
    for x in range(-reach.y,reach.y+1):
     var gap=absi(x)+absi(y)
     if gap>=reach.x and gap<=reach.y:goals.append(at+Vector2i(x,y))
   return directed_plan(unit,goals,pursuers,15.0)
 if ui.game.stage_id==405 and ui.game.turn<=6 and str(unit.id) in ["lord","shia","roan"] and ui.game.living("enemy").any(func(e):return e.has("well_target")):
  return well_plan(unit)
 var regular=super.plan(unit)
 return safe_leader(unit,regular)
func safe_leader(u:Dictionary,choice:Dictionary)->Dictionary:
 if u.id!="eileen" or ui.game.living("enemy").is_empty():return choice
 var candidate=u.duplicate(true);candidate.position=[choice.cell.x,choice.cell.y]
 var danger=risk(candidate,choice.cell);var counter=0.0
 if choice.kind=="attack":
  if int(choice.spell)>=0:candidate.weapon_index=int(choice.spell)
  var enemy=ui.game.find_unit(choice.target);var gap=distance(choice.cell,State.pos(enemy));var reply=Rules.default_counter(enemy,gap)
  if Rules.can_attack(reply,gap):
   var st=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(choice.cell));counter=float(st.damage)*(2 if st.attack_speed>st.defender_attack_speed else 1)
 if danger*1.2+counter+Items.cost(int(choice.get("spell",-1)))<int(u.hp)-6:return choice
 var front=ui.game.find_unit("lord")
 if front.is_empty()or int(front.hp)<=0:front=ui.game.find_unit("carlo")
 if front.is_empty()or int(front.hp)<=0:return choice
 var graph=ui.game.reachable(u);var best={"kind":"wait","cell":State.pos(u),"score":-1.0e9,"target":"","spell":-1}
 for cell in graph.costs:
  if not ui.game.can_stop(u,cell):continue
  var score=-risk(u,cell)*8.0-abs(distance(cell,State.pos(front))-3)*1.7-float(graph.costs[cell])*.05
  if risk(u,cell)>=int(u.hp)-6:score-=500
  if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return best
func rank(u:Dictionary)->int:
 if u.id==ui.game.leader_id():return 9
 if u.id in ["lord","german"]:return 0
 if u.id in ["roan","daan"]:return 1
 if int(u.class_id) in [17,18]:return 8
 return 3
func treat_normally(member:String)->void:
 if not ui.game.roster.has(member)or not ui.game.is_dying(ui.game.roster[member]):return
 if ui.game.treatment_remaining()<=0:return
 var before=ui.game.treatment_remaining()
 await hub_action("treatment")
 if ui.menu_actions.has("hub:treat_choose_"+member):
  choose("hub:treat_choose_"+member);choose("hub:treat_confirm_"+member);await settle()
  if ui.game.is_dying(ui.game.roster[member])or ui.game.treatment_remaining()!=before-1:record_failure("Normal treatment failed: "+member)
  operations.append({"kind":"ordinary existing treatment resource","member":member,"before":before,"after":ui.game.treatment_remaining()})
 elif not ui.menu_items.is_empty():key(KEY_X)
func run_continuous()->void:
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/chapter3-redesign-20261022/play/continuous-retry/continuous-retry-chapter4-start.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine third-chapter completion failed")
 if not abort:ui._resume_journey();await settle();await snapshot("chapter4-start")
 # Spend genuinely retained sources at the meeting hub through ordinary choices.
 if not abort:
  enter_hub();await settle();await treat_normally("fula");await treat_normally("lena");await leave_hub()
  await switch_team();enter_hub();await settle();await treat_normally("mireille");await leave_hub()
  await snapshot("after-ordinary-treatment")
 for code in ["M41","S41","M42","M43","F41","F42","F43","S42","M44","F44"]:
  if abort:break
  var stage={"M41":401,"M42":402,"M43":403,"M44":404,"F41":405,"F42":406,"F43":407,"F44":408,"S41":411,"S42":412}[code]
  path_cache.clear();risk_cache.clear()
  if ui.game.route!=ui.game.stages[stage].route:await switch_team()
  if stage==404 and not ui.game.flags.get("west_tower_safe",false):
   await go(12);enter_hub();await settle();await hub_action("fourth_tower_shutdown");await leave_hub()
  if not abort:await go(int(ui.game.stages[stage].node));await prepare_current()
  if abort:break
  var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  var count=battles.size();await battle(false)
  var b={"code":code,"source":source_checkpoint,"source_sha256":source_hash,"scope":"Continuous from genuine chapter-three completion, normal treatment, route switching, recruitment and equipment; all growth and casualties carried forward","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
  if battles.size()>count:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(prior_failures);b.final_turn=ui.game.turn;b.return_view=ui.view;b.route=ui.game.route
  late_records.append(b);write_progress();print("CH4_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))
  if OS.get_cmdline_user_args().has("--opening-only"):
   ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1);return
 if not abort:
  await go(9);enter_hub();await settle();await hub_action("third_council");await hub_action("third_messenger");choose("hub:fourth_finish");await settle();await snapshot("chapter-end")
  if not ui.game.flags.get("chapter4_closed",false):record_failure("Fourth chapter did not complete")
  if not abort:
   key(KEY_Z);choose("new:chapter5");await settle()
   if ui.game.chapter!=5:record_failure("Fifth chapter did not open")
   else:await snapshot("chapter5-start")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original chapter start changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
