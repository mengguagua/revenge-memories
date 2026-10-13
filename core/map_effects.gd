class_name FeMapEffects
extends RefCounted
## Original tactical-map OAM/pose programs, separate from close-up combat.
## Assets and evidence: data/full_map_effects.json. No invented spell substitute.
const FPS = 60.0988
static var _cache: Dictionary = {}
var _owner: WeakRef
var _generation = 0
var _program: Dictionary = {}
var _cell := Vector2i.ZERO
var _frame = 0
var _active = false
var _hidden_ids: Array[String] = []
var _saved_alpha: Dictionary = {}
var _saved_modulate := Color.WHITE
var _emphasis_active = false
var emphasis_register = 0
var missing_programs: Array[int] = []
var ticks_played = 0

func _init(owner) -> void:
	_owner = weakref(owner)

func _ui():
	return _owner.get_ref() if _owner != null else null

static func source() -> Dictionary:
	if _cache.is_empty():
		var raw = JSON.parse_string(FileAccess.get_file_as_string("res://data/full_map_effects.json"))
		if raw is Dictionary: _cache = raw
	return _cache

static func summon_program(unit: Dictionary, disappearing: bool = false) -> int:
	if str(unit.get("side", "player")) == "player": return 1
	var cid = int(unit.get("class_id", 0))
	return int(({5: 4, 3: 11, 11: 6, 17: 8, 16: 2, 18: 11} if disappearing else {5: 3, 3: 11, 11: 5, 17: 7, 16: 1, 18: 11}).get(cid, -1))

func reset() -> void:
	_generation += 1
	var ui = _ui()
	if ui != null:
		for id in _hidden_ids:
			if _saved_alpha[id] == null: ui.map_actor_alpha.erase(id)
			else: ui.map_actor_alpha[id] = _saved_alpha[id]
		if _emphasis_active: ui.self_modulate = _saved_modulate
		ui.map_offset = Vector2.ZERO
		ui.queue_redraw()
	_hidden_ids.clear()
	_saved_alpha.clear()
	_emphasis_active = false
	emphasis_register = 0
	_active = false
	_program = {}

func dispose() -> void:
	reset()
	_owner = null

func _hide(unit: Dictionary) -> void:
	var ui = _ui()
	if ui == null: return
	var id = str(unit.id)
	if not _hidden_ids.has(id):
		_hidden_ids.append(id)
		_saved_alpha[id] = ui.map_actor_alpha.get(id)
	ui.map_actor_alpha[id] = 0.0

func _restore(id: String) -> void:
	var ui = _ui()
	if not _hidden_ids.has(id): return
	if ui != null:
		if _saved_alpha[id] == null: ui.map_actor_alpha.erase(id)
		else: ui.map_actor_alpha[id] = _saved_alpha[id]
	_hidden_ids.erase(id)
	_saved_alpha.erase(id)

func draw() -> void:
	var ui = _ui()
	if ui == null or not _active or _program.is_empty(): return
	var offset = Vector2(_program.tile_origin_offset[0], _program.tile_origin_offset[1])
	var anchor = Vector2(_program.anchor[0], _program.anchor[1])
	ui._draw_frame(_program, _frame, ui._battle_cell_screen(_cell) + offset - anchor)

func play_program(program: int, unit: Dictionary) -> void:
	var ui = _ui()
	if ui == null: return
	if not source().programs.has(str(program)):
		if not missing_programs.has(program):
			missing_programs.append(program)
			push_warning("Original map effect program missing: %d" % program)
		return
	var token = _generation
	_program = source().programs[str(program)]
	_cell = Vector2i(int(unit.position[0]), int(unit.position[1]))
	ui._focus_battle(_cell, true)
	var hide_body = program != 9 and program != 10
	if hide_body: _hide(unit)
	_active = true
	ui.audio.play_request(int(_program.sound_request))
	var timeline: Array = _program.cycle_timeline
	# Source35=6 for service10/11, source35=2 for target feedback. The
	# native player starts the shared divide-by-ten timer at its full phase.
	var duration = 20 if program in [9, 10] else 60
	for tick in range(duration):
		if _ui() == null or token != _generation: return
		_frame = int(timeline[tick % timeline.size()])
		ticks_played += 1
		ui.queue_redraw()
		await ui._wait(1.0 / FPS)
	if token != _generation or _ui() == null: return
	ui.audio.play_request(int(_program.end_sound_request))
	_active = false
	_program = {}
	if hide_body: _restore(str(unit.id))
	ui.queue_redraw()

func flash(kind: String) -> void:
	var ui = _ui()
	if ui == null: return
	var token = _generation
	if kind == "quake":
		var quake = source().routing.quake
		ui.audio.play_request(int(quake.music_request))
		var phase = int(ui.game.frame_counter) & 3
		var frames: Array = quake.timeline_by_initial_frame_counter_mod4[str(phase)]
		for offset in frames:
			if _ui() == null or token != _generation: return
			ui.map_offset = Vector2(float(offset[0]), float(offset[1]))
			ticks_played += 1
			ui.queue_redraw()
			await ui._wait(1.0 / FPS)
		if _ui() != null and token == _generation:
			ui.map_offset = Vector2.ZERO
			ui.queue_redraw()
		return
	var name = "expel_flash" if kind == "expel" else "invoke_flash"
	var info = source().routing[name]
	_saved_modulate = ui.self_modulate
	_emphasis_active = true
	for tick in range(int(info.ticks)):
		if _ui() == null or token != _generation: return
		var enabled = ((int(info.ticks) - tick) & 1) == 0
		emphasis_register = int(info.even_remaining_ticks_ppumask_or) if enabled else 0
		# PPUMASK emphasizes one channel by attenuating the other channels.
		# NES analog color response is approximate with the fixed RGB palette;
		# preserve original bit/tick pattern instead of adding white flashes.
		var emphasis = Color(1.0, 0.75, 0.75) if kind == "expel" else Color(0.75, 0.75, 1.0)
		ui.self_modulate = _saved_modulate * emphasis if enabled else _saved_modulate
		ticks_played += 1
		ui.queue_redraw()
		await ui._wait(1.0 / FPS)
	if _ui() == null or token != _generation: return
	ui.self_modulate = _saved_modulate
	_emphasis_active = false
	emphasis_register = 0
	ui.queue_redraw()

func teleport(unit: Dictionary, landing: Vector2i) -> void:
	var ui = _ui()
	if ui == null: return
	var token = _generation
	_hide(unit)
	await play_program(2, unit)
	if _ui() == null or token != _generation: return
	# play_program restores its owner alpha; keep actor hidden at the new
	# coordinate until the original appearance OAM finishes.
	_hide(unit)
	unit.position = [landing.x, landing.y]
	ui._focus_battle(landing, true)
	await play_program(1, unit)
	if _ui() == null or token != _generation: return
	_restore(str(unit.id))
	ui.queue_redraw()
