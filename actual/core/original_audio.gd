extends Node
## Original campaign score and original sound effects. Source request aliases
## resolve to campaign context; duels switch to an urgent variant and restore
## the map's saved position. Turn changes keep the same map position.
## Two reusable BGM voices crossfade; short cues pause and resume both voices.

signal music_changed(key: String)
signal music_finished(key: String)
signal jingle_started(key: String)
signal jingle_finished(key: String)
signal playback_failed(key: String, reason: String)
signal sfx_played(key: String)

const SOURCE_REQUESTS_PATH := "res://data/legacy/full_audio.json"
const SCORE_PATH := "res://data/soundtrack.json"
const SFX_PATH := "res://data/sound_effects.json"
const ScoreRouting = preload("res://core/soundtrack_routing.gd")
const CROSSFADE_SECONDS := 0.6
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
var soundtrack: Dictionary = {}
var sound_effects: Dictionary = {}
var _sfx_aliases: Dictionary = {}
var _stream_cache: Dictionary = {}
var _music_player: AudioStreamPlayer
var _previous_music_player: AudioStreamPlayer
var _crossfade_left := 0.0
var _outgoing_start_gain := 1.0
var _context_signature := ""
var _last_context_view := ""
var _battle_was_active := false
var _jingle_player: AudioStreamPlayer
var _sfx_players: Array[AudioStreamPlayer] = []
var _reviewed_players: Array[AudioStreamPlayer] = []
var _music_key := ""
var _jingle_key := ""
var _jingle_active := false
var _music_pending_start := false
var _pending_music_position := 0.0
var _duel_map_key := ""
var _duel_map_position := 0.0
var _step_player: AudioStreamPlayer
var _last_map_step_ms := -1000
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
var _touch_feedback_depth := 0
var _critical_active := false
var _critical_time := 0.0
var _critical_gain := 1.0
var _critical_music_gain := 1.0
var _critical_sfx: AudioStreamPlayer
var _critical_music: AudioStreamPlayer


func _ready() -> void:
	_ensure_initialized()


func _process(delta: float) -> void:
	_sync_context()
	if _crossfade_left > 0.0 and _music_enabled and not _jingle_active and not _critical_active:
		_crossfade_left = maxf(0.0, _crossfade_left - delta)
		if _crossfade_left == 0.0:
			_previous_music_player.stop()
			_previous_music_player.stream = null
		_apply_volume()
	if _fade_left > 0.0:
		_fade_left = maxf(0.0, _fade_left - delta)
		_fade_gain = _fade_left / SOURCE_FADE_SECONDS
		_apply_volume()
		if _fade_left == 0.0:
			_stop_music()


func play_music(key: String) -> void:
	_ensure_initialized()
	var canonical := ScoreRouting.resolve(soundtrack, key, _read_context())
	if canonical.is_empty():
		playback_failed.emit(key, "Unknown original campaign music cue")
		return
	if str(soundtrack.get("tracks", {}).get(canonical, {}).get("kind", "bgm")) == "jingle":
		play_jingle(canonical)
		return
	_play_track(canonical)


