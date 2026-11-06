extends SceneTree
## Headless/Dummy native mixer fixture. Does not load a save or open a window.
const CampaignAudio = preload("res://core/original_audio.gd")
const OUT := "res://reports/audio-content-review-20261024/native-engine-mix.wav"
class ReviewHost:
	extends Node
	var game: Variant = null

func _initialize() -> void:
	Engine.max_fps = 60
	call_deferred("_record")

func _record() -> void:
	var bus := AudioServer.bus_count
	AudioServer.add_bus()
	AudioServer.set_bus_name(bus,"AudioReviewCapture")
	AudioServer.set_bus_send(bus,"Master")
	var recorder := AudioEffectRecord.new()
	recorder.format = AudioStreamWAV.FORMAT_16_BITS
	AudioServer.add_bus_effect(bus,recorder)
	var host := ReviewHost.new()
	root.add_child(host)
	var campaign := CampaignAudio.new()
	host.add_child(campaign)
	await process_frame
	for child in campaign.get_children():
		if child is AudioStreamPlayer:
			child.bus = "AudioReviewCapture"
	recorder.set_recording_active(true)
	campaign.play_music("rm_battle_snow")
	await create_timer(.20).timeout
	campaign.play_request(0x23)
	await create_timer(32.0/60.0988).timeout
	campaign.play_request(0x30)
	await create_timer(.25).timeout
	campaign.play_request(0x53)
	await create_timer(3.0/60.0988).timeout
	campaign.play_sfx("hit")
	await create_timer(11.0/60.0988).timeout
	for i in range(4):
		campaign.play_sfx("hp_tick")
		await create_timer(1.0/60.0988).timeout
	await create_timer(.45).timeout
	campaign.play_sfx("miss")
	await create_timer(.35).timeout
	campaign.play_request(0x21)
	await create_timer(.9).timeout
	campaign.play_request(0x30)
	campaign.play_jingle("rm_jingle_growth")
	await create_timer(3.1).timeout
	recorder.set_recording_active(false)
	var rendered: AudioStreamWAV = recorder.get_recording()
	var error := rendered.save_to_wav(OUT)
	campaign.stop_all()
	host.queue_free()
	await process_frame
	await process_frame
	print(JSON.stringify({"native_engine_fixture":true,"output":OUT,
		"pcm_bytes":rendered.data.size(),"sample_rate":rendered.mix_rate,
		"save_error":error,"iphone_accessed":false,"save_loaded":false}))
	quit(0 if error == OK and rendered.data.size() > 1000 else 1)
