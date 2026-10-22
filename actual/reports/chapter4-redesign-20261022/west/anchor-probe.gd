extends SceneTree
const State=preload("res://core/game_state.gd")
const CODES=["M42","M43","M44","S41"]
var checks=0
var errors=[]
var records={}
func check(ok,label):
 checks+=1
 if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
 for code in CODES:
  var g=State.new();g.battle_data=State.read_json("res://data/stages/"+code+".json")
  var d=g.battle_data;var start=d.player_positions[0].duplicate();var actor={"id":"anchor_probe","class_id":6,"position":start.duplicate(),"side":"player","hp":1,"move":5,"item_id":0}
  g.units=[actor];g.selected_id=actor.id
  var closed=g.reachable(actor,true).costs
  for p in d.player_positions:check(closed.has(Vector2i(p[0],p[1])),code+" deployment reachable "+str(p))
  for u in d.enemies+d.reinforcements:
   var p=Vector2i(u.position[0],u.position[1])
   if g.movement_cost(actor,p)<255:check(closed.has(p),code+" ground enemy reachable "+u.id)
  for obj in d.objects:
   var fronts=g.visit_fronts(obj)
   if fronts.is_empty():
    var at=Vector2i(obj.position[0],obj.position[1]);fronts=[at]
    if obj.get("adjacent",false):
     for delta in g.DIRECTIONS:fronts.append(at+delta)
   check(fronts.any(func(p):return closed.has(p)),code+" actual object front reachable "+obj.id)
  var width=int(d.map.width)
  for obj in d.objects:
   if obj.kind in ["door","rescue","bridge"]:
    for p in obj.get("opens",[obj.position]if obj.kind in["door","rescue"]else[]):d.map.tiles[int(p[1])*width+int(p[0])]=int(obj.get("open_tile",208))
  var opened=g.reachable(actor,true).costs
  for u in d.npc_units:check(opened.has(Vector2i(u.position[0],u.position[1])),code+" NPC connected after openings "+u.id)
  var goal=Vector2i(d.exit[0],d.exit[1]);check(goal.x>0 and goal.y>0 and goal.x<width-1 and goal.y<int(d.map.height)-1,code+" exit inside playable border")
  check(opened.has(goal),code+" exit in actual reachable graph")
  var trace=[actor.position.duplicate()]
  if opened.has(goal):
   for turn in range(100):
    if State.pos(actor)==goal:break
    var action=g._toward(actor,goal);var old=actor.position.duplicate()
    check(g.move_selected(action.destination),code+" ordinary move_selected accepted "+str(turn))
    trace.append(actor.position.duplicate())
    if actor.position==old:break
   check(State.pos(actor)==goal,code+" actual step sequence reaches exit")
  records[code]={"sha256":FileAccess.get_file_as_string("res://data/stages/"+code+".json").sha256_text(),"exit":d.exit,"closed_reachable":closed.size(),"opened_reachable":opened.size(),"exit_step_trace":trace}
 var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"maps":records,"scope":"In-memory fixture uses actual reachable and move_selected methods, with ordinary 5-move infantry and no occupants; logical door opening applied only in memory. Checks four west maps' deployment, ground enemies, object fronts, released NPCs and exit, then genuinely steps to each exit. No save or source map is mutated; not a combat playthrough."}
 var f=FileAccess.open("res://reports/chapter4-redesign-20261022/west/anchor-probe.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("CH4_WEST_ANCHORS ",JSON.stringify({"passed":report.passed,"checks":checks,"errors":errors}));quit(0 if errors.is_empty()else 1)
