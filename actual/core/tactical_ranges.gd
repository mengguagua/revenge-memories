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
		for distance in distances:
			for dx in range(-distance,distance+1):
				var dy=distance-absi(dx)
				for sign_ in ([1] if dy==0 else [-1,1]):
					var cell=origin+Vector2i(dx,dy*sign_)
					if game.in_bounds(cell) and not blue.has(cell):outside[cell]=true
	return {"movement":movement,"attack":outside.keys()}
