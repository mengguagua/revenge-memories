extends SceneTree
## Copy this script outside the PCK to audit the standalone exported resources.
const Programs = preload("res://core/animation_programs.gd")
const Reviewed = preload("res://core/reviewed_animations.gd")
var checks: Array = []
var errors: Array = []
var images: Dictionary = {}
func _initialize():call_deferred("run")
func check(ok: bool,label: String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func gather(value):
	if value is String:
		if value.begins_with("res://assets/") and (value.ends_with(".png") or value.ends_with(".webp")):images[value]=true
	elif value is Dictionary:
		for child in value.values():gather(child)
	elif value is Array:
		for child in value:gather(child)
func run():
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Programs.MANIFEST))
	var counts: Dictionary = {};var total_variants=0
	var ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/revenge-performance-20261025/pack-slots";ui.game.save_path="/private/tmp/revenge-performance-20261025/pack-save.json";root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all();ui.audio.set_process(false)
	var source_memory=int(Performance.get_monitor(Performance.MEMORY_STATIC))
	var start=Time.get_ticks_usec();ui.battle_animation._source_metadata();var metadata_usec=Time.get_ticks_usec()-start
	var key=str(Reviewed.metadata().battle["21_ally"].reviewed_variants.values()[0]);start=Time.get_ticks_usec();var first=Reviewed.variant(key);var first_usec=Time.get_ticks_usec()-start
	check(not first.is_empty(),"first actual hero animation loads from packaged index")
	for group in manifest.groups:
		var entry: Dictionary = manifest.groups[group]
		check(not FileAccess.file_exists(entry.source),"full offline JSON excluded from PCK: "+group)
		check(FileAccess.file_exists(entry.programs),"indexed binary included in PCK: "+group)
		check(FileAccess.get_sha256(entry.programs)==str(entry.program_sha256),"packaged animation bytes exactly match source build: "+group)
		var metadata=Programs.metadata(group);gather(metadata)
		check(not Programs.groups[group].has("fallback"),"packaged gameplay never falls back to full JSON: "+group)
		var index: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(entry.index));var count=0;var frames=0
		for program in index.variants:
			var value=Programs.variant(group,program)
			if value.is_empty():errors.append("missing packaged animation: "+group+"/"+program)
			frames+=value.get("frames",[]).size();count+=1
		check(count==int(entry.variant_count),"all expected packaged actions readable: "+group)
		counts[group]={"variants":count,"frames":frames};total_variants+=count
	gather(ui.graphics);gather(ui.game.stages);gather(ui.world);gather(ui.battle_pack);gather(ui.nature_layouts)
	var missing: Array = []
	for path in images:
		if not ResourceLoader.exists(path):missing.append(path);continue
		var texture=load(path) as Texture2D
		if texture==null or texture.get_width()<=0 or texture.get_height()<=0:missing.append(path)
	check(missing.is_empty(),"all referenced portrait/body/effect/map textures load from standalone PCK")
	check(Reviewed.cache.is_empty() and ui.battle_animation._source_cache.is_empty(),"exported gameplay preserves lazy whole-library interfaces")
	check(Programs.recent.size()<=Programs.CACHE_ENTRIES and Programs.cached_bytes<=Programs.CACHE_BYTES,"all packaged program reads keep bounded cache")
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"groups":counts,"variants":total_variants,"textures":images.size(),"missing_textures":missing,"ui_static_memory_bytes":source_memory,"first_metadata_usec":metadata_usec,"first_hero_program_usec":first_usec,"standalone_pck":true,"device_installed":false}
	var file=FileAccess.open("/private/tmp/revenge-performance-20261025/package-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("PERFORMANCE_PACK ",JSON.stringify(result));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
