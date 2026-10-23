extends "res://tests/ch2_environment_ships.gd"
# Resume the exact live F22 T91 stalemate through ordinary actions.
# Guarded melee enemies are approached at actual spell range, never by editing state.
const LIVE_SOURCE="res://reports/chapter2-environment-20261023/play/continuous-final/working-journey.json"
const PRIOR="res://reports/chapter2-environment-20261023/play/continuous-final/continuous-final-play.json"
var live_hash=""
var continuation_source=LIVE_SOURCE
var predecessor_report=PRIOR
var retry_shore=false
var after_shore=false
var after_lighthouse=false
func plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id==203:return conservative_shore_plan(unit)
 if ui.game.stage_id==205:return harbor_plan(unit)
 if ui.game.stage_id!=202 or ui.game.living("enemy").is_empty():return super.plan(unit)
 if ui.game.living("enemy").any(func(e):return e.get("behavior","")!="guard"):return super.plan(unit)
 var enemies=ui.game.living("enemy");var origin=State.pos(unit);var ranged=Items.spells(unit).any(func(s):return not Items.is_support(s) and Items.can_use(unit,s))
 var goals:Array=[]
 if ranged:
  for enemy in enemies:
   for y in range(-2,3):
    for x in range(-2,3):
     if absi(x)+absi(y)==2:goals.append(State.pos(enemy)+Vector2i(x,y))
 else:
  goals=[Vector2i(18,14),Vector2i(18,15)]
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  if danger>=int(unit.hp)-1:continue
  var walking=8.0*(before-int(field.get(cell,99999)))-danger*4.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for spell in Items.spells(unit):
   if Items.is_support(spell) or not Items.can_use(unit,spell):continue
   candidate.weapon_index=spell
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    if Rules.can_attack(reply,dist):continue
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var score=120.0+minf(stats.damage,enemy.hp)*5.0-danger*5.0-Items.cost(spell)
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":spell}
 return best

func run()->void:
 late_label="continuous-resumed"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):late_label=arg.trim_prefix("--label=")
 retry_shore=OS.get_cmdline_user_args().has("--retry-f23")
 if retry_shore:
  continuation_source="res://reports/chapter2-environment-20261023/play/continuous-resumed/continuous-resumed-F23-entry.json"
  predecessor_report="res://reports/chapter2-environment-20261023/play/continuous-resumed/continuous-resumed-play.json"
 after_shore=OS.get_cmdline_user_args().has("--after-shore")
 if after_shore:
  continuation_source="res://reports/chapter2-environment-20261023/play/continuous-shore-retry/working-journey.json"
  predecessor_report="res://reports/chapter2-environment-20261023/play/continuous-shore-retry/continuous-shore-retry-play.json"
 after_lighthouse=OS.get_cmdline_user_args().has("--after-lighthouse")
 if after_lighthouse:
  after_shore=true
  continuation_source="res://reports/chapter2-environment-20261023/play/continuous-after-shore/working-journey.json"
  predecessor_report="res://reports/chapter2-environment-20261023/play/continuous-after-shore/continuous-after-shore-play.json"
 late_folder=LATE_OUT+late_label+"/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
 source_checkpoint=continuation_source;live_hash=FileAccess.get_file_as_string(continuation_source).sha256_text();var prior=State.read_json(predecessor_report)
 var working=late_folder+"working-journey.json";DirAccess.copy_absolute(ProjectSettings.globalize_path(continuation_source),ProjectSettings.globalize_path(working))
 ui=load("res://scenes/main.tscn").instantiate();ui.game.save_path=working;root.add_child(ui);await process_frame;ui.instant_mode=true
 if not ui.game.load_game():record_failure("Exact F22 live source failed")
 if not abort and not retry_shore and not after_shore and (ui.game.stage_id!=202 or ui.game.turn!=91 or ui.game.battle_outcome!=""):record_failure("Source is not exact F22 T91 live battle")
 var west={}
 for id in ui.game.parties.alm:west[id]=ui.game.roster[id].duplicate(true)
 if not abort:
  ui._resume_journey();await settle()
  if after_lighthouse:
   await snapshot("F24-hub-optional-branch")
   await leave_hub()
  if retry_shore:
   key(KEY_S);choose("new:prepare");await settle();await go(20);await prepare_current()
   if not abort:key(KEY_Z);choose("new:battle");await settle();await snapshot("F23-entry")
  else:await snapshot("after-F23-world"if after_shore else"F22-resume-T91")
 var order=["F23","S21","S22","F24","F25","F26"]if retry_shore else["F22","F23","S21","S22","F24","F25","F26"]
 if after_shore:order=["S21","S22","F24","F25","F26"]
 if after_lighthouse:order=["F25","F26"]
 for code in order:
  if abort:break
  var stage={"F22":202,"F23":203,"F24":204,"F25":205,"F26":206,"S21":211,"S22":212}[code]
  path_cache.clear();risk_cache.clear()
  if code!=order[0] or after_shore:
   await go(int(ui.game.stages[stage].node));await prepare_current()
   if abort:break
   key(KEY_Z);choose("new:battle");await settle();await snapshot(code+"-entry")
  var before=inputs;var failures_before=failures.size();var starting=ui.game.turn;var hash=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
  var n=battles.size();await battle(false)
  var b={"code":code,"source":continuation_source,"source_sha256":live_hash,"starting_turn":starting,"entry_map_sha256":hash,"map_sha256":hash,"outcome":"incomplete","scope":"F23 ordinary preparation retry after retained defeat; all growth and injuries preserved" if retry_shore else "Exact post-battle world/hub continuation, no additional retry" if after_shore else "Exact F22 T91 live continuation, no battle retry"}
  if battles.size()>n:b.merge(battles[-1],true)
  b.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await post_battle(stage)
  b.key_inputs=inputs-before;b.failures=failures.slice(failures_before);b.return_view=ui.view;b.final_turn=ui.game.turn;b.chapter_complete=ui.game.flags.get("chapter2_complete",false)
  late_records.append(b);write_progress();print("ENV_CONTINUATION ",code," ",b.outcome," ",JSON.stringify(b.failures))
 if not abort:
  if not ui.game.flags.get("chapter2_complete",false):record_failure("Chapter two did not complete")
  for id in west:
   if JSON.parse_string(JSON.stringify(west[id]))!=JSON.parse_string(JSON.stringify(ui.game.roster[id])):record_failure("Persisted west roster changed: "+id)
  if not abort:
   key(KEY_Z);choose("new:chapter3");await settle()
   if ui.game.chapter!=3:record_failure("Chapter three did not open")
   else:await snapshot("chapter3-start")
 if FileAccess.get_file_as_string(continuation_source).sha256_text()!=live_hash:record_failure("Live source changed")
 write_progress()
 var chain={"passed":not abort,"predecessor_report":predecessor_report,"predecessor_sha256":FileAccess.get_file_as_string(predecessor_report).sha256_text(),"inherited_victories":prior.battles.filter(func(b):return b.outcome=="victory"),"retained_stall":prior.battles.filter(func(b):return b.code=="F22"),"resumed_battles":late_records,"source":continuation_source,"source_sha256":live_hash,"source_unchanged":FileAccess.get_file_as_string(continuation_source).sha256_text()==live_hash,"chapter":ui.game.chapter,"chapter2_complete":ui.game.flags.get("chapter2_complete",false),"inputs":inputs,"checkpoints":checkpoints,"failures":failures,"no_state_rng_or_outcome_edits":true,"battle_retries":1 if retry_shore else 0}
 var f=FileAccess.open(late_folder+"continuous-chain.json",FileAccess.WRITE);f.store_string(JSON.stringify(chain,"  "));f.close()
 ui.queue_free();await process_frame;ui=null;quit(1 if abort else 0)

