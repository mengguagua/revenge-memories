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
const ReviewFx = preload("res://core/reviewed_battle_fx.gd")
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
var review_fx: ReviewFx
var _reaction_actor := ""
var _reaction_frame: Dictionary = {}
var _review_trail: Array[Dictionary] = []

func _init(owner) -> void:
	_ui_ref = weakref(owner)
	cinema=CriticalCinema.new(owner)
	review_fx = ReviewFx.new(owner)

func reset() -> void:
	if cinema!=null:cinema.reset()
	review_fx.reset()
	_review_trail.clear()
	_reaction_actor = ""
	_reaction_frame = {}
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
		_source_metadata_cache.sprites.merge(MechanicalArt.trio_data().effects,true)
		for name in ReviewFx.data().water:
			var graphic: Dictionary = _source_metadata_cache.sprites[name].duplicate(false)
			graphic.path = ReviewFx.data().water[name]
			_source_metadata_cache.sprites[name] = graphic
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
	if review_fx.plan.get("ghosts",false) and not review_fx.contacted:
		_review_trail.append({"time":review_fx.clock,"frame":int(frame.frame),"offset":ui.combat_offsets[id],"flip":flips[id]})
		while _review_trail.size()>1 and float(_review_trail[1].time)<review_fx.clock-.22:
			_review_trail.pop_front()
	if frame.has("target_palette"):
		var hidden = true
		for color in frame.target_palette:
			if int(color) not in [13, 14, 15, 29, 30, 31, 45, 46, 47, 61, 62, 63]: hidden = false
		target_alpha[str(event.defender)] = 0.0 if hidden else 1.0
	if sounds and not bool(ui.instant_mode):
		for request in frame.get("sound_requests", []):
			# Reviewed cues are registered to this source program's phases.
			# Legacy stop requests would cut the continuous fireball cue short.
			if not review_fx.plays_audio() or ui.audio.full_manifest.get("music_by_request",{}).has("%02X" % int(request)):
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
	if not cinema.active and not ui.instant_mode:
		review_fx.contact()
		_review_contact(event)
	await ui._contact(event)

func _review_contact(event: Dictionary) -> void:
	if not event.has("hp_before") or event.get("visual_only",false):
		return
	var actor: Dictionary = ui.game.find_unit(str(event.attacker))
	var target: Dictionary = ui.game.find_unit(str(event.defender))
	var target_at := origin(target,ui.combat)
	var facing_left := origin(actor,ui.combat).x > target_at.x
	if not event.get("hit",true):
		review_fx.extra("dust",target_at+Vector2(0,-4),.04,false,.65)
		return
	var lost := int(event.hp_before)-int(event.hp_after)
	if not str(event.get("target_part","")).is_empty():
		lost = int(event.part_hp_before)-int(event.part_hp_after)
		if lost > 0 and int(event.part_hp_after) == 0 and not MechanicalArt.trio(target):
			var core := Rules.Body.Mechanical.is_titan(target)
			review_fx.extra("legacy-core" if core else "legacy-cannon",
				target_at+Vector2(0,-25 if core else -13),.30,false,.9)
	elif active_variant == "mechanical_cannon" and lost > 0:
		review_fx.extra("legacy-water",target_at+Vector2(0,-8),0.0,false,.9)
	elif review_fx.plan.is_empty() and lost > 0:
		review_fx.extra("hit",target_at+Vector2(0,-2),0.0,facing_left,.86)
	if lost > 0 and event.get("critical",false) and CriticalCinema.is_hero(actor):
		review_fx.float_damage(lost,target_at+Vector2(0,-33))

func hit_reaction_duration(unit: Dictionary) -> float:
	var graphic := sprite(unit)
	var variant: Dictionary
	if Rules.Body.Mechanical.is_puppet(unit):
		variant = MechanicalArt.reaction(unit,"hit",origin(unit,ui.combat),_left(unit,ui.combat))
	else:
		var key := str(graphic.get("reviewed_reactions",{}).get("hit",""))
		variant = {} if key.is_empty() else Reviewed.variant(key)
	return 11.0/FPS if variant.is_empty() else float(variant.frames.size())/float(variant.native_fps)

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
	var variant:Dictionary=MechanicalArt.reaction(unit,kind,origin(unit,ui.combat),_left(unit,ui.combat)) if mechanical else Reviewed.variant(key)
	if not bool(ui.instant_mode):
		_reaction_actor = unit_id
		var deadline=float(Time.get_ticks_usec())
		for row in variant.frames:
			_reaction_frame = row
			ui.queue_redraw()
			deadline+=1000000.0/(float(variant.native_fps)*float(ui.effective_animation_speed()))
			while float(Time.get_ticks_usec())<deadline:await ui.get_tree().process_frame
		_reaction_actor = ""
		_reaction_frame = {}
	if kind.begins_with("part_break") or kind=="revive":
		ui.combat_poses[unit_id]=int(sprite(unit).sequences.idle[0])
	if kind=="exit":ui.combat_fades[unit_id]=0.0
	ui.queue_redraw()
	return true

