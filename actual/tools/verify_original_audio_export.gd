extends SceneTree
## Headless export check: all replacement audio loads; legacy recordings are absent.
## Copy this probe to an empty temporary directory and run the PCK there with
## --path pointing to that directory, so res:// cannot fall back to source assets.
var checks: Array = []
var errors: Array = []
func check(ok: bool, label: String) -> void:
	checks.append(label)
	if not ok: errors.append(label); push_error(label)
func _initialize() -> void:
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/full_audio.json"))
	var aliases: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/audio.json"))
	var music: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/soundtrack.json"))
	var effects: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/sound_effects.json"))
	var old_paths: Dictionary = {}
	for entries in [source.music_by_request, source.sfx_by_request, aliases.music, aliases.sfx]:
		for entry in entries.values(): old_paths[str(entry.path)] = true
	check(old_paths.size() == 77, "35 old music and 42 old SFX paths inventoried")
	for path in old_paths:
		check(not ResourceLoader.exists(path) and not FileAccess.file_exists(path) and not FileAccess.file_exists(path+".remap"), "legacy recording excluded: "+path)
	check(music.tracks.size() == 28 and effects.effects.size() == 41, "28 new music plus 41 new SFX resources")
	var new_paths: Dictionary = {}
	for entries in [music.tracks, effects.effects]:
		for id in entries:
			var entry: Dictionary = entries[id]
			var path := str(entry.path)
			new_paths[path] = true
			check(bool(entry.get("asset_ready", false)), "finished generated asset: "+str(id))
			check(not old_paths.has(path), "new resource path: "+str(id))
			var stream := load(path) as AudioStream
			check(stream != null and stream.get_length() > 0.0, "exported generated OGG loads: "+str(id))
	check(new_paths.size() == 69, "69 unique replacement resources present")
	var request_keys: Dictionary = {}
	for entries in [source.music_by_request, source.sfx_by_request, source.control_requests, source.ignored_requests]:
		for key in entries: request_keys[str(key)] = true
	for bank in range(12):
		for bit in range(8): check(request_keys.has("%X%X" % [bank,bit]), "source request classified: %X%X" % [bank,bit])
	var result := {"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"legacy_recordings_excluded":old_paths.size(),"new_audio_resources":new_paths.size(),"source_requests_classified":request_keys.size(),"iphone_accessed":false,"auditory_review":false}
	var output := OS.get_environment("AUDIO_EXPORT_CHECK_REPORT")
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"  ")); file.close()
	print("AUDIO_EXPORT_CHECK ",JSON.stringify(result))
	quit(0 if errors.is_empty() else 1)
