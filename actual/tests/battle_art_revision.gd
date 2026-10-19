extends SceneTree
## Validate the approved battle revision both in the source project and exported PCK.
const Reviewed = preload("res://core/reviewed_animations.gd")
var checks := 0
var errors: Array = []
var slots_checked := 0
var variants_checked := 0
var arrows_checked := 0
var ui

func _initialize(): call_deferred("run")

func check(ok: bool, label: String):
	checks += 1
	if not ok: errors.append(label); push_error(label)

func visible_hash(image: Image) -> String:
	image.convert(Image.FORMAT_RGBA8)
	var bytes = image.get_data()
	for i in range(0, bytes.size(), 4):
		if bytes[i + 3] == 0:
			bytes[i] = 0; bytes[i + 1] = 0; bytes[i + 2] = 0
	var digest = HashingContext.new()
	digest.start(HashingContext.HASH_SHA256); digest.update(bytes)
	return digest.finish().hex_encode()

func run():
	var expected_path = OS.get_environment("BATTLE_ART_EXPECTED")
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(expected_path))
	var before: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(expected_path.get_base_dir() + "/before/reviewed_animations.json"))
	var data = Reviewed.data()
	var expected_version: String = expected.get("version", "0.8.10")
	check(ProjectSettings.get_setting("application/config/version") == expected_version, "package version " + expected_version)
	check(data.maps == before.maps and data.map_revisions == before.map_revisions, "approved map identities, movement and shadows unchanged")
	ui = load("res://scenes/main.tscn").instantiate(); root.add_child(ui); await process_frame
	ui.set_process(false); ui.game.new_game(); ui.game.save_path = "/private/tmp/battle-art-revision-unused-save.json"
	var changed_variants = []
	for item in expected.inventory:
		var key: String = item.key
		var art: Dictionary = data.battle[key]
		check(art.art_revision == item.revision, "approved revision " + key)
		var texture: Texture2D = load(art.path)
		check(texture != null, "runtime texture loads " + key)
		if texture == null: continue
		var image = texture.get_image()
		check(image.get_size() == Vector2i(item.size[0], item.size[1]), "atlas dimensions " + key)
		for slot in item.frame_hashes:
			var n = int(slot)
			var region = Rect2i((n % int(art.columns)) * int(art.frame_size[0]), (n / int(art.columns)) * int(art.frame_size[1]), art.frame_size[0], art.frame_size[1])
			check(visible_hash(image.get_region(region)) == item.frame_hashes[slot], "review pixels " + key + "/" + slot)
			slots_checked += 1
		for effect in item.effects:
			var meta: Dictionary = data.sprites[effect.id]
			var old: Dictionary = data.sprites[effect.source_id]
			var arrow: Texture2D = load(meta.path)
			check(visible_hash(arrow.get_image()) == effect.visible_rgba_sha256, "faction arrow pixels " + key)
			check(meta.anchor == old.anchor and meta.flip_origin_offset == old.flip_origin_offset, "arrow anchor and flip offset " + key)
			check(int(meta.native_density) == 4, "4x arrow density " + key)
			for flip in [false, true]:
				for at in [Vector2(80, 45), Vector2(-12, 45), Vector2(240, 45)]:
					var old_region = ui.battle_animation.clipped_region(old, 0, at, flip)
					var new_region = ui.battle_animation.clipped_region(meta, 0, at, flip)
					check(old_region.destination == new_region.destination, "arrow display geometry " + key + str(flip) + str(at))
					check(old_region.source.size * 4 == new_region.source.size, "arrow source density " + key + str(flip) + str(at))
			arrows_checked += 1
		var actor = ui.game.characters.hunapu.duplicate(true)
		actor.id = "revision_actor"; actor.class_id = art.reviewed_class_id
		actor.side = "enemy" if art.reviewed_side == "enemy" else "player"
		actor.hp = 30; actor.max_hp = 30; actor.acted = false
		var target = actor.duplicate(true); target.id = "revision_target"
		target.side = "player" if actor.side == "enemy" else "enemy"
		ui.game.units = [actor, target]
		var sample_event = {}
		for source_key in art.reviewed_variants:
			var base: String = source_key.split("_far_")[0].trim_suffix("_vs_heavy")
			var weapon := 0
			var original: Dictionary = ui.graphics.battle["class_" + key]
			for table in [original.get("weapon_variants", {}), original.get("spell_variants", {})]:
				for candidate in table:
					if str(table[candidate]).trim_prefix("fe2_") == base: weapon = int(candidate)
			if weapon == 0 and "_bow" in base: weapon = 1
			if "_silver_bow" in base: weapon = 21
			target.class_id = 7 if source_key.ends_with("_vs_heavy") else 6
			ui.combat = {"attacker": actor.id, "defender": target.id, "distance": 2 if "_far_" in source_key else 1, "initiative_side": "enemy" if "_far_enemy" in source_key else "player"}
			var event = {"attacker": actor.id, "defender": target.id, "weapon_index": weapon, "hit": true, "critical": false, "hp_before": 30, "hp_after": 29}
			ui.battle_animation.active_event = event.duplicate(false)
			var chosen = ui.battle_animation.selection(event)
			var runtime_key: String = art.reviewed_variants[source_key]
			check(chosen.get("key", "") == runtime_key, "runtime variant " + source_key)
			var normalized: Dictionary = data.variants[runtime_key].duplicate(true)
			var unchanged = normalized == before.variants[runtime_key]
			var effects_load = true
			for frame in normalized.frames:
				for effect in frame.get("effects", []):
					effects_load = effects_load and ResourceLoader.exists(ui.battle_animation._source().sprites[str(effect.sprite)].path)
					for source_id in item.effect_aliases:
						if effect.sprite == item.effect_aliases[source_id]: effect.sprite = source_id
			check(effects_load, "all effects load " + source_key)
			check(unchanged or normalized == before.variants[runtime_key], "complete source timing and contacts unchanged " + source_key)
			changed_variants.append(runtime_key); variants_checked += 1
			if sample_event.is_empty(): sample_event = event
		ui.instant_mode = true; ui.battle_animation.reset()
		await ui.battle_animation.play(sample_event)
		check(ui.battle_animation.contact_calls == 1 and int(target.hp) == 29, "single real gameplay contact " + key)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[actor.id] == Vector2.ZERO, "animation cleanup " + key)
	var unaffected = true
	for key in before.variants:
		if key not in changed_variants: unaffected = unaffected and data.variants[key] == before.variants[key]
	check(unaffected, "all other attack variants unchanged")
	check(slots_checked == int(expected.source_frame_slots_checked) and variants_checked == int(expected.source_attack_variants) and arrows_checked == int(expected.scoped_arrow_textures), "complete requested revision loaded")
	var report = {"passed": errors.is_empty(), "checks": checks, "slots_checked": slots_checked, "variants_checked": variants_checked, "arrows_checked": arrows_checked, "errors": errors, "version": ProjectSettings.get_setting("application/config/version"), "scope": "Headless runtime and imported-texture validation; no device-play claim"}
	var file = FileAccess.open(OS.get_environment("BATTLE_ART_REPORT"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ")); file.close()
	print("BATTLE_ART_REVISION ", JSON.stringify(report))
	ui.queue_free(); await process_frame; quit(0 if errors.is_empty() else 1)
