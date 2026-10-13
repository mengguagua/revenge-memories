extends SceneTree
const Effects = preload("res://core/map_effects.gd")
class Audio extends RefCounted:
	var requests: Array = []
	func play_request(id: int) -> void: requests.append(id)
class Game extends RefCounted:
	var frame_counter = 0
class UI extends RefCounted:
	var audio = Audio.new()
	var game = Game.new()
	var map_actor_alpha: Dictionary = {}
	var map_offset := Vector2.ZERO
	var self_modulate := Color.WHITE
	var instant_mode = true
	var effects
	var samples: Array = []
	var calls: Array = []
	var focused: Array = []
	var cancel_next = false
	func queue_redraw() -> void: pass
	func _focus_battle(cell: Vector2i, _force: bool) -> void: focused.append(cell)
	func _battle_cell_screen(cell: Vector2i) -> Vector2: return Vector2(cell) * 16
	func _draw_frame(sprite: Dictionary, frame: int, at: Vector2) -> void: calls.append({"sprite": sprite.path, "frame": frame, "at": at})
	func _wait(_seconds: float) -> void:
		samples.append({"alpha": map_actor_alpha.duplicate(), "offset": map_offset, "color": self_modulate, "frame": effects._frame})
		effects.draw()
		if cancel_next:
			cancel_next = false
			effects.dispose()
var checks = 0
var failures: Array = []
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message); push_error(message)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var ui = UI.new()
	var effects = Effects.new(ui)
	ui.effects = effects
	var unit = {"id": "unit", "class_id": 16, "side": "enemy", "position": [3, 4], "hp": 30}
	for i in range(1, 12):
		ui.samples.clear(); ui.calls.clear(); ui.audio.requests.clear()
		var original = JSON.stringify(Effects.source().programs[str(i)])
		await effects.play_program(i, unit)
		var info = Effects.source().programs[str(i)]
		check(ui.samples.size() == (20 if i in [9, 10] else 60), "program%d source duration" % i)
		check(ui.audio.requests == [int(info.sound_request), 48], "program%d source sound and stop" % i)
		check(ui.map_actor_alpha.is_empty() and not effects._active, "program%d visibility cleanup" % i)
		check(ui.samples.all(func(s): return s.frame >= 0 and s.frame < info.frames), "program%d all valid frames" % i)
		check(ui.calls[0].at == Vector2(3, 4) * 16 + Vector2(15, 15) - Vector2(info.anchor[0], info.anchor[1]), "program%d source tile OAM origin" % i)
		check(JSON.stringify(Effects.source().programs[str(i)]) == original, "program%d immutable source cache" % i)
	ui.samples.clear(); ui.audio.requests.clear()
	await effects.teleport(unit, Vector2i(9, 10))
	check(unit.position == [9, 10] and unit.hp == 30, "teleport moves once without affecting HP")
	check(ui.samples.size() == 120 and ui.map_actor_alpha.is_empty(), "teleport disappearance/appearance cleanup")
	check(ui.samples.all(func(s): return s.alpha.get("unit", 1.0) == 0.0), "teleport does not overlay duplicate actor")
	check(ui.audio.requests == [35, 48, 35, 48], "teleport original map audio sequence")
	ui.samples.clear()
	await effects.flash("invoke")
	check(ui.samples.size() == 48, "invoke source48 tick emphasis")
	check(ui.samples.filter(func(s): return s.color != Color.WHITE).size() == 24, "invoke alternates exact source emphasis pattern")
	check(ui.self_modulate == Color.WHITE and effects.emphasis_register == 0, "invoke restores CanvasItem color")
	ui.samples.clear()
	await effects.flash("expel")
	check(ui.samples[0].color == Color(1, .75, .75) and ui.samples[1].color == Color.WHITE, "expel red-emphasis register pattern")
	ui.samples.clear(); ui.audio.requests.clear()
	await effects.flash("quake")
	check(ui.samples.size() == 400 and ui.audio.requests == [165], "quake original400 tick duration and A5 track")
	check(ui.samples.any(func(s): return s.offset.y != 0) and ui.map_offset == Vector2.ZERO, "quake source two-axis scroll and cleanup")
	for cid in [5, 3, 11, 17, 16, 18]:
		unit.class_id = cid
		check(Effects.summon_program(unit) in [1, 3, 5, 7, 11], "original monster appearance routing %d" % cid)
		check(Effects.summon_program(unit, true) in [2, 4, 6, 8, 11], "original monster removal routing %d" % cid)
	ui.cancel_next = true
	await effects.play_program(1, unit)
	check(ui.map_actor_alpha.is_empty() and not effects._active and effects._ui() == null, "dispose restores hidden actors and drops weak owner")
	ui.effects = null
	var report = {"checks": checks, "failures": failures, "failure_count": failures.size()}
	var f = FileAccess.open("res://reports/map-effects-tests.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  ") + "\n"); f.close()
	print(JSON.stringify(report)); quit(0 if failures.is_empty() else 1)
