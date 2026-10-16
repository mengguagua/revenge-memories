extends "res://tests/tactical_review_play.gd"
## Real-input samples on revised maps. Cache only pure helper path/risk results;
## game logic, random stream, enemies and unit statistics are never altered.
var path_cache: Dictionary={}
var risk_cache: Dictionary={}

func _initialize() -> void:
 var label="round1"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--label="):label=arg.split("=")[1]
 review_out="res://reports/battlefield-0.3.0/play/"+label+"/"
 call_deferred("run")

func distance_map(unit: Dictionary,goals: Array) -> Dictionary:
 var key_=str(ui.game.stage_id)+":"+str(unit.class_id)+":"+str(unit.get("item_id",0))+":"+JSON.stringify(goals)+":"+JSON.stringify(ui.game.flags.quest.objects)
 if not path_cache.has(key_):path_cache[key_]=super.distance_map(unit,goals)
 return path_cache[key_]

func refresh_threats() -> void:
 risk_cache.clear();super.refresh_threats()

func risk(unit: Dictionary,cell: Vector2i,skip: String="") -> float:
 var key_=str(unit.id)+":"+str(unit.hp)+":"+str(unit.get("weapon_index",-1))+":"+str(cell)+":"+skip
 if not risk_cache.has(key_):risk_cache[key_]=super.risk(unit,cell,skip)
 return float(risk_cache[key_])

func plan(unit: Dictionary) -> Dictionary:
 if ui.game.stage_id in [201,202] and ui.game.turn<=4:
  for object in ui.game.battle_data.objects:
   if object.get("kind","")!="visit" or ui.game.flags.quest.objects.get(object.id,false):continue
   var at=Vector2i(object.approach[0],object.approach[1])
   if ui.game.reachable(unit).costs.has(at) and ui.game.can_stop(unit,at):
    return {"kind":"interact","cell":at,"score":250.0,"target":str(object.id),"spell":-1}
 if ui.game.stage_id in [201,202] and int(unit.hp)<int(unit.max_hp)*.8:
  var goals: Array=[]
  var map=ui.game.battle_data.map
  for y in range(map.height):
   for x in range(map.width):
    var cell=Vector2i(x,y)
    if ui.game.category(cell)==15:goals.append(cell)
  if not goals.is_empty():
   var field=distance_map(unit,goals);var origin=State.pos(unit);var before=int(field.get(origin,99999))
   var best={"kind":"wait","cell":origin,"score":-99999.0,"target":"","spell":-1}
   for cell in ui.game.reachable(unit).costs:
    if not ui.game.can_stop(unit,cell):continue
    var score=18.0*(before-int(field.get(cell,99999)))-risk(unit,cell)*3.0
    if goals.has(cell):score+=200.0
    if score>best.score:best={"kind":"wait","cell":cell,"score":score,"target":"","spell":-1}
   return best
 return super.plan(unit)

func tower_plan(unit: Dictionary) -> Dictionary:
 var origin=State.pos(unit);var boss=ui.game.find_unit("M15_boss");var rider=str(unit.id)=="lance"
 var point=ui.game.battle_data.get("assault_gate",[14,16]);var gate=Vector2i(point[0],point[1]);var exit_=ui.game.battle_data.exit;var exit_cell=Vector2i(exit_[0],exit_[1])
 var goal=gate if origin.y>gate.y else exit_cell if rider else State.pos(boss)
 var goals: Array=[goal]
 if not rider and origin.y<=gate.y:
  goals=[]
  for d in ui.game.DIRECTIONS:goals.append(State.pos(boss)+d)
 var field=distance_map(unit,goals);var before=int(field.get(origin,99999));var best={"kind":"wait","cell":origin,"score":-risk(unit,origin),"target":"","spell":-1}
 for cell in ui.game.reachable(unit).costs:
  if not ui.game.can_stop(unit,cell):continue
  var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
  var danger=risk(unit,cell);var walking=25.0*(before-int(field.get(cell,99999)))-danger*1.2
  if danger>=int(unit.hp)-2:walking-=100.0
  if rider and cell==exit_cell:walking+=300.0
  if walking>best.score:best={"kind":"wait","cell":cell,"score":walking,"target":"","spell":-1}
  for enemy in ui.game.targets(candidate):
   var stats=Rules.attack_stats(candidate,enemy,ui.game.terrain_avoid(State.pos(enemy)));var score=walking+minf(stats.damage,enemy.hp)*2.0+(120.0 if enemy.id=="M15_boss" and not rider else 0.0)
   if rider and cell!=exit_cell:score-=35.0
   if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":-1}
 return best

func write_review() -> void:
 # Keep compact readable evidence in Git; full rosters and repeated operation
 # dictionaries remain as local diagnostic cache, with final states in saves.
 var cache="res://.cache/battlefield-0.3.0/"+review_label
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(cache))
 var full=FileAccess.open(cache+"/trace.json",FileAccess.WRITE)
 full.store_string(JSON.stringify({"battles":review_battles,"operations":operations,"inputs":inputs,"failures":failures}));full.close()
 var concise=[]
 for b in review_battles:
  var item={}
  for k in ["code","source","scope","outcome","final_turn","key_inputs","failures","turns","quest"]:item[k]=b[k]
  item.actions=[];item.first_attack_turn=0
  for a in b.tactical_actions:
   var action={"turn":a.turn,"unit":a.unit,"from":a.from,"to":a.to,"terrain":a.terrain,"avoid":a.avoid}
   for op in a.operations:
    if op.has("action"):
     action.kind=op.action.kind;action.target=op.action.get("target","")
     if action.kind=="attack" and item.first_attack_turn==0:item.first_attack_turn=int(a.turn)
   item.actions.append(action)
  concise.append(item)
 var f=FileAccess.open(review_out+review_label+"-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"round":review_round,"passed":not review_battles.is_empty() and review_battles.all(func(b):return b.outcome=="victory"),"battles":concise,"inputs":inputs,"failures":failures,"checkpoints":checkpoints,"stat_edits":false,"forced_victories":false,"local_full_trace":cache+"/trace.json"},"  "));f.close()
