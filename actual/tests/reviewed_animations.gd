extends SceneTree
## Targeted runtime integration checks, also runnable against the exported PCK.
const Reviewed = preload("res://core/reviewed_animations.gd")
const Party = preload("res://core/party_sprites.gd")
var ui
var checks := 0
var errors: Array = []
var variants_checked := 0
func _initialize(): call_deferred("run")
func check(ok: bool, label: String):
	checks += 1
	if not ok: errors.append(label);push_error(label)
func run():
	ui = load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.new_game();ui.game.save_path = "/private/tmp/reviewed-animation-unused-save.json"
	var saved_roster = ui.game.roster.duplicate(true)
	var data = Reviewed.data()
	check(data.battle.size() == 20, "20 completed class/faction bodies")
	for class_key in data.battle:
		var art: Dictionary = data.battle[class_key]
		check(ResourceLoader.exists(art.path), "battle texture " + class_key)
		var actor = ui.game.characters.hunapu.duplicate(true)
		actor.id = "review_actor";actor.class_id = art.reviewed_class_id
		actor.side = "enemy" if art.reviewed_side == "enemy" else "player"
		actor.hp = 30;actor.max_hp = 30;actor.acted = false
		var target = actor.duplicate(true);target.id = "review_target";target.side = "player" if actor.side == "enemy" else "enemy"
		ui.game.units = [actor, target]
		var sample_event = {}
		for source_key in art.reviewed_variants:
			actor.class_id = 23 if source_key.ends_with("_promoted") else art.reviewed_class_id
			var base: String = source_key.split("_far_")[0].trim_suffix("_vs_heavy")
			var weapon := 0
			var original: Dictionary = ui.graphics.battle["class_" + class_key]
			var found := false
			for table in [original.get("weapon_variants", {}), original.get("spell_variants", {})]:
				for item in table:
					if str(table[item]).trim_prefix("fe2_") == base: weapon = int(item);found = true
			if not found and "_bow" in base: weapon = 1
			if "_silver_bow" in base: weapon = 21
			var far = "_far_" in source_key
			target.class_id = 7 if source_key.ends_with("_vs_heavy") else 6
			ui.combat = {"attacker": actor.id, "defender": target.id, "distance": 2 if far else 1,
				"initiative_side": "enemy" if "_far_enemy" in source_key else "player"}
			var event = {"attacker": actor.id, "defender": target.id, "weapon_index": weapon,
				"critical": source_key.ends_with("_critical"), "hit": true, "hp_before": 30, "hp_after": 29}
			ui.battle_animation.active_event = event.duplicate(false)
			var chosen = ui.battle_animation.selection(event)
			var expected: String = art.reviewed_variants[source_key]
			check(chosen.get("key", "") == expected, "runtime variant " + source_key)
			if chosen.get("key", "") != expected: continue
			variants_checked += 1
			var variant: Dictionary = chosen.variant
			check(int(variant.contact_tick) >= 0 and int(variant.contact_tick) < variant.frames.size(), "contact boundary " + source_key)
			for frame in variant.frames:
				check(int(frame.frame) < int(art.frames), "body slot " + source_key)
				for effect in frame.get("effects", []):
					check(ResourceLoader.exists(data.sprites[str(effect.sprite)].path), "effect texture " + str(effect.sprite))
			if sample_event.is_empty(): sample_event = event
		# Run the real animation/contact controller once per completed body.
		ui.instant_mode = true;ui.battle_animation.reset()
		await ui.battle_animation.play(sample_event)
		check(ui.battle_animation.contact_calls == 1, "one gameplay contact " + class_key)
		check(int(target.hp) == 29, "real HP commit " + class_key)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[actor.id] == Vector2.ZERO, "animation cleanup " + class_key)
	for class_key in data.maps:
		for context in data.maps[class_key]:
			var art: Dictionary = data.maps[class_key][context]
			check(ResourceLoader.exists(art.path), "map texture " + class_key + "/" + context)
			if context == "tactical-walk":
				check(art.directions.has("left") and art.directions.has("right"), "independent native side directions " + class_key)
	check(variants_checked == 269, "all 269 completed attack variants selected")
	check(Reviewed.map_sprite("hub", ui.game.characters.daan).get("frames",0) == 1, "approved archer static story pose")
	check(Reviewed.map_sprite("hub", ui.game.characters.otto).get("frames",0) == 1, "approved spearman static story pose")
	check(Reviewed.map_sprite("map", {"id": "hunapu", "class_id": 21, "promoted": true}).is_empty(), "unfinished promoted map retained")
	check(Reviewed.battle({"class_id": 10, "side": "player"}, {"path": "original"}, {}).path == "original", "unfinished profession retained")
	var unsupported = {"attacker": "review_actor", "weapon_index": 4}
	var old: Dictionary = ui.graphics.battle.class_6_enemy
	check(Reviewed.battle({"id": "review_actor", "class_id": 6, "side": "enemy"}, old, unsupported) == old, "uncompleted soldier javelin retains complete existing body")
	check(ui.game.roster == saved_roster, "roster growth and equipment untouched")
	var result = {"passed": errors.is_empty(), "checks": checks, "variants_checked": variants_checked, "errors": errors}
	var output = OS.get_environment("REVIEWED_ANIMATION_REPORT")
	if output.is_empty(): output = "res://reports/animation-test-20261018/runtime.json"
	var file = FileAccess.open(output, FileAccess.WRITE);file.store_string(JSON.stringify(result, "  "));file.close()
	print("REVIEWED_ANIMATION ", JSON.stringify(result))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
