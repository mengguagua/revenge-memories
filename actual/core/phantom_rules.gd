extends RefCounted
## Campaign Illusion. Enemy summons retain their original templates/budgets.
const Items=preload("res://core/item_rules.gd")
const Experience=preload("res://core/campaign_experience.gd")
const COST=10
const LIMIT=6
const BASIC=[1,6,8,12,3]
const ADVANCED=[4,2,9,13,5]
const FINAL=[7,22,10,20,5]

static func is_phantom(unit:Dictionary)->bool:
	return bool(unit.get("phantom",false))

static func formal(g,unit:Dictionary)->bool:
	return not unit.is_empty() and unit.get("side","")=="player" and not unit.get("temporary",false) and not unit.get("neutral",false) and g.roster.has(str(unit.get("id",""))) and not g.Casualties.owner({"parties":g.parties},str(unit.get("id",""))).is_empty()

static func uses(g,caster:Dictionary)->int:
	return int(g.flags.get("phantom_training",{}).get(str(caster.get("id","")),0))

static func rank(g,caster:Dictionary)->int:
	return mini(3,1+uses(g,caster)/6)

static func pool(level:int)->Array:
	var result=BASIC.duplicate()
	for cid in (ADVANCED if level>=2 else [])+(FINAL if level>=3 else []):
		if not result.has(cid):result.append(cid)
	return result

static func body(g,caster:Dictionary,cid:int)->Dictionary:
	var unit:Dictionary=Items.data().promotion_bases[str(cid)].duplicate(true)
	unit.merge({"class_id":cid,"character_id":35,"name_id":35,"name_zh":"幻影","class":g.catalog.classes[str(cid)].key,
		"level":1,"exp":0,"hp":int(unit.max_hp),"item_id":0,"magic_flags":0,"raw_magic_flags":0,
		"resistance":15 if cid==10 else 0,"personal_resistance":0,"move":int(Items.data().class_move[cid-1]),
		"side":"player","route":str(caster.get("route",g.route)),"summoner_id":str(caster.id),
		"phantom":true,"temporary":true,"controllable":false,"no_experience":true,"no_drop":true,
		"acted":true,"dead":false,"ai_flags":68,"raw_ai_flags":68,"phantom_born_turn":int(g.turn)},true)
	return unit

static func reason(g,caster:Dictionary)->String:
	if not formal(g,caster):return "仅正式队员可施放幻影"
	if g.flags.get("phantom_maps",{}).get(str(g.stage_id),false):return "本地图全队已使用幻影"
	if int(caster.get("hp",0))<=COST:return "生命须高于10才能施放"
	if plan(g,caster,false).is_empty():return "周围没有可生成幻影的空位"
	return ""

static func plan(g,caster:Dictionary,randomize:bool)->Array:
	var level=rank(g,caster);var classes=pool(level);var cells=[];var choices={}
	for offset in Items.summon_offsets():
		var cell=g.pos(caster)+Vector2i(int(offset[1]),int(offset[0]))
		if cells.has(cell) or not g.in_bounds(cell) or not g.unit_at(cell).is_empty():continue
		cells.append(cell);choices[cell]=[]
		for cid in classes:
			if g.movement_cost(body(g,caster,cid),cell)<255:choices[cell].append(cid)
	var result=[];var selected=[]
	while result.size()<level*2:
		var eligible=[]
		var required=(FINAL if level==3 else ADVANCED) if result.is_empty() and level>1 else classes
		for cid in required:
			if cells.any(func(cell):return choices[cell].has(cid)):eligible.append(cid)
		if eligible.is_empty():break
		var distinct=eligible.filter(func(cid):return not selected.has(cid))
		if not distinct.is_empty():eligible=distinct
		var cid=int(eligible[g.random_bounded(eligible.size())] if randomize else eligible[0])
		var available=cells.filter(func(cell):return choices[cell].has(cid))
		# Put flying bodies over water/rough ground first, preserving ordinary
		# ground for the remaining professions. Count takes priority over variety.
		available.sort_custom(func(a,b):return choices[a].size()<choices[b].size())
		var cell=available[0]
		result.append({"class_id":cid,"cell":cell});selected.append(cid);cells.erase(cell)
	return result

