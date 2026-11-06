extends SceneTree
const Audio = preload("res://core/original_audio.gd")
const Routing = preload("res://core/soundtrack_routing.gd")
class AudioHost extends Node:
	var game: Dictionary = {"mode":"title", "chapter":1, "stage_id":101, "hub_record":"H01", "battle_outcome":"", "battle_settled":false}
	var view := "title"
	var plot_callback := ""
	var plot_return := "hub"
	var journey: Dictionary = {"intent":"load", "return_view":"title"}
	var training_reward_open := false
	var combat: Dictionary = {}
var checks := 0
var failures: Array = []
var changes: Array = []
var jingles: Array = []
var playback_errors: Array = []
func _initialize() -> void:
	call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)
func run() -> void:
	var score: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/soundtrack.json"))
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/full_audio.json"))
	var aliases: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/audio.json"))
	check(score.tracks.size() == 28, "28 original compositions")
	check(score.routing.stage_by_id.size() == 40, "40 actual battle IDs mapped")
	check(score.routing.hub_by_id.size() == 42, "42 actual hub IDs mapped")
	for request in source.music_by_request:
		var id := Routing.resolve(score, "request_" + str(request))
		check(not id.is_empty() and score.tracks.has(id), "legacy music mapped " + str(request))
		check(str(score.tracks[id].path).begins_with("res://assets/music/20261024/"), "original music path " + str(request))
	for alias in aliases.music:
		check(not Routing.resolve(score, str(alias)).is_empty(), "named alias " + str(alias))
	for entry in score.routing.stage_details:
		var id := Routing.stage_track(score, int(entry.id))
		check(id == str(entry.track_id), "actual stage " + str(entry.code))
		for phase_view in ["battle", "reward", "battle_story", "victory"]:
			check(Routing.context_track(score, {"view":phase_view,"mode":"battle","stage_id":entry.id}) == id, str(entry.code) + " continuous " + phase_view)
		check(Routing.context_track(score,{"view":"combat","mode":"battle","stage_id":entry.id})=="rm_duel_urgent",str(entry.code)+" attack uses urgent duel variant")
	for room in score.routing.hub_by_id:
		check(Routing.context_track(score,{"view":"hub","mode":"hub","hub_record":room}) == score.routing.hub_by_id[room], "hub " + str(room))
	for chapter in range(1,6):
		check(Routing.context_track(score,{"view":"world","mode":"world","chapter":chapter}) == "rm_world_ch"+str(chapter), "world chapter " + str(chapter))
	check(Routing.stage_track(score, 534) == "rm_battle_final", "J54 actual 534 selects final theme")
	check(Routing.resolve(score, "request_86", {"view":"combat","mode":"battle","stage_id":534}) == "rm_duel_urgent", "finale attack uses urgent owned variant")
	check(Routing.resolve(score, "request_A2", {"view":"combat","mode":"battle","stage_id":203,"combat_support":true}) == "rm_battle_tide", "support keeps current battle music")
	check(Routing.resolve(score, "levelup", {"view":"combat","mode":"battle","stage_id":203}) == "rm_jingle_growth", "jingle is not replaced by background context")
	check(Routing.context_track(score,{"view":"plot","mode":"hub","hub_record":"H30","plot_callback":"third_prologue","plot_return":"hub"}) == "rm_story_divine", "major plot callback selects divine dialogue")
	check(Routing.resolve(score,"unrecognized_legacy_music").is_empty(), "unknown music cannot fall back to original recording")
	var host := AudioHost.new()
	var audio := Audio.new()
	host.add_child(audio)
	root.add_child(host)
	audio.set_process(false)
	audio.music_changed.connect(func(id): changes.append(id))
	audio.jingle_started.connect(func(id): jingles.append(id))
	audio.playback_failed.connect(func(id, reason): playback_errors.append([id,reason]))
	# Synthetic PCM fixtures exercise real AudioStreamPlayer lifecycle without
	# claiming generated assets exist or changing the runtime asset manifest.
	var bed := AudioStreamWAV.new()
	bed.format = AudioStreamWAV.FORMAT_16_BITS
	bed.mix_rate = 44100
	bed.loop_mode = AudioStreamWAV.LOOP_FORWARD
	bed.loop_end = 44100 * 4
	var pcm := PackedByteArray()
	pcm.resize(44100 * 4 * 2)
	bed.data = pcm
	var cue := AudioStreamWAV.new()
	cue.format = AudioStreamWAV.FORMAT_16_BITS
	cue.mix_rate = 44100
	pcm = PackedByteArray()
	pcm.resize(4410 * 2)
	cue.data = pcm
	for id in score.tracks:
		audio._stream_cache["music:" + str(id)] = cue if score.tracks[id].kind == "jingle" else bed
	for id in score.get("additional_tracks",{}):audio._stream_cache["music:"+str(id)]=bed
	audio.play_music("title")
	check(audio._music_key == "rm_title" and audio._music_player.playing, "title starts original score")
	host.game.mode = "battle"; host.view = "battle"; host.game.stage_id = 101
	audio.play_battle("alm","player",5,false)
	check(audio._music_key == "rm_battle_snow" and audio._crossfade_left > 0.0, "title to map uses crossfade")
	check(audio._previous_music_player.playing, "outgoing music remains during crossfade")
	audio._process(0.61)
	check(not audio._previous_music_player.playing and audio._previous_music_player.stream == null, "outgoing stream released after crossfade")
	await create_timer(0.12).timeout
	var before := audio._music_player.get_playback_position()
	var count := changes.size()
	var voice = audio._music_player
	for phase in ["player","enemy"]:
		for remaining in [5,1]:
			audio.play_battle("alm",phase,remaining,false)
			audio.play_combat({}, {},false,true,false)
	check(changes.size() == count and audio._music_player == voice, "support last enemy and both phases never restart map BGM")
	check(audio._music_player.get_playback_position() >= before, "same-track playback position is preserved")
	host.view="combat";host.combat={"support":false}
	audio.play_combat({}, {"class_id":21,"character_id":129},true,false,false)
	check(audio._music_key=="rm_duel_urgent" and is_equal_approx(audio._music_player.pitch_scale,1.12),"attack enters urgent 1.12x variant")
	var saved_map_position=audio._duel_map_position
	count=changes.size();audio._process(.61);audio.play_combat({}, {},false,false,false)
	check(changes.size()==count and audio._music_key=="rm_duel_urgent","context sync and repeated strikes keep duel position")
	host.view="battle";host.combat={};audio.play_battle("alm","player",5,false);audio._process(.61)
	check(audio._music_key=="rm_battle_snow" and is_equal_approx(audio._music_player.pitch_scale,1.0),"duel exit restores map and normal pitch")
	check(is_equal_approx(audio._pending_music_position,saved_map_position),"duel exit resumes map from saved position")
	host.view="combat";audio.play_combat({}, {},false,false,false)
	saved_map_position=audio._duel_map_position
	host.view="plot";host.plot_callback="third_prologue";audio._process(.1)
	check(audio._music_key=="rm_story_divine" and audio._duel_map_key=="rm_battle_snow","post-contact story preserves map checkpoint")
	host.view="battle";host.plot_callback="";audio.play_battle("alm","player",5,false)
	check(is_equal_approx(audio._pending_music_position,saved_map_position),"map resumes after intervening story")
	audio.set_music_enabled(false);host.view="combat";audio.play_combat({}, {})
	saved_map_position=audio._duel_map_position
	host.view="battle";audio.play_battle("alm","player",5,false)
	check(audio._music_pending_start and is_equal_approx(audio._pending_music_position,saved_map_position),"muted duel return preserves pending map position")
	audio.set_music_enabled(true);audio._process(.61)
	voice=audio._music_player
	before = audio._music_player.get_playback_position()
	audio.play_jingle("levelup")
	check(audio._jingle_active and audio._music_player.stream_paused, "growth jingle pauses original bed")
	await create_timer(0.24).timeout
	check(not audio._jingle_active and not audio._music_player.stream_paused, "growth jingle automatically resumes bed")
	check(audio._music_player == voice and audio._music_player.get_playback_position() >= before, "jingle does not reset underlying voice or position")
	audio.set_music_enabled(false)
	check(audio._music_player.stream_paused and audio.sfx_enabled, "music mute leaves SFX enabled")
	host.game.stage_id = 534
	audio.play_battle("joint","enemy",8,false)
	check(audio._music_key == "rm_battle_final" and audio._music_pending_start and not audio._music_player.playing, "muted new finale prepared without source stage 62")
	audio.play_battle("joint","player",1,false)
	check(audio._music_pending_start, "muted repeat retains one pending start")
	audio.set_music_enabled(true)
	check(audio._music_player.playing and not audio._music_pending_start, "unmute starts latest prepared original track")
	audio.set_volume(0.3)
	check(is_equal_approx(db_to_linear(audio._music_player.volume_db),0.3 * audio.MUSIC_GAIN), "volume applied once without stacked gain")
	audio.set_sfx_enabled(false)
	check(not audio.sfx_enabled and audio._music_player.playing, "SFX mute leaves music playing")
	audio.set_sfx_enabled(true)
	for key in aliases.sfx:
		var effect: Dictionary = audio._manifest.sfx[key]
		check(str(effect.path).begins_with("res://assets/sfx/20261024/") and effect.default_enabled == aliases.sfx[key].default_enabled and effect.manual_stop == aliases.sfx[key].manual_stop, "named SFX replaced with source enable/stop rules retained " + str(key))
	for key in source.sfx_by_request:
		var effect: Dictionary = audio._manifest.sfx["request_" + str(key)]
		var verified_enabled:bool = bool(source.sfx_by_request[key].default_enabled) or key in ["21","53"]
		check(str(effect.path).begins_with("res://assets/sfx/20261024/") and effect.default_enabled == verified_enabled and effect.manual_stop == source.sfx_by_request[key].manual_stop, "SFX resource replaced with verified request enablement and source stop rules " + str(key))
	# A major dialogue may change BGM; ordinary pages keep the room's track.
	host.game.mode = "hub"; host.game.hub_record = "H30"; host.view = "hub"
	audio.play_music("village"); audio._process(0.61)
	check(audio._music_key == "rm_prologue", "legacy village call resolves actual story hub")
	host.view = "plot"; host.plot_callback = "third_prologue"
	audio._process(0.1)
	check(audio._music_key == "rm_story_divine", "live major story context changes music")
	host.view = "hub";host.plot_callback = "";audio._process(0.61)
	check(audio._music_key == "rm_prologue", "dialogue end returns to room score")
	# Save slots are an overlay, not a return to the title screen.
	for origin in ["world", "hub", "battle"]:
		host.view = origin;host.game.mode = origin;audio._process(0.61)
		var unchanged_key: String = audio._music_key
		count = changes.size();voice = audio._music_player
		host.journey = {"intent":"save", "return_view":origin}
		host.view = "journal";audio._process(0.1)
		host.view = "journal_confirm";audio._process(0.1)
		host.view = origin;audio._process(0.1)
		check(changes.size() == count and audio._music_player == voice and audio._music_key == unchanged_key, "save and overwrite keep " + origin + " track and position")
	host.game.mode = "battle";host.view = "battle";host.game.stage_id = 101
	audio.play_battle("alm","player",5,false);audio._process(0.61)
	host.game.stage_id = 201;audio.play_battle("celica","player",5,false);audio._process(0.2)
	var outgoing_level: float = db_to_linear(audio._music_player.volume_db)
	host.game.stage_id = 534;audio.play_battle("joint","player",5,false)
	check(is_equal_approx(db_to_linear(audio._previous_music_player.volume_db),outgoing_level), "rapid transition preserves the outgoing voice gain")
	check(audio._music_key == "rm_battle_final" and audio._music_player.playing and audio._previous_music_player.playing, "rapid transition has only latest target and one outgoing voice")
	audio._process(0.2)
	var left: float = audio._crossfade_left
	audio.set_volume(0.2)
	check(is_equal_approx(db_to_linear(audio._music_player.volume_db),0.2 * audio.MUSIC_GAIN * audio._active_envelope()), "volume change honors incoming fade envelope")
	check(db_to_linear(audio._previous_music_player.volume_db) <= 0.2 * audio.MUSIC_GAIN, "volume change honors outgoing fade envelope")
	audio.set_music_enabled(false);audio._process(1.0)
	check(is_equal_approx(audio._crossfade_left,left) and audio._music_player.stream_paused and audio._previous_music_player.stream_paused, "mute pauses both voices and fade clock")
	audio.set_music_enabled(true)
	audio.play_jingle("levelup")
	check(audio._music_player.stream_paused and audio._previous_music_player.stream_paused, "jingle freezes both crossfading voices")
	audio.set_volume(0.4)
	check(is_equal_approx(db_to_linear(audio._jingle_player.volume_db),0.4 * audio.MUSIC_GAIN), "jingle follows live volume exactly once")
	audio.set_music_enabled(false);audio._process(1.0)
	await create_timer(0.16).timeout
	check(audio._jingle_active and audio._jingle_player.stream_paused and is_equal_approx(audio._crossfade_left,left), "muted jingle does not finish or advance fade")
	audio.set_music_enabled(true)
	await create_timer(0.24).timeout
	check(not audio._jingle_active and not audio._music_player.stream_paused and not audio._previous_music_player.stream_paused, "unmuted jingle resumes paused crossfade voices")
	audio._process(0.61)
	check(audio._music_key == "rm_battle_final" and not audio._previous_music_player.playing, "rapid fade ends on latest requested final theme")

	# Victory notification is single-owned by a battle that was actually active.
	host.view = "battle";host.game.mode = "battle";host.game.battle_outcome = "";host.game.battle_settled = false
	audio._process(0.1)
	# This is main.play_victory_rewards' real ordering: settlement changes
	# mode first, opens a reward view and plays levelup before the next frame.
	host.view = "reward";host.game.mode = "victory";host.game.battle_outcome = "victory";host.game.battle_settled = true
	host.training_reward_open = true;audio.play_jingle("levelup")
	count = jingles.size();audio._process(0.1)
	check(jingles.size() == count and audio._jingle_key == "rm_jingle_growth" and audio._battle_was_active, "pending victory does not interrupt settlement levelup")
	await create_timer(0.24).timeout
	audio._process(0.1)
	check(jingles.size() == count and audio._battle_was_active, "victory remains pending while reward UI is open")
	host.training_reward_open = false;host.view = "battle_story";audio._process(0.1)
	check(jingles.size() == count, "victory waits through postbattle story")
	host.view = "victory";audio._process(0.1);audio._process(0.1)
	check(jingles.size() == count+1 and jingles.back() == "rm_jingle_victory", "victory cue plays once after settlement sequence")
	audio.stop_all();host.view = "defeat";host.game.mode = "defeat";audio.play_jingle("unit_death")
	await create_timer(0.24).timeout
	audio._process(0.1)
	check(audio._music_key.is_empty() and not audio._music_player.playing, "defeat cue does not restart stopped battle")
	check(playback_errors.is_empty(), "no fixture playback errors")
	var resource_checks := OS.get_environment("SOUNDTRACK_CHECK_ASSETS") == "1"
	if resource_checks:
		audio.stop_all();audio._stream_cache.clear()
		for id in score.tracks:
			var stream = audio._get_stream("music",str(id))
			check(stream != null and stream.get_length() > 0.0, "actual generated resource loads " + str(id))
			if stream is AudioStreamOggVorbis:
				check(stream.loop == bool(score.tracks[id].loop), "actual loop metadata " + str(id))
				check(absf(stream.get_length() - float(score.tracks[id].duration)) < 0.05, "actual imported duration " + str(id))
	var report := {"passed":failures.is_empty(),"checks":checks,"failures":failures,"actual_generated_assets_checked":resource_checks,"fixture":"Synthetic PCM, real AudioStreamPlayer lifecycle; no visible window or GPU rendering","music_changes":changes,"jingles":jingles,"scope":"40 stage identities, 42 hubs, 35 source music requests, attack duel variant and saved map-position restoration, support continuity, repeated phase stability, crossfade, jingle resume, mute, defeat, SFX source enable/stop rules"}
	var report_path := OS.get_environment("SOUNDTRACK_TEST_REPORT")
	if report_path.is_empty(): report_path = "/private/tmp/soundtrack-routing-report.json"
	var file := FileAccess.open(report_path,FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(report,"  "));file.close()
	else:
		check(false,"report destination is writable")
	print("SOUNDTRACK_TEST ",JSON.stringify(report))
	host.queue_free();await process_frame
	quit(0 if failures.is_empty() else 1)
