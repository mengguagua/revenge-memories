extends SceneTree
const Items=preload("res://core/item_rules.gd")
func _initialize():
	var errors=[]
	if str(ProjectSettings.get_setting("application/config/version"))!="0.10.1":errors.append("version")
	var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://data/legacy/rules_full.json"))
	var ghost=Items.item(31);var unchanged=source.items[31].duplicate(true);unchanged.name_zh="鬼火"
	if ghost!=unchanged:errors.append("ghost fire name and original parameters")
	for path in ["res://tools/import_recent_review_art.py","res://reports/recent-art-20261021/import.json","res://source/characters/original-motion/full-original-motion.json"]:
		if FileAccess.file_exists(path):errors.append("development-only file exported: "+path)
	var f=FileAccess.open(OS.get_environment("PACKAGE_ART_PROBE"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"version":"0.10.1","ghost_fire_display_name":ghost.name_zh,"original_spell_parameters_retained":ghost==unchanged,"offline_sources_excluded":true},"  "));f.close()
	print("PACKAGE_ART_PROBE ",errors);quit(0 if errors.is_empty() else 1)