static func cast(g,caster:Dictionary)->Dictionary:
	if g.mode!="battle" or g.phase!="player" or caster.get("acted",false) or not Items.spells(caster).has(45) or not reason(g,caster).is_empty():return {}
	var placement=plan(g,caster,true)
	if placement.is_empty():return {}
	var before=rank(g,caster);var spawned=[]
	for n in range(placement.size()):
		var unit=body(g,caster,int(placement[n].class_id));var cell:Vector2i=placement[n].cell
		unit.id="phantom_%d_%d_%d"%[g.stage_id,g.frame_counter,g.units.size()]
		unit.position=[cell.x,cell.y];unit.phantom_slot=n
		g.units.append(unit);spawned.append(str(unit.id))
	caster.hp=int(caster.hp)-COST;caster.acted=true;caster.erase("weapon_index");g.selected_id=""
	if not g.flags.has("phantom_maps"):g.flags.phantom_maps={}
	if not g.flags.has("phantom_training"):g.flags.phantom_training={}
	g.flags.phantom_maps[str(g.stage_id)]=true
	if not g.Training.active(g):g.flags.phantom_training[str(caster.id)]=mini(12,uses(g,caster)+1)
	g.check_outcome()
	return {"caster":str(caster.id),"spell_id":45,"action":"invoke","changed":[],"spawned":spawned,
		"phantom_rank_before":before,"phantom_rank_after":rank(g,caster),"source_hp_after_support":int(caster.hp)}

static func reward(g,exchange:Dictionary)->Dictionary:
	if exchange.get("phantom_rewarded",false):return {}
	var first=g.find_unit(str(exchange.attacker));var second=g.find_unit(str(exchange.defender))
	var actor=first if is_phantom(first) else second
	if not is_phantom(actor):return {}
	var enemy=second if actor==first else first
	var owner=g.find_unit(str(actor.summoner_id))
	if not formal(g,owner) or int(owner.hp)<=0 or enemy.get("no_experience",false):return {}
	if not exchange.events.any(func(event):return str(event.attacker)==str(actor.id)):return {}
	var before=int(exchange.initial_defender_hp) if actor==first else int(exchange.initial_attacker_hp)
	var gain=g.Rules.experience_gain(owner,enemy,before,int(enemy.hp),int(enemy.hp)<=0)
	if gain<=0:return {}
	exchange.phantom_rewarded=true
	var receipt=Experience.award(g,owner,gain)
	receipt.victory_training=false;receipt.phantom_source=str(actor.id)
	return receipt

static func valid_unit(g,unit:Dictionary)->bool:
	if not unit.get("phantom") is bool:return false
	if not is_phantom(unit):return true
	if unit.side!="player" or not unit.get("temporary",false) or unit.get("controllable",true) or not unit.get("no_experience",false) or not unit.get("no_drop",false):return false
	if not pool(3).has(int(unit.class_id)) or int(unit.level)!=1 or int(unit.get("exp",0))!=0 or int(unit.get("item_id",0))!=0:return false
	if not g.characters.has(str(unit.get("summoner_id",""))) or unit.get("personal_resistance")!=0 or unit.get("resistance")!=(15 if int(unit.class_id)==10 else 0):return false
	var base:Dictionary=Items.data().promotion_bases[str(int(unit.class_id))]
	for key in ["max_hp","strength","skill","speed","luck","defence"]:
		if unit.get(key)!=base[key]:return false
	if unit.get("move")!=Items.data().class_move[int(unit.class_id)-1]:return false
	if not g.SaveValidation._integer(unit.get("phantom_born_turn"),1,2147483647):return false
	if not unit.get("phantom_slot") is float and not unit.get("phantom_slot") is int:return false
	return float(unit.phantom_slot)==int(unit.phantom_slot) and int(unit.phantom_slot)>=0 and int(unit.phantom_slot)<LIMIT
