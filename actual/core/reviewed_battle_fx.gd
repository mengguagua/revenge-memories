extends RefCounted
## Offline PixelFX atlases registered to the native strike clock and combatants.
## This player receives presentation data only. It cannot commit a strike.
const DATA := "res://data/battle_fx.json"
const PUPPET_DATA := "res://data/puppet_battle_fx.json"
const DAMAGE_DATA := "res://data/battle_damage_glyphs.json"
const FIELD := Rect2(0, 0, 256, 128)
const REVIEW_FPS := 60.0
static var _data: Dictionary = {}
static var _damage: Dictionary = {}

var plan: Dictionary = {}
var clock := 0.0
var contacted := false
var _owner: WeakRef
var _actor := Vector2.ZERO
var _target := Vector2.ZERO
var _mirrored := false
var _did_damage := false
var _played: Dictionary = {}
var _sound_was_enabled := true
var _extra: Array[Dictionary] = []
var _floating_damage := 0
var _damage_at := Vector2.ZERO

func _init(owner) -> void:
	_owner = weakref(owner)

static func data() -> Dictionary:
	if _data.is_empty():
		_data = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		var puppets: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PUPPET_DATA))
		_data.effects.merge(puppets.effects)
		_data.puppets = puppets.plans
	return _data

static func damage_data() -> Dictionary:
	if _damage.is_empty():
		_damage = JSON.parse_string(FileAccess.get_file_as_string(DAMAGE_DATA))
	return _damage

static func point(pair: Array) -> Vector2:
	return Vector2(float(pair[0]), float(pair[1]))

static func battle_plan(key: String, event: Dictionary) -> Dictionary:
	var table: Dictionary = data().battle
	var weapon := str(int(event.get("weapon_index", 0)))
	var suffix := ":recoil" if int(event.get("self_damage", 0)) > 0 else ""
	return table.get(key+"|"+weapon+suffix, table.get(key+"|0", {}))

static func puppet_plan(key: String, variant: Dictionary) -> Dictionary:
	var recipe: Dictionary = data().puppets[key].duplicate(false)
	recipe.first = -float(variant.contact_tick)/float(variant.native_fps)
	return recipe

func reset() -> void:
	plan = {}
	clock = 0.0
	contacted = false
	_played.clear()
	_extra.clear()
	_floating_damage = 0

func prepare(recipe: Dictionary, event: Dictionary, actor := Vector2.ZERO, target := Vector2.ZERO) -> void:
	reset()
	_did_damage = bool(event.get("hit", true)) and (
		int(event.get("hp_after",0)) < int(event.get("hp_before",0))
		or int(event.get("part_hp_after",0)) < int(event.get("part_hp_before",0))
		or int(event.get("self_damage",0)) > 0
	)
	if recipe.get("positive_damage",false) and not _did_damage:
		return
	plan = recipe
	clock = float(plan.get("first", 0.0))
	_actor = actor
	_target = target
	var left := actor.x < target.x
	_mirrored = plan.has("left") and left != bool(plan.left) and actor != target

func plays_audio() -> bool:
	return plan.has("audio")

func replaces_hit_sound() -> bool:
	if not _did_damage or not plays_audio():
		return false
	for cue in plan.audio:
		if absf(float(cue.time)) <= .06:
			return true
		# The continuous fireball already includes its impact.
		if str(cue.key).begins_with("r4-fire-"):
			return true
	return false

func source_tick(tick: int, contact_tick: int, rate := 1.0) -> void:
	if contacted or plan.is_empty():
		return
	seek(lerpf(float(plan.first),0.0,float(tick)/maxi(1,contact_tick)),true,rate)

func contact() -> void:
	contacted = true
	seek(0.0)

func process(delta: float) -> void:
	var ui = _owner.get_ref()
	if not contacted or ui == null or ui.instant_mode:
		return
	seek(clock+delta*ui.effective_animation_speed())

