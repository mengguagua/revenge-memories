extends SceneTree
## Delivered-bytecode/resource smoke for the new recovery only.
var ui
var failures: Array[String] = []
var checks := 0

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label)

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = "/private/tmp/test-round7-pack-save.json"
	root.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	ui.game.route = "celica"
	ui.game.party = []
	ui.game.recruit("celica")
	ui.game.recruit("palla")
	ui.game.units = [ui.game.roster.celica.duplicate(true),ui.game.roster.palla.duplicate(true)]
	ui.combat = {"attacker":"celica","defender":"palla","support":true,"distance":1}
	var chosen: Dictionary = ui.battle_animation.selection({"attacker":"celica","defender":"palla","weapon_index":40})
	check(chosen.get("kind") == "source", "Delivered class11 recovery selects original source program")
	if chosen.get("kind") == "source":
		check(chosen.variant.source_program_id == 29 and chosen.variant.source_effect_id == 5, "Delivered program29/effect5 metadata")
		check(chosen.variant.contact_count == 1 and chosen.variant.contact_tick == 89, "Delivered recovery contact")
		var all_exist := true
		for frame in chosen.variant.frames:
			for effect in frame.effects:
				if not ResourceLoader.exists(str(ui.battle_animation._source().sprites[effect.sprite].path)): all_exist = false
		check(all_exist, "Delivered reused effect images resolve")
	ui.battle_animation.active_event = {"attacker":"celica","defender":"palla","weapon_index":40}
	var body: Dictionary = ui.battle_animation.sprite(ui.game.find_unit("celica"))
	check(body.get("recovery_body",false) and body.frames == 9 and body.source_oam_frame_count == 0 and ResourceLoader.exists(body.path), "Delivered complete recovery body atlas resolves")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	var file := FileAccess.open("/private/tmp/round7-package-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"scope":"External-directory pack smoke of new recovery data/bytecode; no previous battle checks.","user_save_accessed":false},"  ")+"\n")
	file.close()
	print("ROUND7 PACK:",checks," checks,",failures.size()," failures")
	quit(0 if failures.is_empty() else 1)
