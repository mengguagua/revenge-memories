extends RefCounted
## Plays decoded original body/OAM timelines. Gameplay resolves at one contact.
## Source asset/coordinate contract: data/full_animation_schema.md.

const Rules = preload("res://core/combat_rules.gd")
const FIELD := Rect2(0, 0, 256, 128)
const FPS := 60.0988
const EFFECT_PATH := "res://data/legacy/full_animation_effects.json"
static var _source_cache: Dictionary = {}

var _ui_ref: WeakRef
var ui:
	get: return _ui_ref.get_ref()
var flips: Dictionary = {}
var effects: Array = []
var target_alpha: Dictionary = {}
var missing_animations: Array[String] = []
var active_variant := ""
var active_tick := -1
var active_event: Dictionary = {}
var contact_calls := 0

func _init(owner) -> void:
	_ui_ref = weakref(owner)

func reset() -> void:
	flips.clear()
	effects.clear()
	target_alpha.clear()
	active_variant = ""
	active_tick = -1
	active_event.clear()
	contact_calls = 0

func _source() -> Dictionary:
	if _source_cache.is_empty():
		var raw = JSON.parse_string(FileAccess.get_file_as_string(EFFECT_PATH))
		if raw is Dictionary:
			_source_cache = raw
	return _source_cache

func _class(unit: Dictionary) -> int:
	var cid = int(unit.get("class_id", 0))
	# Promotion stores hero/princess identities separately from source class.
	if cid == 23: return 21
	if cid == 24: return 11
	return cid

func _source_id(unit: Dictionary) -> int:
	return int(unit.get("character_id", unit.get("name_id", 0)))

func _record_missing(message: String) -> void:
	if message in missing_animations:
		return
	missing_animations.append(message)
	push_warning("Original animation missing: " + message)

func sprite(unit: Dictionary) -> Dictionary:
	if unit.get("event_object",false):return {"path":"res://assets/battle_tiles/modules/medicine_wagon.png","frame_size":[32,16],"frames":1,"anchor":[16,16],"sequences":{"idle":[0]},"source_oam_frame_count":0}
	var side = "enemy" if str(unit.get("side", "player")) == "enemy" else "ally"
	var cid = _class(unit)
	var key = "class_%d_%s" % [cid, side]
	var battle: Dictionary = ui.graphics.get("battle", {})
	if not battle.has(key):
		_record_missing("class %d / %s" % [cid, side])
		# An explicitly missing, invisible actor is preferable to the wrong unit.
		return {"missing": true, "sequences": {"idle": [0]}, "frames": 1}
	var result: Dictionary = battle[key]
	var sid = _source_id(unit)
	var palette: Dictionary = result.get("palette_variants", {})
	var name_key = str(unit.get("name_id", sid)) if side == "enemy" else str(sid)
	if palette.has(name_key):
		result = battle[str(palette[name_key])]
	elif side == "enemy" and int(unit.get("level", 1)) >= 10 and palette.has("elite"):
		result = battle[str(palette.elite)]
	var promoted = bool(unit.get("promoted", unit.get("alm_promoted", false)))
	if side == "ally" and cid == 21 and (promoted or sid == 36 or int(unit.get("class_id", 0)) == 23):
		result = battle.get("promoted_alm_ally", result)
	elif side == "ally" and cid == 11 and (promoted or sid == 37 or int(unit.get("class_id", 0)) == 24):
		result = battle.get("promoted_celica_ally", result)
	# New recovery body sheets retain cumulative source BG tile uploads.
	# The action-specific pose is used only for the active caster.
	if str(active_event.get("attacker", "")) == str(unit.get("id", "")):
		var body_key = str(result.get("spell_body_variants", {}).get(str(int(active_event.get("weapon_index", -1))), ""))
		if not body_key.is_empty(): result = battle.get(body_key, result)
	if side == "enemy" and cid == 21:
		# L05952D entry sequence ends on pose9 intact, pose5 below52HP.
		result = result.duplicate(false)
		result.sequences = result.sequences.duplicate(true)
		result.sequences.idle = [int(result.background_frame_offset) + (5 if int(unit.get("hp", 182)) < 52 else 9)]
	if ui.has_method("_personal_battle_sprite"):result=ui.call("_personal_battle_sprite",unit,result)
	return result

func _left(unit: Dictionary, exchange: Dictionary) -> bool:
	if bool(exchange.get("support", false)):
		return str(unit.get("id", "")) == str(exchange.get("defender", "")) and str(exchange.get("attacker", "")) != str(exchange.get("defender", ""))
	return str(unit.get("side", "player")) == "enemy"

func _far_role(exchange: Dictionary) -> String:
	if int(exchange.get("distance", 1)) <= 1:
		return ""
	if bool(exchange.get("support", false)):
		return "ally"
	return "enemy" if str(exchange.get("initiative_side", "player")) == "enemy" else "ally"

