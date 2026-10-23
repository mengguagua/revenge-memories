extends RefCounted
## Campaign-only professions overlay the source class, preserving spell slots,
## growth/EXP rules and animation bindings without repurposing legacy IDs 23/24.
const DEFINITIONS = {
	"hunapu": {"key":"dawn_warrior", "name":"破晓勇士", "character_id":1, "class_id":21, "move":6,
		"bases":{"max_hp":36,"strength":16,"skill":14,"speed":14,"luck":10,"defence":10}},
	"eileen": {"key":"light_guide", "name":"引光剑使", "character_id":2, "class_id":11, "move":5,
		"bases":{"max_hp":34,"strength":14,"skill":12,"speed":12,"luck":12,"defence":8,"resistance":10}}
}

static func definition(unit: Dictionary) -> Dictionary:
	var spec: Dictionary = DEFINITIONS.get(str(unit.get("id","")),{})
	if spec.is_empty() or unit.get("side","") != "player" or unit.get("temporary",false) or unit.get("neutral",false):return {}
	if int(unit.get("class_id",0)) != int(spec.class_id) or int(unit.get("character_id",0)) != int(spec.character_id):return {}
	return spec

static func advanced(unit: Dictionary) -> bool:
	var spec = definition(unit)
	return not spec.is_empty() and unit.get("hero_profession","") == spec.key and unit.get("promoted",false) == true

static func name(unit: Dictionary) -> String:
	return str(definition(unit).name) if advanced(unit) else ""

static func apply(unit: Dictionary, allow_injured: bool = false) -> bool:
	var spec = definition(unit)
	if spec.is_empty() or advanced(unit):return false
	if not allow_injured and (int(unit.get("hp",0)) <= 0 or unit.get("dying",false) or unit.get("dead",false)):return false
	# Only permanent values enter the minima. Current HP, equipment, training,
	# level, EXP and personal growth rates are deliberately untouched.
	for key in spec.bases:unit[key] = maxi(int(unit.get(key,0)),int(spec.bases[key]))
	if spec.bases.has("resistance"):
		unit.personal_resistance = maxi(int(unit.get("personal_resistance",unit.resistance)),int(spec.bases.resistance))
	unit.move = int(spec.move)
	unit.promoted = true
	unit.hero_profession = spec.key
	return true

static func upgrade_checkpoint(state: Dictionary) -> void:
	# Each retry snapshot uses its own historical flags, never the live flags.
	var flags: Dictionary = state.get("flags",{})
	var members: Array = state.get("roster",{}).values()
	members.append_array(state.get("units",[]))
	for unit in members:
		if definition(unit).is_empty():continue
		if flags.get("chapter4_promoted_"+str(unit.id),false) or unit.get("promoted",false):apply(unit,true)
	var snapshot: Dictionary = state.get("battle_start_snapshot",{})
	if not snapshot.is_empty():upgrade_checkpoint(snapshot)

static func valid_marker(unit: Dictionary) -> bool:
	return not unit.has("hero_profession") or (unit.hero_profession is String and advanced(unit))

static func summary(unit: Dictionary) -> String:
	if not advanced(unit):return ""
	return "术法精熟 · 攻击法术减耗1" if str(unit.id)=="eileen" else "剑弓兼用 · 基础移动6"
