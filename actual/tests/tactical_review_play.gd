extends "res://tests/chapter2_play.gd"
## Two review rounds use isolated copies of genuine deployment checkpoints.
## All battle moves, menus, attacks, retries and object actions use normal input.
var review_round=1
var review_codes: PackedStringArray=[]
var review_out="res://reports/review-0.2.1/"
var review_battles: Array=[]
var review_label=""
func _initialize() -> void:call_deferred("run")
func snapshot(name: String) -> void:
 var old=ui.game.save_path;var path=review_out+review_label+"-"+name+".json"
 ui.game.save_path=path;ui.game.save_game();ui.game.save_path=old
 checkpoints.append({"name":name,"save":path,"view":ui.view,"stage":ui.game.stage_id,"turn":ui.game.turn})
func plan(unit: Dictionary) -> Dictionary:
 if ui.game.stage_id==105 and str(unit.id) in ["hunapu","lance","daan","beck"] and int(ui.game.find_unit("M15_boss").hp)>0:return tower_plan(unit)
 if ui.game.chapter==2 and ui.game.stage_id!=201:return super.plan(unit)
 var best=combat_plan(unit);var graph=ui.game.reachable(unit)
 var important="M15_boss" if ui.game.stage_id==105 else ""
 if ui.game.stage_id==102:
  for enemy in ui.game.living("enemy"):
   if enemy.get("burner",false):important=str(enemy.id)
 var focus=ui.game.find_unit(important)
 if ui.game.stage_id in [101,111,112]:
  var nearest=99999
  for enemy in ui.game.living("enemy"):
   for npc in ui.game.living("player"):
    if npc.get("quest_kind","") not in ["escort","medicine"]:continue
    var d=distance(State.pos(enemy),State.pos(npc))
    if d<nearest:nearest=d;focus=enemy;important=str(enemy.id)
 var race_field={}
 if not focus.is_empty():
  var goals=[]
  for d in ui.game.DIRECTIONS:goals.append(State.pos(focus)+d)
  race_field=distance_map(unit,goals)
 for cell in graph.costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  for object in ui.game.interactions_for(candidate):
   if ui.game.stage_id==105 and not focus.is_empty() and int(focus.hp)>0 and str(unit.id) in ["hunapu","lance","daan","beck"]:continue
   var score=250.0-risk(candidate,cell)
   if score>best.score:best={"kind":"interact","cell":cell,"score":score,"target":str(object.id),"spell":-1}
  if focus.is_empty() or int(focus.hp)<=0:
   var goals=[]
   for object in ui.game.battle_data.objects:
    if ui.game.flags.quest.objects.get(str(object.id),false):continue
    var at=Vector2i(object.position[0],object.position[1])
    if not object.get("adjacent",true):goals.append(at)
    else:
     for d in ui.game.DIRECTIONS:goals.append(at+d)
   if not goals.is_empty():
    var field=distance_map(unit,goals)
    var walking=10.0*(int(field.get(State.pos(unit),99999))-int(field.get(cell,99999)))-risk(candidate,cell)
    if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
   continue
  var walking=12.0*(int(race_field.get(State.pos(unit),99999))-int(race_field.get(cell,99999)))-risk(candidate,cell)
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  var weapons: Array=[-1]
  for spell in Items.spells(unit):
   if not Items.is_support(spell) and Items.can_use(unit,spell):weapons.append(spell)
  for weapon in weapons:
   candidate.erase("weapon_index")
   if weapon>=0:candidate.weapon_index=weapon
   if not ui.game.targets(candidate).has(focus):continue
   var stats=Rules.attack_stats(candidate,focus,ui.game.terrain_avoid(State.pos(focus)))
   var score=120.0+float(stats.damage)*2-risk(candidate,cell)
   if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":important,"spell":weapon}
 return best
func tower_plan(unit: Dictionary) -> Dictionary:
 var origin=State.pos(unit);var boss=ui.game.find_unit("M15_boss");var rider=str(unit.id)=="lance"
 var goal=Vector2i(14,16) if origin.y>16 else Vector2i(28,3) if rider else State.pos(boss)
 var goals: Array=[goal]
 if not rider and origin.y<=16:
  goals=[]
  for d in ui.game.DIRECTIONS:goals.append(State.pos(boss)+d)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999));var best={"kind":"wait","cell":origin,"score":-risk(unit,origin),"target":"","spell":-1}
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(unit,cell);var walking=25.0*(before-int(field.get(cell,99999)))-danger*1.2
  if danger>=int(unit.hp)-2:walking-=100.0
  if rider and cell==Vector2i(28,3):walking+=300.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for enemy in ui.game.targets(candidate):
   var stats=Rules.attack_stats(candidate,enemy,ui.game.terrain_avoid(State.pos(enemy)));var score=walking+minf(stats.damage,enemy.hp)*2.0+(120.0 if enemy.id=="M15_boss" and not rider else 0.0)
   if rider and cell!=Vector2i(28,3):score-=35.0
   if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":-1}
 return best