func _play_track(canonical: String) -> void:
	if canonical == _music_key and (_music_player.playing or _music_player.stream_paused or _music_pending_start):
		return
	var stream := _get_stream("music", canonical)
	if stream == null:
		return
	var duel := str(soundtrack.get("routing",{}).get("duel_attack",""))
	var resume_position := 0.0
	if canonical == duel and _music_key != duel and not _music_key.is_empty():
		if _duel_map_key.is_empty():
			_duel_map_key=_music_key
			_duel_map_position=_pending_music_position if _music_pending_start else _music_player.get_playback_position()
	elif not _duel_map_key.is_empty():
		if canonical == _duel_map_key:
			resume_position=_duel_map_position
			_duel_map_key="";_duel_map_position=0.0
		elif not canonical.begins_with("rm_story_"):
			# A post-contact story may precede map return. Leaving for a title,
			# world or different stage invalidates the previous map checkpoint.
			_duel_map_key="";_duel_map_position=0.0
	_cancel_fade()
	var can_crossfade := _music_enabled and not _jingle_active and _music_player.playing
	# Retargeting an unfinished fade must not jump its incoming voice back
	# to full volume when that voice becomes the next outgoing voice.
	var active_gain := _active_envelope()
	_previous_music_player.stop()
	_previous_music_player.stream_paused = false
	if can_crossfade:
		var outgoing := _music_player
		_music_player = _previous_music_player
		_previous_music_player = outgoing
	else:
		_music_player.stop()
		_previous_music_player.stream = null
	_music_key = canonical
	_music_player.stream_paused = false
	_music_player.stream = stream
	_music_player.pitch_scale=float(_manifest.music.get(canonical,{}).get("playback_pitch_scale",1.0))
	_music_pending_start = true
	_pending_music_position=resume_position
	_outgoing_start_gain = active_gain if can_crossfade else 1.0
	_crossfade_left = CROSSFADE_SECONDS if can_crossfade else 0.0
	_apply_volume()
	# A new cue requested while muted or during a jingle is prepared exactly
	# once and starts only when audible. Existing cues keep their positions.
	if _music_enabled and not _jingle_active and not _critical_active:
		_music_player.play(_pending_music_position)
		_music_pending_start = false
	_music_player.stream_paused = not _music_enabled or _jingle_active or _critical_active
	music_changed.emit(canonical)


func _read_context() -> Dictionary:
	var host := get_parent()
	if host == null:
		return {}
	var game: Variant = host.get("game")
	if game == null:
		return {}
	var journey: Variant = host.get("journey")
	var exchange: Variant = _field(host,"combat",{})
	return {
		"view": _field(host, "view", ""), "mode": _field(game, "mode", ""),
		"chapter": _field(game, "chapter", 1), "stage_id": _field(game, "stage_id", 0),
		"hub_record": _field(game, "hub_record", ""),
		"plot_callback": _field(host, "plot_callback", ""),
		"plot_return": _field(host, "plot_return", ""),
		"journal_intent": _field(journey, "intent", "load"),
		"journal_return_view": _field(journey, "return_view", "title"),
		"battle_outcome": _field(game, "battle_outcome", ""),
		"battle_settled": _field(game, "battle_settled", false),
		"training_reward_open": _field(host, "training_reward_open", false),
		"combat_support": bool(exchange.get("support",false)) if exchange is Dictionary else false
	}


func _field(source: Variant, key: String, fallback: Variant) -> Variant:
	var value: Variant = source.get(key) if source is Object or source is Dictionary else null
	return fallback if value == null else value


func _sync_context() -> void:
	if not _initialized:
		return
	var context := _read_context()
	if context.is_empty():
		return
	if _last_context_view == "combat" and str(context.view) != "combat":
		finish_combat_sfx()
	_last_context_view = str(context.view)
	var signature := JSON.stringify(context)
	if signature != _context_signature:
		_context_signature = signature
		# A deliberate stop (defeat, source stop request) stays stopped. Scene
		# entry APIs own starting music; this only follows a live score.
		if not _music_key.is_empty():
			var target := ScoreRouting.context_track(soundtrack, context)
			if not target.is_empty():
				_play_track(target)
	if str(context.mode) == "battle" and str(context.battle_outcome).is_empty():
		_battle_was_active = true
	elif str(context.mode) == "victory" and bool(context.battle_settled) and _battle_was_active:
		# Settlement may immediately open a level-up reward, loot or story page.
		# Keep victory pending until that sequence returns to its result view;
		# never interrupt its level-up cue. A direct ending clears it below.
		if str(context.view) == "victory" and not bool(context.training_reward_open) and not _jingle_active:
			_battle_was_active = false
			play_jingle("rm_jingle_victory")
	elif str(context.mode) in ["title", "hub", "world", "ending", "defeat"]:
		_battle_was_active = false


