extends "res://tests/play_round7_late.gd"
## Source-data terrain decoding and real cursor movement; no campaign battle replay.
var checks := 0
var results: Array = []
func check(ok: bool, label: String) -> void:
	checks += 1
	results.append({"passed":ok,"label":label})
	if not ok: failures.append(label)

func run() -> void:
	var game = State.new()
	for stage in range(1,81):
		game.battle_data = game.stages[stage]
		var mismatches := 0
		for y in range(int(game.battle_data.map.height)):
			for x in range(int(game.battle_data.map.width)):
				var cell := Vector2i(x,y)
				var tile: int = game.battle_data.map.tiles[y*int(game.battle_data.map.width)+x]
				var expected: int = game.battle_data.terrain.tile_categories.get(str(tile),0)
				if game.category(cell) != expected: mismatches += 1
		check(mismatches == 0,"source terrain categories map%d (mismatches%d)" % [stage,mismatches])
	game.battle_data = game.stages[10]
	check(game.category(Vector2i(28,19)) == 7,"sea tile96 is water category7")
	check(game.movement_cost(game.characters.celica,Vector2i(28,19)) == 255,"priestess cannot walk on open sea")
	check(game.movement_cost(game.characters.saber,Vector2i(28,19)) == 255,"mercenary cannot walk on open sea")
	check(game.movement_cost(game.characters.palla,Vector2i(28,19)) == 1,"pegasus keeps source flight over water")
	game.battle_data = game.stages[2]
	var forest := Vector2i(-1,-1)
	for i in range(game.battle_data.map.tiles.size()):
		var tile: int = game.battle_data.map.tiles[i]
		if int(game.battle_data.terrain.tile_categories.get(str(tile),0)) == 1:
			forest = Vector2i(i % int(game.battle_data.map.width),i / int(game.battle_data.map.width))
			break
	check(forest.x >= 0 and game.terrain_avoid(forest) == 40,"forest has original40 avoidance")
	check(game.movement_cost(game.characters.alm,forest) == 2,"forest has original foot movement cost2")
	if not OS.get_cmdline_user_args().has("--before"):
		ui = load("res://scenes/main.tscn").instantiate()
		ui.game.save_path = "res://reports/round9-terrain-test-save.json"
		root.add_child(ui)
		await process_frame
		ui.audio.set_music_enabled(false)
		ui.audio.set_sfx_enabled(false)
		ui.animation_speed = 100.0
		ui.game.new_game()
		ui.game.chapter = 2
		ui.game.route = "celica"
		ui.game.party = []
		ui.game.parties.celica = []
		for id in ["celica","genny","boey","mae","saber"]: ui.game.recruit(id)
		ui.game.roster.mae.dead = true
		ui.game.roster.mae.hp = 0
		ui.game.cleared_stages = [8,9]
		ui.game.world_node = 10
		ui.game.route_positions.celica = 10
		ui.game.start_battle(10)
		ui.view = "battle"
		var actor: Dictionary = ui.game.find_unit("celica")
		var origin := State.pos(actor)
		check(ui.view == "battle" and ui.game.stage_id == 10,"isolated source sea10 fixture starts without playing or clearing campaign battles")
		check(not ui.game.reachable(actor).costs.has(Vector2i(23,12)),"water outside ship is absent from displayed movement range")
		var enemy: Dictionary = ui.game.find_unit("g10_02")
		check(ui.game.reachable(enemy).costs.keys().all(func(cell):return ui.game.movement_cost(enemy,cell) < 255),"enemy pathfinding respects the same source terrain")
		cursor_to(origin); key(KEY_Z)
		cursor_to(Vector2i(23,12)); key(KEY_Z)
		await settle()
		check(ui.ui_mode == "move" and State.pos(actor) == origin and ui.menu_actions.is_empty(),"confirming off-ship water rejects movement and keeps cursor controllable")
		cursor_to(Vector2i(20,14)); key(KEY_Z)
		await settle()
		check(ui.menu_context == "unit_action" and State.pos(actor) == Vector2i(20,14),"actual cursor can continue onto valid ship deck after rejected move")
		check(ui.menu_actions.has("wait") and ui.menu_actions.has("magic"),"valid deck action menu remains available")
		check(not ui.game.needs_terrain_recovery(),"normal source deployment offers no terrain retry")
		key(KEY_X)
		ui.ui_mode = "inspect"
		# Reproduce a legal old-format suspend made while all terrain decoded as plain.
		actor.position = [28,19]
		actor.hp -= 2
		actor.exp = 7
		var clears: Array = ui.game.cleared_stages.duplicate()
		check(ui.game.save_game(),"old off-ship fixture saves through normal current suspend format")
		ui._show_title()
		key(KEY_DOWN); key(KEY_Z)
		await settle()
		check(ui.game.needs_terrain_recovery() and ui.notice.contains("S菜单可重试本关"),"actual title continue identifies off-ship position and explains recovery")
		key(KEY_S); choose("terrain_retry")
		check(ui.menu_context == "terrain_retry_confirm" and ui.notice.contains("重置本战进度"),"recovery confirmation explains loss of current battle progress")
		choose("terrain_retry_cancel")
		check(State.pos(ui.game.find_unit("celica")) == Vector2i(28,19) and int(ui.game.find_unit("celica").exp) == 7,"cancel preserves position and earned battle progress")
		choose("terrain_retry"); choose("retry")
		await settle()
		check(ui.view == "battle" and ui.game.turn == 1 and State.pos(ui.game.find_unit("celica")) == origin,"confirmed real menu retry restores the source deployment")
		check(int(ui.game.find_unit("celica").exp) == 0 and ui.game.cleared_stages == clears and clears == [8,9] and ui.game.stage_cleared(8) and ui.game.stage_cleared(9) and ui.game.roster.mae.dead and ui.game.find_unit("mae").is_empty(),"snapshot retry resets current growth while preserving prior clears and deaths")
		check(not ui.game.needs_terrain_recovery(),"terrain retry disappears after legal deployment is restored")
		ui.audio.stop_all(); ui.queue_free()
		await process_frame
		DirAccess.remove_absolute("res://reports/round9-terrain-test-save.json")
	var report := FileAccess.open("res://reports/round9-terrain-"+("before" if OS.get_cmdline_user_args().has("--before") else "after")+".json",FileAccess.WRITE)
	report.store_string(JSON.stringify({"checks":checks,"failures":failures,"results":results,"natural_battles_replayed":0,"screenshots":0},"  ")+"\n")
	print("ROUND9_TERRAIN checks=",checks," failures=",failures.size())
	quit(0 if failures.is_empty() else 1)
