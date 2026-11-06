extends SceneTree
const Cinema=preload("res://core/critical_cinema.gd")
var checks=0
var errors=[]
func check(ok:bool,label:String):
	checks+=1
	if not ok:errors.append(label);push_error(label)
func _initialize():call_deferred("run")
func run():
	var manifest=Cinema.data();check(manifest.cases.size()==14,"fourteen programs in isolated pack")
	for row in manifest.images:
		check(ResourceLoader.exists(row.path) and load(row.path) is Texture2D,"packed actor/effect/label "+row.path)
	for key in manifest.backgrounds:
		check(load(manifest.backgrounds[key]) is Texture2D,"packed pixel background "+str(key))
	for key in manifest.cases:
		var spec=manifest.cases[key];var packed=FileAccess.get_file_as_bytes(spec.program)
		var program=JSON.parse_string(packed.decompress_dynamic(32*1024*1024,FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
		check(not program.is_empty() and program.frames.size()==int(spec.frame_count),"packed draw program "+key)
		check(load(spec.sfx) is AudioStream,"packed unique effects "+key)
	for key in manifest.themes:check(load(manifest.themes[key]) is AudioStream,"packed hero theme "+str(key))
	var vp=SubViewport.new();vp.size=Vector2i(426,240);root.add_child(vp)
	var ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/critical-package-slots";ui.game.save_path="/private/tmp/critical-package-unused.json";vp.add_child(ui);await process_frame
	ui.set_process(false);ui.audio.stop_all();ui.game.new_game();ui.game.battle_data=ui.game.stages[101].duplicate(true)
	var actor=ui.game.characters.hunapu.duplicate(true);actor.side="player";actor.position=[4,4]
	var target=ui.game.stages[101].enemies[0].duplicate(true);ui.game.units=[actor,target]
	var event={"attacker":actor.id,"defender":target.id,"weapon_index":0,"critical":true,"hit":true,"hp_before":30,"hp_after":23}
	check(ui.battle_animation.cinema.prepare(event),"production scene prepares cinema entirely from exported pack")
	check(ui.battle_animation.cinema.target_texture!=null,"real enemy snapshot works without source PNG/editor files")
	check(not ui.battle_animation.cinema.has_method("draw_battle_background"),"package cannot replace ordinary combat background")
	ui.battle_animation.reset();ui.audio.stop_all();ui.queue_free();await process_frame;vp.queue_free();await process_frame
	var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"isolated_exported_pack":true,"source_assets_available":false,"device_installed":false}
	var f=FileAccess.open(OS.get_environment("CRITICAL_PACKAGE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("CRITICAL_PACKAGE ",checks," checks; ",errors);quit(0 if errors.is_empty() else 1)
