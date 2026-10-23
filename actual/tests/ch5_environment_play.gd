extends "res://tests/chapter5_play.gd"
# Final-chapter isolated real-input review; no live attributes or outcomes edited.

const LATE_OUT="res://reports/chapter5-environment-20261023/play/"
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
 f.store_string(JSON.stringify({"passed":failures.is_empty() and not late_records.is_empty() and late_records.all(func(b):return b.outcome=="victory" and b.failures.is_empty()),"entry_only":late_entry_only,"failures":failures,"total_inputs":inputs,"battles":late_records,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"source_saves_modified":false,"operations":operations,"route_trace":operations.filter(func(a):return a.get("kind","")=="route trace"),"scope":"Independent genuine deployment checkpoints, ordinary return-to-preparation and current-map reentry, actual input battles and post-battle hub actions; no live attributes, RNG, positions or win conditions edited."},"  "));f.close()
func run()->void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
  if arg.begins_with("--codes="):late_codes=arg.trim_prefix("--codes=").split(",")
  if arg=="--entry-only":late_entry_only=true
 if OS.get_cmdline_user_args().has("--continuous"):
  await run_continuous();return
 if late_codes.is_empty():late_codes=["M51", "M52", "F51", "F52", "S51", "J53", "J54"]
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 var sources=State.read_json("res://reports/chapter5-environment-20261023/sources.json")
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
   if not abort and ui.game.stage_id!=534:
    await post_battle(ui.game.stage_id)
    b.return_view=ui.view;b.return_node=ui.game.world_node
   elif not abort:
    await finish_ending();b.ending_done=ui.game.flags.get("ending_done",false)
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
 if member.is_empty() or not ui.game.can_deploy(member) or int(member.get("item_id",0))!=0:return
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
  await equip_from_convoy("mireille",49)
  await equip_from_convoy("carlo",11)
  await equip_from_convoy("shia",5)


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
func rank(u:Dictionary)->int:
 if u.id in ["hunapu","eileen"]:return 9
 if u.id in ["lord","german"]:return 0
 if u.id in ["roan","daan"]:return 1
 if int(u.class_id) in [17,18]:return 8
 return 3
func finish_ending()->void:
 if ui.view!="ending":record_failure("Final victory did not enter ending");return
 await snapshot("ending-first")
 for page in range(160):
  if abort or ui.game.flags.get("ending_done",false):break
  key(KEY_Z);await settle()
 if not abort and not ui.game.flags.get("ending_done",false):record_failure("Ending did not complete")
 if not abort:await snapshot("ending-complete")
func run_continuous()->void:
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint="res://reports/chapter4-environment-20261023/play/chapter-transition/chapter-transition-chapter5-start.json"
 var source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text();var working=late_folder+"working-journey.json"
 DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Genuine fourth-chapter completion failed")
 if not abort:ui._resume_journey();await settle();await snapshot("chapter5-start")
 for code in ["M51","M52","F51","F52","S51"]:
  if abort:break
  var stage={"M51":501,"M52":502,"F51":503,"F52":504,"S51":511}[code]
  if ui.game.route!=ui.game.stages[stage].route:await switch_team()
  if not abort:await go(int(ui.game.stages[stage].node));await prepare_current()
  if not abort:await continuous_battle(code)
 if not abort:
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
  var stage=533 if code=="J53"else 534
  await go(int(ui.game.stages[stage].node));await prepare_current()
  if not abort:await continuous_battle(code)
 if not abort:
  if not ui.game.flags.get("campaign_complete",false)or not ui.game.flags.get("ending_done",false):record_failure("Final campaign or ending incomplete")
 if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Original fifth-chapter source changed")
 write_progress();ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)
func continuous_battle(code:String)->void:
 path_cache.clear();risk_cache.clear();var before=inputs;var prior_failures=failures.size();var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
 key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
 var count=battles.size();await battle(false)
 var b={"code":code,"source":source_checkpoint,"source_sha256":FileAccess.get_file_as_string(source_checkpoint).sha256_text(),"scope":"Continuous from genuine chapter-four completion with original casualties and normal equipment, treatment and joint-deployment menus","entry_map_sha256":hash,"map_sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"outcome":"incomplete"}
 if battles.size()>count:b.merge(battles[-1],true)
 b.quest=ui.game.flags.quest.duplicate(true)
 if not abort:
  if ui.game.stage_id!=534:await post_battle(ui.game.stage_id)
  else:await finish_ending();b.ending_done=ui.game.flags.get("ending_done",false)
 b.key_inputs=inputs-before;b.failures=failures.slice(prior_failures);b.final_turn=ui.game.turn;b.return_view=ui.view;b.route=ui.game.route
 late_records.append(b);write_progress();print("CH5_CONTINUOUS ",code," ",b.outcome," ",JSON.stringify(b.failures))

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


# The repair courts are separated by a long canal. Keeping every unit within
# four Manhattan tiles of the healer stalls both ends of a real bridge.
# March by the actual walkable path; attacks and interactions remain normal input.
func plan(unit:Dictionary)->Dictionary:
 var regular=super.plan(unit)
 if ui.game.stage_id==511 and regular.kind!="attack" and regular.kind!="heal":
  var key="archive_exit" if ui.game.flags.quest.objects.get("old_record",false) else "old_record"
  if regular.kind=="interact" and regular.target==key:return regular
  var object=ui.game.battle_data.objects.filter(func(o):return o.id==key)[0]
  var point=object.get("approach",object.position)
  return directed_plan(unit,[Vector2i(point[0],point[1])],[],8.0)
 if ui.game.stage_id!=503 or ui.game.turn<8 or regular.kind!="wait":return regular
 var goals=[]
 if int(unit.class_id) in [17,18]:
  var lead=ui.game.find_unit("lord")
  if not lead.is_empty() and lead.hp>0:
   for delta in ui.game.DIRECTIONS:goals.append(State.pos(lead)+delta)
 else:
  for enemy in ui.game.living("enemy"):
   for delta in ui.game.DIRECTIONS:goals.append(State.pos(enemy)+delta)
 if goals.is_empty():return regular
 return directed_plan(unit,goals,[],7.0)
