extends SceneTree
## Directed geometry/rule checks, separate from real-input battle play.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
var checks: Array=[]
var errors: Array=[]
var stages: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func source(code: String) -> String:
 return ("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
func start(code: String):
 var g=State.new();g.save_path=source(code);check(g.load_game(),code+" genuine deployment loads")
 g.save_path="res://reports/review-0.2.1/rules-working-save.json"
 g.flags.erase("active_plot");g.story_events.clear()
 check(g.start_battle(g.stage_id),code+" fresh current map starts with actual roster");return g
func flood(g,unit: Dictionary,start_cell: Vector2i,closed: Array=[]) -> Dictionary:
 var seen={start_cell:0};var q: Array=[start_cell]
 while not q.is_empty():
  var p=q.pop_front()
  for delta in g.DIRECTIONS:
   var n=p+delta
   if not g.in_bounds(n) or seen.has(n) or n in closed or g.movement_cost(unit,n)>=255:continue
   if n.x==0 or n.y==0 or n.x==g.battle_data.map.width-1 or n.y==g.battle_data.map.height-1:continue
   seen[n]=int(seen[p])+1;q.append(n)
 return seen
func run() -> void:
 for code in ["M11","M12","M13","M14","M15","S11","S12","F21","F22","F23","F24","F25","F26","S21","S22"]:
  var before=FileAccess.get_file_as_bytes(source(code));var g=State.new();g.save_path=source(code)
  check(g.load_game(),code+" original save valid")
  var compatibility="res://data/compat/0.2.0/"+code+".json"
  if FileAccess.file_exists(compatibility):check(not g.battle_data.has("tactical_review_version"),code+" old in-progress geometry retained")
  g.save_path="res://reports/review-0.2.1/rules-working-save.json"
  g.flags.erase("active_plot");g.story_events.clear()
  check(g.start_battle(g.stage_id),code+" current layout starts")
  var geometry=g.battle_data;var occupied={};var foot={"class_id":8};var hero=g.find_unit(g.leader_id());var all_open=geometry.duplicate(true)
  for unit in g.units:
   check(g.in_bounds(State.pos(unit)) and g.movement_cost(unit,State.pos(unit))<255,code+" deployment is legal "+str(unit.id))
   check(not occupied.has(State.pos(unit)),code+" unique deployment "+str(unit.id));occupied[State.pos(unit)]=true
  for o in geometry.objects:
   if o.kind in ["door","rescue","bridge"]:
    for p in o.get("opens",[o.position] if o.kind in ["door","rescue"] else []):
     all_open.map.tiles[int(p[1])*int(geometry.map.width)+int(p[0])]=int(o.get("open_tile",208))
  g.battle_data=all_open;var field=flood(g,foot,State.pos(hero));g.battle_data=geometry
  for unit in g.units:
   check(field.has(State.pos(unit)),code+" ground route reaches original deployment "+str(unit.id))
  check(field.has(Vector2i(geometry.exit[0],geometry.exit[1])),code+" exit connected")
  for o in geometry.objects:
   var at=Vector2i(o.position[0],o.position[1]);var found=field.has(at) if not o.get("adjacent",true) else false
   for delta in g.DIRECTIONS:
    if field.has(at+delta):found=true
   check(found,code+" object has a reachable interaction side "+str(o.id))
  for m in geometry.art_modules:
   if m.get("logic","")!="#":continue
   for y in range(m.origin[1],m.origin[1]+m.footprint[1]):
    for x in range(m.origin[0],m.origin[0]+m.footprint[0]):
     # Dynamic door apertures can be opened, while saved base map is closed.
     check(g.movement_cost(foot,Vector2i(x,y))>=255,code+" solid artwork blocks foot movement: "+str(m.name)+str(Vector2i(x,y)))
  var forest=[];var stone=[];var plain=[]
  for y in range(geometry.map.height):
   for x in range(geometry.map.width):
    var at=Vector2i(x,y);var cat=g.category(at)
    if cat==1:forest.append(at)
    elif cat==8:stone.append(at)
    elif cat==0:plain.append(at)
  if not forest.is_empty():
   var cell=forest[0];check(g.terrain_avoid(cell)==40,code+" forest provides original 40 avoidance")
   check(g.movement_cost({"class_id":1},cell)==3 and g.movement_cost({"class_id":8},cell)==2 and g.movement_cost({"class_id":3},cell)==1,code+" forest costs distinguish cavalry, foot and flyer")
  if not stone.is_empty():check(g.terrain_avoid(stone[0])==20 and g.movement_cost(foot,stone[0])==1,code+" stone provides original 20 avoidance and normal movement")
  if not plain.is_empty():check(g.terrain_avoid(plain[0])==0,code+" open ground has no cover")
  check(not geometry.get("tactical_notes",[]).is_empty(),code+" tactics reachable in objective menu")
  check(g.save_game(),code+" new tactical save written")
  var reload=State.new();reload.save_path=g.save_path;check(reload.load_game() and reload.battle_data.get("tactical_review_version","")=="0.2.1",code+" new save resumes current geometry")
  check(before==FileAccess.get_file_as_bytes(source(code)),code+" original gameplay checkpoint unchanged")
  stages.append({"code":code,"forest_cells":forest.size(),"stone_cells":stone.size(),"open_ground_cells":plain.size(),"connected_ground_cells":field.size()})
 var prison=start("M13");var captive=prison.find_unit("M13_workers0");var attacker=prison.find_unit("M13_e1")
 attacker.position=[int(captive.position[0]),int(captive.position[1])+1]
 check(not prison.can_attack(attacker,captive),"closed first-chapter prisoners are held, not automatically executed")
 captive.locked=false;check(prison.can_attack(attacker,captive),"released first-chapter prisoners receive normal damage")
 var tower=start("M15");var worker=tower.find_unit("M15_workers0");var guard=tower.find_unit("M15_e1");guard.position=[int(worker.position[0]),int(worker.position[1])+1]
 check(not tower.can_attack(guard,worker),"tower captives protected by guard intent before release")
 worker.locked=false;check(tower.can_attack(guard,worker),"tower captives are vulnerable after release")
 var ship=start("F21");var defender=ship.find_unit("carlo");var mage=ship.find_unit("lisa");var soldier=ship.find_unit("F21_e1")
 # Declared local tactical fixture: original actors/stat sheets, legal floor.
 ship.units=[defender,mage,soldier];defender.position=[14,11];mage.position=[13,11];soldier.position=[15,11]
 check(not ship.reachable(soldier).costs.has(Vector2i(13,11)),"front defender prevents ground enemy crossing narrow jumpboard this turn")
 check(ship.can_attack(mage,soldier) and not ship.can_attack(soldier,mage),"mage supports from behind defender outside sword counter range")
 check(ship.reachable(soldier,true).costs.has(Vector2i(13,13)),"second jumpboard remains a real alternate attack route")
 var courtyard=start("M13");var front=State.pos(courtyard.find_unit(courtyard.leader_id()));var closed=[]
 for x in [7,8,13,14]:closed.append(Vector2i(x,12))
 check(flood(courtyard,{"class_id":8},front,closed).has(Vector2i(23,4)),"prison eastern passage bypasses both defended yard entrances")
 var harbor=start("F25");var western=flood(harbor,{"class_id":8},Vector2i(18,9),[Vector2i(18,8)])
 check(western.has(Vector2i(18,6)),"military harbor warehouse choke has a traversable flank route")
 var sea=start("F26")
 for boat in sea.battle_data.event_boats:
  for p in boat.path:check(sea.category(Vector2i(p[0],p[1]))==7,"civilian event boat follows actual water cells")
 var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"stages":stages,"scope":"Directed geometry, movement, cover, choke/flank and old-save compatibility fixtures; not natural combat wins","combat_formula_changed":false}
 var f=FileAccess.open("res://reports/review-0.2.1/rules.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("TACTICAL_RULES ",JSON.stringify({"passed":report.passed,"checks":report.checks,"errors":errors}));quit(0 if errors.is_empty() else 1)