func run() -> void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--round="):review_round=int(arg.split("=")[1])
  if arg.begins_with("--codes="):review_codes=arg.split("=")[1].split(",")
  if arg.begins_with("--label="):review_label=arg.split("=")[1]
 if review_label.is_empty():review_label="round"+str(review_round)
 if review_codes.is_empty():review_codes=["M13","S12","F21","F24"] if review_round==1 else ["M12","M15","F25","F26"]
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
 ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
 for code in review_codes:
  abort=false;var failures_before=failures.size();var inputs_before=inputs;var ops_before=operations.size()
  var source=("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
  ui.game.save_path=source
  if not ui.game.load_game():record_failure("Actual deployment does not load: "+code);continue
  ui.game.save_path=review_out+"working-save.json";ui.view=ui.game.mode;ui.busy=false;ui.batch_running=false;ui._clear_menu();ui.ui_mode="inspect";ui.held_direction=Vector2i.ZERO;ui.phase_time=0
  ui._focus_battle(ui.game.cursor,true)
  # Real return-to-preparation and re-entry picks up updated maps/NPCs.
  var target_node=ui.game.world_node
  key(KEY_S);choose("new:prepare");await settle()
  await go(target_node)
  if code=="M15":
   await equip_from_convoy("hunapu",11)
   await equip_from_convoy("otto",2)
  key(KEY_Z);choose("new:battle");await settle()
  await snapshot(code+"-entry")
  var record={"code":code,"source":source,"initial_roster":ui.game.roster.duplicate(true),"turns":[],"tactical_actions":[],"scope":"Actual keyboard re-entry from genuine campaign checkpoint; no HP/stat/RNG/position edits"}
  key(KEY_S);choose("new:goal");await settle()
  for step in range(65):
   if abort or not ui.game.battle_outcome.is_empty():break
   var turn_=ui.game.turn;var members=ui.game.party.duplicate()
   if ui.game.chapter==2:members.sort_custom(func(a,b):return rank(ui.game.roster[a])<rank(ui.game.roster[b]))
   for id in members:
    if abort or ui.game.turn!=turn_ or not ui.game.battle_outcome.is_empty():break
    var unit=ui.game.find_unit(str(id))
    if unit.is_empty() or int(unit.hp)<=0 or unit.acted:continue
    var start=State.pos(unit);var before_ops=operations.size();await act(str(id))
    var at=State.pos(unit)
    record.tactical_actions.append({"turn":turn_,"unit":id,"from":[start.x,start.y],"to":[at.x,at.y],"terrain":ui.game.category(at),"avoid":ui.game.terrain_avoid(at),"operations":operations.slice(before_ops)})
   if not abort and ui.game.battle_outcome.is_empty() and ui.game.turn==turn_:
    key(KEY_S);choose("end_turn");await settle()
   record.turns.append({"turn":ui.game.turn,"enemies":ui.game.living("enemy").size(),"outcome":ui.game.battle_outcome})
   print("REVIEW ",review_round," ",code," turn ",ui.game.turn," E ",ui.game.living("enemy").size()," ",ui.game.battle_outcome)
   if step==2:await snapshot(code+"-field")
   if code=="F26" and step==5:await snapshot(code+"-boats")
  record.outcome=ui.game.battle_outcome;record.final_turn=ui.game.turn;record.key_inputs=inputs-inputs_before
  record.failures=failures.slice(failures_before);record.final_roster=ui.game.roster.duplicate(true);record.quest=ui.game.flags.quest.duplicate(true)
  if not abort:await snapshot(code+"-"+("victory" if record.outcome=="victory" else "stopped"))
  review_battles.append(record);write_review()
  ui.busy=false;ui.batch_running=false;ui._clear_menu()
 write_review();ui.queue_free();await process_frame;ui=null
 quit(0 if review_battles.all(func(b):return b.outcome=="victory") else 1)
func write_review() -> void:
 var path=review_out+review_label+"-play.json"
 var f=FileAccess.open(path,FileAccess.WRITE)
 f.store_string(JSON.stringify({"round":review_round,"passed":not review_battles.is_empty() and review_battles.all(func(b):return b.outcome=="victory"),"battles":review_battles,"inputs":inputs,"failures":failures,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false},"  "));f.close()
