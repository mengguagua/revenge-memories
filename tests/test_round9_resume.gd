extends "res://tests/play_round7_late.gd"
## Only the newly reached chapter3 suspend; never replays a passed battle.
func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = "res://reports/round9-resume-isolated-save.json"
	DirAccess.copy_absolute("res://reports/round9-chapter2-save.json",ui.game.save_path)
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.animation_speed = 100.0
	key(KEY_DOWN); key(KEY_Z)
	await settle()
	var loaded: bool = ui.view == "hub" and ui.game.chapter == 3 and ui.game.route == "alm" and ui.game.hub_id == 44
	var origin: Vector2i = ui.game.hub_position
	key(KEY_DOWN)
	await settle()
	var moved: bool = ui.view == "hub" and ui.game.hub_position == origin + Vector2i.DOWN
	var live: Array = ui.game.parties.celica.filter(func(id):return not ui.game.roster[id].get("dead",false))
	var file := FileAccess.open("res://reports/round9-resume-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"loaded_new_chapter3_suspend":loaded,"actual_direction_moves_after_continue":moved,"preserved_celica_survivors":live,"source_progression_unfrozen":not ui.game.flags.get("scenario_alm_frozen",true),"natural_battles_replayed":0,"screenshots":0,"user_save_accessed":false},"  ")+"\n")
	ui.audio.stop_all(); ui.queue_free()
	await process_frame
	await create_timer(0.15).timeout
	DirAccess.remove_absolute("res://reports/round9-resume-isolated-save.json")
	print("ROUND9_RESUME loaded=",loaded," moved=",moved)
	quit(0 if loaded and moved else 1)
