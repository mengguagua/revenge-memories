extends Node
## Original NES audio rendered as standard Ogg Vorbis resources.
## Music and jingle players persist for the lifetime of this node. A jingle
## pauses the current music player, then resumes its original playback position.

signal music_changed(key: String)
signal music_finished(key: String)
signal jingle_started(key: String)
signal jingle_finished(key: String)
signal playback_failed(key: String, reason: String)
signal sfx_played(key: String)

const MANIFEST_PATH := "res://data/legacy/audio.json"
const MUSIC_GAIN := 0.50
const SFX_GAIN := 0.65
const SFX_VOICES := 2
# L0E87A0: four stages, each32 NTSC audio frames, then music stops.
# Ogg mixes cannot independently change the original four APU envelopes;
# apply the same overall duration to the native music/jingle bus gain.
const SOURCE_FADE_SECONDS := 128.0 / 60.0988
# L0FF12D, consulted by L0580EA before choosing the normal duel music.
const SOURCE_BOSS_MUSIC_IDS := [129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,154,155,156,157,158,168,169,170,171,212]

var _manifest: Dictionary = {}
var full_manifest: Dictionary = {}
var _stream_cache: Dictionary = {}
var _music_player: AudioStreamPlayer
var _jingle_player: AudioStreamPlayer
var _sfx_players: Array[AudioStreamPlayer] = []
var _music_key := ""
var _jingle_key := ""
var _jingle_active := false
var _music_pending_start := false
var _music_enabled := true
var _sfx_enabled := true
var _volume := 1.0
var _fade_left := 0.0
var _fade_gain := 1.0
var music_enabled: bool:
	get:
		return _music_enabled
var sfx_enabled: bool:
	get:
		return _sfx_enabled

var _next_sfx_voice := 0
var _initialized := false


func _ready() -> void:
	_ensure_initialized()


func _process(delta: float) -> void:
	if _fade_left <= 0.0:
		return
	_fade_left = maxf(0.0, _fade_left - delta)
	_fade_gain = _fade_left / SOURCE_FADE_SECONDS
	_apply_volume()
	if _fade_left == 0.0:
		_stop_music()


func play_music(key: String) -> void:
	_ensure_initialized()
	var stream := _get_stream("music", key)
	if stream == null:
		return
	_cancel_fade()
	if key == _music_key and (_music_player.playing or _music_player.stream_paused):
		return
	_music_key = key
	_music_player.stream_paused = false
	_music_player.stop()
	_music_player.stream = stream
	_music_pending_start = true
	# Muting preserves an existing track's position. A newly requested track
	# while muted is only prepared, so no paused playback is queued on the audio
	# server for every scene/phase change (also important for headless tests).
	if _music_enabled:
		_music_player.play()
		_music_pending_start = false
	_music_player.stream_paused = not _music_enabled or _jingle_active
	music_changed.emit(key)


func play_sfx(key: String) -> void:
	_ensure_initialized()
	if not _sfx_enabled:
		return
	var stream := _get_stream("sfx", key)
	if stream == null:
		return
	# Two reusable voices allow a cursor/HP sound to finish without accumulating
	# loud stacks of effects. If both are occupied, replace the oldest request.
	var player: AudioStreamPlayer = _sfx_players[_next_sfx_voice]
	for candidate in _sfx_players:
		if not candidate.playing:
			player = candidate
			break
	_next_sfx_voice = (_sfx_players.find(player) + 1) % SFX_VOICES
	player.stop()
	player.stream = stream
	player.play()
	sfx_played.emit(key)

