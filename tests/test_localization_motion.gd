extends SceneTree
const SAVE := "res://reports/localization-save.json"
var checks := 0
var failures := 0
var ui

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, why: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(why)

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	root.add_child(ui)
	ui.game.save_path = SAVE
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	check(ui._text_width("阿尔姆") == 36, "Chinese names use the real 12px advance")
	check(ui._text_width("生命28/28") == 64, "Mixed Chinese/digits preserve their separate widths")
	for key in ui.game.opening.dialogues:
		ui._start_dialogue(str(key), "alm")
		for page in ui.dialogue_pages:
			check(not str(page.display_text).is_empty(), "Every source page has Chinese text")
			check(str(page.display_text).split("\n").size() <= 4, "Dialogue continuation preserves the four-line content area")
			check(ui._text_width(str(page.display_text)) <= 152, "Dialogue lines fit beside the portrait")
	for id in ui.graphics.village_units:
		check(int(ui.graphics.village_units[id].chr_bank) == 30, "All village actors use original CHR30")
	ui.game.new_game()
	ui.view = "village"
	ui._sync_village_position()
	ui._direction(Vector2i.RIGHT)
	check(ui.village_render_position == Vector2(80, 160) and ui.village_motion_time > 0,
		"A village step begins at the old image position instead of jumping a whole tile")
	ui._process(ui.VILLAGE_STEP_SECONDS / 2)
	check(ui.village_render_position.distance_to(Vector2(88, 160)) < 0.01, "Half a walking step draws halfway between tiles")
	ui._accept()
	check(ui.view == "village", "Conversation cannot start before the walking image arrives")
	ui._process(ui.VILLAGE_STEP_SECONDS / 2 + 0.001)
	check(ui.village_render_position == Vector2(96, 160), "Walking ends exactly on the destination pixel grid")
	ui.game.recruit("lukas")
	ui.game.start_battle()
	ui.game.find_unit("alm").name_zh = "阿鲁姆"
	check(ui.game.save_game(), "An older-name save can be created in the isolated test file")
	check(ui.game.load_game() and ui.game.find_unit("alm").name_zh == "阿尔姆", "Continue refreshes old names without replacing saved gameplay")
	ui.audio.stop_all()
	ui.queue_free()
	DirAccess.remove_absolute(SAVE)
	await create_timer(0.2).timeout
	print("FE2 localization/motion: ", checks, " checks, ", failures, " failures")
	quit(0 if failures == 0 else 1)
