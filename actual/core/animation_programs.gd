extends RefCounted
## Metadata stays small. Individual immutable source programs are loaded on demand.
const MANIFEST = "res://data/animation_runtime/manifest.json"
const CACHE_BYTES = 8 * 1024 * 1024
const CACHE_ENTRIES = 24
static var groups: Dictionary = {}
static var programs: Dictionary = {}
static var recent: Array = []
static var cached_bytes := 0
static var disk_reads := 0

static func _group(name: String) -> Dictionary:
	if groups.has(name):return groups[name]
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	var entry: Dictionary = manifest.groups[name]
	# Local art tools may have just updated a source. Never silently display stale
	# generated motions; development falls back until the index is regenerated.
	if FileAccess.file_exists(entry.source) and FileAccess.get_sha256(entry.source) != str(entry.source_sha256):
		push_warning("Animation source changed; rebuild tools/build_runtime_animations.py: " + name)
		groups[name] = {"fallback":JSON.parse_string(FileAccess.get_file_as_string(entry.source))}
		return groups[name]
	var index: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(entry.index))
	index.programs = entry.programs
	groups[name] = index
	return index

static func metadata(name: String) -> Dictionary:
	var group = _group(name)
	return group.fallback if group.has("fallback") else group.metadata

static func variant(name: String, key: String) -> Dictionary:
	var group = _group(name)
	if group.has("fallback"):return group.fallback.get("variants",{}).get(key,{})
	if not group.variants.has(key):return {}
	var identity = name + ":" + key
	if programs.has(identity):
		recent.erase(identity);recent.append(identity)
		return programs[identity].value
	var location: Array = group.variants[key]
	var stream = FileAccess.open(group.programs,FileAccess.READ)
	if stream == null:push_error("Missing animation programs: " + str(group.programs));return {}
	stream.seek(int(location[0]))
	var packed = stream.get_buffer(int(location[1]))
	stream.close()
	var raw = packed.decompress(int(location[2]),FileAccess.COMPRESSION_DEFLATE) if location.size() > 2 else packed
	var value = JSON.parse_string(raw.get_string_from_utf8())
	if not value is Dictionary:push_error("Invalid animation program: " + identity);return {}
	disk_reads += 1
	programs[identity] = {"value":value,"bytes":raw.size()};recent.append(identity);cached_bytes += raw.size()
	# A caller retains its current Dictionary even when an older cache entry is
	# evicted. Never alter its frames or interrupt an in-flight animation.
	while recent.size() > 1 and (cached_bytes > CACHE_BYTES or recent.size() > CACHE_ENTRIES):
		var oldest = recent.pop_front();cached_bytes -= int(programs[oldest].bytes);programs.erase(oldest)
	return value

static func full_data(name: String) -> Dictionary:
	# Offline audits retain the historical whole-library interface; gameplay
	# never calls this, including in exported builds where sources are excluded.
	var group = _group(name)
	if group.has("fallback"):return group.fallback
	var result: Dictionary = group.metadata.duplicate(false)
	result.variants = {}
	for key in group.variants:result.variants[key] = variant(name,key)
	return result
