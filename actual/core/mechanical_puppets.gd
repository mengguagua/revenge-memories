extends RefCounted
## Mechanical identity, independent parts, finite debuff and non-kill withdrawal.
const CLASS_ID=25
const TITAN_CLASS_ID=26
const HAMMER=1009
const PALM=1007
const WATER=1008
const PART="back_cannon"
const CORE="protective_core"

const MODELS={25:"water_monkey",26:"pseudo_titan",27:"cyclops",28:"owl",29:"prometheus"}
const PULSE=1010
const CLAW=1011
const ANCHOR=1012
const FIRE=1013
const PARTS={"back_cannon":["背炮",10,2,1],"protective_core":["防护核心",16,3,2],"eye":["独眼核心",12,2,2],"engine":["引擎核心",12,3,2],"fire":["火之核心",18,5,3],"life":["生命核心",22,4,4]}
static func is_puppet(u:Dictionary)->bool:
 return str(u.get("unit_kind",""))=="mechanical_puppet" and MODELS.get(int(u.get("class_id",0)),"")==str(u.get("mechanical_model","?"))
static func is_water(u:Dictionary)->bool:return int(u.get("class_id",0))==25 and u.get("mechanical_model","")=="water_monkey"
static func is_titan(u:Dictionary)->bool:return int(u.get("class_id",0))==26 and u.get("mechanical_model","")=="pseudo_titan"
static func is_cyclops(u:Dictionary)->bool:return int(u.get("class_id",0))==27 and u.get("mechanical_model","")=="cyclops"
static func is_owl(u:Dictionary)->bool:return int(u.get("class_id",0))==28 and u.get("mechanical_model","")=="owl"
static func is_prometheus(u:Dictionary)->bool:return int(u.get("class_id",0))==29 and u.get("mechanical_model","")=="prometheus"
static func part_keys(u:Dictionary)->Array:
 if not is_puppet(u):return []
 return {25:[PART],26:[CORE],27:["eye"],28:["engine"],29:["fire","life"]}[int(u.class_id)]
static func part_key(u:Dictionary)->String:return str(part_keys(u)[0]) if is_puppet(u) else ""
static func part(u:Dictionary,key:String="")->Dictionary:return u.get("parts",{}).get(part_key(u) if key.is_empty() else key,{})
static func part_name(u:Dictionary,short:bool=false,key:String="")->String:
 key=part_key(u) if key.is_empty() else key
 var name=str(PARTS.get(key,[""])[0])
 return name.replace("核心","") if short else name
static func part_hp(u:Dictionary,key:String="")->int:return int(part(u,key).get("hp",0))
static func part_max(u:Dictionary,key:String="")->int:return int(PARTS.get(part_key(u) if key.is_empty() else key,["",0])[1])
static func base_move(u:Dictionary)->int:return int({25:5,26:4,27:4,28:8,29:6}.get(int(u.get("class_id",0)),0))
static func active(u:Dictionary,key:String)->bool:return is_puppet(u) and part_hp(u,key)>0 and not u.get("mechanical_part_context",false) and not u.get("maintenance",false)
static func core_active(u:Dictionary)->bool:return is_titan(u) and active(u,CORE)
static func armour_bonus(u:Dictionary)->int:return 10 if core_active(u) else 0
static func reflect(event:Dictionary,source:Dictionary,target:Dictionary)->void:
 if not core_active(target) or not str(event.get("target_part","")).is_empty():return
 var before=int(event.get("source_hp_after",source.get("hp",0)))
 event.reflection_hp_before=before;event.reflection_damage=mini(2,maxi(0,before))
 event.source_hp_before=int(event.get("source_hp_before",source.get("hp",0)))
 event.source_hp_after=maxi(0,before-2)
static func cannon_hp(u:Dictionary)->int:return part_hp(u) if is_water(u) else 0
static func valid_part(u:Dictionary,key:String)->bool:
 return part_keys(u).has(key) and int(u.get("hp",0))>0 and part_hp(u,key)>0 and not u.get("escaped",false) and not u.get("maintenance",false) and u.get("side","")=="enemy"
static func defence_context(u:Dictionary,key:String)->Dictionary:
 if not part_keys(u).has(key):return u
 var copy=u.duplicate(true)
 copy.defence=int(part(u,key).get("defence",0));copy.resistance=int(part(u,key).get("resistance",0));copy.item_id=0;copy.mechanical_part_context=true
 copy.hp=part_hp(u,key);copy.max_hp=part_max(u,key)
 return copy
static func prepare(u:Dictionary)->void:
 if not is_puppet(u):return
 if not u.has("parts"):
  u.parts={}
  for key in part_keys(u):
   var spec=PARTS[key];u.parts[key]={"hp":spec[1],"max_hp":spec[1],"defence":spec[2],"resistance":spec[3]}
 if not u.has("mechanical_base_move"):u.mechanical_base_move=base_move(u)
