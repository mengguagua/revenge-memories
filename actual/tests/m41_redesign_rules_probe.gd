extends SceneTree
## Isolated rule fixtures, not a gameplay victory. Never writes stage/core/source saves.
const State=preload("res://core/game_state.gd")
const SOURCE="res://reports/chapter4/play/round2-M41-deployment.json"
const OUT="res://reports/m41-redesign-20261022/rules-probe.json"
var checks=[]
var errors=[]
var observations={}
func _initialize():call_deferred("run")
func check(ok:bool,label:String)->void:
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func fixture():
 var g=State.new();g.save_path=SOURCE;check(g.load_game(),"historical deployment loads")
 g.save_path="/private/tmp/m41-rules-probe-unused-save.json"
 check(g.retry_battle(),"authentic pre-battle roster restores")
 check(g.start_battle(401),"current M41 normal start_battle entry")
 return g
func dist(a:Vector2i,b:Vector2i)->int:return absi(a.x-b.x)+absi(a.y-b.y)
func legal_anchors(g)->void:
 var occupied={}
 for u in g.units:
  var p=State.pos(u)
  check(not occupied.has(p),"unique initial unit "+str(u.id));occupied[p]=u.id
  check(p.x>0 and p.y>0 and p.x<int(g.battle_data.map.width)-1 and p.y<int(g.battle_data.map.height)-1,"inside playable border "+str(u.id))
  check(g.movement_cost(u,p)<255,"legal actor terrain "+str(u.id))
 var stored=g.units;g.units=[]
 var foot={"id":"probe","class_id":6,"side":"player","position":g.battle_data.player_positions[0],"move":4,"hp":28,"max_hp":28,"item_id":0}
 var field=g.reachable(foot,true).costs
 for u in stored:check(field.has(State.pos(u)),"static foot connectivity "+str(u.id))
 for o in g.battle_data.objects:check(field.has(Vector2i(o.position[0],o.position[1])),"static object connectivity "+str(o.id))
 check(field.has(Vector2i(g.battle_data.exit[0],g.battle_data.exit[1])),"static exit connectivity")
 observations.empty_foot_connected=field.size();g.units=stored
func use(g,id:String)->void:
 var hero=g.find_unit("hunapu")
 for o in g.battle_data.objects:
  if o.id!=id:continue
  for u in g.units:
   if u.id!=hero.id and u.position==o.position:u.hidden=true
  hero.position=o.position.duplicate();hero.acted=false;g.selected_id=hero.id
  check(g.interactions_for(hero).any(func(x):return x.id==id),"control available while standing "+id)
  check(g.interact(id),"ordinary interaction API accepts "+id);return
func evac(g,id:String)->void:
 var u=g.find_unit(id);u.position=g.battle_data.exit.duplicate();u.acted=false;g.mark_wait(id)
 check(g.flags.quest.evacuated.has(id) and u.side=="evacuated" and u.hidden,"exit mark_wait evacuates "+id)