func play_request(request: int) -> void:
	_ensure_initialized()
	var key := "%02X" % request
	# Every null SFX pointer is a stop request, not only the named0x30.
	var control := str(full_manifest.get("control_requests", {}).get(key,
		"stop_all" if request == 0 else "stop_sfx" if request == 48 else ""))
	match control:
		"stop_all":
			stop_all()
			return
		"stop_sfx":
			_stop_sfx()
			return
		"fade_music":
			if _fade_left <= 0.0 and (not _music_key.is_empty() or _jingle_active):
				_fade_left = SOURCE_FADE_SECONDS
				_fade_gain = 1.0
			return
	if full_manifest.get("ignored_requests", {}).has(key):
		# Source null music pointers preserve current notes/playback.
		return
	if full_manifest.get("music_by_request", {}).has(key):
		var entry: Dictionary = full_manifest.music_by_request[key]
		if bool(entry.get("resume_music", false)):
			play_jingle("request_" + key)
		else:
			play_music("request_" + key)
	elif full_manifest.get("sfx_by_request", {}).has(key):
		play_sfx("request_" + key)

func play_world(chapter: int) -> void:
	_ensure_initialized()
	var table: Array = full_manifest.get("routing", {}).get("world_by_chapter", [160])
	play_request(int(table[clampi(chapter - 1, 0, table.size() - 1)]))

func play_battle(route: String, phase: String, remaining: int, final_battle: bool = false, _final_phase: bool = false) -> void:
	_ensure_initialized()
	var routing: Dictionary = full_manifest.get("routing", {})
	if final_battle:
		play_request(int(routing.get("final_battle_by_phase", [180, 181])[1 if phase == "enemy" else 0]))
	else:
		var table = "enemy_by_route" if phase == "enemy" else ("player_last_enemy_by_route" if remaining < 2 else "player_by_route")
		play_request(int(routing.get(table, [112, 119] if phase == "enemy" else [163, 167] if remaining < 2 else [161, 164])[1 if route == "celica" else 0]))

func play_hub(hub_id: int) -> void:
	_ensure_initialized()
	if hub_id <= 0:
		return
	var routing: Dictionary = full_manifest.get("routing", {})
	var table: Array = routing.get("hub_music_index_by_map", [])
	var requests: Array = routing.get("hub_music_requests", [])
	var limit := int(routing.get("hub_music_lookup_limit_exclusive", 111))
	var index := int(routing.get("hub_music_default_index", 4))
	if hub_id < limit and hub_id <= table.size():
		index = int(table[hub_id - 1])
	if index >= 0 and index < requests.size():
		play_request(int(requests[index]))


func play_combat(_player: Dictionary, enemy: Dictionary, enemy_initiated: bool = false, support: bool = false, final_battle: bool = false) -> void:
	# L058066-L0580AB writes the same packed request bits as L0FF58A.
	# This is an attacker/support/boss decision, not an Alm/Celica route table.
	if support:
		play_request(0xA2)
	elif int(enemy.get("class_id", 0)) == 21:
		play_request(0xA5)
	elif int(enemy.get("character_id", 0)) in SOURCE_BOSS_MUSIC_IDS:
		play_request(0x76)
	elif enemy_initiated:
		play_request(0x80)
	else:
		play_request(0xB0 if final_battle else 0x86)


func play_ending() -> void:
	# L04B0F9 begins the character epilogues with request115.
	play_request(0x73)


func play_jingle(key: String) -> void:
	_ensure_initialized()
	if not _music_enabled:
		return
	var stream := _get_stream("music", key)
	if stream == null:
		return
	if stream is AudioStreamOggVorbis and stream.loop:
		playback_failed.emit(key, "Looping music cannot be played as a jingle")
		return
	_cancel_fade()
	_music_player.stream_paused = true
	_jingle_player.stop()
	_jingle_key = key
	_jingle_active = true
	_jingle_player.stream = stream
	_jingle_player.stream_paused = false
	_jingle_player.play()
	jingle_started.emit(key)


func set_music_enabled(enabled: bool) -> void:
	_ensure_initialized()
	_music_enabled = enabled
	if enabled and _music_pending_start:
		_music_player.stream_paused = false
		_music_player.play()
		_music_pending_start = false
	_music_player.stream_paused = not enabled or _jingle_active
	_jingle_player.stream_paused = not enabled


func set_sfx_enabled(enabled: bool) -> void:
	_ensure_initialized()
	_sfx_enabled = enabled
	if not enabled:
		for player in _sfx_players:
			player.stop()


func set_volume(value: float) -> void:
	_volume = clampf(value, 0.0, 1.0)
	if _initialized:
		_apply_volume()