func play_sfx(key: String) -> void:
	if _touch_feedback_depth>0 and key in ["menu_move","menu_confirm","menu_cancel"]:return
	_ensure_initialized()
	if not _sfx_enabled:
		return
	var canonical := _sfx_canonical(key)
	# Verified source hit/miss requests replace the existing arrow-rain wash.
	# Do not preempt another spell, UI tick or HP voice as part of this cleanup.
	if canonical in ["rm_sfx_03","rm_sfx_43"]:
		_stop_sfx_cue("rm_sfx_53")
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
	player.set_meta("campaign_sfx_key",canonical)
	if canonical == "rm_sfx_53" and str(_read_context().get("view","")) == "combat":
		_last_context_view = "combat"
	player.play()
	sfx_played.emit(key)

func play_reviewed_sfx(key: String, path: String, gain: float, offset: float, speed: float) -> void:
	_ensure_initialized()
	if not _sfx_enabled:
		return
	var stream := load(path) as AudioStream
	if stream == null:
		playback_failed.emit(key, "Reviewed battle cue could not be loaded")
		return
	var voice := _reviewed_players[0]
	for player in _reviewed_players:
		if not player.playing:
			voice = player
			break
		if player.get_playback_position() > voice.get_playback_position():
			voice = player
	voice.stop()
	voice.stream = stream
	voice.set_meta("reviewed_gain", gain)
	voice.volume_db = linear_to_db(maxf(.000001, _volume*SFX_GAIN*gain))
	voice.pitch_scale = clampf(speed,.05,4.0)
	voice.play(offset)
	sfx_played.emit(key)

func sync_reviewed_sfx(speed: float) -> void:
	for player in _reviewed_players:
		player.pitch_scale = clampf(speed,.05,4.0)

func stop_reviewed_sfx() -> void:
	for player in _reviewed_players:
		player.stop()
		player.stream = null

func play_map_step(unit: Dictionary) -> void:
	_ensure_initialized()
	# A quiet dedicated movement voice cannot replace a UI/HP/spell voice.
	if not _sfx_enabled or bool(unit.get("event_object",false)):return
	var now=Time.get_ticks_msec()
	if now-_last_map_step_ms<85:return
	var stream=_get_stream("sfx","map_step")
	if stream==null:return
	_last_map_step_ms=now
	_step_player.stream=stream
	_step_player.pitch_scale=.82 if int(unit.get("class_id",0)) in [1,2,4,7] else 1.0
	_step_player.play()
	sfx_played.emit("map_step")

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
		play_music("request_" + key)
	elif full_manifest.get("sfx_by_request", {}).has(key):
		play_sfx("request_" + key)

func play_world(chapter: int) -> void:
	_ensure_initialized()
	_play_track(str(soundtrack.get("routing", {}).get("world_by_chapter", {}).get(str(chapter), "rm_world_ch1")))


func play_battle(route: String, phase: String, remaining: int, final_battle: bool = false, _final_phase: bool = false) -> void:
	_ensure_initialized()
	# New campaign J54 is 534, not the source campaign's stage 62. Never use
	# old stage identity or actor IDs to override an actual campaign map.
	var track := ScoreRouting.stage_track(soundtrack, int(_read_context().get("stage_id", 0)))
	if not track.is_empty():
		_play_track(track)
		return
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
	_ensure_initialized()
	var track := ScoreRouting.stage_track(soundtrack, int(_read_context().get("stage_id", 0)))
	if not track.is_empty():
		_play_track(track if support else str(soundtrack.get("routing",{}).get("duel_attack",track)))
		return
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
	_ensure_initialized()
	_play_track("rm_ending")