func run()->void:
 var source_hash=FileAccess.get_file_as_string(SOURCE).sha256_text();var map_hash=FileAccess.get_file_as_string("res://data/stages/M41.json").sha256_text()
 var g=fixture();legal_anchors(g)
 var active=g.living("player").filter(func(u):return not u.get("neutral",false))
 check(active.size()==8,"eight genuine healthy combatants without Lena")
 check(not active.any(func(u):return u.id=="lena"),"injured flying member remains unavailable")
 check(g.check_outcome()=="","no initial outcome")
 var guards=[]
 for u in g.living("enemy"):
  var a=g.ai_action(u);check(a.destination==State.pos(u),"fixed guard stays put "+str(u.id))
  guards.append({"id":u.id,"cell":u.position,"range":[g.Rules.attack_range(u).x,g.Rules.attack_range(u).y],"initial_target":a.target})
 observations.fixed_guards=guards
 var civilians=[]
 for u in g.units:
  if u.get("quest_kind","")!="escort":continue
  var action=g.ai_action(u);var nearest=999;var danger_by=[]
  for e in g.living("enemy"):
   var distance=dist(State.pos(u),State.pos(e));nearest=mini(nearest,distance)
   if distance<=maxi(4,g.Rules.attack_range(e).y+1):danger_by.append(e.id)
  civilians.append({"id":u.id,"cell":u.position,"nearest_enemy":nearest,"blocked_by_safety":danger_by,"first_auto_destination":[action.destination.x,action.destination.y]})
 observations.initial_civilians=civilians
 var opening=[]
 for e in g.living("enemy"):
  var action=g.ai_action(e)
  if str(action.target).is_empty():continue
  var target=g.find_unit(str(action.target))
  if target.get("quest_kind","")!="escort":continue
  var stats=g.Rules.attack_stats(e,target,g.terrain_avoid(State.pos(target)))
  opening.append({"enemy":e.id,"resident":target.id,"distance":dist(State.pos(e),State.pos(target)),"damage":stats.damage,"hit":stats.hit,"attacker_speed":g.Rules.attack_speed(e),"resident_speed":g.Rules.attack_speed(target),"resident_hp":target.hp,"counter_allowed":not target.get("no_counter",false)})
 observations.opening_resident_exposure=opening
 # Every civilian must be safe from every fixed guard at entry, independently
 # of which candidate the guard currently prefers to target.
 for resident in g.units:
  if resident.get("quest_kind","")!="escort":continue
  for enemy in g.living("enemy"):
   if enemy.get("behavior","")!="guard_exit":continue
   var can_hit=g.Rules.can_attack(enemy,dist(State.pos(enemy),State.pos(resident))) and not g.Rules.attack_blocked(enemy,resident)
   check(not can_hit,"civilian outside initial fixed-guard attack range "+str(resident.id)+" / "+str(enemy.id))
 check(opening.is_empty(),"no fixed guard selects a civilian as initial attack target")
 # Normal phase API proves warning/spawn timing, with combat deliberately absent.
 g=fixture();g.story_events.clear()
 for i in range(3):g.next_phase()
 check(g.turn==2 and g.phase=="enemy" and not g.flags.quest.reinforced,"no reinforcement by enemy turn two")
 g.next_phase();check(g.turn==3 and g.phase=="player","third player phase reached")
 observations.turn3_story_events=g.story_events.duplicate(true)
 check(JSON.stringify(g.story_events).contains("M41-REINFORCEMENT-WARNING"),"warning queued on player turn three")
 g.next_phase();check(g.units.filter(func(u):return str(u.id).begins_with("M41_r")).is_empty(),"enemy turn three has no wave")
 g.next_phase();g.next_phase()
 var wave=g.units.filter(func(u):return str(u.id).begins_with("M41_r"))
 check(g.turn==4 and g.phase=="enemy" and wave.size()==2,"two riders spawn on enemy turn four")
 var wave_records=[]
 for u in wave:
  var a=g.ai_action(u);check(not u.acted,"new rider ready same phase "+u.id);check(g.can_stop(u,State.pos(u)),"rider spawn unique "+u.id)
  wave_records.append({"id":u.id,"cell":u.position,"destination":[a.destination.x,a.destination.y],"target":a.target})
 observations.wave_without_player_defence=wave_records
 g.next_phase();g.next_phase();check(g.units.filter(func(u):return str(u.id).begins_with("M41_r")).size()==2,"no second wave on turn five")
 # Isolated objective fixtures deliberately set positions/HP; never represented as play.
 g=fixture();use(g,"south_gate");use(g,"rest_station");g.find_unit("M41_boss").hp=0
 check(g.check_outcome()=="","flags and boss without evacuation do not win")
 evac(g,"snow_group0");check(g.check_outcome()=="","one evacuated group insufficient")
 evac(g,"snow_group1");check(g.check_outcome()=="victory","two groups plus both controls and boss win")
 g=fixture();evac(g,"snow_group0");evac(g,"snow_group1");g.find_unit("M41_boss").hp=0
 check(g.check_outcome()=="","evacuation plus boss but missing flags does not win")
 g=fixture();g.find_unit("snow_group0").hp=0;check(g.check_outcome()=="","one casualty remains recoverable")
 g.find_unit("snow_group1").hp=0;check(g.check_outcome()=="defeat","two civilian casualties fail immediately")
 # With hostiles removed in fixture, all three real routes reach the true exit without overlap.
 g=fixture();g.units=g.units.filter(func(u):return u.get("quest_kind","")=="escort");g.flags.quest.reinforced=true
 var itinerary={}
 for u in g.units:itinerary[str(u.id)]=[u.position.duplicate()]
 for round in range(20):
  for u in g.units:
   if u.side=="evacuated":continue
   u.acted=false;var a=g.ai_action(u);check(g.can_stop(u,a.destination),"escort safe empty landing "+u.id)
   u.position=[a.destination.x,a.destination.y];itinerary[str(u.id)].append(u.position.duplicate());g.mark_wait(u.id)
  if g.flags.quest.evacuated.size()==3:break
 check(g.flags.quest.evacuated.size()==3,"all three geometry routes evacuate after enemies cleared")
 observations.clear_route_itineraries=itinerary
 check(FileAccess.get_file_as_string(SOURCE).sha256_text()==source_hash,"historical checkpoint unchanged")
 check(FileAccess.get_file_as_string("res://data/stages/M41.json").sha256_text()==map_hash,"M41 data unchanged by probe")
 var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"fixture":true,"is_actual_playthrough":false,"map_sha256":map_hash,"checks":checks,"errors":errors,"observations":observations,"scope":"Read-only production files; isolated in-memory position/HP fixtures only for rules, never a victory claim."},"  "));f.close()
 print("M41_RULES_PROBE ",checks.size()," checks ",errors);quit(0 if errors.is_empty()else 1)
