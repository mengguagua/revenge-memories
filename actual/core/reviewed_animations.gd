extends RefCounted
## Selected art only. The existing controller owns combat contacts and save data.
static var cache: Dictionary = {}

static func data() -> Dictionary:
	if cache.is_empty():
		cache = JSON.parse_string(FileAccess.get_file_as_string("res://data/reviewed_animations.json"))
	return cache

static func key(actor: Dictionary) -> String:
	return str(int(actor.get("class_id", 0))) + ("_enemy" if actor.get("side", "player") == "enemy" else "_ally")

static func map_sprite(kind: String, actor: Dictionary) -> Dictionary:
	if actor.get("event_object", false) or actor.get("neutral", false): return {}
	if int(actor.get("class_id", 0)) == 21 and bool(actor.get("promoted", actor.get("alm_promoted", false))): return {}
	var context = {"map": "tactical-idle", "map_move": "tactical-walk", "hub": "story", "world": "world"}.get(kind, "")
	if context.is_empty(): return {}
	# Story identity is personal; class samples must never replace other named people.
	if kind in ["hub", "world"] and str(actor.get("id", "")) != "hunapu": return {}
	return data().maps.get(key(actor), {}).get(context, {}).duplicate(false)

static func battle(actor: Dictionary, original: Dictionary, event: Dictionary) -> Dictionary:
	if actor.get("event_object", false): return original
	# The reviewed Hunapu atlas explicitly includes the promoted source program.
	var battle_key = "21_ally" if int(actor.get("class_id", 0)) == 23 and actor.get("side", "player") != "enemy" else key(actor)
	var art: Dictionary = data().battle.get(battle_key, {})
	if art.is_empty(): return original
	if str(event.get("attacker", "")) == str(actor.get("id", "")):
		var weapon = str(int(event.get("weapon_index", -1)))
		var base = str(original.get("weapon_variants", {}).get(weapon, original.get("spell_variants", {}).get(weapon, ""))).trim_prefix("fe2_")
		if not base.is_empty() and not art.reviewed_variants.has(base): return original
	var result = original.duplicate(false)
	result.merge(art, true)
	result.reviewed_promoted = int(actor.get("class_id", 0)) == 23 or bool(actor.get("promoted", actor.get("alm_promoted", false)))
	# Selected full-body source IDs replace the old cumulative body atlas mapping.
	result.erase("costume_variant_frames")
	return result

static func selection(graphic: Dictionary, event: Dictionary, weapon: int, far: String, heavy: bool) -> Dictionary:
	if not graphic.has("reviewed_variants"): return {}
	var available: Dictionary = graphic.reviewed_variants
	var base = str(graphic.get("weapon_variants", {}).get(str(weapon), graphic.get("spell_variants", {}).get(str(weapon), ""))).trim_prefix("fe2_")
	if weapon == 21 and available.has("class_12_ally_silver_bow"): base = "class_12_ally_silver_bow"
	if base.is_empty() and weapon in [1, 20, 21, 22] and int(graphic.reviewed_class_id) in [12, 13, 20]:
		base = str(graphic.get("attack_schedule", {}).get("effect_variant", "")).trim_prefix("fe2_")
	if base.is_empty():
		base = "original_class_" + str(int(graphic.reviewed_class_id)) + ("_enemy" if graphic.reviewed_side == "enemy" else "")
		var critical = base + "_critical"
		if graphic.get("reviewed_promoted", false) and available.has(base + "_promoted"):
			base += "_promoted"
		else:
			base = critical if event.get("critical", false) and available.has(critical) else base + "_normal"
	else:
		if not far.is_empty(): base += "_far_" + far
		if heavy: base += "_vs_heavy"
	if not available.has(base): return {}
	var runtime_key: String = available[base]
	return {"kind": "source", "key": runtime_key, "variant": data().variants[runtime_key], "sprite": graphic}
