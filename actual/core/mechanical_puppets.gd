extends RefCounted
## Mechanical identity, independent parts, finite debuff and non-kill withdrawal.
const CLASS_ID=25
const TITAN_CLASS_ID=26
const HAMMER=1009
const PALM=1007
const WATER=1008
const PART="back_cannon"
const CORE="protective_core"

static func is_puppet(u:Dictionary)->bool:
	return str(u.get("unit_kind",""))=="mechanical_puppet" and (is_water(u) or is_titan(u))

static func is_water(u:Dictionary)->bool:
	return int(u.get("class_id",0))==CLASS_ID and str(u.get("mechanical_model",""))=="water_monkey"

static func is_titan(u:Dictionary)->bool:
	return int(u.get("class_id",0))==TITAN_CLASS_ID and str(u.get("mechanical_model",""))=="pseudo_titan"

static func part_key(u:Dictionary)->String:return CORE if is_titan(u) else PART
static func part_name(u:Dictionary,short:bool=false)->String:return ("核心" if short else "防护核心") if is_titan(u) else "背炮"
static func part_hp(u:Dictionary)->int:return int(part(u).get("hp",0))
static func part_max(u:Dictionary)->int:return 16 if is_titan(u) else 10
static func base_move(u:Dictionary)->int:return 4 if is_titan(u) else 5
static func core_active(u:Dictionary)->bool:
	return is_puppet(u) and is_titan(u) and part_hp(u)>0 and not u.get("mechanical_part_context",false)
static func armour_bonus(u:Dictionary)->int:return 10 if core_active(u) else 0

static func reflect(event:Dictionary,source:Dictionary,target:Dictionary)->void:
	# Snapshot before applying the target's wound: even a fatal/missed body strike reflects.
	if not core_active(target) or not str(event.get("target_part","")).is_empty():return
	var before=int(event.get("source_hp_after",source.get("hp",0)))
	event.reflection_hp_before=before;event.reflection_damage=mini(2,maxi(0,before))
	event.source_hp_before=int(event.get("source_hp_before",source.get("hp",0)))
	event.source_hp_after=maxi(0,before-2)

static func part(u:Dictionary)->Dictionary:
	return u.get("parts",{}).get(part_key(u),{}) if is_puppet(u) else {}

static func cannon_hp(u:Dictionary)->int:return part_hp(u) if is_water(u) else 0

static func valid_part(u:Dictionary,key:String)->bool:
	return key==part_key(u) and is_puppet(u) and int(u.get("hp",0))>0 and part_hp(u)>0 and not u.get("escaped",false)

static func defence_context(u:Dictionary,key:String)->Dictionary:
	if key!=part_key(u) or not is_puppet(u):return u
	var copy=u.duplicate(true)
	copy.defence=int(part(u).get("defence",2));copy.resistance=int(part(u).get("resistance",1));copy.item_id=0;copy.mechanical_part_context=true
	copy.hp=part_hp(u);copy.max_hp=part_max(u)
	return copy

static func prepare(u:Dictionary)->void:
	if not is_puppet(u):return
	if not u.has("parts"):u.parts={part_key(u):{"hp":part_max(u),"max_hp":part_max(u),"defence":3 if is_titan(u) else 2,"resistance":2 if is_titan(u) else 1}}
	if not u.has("mechanical_base_move"):u.mechanical_base_move=base_move(u)

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
		var fleeing=not u.get("escaped",false) and int(u.hp)>0 and retreat_condition(g,str(u.side))
		u.mechanical_retreating=fleeing;u.move=int(u.mechanical_base_move)+(3 if fleeing else 0)
		if fleeing and allow_escape and at_edge(g,u):escape(g,u)

static func end_action(u:Dictionary)->void:u.erase("water_slow")

static func water_cell(g,p:Vector2i)->bool:
	var grid=g.battle_data.get("logic_grid",[])
	return g.stage_id==201 and p.y>=0 and p.y<grid.size() and p.x>=0 and p.x<str(grid[p.y]).length() and str(grid[p.y])[p.x]=="~"

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
	if gather or not is_puppet(u) or u.get("acted",false) or u.get("escaped",false) or int(u.hp)<=0:return {}
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
			var attack=g.Rules.attack_context(u,distance)
			attack=attack.duplicate(true);attack.position=[cell.x,cell.y]
			if not g.can_attack(attack,target):continue
			var stats=g.Rules.attack_stats(attack,target,g.terrain_avoid(g.pos(target)))
			var value=float(stats.damage)*float(stats.hit)/100.0*5.0-float(graph.costs[cell])*.1
			if is_water(u) and distance>1 and not target.get("water_slow",false):value+=8
			if value>score:score=value;result.destination=cell;result.target=str(target.id)
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
	if u.has("mechanical_part_context"):return false # Ephemeral forecast context must never enter a save.
	var marked=int(u.get("class_id",0)) in [CLASS_ID,TITAN_CLASS_ID] or u.has("mechanical_model") or u.get("unit_kind","")=="mechanical_puppet"
	if not marked:return not u.has("parts") and not u.has("mechanical_retreating") and not u.has("escaped")
	if not is_puppet(u) or not u.get("parts") is Dictionary or u.parts.size()!=1 or not u.parts.get(part_key(u)) is Dictionary:return false
	var p:Dictionary=u.parts[part_key(u)]
	for k in ["hp","max_hp","defence","resistance"]:
		if not p.get(k) is float and not p.get(k) is int:return false
		if float(p[k])!=floorf(float(p[k])):return false
	if int(p.max_hp)!=part_max(u) or int(p.hp)<0 or int(p.hp)>part_max(u) or int(p.defence)!=(3 if is_titan(u) else 2) or int(p.resistance)!=(2 if is_titan(u) else 1):return false
	if u.has("mechanical_base_move") and (not (u.mechanical_base_move is int or u.mechanical_base_move is float) or float(u.mechanical_base_move)!=float(base_move(u))):return false
	for k in ["mechanical_retreating","escaped"]:
		if u.has(k) and not u[k] is bool:return false
	if u.get("escaped",false) and (not u.get("hidden",false) or int(u.get("hp",0))<=0):return false
	return true
