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
func test_camp_fort():
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


func static_flood(g,start:Vector2i,opened:bool)->Dictionary:
 var prior=g.battle_data.map.tiles.duplicate();var width=int(g.battle_data.map.width)
 if opened:
  for obj in g.battle_data.objects:
   if obj.kind in ["door","rescue"]:
    var p=obj.position;g.battle_data.map.tiles[int(p[1])*width+int(p[0])]=int(obj.get("open_tile",208))
 var seen={start:0};var todo=[start]
 while not todo.is_empty():
  var p=todo.pop_front()
  for delta in g.DIRECTIONS:
   var n=p+delta
   if n.x<=0 or n.y<=0 or n.x>=width-1 or n.y>=int(g.battle_data.map.height)-1 or seen.has(n):continue
   if g.movement_cost({"class_id":6},n)>=255:continue
   seen[n]=int(seen[p])+1;todo.append(n)
 g.battle_data.map.tiles=prior;return seen
func fronts(g,obj)->Array:
 var p=Vector2i(obj.position[0],obj.position[1]);var result=g.visit_fronts(obj)
 if not result.is_empty():return result
 if not obj.get("adjacent",false):return [p]
 result=[p]
 for delta in g.DIRECTIONS:result.append(p+delta)
 return result
func position_actor(g,cell:Vector2i):
 var hero=g.find_unit(g.leader_id())
 for unit in g.units:
  if unit.id!=hero.id and State.pos(unit)==cell:unit.hidden=true
 hero.position=[cell.x,cell.y];hero.acted=false;g.selected_id=hero.id;return hero
func interact_named(g,id:String)->void:
 var found=false
 for obj in g.battle_data.objects:
  if obj.id!=id:continue
  found=true;var closed=static_flood(g,State.pos(g.find_unit(g.leader_id())),false);var legal=fronts(g,obj).filter(func(p):return closed.has(p))
  check(not legal.is_empty(),str(g.battle_data.code)+" object has reachable front "+id)
  if legal.is_empty():return
  position_actor(g,legal[0]);check(g.interact(id),str(g.battle_data.code)+" normal interaction "+id)
 check(found,"object identity exists "+id)
func evacuate_at(g,id:String,at:Array)->void:
 var u=g.find_unit(id);u.position=at.duplicate();u.acted=false;g.mark_wait(id)
func assert_saved(g,code:String,suffix:String)->void:
 g.save_path="res://reports/chapter1-climate-20261022/fixtures/"+code+"-"+suffix+".json"
 var units=JSON.stringify(g.units);var roster=JSON.stringify(g.roster);var flags=JSON.stringify(g.flags.quest);var tiles=JSON.stringify(g.battle_data.map.tiles);var size=[g.battle_data.map.width,g.battle_data.map.height]
 check(g.save_game(),code+" current checkpoint saved "+suffix)
 var restored=State.new();restored.save_path=g.save_path;check(restored.load_game(),code+" current checkpoint reloads "+suffix)
 check(restored.units==JSON.parse_string(units),code+" reloaded units exact "+suffix)
 check(restored.roster==JSON.parse_string(roster),code+" reloaded roster exact "+suffix)
 check(restored.flags.quest==JSON.parse_string(flags),code+" reloaded quest exact "+suffix)
 var parsed_tiles=JSON.parse_string(tiles);var differences=[]
 for i in range(parsed_tiles.size()):
  if float(restored.battle_data.map.tiles[i])!=float(parsed_tiles[i]):differences.append({"index":i,"before":parsed_tiles[i],"after":restored.battle_data.map.tiles[i]})
 if not info.has("reload_terrain_differences"):info.reload_terrain_differences={}
 info.reload_terrain_differences[code+"-"+suffix]=differences
 check(differences.is_empty() and JSON.parse_string(JSON.stringify(restored.battle_data.map.tiles))==parsed_tiles,code+" reloaded open-door terrain exact "+suffix)
 check([restored.battle_data.map.width,restored.battle_data.map.height]==size,code+" reloaded current dimensions "+suffix)
 check(str(restored.battle_data.tactical_review_version)=="0.10.5-ch1",code+" current revision retained "+suffix)