func seek(at: float, sounds := true, rate := 1.0) -> void:
	clock = at
	var ui = _owner.get_ref()
	if not sounds or ui == null or ui.instant_mode or not plays_audio():
		return
	var enabled: bool = ui.audio.sfx_enabled
	if not enabled:
		_sound_was_enabled = false
		return
	if not _sound_was_enabled:
		_played.clear()
	_sound_was_enabled = true
	ui.audio.sync_reviewed_sfx(ui.effective_animation_speed()*rate)
	for cue in plan.audio:
		var age := at-float(cue.time)
		var key := str(cue.key)
		if age < -.0001 or age >= float(cue.duration) or _played.has(key):
			continue
		if cue.on_hit and not _did_damage:
			continue
		_played[key] = true
		play_sound(ui, key, float(cue.gain), maxf(0.0, age), rate)

static func play_sound(ui, key: String, gain := .88, offset := 0.0, rate := 1.0) -> void:
	var path := str(data().audio.get(key,""))
	if not path.is_empty() and not ui.instant_mode:
		ui.audio.play_reviewed_sfx(key, path, gain, offset, ui.effective_animation_speed()*rate)

func replaces_sprite(name: String) -> bool:
	return name in plan.get("replace_sprites", [])

func replaces_native() -> bool:
	if plan.has("replace") and clock >= float(plan.replace[0]) and clock < float(plan.replace[1]):
		return true
	for cue in plan.get("layers", []):
		if cue.get("projectile","") == "arrow" and _cue_visible(cue) and _cue_point(cue) != null:
			return true
	return false

func actor_pose() -> Array:
	if not plan.has("actor"):
		return []
	var stage: Dictionary = plan.actor
	var index := _frame_index()-int(stage.first)
	if index < 0 or index >= stage.frames.size() or stage.frames[index] == null:
		return []
	return stage.frames[index]

func draw_actor(ui, pose: Array, clip: Rect2, opacity := 1.0) -> void:
	if pose.is_empty():
		return
	var at := _registered(Vector2(float(pose[1]),float(pose[2])))
	draw_frame(ui,data().effects[str(plan.actor.effect)],int(pose[0]),at,
		bool(pose[3]) != _mirrored, opacity*float(pose[4]), clip, _scale())

func draw_layer(ui, name: String, clip: Rect2, opacity := 1.0) -> void:
	for cue in plan.get("layers", []):
		var layer := str(cue.get("layer","front"))
		if plan.get("weapon_front",false) and str(cue.effect).ends_with("-charge"):
			layer = "back"
		if layer != name or not _cue_visible(cue):
			continue
		var pos = _cue_point(cue)
		if pos == null:
			continue
		var age := clock-float(cue.start)
		var alpha := opacity*float(cue.get("alpha",1.0))
		if cue.has("fadeIn"):
			alpha *= clampf(age/float(cue.fadeIn),0.0,1.0)
		if cue.has("fadeOut"):
			alpha *= clampf((float(cue.end)-clock)/float(cue.fadeOut),0.0,1.0)
		var flip := bool(cue.get("flip",false)) != _mirrored
		var area := clip
		if cue.has("limit"):
			var x := _registered(Vector2(float(cue.limit), 0)).x
			var from := clip.position.x if flip else maxf(clip.position.x,x)
			var to := minf(clip.end.x,x) if flip else clip.end.x
			area = Rect2(from,clip.position.y,maxf(0.0,to-from),clip.size.y)
		draw_effect(ui, str(cue.effect), age*float(cue.get("rate",1.0))+float(cue.get("offset",0.0)),
			_registered(pos), flip, alpha, area, _scale()*float(cue.get("scale",1.0)))
	if name == "front":
		for cue in _extra:
			draw_effect(ui,cue.effect,clock-cue.start,cue.at,cue.flip,cue.alpha,clip)
		if _floating_damage > 0:
			draw_damage(ui,_floating_damage,clock,_damage_at,clip)

func extra(effect: String, at: Vector2, delay := 0.0, flip := false, alpha := 1.0) -> void:
	_extra.append({"effect":effect,"start":clock+delay,"at":at,"flip":flip,"alpha":alpha})

