extends SceneTree
## Dedicated themes/effects must respect mute, seek, exit, and the suspended score.
const Audio=preload("res://core/original_audio.gd")
const Cinema=preload("res://core/critical_cinema.gd")
var errors=[]
var checks=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func run():
	var audio=Audio.new();root.add_child(audio);audio.set_process(false)
	audio.play_music("rm_duel_urgent");await create_timer(.15).timeout
	var before=audio._music_player.get_playback_position();var stream=audio._music_player.stream;var key=audio._music_key
	for hero in ["hunapu","eileen"]:
		var spec=Cinema.data().cases[hero+"-sword"]
		audio.begin_critical_audio(load(spec.sfx),load(Cinema.data().themes[hero]),float(spec.audio_gain))
		check(audio._critical_active and audio._music_player.stream_paused,"exclusive "+hero+" theme pauses score")
		await create_timer(.12).timeout
		check(absf(audio._music_player.get_playback_position()-before)<.04,"suspended score keeps exact cue position "+hero)
		audio.sync_critical_audio(2.,3.,.12)
		check(is_equal_approx(audio._critical_sfx.pitch_scale,3.) and is_equal_approx(audio._critical_music.pitch_scale,3.),"SFX and theme follow accelerated source clock "+hero)
		check(audio._critical_sfx.playing and audio._critical_music.playing,"both exclusive streams are active "+hero)
		audio.set_music_enabled(false);audio.set_sfx_enabled(false);audio.sync_critical_audio(2.1,1.,.3)
		check(not audio._critical_sfx.playing and not audio._critical_music.playing and audio._music_player.stream_paused,"mute silences streams without resuming score "+hero)
		audio.set_music_enabled(true);audio.set_sfx_enabled(true);audio.sync_critical_audio(2.2,1.,.3)
		check(audio._critical_sfx.playing and audio._critical_music.playing and audio._music_player.stream_paused,"unmute resumes current critical time only "+hero)
		audio.finish_combat_sfx()
		check(not audio._critical_active and audio._critical_music.stream==null and audio._critical_sfx.stream==null,"scene exit frees both exclusive streams "+hero)
		check(audio._music_player.stream==stream and audio._music_key==key and not audio._music_player.stream_paused,"same score resumes after critical "+hero)
		before=audio._music_player.get_playback_position()
	var spec=Cinema.data().cases["hunapu-sword"]
	audio.begin_critical_audio(load(spec.sfx),load(Cinema.data().themes.hunapu));audio.set_music_enabled(false);audio.finish_critical_audio()
	check(audio._music_player.stream_paused,"finish respects music mute")
	audio.stop_all();check(not audio._critical_active and not audio._music_player.playing,"stop_all leaves no music playing")
	var f=FileAccess.open("res://reports/critical-cinema-20261104/audio.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors},"  "));f.close()
	stream=null;audio.stop_all();await create_timer(.12).timeout;audio.queue_free();await process_frame;print("CRITICAL_AUDIO ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
