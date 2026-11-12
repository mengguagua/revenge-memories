extends RefCounted
## Movement plus the union of attacks from legal landing cells. Preview only.
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")

static func preview(game,unit: Dictionary) -> Dictionary:
	if unit.is_empty():return {"movement":[],"attack":[]}
	var movement=game.reachable(unit).costs.keys().filter(func(cell):return game.can_stop(unit,cell))
	var blue={}
	for cell in movement:blue[cell]=true
	var equipped=unit.duplicate(true)
	# Last turn's temporary spell selection is cleared by the action menu too.
	# It must not survive here as an extra, potentially locked attack option.
	equipped.erase("weapon_index")
	var attacks=[equipped]
	for spell in Items.spells(unit):
		if Items.is_support(spell):continue
		var caster=unit.duplicate(true);caster.weapon_index=spell;attacks.append(caster)
	var distances=[]
	# All supported bows/spells/body actions have at most five tiles of reach.
	for distance in range(1,6):
		if attacks.any(func(actor):return Rules.can_attack(actor,distance)):distances.append(distance)
	var outside={}
	for origin in movement:
		var mounted=Rules.platform_bow(game.combatant_at(equipped,origin))
		_add_cells(game,origin,range(1,Rules.ARROW_PLATFORM_RANGE+1) if mounted else distances,outside)
	return {"movement":movement,"attack":outside.keys().filter(func(cell):return not blue.has(cell))}

static func from_current_cell(game, unit: Dictionary) -> Array:
	var origin:Vector2i=game.pos(unit)
	var reach=Rules.attack_range(game.combatant_at(unit,origin))
	var cells={}
	if reach.y>0:_add_cells(game,origin,range(reach.x,reach.y+1),cells)
	return cells.keys()

static func _add_cells(game, origin: Vector2i, distances: Array, cells: Dictionary) -> void:
	for distance in distances:
		for dx in range(-distance,distance+1):
			var dy=distance-absi(dx)
			for sign_ in ([1] if dy==0 else [-1,1]):
				var cell=origin+Vector2i(dx,dy*sign_)
				if game.in_bounds(cell):cells[cell]=true