func test_six_layouts()->void:
 var codes={"M12":102,"M13":103,"M14":104,"M15":105,"S11":111,"S12":112};var records=[]
 for code in codes:
  var g=setup(code,codes[code]);var closed=static_flood(g,State.pos(g.find_unit(g.leader_id())),false);var opened=static_flood(g,State.pos(g.find_unit(g.leader_id())),true)
  check(g.check_outcome()=="",code+" no initial outcome")
  for p in g.battle_data.player_positions:check(closed.has(Vector2i(p[0],p[1])),code+" deployment connected "+str(p))
  for u in g.battle_data.enemies+g.battle_data.reinforcements:check(closed.has(State.pos(u)),code+" enemy anchor connected "+str(u.id))
  for u in g.battle_data.npc_units:check(opened.has(State.pos(u)),code+" NPC connected after unlock "+str(u.id))
  check(closed.has(Vector2i(g.battle_data.exit[0],g.battle_data.exit[1])),code+" exit reachable from outside cells")
  var route_units=g.units.duplicate(true)
  for obj in g.battle_data.objects:
   var approach=fronts(g,obj).filter(func(p):return closed.has(p));check(not approach.is_empty(),code+" object accessible "+obj.id)
   for cell in approach:
    var hero=position_actor(g,cell);check(g.interactions_for(hero).any(func(o):return o.id==obj.id),code+" actual menu offers "+obj.id+" at "+str(cell))
  g.units=route_units;g.selected_id=""
  assert_saved(g,code,"entry")
  for index in range(g.battle_data.objects.size()):
   var obj=g.battle_data.objects[index]
   if obj.kind not in ["door","rescue"]:continue
   var worker=code+"_workers"+str(index);check(not g.find_unit(worker).is_empty(),code+" gate array index maps to worker "+str(index));check(g.find_unit(worker).locked,code+" matching worker initially locked "+str(index))
   interact_named(g,obj.id);check(not g.find_unit(worker).locked,code+" matching worker released "+str(index))
   var at=Vector2i(obj.position[0],obj.position[1]);check(g.movement_cost({"class_id":6},at)<255,code+" opened gate becomes legal terrain "+str(index))
   for art in obj.get("open_art_cells",[]):check(art.position==obj.position,code+" opening artwork uses current gate "+str(index))
  if code in ["M13","M15"]:assert_saved(g,code,"gates-open")
  records.append({"code":code,"width":g.battle_data.map.width,"height":g.battle_data.map.height,"closed_connected":closed.size(),"opened_connected":opened.size()})
 info.six_layouts=records
func test_grain()->void:
 var g=setup("M12",102);check(int(g.battle_data.burner_departure_turn)==7,"M12 unchanged seventh-turn departure")
 var burner=g.units.filter(func(u):return u.get("burner",false))[0];g.units=[burner];g.turn=6;var before=State.pos(burner);var a=g.ai_action(burner)
 check(a.destination==before,"M12 burner holds through turn six")
 g.turn=7;a=g.ai_action(burner);check(a.destination!=before,"M12 burner departs turn seven toward targets zero")
 g=setup("M12",102);burner=g.units.filter(func(u):return u.get("burner",false))[0];g.turn=7;burner.position=g.battle_data.targets[0].duplicate();g.mark_wait(burner.id)
 check(g.flags.quest.burn_streak==1 and g.battle_outcome=="","M12 first consecutive ignition warns without loss")
 burner.position=[burner.position[0]-1,burner.position[1]];g.turn=8;g.mark_wait(burner.id);check(g.flags.quest.burn_streak==0,"M12 leaving warehouse breaks fire streak")
 burner.position=g.battle_data.targets[0].duplicate();g.turn=9;g.mark_wait(burner.id);check(g.flags.quest.burn_streak==1 and g.battle_outcome=="","M12 renewed first ignition remains recoverable")
 g.turn=10;g.mark_wait(burner.id);check(g.flags.quest.burn_streak==2 and g.battle_outcome=="defeat","M12 second consecutive ignition fails")
 g=setup("M12",102);g.find_unit(g.battle_data.boss_id).hp=0;check(g.check_outcome()=="","M12 boss alone insufficient");interact_named(g,"M12_occupy_0");check(g.check_outcome()=="victory","M12 boss plus occupation wins")
 g=setup("M12",102);interact_named(g,"M12_occupy_0");check(g.check_outcome()=="","M12 occupation alone insufficient");g.find_unit(g.battle_data.boss_id).hp=0;check(g.check_outcome()=="victory","M12 occupation then boss wins")
