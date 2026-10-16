extends SceneTree
const State=preload("res://core/game_state.gd")
var checks=0
var errors: Array=[]
func check(ok: bool,message: String) -> void:
 checks+=1
 if not ok:errors.append(message);push_error(message)
func _initialize() -> void:
 var g=State.new()
 for code in ["M11","M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","F26","S21","S22"]:
  var prefix="res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/"
  g.save_path=prefix+"natural-"+code+"-deployment-save.json"
  check(g.load_game(),code+" old opening loads")
  check(str(g.battle_data.get("tactical_review_version","0.2.0"))!="0.3.0",code+" old active geometry retained")
  var before=g.battle_start_snapshot.roster.duplicate(true)
  check(g.retry_battle(),code+" ordinary retry adopts new entry")
  check(str(g.battle_data.tactical_review_version)==str(g.stages[g.stage_id].tactical_review_version),code+" new geometry active")
  check(g.roster==before,code+" retry preserves actual pre-battle growth and casualties")
  for unit in g.units:
   check(g.movement_cost(unit,g.pos(unit))<255,code+" legal fresh position "+str(unit.id))
   if unit.side=="player" and not unit.get("neutral",false):
    check(unit.position==g.battle_data.player_positions[int(unit.player_slot)],code+" current deployment "+str(unit.id))
  var roster=g.roster.duplicate(true);var units=g.units.duplicate(true)
  g.save_path="res://reports/battlefield-0.3.0/state-working-save.json"
  check(g.save_game() and g.load_game(),code+" new save round trip")
  check(g.units==JSON.parse_string(JSON.stringify(units)) and g.roster==JSON.parse_string(JSON.stringify(roster)),code+" round trip does not move or change members")
  check(str(g.battle_data.tactical_review_version)==str(g.stages[g.stage_id].tactical_review_version),code+" reload uses correct revision")
 # Explicit 0.2.1 active field: older saved positions remain usable until retry.
 g.save_path="res://reports/review-0.2.1/round2-tower-M15-field.json"
 check(g.load_game(),"0.2.1 field loads")
 check(g.battle_data.map.width==32,"0.2.1 field retains old dimensions")
 check(g.return_to_preparation(),"old field returns through normal preparation")
 check(g.battle_data.map.width==44 and g.mode=="world","preparation moved to redesigned field safely")
 # Directed interaction fixtures test the rules independently of full playthroughs.
 for code in ["M11","M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","S21","S22"]:
  var prefix="res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/"
  g.save_path=prefix+"natural-"+code+"-deployment-save.json";check(g.load_game(),code+" visit source loads")
  check(g.retry_battle(),code+" visit fixture new map")
  var object=g.battle_data.objects.filter(func(o):return o.kind=="visit")[0]
  var actor=g.find_unit(g.leader_id());actor.acted=false
  actor.position=[object.position[0]-1,object.position[1]]
  check(not g.interactions_for(actor).any(func(o):return o.id==object.id),code+" side wall cannot visit")
  actor.position=[object.position[0],object.position[1]-1]
  check(not g.interactions_for(actor).any(func(o):return o.id==object.id),code+" rear cannot visit")
  for front in g.visit_fronts(object):
   actor.position=[front.x,front.y]
   check(g.interactions_for(actor).any(func(o):return o.id==object.id),code+" each native entrance front offers visit")
  actor.position=object.approach.duplicate();g.selected_id=actor.id
  check(g.interactions_for(actor).any(func(o):return o.id==object.id),code+" marked front offers visit")
  check(g.interact(object.id),code+" front visit works")
  check(actor.acted and g.flags.quest.objects.get(object.id,false),code+" visit consumes action and persists")
  var inventory=JSON.stringify([g.roster,g.convoy]);actor.acted=false;g.selected_id=actor.id
  check(not g.interact(object.id),code+" repeated visit rejected")
  check(inventory==JSON.stringify([g.roster,g.convoy]),code+" no duplicate reward")
  g.save_path="res://reports/battlefield-0.3.0/state-working-save.json";check(g.save_game() and g.load_game(),code+" visited state reload")
  check(g.flags.quest.objects.get(object.id,false),code+" visited flag survives reload")
  for site in g.battle_data.get("building_sites",[]):
   var cell=Vector2i(site.position[0],site.position[1])
   check(g.movement_cost(g.find_unit(g.leader_id()),cell)<255,code+" building is occupiable")
   check(g.terrain_avoid(cell)==int(site.avoid),code+" building advantage matches UI")
   if int(site.phase_heal)>0:
    for side in ["player","enemy"]:
     var probe={"hp":10,"max_hp":20,"class_id":8,"item_id":0,"side":side}
     check(g.Items.phase_effect(probe,218,15).hp_after==15,code+" occupation heals either side equally")
 # The lighthouse shelter uses a complete one-cell house and retains rescue.
 g.save_path="res://reports/chapter2/play/natural-F24-deployment-save.json";g.load_game();g.retry_battle()
 var shelter=g.battle_data.objects.filter(func(o):return o.id=="shelter")[0]
 var visitor=g.find_unit(g.leader_id());visitor.acted=false
 visitor.position=[shelter.position[0]-1,shelter.position[1]]
 check(not g.interactions_for(visitor).any(func(o):return o.id=="shelter"),"shelter side wall cannot trigger rescue")
 for front in g.visit_fronts(shelter):
  visitor.position=[front.x,front.y]
  check(g.interactions_for(visitor).any(func(o):return o.id=="shelter"),"shelter own square/front remains interactable")
 g.selected_id=visitor.id;check(g.interact("shelter") and g.flags.quest.shelter_open,"native shelter keeps rescue effect")
 # Optional visits cannot fulfill main occupation/rescue requirements.
 g.save_path="res://reports/campaign/natural-M13-deployment-save.json";g.load_game();g.retry_battle()
 g.find_unit(g.battle_data.boss_id).hp=0
 g.flags.quest.objects={"M13_visit_0":true};g.units.filter(func(u):return str(u.id).begins_with("M13_workers"))[0].locked=false
 check(g.check_outcome()!="victory","optional visit cannot bypass two prison doors")
 for code in ["M12","M14"]:
  g.save_path="res://reports/campaign/natural-"+code+"-deployment-save.json";g.load_game();g.retry_battle()
  g.find_unit(g.battle_data.boss_id).hp=0
  for object_ in g.battle_data.objects:
   if not object_.get("optional",false):g.flags.quest.objects[object_.id]=true
  check(g.check_outcome()=="victory",code+" optional visit never required for victory")
 # A mid-battle 0.3.0 save must not move an actor into the restored river.
 g.save_path="res://reports/battlefield-0.3.0/play/acceptance1-west/acceptance1-west-M11-field.json"
 check(g.load_game(),"0.3.0 snow field loads safely")
 check(g.battle_data.map.tiles==g.read_json("res://data/compat/0.3.0/M11.json").map.tiles,"0.3.0 field keeps its original river geometry")
 var growth=g.battle_start_snapshot.roster.duplicate(true)
 check(g.retry_battle(),"old snow field can retry normally")
 check(g.battle_data.tactical_review_version=="0.3.1" and g.roster==growth,"retry adopts continuous river without losing prebattle roster")
 for unit in g.units:check(g.movement_cost(unit,g.pos(unit))<255,"new river deploys legally: "+str(unit.id))
 # Full inventory: keep reward available, without consuming an action or item.
 g.save_path="res://reports/campaign/natural-M12-deployment-save.json";g.load_game();g.retry_battle()
 for id in g.party:g.roster[id].item_id=48
 g.convoy[g.route]=[]
 for i in range(40):g.convoy[g.route].append(48)
 var object=g.battle_data.objects.filter(func(o):return o.kind=="visit")[0]
 var actor=g.find_unit(g.leader_id());actor.item_id=48;actor.position=object.approach.duplicate();actor.acted=false;g.selected_id=actor.id
 check(not g.interact(object.id),"full inventory refuses collection safely")
 check(not actor.acted and not g.flags.quest.objects.get(object.id,false),"full inventory allows later collection")
 check(g.convoy[g.route].size()==40,"full inventory never overflows")
 # Moving a former fort back to its mountain underlay must not strand an
 # actor in an existing 0.3.0 battle. Preserve that field until normal retry.
 for code in ["M12","M13","M14","M15","S12","F25"]:
  var part="chambers" if code=="M15" else "east" if code=="F25" else "west"
  g.save_path="res://reports/battlefield-0.3.0/play/acceptance1-"+part+"/acceptance1-"+part+"-"+code+"-field.json"
  check(g.load_game(),code+" prior building layout loads")
  check(g.battle_data.map.tiles==g.read_json("res://data/compat/0.3.0/"+code+".json").map.tiles,code+" active old building terrain retained")
  var old_growth=g.battle_start_snapshot.roster.duplicate(true)
  g.save_path="res://reports/battlefield-0.3.0/state-working-save.json"
  check(g.retry_battle(),code+" old building layout retries safely")
  check(g.battle_data.tactical_review_version==g.stages[g.stage_id].tactical_review_version and g.roster==old_growth,code+" new posts retain prebattle growth")
  for unit in g.units:check(g.movement_cost(unit,g.pos(unit))<255,code+" renewed deployment legal "+str(unit.id))
 # Road flags require standing on the flag cell. Control persists and does
 # not conjure a door or alter either road opening/palisade collision.
 g.save_path="res://reports/campaign/natural-M14-deployment-save.json";g.load_game()
 g.save_path="res://reports/battlefield-0.3.0/state-working-save.json";g.retry_battle()
 var controls=g.battle_data.objects.filter(func(o):return o.kind=="control")
 var camp_ground=g.battle_data.map.tiles.duplicate()
 for point in controls:
  var commander=g.find_unit(g.leader_id());commander.acted=false
  commander.position=[point.position[0],point.position[1]+1]
  check(not g.interactions_for(commander).any(func(o):return o.id==point.id),"M14 adjoining road cell cannot control flag")
  commander.position=point.position.duplicate();g.selected_id=commander.id
  check(g.interactions_for(commander).any(func(o):return o.id==point.id),"M14 flag cell offers named control action")
  check(g.interact(point.id) and commander.acted and g.flags.quest.objects.get(point.id,false),"M14 control consumes action and records ownership")
  check(g.battle_data.map.tiles==camp_ground,"M14 capture keeps road and palisade geometry intact")
  check(g.save_game() and g.load_game() and g.flags.quest.objects.get(point.id,false),"M14 ownership survives save reload")
 # 0.3.4 positions may lie under the new stockade: load with their old field,
 # then use ordinary retry to deploy onto the authored checkpoint map.
 g.save_path="res://.cache/camp-checkpoint-fix/M14-old-0.3.4-entry.json"
 check(g.load_game(),"M14 0.3.4 field loads")
 check(g.battle_data.tactical_review_version=="0.3.4" and g.battle_data.map.tiles==g.read_json("res://data/compat/0.3.4/M14.json").map.tiles,"M14 prior field preserved until retry")
 var camp_growth=g.battle_start_snapshot.roster.duplicate(true)
 g.save_path="res://reports/battlefield-0.3.0/state-working-save.json"
 var old_traveller=g.find_unit(g.leader_id());old_traveller.position=[16,18]
 check(g.movement_cost(old_traveller,Vector2i(16,18))<255,"M14 prior ground stays walkable under future palisade")
 check(g.save_game() and g.load_game(),"M14 actor on future palisade cell reloads against prior geometry")
 check(g.battle_data.tactical_review_version=="0.3.4" and g.pos(g.find_unit(g.leader_id()))==Vector2i(16,18),"M14 prior actor is never moved or embedded into new stockade")
 check(g.retry_battle() and g.battle_data.tactical_review_version=="0.3.5" and g.roster==camp_growth,"M14 checkpoint retry preserves growth and current deployment")
 var f=FileAccess.open("res://reports/battlefield-0.3.0/state-checks.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"scope":"15 genuine old openings, 0.2.1 field, ordinary retry/preparation, correct new deployment and save round trips. No stored campaign checkpoint overwritten."},"  "));f.close()
 print("REDESIGN_STATE ",checks," ",errors)
 quit(0 if errors.is_empty() else 1)