func origin(unit: Dictionary, exchange: Dictionary) -> Vector2:
	var left = _left(unit, exchange)
	var far = _far_role(exchange)
	var cid = _class(unit)
	if left:
		if cid in [4, 5, 7]: return Vector2(56, 128)
		return Vector2(32 if far == "enemy" else 64, 128)
	if cid in [4, 7]: return Vector2(184, 128)
	if far == "ally": return Vector2(184 if cid in [3, 5] else 208, 128)
	return Vector2(176, 128)

func selection(event: Dictionary) -> Dictionary:
	var actor = ui.game.find_unit(str(event.attacker))
	var target = ui.game.find_unit(str(event.defender))
	var graphic = sprite(actor)
	if graphic.get("missing", false): return {"kind": "missing", "reason": "unknown class"}
	var weapon = int(event.get("weapon_index", Rules.weapon_index(actor)))
	var schedule: Dictionary = graphic.get("attack_schedule", {})
	var base = ""
	if graphic.get("weapon_variants", {}).has(str(weapon)):
		base = str(graphic.weapon_variants[str(weapon)])
	elif graphic.get("spell_variants", {}).has(str(weapon)):
		base = str(graphic.spell_variants[str(weapon)])
	elif weapon >= 23:
		return {"kind": "missing", "reason": "class %d / %s / spell %d" % [_class(actor), str(actor.side), weapon], "sprite": graphic}
	elif weapon in [1, 20, 21, 22] and _class(actor) in [12, 13, 20]:
		base = str(schedule.get("effect_variant", ""))
	elif graphic.has("personal_source_programs"):
		var kind="critical" if bool(event.get("critical",false)) else "normal"
		return {"kind":"source","key":"hunapu_"+kind,"variant":graphic.personal_source_programs[kind],"sprite":graphic}
	elif schedule.has("native_timeline"):
		return {"kind": "melee", "timeline": schedule.native_timeline, "sprite": graphic}
	else:
		return {"kind": "missing", "reason": "class %d / weapon %d has no recovered attack" % [_class(actor), weapon], "sprite": graphic}
	var key = base
	var far = _far_role(ui.combat)
	if far != "": key += "_far_" + far
	var target_x = int(origin(target, ui.combat).x)
	var heavy = target_x == (56 if _left(target, ui.combat) else 184)
	if heavy: key += "_vs_heavy"
	var variants: Dictionary = _source().get("variants", {})
	if not variants.has(key):
		return {"kind": "missing", "reason": "source variant " + key, "sprite": graphic}
	return {"kind": "source", "key": key, "variant": variants[key], "sprite": graphic}

func _vec(value) -> Vector2:
	return value if value is Vector2 else Vector2(float(value[0]), float(value[1]))

func _source_frame(event: Dictionary, frame: Dictionary, tick: int, sounds: bool) -> void:
	var id = str(event.attacker)
	ui.combat_poses[id] = int(frame.frame)
	ui.combat_offsets[id] = _vec(frame.get("offset", [0, 0]))
	flips[id] = bool(frame.get("flip", false))
	effects = frame.get("effects", []).duplicate(false)
	active_tick = tick
	if frame.has("target_palette"):
		var hidden = true
		for color in frame.target_palette:
			if int(color) not in [13, 14, 15, 29, 30, 31, 45, 46, 47, 61, 62, 63]: hidden = false
		target_alpha[str(event.defender)] = 0.0 if hidden else 1.0
	if sounds and not bool(ui.instant_mode):
		for request in frame.get("sound_requests", []):
			ui.audio.play_request(int(request))
	ui.queue_redraw()

func show_frame(event: Dictionary, tick: int) -> bool:
	# Deterministic frame selection for guarded background visual verification.
	var chosen = selection(event)
	if str(chosen.kind) != "source": return false
	var frames: Array = chosen.variant.frames
	if tick < 0 or tick >= frames.size(): return false
	active_variant = str(chosen.key)
	active_event = event.duplicate(false)
	_source_frame(event, frames[tick], tick, false)
	return true

func _contact(event: Dictionary) -> void:
	contact_calls += 1
	await ui._contact(event)

func _body_frame(event: Dictionary, frame: Dictionary) -> void:
	var actor = ui.game.find_unit(str(event.attacker))
	var offset = _vec(frame.get("offset", [0, 0]))
	if _left(actor, ui.combat): offset.x = -offset.x
	ui.combat_poses[str(event.attacker)] = int(frame.frame)
	ui.combat_offsets[str(event.attacker)] = offset
	flips[str(event.attacker)] = bool(frame.get("flip", false))
	ui.queue_redraw()

