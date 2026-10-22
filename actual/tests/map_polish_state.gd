extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/map-polish-20261022/"
var errors=[]
var checks=0
var records=[]
func check(ok:bool,label:String):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func flood(g,start:Vector2i,opened:bool) -> Dictionary:
 var old=g.battle_data.map.tiles.duplicate();var w=int(g.battle_data.map.width)
 if opened:
  for o in g.battle_data.objects:
   for p in o.get("opens",[o.position] if o.kind in ["door","rescue"] else []):g.battle_data.map.tiles[int(p[1])*w+int(p[0])]=int(o.get("open_tile",208))
 var seen={start:0};var queue=[start];var index=0
 while index<queue.size():
  var p=queue[index];index+=1
  for delta in g.DIRECTIONS:
   var n=p+delta
   if not g.in_bounds(n) or seen.has(n) or g.movement_cost({"class_id":6},n)>=255:continue
   seen[n]=int(seen[p])+1;queue.append(n)
 g.battle_data.map.tiles=old;return seen
func _initialize():call_deferred("run")
func run():
 var codes:PackedStringArray=[]
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--codes="):codes=arg.split("=")[1].split(",")
 if codes.is_empty():codes=["M12","M13","M14","M15","S11","S12"]
 var source_hashes={}
 for code in codes:
  var source=("res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/")+"natural-"+code+"-deployment-save.json"
  source_hashes[code]=FileAccess.get_file_as_string(source).sha256_text()
  var g=State.new();g.save_path=source;check(g.load_game(),code+" genuine historical checkpoint loads")
  g.save_path=OUT+"state-working-save.json"
  check(g.retry_battle(),code+" normal retry enters current map")
  var d=g.battle_data
  check(str(d.tactical_review_version)=="0.10.2",code+" new map revision active")
  var positions={}
  for u in g.units:
   check(g.in_bounds(State.pos(u)) and g.movement_cost(u,State.pos(u))<255,code+" legal deployment "+str(u.id))
   check(not positions.has(State.pos(u)),code+" distinct deployment "+str(u.id));positions[State.pos(u)]=true
  var closed=flood(g,State.pos(g.find_unit(g.leader_id())),false);var opened=flood(g,State.pos(g.find_unit(g.leader_id())),true)
  for p in d.player_positions:check(closed.has(Vector2i(p[0],p[1])),code+" initial deployment connected")
  for u in d.enemies+d.npc_units+d.reinforcements:check(opened.has(Vector2i(u.position[0],u.position[1])),code+" route reaches "+str(u.id))
  check(opened.has(Vector2i(d.exit[0],d.exit[1])),code+" exit connected after normal unlocks")
  for o in d.objects:
   var fronts=g.visit_fronts(o);var at=Vector2i(o.position[0],o.position[1])
   if fronts.is_empty():
    fronts=[at]
    if o.get("adjacent",false):
     for delta in g.DIRECTIONS:fronts.append(at+delta)
   check(fronts.any(func(p):return closed.has(p)),code+" accessible interaction "+str(o.id))
  var before=g.roster.duplicate(true);var units=g.units.duplicate(true)
  check(g.save_game() and g.load_game(),code+" new map save/reload")
  check(g.roster==JSON.parse_string(JSON.stringify(before)) and g.units==JSON.parse_string(JSON.stringify(units)),code+" save retains roster and formation")
  check(FileAccess.get_file_as_string(source).sha256_text()==source_hashes[code],code+" original checkpoint unchanged")
  records.append({"code":code,"closed_reachable":closed.size(),"opened_reachable":opened.size(),"hash":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text()})
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"maps":records,"scope":"Directed legal deployment, terrain connectivity, native interaction access and current-map save fixtures; no old-map compatibility retained and no combat wins claimed."}
 var f=FileAccess.open(OUT+"state-"+"-".join(codes)+".json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
 print("MAP_POLISH_STATE ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors}));quit(0 if errors.is_empty() else 1)
