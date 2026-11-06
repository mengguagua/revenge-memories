extends RefCounted
## Bounded campaign variants; source-game AI remains available to legacy battles.
const FIRST_SUMMON_TURN = 3
const SUMMON_INTERVAL = 3
const BLINK_INTERVAL = 3

static func protected_cell(g, cell: Vector2i) -> bool:
	if g.battle_data.has("exit") and cell == Vector2i(g.battle_data.exit[0],g.battle_data.exit[1]):return true
	for p in g.battle_data.get("targets",[]):
		if cell == Vector2i(p[0],p[1]):return true
	for obj in g.battle_data.get("objects",[]):
		for key in ["position","approach"]:
			if obj.has(key) and cell == Vector2i(obj[key][0],obj[key][1]):return true
	return false

static func base(g, unit: Dictionary) -> Dictionary:
	return {"destination":g.pos(unit),"target":"","spell_id":-1,"support":false,"teleport":false}

static func action(g, unit: Dictionary, gather: bool=false) -> Dictionary:
	if gather or str(unit.get("side",""))!="enemy" or int(unit.hp)<=0 or unit.get("acted",false):return {}
	var role = str(unit.get("campaign_role",""))
	if role == "short_blink" and g.turn >= 2 and g.turn >= int(unit.get("role_last_turn",-1))+BLINK_INTERVAL:
		var landing = blink_landing(g,unit)
		if landing != g.pos(unit):
			var result = base(g,unit)
			result.destination=landing;result.teleport=true;result.teleport_position=landing
			result.special="campaign_blink";result.blink_origin=g.pos(unit)
			return result
	if role not in ["bounded_summoner","bounded_divider"]:return {}
	var limit = 2 if role == "bounded_summoner" else 1
	var used = int(unit.get("role_summons_used",0))
	var ready = g.turn >= FIRST_SUMMON_TURN and g.turn >= int(unit.get("role_last_turn",0))+SUMMON_INTERVAL
	if used < limit and ready and g.Summons.available_slots(g,"enemy") > 0:
		var cid = 17 if role == "bounded_summoner" else 18
		var cost = 2 if cid == 17 else 0
		if int(unit.hp)>cost:
			var result = base(g,unit)
			result.target=str(unit.id);result.support=true;result.spell_id=37;result.special="campaign_summon"
			result.source_summon={"class_id":cid,"count":2 if cid==17 else 1,"hp_cost":cost,"divide":cid==18,
				"source_template_index":3 if cid==17 else 10,"campaign_minion":true,"avoid_objectives":true}
			return result
	# Between finite summon waves, fall through to campaign tactics. The
	# cantor's existing ghost-fire remains usable after its summons run out.
	return {}

static func blink_landing(g,unit:Dictionary) -> Vector2i:
	var origin=g.pos(unit);var best=origin;var nearest=999
	for target in g.living("player"):nearest=mini(nearest,distance(origin,g.pos(target)))
	# No global rear-line teleport: only relocate within four tiles of this body.
	for y in range(origin.y-4,origin.y+5):
		for x in range(origin.x-4,origin.x+5):
			var cell=Vector2i(x,y)
			if distance(origin,cell)>4 or not g.in_bounds(cell) or protected_cell(g,cell):continue
			if not g.unit_at(cell).is_empty() or g.movement_cost(unit,cell)>=255:continue
			var gap=999
			for target in g.living("player"):gap=mini(gap,distance(cell,g.pos(target)))
			if gap>=3 and gap<nearest:nearest=gap;best=cell
	return best

static func distance(a:Vector2i,b:Vector2i) -> int:return absi(a.x-b.x)+absi(a.y-b.y)

static func apply_special(g,caster:Dictionary,action_data:Dictionary) -> Dictionary:
	if int(caster.hp)<=0 or caster.get("acted",false):return {}
	if action_data.special=="campaign_blink":
		var cell:Vector2i=action_data.teleport_position
		# Rendering may already have moved the actor; recheck the original bounded leap.
		if str(caster.get("campaign_role",""))!="short_blink" or distance(action_data.blink_origin,cell)>4 or protected_cell(g,cell):return {}
		var occupant=g.unit_at(cell)
		if not g.in_bounds(cell) or g.movement_cost(caster,cell)>=255 or (not occupant.is_empty() and str(occupant.id)!=str(caster.id)):return {}
		caster.position=[cell.x,cell.y];caster.role_last_turn=g.turn;caster.acted=true;g.selected_id=""
		return {"action":"campaign_blink","changed":[],"spawned":[]}
	var role=str(caster.get("campaign_role",""));var limit=2 if role=="bounded_summoner" else 1
	if role not in ["bounded_summoner","bounded_divider"] or int(caster.get("role_summons_used",0))>=limit:return {}
	var spec:Dictionary=action_data.source_summon
	if g.turn<FIRST_SUMMON_TURN or g.turn<int(caster.get("role_last_turn",0))+SUMMON_INTERVAL or int(caster.hp)<=int(spec.hp_cost):return {}
	var spawned=g._summon(caster,int(spec.class_id),int(spec.count),spec)
	if not spawned.is_empty():
		caster.hp-=int(spec.hp_cost);caster.role_summons_used=int(caster.get("role_summons_used",0))+1;caster.role_last_turn=g.turn
	caster.acted=true;g.selected_id=""
	return {"action":"summon","changed":[],"spawned":spawned,"divide":bool(spec.divide)}