func _source_contact(event: Dictionary, pending: Array[bool]) -> void:
	await _contact(event)
	pending[0] = false

func _finish_source_pose(id: String, graphic: Dictionary) -> void:
	ui.combat_offsets[id] = Vector2.ZERO
	ui.combat_poses[id] = int(graphic.get("sequences", {"idle": [0]}).idle[0])
	flips.erase(id)
	pose_alpha.erase(id)
	pose_tint.erase(id)
	effects.clear()
	target_alpha.clear()
	ui.queue_redraw()

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
	var recipe := ReviewFx.puppet_plan(str(chosen.puppet_fx),chosen.variant) if chosen.has("puppet_fx") else ReviewFx.battle_plan(str(chosen.get("key","")),event)
	review_fx.reset()
	_review_trail.clear()
	if not recipe.is_empty():
		var target: Dictionary = ui.game.find_unit(str(event.defender))
		review_fx.prepare(recipe,event,origin(actor,ui.combat),origin(target,ui.combat))
	# Cost is a display update; the only gameplay commit remains _contact.
	if int(event.get("hp_cost", 0)) > 0 and (not bool(event.get("visual_only", false)) or event.has("source_hp_before")):
		ui.combat_hp[id] = maxi(0, int(event.get("source_hp_before", actor.hp)) - int(event.hp_cost))
	var pending: Array[bool] = [false]
	match str(chosen.kind):
		"critical_cinema":
			await cinema.play(event)
		"source":
			active_variant = str(chosen.key)
			var variant: Dictionary = chosen.variant
			var contact = int(variant.contact_tick)
			var fps := float(variant.get("native_fps",FPS))
			var medusa := int(event.get("weapon_index",0)) == 34
			if bool(ui.instant_mode):
				_source_frame(event, variant.frames[contact], contact, false)
				await _contact(event)
			else:
				# Run the source through recovery while the separate hit reaction
				# and HP display play. A paused source would revive its contact
				# frame or projectile after the HP display finishes.
				var deadline=float(Time.get_ticks_usec())
				var original_motion := bool(graphic.get("original_motion",false))
				for tick in range(variant.frames.size()):
					# Compress Medusa's travel and sustained gaze. Leave the
					# opening cue, final flash, reaction and HP clock at normal speed.
					var rate := 1.0
					if medusa and tick/fps >= 1.12 and (contact-tick)/fps > .24:
						rate = 2.0 if tick/fps < 2.55 else 4.4
					review_fx.source_tick(tick,contact,rate)
					_source_frame(event, variant.frames[tick], tick, true)
					if tick == contact:
						if not original_motion:deadline=float(Time.get_ticks_usec())
						pending[0] = true
						_source_contact(event,pending)
					var speed=float(ui.effective_animation_speed())
					if not original_motion and tick < contact:
						await ui._wait(1.0/(fps*rate))
						continue
					deadline+=1000000.0/(fps*speed*rate)
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
	_finish_source_pose(id,graphic)
	while pending[0]:await ui.get_tree().process_frame
	if event.has("source_hp_after"):
		ui.combat_hp[id] = int(event.source_hp_after)
		if int(event.source_hp_after) <= 0:
			ui.combat_fades[id] = 0.0
	ui.combat_message = ""
	ui.combat_hit_id = ""
	if not ui.instant_mode and review_fx.contacted and not review_fx.plan.is_empty():
		await ui._wait(minf(.8,review_fx.remaining()))
	review_fx.reset()
	_review_trail.clear()
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

