extends RefCounted
## Displacement belongs to a completed initiating melee exchange, not a strike.
## Counterattacks and follow-ups resolve before it, with no extra damage/action.
const Items = preload("res://core/item_rules.gd")
const Rules = preload("res://core/combat_rules.gd")
static var _config: Dictionary = {}

static func config() -> Dictionary:
	if _config.is_empty():_config=JSON.parse_string(FileAccess.get_file_as_string("res://data/knockback_equipment.json"))
	return _config

static func innate(g, unit: Dictionary) -> bool:
	return str(unit.get("side",""))=="enemy" and config().innate_elites.get(str(int(g.stage_id)),[]).has(str(unit.get("id","")))

static func capable(g, unit: Dictionary) -> bool:
	if unit.is_empty():return false
	if innate(g,unit):return true
	var held_id=int(unit.get("item_id",0))
	var held=Items.item(held_id)
	return bool(held.get("knockback",false)) and Items.can_use(unit,held_id) and Rules.weapon_index(unit)==int(held.get("base_weapon",-1))

static func description(g, unit: Dictionary) -> String:
	if not capable(g,unit):return ""
	return "击退：主动近战命中并造成伤害，交战结束推开存活目标1格；反击不触发，障碍、占位或不可通行时不推。"

static func preview(g, attacker: Dictionary, defender: Dictionary) -> Dictionary:
	var result={"valid":false,"reason":"","target":str(defender.get("id","")),"from":[],"to":[]}
	if not capable(g,attacker):return result
	if defender.is_empty() or int(attacker.get("hp",0))<=0 or int(defender.get("hp",0))<=0:return result
	if str(attacker.get("side",""))==str(defender.get("side","")):return result
	var delta:Vector2i=g.pos(defender)-g.pos(attacker)
	if absi(delta.x)+absi(delta.y)!=1:
		result.reason="仅主动近战可击退";return result
	result.from=[g.pos(defender).x,g.pos(defender).y]
	var at:Vector2i=g.pos(defender)+delta
	result.to=[at.x,at.y]
	# Captives, event apparatus and tethered story objects are not movable foes.
	if bool(defender.get("locked",false)) or bool(defender.get("event_object",false)):
		result.reason="目标被固定，无法击退";return result
	if not g.in_bounds(at) or at.x<=0 or at.y<=0 or at.x>=int(g.battle_data.map.width)-1 or at.y>=int(g.battle_data.map.height)-1:
		result.reason="后方为边界，不击退";return result
	# Flight may traverse the source terrain category for walls/cargo, but a
	# horizontal shove must not place a body inside a solid obstacle. Check the
	# live category so opened gates and demolished cargo immediately become legal.
	# Forest (1), mountains and flyable water (7) retain their ordinary movement.
	if g.category(at)==12 or g.movement_cost(defender,at)>=255:
		result.reason="后方有障碍或不可通行，不击退";return result
	if not g.can_stop(defender,at):
		result.reason="后方已被占据，不击退";return result
	result.valid=true
	result.reason="造成伤害且交战后双方存活：击退1格"
	return result

static func apply_exchange(g, exchange: Dictionary) -> Dictionary:
	if exchange.is_empty() or bool(exchange.get("knockback_resolved",false)):return {}
	exchange.knockback_resolved=true
	var attacker=g.find_unit(str(exchange.get("attacker","")))
	var defender=g.find_unit(str(exchange.get("defender","")))
	# Finish_exchange may remove the selected weapon, so inspect committed event
	# metadata as well. A held lance must never add knockback to a selected spell.
	if not capable(g,attacker):return {}
	var legal_hit=false
	for event in exchange.get("events",[]):
		if str(event.get("attacker",""))!=str(attacker.get("id","")) or str(event.get("defender",""))!=str(defender.get("id","")):continue
		if bool(event.get("hit",false)) and int(event.get("damage",0))>0 and int(event.get("distance",exchange.get("distance",0)))==1 and int(event.get("weapon_index",47))<23:
			legal_hit=true;break
	if not legal_hit:return {}
	var result=preview(g,attacker,defender)
	if not bool(result.valid):return result
	defender.position=result.to.duplicate()
	# No acted/cursor/turn changes: forced movement is not a new action or wait.
	return result

static func award_clear(g, stage: int, announce: bool=true) -> void:
	var spec:Dictionary=config().rewards.get(str(stage),{})
	if spec.is_empty() or not g.stage_cleared(stage):return
	var taken:Dictionary=g.flags.get("knockback_clear_rewards",{})
	if bool(taken.get(str(stage),false)):return
	g.convoy[str(spec.route)].append(int(spec.item_id))
	taken[str(stage)]=true;g.flags.knockback_clear_rewards=taken
	if announce:g.queue_lines(str(spec.text),"KNOCKBACK-SUPPLY-"+str(stage))