func play(event: Dictionary) -> void:
	active_event = event.duplicate(false)
	active_variant = ""
	active_tick = -1
	effects.clear()
	target_alpha.clear()
	var actor = ui.game.find_unit(str(event.attacker))
	var graphic = sprite(actor)
	var chosen = selection(event)
	var id = str(event.attacker)
	# Cost is a display update; the only gameplay commit remains _contact.
	if int(event.get("hp_cost", 0)) > 0 and (not bool(event.get("visual_only", false)) or event.has("source_hp_before")):
		ui.combat_hp[id] = maxi(0, int(event.get("source_hp_before", actor.hp)) - int(event.hp_cost))
	match str(chosen.kind):
		"source":
			active_variant = str(chosen.key)
			var variant: Dictionary = chosen.variant
			var contact = int(variant.contact_tick)
			if bool(ui.instant_mode):
				_source_frame(event, variant.frames[contact], contact, false)
				await _contact(event)
			else:
				for tick in range(variant.frames.size()):
					_source_frame(event, variant.frames[tick], tick, true)
					if tick == contact:
						await _contact(event)
					await ui._wait(1.0 / float(variant.get("native_fps", FPS)))
		"melee":
			var timeline: Dictionary = chosen.timeline
			if not bool(ui.instant_mode):
				for frame in timeline.before_contact:
					_body_frame(event, frame)
					await ui._wait(1.0 / float(timeline.get("native_fps", FPS)))
			await _contact(event)
			if not bool(ui.instant_mode):
				for frame in timeline.after_contact:
					_body_frame(event, frame)
					await ui._wait(1.0 / float(timeline.get("native_fps", FPS)))
		_:
			_record_missing(str(chosen.get("reason", "unknown source program")))
			# Preserve the actual actor silhouette. No unrelated Fire/melee asset.
			await ui._wait(0.25)
			await _contact(event)
	if event.has("source_hp_after"):
		ui.combat_hp[id] = int(event.source_hp_after)
		if int(event.source_hp_after) <= 0:
			ui.combat_fades[id] = 0.0
	ui.combat_offsets[id] = Vector2.ZERO
	ui.combat_poses[id] = int(graphic.get("sequences", {"idle": [0]}).idle[0])
	flips.erase(id)
	effects.clear()
	target_alpha.clear()
	ui.combat_message = ""
	ui.combat_hit_id = ""
	ui.queue_redraw()
	await ui._wait(0.18)

func clipped_region(graphic: Dictionary, frame: int, at: Vector2, flip: bool) -> Dictionary:
	var size = _vec(graphic.frame_size)
	var destination = Rect2(at.round(), size)
	var visible = destination.intersection(FIELD)
	if not visible.has_area(): return {}
	var offset = visible.position - destination.position
	var source_x = size.x - offset.x - visible.size.x if flip else offset.x
	return {"destination": visible, "source": Rect2(Vector2(frame * size.x + source_x, offset.y), visible.size), "flip": flip}

func _draw_frame(graphic: Dictionary, frame: int, at: Vector2, flip: bool, color: Color) -> void:
	if bool(graphic.get("missing", false)): return
	if int(graphic.get("frames",0))==1:frame=0
	var region = clipped_region(graphic, frame, at, flip)
	if region.is_empty(): return
	var destination: Rect2 = region.destination
	if flip: destination.size.x = -destination.size.x
	ui.draw_texture_rect_region(ui._tex(str(graphic.path)), destination, region.source, color)

func draw_actors() -> void:
	if ui.combat.is_empty(): return
	var a = ui.game.find_unit(str(ui.combat.attacker))
	var b = ui.game.find_unit(str(ui.combat.defender))
	var actors: Array = [b, a] if _left(b, ui.combat) else [a, b]
	var drawn: Array[String] = []
	for unit in actors:
		if unit.is_empty() or str(unit.id) in drawn: continue
		drawn.append(str(unit.id))
		var id = str(unit.id)
		var graphic = sprite(unit)
		if bool(graphic.get("missing", false)): continue
		var frame = int(ui.combat_poses.get(id, graphic.sequences.idle[0]))
		var flip = _left(unit, ui.combat) != bool(flips.get(id, false))
		var at = origin(unit, ui.combat) + _vec(ui.combat_offsets.get(id, Vector2.ZERO)) - _vec(graphic.anchor)
		if flip and frame < int(graphic.get("source_oam_frame_count", 0)):
			at += _vec(graphic.get("oam_flip_origin_offset", [0, 0]))
		var color = Color.WHITE
		color.a = float(ui.combat_fades.get(id, 1.0)) * float(target_alpha.get(id, 1.0))
		if str(ui.combat_hit_id) == id and float(ui.combat_hit_time) > 0.0 and int(float(ui.elapsed) * 30.0) % 2 == 0:
			color = Color(0.35, 0.35, 0.35, color.a)
		_draw_frame(graphic, frame, at, flip, color)
	if not effects.is_empty():
		var sprites: Dictionary = _source().sprites
		for effect in effects:
			var graphic: Dictionary = sprites[str(effect.sprite)]
			var at = _vec(effect.position) - _vec(graphic.anchor)
			if bool(effect.flip): at += _vec(graphic.get("flip_origin_offset", [0, 0]))
			_draw_frame(graphic, 0, at, bool(effect.flip), Color.WHITE)
