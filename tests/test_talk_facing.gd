extends SceneTree
var ui
var checks := 0
var failures := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func reset(at: Vector2i, direction: Vector2i) -> void:
	ui.view = "village"
	ui._clear_menu()
	ui.game.village_position = at
	ui.game.village_facing = direction
	ui._sync_village_position()

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	root.add_child(ui)
	ui.audio.stop_all()
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	for facing in [Vector2i.UP, Vector2i.LEFT, Vector2i.RIGHT]:
		reset(Vector2i(5, 10), facing)
		ui._accept()
		check(ui.view == "village" and not ui.menu_items.is_empty(), "A nearby NPC cannot be addressed behind or beside the player")
	reset(Vector2i(5, 10), Vector2i.DOWN)
	ui._accept()
	check(ui.view == "dialogue" and ui.dialogue_actor == "mycen", "Adjacent Mycen can be addressed when facing him")
	reset(Vector2i(5, 9), Vector2i.DOWN)
	ui._accept()
	check(ui.view == "village", "Facing a character two tiles away cannot start a conversation")
	ui.game.complete_dialogue("alm_volunteers")
	reset(Vector2i(20, 8), Vector2i.RIGHT)
	ui._accept()
	check(ui.view == "village", "A recruited NPC removed from the village cannot be addressed")
	ui.queue_free()
	await create_timer(0.3).timeout
	print("FE2 facing interaction: ", checks, " checks, ", failures, " failures")
	quit(0 if failures == 0 else 1)