static func revive_event(u:Dictionary,event:Dictionary)->bool:
 if not is_prometheus(u) or int(event.get("hp_after",1))>0 or not active(u,"life") or not str(event.get("target_part","")).is_empty():return false
 event.prometheus_revived=true;event.hp_after=24
 u.hp=24;u.parts.life.hp=0
 return true
static func phase_start(g)->void:
 for u in g.living(g.phase):
  if not is_cyclops(u) or not active(u,"eye"):continue
  var healed=0
  for other in g.living(g.phase):
   if other.id==u.id or other.get("event_object",false) or other.get("hidden",false):continue
   var delta=g.pos(other)-g.pos(u)
   if maxi(absi(delta.x),absi(delta.y))!=1:continue
   var old=int(other.hp);other.hp=mini(int(other.max_hp),old+5);healed+=int(other.hp)-old
  if healed>0:
   g.log_lines.append(str(u.name_zh)+"为邻格队友恢复生命")
   if g.stage_id==204:
    var L=load("res://core/late_dialogue.gd");L.queue(g,L.lines("F24","战中推进",0),"F24-EYE-HEAL")
static func phase_end(g)->void:
 for u in g.living(g.phase):
  if is_prometheus(u) and active(u,"life"):
   var old=int(u.hp);u.hp=mini(int(u.max_hp),old+6)
   if int(u.hp)>old:g.log_lines.append("生命核心恢复%dHP"%(int(u.hp)-old))
static func canto_path(g,u:Dictionary)->Array:
 if not u.get("mechanical_canto_pending",false):return []
 u.erase("mechanical_canto_pending")
 if not is_owl(u) or not active(u,"engine") or int(u.hp)<=0 or u.get("mechanical_retreating",false) or not g.battle_outcome.is_empty():return []
 var mover=u.duplicate(true);mover.move=3
 var graph=g.reachable(mover);var goal=g.pos(u);var score=-INF
 for cell in graph.costs:
  if not g.can_stop(mover,cell):continue
  var gap=999
  for target in g.living("player"):gap=mini(gap,absi(cell.x-g.pos(target).x)+absi(cell.y-g.pos(target).y))
  var value=float(gap)-float(graph.costs[cell])*.01
  if value>score:score=value;goal=cell
 return g.path_to(mover,goal)

static func retreat_condition(g,side:String)->bool:
 var found=false
 for u in g.units:
  if str(u.get("side",""))!=side or int(u.get("hp",0))<=0 or u.get("hidden",false) or u.get("event_object",false):continue
  if not is_puppet(u):return false
  found=true
 return found

static func at_edge(g,u:Dictionary)->bool:
 var p=g.pos(u)
 return p.x==0 or p.y==0 or p.x==int(g.battle_data.map.width)-1 or p.y==int(g.battle_data.map.height)-1

static func escape(g,u:Dictionary)->void:
 if u.get("escaped",false) or int(u.hp)<=0:return
 u.escaped=true;u.hidden=true;u.acted=true
 g.log_lines.append(str(u.name_zh)+"逃离战场，未取得击败经验")

static func refresh(g,allow_escape:bool=true)->void:
 for u in g.units:
  if not is_puppet(u):continue
  prepare(u)
  var fleeing=not is_prometheus(u) and not u.get("maintenance",false) and not u.get("escaped",false) and int(u.hp)>0 and retreat_condition(g,str(u.side))
  u.mechanical_retreating=fleeing;u.move=int(u.mechanical_base_move)+(3 if fleeing else 0)
  if fleeing and allow_escape and at_edge(g,u):escape(g,u)

static func end_action(u:Dictionary)->void:u.erase("water_slow")

static func water_cell(g,p:Vector2i)->bool:
 var grid=g.battle_data.get("logic_grid",[])
 return p.y>=0 and p.y<grid.size() and p.x>=0 and p.x<str(grid[p.y]).length() and str(grid[p.y])[p.x]=="~"

static func escape_graph(g,u:Dictionary,unrestricted:bool)->Dictionary:
 var origin=g.pos(u);var costs={origin:0};var previous={};var queue=[origin]
 var budget=99999 if unrestricted else int(u.move)
 while not queue.is_empty():
  var best=0
  for i in range(1,queue.size()):
   if int(costs[queue[i]])<int(costs[queue[best]]):best=i
  var p:Vector2i=queue[best];queue.remove_at(best)
  for d in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
   var cell=p+d
   if not g.in_bounds(cell):continue
   var occupant:Dictionary=g.unit_at(cell)
   if not occupant.is_empty() and str(occupant.id)!=str(u.id):continue
   var step=int(g.movement_cost(u,cell))
   if step>=255:continue
   var cost=int(costs[p])+step
   if cost>budget or (costs.has(cell) and int(costs[cell])<=cost):continue
   costs[cell]=cost;previous[cell]=p
   if not queue.has(cell):queue.append(cell)
 return {"costs":costs,"previous":previous,"origin":origin}