func harbor_plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=205:return super.plan(unit)
 var origin=State.pos(unit);var graph=ui.game.reachable(unit)
 var best=combat_plan(unit)
 if best.kind=="heal":return best
 if best.kind=="attack":
  var target=ui.game.find_unit(str(best.target));var candidate=unit.duplicate(true);candidate.position=[best.cell.x,best.cell.y]
  if int(best.spell)>=0:candidate.weapon_index=int(best.spell)
  var reply=Rules.default_counter(target,distance(best.cell,State.pos(target)))
  var attack=Rules.attack_stats(candidate,target,ui.game.terrain_avoid(State.pos(target)))
  var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(best.cell))
  if int(unit.hp)>Items.cost(int(best.spell))+int(response.damage) or int(attack.damage)>=int(target.hp):return best
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  for object in ui.game.interactions_for(candidate):
   if object.get("optional",false):continue
   if risk(candidate,cell)>=int(unit.hp)-3:continue
   return {"kind":"interact","cell":cell,"score":250.0,"target":str(object.id),"spell":-1}
 var front=ui.game.find_unit("lord")
 if front.is_empty() or int(front.hp)<=0:front=ui.game.find_unit("eileen")
 var healer=int(unit.class_id) in [17,18]
 var goals:Array=[]
 if healer and not front.is_empty():
  for d in ui.game.DIRECTIONS:goals.append(State.pos(front)+d)
 else:
  var boss=ui.game.find_unit(str(ui.game.battle_data.boss_id))
  if not boss.is_empty() and int(boss.hp)>0:
   for d in ui.game.DIRECTIONS:goals.append(State.pos(boss)+d)
  else:
   for object in ui.game.battle_data.objects:
    if object.get("optional",false) or ui.game.flags.quest.objects.get(str(object.id),false):continue
    var p=Vector2i(object.position[0],object.position[1])
    if not object.get("adjacent",true):goals.append(p)
    else:
     for d in ui.game.DIRECTIONS:goals.append(p+d)
 if goals.is_empty():return super.plan(unit)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999))
 best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell) or not field.has(cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  var score=10.0*(before-int(field[cell]))-danger*(3.0 if healer else 2.0)
  if danger>=int(unit.hp)-3:score-=300.0
  # Support catches up with the advancing guard. A wounded rear unit never
  # supplies a global tether that can freeze the healthy assault group.
  if not healer and str(unit.id)!="lord" and not front.is_empty():score-=maxi(0,distance(cell,State.pos(front))-5)*1.5
  if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
 return best


func conservative_shore_plan(unit:Dictionary)->Dictionary:
 if ui.game.stage_id!=203 or ui.game.living("enemy").is_empty():return super.plan(unit)
 var hold=ui.game.turn<=4
 for e in ui.game.living("enemy"):
  if e.get("behavior","")!="guard" and State.pos(e).y>=13:hold=true
 if not hold:return super.plan(unit)
 var origin=State.pos(unit);var id=str(unit.id)
 var front=id in ["lord","carlo"]
 var goals={"lord":Vector2i(12,18),"carlo":Vector2i(14,18),"lisa":Vector2i(12,21),"mireille":Vector2i(11,22),"eileen":Vector2i(10,22)}
 var goal:Vector2i=goals.get(id,Vector2i(12,19))
 var best={"kind":"wait","cell":origin,"score":-1.0e9,"target":"","spell":-1}
 var weapons:Array=[-1]
 for spell in Items.spells(unit):
  if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  if cell.x<10 or cell.x>17 or cell.y<16 or cell.y>22:continue
  if id=="eileen" and cell.y<21:continue
  # A defensive choice is a real movement limit, including attack moves.
  # The general driver's eager attack preview otherwise bypasses formation.
  if ui.game.turn<=3 and (cell.x>15 or cell.y<18):continue
  if ui.game.turn<=3 and not front and (cell.x>14 or cell.y<19):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(candidate,cell)
  var formation=-float(distance(cell,goal))*5.0
  if not front:formation-=float(maxi(0,18-cell.y)+maxi(0,cell.x-14))*12.0
  var walking=formation-danger*(1.2 if front else 2.3)
  if danger>=int(unit.hp)-3:walking-=250.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for spell in Items.spells(unit):
   if spell not in [40,41] or not Items.can_use(unit,spell):continue
   candidate.erase("weapon_index")
   for ally in ui.game.support_targets(candidate,spell):
    var missing=int(ally.max_hp)-int(ally.hp)
    if missing<4:continue
    var urgency=45.0 if int(ally.hp)<int(ally.max_hp)*.5 else 0.0
    var score=mini(missing,int(unit.strength))*5.0+urgency+formation*.35-danger*2.0-Items.cost(spell)*2.0
    if danger>=int(unit.hp)-Items.cost(spell)-2:score-=250.0
    if score>best.score:best={"kind":"heal","cell":cell,"score":score,"target":str(ally.id),"spell":spell}
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   for enemy in ui.game.targets(candidate):
    var dist=distance(cell,State.pos(enemy));var reply=Rules.default_counter(enemy,dist)
    var stats=Rules.attack_stats(candidate,reply,ui.game.terrain_avoid(State.pos(enemy)))
    var strikes=2 if stats.attack_speed>stats.defender_attack_speed else 1
    var expected=float(stats.damage*strikes)*stats.hit/100.0
    var kill=expected>=int(enemy.hp)*.95
    var response=Rules.attack_stats(reply,candidate,ui.game.terrain_avoid(cell))
    var counter=float(response.damage)*response.hit/100.0*(2 if response.attack_speed>response.defender_attack_speed else 1) if Rules.can_attack(reply,dist) else 0.0
    if counter>=int(unit.hp)-Items.cost(weapon)-1:continue
    var after=risk(candidate,cell,str(enemy.id) if kill else "")
    var urgency=maxf(0.0,30.0-distance(State.pos(enemy),Vector2i(12,19))*3.0)
    # Flyers can cross the line and reach the cleric. Finish those attackers
    # before an equally exposed foot raider when both are available.
    if int(enemy.class_id)==3 and State.pos(enemy).y>=14:urgency+=35.0
    var score=minf(expected,enemy.hp)*3.0+(55.0 if kill else 0.0)+urgency+formation*.5-counter-after*(1.0 if front else 1.8)-Items.cost(weapon)
    if after+counter>=int(unit.hp)-Items.cost(weapon)-2:score-=250.0
    if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":weapon}
 return best

func equip_from_convoy(id:String,item:int)->void:
 var member=ui.game.roster.get(id,{})
 if member.is_empty() or not ui.game.can_deploy(member):
  operations.append({"kind":"ordinary equipment omitted for unavailable member","unit":id,"item":item});return
 await super.equip_from_convoy(id,item)

func hub_action(action:String)->void:
 if action=="r05" and not ui.hub_controller.objects.any(func(o):return str(o.action)==action):
  operations.append({"kind":"conditional optional conversation absent as expected","action":action,"room":ui.game.hub_record,"carlo_dying":ui.game.roster.get("carlo",{}).get("dying",false)});return
 await super.hub_action(action)