func play_jingle(key: String) -> void:
	_ensure_initialized()
	if not _music_enabled:
		return
	var canonical := ScoreRouting.resolve(soundtrack, key)
	var stream := _get_stream("music", canonical)
	if stream == null:
		return
	if bool(soundtrack.get("tracks", {}).get(canonical, {}).get("loop", false)):
		playback_failed.emit(key, "Looping music cannot be played as a jingle")
		return
	_cancel_fade()
	_music_player.stream_paused = true
	_previous_music_player.stream_paused = true
	_jingle_player.stop()
	_jingle_key = canonical
	_jingle_active = true
	_jingle_player.stream = stream
	_jingle_player.stream_paused = false
	_jingle_player.play()
	jingle_started.emit(canonical)


func begin_touch_feedback(key: int) -> void:
	# A touch gets one click even when its game action has no menu sound.
	# Suppress only synchronous duplicate menu sounds from that same action.
	play_sfx("menu_move" if key in [KEY_UP,KEY_DOWN,KEY_LEFT,KEY_RIGHT] else "menu_cancel" if key==KEY_X else "menu_confirm")
	_touch_feedback_depth+=1

func end_touch_feedback() -> void:
	_touch_feedback_depth=maxi(0,_touch_feedback_depth-1)

func set_music_enabled(enabled: bool) -> void:
	_ensure_initialized()
	_music_enabled = enabled
	if enabled and _music_pending_start and not _jingle_active and not _critical_active:
		_music_player.stream_paused = false
		_music_player.play(_pending_music_position)
		_music_pending_start = false
	_music_player.stream_paused = not enabled or _jingle_active or _critical_active
	_previous_music_player.stream_paused = not enabled or _jingle_active or _critical_active
	_jingle_player.stream_paused = not enabled
	if not enabled and _critical_music!=null:_critical_music.stop()


func set_sfx_enabled(enabled: bool) -> void:
	_ensure_initialized()
	_sfx_enabled = enabled
	if not enabled:
		_stop_sfx()
		if _critical_sfx!=null:_critical_sfx.stop()


func set_volume(value: float) -> void:
	_volume = clampf(value, 0.0, 1.0)
	if _initialized:
		_apply_volume()


func stop_all() -> void:
	_ensure_initialized()
	finish_critical_audio()
	_stop_music()
	_stop_sfx()


func _stop_music() -> void:
	_music_player.stream_paused = false
	_previous_music_player.stream_paused = false
	_jingle_player.stream_paused = false
	_music_player.stop()
	_previous_music_player.stop()
	_jingle_player.stop()
	_music_player.stream = null
	_previous_music_player.stream = null
	_crossfade_left = 0.0
	_jingle_player.stream = null
	_music_pending_start = false
	_pending_music_position=0.0;_duel_map_key="";_duel_map_position=0.0
	_music_key = ""
	_jingle_key = ""
	_jingle_active = false
	_cancel_fade()


func _stop_sfx() -> void:
	stop_reviewed_sfx()
	if _step_player!=null:
		_step_player.stop();_step_player.stream=null
	for player in _sfx_players:
		player.stop()
		player.stream = null
		player.remove_meta("campaign_sfx_key")


func _stop_sfx_cue(canonical: String) -> void:
	for player in _sfx_players:
		if str(player.get_meta("campaign_sfx_key","")) != canonical:continue
		player.stop()
		player.stream = null
		player.remove_meta("campaign_sfx_key")


func finish_combat_sfx() -> void:
	if _critical_active:finish_critical_audio()
	stop_reviewed_sfx()
	# Some extracted arrow-rain timelines end before the driver's explicit stop.
	# The verified transition wash must never survive an action or duel exit.
	_stop_sfx_cue("rm_sfx_53")


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
	_music_player = _make_player("CampaignMusicA")
	_previous_music_player = _make_player("CampaignMusicB")
	_jingle_player = _make_player("CampaignJingle")
	_music_player.finished.connect(_on_music_voice_finished.bind(_music_player))
	_previous_music_player.finished.connect(_on_music_voice_finished.bind(_previous_music_player))
	_jingle_player.finished.connect(_on_jingle_finished)
	for index in range(SFX_VOICES):
		_sfx_players.append(_make_player("CampaignSfx%d" % index))
	for index in range(4):
		_reviewed_players.append(_make_player("ReviewedSfx%d" % index))
	_step_player=_make_player("CampaignMapStep")
	_critical_sfx=_make_player("CriticalEffects")
	_critical_music=_make_player("CriticalTheme")
	_apply_volume()