static func edge_rank(g,p:Vector2i)->int:
 if p.y==0:return p.x
 if p.x==int(g.battle_data.map.width)-1:return 10000+p.y
 if p.y==int(g.battle_data.map.height)-1:return 20000+p.x
 return 30000+p.y

static func action(g,u:Dictionary,gather:bool=false)->Dictionary:
 if gather or not is_puppet(u) or u.get("acted",false) or u.get("escaped",false) or u.get("maintenance",false) or int(u.hp)<=0:return {}
 refresh(g)
 var result={"destination":g.pos(u),"target":"","spell_id":-1,"support":false,"teleport":false}
 if u.get("escaped",false):return result
 if u.get("mechanical_retreating",false):
  var graph=escape_graph(g,u,true);var goal=g.pos(u);var best=999999;var rank=999999
  for p in graph.costs:
   if p.x!=0 and p.y!=0 and p.x!=int(g.battle_data.map.width)-1 and p.y!=int(g.battle_data.map.height)-1:continue
   var cost=int(graph.costs[p]);var order=edge_rank(g,p)
   if cost<best or (cost==best and order<rank):goal=p;best=cost;rank=order
  var path=[goal]
  while path[0]!=g.pos(u) and graph.previous.has(path[0]):path.push_front(graph.previous[path[0]])
  for p in path:
   if int(graph.costs.get(p,99999))<=int(u.move):result.destination=p
  result.reason="mechanical_escape";return result
 var graph=g.reachable(u);var score=-INF
 for cell in graph.costs:
  if not g.can_stop(u,cell):continue
  for target in g.living("player"):
   if target.get("event_object",false):continue
   var distance=absi(cell.x-g.pos(target).x)+absi(cell.y-g.pos(target).y)
   var choices=[FIRE,ANCHOR] if is_prometheus(u) and active(u,"fire") else [0]
   for choice in choices:
    var probe=u.duplicate(true)
    if choice>0:probe.innate_attack_index=choice
    var attack=g.Rules.attack_context(probe,distance)
    attack=attack.duplicate(true);attack.position=[cell.x,cell.y]
    if not g.can_attack(attack,target):continue
    var stats=g.Rules.attack_stats(attack,target,g.terrain_avoid(g.pos(target)))
    var value=float(stats.damage)*float(stats.hit)/100.0*5.0-float(graph.costs[cell])*.1
    if is_water(u) and distance>1 and not target.get("water_slow",false):value+=8
    if value>score:
     score=value;result.destination=cell;result.target=str(target.id)
     if choice>0:result.innate_attack_index=choice

 if not str(result.target).is_empty():return result
 var nearest=99999
 for cell in graph.costs:
  if not g.can_stop(u,cell):continue
  for target in g.living("player"):
   var gap=absi(cell.x-g.pos(target).x)+absi(cell.y-g.pos(target).y)
   if gap<nearest:nearest=gap;result.destination=cell
 return result

static func valid_unit(u:Dictionary)->bool:
 if u.has("water_slow") and not u.water_slow is bool:return false
 if u.has("mechanical_part_context"):return false
 var marked=MODELS.has(int(u.get("class_id",0))) or u.has("mechanical_model") or u.get("unit_kind","")=="mechanical_puppet"
 if not marked:return not u.has("parts") and not u.has("mechanical_retreating") and not u.has("escaped")
 if not is_puppet(u) or not u.get("parts") is Dictionary or u.parts.size()!=part_keys(u).size():return false
 for key in part_keys(u):
  if not u.parts.get(key) is Dictionary:return false
  var p:Dictionary=u.parts[key];var spec=PARTS[key]
  for k in ["hp","max_hp","defence","resistance"]:
   if not p.get(k) is float and not p.get(k) is int:return false
   if float(p[k])!=floorf(float(p[k])):return false
  if int(p.max_hp)!=int(spec[1]) or int(p.hp)<0 or int(p.hp)>int(spec[1]) or int(p.defence)!=int(spec[2]) or int(p.resistance)!=int(spec[3]):return false
 if u.has("mechanical_base_move") and (not (u.mechanical_base_move is int or u.mechanical_base_move is float) or float(u.mechanical_base_move)!=float(base_move(u))):return false
 for k in ["mechanical_retreating","escaped","maintenance","mechanical_canto_pending"]:
  if u.has(k) and not u[k] is bool:return false
 if u.get("escaped",false) and (is_prometheus(u) or not u.get("hidden",false) or int(u.get("hp",0))<=0):return false
 if u.get("maintenance",false) and (not is_prometheus(u) or u.get("side","")!="neutral" or not u.get("no_counter",false)):return false
 return true
