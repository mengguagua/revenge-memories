extends RefCounted
## Platforms are terrain. The occupant's live position is the only state.

const SPRITE = "res://assets/battlefield-0.3.0/modules/arrow_platform.png"
const GUIDE = "弓手站上箭台，射程变为1～6格、力量减2。两边的弓手都能用，离开箭台即恢复。"

static func has_at(stage: Dictionary, cell: Vector2i) -> bool:
	for point in stage.get("arrow_platforms", []):
		if cell == Vector2i(int(point[0]), int(point[1])):return true
	return false

static func combatant(stage: Dictionary, unit: Dictionary, cell: Vector2i) -> Dictionary:
	if int(unit.get("class_id", 0)) not in [12, 13, 20] or not has_at(stage, cell):return unit
	var result := unit.duplicate()
	result.fixed_arrow_platform = true
	return result

static func props(stage: Dictionary) -> Array:
	var result := []
	for point in stage.get("arrow_platforms", []):
		result.append({"path":SPRITE,"position":[int(point[0])*16,int(point[1])*16]})
	return result
