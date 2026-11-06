extends RefCounted
## Plays decoded original body/OAM timelines. Gameplay resolves at one contact.
## Source asset/coordinate contract: data/full_animation_schema.md.

const Rules = preload("res://core/combat_rules.gd")
const Innate = preload("res://core/innate_attack_animation.gd")
const CampaignEffects=preload("res://core/campaign_effects.gd")
const Reviewed = preload("res://core/reviewed_animations.gd")
const CriticalCinema=preload("res://core/critical_cinema.gd")
const Counter = preload("res://core/counter_animation.gd")
const MechanicalArt=preload("res://core/mechanical_art.gd")
const FIELD := Rect2(0, 0, 256, 128)
const FPS := 60.0988
const EFFECT_PATH := "res://data/legacy/full_animation_effects.json"
static var _source_cache: Dictionary = {}
static var _source_metadata_cache: Dictionary = {}
static var _costume_variant_cache: Dictionary = {}

var _ui_ref: WeakRef
var ui:
	get: return _ui_ref.get_ref()
var flips: Dictionary = {}
var effects: Array = []
var target_alpha: Dictionary = {}
var pose_alpha: Dictionary = {}
var pose_tint: Dictionary = {}
var missing_animations: Array[String] = []
var active_variant := ""
var active_tick := -1
var active_event: Dictionary = {}
var contact_calls := 0
var cinema

func _init(owner) -> void:
	_ui_ref = weakref(owner)
	cinema=CriticalCinema.new(owner)

func reset() -> void:
	if cinema!=null:cinema.reset()
	flips.clear()
	effects.clear()
	target_alpha.clear()
	pose_alpha.clear()
	pose_tint.clear()
	active_variant = ""
	active_tick = -1
	active_event.clear()
	contact_calls = 0

func _source() -> Dictionary:
	if _source_cache.is_empty():
		_source_cache = Reviewed.Programs.full_data("legacy").duplicate(false)
		_source_cache.variants = _source_cache.variants.duplicate(false)
		var original = Reviewed.Programs.full_data("party")
		for key in original.variants:_source_cache.variants["fe2_"+str(key)] = original.variants[key]
		_source_cache.sprites = _source_metadata().sprites
	return _source_cache

func _source_metadata() -> Dictionary:
	if _source_metadata_cache.is_empty():
		_source_metadata_cache={"sprites":CampaignEffects.sprites().duplicate(false)}
		_source_metadata_cache.sprites.merge(Innate.effect_sprites(),true)
		_source_metadata_cache.sprites.merge(MechanicalArt.data().effects,true)
	return _source_metadata_cache

func _source_variant(key: String) -> Dictionary:
	return Reviewed.Programs.variant("party",key.trim_prefix("fe2_")) if key.begins_with("fe2_") else Reviewed.Programs.variant("legacy",key)

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
	if Rules.Body.Mechanical.is_puppet(unit):return MechanicalArt.battle(unit)
	if unit.get("event_object",false):return {"path":"res://assets/battle_tiles/modules/medicine_wagon.png","frame_size":[32,16],"frames":1,"anchor":[16,16],"sequences":{"idle":[0]},"source_oam_frame_count":0}
	var side = "enemy" if str(unit.get("side", "player")) == "enemy" else "ally"
	var cid = _class(unit)
	var key = "class_%d_%s" % [cid, side]
	var battle: Dictionary = ui.graphics.get("battle", {})
	if not battle.has(key):return ui.CampaignArt.battle(unit)
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
	if side == "enemy" and cid == 21 and _source_id(unit)==167:
		# L05952D entry sequence ends on pose9 intact, pose5 below52HP.
		result = result.duplicate(false)
		result.sequences = result.sequences.duplicate(true)
		result.sequences.idle = [int(result.background_frame_offset) + (5 if int(unit.get("hp", 182)) < 52 else 9)]
	if ui.has_method("_personal_battle_sprite"):result=ui.call("_personal_battle_sprite",unit,result)
	return Innate.sprite(unit,Counter.sprite(unit,Reviewed.battle(unit, result, active_event),active_event))

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
	if Rules.Body.is_body(unit):return Innate.safe_origin(sprite(unit),Vector2(32 if left and far=="enemy" else 64 if left else 208 if far=="ally" else 176,128))
	if left:
		if cid in [4, 5, 7]: return Vector2(56, 128)
		return Vector2(32 if far == "enemy" else 64, 128)
	if cid in [4, 7]: return Vector2(184, 128)
	if far == "ally": return Vector2(184 if cid in [3, 5] else 208, 128)
	return Vector2(176, 128)

