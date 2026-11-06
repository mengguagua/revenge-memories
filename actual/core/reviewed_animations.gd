extends RefCounted
## Selected art only. The existing controller owns combat contacts and save data.
static var cache: Dictionary = {}
const Programs = preload("res://core/animation_programs.gd")

static func data() -> Dictionary:
	if cache.is_empty():
		cache = Programs.full_data("reviewed")
	return cache

static func metadata() -> Dictionary:
	return Programs.metadata("reviewed")

static func variant(name: String) -> Dictionary:
	return Programs.variant("reviewed",name)

static func key(actor: Dictionary) -> String:
	if actor.get("side", "player") != "enemy":
		var promoted = int(actor.get("class_id", 0)) in [23, 24] or bool(actor.get("promoted", actor.get("alm_promoted", false)))
		if str(actor.get("id", "")) == "eileen": return "eileen_promoted" if promoted else "eileen"
		if int(actor.get("class_id", 0)) in [21, 23] and promoted: return "23_ally"
	return str(int(actor.get("class_id", 0))) + ("_enemy" if actor.get("side", "player") == "enemy" else "_ally")

static func map_sprite(kind: String, actor: Dictionary) -> Dictionary:
	if actor.get("event_object", false): return {}
	var context = {"map": "tactical-idle", "map_move": "tactical-walk", "hub": "story", "world": "world"}.get(kind, "")
	if context.is_empty(): return {}
	if actor.get("neutral", false):
		# Named prospective companions retain their approved profession body
		# before recruitment; neutral is a control/AI flag, not civilian artwork.
		var npc_class={"hervi":15,"fula":18,"lena":3,"beck":12}
		if context in ["tactical-idle","tactical-walk"] and int(actor.get("class_id",0))==int(npc_class.get(str(actor.get("id","")),-1)):
			return metadata().maps.get(key(actor),{}).get(context,{}).duplicate(true)
		# These two escorts reuse the approved mercenary art without changing class or AI.
		if context in ["tactical-idle", "tactical-walk"] and int(actor.get("class_id", 0)) == 14 and actor.get("side", "player") == "player" and str(actor.get("id", "")) in ["M11_refugees0", "M11_refugees1"]:
			return metadata().maps.get("8_neutral", {}).get(context, {}).duplicate(false)
		return {}
	# Approved friendly archers and spearmen use their static tactical idle identity.
	var class_story = kind == "hub" and int(actor.get("class_id", 0)) in [6, 12] and actor.get("side", "player") == "player"
	if kind in ["hub", "world"] and str(actor.get("id", "")) not in ["hunapu","eileen"] and not class_story: return {}
	return metadata().maps.get(key(actor), {}).get(context, {}).duplicate(false)

static func travel_frame(art: Dictionary, direction: String, clock: float, walking: bool) -> int:
	var cycle:Dictionary=art.get("direction_cycles",{}).get(direction,{})
	if cycle.is_empty():return int(art.directions[direction][(int(clock*60.0988)>>4)&1 if walking else 0])
	if not walking:return int(cycle.frames[0])
	var period=0
	for ticks in cycle.ticks:period+=int(ticks)
	var tick=int(clock*60.0988)%maxi(1,period)
	for n in range(cycle.frames.size()):
		if tick<int(cycle.ticks[n]):return int(cycle.frames[n])
		tick-=int(cycle.ticks[n])
	return int(cycle.frames[0])

static func _safe_body(actor:Dictionary,original:Dictionary)->Dictionary:
	var path=str(original.get("path",""))
	if not path.is_empty() and not path.begins_with("res://assets/original/") and ResourceLoader.exists(path):
		var safe=original.duplicate(false);safe.campaign_safe_idle=true;return safe
	var side="enemy" if actor.get("side","")=="enemy" else "ally"
	var candidate:Dictionary=metadata().battle.get(key(actor),metadata().battle["6_"+side])
	return candidate.duplicate(true)

static func battle(actor: Dictionary, original: Dictionary, event: Dictionary) -> Dictionary:
	if actor.get("event_object", false): return _safe_body(actor,original)
	var art: Dictionary = metadata().battle.get(key(actor), {})
	if art.is_empty() or str(art.get("path","")).begins_with("res://assets/original/") or not ResourceLoader.exists(str(art.get("path",""))): return _safe_body(actor,original)
	if str(event.get("attacker", "")) == str(actor.get("id", "")):
		var weapon = str(int(event.get("weapon_index", -1)))
		var base = str(original.get("weapon_variants", {}).get(weapon, original.get("spell_variants", {}).get(weapon, ""))).trim_prefix("fe2_")
		# Shared native programs may have a different source class prefix. Prefer
		# this profession's reviewed spell rather than reverting to its old body.
		var own_spell = "class_%d_%s_item_%s" % [int(art.reviewed_class_id), str(art.reviewed_side), weapon]
		if not base.is_empty() and not art.reviewed_variants.has(base) and not art.reviewed_variants.has(own_spell): return _safe_body(actor,original)
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
	var own_spell = "class_%d_%s_item_%d" % [int(graphic.reviewed_class_id), str(graphic.reviewed_side), weapon]
	if available.has(own_spell): base = own_spell
	var silver_bow = "class_%d_%s_silver_bow" % [int(graphic.reviewed_class_id),str(graphic.reviewed_side)]
	if weapon == 22 and available.has(silver_bow): base = silver_bow
	if base.is_empty() and weapon in [1, 20, 21, 22] and int(graphic.reviewed_class_id) in [12, 13, 20]:
		base = str(graphic.get("attack_schedule", {}).get("effect_variant", "")).trim_prefix("fe2_")
	if base.is_empty():
		base = "original_class_" + str(int(graphic.reviewed_class_id)) + ("_enemy" if graphic.reviewed_side == "enemy" else "")
		var critical = base + "_critical"
		if event.get("critical", false) and available.has(critical):
			base = critical
		elif graphic.get("reviewed_promoted", false) and available.has(base + "_promoted"):
			base += "_promoted"
		else:
			base += "_normal"
	else:
		if not far.is_empty(): base += "_far_" + far
		if heavy: base += "_vs_heavy"
	if not available.has(base): return {}
	var runtime_key: String = available[base]
	return {"kind": "source", "key": runtime_key, "variant": variant(runtime_key), "sprite": graphic}
