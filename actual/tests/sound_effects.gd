extends SceneTree
const Audio=preload("res://core/original_audio.gd")
const BattlePlayer=preload("res://core/battle_animation.gd")
const MapEffects=preload("res://core/map_effects.gd")
class TraceAudio extends "res://core/original_audio.gd":
	var requests: Array=[]
	func play_request(request:int)->void:
		requests.append(request);super.play_request(request)
class Host extends Node:
	var game={"mode":"title","chapter":1,"stage_id":101,"hub_record":"H01","battle_outcome":"","battle_settled":false}
	var view="title"
	var journey={"intent":"load","return_view":"title"}
	var plot_callback=""
	var plot_return="hub"
	var training_reward_open=false
class FrameUI extends RefCounted:
	var audio
	var game
	var instant_mode=false
	var combat_poses={}
	var combat_offsets={}
	var combat_hp={}
	var combat_fades={}
	var combat_message=""
	var combat_hit_id=""
	var map_actor_alpha={}
	var map_offset=Vector2.ZERO
	var self_modulate=Color.WHITE
	func queue_redraw():pass
	func _focus_battle(_at:Vector2i,_force:bool):pass
	func _wait(_seconds:float):pass
	func _contact(_event:Dictionary):pass
	func effective_animation_speed()->float:return 1.0
class FixtureGame extends RefCounted:
	func find_unit(id:String)->Dictionary:return {"id":id,"hp":20}
class ActionPlayer extends "res://core/battle_animation.gd":
	func sprite(_unit:Dictionary)->Dictionary:return {"sequences":{"idle":[0]}}
	func selection(_event:Dictionary)->Dictionary:
		return {"kind":"source","key":"single_effect_lifecycle","variant":{"frames":[{"frame":0,"sound_requests":[83]}],"contact_tick":0}}
class MockAudio extends RefCounted:
	var requests=[]
	func play_request(request:int):requests.append(request)
var checks=[]
var errors=[]
var playback_errors=[]
var played=[]
var traces=[]
var audio
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func stopped()->bool:return audio._sfx_players.all(func(p):return not p.playing and p.stream==null)
func any_sfx()->bool:return audio._sfx_players.any(func(p):return p.playing)
func active_keys()->Array:return audio._sfx_players.filter(func(p):return p.playing).map(func(p):return str(p.get_meta("campaign_sfx_key","")))
func fixture(seconds:float,loop:bool=false)->AudioStreamWAV:
	var stream=AudioStreamWAV.new();stream.format=AudioStreamWAV.FORMAT_16_BITS;stream.mix_rate=22050
	var bytes=PackedByteArray();bytes.resize(int(seconds*22050)*2);stream.data=bytes
	if loop:stream.loop_mode=AudioStreamWAV.LOOP_FORWARD;stream.loop_end=int(seconds*22050)
	return stream