func float_damage(amount: int, at: Vector2) -> void:
	_floating_damage = amount
	_damage_at = at

func remaining() -> float:
	return maxf(0.0,float(plan.get("end",0.0))-clock)

func _scale() -> float:
	return 1.0/float(plan.get("density",1.0))

func _frame_index() -> int:
	return floori((clock+float(plan.contact))*REVIEW_FPS+.00001)

func _registered(p: Vector2) -> Vector2:
	if plan.has("density"):
		return p
	var target_x := _target.x
	if absf(target_x-_actor.x) < 1.0:
		target_x = _actor.x+(112.0 if plan.get("left",false) else -112.0)
	return Vector2(lerpf(_actor.x,target_x,p.x),p.y)

func _cue_visible(cue: Dictionary) -> bool:
	return clock >= float(cue.start) and clock < float(cue.end) and (not cue.get("hit",false) or _did_damage)

func _cue_point(cue: Dictionary):
	if cue.has("at"):
		return point(cue.at)
	var track: Array = cue.track
	var index := _frame_index()-int(track[0])
	if index < 0 or index >= track[1].size() or track[1][index] == null:
		return null
	return point(track[1][index])

static func draw_effect(ui, key: String, age: float, at: Vector2, flip: bool, alpha: float,
		clip: Rect2, scale := 1.0) -> void:
	if age < 0 or alpha <= 0:
		return
	var graphic: Dictionary = data().effects[key]
	var frame := floori(age*float(graphic.fps)+.00001)
	if graphic.loop:
		frame %= int(graphic.frames)
	draw_frame(ui,graphic,frame,at,flip,alpha,clip,scale)

static func draw_frame(ui, graphic: Dictionary, frame: int, at: Vector2, flip: bool,
		alpha: float, clip: Rect2, scale: float) -> void:
	if alpha <= 0 or frame < 0 or frame >= int(graphic.frames):
		return
	var size := point(graphic.size)
	var pivot := point(graphic.pivot)
	if flip:
		pivot.x = size.x-pivot.x
	var bounds := Rect2(at.round()-pivot*scale,size*scale)
	var dest := bounds.intersection(clip)
	if not dest.has_area():
		return
	var offset := (dest.position-bounds.position)/scale
	var visible := dest.size/scale
	if flip:
		offset.x = size.x-offset.x-visible.x
		dest.size.x = -dest.size.x
	var cell := frame % int(graphic.cells)
	var columns := int(graphic.columns)
	var source := Rect2(Vector2(cell%columns,cell/columns)*size+offset,visible)
	var texture: Texture2D = ui._tex(str(graphic.paths[frame/int(graphic.cells)]))
	if texture != null:
		ui.draw_texture_rect_region(texture,dest,source,Color(1,1,1,alpha))

static func draw_damage(ui, amount: int, age: float, at: Vector2, clip: Rect2, scale := 1.0,
		opacity := 1.0) -> void:
	if amount <= 0 or age < 0 or age >= 1.05:
		return
	var key := "r5-damage-"+str(amount)
	if data().effects.has(key):
		draw_effect(ui,key,age,at,false,opacity,clip,scale)
		return
	var glyph := damage_data()
	var frame := floori(age*float(glyph.fps)+.00001)
	draw_frame(ui,glyph.hit,frame,at,false,opacity,clip,scale)
	var sample = glyph.tracks[frame]
	if sample == null:
		return
	var digits := "-"+str(amount)
	var symbols := str(glyph.symbols)
	var widths: Array = glyph.widths
	var gap := int(glyph.gap)
	var letters: Array[int] = []
	var width := -gap
	for digit in digits:
		var index := symbols.find(digit)
		letters.append(index)
		width += int(widths[index])+gap
	var sx := float(sample[2])
	var base := at+Vector2(float(sample[0])-width*sx*.5,float(sample[1]))*scale
	for index in letters:
		draw_frame(ui,glyph.glyphs,frame*symbols.length()+index,base,false,opacity,clip,scale)
		base.x += (int(widths[index])+gap)*sx*scale
