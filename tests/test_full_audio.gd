extends SceneTree

var checks := 0
var failures: Array[String] = []

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var audio = load("res://core/original_audio.gd").new()
	root.add_child(audio)
	await process_frame
	audio.set_process(false)
	audio.set_music_enabled(false)
	var rejected: Array[String] = []
	audio.playback_failed.connect(func(key, reason): rejected.append(key + ": " + reason))
	var world := [0xA0, 0xB7, 0x94, 0x96, 0x83]
	for chapter in range(1, 6):
		audio.play_world(chapter)
		check(audio._music_key == "request_%02X" % world[chapter - 1], "world chapter %d" % chapter)
	for route in ["alm", "celica"]:
		var route_index := 1 if route == "celica" else 0
		for phase in ["player", "enemy"]:
			for remaining in [0, 1, 2, 8]:
				var expected: int = [0x70, 0x77][route_index] if phase == "enemy" else ([0xA3, 0xA7][route_index] if remaining < 2 else [0xA1, 0xA4][route_index])
				audio.play_battle(route, phase, remaining)
				check(audio._music_key == "request_%02X" % expected, "route/phase/remaining %s/%s/%d" % [route, phase, remaining])
				for low_hp in [false, true]:
					audio.play_battle(route, phase, remaining, true, low_hp)
					check(audio._music_key == ("request_B5" if phase == "enemy" else "request_B4"), "final music uses army phase, not Duma form")
	for hub in [1, 5, 25, 37, 110, 111, 112, 120, 127]:
		# Original L0CB222 only reads its table below 111; later raw bytes
		# happen to look like indexes but are not used by the source routine.
		var expected: int = {1:0xA6, 5:0x93, 25:0x95, 37:0xB5, 110:0xB5}.get(hub, 0x95)
		audio.play_hub(hub)
		check(audio._music_key == "request_%02X" % expected, "hub music %d" % hub)
	var previous: String = audio._music_key
	for request in [0x74, 0x75, 0x92, 0x97, 0xB1]:
		audio.play_request(request)
		check(audio._music_key == previous, "null music pointer preserves active track")
	var duel_cases := [
		[{"character_id":190,"class_id":14},false,false,false,0x86],
		[{"character_id":190,"class_id":14},true,false,false,0x80],
		[{"character_id":190,"class_id":14},false,false,true,0xB0],
		[{"character_id":190,"class_id":14},true,false,true,0x80],
		[{"character_id":129,"class_id":14},false,false,false,0x76],
		[{"character_id":129,"class_id":14},true,false,false,0x76],
		[{"character_id":128,"class_id":21},false,false,true,0xA5],
		[{"character_id":128,"class_id":21},true,false,true,0xA5],
		[{"character_id":128,"class_id":21},false,true,true,0xA2]]
	for duel in duel_cases:
		audio.play_combat({},duel[0],duel[1],duel[2],duel[3])
		check(audio._music_key == "request_%02X" % duel[4], "duel source music precedence")
	audio.play_ending()
	check(audio._music_key == "request_73", "ending source L04B0F9")
	audio.play_request(0x95)
	previous = audio._music_key
	audio.set_music_enabled(true)
	await process_frame
	for request in [0x14, 0x20, 0x24, 0x30, 0x34, 0x35, 0x57, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67]:
		audio.play_request(0x01)
		await process_frame
		check(audio._sfx_players[0].playing or audio._sfx_players[1].playing, "effect started before null pointer")
		audio.play_request(request)
		check(not audio._sfx_players[0].playing and not audio._sfx_players[1].playing and audio._sfx_players[0].stream == null and audio._sfx_players[1].stream == null, "all null SFX requests stop effect %02X" % request)
		check(audio._music_key == previous and audio._music_player.playing, "SFX stop preserves music")
	for request in [0x82, 0x84, 0xB6]:
		var music_player_id: int = audio._music_player.get_instance_id()
		audio.play_request(request)
		await process_frame
		check(audio._jingle_active and audio._jingle_key == "request_%02X" % request, "source temporary music uses jingle %02X" % request)
		check(audio._jingle_player.stream.get_length() < 2.1 and not audio._jingle_player.stream.loop, "temporary music stops at source return to previous track")
		check(audio._music_key == previous and audio._music_player.stream_paused, "temporary music preserves previous track")
		audio._jingle_player.stop()
		audio._jingle_player.finished.emit()
		check(not audio._jingle_active and not audio._music_player.stream_paused and audio._music_player.get_instance_id() == music_player_id, "temporary music resumes same player")
	audio.play_request(0x01)
	await process_frame
	audio.play_request(0x56)
	check(is_equal_approx(audio._fade_left, audio.SOURCE_FADE_SECONDS), "source fade starts at 128 NTSC frames")
	audio._process(audio.SOURCE_FADE_SECONDS / 2.0)
	check(is_equal_approx(audio._fade_gain, 0.5), "fade progresses by elapsed time")
	check(is_equal_approx(db_to_linear(audio._music_player.volume_db), 0.25), "fade changes music gain")
	check(is_equal_approx(db_to_linear(audio._sfx_players[0].volume_db), audio.SFX_GAIN), "fade preserves effect gain")
	audio.play_request(0x56)
	check(is_equal_approx(audio._fade_gain, 0.5), "repeated fade request does not reset driver fade")
	audio._process(audio.SOURCE_FADE_SECONDS)
	check(audio._music_key.is_empty() and audio._music_player.stream == null, "fade terminates active music")
	audio.play_request(0x95)
	await process_frame
	audio.play_request(0x56)
	audio._process(audio.SOURCE_FADE_SECONDS / 2.0)
	audio.play_request(0x95)
	check(audio._fade_left == 0.0 and audio._fade_gain == 1.0, "explicit new music request cancels source fade")
	audio.play_request(0x82)
	await process_frame
	audio.play_request(0x56)
	audio.play_request(0x00)
	check(audio._music_key.is_empty() and not audio._jingle_active and audio._fade_left == 0.0, "stop all clears music, jingle and fade state")
	check(audio._music_player.stream == null and audio._jingle_player.stream == null and audio._sfx_players[0].stream == null and audio._sfx_players[1].stream == null, "stop all releases every playback stream")
	check(rejected.is_empty(), "all verified audio requests load without failure: " + str(rejected))
	var report := {"checks":checks, "failures":failures, "scope":"Original control requests, route/chapter/army-phase music, hub threshold, temporary music resume and native fade duration", "limitation":"Mixed Ogg fade follows the source 128-frame overall duration; original independent APU channel envelope steps cannot be reproduced from mixed audio."}
	var output := FileAccess.open("res://reports/full-audio-routing-verification.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "  ") + "\n")
	output.close()
	print("FE_FULL_AUDIO_ROUTING_CHECK ", checks, " checks; failures=", failures)
	audio.queue_free()
	await create_timer(0.2).timeout
	quit(0 if failures.is_empty() else 1)
