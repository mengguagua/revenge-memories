extends RefCounted
## Campaign ranged troops seek firing distance. Fixed exit guards stay at their post.
const Rules=preload("res://core/combat_rules.gd")

static func action(game, unit: Dictionary, gather: bool=false) -> Dictionary:
	if gather or unit.side!="enemy" or int(unit.hp)<=0 or unit.get("acted",false):return {}
	var fixed=unit.get("behavior","")=="guard_exit"
	if not fixed and int(unit.class_id) not in [12,13,20]:return {}
	var actor=unit.duplicate(true);actor.erase("weapon_index")
	if fixed:actor.move=0
	var graph=game.reachable(actor)
	var opponents=game.living("player")
	var result={"destination":game.pos(unit),"target":"","spell_id":-1,"support":false,"teleport":false,"reason":"hold_exit" if fixed else "seek_firing_position"}
	var best=-INF
	for cell in graph.costs:
		if not game.can_stop(actor,cell):continue
		for target in opponents:
			var distance=absi(cell.x-game.pos(target).x)+absi(cell.y-game.pos(target).y)
			if not Rules.can_attack(actor,distance) or Rules.attack_blocked(actor,target):continue
			var stats=Rules.attack_stats(actor,target,game.terrain_avoid(game.pos(target)))
			var score=float(stats.damage)*5+float(stats.hit)*0.05+game.terrain_avoid(cell)*0.1-float(graph.costs[cell])*.1
			if not Rules.default_counter(target,distance).is_empty() and Rules.can_attack(Rules.default_counter(target,distance),distance):score-=3
			if score>best:best=score;result.destination=cell;result.target=str(target.id)
	if not str(result.target).is_empty() or fixed:return result
	# A ranged troop's destination is an unoccupied firing tile, never the
	# melee-only adjacent goal inherited from the original game AI.
	var full=game.reachable(actor,true);var goal=game.pos(actor);var cost=INF
	for cell in full.costs:
		if float(full.costs[cell])>=cost or not game.can_stop(actor,cell):continue
		for target in opponents:
			var distance=absi(cell.x-game.pos(target).x)+absi(cell.y-game.pos(target).y)
			if Rules.can_attack(actor,distance) and not Rules.attack_blocked(actor,target):goal=cell;cost=float(full.costs[cell]);break
	if goal==game.pos(actor):return result
	var path=[goal]
	while path[0]!=game.pos(actor):
		if not full.previous.has(path[0]):return result
		path.push_front(full.previous[path[0]])
	for cell in path:
		if graph.costs.has(cell) and game.can_stop(actor,cell):result.destination=cell
	return result
