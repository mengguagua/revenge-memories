extends SceneTree
## Real engine mixer, no visible window, speakers, game saves or device access.
const Audio=preload("res://core/original_audio.gd")
const OUT="res://reports/iphone16-feedback-20261024/"
class Host extends Node:
	var game={"mode":"battle","chapter":1,"stage_id":101,"battle_outcome":"","battle_settled":false}
	var view="battle"
	var combat={}
	var journey={}
	var training_reward_open=false
var events=[]
func _initialize():call_deferred("run")
func run():
	var bus=AudioServer.bus_count;AudioServer.add_bus();AudioServer.set_bus_name(bus,"FieldReview");AudioServer.set_bus_send(bus,"Master")
	var recorder=AudioEffectRecord.new();recorder.format=AudioStreamWAV.FORMAT_16_BITS;AudioServer.add_bus_effect(bus,recorder)
	var host=Host.new();var audio=Audio.new();host.add_child(audio);root.add_child(host)
	for child in audio.get_children():
		if child is AudioStreamPlayer:child.bus="FieldReview"
	var start=Time.get_ticks_msec()
	audio.sfx_played.connect(func(key):events.append({"at_ms":Time.get_ticks_msec()-start,"sfx":key}))
	audio.music_changed.connect(func(key):events.append({"at_ms":Time.get_ticks_msec()-start,"music":key}))
	recorder.set_recording_active(true);audio.play_battle("alm","player",5)
	await create_timer(1.).timeout
	for i in range(5):audio.play_map_step({"class_id":21});await create_timer(.22).timeout
	host.view="combat";host.combat={"support":false};audio.play_combat({}, {})
	await create_timer(5.).timeout
	host.view="battle";host.combat={};audio.play_battle("alm","player",5)
	await create_timer(2.).timeout
	recorder.set_recording_active(false)
	var wav=recorder.get_recording();var code=wav.save_to_wav(OUT+"map-walk-duel-return.wav")
	var file=FileAccess.open(OUT+"native-audio-events.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"events":events,"pcm_bytes":wav.data.size(),"mix_rate":wav.mix_rate,"save_error":code,"map_resume_position":audio._pending_music_position,"iphone_accessed":false,"speaker_output":false},"  "));file.close()
	audio.stop_all();host.queue_free();await process_frame
	AudioServer.remove_bus(bus)
	print("FIELD_AUDIO_RECORD ",wav.data.size()," bytes; error=",code)
	quit(0 if code==OK and wav.data.size()>1000 else 1)