func selection(event: Dictionary) -> Dictionary:
	var mechanical_actor=ui.game.find_unit(str(event.attacker))
	if Rules.Body.Mechanical.is_puppet(mechanical_actor):
		return MechanicalArt.selection(mechanical_actor,event,origin(mechanical_actor,ui.combat),origin(ui.game.find_unit(str(event.defender)),ui.combat),_left(mechanical_actor,ui.combat))
	var critical_key=CriticalCinema.case_for(ui.game.find_unit(str(event.attacker)),event)
	if not critical_key.is_empty():return {"kind":"critical_cinema","key":critical_key}
	var actor = ui.game.find_unit(str(event.attacker))
	var target = ui.game.find_unit(str(event.defender))
	var graphic = sprite(actor)
	if graphic.get("campaign_safe_idle",false):return {"kind":"campaign_idle","sprite":graphic}
	if graphic.get("missing", false): return {"kind": "missing", "reason": "unknown class"}
	var weapon = int(event.get("weapon_index", Rules.weapon_index(actor)))
	if Rules.Body.is_body(actor):
		_source_metadata()
		return Innate.selection(graphic,event,origin(actor,ui.combat),origin(target,ui.combat),_left(actor,ui.combat))
	if graphic.has("reviewed_variants"):
		_source_metadata()
		var target_x = int(origin(target, ui.combat).x)
		var heavy = target_x == (56 if _left(target, ui.combat) else 184)
		var counter=Counter.selection(graphic,_far_role(ui.combat),heavy)
		if not counter.is_empty():return counter
		var reviewed = Reviewed.selection(graphic, event, weapon, _far_role(ui.combat), heavy)
		if not reviewed.is_empty(): return reviewed
	return {"kind":"campaign_idle","sprite":graphic}
func _vec(value) -> Vector2:
	return value if value is Vector2 else Vector2(float(value[0]), float(value[1]))

func _source_frame(event: Dictionary, frame: Dictionary, tick: int, sounds: bool) -> void:
	var id = str(event.attacker)
	ui.combat_poses[id] = int(frame.frame)
	ui.combat_offsets[id] = _vec(frame.get("offset", [0, 0]))
	ui.combat_offsets[id].x += float(frame.get("shake",0))
	flips[id] = bool(frame.get("flip", false))
	pose_alpha[id] = float(frame.get("alpha",1.0))
	pose_tint[id] = float(frame.get("tint",1.0))
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
	active_event = event.duplicate(false)
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

func reaction(unit_id: String, kind: String) -> bool:
	var unit:Dictionary=ui.game.find_unit(unit_id)
	if unit.is_empty():return false
	# Korlan falls in the map-scale farewell right after this exchange. Keep
	# the fatal hit intact, without making him vanish and reappear to speak.
	if kind=="exit" and ui.game.stage_id==105 and unit_id=="M15_boss":return true
	var graphic=sprite(unit)
	var mechanical=Rules.Body.Mechanical.is_puppet(unit)
	if mechanical and kind not in ["hit","exit","part_break","reflection"]:return false
	var key="mechanical" if mechanical else str(graphic.get("reviewed_reactions",{}).get(kind,""))
	if key.is_empty():return false
	var variant:Dictionary=MechanicalArt.reaction(unit,kind) if mechanical else Reviewed.variant(key)
	var saved_pose=int(ui.combat_poses.get(unit_id,graphic.sequences.idle[0]))
	var saved_offset:Vector2=ui.combat_offsets.get(unit_id,Vector2.ZERO)
	var saved_flip=bool(flips.get(unit_id,graphic.get("idle_flip",false)))
	var saved_effects=effects.duplicate(false)
	var saved_tick=active_tick
	if not bool(ui.instant_mode):
		var deadline=float(Time.get_ticks_usec())
		for row in variant.frames:
			_source_frame({"attacker":unit_id},row,saved_tick,false)
			deadline+=1000000.0/(float(variant.native_fps)*float(ui.effective_animation_speed()))
			while float(Time.get_ticks_usec())<deadline:await ui.get_tree().process_frame
	ui.combat_poses[unit_id]=saved_pose
	ui.combat_offsets[unit_id]=saved_offset
	flips[unit_id]=saved_flip
	pose_alpha.erase(unit_id);pose_tint.erase(unit_id)
	effects=saved_effects;active_tick=saved_tick
	if kind=="exit":ui.combat_fades[unit_id]=0.0
	ui.queue_redraw()
	return true

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
		"critical_cinema":
			await cinema.play(event)
		"source":
			active_variant = str(chosen.key)
			var variant: Dictionary = chosen.variant
			var contact = int(variant.contact_tick)
			if bool(ui.instant_mode):
				_source_frame(event, variant.frames[contact], contact, false)
				await _contact(event)
			else:
				# A deadline clock avoids one Timer quantization error per NES
				# tick. Contact feedback pauses this clock, as in the original.
				var deadline=float(Time.get_ticks_usec())
				for tick in range(variant.frames.size()):
					_source_frame(event, variant.frames[tick], tick, true)
					if tick == contact:
						var before_contact=Time.get_ticks_usec()
						await _contact(event)
						deadline+=float(Time.get_ticks_usec()-before_contact)
					var speed=float(ui.effective_animation_speed())
					if not graphic.get("original_motion",false):
						await ui._wait(1.0/float(variant.get("native_fps",FPS)))
						continue
					deadline+=1000000.0/(float(variant.get("native_fps",FPS))*speed)
					while float(Time.get_ticks_usec())<deadline:await ui.get_tree().process_frame
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
		"campaign_idle":
			await ui._wait(0.25)
			await _contact(event)
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
	pose_alpha.erase(id)
	pose_tint.erase(id)
	effects.clear()
	target_alpha.clear()
	ui.combat_message = ""
	ui.combat_hit_id = ""
	if ui.audio.has_method("finish_combat_sfx"):ui.audio.finish_combat_sfx()
	ui.queue_redraw()
	await ui._wait(0.18)

