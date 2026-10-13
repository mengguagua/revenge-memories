extends SceneTree
## Run against the packaged app from an unrelated working directory.
var ui

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var errors: Array[String] = []
	ui = load("res://scenes/main.tscn").instantiate()
	root.add_child(ui)
	if not ui.get_window().title.ends_with("0.6"):
		errors.append("Packaged window does not identify version0.6")
	for side in ["ally", "enemy"]:
		for state in ["filled", "empty"]:
			if not ResourceLoader.exists(str(ui.health_ui.cells[side][state].path)):
				errors.append("Packaged original HP cell is missing")
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	if ui.view != "title" or ui.game.opening.dialogues.size() == 0:
		errors.append("Packaged title/opening failed")
	if ui.game.battle_data.enemies.size() != 5:
		errors.append("Packaged first battle data failed")
	var second = ui.game.read_json("res://data/second_battle.json")
	if second.get("enemies", []).size() != 7 or second.get("map", {}).get("width", 0) != 24:
		errors.append("Packaged second battle data failed")
	for side in ["ally", "enemy"]:
		if not ui.graphics.battle.has("archer_" + side) or not ui.graphics.map_units.has("archer_" + side):
			errors.append("Packaged archer sprite metadata is missing")
		elif not ResourceLoader.exists(ui.graphics.battle["archer_" + side].path) or not ResourceLoader.exists(ui.graphics.battle["archer_" + side].projectile.path):
			errors.append("Packaged archer body/projectile resource is missing")
	ui.game.new_game()
	ui.game.recruit("lukas")
	ui.game.start_battle()
	for enemy in ui.game.living("enemy"):
		enemy.hp = 0
	ui.game.check_outcome()
	ui.game.complete_battle()
	if not ui.game.start_battle(2) or ui.game.living("enemy").size() != 7:
		errors.append("Packaged campaign does not enter the second battle")
	elif ui.game.Rules.attack_range(ui.game.find_unit("archer_1")) != Vector2i(1, 3):
		errors.append("Packaged original bow range is incorrect")
	for stage in range(1, 81):
		if not ui.game.stages.has(stage) or ui.game.stages[stage].map.tiles.is_empty():
			errors.append("Missing campaign map " + str(stage))
	for cid in range(1, 23):
		for side in ["ally", "enemy"]:
			var key = "class_%d_%s" % [cid, side]
			for collection in ["battle", "map_units"]:
				if not ResourceLoader.exists(ui.graphics[collection][key].path): errors.append("Missing " + collection + " " + key)
	for path in ["res://data/hubs.json", "res://data/dialogue_zh.json", "res://data/battle_event_zh.json", "res://data/ending_zh.json", "res://data/full_animation_effects.json", "res://data/full_map_effects.json", "res://data/battle_inventory.json"]:
		if not FileAccess.file_exists(path): errors.append("Missing full campaign resource " + path)
	var effects = ui.battle_animation._source()
	if effects.get("variants", {}).size() < 768: errors.append("Missing original animation variants")
	for sprite in effects.get("sprites", {}).values():
		if not ResourceLoader.exists(sprite.path): errors.append("Missing original effect " + str(sprite.path))
	for info in ui.audio.full_manifest.get("music_by_request", {}).values():
		if not ResourceLoader.exists(info.path): errors.append("Missing full music " + str(info.path))
	if ui.source_dialogues.get("events", {}).is_empty() or ui.ending_data.get("characters", {}).is_empty(): errors.append("Missing Chinese campaign text")
	if ui.chinese_font.get("glyphs", {}).get("姆", {}).is_empty():
		errors.append("Packaged Chinese pixel font failed")
	if ui.game.opening.dialogues.gray_advice[0].get("text_zh", "").is_empty():
		errors.append("Packaged Chinese story translation failed")
	if ui.graphics.village_units.alm.chr_bank != 30:
		errors.append("Packaged village sprite bank is incorrect")
	for direction in ["left", "right", "down", "up"]:
		if not ResourceLoader.exists(str(ui.cursors.arrows[direction].path)):
			errors.append("Packaged directional arrow is missing: " + direction)
	for path in ["res://assets/original/graphics/title.png", "res://data/graphics.json", "res://data/audio.json"]:
		# Manifest itself resolves the exact title bitmap path below.
		if path.ends_with("title.png"):
			path = ui.graphics.title.path
		if not ResourceLoader.exists(path) and not FileAccess.file_exists(path):
			errors.append("Missing runtime resource " + path)
	for path in ["res://assets/fonts/OFL.txt", "res://assets/fonts/LICENSES/ark-pixel/OFL.txt", "res://assets/fonts/LICENSES/cubic-11/OFL.txt", "res://assets/fonts/LICENSES/galmuri/LICENSE.txt"]:
		if not FileAccess.file_exists(path):
			errors.append("Missing font license " + path)
	# Verify that the delivered pack includes the new independent-army logic,
	# using in-memory state only; packaging checks never write a user save.
	ui.game.new_game()
	ui.game.world_node = 4
	ui.game.world_armies = {"4": [4, 4]}
	ui.game.WorldArmies.ensure(ui.game)
	var army_ids: Array = ui.game.WorldArmies.instances_at(ui.game, 4)
	if army_ids.size() != 2 or army_ids[0] == army_ids[1]:
		errors.append("Packaged same-template armies do not have independent identities")
	elif not ui.game.start_battle(4, [4, 4]):
		errors.append("Packaged same-template encounter cannot start")
	else:
		for identity in army_ids:
			if not ui.game.living("enemy").any(func(unit): return str(unit.get("army_instance", "")) == str(identity)):
				errors.append("Packaged encounter lost army " + str(identity))
	if FileAccess.file_exists("res://.reference/fe2.nes") or ResourceLoader.exists("res://tests/test_flow.gd") or DirAccess.dir_exists_absolute("res://tools") or FileAccess.file_exists("res://reports/capture-save.json"):
		errors.append("Reference/test artifacts leaked into package")
	print("FE2_PACK_VERIFY ", "PASS" if errors.is_empty() else errors)
	ui.audio.stop_all()
	ui.queue_free()
	await create_timer(0.25).timeout
	quit(0 if errors.is_empty() else 1)
