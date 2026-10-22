extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/chapter2-environment-20261023/"
const CODES={"F21":201,"F22":202,"F23":203,"F24":204,"F25":205,"F26":206,"S21":211,"S22":212}
var checks=[]
var errors=[]
var info={}
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func setup(code:String):
 var g=State.new();g.save_path="res://reports/chapter2/play/natural-"+code+"-deployment-save.json"
 check(g.load_game(),code+" genuine source loads");g.save_path=OUT+"fixtures/working-"+code+".json"
 check(g.retry_battle(),code+" real preparation restores");check(g.start_battle(CODES[code]),code+" current battle enters")
 var occupied={}
 for u in g.units:
  check(not occupied.has(State.pos(u)),code+" unique unit "+u.id);occupied[State.pos(u)]=u.id
  check(g.in_bounds(State.pos(u)) and g.movement_cost(u,State.pos(u))<255,code+" legal unit cell "+u.id)
 return g
func boss_dead(g):g.find_unit(str(g.battle_data.boss_id)).hp=0
func clear_enemies(g):
 for u in g.living("enemy"):u.hp=0
func static_flood(g,start:Vector2i,opened:bool)->Dictionary:
 var prior=g.battle_data.map.tiles.duplicate();var width=int(g.battle_data.map.width)
 if opened:
  for obj in g.battle_data.objects:
   if obj.kind in ["door","rescue","bridge"]:
    for p in obj.get("opens",[obj.position] if obj.kind in ["door","rescue"] else []):
     g.battle_data.map.tiles[int(p[1])*width+int(p[0])]=int(obj.get("open_tile",208))
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
 g.save_path="res://reports/chapter2-environment-20261023/fixtures/"+code+"-"+suffix+".json"
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
 check(str(restored.battle_data.tactical_review_version)=="0.10.6-ch2",code+" current revision retained "+suffix)

func layouts():
 var records=[]
 for code in CODES:
  var g=setup(code);var origin=State.pos(g.find_unit(g.leader_id()));var closed=static_flood(g,origin,false);var opened=static_flood(g,origin,true)
  check(g.check_outcome()=="",code+" no initial outcome")
  for p in g.battle_data.player_positions:check(closed.has(Vector2i(p[0],p[1])),code+" connected deployment "+str(p))
  for u in g.battle_data.enemies+g.battle_data.reinforcements:
   if g.movement_cost({"class_id":6},State.pos(u))<255:check(closed.has(State.pos(u)),code+" ordinary enemy route "+u.id)
  for u in g.battle_data.npc_units:check(opened.has(State.pos(u)),code+" NPC connected after openings "+u.id)
  check(opened.has(Vector2i(g.battle_data.exit[0],g.battle_data.exit[1])),code+" real exit reachable")
  var saved=g.units.duplicate(true)
  for obj in g.battle_data.objects:
   var legal=fronts(g,obj).filter(func(p):return closed.has(p));check(not legal.is_empty(),code+" object reachable "+obj.id)
   for at in legal:
    var actor=position_actor(g,at);check(g.interactions_for(actor).any(func(o):return o.id==obj.id),code+" actual interaction exposed "+obj.id)
  g.units=saved;g.selected_id="";assert_saved(g,code,"entry")
  var changed=false
  for obj in g.battle_data.objects:
   if obj.kind not in ["door","rescue","bridge"]:continue
   interact_named(g,obj.id);changed=true
   for id in obj.get("unlock_units",[]):check(not g.find_unit(id).locked,code+" intended captive unlocked "+id)
   for p in obj.get("opens",[]):check(g.movement_cost({"class_id":6},Vector2i(p[0],p[1]))<255,code+" actual opens tile passable "+str(p))
   for a in obj.get("open_art_cells",[]):
    # A complete two-cell-high door bitmap also clears its already walkable upper interior cell.
    var at=Vector2i(a.position[0],a.position[1]);var nearby=obj.get("opens",[obj.position]).any(func(p):return absi(p[0]-at.x)+absi(p[1]-at.y)<=1)
    check(nearby and g.movement_cost({"class_id":6},at)<255,code+" visible door footprint clears only opened or already walkable neighboring cells "+str(a.position))
  if changed:assert_saved(g,code,"opened")
  records.append({"code":code,"size":[g.battle_data.map.width,g.battle_data.map.height],"closed_connected":closed.size(),"opened_connected":opened.size()})
 info.layouts=records
