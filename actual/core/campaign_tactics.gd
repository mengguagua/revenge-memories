extends RefCounted
## Campaign troops use their real weapon range; guards react to an actual threat.
const Rules=preload("res://core/combat_rules.gd")

static func action(game, unit: Dictionary, gather: bool=false) -> Dictionary:
	if gather or unit.side!="enemy" or int(unit.hp)<=0 or unit.get("acted",false):return {}
	var guard=str(unit.get("behavior","")) in ["guard","guard_exit"]
	var campaign_caster=str(unit.get("campaign_role",""))=="bounded_summoner"
	if not guard and not campaign_caster and int(unit.class_id) not in [12,13,20]:return {}
	var actor=unit.duplicate(true);actor.erase("weapon_index")
	var opponents=game.living("player")
	var scripted_hold=unit.has("advance_after") and game.turn<int(unit.advance_after)
	var mounted=Rules.platform_bow(game.combatant_at(actor,game.pos(unit)))
	if guard and (scripted_hold or not mounted):
		# Only a committed friendly strike releases a sentry from its post.
		# Proximity, previewing an attack and damage-free turns cannot lure it.
		# Chapter objectives can explicitly raise the same persistent alert.
		if not bool(unit.get("guard_alerted",false)) or scripted_hold:
			return {"destination":game.pos(unit),"target":"","reason":"hold_post"}
	var costs={game.pos(unit):0} if mounted else game.reachable(actor).costs
	var result={"destination":game.pos(unit),"target":"","spell_id":-1,"support":false,"teleport":false,"reason":"guard_alert" if bool(unit.get("guard_alerted",false)) else "hold_post" if guard else "seek_firing_position"}
	var best=-INF
	for cell in costs:
		if not game.can_stop(actor,cell):continue
		var from_cell=game.combatant_at(actor,cell)
		for target in opponents:
			var distance=_distance(cell,game.pos(target))
			var attack=Rules.attack_context(from_cell,distance)
			if not Rules.can_attack(attack,distance) or Rules.attack_blocked(attack,target):continue
			var stats=Rules.attack_stats(attack,target,game.terrain_avoid(game.pos(target)))
			var counter=Rules.default_counter(game.combatant_at(target,game.pos(target)),distance)
			var sequence=Rules.strike_sequence(attack,counter,distance)
			var damage=float(stats.damage)*float(stats.hit)/100.0*sequence.count("attacker")
			var risk=0.0
			if sequence.has("defender"):
				var reply=Rules.attack_stats(counter,attack,game.terrain_avoid(cell))
				risk=float(reply.damage)*float(reply.hit)/100.0*sequence.count("defender")
			var score=damage*5.0-risk*2.0+game.terrain_avoid(cell)*0.1-float(costs[cell])*.1
			if damage>=int(target.hp):score+=30.0
			if risk>=int(actor.hp):score-=40.0
			if score>best:
				best=score;result.destination=cell;result.target=str(target.id)
				var weapon=Rules.weapon_index(attack)
				result.spell_id=weapon if weapon>=23 and weapon<47 else -1
	if not str(result.target).is_empty() or mounted or int(actor.move)<=0:return result
	# Seek an unoccupied firing tile, not a melee-only adjacent destination.
	var full=game.reachable(actor,true);var goal=game.pos(actor);var cost=INF
	for cell in full.costs:
		if float(full.costs[cell])>=cost or not game.can_stop(actor,cell):continue
		var from_cell=game.combatant_at(actor,cell)
		for target in opponents:
			var distance=_distance(cell,game.pos(target))
			if Rules.can_attack(from_cell,distance) and not Rules.attack_blocked(from_cell,target):goal=cell;cost=float(full.costs[cell]);break
	if goal==game.pos(actor):return result
	var path=[goal]
	while path[0]!=game.pos(actor):
		if not full.previous.has(path[0]):return result
		path.push_front(full.previous[path[0]])
	for cell in path:
		if costs.has(cell) and game.can_stop(actor,cell):result.destination=cell
	return result

static func _distance(a:Vector2i,b:Vector2i)->int:return absi(a.x-b.x)+absi(a.y-b.y)
