extends SceneTree
const State=preload("res://core/game_state.gd")
var checks=[]
var errors=[]
var info={}
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func setup(code,id):
 var g=State.new();g.save_path="res://reports/campaign/natural-"+code+"-deployment-save.json"
 check(g.load_game(),code+" real historical deployment loads");g.save_path="/private/tmp/ch1-camp-fort-probe-unused.json"
 check(g.retry_battle(),code+" historical pre-battle state restores");check(g.start_battle(id),code+" current normal entry")
 var occupied={}
 for u in g.units:
  check(not occupied.has(State.pos(u)),code+" unique unit "+u.id);occupied[State.pos(u)]=u.id
  check(g.movement_cost(u,State.pos(u))<255,code+" legal terrain "+u.id)
 return g
func open_object(g,index):
 var obj=g.battle_data.objects[index];var hero=g.find_unit("hunapu");hero.position=[obj.position[0],obj.position[1]+1];hero.acted=false;g.selected_id=hero.id
 for u in g.units:
  if u.id!=hero.id and u.position==hero.position:u.hidden=true
 check(g.interact(obj.id),"M15 real interaction opens "+str(index))
 check(not g.find_unit("M15_workers"+str(index)).locked,"M15 matching worker unlock "+str(index))
 var cell=Vector2i(obj.position[0],obj.position[1]);check(g.movement_cost(hero,cell)<255,"M15 unlocked door traversable "+str(index))
func run():
 var g=setup("M14",104);var boss=g.find_unit("M14_boss")
 boss.hp=13;g.check_outcome();check(boss.offering_surrender and boss.no_counter,"M14 half health offering survives")
 var hero=g.find_unit("hunapu");hero.position=[boss.position[0]-1,boss.position[1]];hero.acted=false;g.selected_id=hero.id
 check(g.interact("surrender") and boss.surrendered,"M14 adjacent accepted surrender")
 check(g.check_outcome()=="","M14 still requires both checkpoints")
 for o in g.battle_data.objects:
  if o.kind!="control":continue
  hero.position=o.position.duplicate();hero.acted=false;g.selected_id=hero.id;check(g.interact(o.id),"M14 reachable stand-on checkpoint "+o.id)
 check(g.check_outcome()=="victory","M14 both checkpoints plus surrender wins")
 g=setup("M15",105)
 for i in range(2):
  var u=g.find_unit("M15_workers"+str(i));check(u.locked,"M15 worker initially captive "+str(i));check(not g.can_attack(g.find_unit("M15_e1"),u),"M15 prisoner not targeted by own guards "+str(i))
 open_object(g,0);check(g.find_unit("M15_workers1").locked,"M15 first gate does not unlock second cell");open_object(g,1)
 g=setup("M15",105);boss=g.find_unit("M15_boss");var initial=boss.position.duplicate();g.units=[boss]
 check(boss.move==9,"M15 exact original nine movement retained")
 g.turn=5;boss.hp=15;var a=g.ai_action(boss);check(a.destination==State.pos(boss),"M15 no retreat turn five at low health")
 g.turn=6;boss.hp=16;a=g.ai_action(boss);check(a.destination==State.pos(boss),"M15 exactly half health not early retreat")
 boss.hp=15;a=g.ai_action(boss);check(a.destination!=State.pos(boss) and g.flags.quest.escape_announced,"M15 below half at six starts announced retreat")
 boss.position=initial.duplicate();boss.hp=32;g.turn=8;a=g.ai_action(boss)
 var first=a.destination;var exit=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]);check(first!=exit,"M15 cannot escape from initial post in one nine-move action")
 boss.position=[first.x,first.y];g.turn=9;a=g.ai_action(boss);check(a.destination==exit,"M15 unblocked retreat reaches gate on second action")
 info.boss_retreat={"move":boss.move,"initial":initial,"turn8_destination":[first.x,first.y],"turn9_destination":[a.destination.x,a.destination.y]}
 g=setup("M15",105);var lance=g.find_unit("lance");check(not lance.is_empty(),"M15 authentic Lance available")
 if not lance.is_empty():
  g.units=[lance];var steps=[];var goal=Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]);var destinations=[Vector2i(30,23),Vector2i(30,5),goal]
  var turn=0
  for dest in destinations:
   for count in range(12):
    if State.pos(lance)==dest:break
    var action=g._toward(lance,dest);check(action.destination!=State.pos(lance),"M15 east-boardwalk advances to "+str(dest))
    lance.position=[action.destination.x,action.destination.y];turn+=1;steps.append(lance.position.duplicate())
  info.cavalry_unopposed_east_route={"move":lance.move,"turns":turn,"positions":steps,"note":"In-memory unobstructed movement fixture, not a combat playthrough."}
  check(State.pos(lance)==goal and turn<=7,"M15 seven-move cavalry can intercept via east boardwalk by turn seven")
 var f=FileAccess.open("res://reports/chapter1-redesign-20261022/camp-fort/rules-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"fixture":true,"checks":checks,"errors":errors,"observations":info,"map_hashes":{"M14":FileAccess.get_file_as_string("res://data/stages/M14.json").sha256_text(),"M15":FileAccess.get_file_as_string("res://data/stages/M15.json").sha256_text()},"scope":"Independent in-memory rule fixtures only, no production state or save changed; not a victory claim."},"  "));f.close();print("CAMP_FORT_RULES ",checks.size()," ",errors);quit(0 if errors.is_empty()else 1)