func objectives():
 var g=setup("F21");boss_dead(g);check(g.check_outcome()=="victory","F21 commander down plus intact ship wins")
 g=setup("F21");g.find_unit("friendly_ship").hp=0;check(g.check_outcome()=="defeat","F21 ship destruction fails")
 g=setup("F22");interact_named(g,"prison_door")
 for id in ["prisoners_0","prisoners_1","prisoners_2","lord"]:check(not g.find_unit(id).locked,"F22 master gate unlocks "+id)
 g.find_unit("lord").hp=0;check(g.check_outcome()=="","F22 optional Lord death does not fail rescue")
 for id in ["prisoners_0","prisoners_1","prisoners_2"]:evacuate_at(g,id,g.battle_data.exit)
 check(g.check_outcome()=="","F22 three evacuated still needs commander");boss_dead(g);check(g.check_outcome()=="victory","F22 three ordinary prisoners plus captain wins")
 g=setup("F22");g.find_unit("prisoners_1").hp=0;check(g.check_outcome()=="defeat","F22 any ordinary prisoner death makes three impossible")
 g=setup("F23");boss_dead(g);check(g.check_outcome()=="","F23 boss alone not enough");clear_enemies(g);check(g.check_outcome()=="victory","F23 all monsters cleared and camp alive wins")
 g=setup("F23");g.find_unit("fishers").hp=0;check(g.check_outcome()=="defeat","F23 camp destruction fails")
 g=setup("F24");boss_dead(g);g.turn=5;check(g.check_outcome()=="","F24 cannot finish before six");g.turn=6;g.phase="enemy";check(g.check_outcome()=="","F24 waits player phase");g.phase="player";check(g.check_outcome()=="victory","F24 six player phase plus boss wins")
 g=setup("F24");var attacker=g.find_unit("F24_e4");attacker.position=g.battle_data.targets[0].duplicate();g.turn=2;g.phase="player"
 g.ChapterTwo.after_phase(g);check(g.battle_outcome=="" and g.flags.quest.beacon_contested,"F24 initial occupation warns")
 g.turn=3;g.ChapterTwo.after_phase(g);check(g.battle_outcome=="defeat","F24 uninterrupted occupation for whole round fails")
 g=setup("F24");attacker=g.find_unit("F24_e4");attacker.position=g.battle_data.targets[0].duplicate();g.turn=2;g.phase="player";g.ChapterTwo.after_phase(g);attacker.hp=0;g.check_outcome();g.turn=3;g.ChapterTwo.after_phase(g);check(g.battle_outcome=="" and not g.flags.quest.beacon_contested,"F24 reclaim clears failure timer")
 g=setup("F25");boss_dead(g);check(g.check_outcome()=="","F25 boss does not secure objects");interact_named(g,"pilot_prison");check(g.check_outcome()=="","F25 prison alone insufficient");interact_named(g,"myth_box");check(g.check_outcome()=="victory","F25 prison and physical box confirmation wins")
 g=setup("S21");boss_dead(g);evacuate_at(g,"patients0",g.battle_data.exit);check(g.check_outcome()=="","S21 remaining monsters still matter");clear_enemies(g);check(g.check_outcome()=="victory","S21 one patient group plus all monsters wins")
 g=setup("S21");g.find_unit("patients0").hp=0;check(g.check_outcome()=="","S21 one survivor can still finish");g.find_unit("patients1").hp=0;check(g.check_outcome()=="defeat","S21 loss of both patient groups fails")
 g=setup("S22");clear_enemies(g);g.find_unit("old_sailor").hp=0;check(g.check_outcome()=="","S22 sailor death still requires relic");interact_named(g,"relics");check(g.check_outcome()=="victory","S22 death branch does not block relic clear")
func boats():
 var g=setup("F26");var paths=[]
 for b in g.battle_data.event_boats:
  check(int(b.hp)==30 and int(b.max_hp)==30 and int(b.speed)==3,"F26 ship original HP/speed "+b.id)
  for i in range(b.path.size()):
   var p=Vector2i(b.path[i][0],b.path[i][1]);check(g.in_bounds(p) and g.category(p)==7,"F26 boat on actual water "+b.id+" "+str(i))
   if i>0:check(absi(b.path[i][0]-b.path[i-1][0])+absi(b.path[i][1]-b.path[i-1][1])==1,"F26 contiguous water step "+b.id+" "+str(i))
  paths.append(b.path.size())
 check(g.battle_data.event_boats[0].delay==4 and g.battle_data.event_boats[1].delay==8,"F26 original staggered departure")
 boss_dead(g);check(g.check_outcome()=="","F26 commander alone insufficient");clear_enemies(g)
 for tick in range(100):
  if not g.battle_outcome.is_empty():break
  g.next_phase()
 check(g.event_boats().any(func(b):return b.arrived),"F26 actual phase progression brings a boat home")
 check(g.check_outcome()=="victory","F26 actual arrival plus boss wins");assert_saved(g,"F26","boat-arrived")
 g=setup("F26")
 for b in g.flags.quest.boats:b.hp=0
 check(g.check_outcome()=="defeat","F26 all boats destroyed fails")
 info.boat_path_lengths=paths
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+"fixtures"))
 var sources=State.read_json(OUT+"sources.json");var source_hashes={};var map_hashes={}
 for c in CODES:source_hashes[c]=FileAccess.get_file_as_string(sources[c]).sha256_text();map_hashes[c]=FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()
 layouts();objectives();boats()
 for c in CODES:
  check(FileAccess.get_file_as_string(sources[c]).sha256_text()==source_hashes[c],c+" original source untouched")
  check(FileAccess.get_file_as_string("res://data/stages/"+c+".json").sha256_text()==map_hashes[c],c+" map untouched by fixture")
 var f=FileAccess.open(OUT+"rules-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"check_count":checks.size(),"checks":checks,"errors":errors,"map_hashes":map_hashes,"source_hashes":source_hashes,"observations":info,"fixture":true,"is_actual_playthrough":false,"scope":"Current-map legal positions, connectivity, real interaction fronts, checkpoint reload, and isolated objective fixtures. No production data/core or genuine save modified."},"  "));f.close()
 print("CH2_RULES ",checks.size()," ",JSON.stringify(errors));quit(0 if errors.is_empty()else 1)