func run():
	var source=JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/full_audio.json"))
	var old_named=JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/audio.json")).sfx
	var catalog=JSON.parse_string(FileAccess.get_file_as_string("res://data/sound_effects.json"))
	var plan=JSON.parse_string(FileAccess.get_file_as_string("res://reports/sfx-20261024/plan.json"))
	check(catalog.effects.size()==41 and catalog.request_aliases.size()==41 and catalog.named_aliases.size()==9,"41 unique effects cover41requests and9named aliases")
	check(catalog.old_path_aliases.size()==42 and catalog.old_path_aliases==plan.old_path_aliases,"all42 old physical SFX paths accounted for")
	check(catalog.request_aliases==plan.request_aliases and catalog.named_aliases==plan.named_aliases,"runtime aliases match independent source audit")
	var host=Host.new();root.add_child(host);audio=TraceAudio.new();host.add_child(audio);audio.set_process(false)
	audio.playback_failed.connect(func(key,reason):playback_errors.append([key,reason]))
	audio.sfx_played.connect(func(key):played.append(key))
	check(audio.full_manifest.control_requests==source.control_requests and source.control_requests.size()==15,"all15 source control requests retained")
	check(audio.full_manifest.ignored_requests==source.ignored_requests and source.ignored_requests.size()==5,"all5 ignored music requests retained")
	var finite=fixture(8);var bed=fixture(4,true);var cue=fixture(0.1)
	for key in audio.soundtrack.tracks:audio._stream_cache["music:"+str(key)]=cue if audio.soundtrack.tracks[key].kind=="jingle" else bed
	for request in source.sfx_by_request:
		var id=str(catalog.request_aliases[request]);var entry=catalog.effects[id];var old=source.sfx_by_request[request]
		check(entry.path=="res://assets/sfx/20261024/"+id+".ogg","new dedicated resource "+str(request))
		var verified_enabled=bool(old.default_enabled) or request in ["21","53"]
		check(entry.default_enabled==verified_enabled and entry.manual_stop==old.manual_stop and entry.loop==old.loop,"source manual-stop/finite-loop rules plus verified request enablement "+str(request))
		check(audio._manifest.sfx["request_"+request]==audio._manifest.sfx[id],"numeric request uses canonical entry "+str(request))
		if entry.default_enabled:audio._stream_cache["sfx:"+id]=finite
	for alias in old_named:
		var request="%02X"%str(old_named[alias].source_request).hex_to_int();var id=str(catalog.request_aliases[request])
		check(audio._sfx_canonical(alias)==id and audio._manifest.sfx[alias].path==audio._manifest.sfx["request_"+request].path,"named alias points to same resource "+str(alias))
		if alias in ["attack","death"]:
			check(audio._get_stream("sfx",alias)==null and audio._get_stream("sfx","request_"+request)!=null,"unverified generic alias remains disabled while verified numeric request is enabled "+str(alias))
		else:check(audio._get_stream("sfx",alias)==audio._get_stream("sfx","request_"+request),"named and numeric alias share identical cached stream "+str(alias))
	check(audio._get_stream("sfx","menu_move")==audio._get_stream("sfx","hp_tick"),"menu movement and HP tick share0x12 stream")
	for request in source.sfx_by_request:
		audio._stop_sfx();var count=played.size();audio.play_request(str(request).hex_to_int())
		var enabled=bool(source.sfx_by_request[request].default_enabled) or request in ["21","53"]
		check(played.size()==count+(1 if enabled else 0) and any_sfx()==enabled,"numeric request preserves enabled state "+str(request))
	for key in ["attack","death"]:
		audio._stop_sfx();var count=played.size();audio.play_sfx(key)
		check(stopped() and played.size()==count,"unverified generic alias remains silent "+key)
	for key in ["rm_sfx_21","rm_sfx_53"]:
		audio._stop_sfx();var count=played.size();audio.play_sfx(key)
		check(any_sfx() and played.size()==count+1,"verified canonical effect is enabled "+key)
	for request in [0x03,0x43]:
		audio._stop_sfx();audio.play_request(0x53);audio.play_request(0x23);audio.play_request(request)
		check(not active_keys().has("rm_sfx_53") and active_keys().has("rm_sfx_23") and active_keys().has("rm_sfx_%02x"%request),"hit/miss replaces only53 and keeps other effect "+str(request))
	host.view="combat";host.game.mode="battle";audio._stop_sfx();audio.play_request(0x53);audio.play_request(0x23)
	host.view="battle";audio._sync_context()
	check(not active_keys().has("rm_sfx_53") and active_keys().has("rm_sfx_23"),"leaving combat clears53 without preempting other effect")
	host.view="title";host.game.mode="title"
	# Test actual native player stop ordering in the same process frame, not a mock mixer.
	for request in source.control_requests:
		audio.stop_all();audio.play_music("rm_title");audio.play_request(0x23);audio.play_sfx("hp_tick")
		var control=str(source.control_requests[request]);var music=audio._music_player
		if control=="stop_all":audio.play_jingle("levelup")
		audio.play_request(str(request).hex_to_int())
		if control=="stop_sfx":
			check(stopped(),"same-frame control clears all pending SFX voices "+str(request))
			check(audio._music_player==music and music.playing and audio._music_key=="rm_title","SFX stop preserves BGM "+str(request))
		elif control=="stop_all":
			check(stopped() and audio._music_key.is_empty() and not audio._jingle_active and audio._jingle_player.stream==null,"stop_all clears SFX/music/jingle")
		else:
			check(is_equal_approx(audio._fade_left,audio.SOURCE_FADE_SECONDS) and any_sfx(),"source fade starts without stopping SFX")
			audio._process(audio.SOURCE_FADE_SECONDS/2.0);audio.play_request(0x56)
			check(is_equal_approx(audio._fade_gain,0.5),"repeated fade preserves128-frame source fade progress")
			audio._process(audio.SOURCE_FADE_SECONDS)
			check(audio._music_key.is_empty() and any_sfx(),"source fade ends only music")
	audio.stop_all();audio.play_request(0x23);audio.play_request(0x30);await process_frame
	check(stopped(),"same-frame play then stop stays stopped after audio frame")
	for request in source.ignored_requests:
		audio.play_music("rm_title");audio.play_request(0x23);var music=audio._music_player;var count=played.size()
		audio.play_request(str(request).hex_to_int())
		check(audio._music_player==music and music.playing and any_sfx() and played.size()==count,"ignored request preserves music and SFX "+str(request))
	audio.set_volume(0.3)
	check(audio._sfx_players.all(func(p):return is_equal_approx(db_to_linear(p.volume_db),0.3*audio.SFX_GAIN)),"master volume applies SFX gain once")
	audio.set_music_enabled(false);var count=played.size();audio.play_sfx("menu_confirm")
	check(played.size()==count+1 and any_sfx() and audio._music_player.stream_paused,"music mute leaves SFX audible")
	audio.set_sfx_enabled(false);count=played.size();audio.play_request(0x23)
	check(not any_sfx() and played.size()==count,"SFX mute stops active finite effect and rejects new requests")
	audio.set_music_enabled(true);check(audio._music_player.playing,"SFX mute does not stop BGM")
	audio.set_sfx_enabled(true);check(not any_sfx(),"unmuting SFX does not resurrect stopped effects")
	audio.play_request(0x23);audio.play_request(0x26);audio.play_sfx("hp_tick")
	check(audio._sfx_players.size()==2 and audio._sfx_players.all(func(p):return p.playing),"high-rate ticks retain original bounded two-voice replacement")
	# Existing animation frames dispatch original requests in their stored order.
	var frame_ui=FrameUI.new();frame_ui.audio=audio;frame_ui.game=FixtureGame.new();var animation=BattlePlayer.new(frame_ui)
	var programs=animation._source().variants
	for key in ["class_11_ally_item_23","class_11_ally_item_24","class_11_ally_item_25","class_11_ally_item_40"]:
		check(programs.has(key),"real source animation exists "+key)
		if not programs.has(key):continue
		var expected=[];audio.requests.clear();audio._stop_sfx()
		for i in range(programs[key].frames.size()):
			var frame:Dictionary=programs[key].frames[i]
			for request in frame.get("sound_requests",[]):expected.append(int(request))
			animation._source_frame({"attacker":"fixture-a","defender":"fixture-b"},frame,i,true)
		check(audio.requests==expected,"source combat frame order/count unchanged "+key)
		traces.append({"variant":key,"source_frames":programs[key].frames.size(),"requests":expected})
	var same_frame={"frame":0,"sound_requests":[0x23,0x30]}
	audio._stop_sfx();audio.requests.clear();animation._source_frame({"attacker":"a","defender":"b"},same_frame,0,true)
	check(audio.requests==[0x23,0x30] and stopped(),"same animation frame preserves start-then-stop order")
	same_frame.sound_requests=[0x30,0x03];audio.requests.clear();animation._source_frame({"attacker":"a","defender":"b"},same_frame,0,true)
	check(audio.requests==[0x30,0x03] and any_sfx(),"same animation frame preserves stop-then-impact order")
	frame_ui.instant_mode=true;audio.requests.clear();animation._source_frame({"attacker":"a","defender":"b"},same_frame,0,true)
	check(audio.requests.is_empty(),"instant simulation does not emit combat sound requests")
	frame_ui.instant_mode=false
	var action=ActionPlayer.new(frame_ui);audio._stop_sfx();audio.requests.clear()
	await action.play({"attacker":"a","defender":"b"})
	check(audio.requests==[0x53] and not active_keys().has("rm_sfx_53"),"real action lifecycle clears53 at completion without invented stop timer")
	var mock=MockAudio.new();frame_ui.audio=mock
	await action.play({"attacker":"a","defender":"b"})
	check(mock.requests==[0x53],"action cleanup remains compatible with existing audio mocks")
	frame_ui.audio=audio
	var maps=MapEffects.new(frame_ui);var unit={"id":"fixture","side":"player","position":[3,4],"hp":20}
	for program in range(1,12):
		audio.requests.clear();await maps.play_program(program,unit)
		var entry=MapEffects.source().programs[str(program)]
		check(audio.requests==[int(entry.sound_request),int(entry.end_sound_request)] and stopped(),"actual map effect starts and stops through native players "+str(program))
	check(playback_errors.is_empty(),"all verified fixture routing loads without unexpected failures")
	# Deliberate missing/corrupt mappings fail explicitly and never load old OGGs.
	var original:Dictionary=audio._manifest.sfx.rm_sfx_03.duplicate(true)
	audio._stream_cache.erase("sfx:rm_sfx_03");audio._manifest.sfx.rm_sfx_03=original.duplicate(true)
	audio._manifest.sfx.rm_sfx_03.path="res://assets/original/audio/hit.ogg";audio._stop_sfx();count=playback_errors.size()
	audio.play_sfx("hit")
	check(stopped() and playback_errors.size()==count+1,"source-recording path rejected even if old file exists")
	audio._manifest.sfx.rm_sfx_03.path="res://assets/sfx/20261024/does-not-exist.ogg";count=playback_errors.size();audio.play_sfx("hit")
	check(stopped() and playback_errors.size()==count+1,"missing new SFX does not fall back to source recording")
	audio._manifest.sfx.rm_sfx_03=original
	var real_assets=OS.get_environment("SFX_CHECK_ASSETS")=="1";var resources=[]
	if real_assets:
		audio.stop_all();audio._stream_cache.clear()
		for id in catalog.effects:
			var entry=catalog.effects[id];var raw=load(str(entry.path))
			check(bool(entry.asset_ready) and raw is AudioStreamOggVorbis,"generated OGG exists for verified request "+str(id))
			if not raw is AudioStreamOggVorbis:continue
			check(absf(raw.get_length()-float(entry.duration))<0.05,"imported duration matches manifest "+str(id))
			check(raw.get_length()<=float(entry.max_duration)+0.05,"finite duration respects source use "+str(id))
			var stream=audio._get_stream("sfx",str(id))
			check((stream!=null)==bool(entry.default_enabled),"actual resource follows disabled policy "+str(id))
			if stream!=null:check(not stream.loop and is_zero_approx(stream.loop_offset),"actual SFX remains finite without synthetic loop "+str(id))
			resources.append({"id":id,"path":entry.path,"duration":raw.get_length(),"default_enabled":entry.default_enabled,"manual_stop":entry.manual_stop})
		for alias in catalog.named_aliases:
			if alias in ["attack","death"]:check(audio._get_stream("sfx",str(alias))==null,"real generic alias remains disabled "+str(alias))
			else:check(audio._get_stream("sfx",str(alias))==audio._get_stream("sfx",str(catalog.named_aliases[alias])),"real named and canonical API share stream "+str(alias))
	var out=OS.get_environment("SFX_TEST_REPORT")
	if out.is_empty():out="res://reports/sfx-20261024/integration-tests.json"
	var f=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"real_assets_checked":real_assets,"resources":resources,"animation_traces":traces,"scope":"41request/42old-path/9alias coverage,15controls/5ignored, source disable/manual-stop semantics, two-voice lifecycle, exact combat-frame request order,11map-program starts/stops; headless only,no screenshots or saves."},"  "));f.close()
	print("SFX_TEST ",checks.size()," checks; errors: ",errors)
	audio.stop_all();frame_ui.audio=null;host.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
