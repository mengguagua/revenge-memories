extends RefCounted
## Runtime texture bindings are independent of preserved motion/contact programs.
static var cache:Dictionary={}
static var excluded_paths:Dictionary={}
static func data()->Dictionary:
	if cache.is_empty():
		cache=JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign_effects.json"))
		for path in cache.excluded_exact_copy_paths:excluded_paths[path]=true
	return cache
static func sprites()->Dictionary:return data().sprites
static func graphic(key:String,variant:String)->Dictionary:
	return data().variants.get(variant,{}).get(key,sprites().get(key,{}))
static func excluded(path:String)->bool:
	data();return excluded_paths.has(path)
