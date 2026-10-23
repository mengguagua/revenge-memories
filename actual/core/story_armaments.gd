extends RefCounted
## One fixed event per armament. Convoy delivery never replaces carried gear.
const Items = preload("res://core/item_rules.gd")

static func claimed(g, item_id: int) -> bool:
	return bool(g.flags.get("story_armaments_claimed",{}).get(str(item_id),false))

static func delivery_pages(item_id: int) -> Array:
	var spec: Dictionary = Items.armaments().items.get(str(item_id),{})
	if spec.is_empty():return []
	var pages: Array = spec.delivery_pages.duplicate(true)
	pages.append({"speaker":"旁白","text":str(Items.armaments().set_name)+" · "+str(spec.name_zh)+"已收入"+("西队" if spec.route=="alm" else "东队")+"行囊，可在部队整备中分配。"})
	return pages

static func claim(g, item_id: int, announce: bool = true) -> bool:
	var spec: Dictionary = Items.armaments().items.get(str(item_id),{})
	if spec.is_empty() or claimed(g,item_id) or not g.stage_cleared(int(spec.stage)):return false
	if spec.trigger=="local_cycle" and not g.HeroProfessions.advanced(g.roster.get("eileen",{})):return false
	# Like ordinary automatic supplies, preserve the reward above manual capacity.
	g.convoy[str(spec.route)].append(item_id)
	var taken: Dictionary = g.flags.get("story_armaments_claimed",{})
	taken[str(item_id)] = true
	g.flags.story_armaments_claimed = taken
	if announce:g.queue_pages(delivery_pages(item_id),"ARMAMENT-"+str(item_id))
	return true

static func award_clear(g, stage: int, announce: bool = true) -> void:
	for key in Items.armaments().items:
		var spec: Dictionary = Items.armaments().items[key]
		if spec.trigger=="clear" and int(spec.stage)==stage:claim(g,int(key),announce)