func clipped_region(graphic: Dictionary, frame: int, at: Vector2, flip: bool) -> Dictionary:
	var density = maxf(1.0, float(graphic.get("native_density", 1)))
	var source_size = _vec(graphic.frame_size)
	var size = _vec(graphic.logical_frame_size) if graphic.has("logical_frame_size") else source_size / density
	var axes_density=source_size/size
	var destination = Rect2(at.round(), size)
	var visible = destination.intersection(FIELD)
	if not visible.has_area(): return {}
	var offset = visible.position - destination.position
	var source_x = size.x - offset.x - visible.size.x if flip else offset.x
	var columns=int(graphic.get("columns",graphic.get("frames",1)))
	return {"destination": visible, "source": Rect2(Vector2((frame%columns)*source_size.x+source_x*axes_density.x,floori(float(frame)/columns)*source_size.y+offset.y*axes_density.y),visible.size*axes_density),"flip":flip}

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
		var flip = Innate.horizontal_flip(graphic,_left(unit,ui.combat),bool(flips.get(id,graphic.get("idle_flip",false)))) if Rules.Body.is_body(unit) else _left(unit, ui.combat) != bool(flips.get(id, graphic.get("idle_flip",false)))
		var at = origin(unit, ui.combat) + _vec(ui.combat_offsets.get(id, Vector2.ZERO)) - _vec(graphic.anchor)
		if flip and frame < int(graphic.get("source_oam_frame_count", 0)):
			at += _vec(graphic.get("oam_flip_origin_offset", [0, 0]))
		var shade=float(pose_tint.get(id,1.0))
		var color = Color(shade,shade,shade,1.0)
		color.a = float(ui.combat_fades.get(id, 1.0)) * float(target_alpha.get(id, 1.0)) * float(pose_alpha.get(id,1.0))
		if str(ui.combat_hit_id) == id and float(ui.combat_hit_time) > 0.0 and int(float(ui.elapsed) * 30.0) % 2 == 0:
			color = Color(0.35, 0.35, 0.35, color.a)
		_draw_frame(graphic, frame, at, flip, color)
	if not effects.is_empty():
		var sprites: Dictionary = _source_metadata().sprites
		for effect in effects:
			var graphic: Dictionary = CampaignEffects.graphic(str(effect.sprite),active_variant)
			if graphic.is_empty():graphic=sprites.get(str(effect.sprite),{})
			if graphic.is_empty():continue
			var point=effect_position(effect)
			var role=str(graphic.get("campaign_anchor_role",""))
			if not role.is_empty() and not active_event.is_empty():
				var owner=ui.game.find_unit(str(active_event.defender if role=="defender" else active_event.attacker))
				if not owner.is_empty():point=origin(owner,ui.combat)+(Vector2(0,-52) if role=="attacker_charge" else Vector2.ZERO)
			var at = point - _vec(graphic.anchor)
			if bool(effect.flip): at += _vec(graphic.get("flip_origin_offset", [0, 0]))
			var tint=effect.get("tint",[1,1,1,1])
			_draw_frame(graphic, 0, at, bool(effect.flip), Color(float(tint[0]),float(tint[1]),float(tint[2]),float(tint[3])))

func effect_position(effect: Dictionary) -> Vector2:
	# Review-only example targets never ship. Engulf the real defender at its
	# current battle origin; its existing body, HP and fade remain authoritative.
	if effect.get("bind_target", false) and not active_event.is_empty():
		var target=ui.game.find_unit(str(active_event.get("defender", "")))
		if not target.is_empty():
			return origin(target,ui.combat)+_vec(ui.combat_offsets.get(str(target.id),Vector2.ZERO))
	return _vec(effect.position)