func stop_all() -> void:
	_ensure_initialized()
	_stop_music()
	_stop_sfx()


func _stop_music() -> void:
	_music_player.stream_paused = false
	_jingle_player.stream_paused = false
	_music_player.stop()
	_jingle_player.stop()
	_music_player.stream = null
	_jingle_player.stream = null
	_music_pending_start = false
	_music_key = ""
	_jingle_key = ""
	_jingle_active = false
	_cancel_fade()


func _stop_sfx() -> void:
	for player in _sfx_players:
		player.stop()
		player.stream = null


func _cancel_fade() -> void:
	_fade_left = 0.0
	_fade_gain = 1.0
	_apply_volume()


func _exit_tree() -> void:
	if not _initialized:
		return
	stop_all()
	_stream_cache.clear()


func _ensure_initialized() -> void:
	if _initialized:
		return
	_initialized = true
	_load_manifest()
	_music_player = _make_player("OriginalMusic")
	_jingle_player = _make_player("OriginalJingle")
	_music_player.finished.connect(_on_music_finished)
	_jingle_player.finished.connect(_on_jingle_finished)
	for index in range(SFX_VOICES):
		_sfx_players.append(_make_player("OriginalSfx%d" % index))
	_apply_volume()


func _make_player(player_name: String) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.name = player_name
	player.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(player)
	return player


func _load_manifest() -> void:
	if not FileAccess.file_exists(MANIFEST_PATH):
		playback_failed.emit("", "Original audio manifest is missing")
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
	if parsed is Dictionary:
		_manifest = parsed
		if FileAccess.file_exists("res://data/legacy/full_audio.json"):
			full_manifest = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/full_audio.json"))
			for key in full_manifest.get("music_by_request", {}):
				_manifest.music["request_" + key] = full_manifest.music_by_request[key]
			for key in full_manifest.get("sfx_by_request", {}):
				_manifest.sfx["request_" + key] = full_manifest.sfx_by_request[key]
	else:
		playback_failed.emit("", "Original audio manifest could not be parsed")


func _get_stream(group: String, key: String) -> AudioStream:
	var entries: Dictionary = _manifest.get(group, {})
	var entry: Dictionary = entries.get(key, {})
	if entry.is_empty():
		playback_failed.emit(key, "Unknown original audio cue")
		return null
	# An extracted sound is not evidence for its gameplay binding. Never play
	# unverified candidate cues, including attack/death, through the normal API.
	if not bool(entry.get("default_enabled", true)):
		return null
	var cache_key := group + ":" + key
	if _stream_cache.has(cache_key):
		return _stream_cache[cache_key] as AudioStream
	var path := String(entry.get("path", ""))
	if path.is_empty() or not ResourceLoader.exists(path):
		playback_failed.emit(key, "Original audio resource is missing: " + path)
		return null
	var imported := load(path) as AudioStream
	if imported == null:
		playback_failed.emit(key, "Original audio resource could not be loaded")
		return null
	# Duplicate only once, so loop metadata does not mutate an imported resource
	# shared with another scene or preview.
	var stream := imported.duplicate() as AudioStream
	if stream is AudioStreamOggVorbis:
		stream.loop = bool(entry.get("loop", false))
		stream.loop_offset = float(entry.get("loop_offset", 0.0))
	_stream_cache[cache_key] = stream
	return stream


func _apply_volume() -> void:
	_music_player.volume_db = linear_to_db(maxf(0.000001, _volume * MUSIC_GAIN * _fade_gain))
	_jingle_player.volume_db = _music_player.volume_db
	for player in _sfx_players:
		player.volume_db = linear_to_db(maxf(0.000001, _volume * SFX_GAIN))


func _on_music_finished() -> void:
	if not _music_key.is_empty():
		music_finished.emit(_music_key)


func _on_jingle_finished() -> void:
	if not _jingle_active:
		return
	var finished_key := _jingle_key
	_jingle_key = ""
	_jingle_active = false
	_music_player.stream_paused = not _music_enabled
	jingle_finished.emit(finished_key)