func _make_player(player_name: String) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.name = player_name
	player.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(player)
	return player


func _load_manifest() -> void:
	_manifest = {"music":{},"sfx":{}}
	# Retain source request/control metadata, never its extracted audio paths.
	if FileAccess.file_exists(SOURCE_REQUESTS_PATH):
		var source: Variant = JSON.parse_string(FileAccess.get_file_as_string(SOURCE_REQUESTS_PATH))
		if source is Dictionary:full_manifest = source
	if full_manifest.is_empty():
		playback_failed.emit("", "Source audio request metadata is missing or invalid")
	if FileAccess.file_exists(SCORE_PATH):
		var score: Variant = JSON.parse_string(FileAccess.get_file_as_string(SCORE_PATH))
		if score is Dictionary:
			soundtrack = score
			_manifest.music = soundtrack.get("tracks", {}).duplicate(true)
			_manifest.music.merge(soundtrack.get("additional_tracks",{}),true)
	if soundtrack.is_empty():
		playback_failed.emit("", "Original campaign soundtrack manifest is missing or invalid")
	if FileAccess.file_exists(SFX_PATH):
		var effects: Variant = JSON.parse_string(FileAccess.get_file_as_string(SFX_PATH))
		if effects is Dictionary:
			sound_effects = effects
			_manifest.sfx = sound_effects.get("effects", {}).duplicate(true)
			_manifest.sfx.merge(sound_effects.get("gameplay_effects",{}),true)
			_sfx_aliases = sound_effects.get("named_aliases", {}).duplicate(true)
			for request in sound_effects.get("request_aliases", {}):
				_sfx_aliases["request_"+str(request)] = sound_effects.request_aliases[request]
			for alias in _sfx_aliases:
				var canonical := str(_sfx_aliases[alias])
				if _manifest.sfx.has(canonical):
					var entry:Dictionary = _manifest.sfx[canonical]
					var overrides:Dictionary = sound_effects.get("named_alias_overrides",{}).get(alias,{})
					if not overrides.is_empty():entry=entry.duplicate(true);entry.merge(overrides,true)
					_manifest.sfx[alias] = entry
				else:playback_failed.emit(str(alias), "Original campaign sound effect alias is invalid")
	if sound_effects.is_empty():
		playback_failed.emit("", "Original campaign sound effects manifest is missing or invalid")


func _sfx_canonical(key: String) -> String:
	return str(_sfx_aliases.get(key,key))


func _get_stream(group: String, key: String) -> AudioStream:
	var canonical := _sfx_canonical(key) if group == "sfx" else key
	var entries: Dictionary = _manifest.get(group, {})
	var entry: Dictionary = entries.get(canonical, {})
	if entry.is_empty():
		playback_failed.emit(key, "Unknown original audio cue")
		return null
	# Keep the unverified generic attack/death names silent independently of
	# their verified numeric requests used by specific source effect programs.
	var requested:Dictionary = entries.get(key,entry)
	if not bool(entry.get("default_enabled", true)) or not bool(requested.get("default_enabled",true)):
		return null
	var path := String(entry.get("path", ""))
	if group == "sfx" and not path.begins_with("res://assets/sfx/"):
		playback_failed.emit(key, "Original campaign SFX must use a new sound-effect resource")
		return null
	# 0x12's menu_move/hp_tick names share one resource and one cached stream.
	# The requested entry's policy is checked before this shared cache, so a
	# cached numeric request cannot bypass a disabled generic alias.
	var cache_key := group + ":" + canonical
	if _stream_cache.has(cache_key):
		return _stream_cache[cache_key] as AudioStream
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


func _active_envelope() -> float:
	return sin((1.0 - _crossfade_left / CROSSFADE_SECONDS) * PI * 0.5) if _crossfade_left > 0.0 else 1.0