func _draw_review_trail(unit: Dictionary, graphic: Dictionary) -> void:
	if _review_trail.is_empty() or review_fx.clock>=-.04:
		return
	var base := origin(unit,ui.combat)-_vec(graphic.anchor)
	var current: Vector2 = ui.combat_offsets.get(str(unit.id),Vector2.ZERO)
	for style in [[.20,.10],[.10,.19]]:
		var old: Dictionary = _review_trail[0]
		for pose in _review_trail:
			if float(pose.time)>review_fx.clock-float(style[0]):break
			old=pose
		var offset: Vector2 = old.offset
		if absf(current.x-offset.x)<5.0:continue
		var flip := _left(unit,ui.combat) != bool(old.flip)
		var at := base+offset
		if flip and int(old.frame)<int(graphic.get("source_oam_frame_count",0)):
			at+=_vec(graphic.get("oam_flip_origin_offset",[0,0]))
		_draw_frame(graphic,int(old.frame),at,flip,Color(.63,.75,.8,float(style[1])))

func _actor_offset(id: String) -> Vector2:
	if id == _reaction_actor and not _reaction_frame.is_empty():
		return _vec(_reaction_frame.get("offset",[0,0]))+Vector2(float(_reaction_frame.get("shake",0)),0)
	return _vec(ui.combat_offsets.get(id,Vector2.ZERO))

func draw_actors() -> void:
	if ui.combat.is_empty(): return
	review_fx.draw_layer(ui,"back",FIELD)
	var a = ui.game.find_unit(str(ui.combat.attacker))
	var b = ui.game.find_unit(str(ui.combat.defender))
	var actors: Array = [b, a] if _left(b, ui.combat) else [a, b]
	var drawn: Array[String] = []
	var staged := review_fx.actor_pose()
	for unit in actors:
		if unit.is_empty() or str(unit.id) in drawn: continue
		drawn.append(str(unit.id))
		var id = str(unit.id)
		var reacting := id == _reaction_actor and not _reaction_frame.is_empty()
		if not reacting and id == str(active_event.get("attacker","")) and not staged.is_empty():
			review_fx.draw_actor(ui,staged,FIELD,float(ui.combat_fades.get(id,1.0)))
			continue
		var graphic = sprite(unit)
		if bool(graphic.get("missing", false)): continue
		if not reacting and id == str(active_event.get("attacker","")):
			_draw_review_trail(unit,graphic)
		var frame = int(_reaction_frame.frame) if reacting else int(ui.combat_poses.get(id, graphic.sequences.idle[0]))
		var pose_flip := bool(_reaction_frame.get("flip",false)) if reacting else bool(flips.get(id,graphic.get("idle_flip",false)))
		var flip = Innate.horizontal_flip(graphic,_left(unit,ui.combat),pose_flip) if Rules.Body.is_body(unit) else _left(unit, ui.combat) != pose_flip
		var at = origin(unit, ui.combat) + _actor_offset(id) - _vec(graphic.anchor)
		if flip and frame < int(graphic.get("source_oam_frame_count", 0)):
			at += _vec(graphic.get("oam_flip_origin_offset", [0, 0]))
		var shade := float(_reaction_frame.get("tint",1.0)) if reacting else float(pose_tint.get(id,1.0))
		var alpha := float(_reaction_frame.get("alpha",1.0)) if reacting else float(target_alpha.get(id,1.0))*float(pose_alpha.get(id,1.0))
		var color = Color(shade,shade,shade,1.0)
		color.a = float(ui.combat_fades.get(id, 1.0)) * alpha
		if str(ui.combat_hit_id) == id and float(ui.combat_hit_time) > 0.0 and int(float(ui.elapsed) * 30.0) % 2 == 0:
			color = Color(0.35, 0.35, 0.35, color.a)
		_draw_frame(graphic, frame, at, flip, color)
	if not review_fx.replaces_native():
		_draw_effects(effects,true)
	_draw_effects(_reaction_frame.get("effects",[]),false)
	review_fx.draw_layer(ui,"front",FIELD)

func _draw_effects(layer: Array, strike: bool) -> void:
	if layer.is_empty():return
	var sprites: Dictionary = _source_metadata().sprites
	for effect in layer:
		if strike and review_fx.replaces_sprite(str(effect.sprite)):continue
		var graphic: Dictionary = CampaignEffects.graphic(str(effect.sprite),active_variant)
		if graphic.is_empty():graphic=sprites.get(str(effect.sprite),{})
		if graphic.is_empty():continue
		if effect.has("size") and str(effect.sprite).begins_with("trio-"):
			graphic=graphic.duplicate(true)
			var ratio=_vec(effect.size)/_vec(graphic.frame_size);graphic.logical_frame_size=effect.size
			graphic.anchor=[float(graphic.anchor[0])*ratio.x,float(graphic.anchor[1])*ratio.y]
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
			return origin(target,ui.combat)+_actor_offset(str(target.id))
	return _vec(effect.position)