func test_prison()->void:
 var g=setup("M13",103);g.find_unit(g.battle_data.boss_id).hp=0;check(g.check_outcome()=="","M13 boss alone insufficient")
 interact_named(g,"M13_door_0");check(not g.find_unit("M13_workers0").locked and not g.find_unit("lena").locked,"M13 first gate releases worker zero and Lena")
 check(g.find_unit("M13_workers1").locked and g.check_outcome()=="","M13 first gate alone insufficient")
 interact_named(g,"M13_door_1");check(g.check_outcome()=="victory","M13 both gates and live freed workers plus boss win")
 g=setup("M13",103);g.find_unit("lena").hp=0;check(g.check_outcome()=="","M13 Lena casualty does not block main objective")
 g.find_unit("M13_workers0").hp=0;check(g.check_outcome()=="","M13 one worker casualty still recoverable")
 g.find_unit("M13_workers1").hp=0;check(g.check_outcome()=="defeat","M13 both worker casualties fail")
func test_mine()->void:
 var g=setup("S11",111);g.find_unit(g.battle_data.boss_id).hp=0;check(g.check_outcome()=="","S11 boss alone insufficient")
 evacuate_at(g,"S11_miners0",g.battle_data.exit);check(g.flags.quest.evacuated.has("S11_miners0") and g.check_outcome()=="","S11 one miner at exit insufficient")
 evacuate_at(g,"S11_miners1",g.battle_data.exit);check(g.check_outcome()=="victory","S11 both miners and boss win")
 g=setup("S11",111);evacuate_at(g,"S11_miners0",g.battle_data.exit);evacuate_at(g,"S11_miners1",g.battle_data.exit);check(g.check_outcome()=="","S11 both evacuees without boss insufficient")
 g=setup("S11",111);g.find_unit("beck").hp=0;check(g.check_outcome()=="","S11 Beck casualty does not block main objective")
 g.find_unit("S11_miners0").hp=0;check(g.check_outcome()=="defeat","S11 a required miner death fails")
func test_medicine()->void:
 var g=setup("S12",112);var wagon=g.find_unit("medicine_wagon")
 evacuate_at(g,"medicine_wagon",g.battle_data.exit);check(not g.flags.quest.evacuated.has("medicine_wagon"),"S12 map exit is not the delivery target")
 evacuate_at(g,"medicine_wagon",g.battle_data.targets[0]);check(g.flags.quest.evacuated.has("medicine_wagon") and wagon.hidden and wagon.side=="evacuated","S12 targets zero is actual medicine delivery")
 check(g.check_outcome()=="","S12 delivered wagon still requires boss")
 g.find_unit(g.battle_data.boss_id).hp=0;check(g.check_outcome()=="victory","S12 delivery and boss win")
 g=setup("S12",112);g.find_unit(g.battle_data.boss_id).hp=0;check(g.check_outcome()=="","S12 boss alone insufficient")
 g=setup("S12",112);g.find_unit("medicine_wagon").hp=0;check(g.check_outcome()=="defeat","S12 medicine wagon destruction fails")
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/chapter1-climate-20261022/fixtures"))
 var sources=State.read_json("res://reports/chapter1-climate-20261022/sources.json");var source_hashes={};var map_hashes={}
 for code in sources:
  source_hashes[code]=FileAccess.get_file_as_string(sources[code]).sha256_text();map_hashes[code]=FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()
 test_six_layouts();test_grain();test_prison();test_mine();test_medicine();test_camp_fort()
 for code in sources:
  check(FileAccess.get_file_as_string(sources[code]).sha256_text()==source_hashes[code],code+" original genuine checkpoint unchanged")
  check(FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()==map_hashes[code],code+" stage data unchanged by probe")
 var f=FileAccess.open("res://reports/chapter1-climate-20261022/rules-probe.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":errors.is_empty(),"fixture":true,"is_actual_playthrough":false,"checks":checks,"check_count":checks.size(),"errors":errors,"observations":info,"map_hashes":map_hashes,"source_hashes":source_hashes,"scope":"Six current layouts, source-faithful entry, connectivity, live interaction availability, save/reload and isolated in-memory rule fixtures. HP/position setup in fixtures is not represented as a real combat victory. No production data/core or genuine saves changed."},"  "));f.close()
 print("CH1_REDESIGN_RULES ",checks.size()," ",errors);quit(0 if errors.is_empty()else 1)