func _apply_volume() -> void:
	var gain := _volume * MUSIC_GAIN * _fade_gain
	var mix := 1.0 - _crossfade_left / CROSSFADE_SECONDS
	var active_gain := _active_envelope()
	var previous_gain := _outgoing_start_gain * cos(mix * PI * 0.5) if _crossfade_left > 0.0 else 0.0
	_music_player.volume_db = linear_to_db(maxf(0.000001, gain * active_gain))
	_previous_music_player.volume_db = linear_to_db(maxf(0.000001, gain * previous_gain))
	_jingle_player.volume_db = linear_to_db(maxf(0.000001, gain))
	for player in _sfx_players:
		player.volume_db = linear_to_db(maxf(0.000001, _volume * SFX_GAIN))
	for player in _reviewed_players:
		player.volume_db = linear_to_db(maxf(.000001, _volume*SFX_GAIN*float(player.get_meta("reviewed_gain",1.0))))
	if _step_player!=null:_step_player.volume_db=linear_to_db(maxf(0.000001,_volume*SFX_GAIN))
	if _critical_sfx!=null:_critical_sfx.volume_db=linear_to_db(maxf(.000001,_volume*SFX_GAIN*_critical_gain))
	if _critical_music!=null:_critical_music.volume_db=linear_to_db(maxf(.000001,_volume*SFX_GAIN*_critical_gain*_critical_music_gain))


func _on_music_voice_finished(player: AudioStreamPlayer) -> void:
	if player == _music_player and not _music_key.is_empty():
		music_finished.emit(_music_key)


func _on_jingle_finished() -> void:
	if not _jingle_active:
		return
	var finished_key := _jingle_key
	_jingle_key = ""
	_jingle_active = false
	if _music_enabled and _music_pending_start and not _critical_active:
		_music_player.stream_paused = false
		_music_player.play(_pending_music_position)
		_music_pending_start = false
	_music_player.stream_paused = not _music_enabled or _critical_active
	_previous_music_player.stream_paused = not _music_enabled or _critical_active
	jingle_finished.emit(finished_key)


func begin_critical_audio(sfx: AudioStream, theme: AudioStream, gain: float=1.0) -> void:
	_ensure_initialized()
	finish_critical_audio()
	_critical_active=true;_critical_time=0.;_critical_gain=gain;_critical_music_gain=pow(10.,-8./20.)
	_music_player.stream_paused=true;_previous_music_player.stream_paused=true
	_critical_sfx.stream=sfx;_critical_music.stream=theme
	_apply_volume()
	if _sfx_enabled and sfx!=null:_critical_sfx.play()
	if _music_enabled:_critical_music.play()

func sync_critical_audio(time: float, speed: float, theme_gain: float) -> void:
	if not _critical_active:return
	_critical_time=time;_critical_music_gain=theme_gain
	for row in [[_critical_sfx,_sfx_enabled],[_critical_music,_music_enabled]]:
		var player: AudioStreamPlayer=row[0];var enabled=bool(row[1])
		player.pitch_scale=clampf(speed,.05,4.)
		if not enabled:
			player.stop()
		elif player.stream!=null:
			if not player.playing and time<player.stream.get_length():player.play(time)
			elif player.playing and absf(player.get_playback_position()-time)>.18:player.seek(time)
	_apply_volume()

func finish_critical_audio() -> void:
	if not _critical_active:return
	_critical_active=false
	_critical_sfx.stop();_critical_music.stop();_critical_sfx.stream=null;_critical_music.stream=null
	if _music_pending_start and _music_enabled and not _jingle_active:
		_music_player.stream_paused=false
		_music_player.play(_pending_music_position)
		_music_pending_start=false
	_music_player.stream_paused=not _music_enabled or _jingle_active
	_previous_music_player.stream_paused=not _music_enabled or _jingle_active
	_critical_time=0.;_critical_gain=1.;_critical_music_gain=1.
	_apply_volume()
