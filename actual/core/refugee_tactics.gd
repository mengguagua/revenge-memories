extends RefCounted
## M11 armed escorts only. No RNG, speculative kills or changes to combat rules.
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const DIRECTIONS=[Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]

static func safe_attack(game,unit: Dictionary) -> Dictionary:
	if int(unit.hp)<=0 or unit.get("acted",false) or int(unit.hp)*5<int(unit.max_hp)*3:return {}
	var graph=game.reachable(unit);var best={};var score=-INF
	var cells=graph.costs.keys()
	cells.sort_custom(func(a,b):return a.y<b.y if a.y!=b.y else a.x<b.x)
	for cell in cells:
		if not game.can_stop(unit,cell):continue
		var risk=evaluate(game,unit,cell)
		if not risk.safe_position:continue
		for target in game.living("enemy"):
			var distance=_distance(cell,game.pos(target))
			if not Rules.can_attack(unit,distance) or Rules.attack_blocked(unit,target):continue
			var counter=Rules.default_counter(target,distance)
			var strikes=Rules.strike_sequence(unit,counter,distance)
			var damage=_damage(counter,unit,game.terrain_avoid(cell))
			var counter_loss=strikes.count("defender")*damage
			var total=counter_loss+int(risk.incoming)
			var reserve=maxi(5,ceili(int(unit.max_hp)*.35))
			if int(unit.hp)-total<reserve:continue
			if int(risk.threats)>=2 and total>int(unit.max_hp)*.30:continue
			var own=Rules.attack_stats(unit,target,game.terrain_avoid(game.pos(target)))
			var value=float(own.damage)*float(own.hit)/100.0-total*2-float(graph.costs[cell])*.1
			if value>score:
				score=value
				best={"destination":cell,"target":str(target.id),"spell_id":-1,"support":false,"teleport":false,
					"reason":"safe_escort_attack","risk":{"threats":risk.threats,"incoming":risk.incoming,"counter":counter_loss,"hp_reserve":int(unit.hp)-total}}
	return best

static func _distance(a: Vector2i,b: Vector2i) -> int:
	return absi(a.x-b.x)+absi(a.y-b.y)

static func _damage(attacker: Dictionary,defender: Dictionary,avoid: int) -> int:
	var stats=Rules.attack_stats(attacker,defender,avoid)
	# Forecast the full damage rather than relying on a miss. Any possible
	# critical is included; escorts never need to gamble on surviving it.
	return int(stats.damage)*(3 if int(stats.critical)>0 else 1)

static func evaluate(game,unit: Dictionary,cell: Vector2i) -> Dictionary:
	var occupied={}
	for actor in game.units:
		if int(actor.hp)>0 and actor.side!="evacuated" and str(actor.id)!=str(unit.id):occupied[game.pos(actor)]=actor
	occupied[cell]=unit
	var threats=0;var incoming=0
	for enemy in game.living("enemy"):
		if enemy.get("locked",false) or enemy.get("hidden",false) or enemy.get("offering_surrender",false):continue
		if not Rules.can_attack(enemy) or Rules.attack_blocked(enemy,unit):continue
		var graph=_enemy_reach(game,enemy,occupied)
		var worst=0
		for at in graph:
			if occupied.has(at) and str(occupied[at].id)!=str(enemy.id):continue
			var distance=_distance(at,cell)
			if not Rules.can_attack(enemy,distance):continue
			var sequence=Rules.strike_sequence(enemy,Rules.default_counter(unit,distance),distance)
			worst=maxi(worst,sequence.count("attacker")*_damage(enemy,unit,game.terrain_avoid(cell)))
		if worst>0:threats+=1;incoming+=worst
	return {"threats":threats,"incoming":incoming,"safe_position":threats<3}

static func _enemy_reach(game,enemy: Dictionary,occupied: Dictionary) -> Dictionary:
	var start=game.pos(enemy);var costs={start:0};var queue=[start]
	var budget=0 if enemy.get("behavior","") in ["guard","guard_exit"] else Items.movement(enemy)
	while not queue.is_empty():
		queue.sort_custom(func(a,b):return costs[a]<costs[b])
		var at: Vector2i=queue.pop_front()
		for direction in DIRECTIONS:
			var next=at+direction
			if not game.in_bounds(next) or next.x<=0 or next.y<=0 or next.x>=int(game.battle_data.map.width)-1 or next.y>=int(game.battle_data.map.height)-1:continue
			if occupied.has(next) and occupied[next].side!=enemy.side:continue
			var step=game.movement_cost(enemy,next);var cost=int(costs[at])+step
			if step>=255 or cost>budget or (costs.has(next) and int(costs[next])<=cost):continue
			costs[next]=cost;queue.append(next)
	return costs
