extends SceneTree
## Real keyboard + non-instant source VM walking from chapter/world landmarks.
## Armies, battle HP, rewards and character stats are never changed to advance.
const SAVE := "res://reports/test-round4-hub-save.json"
var ui
var checks := 0
var failures: Array[String] = []
var scenarios: Array[String] = []
var walk_inputs := 0
var simulated_ticks := 0
var old_world_recovery: Dictionary = {}

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	event.pressed = false
	ui._input(event)

func advance(ticks: int = 20) -> void:
	for _i in range(ticks):
		ui.hub_controller.process(1.0 / 60.0988)
		simulated_ticks += 1

func reset(chapter: int) -> void:
	ui.game.new_game()
	for transition in range(1, chapter):
		check(ui.game.next_chapter(transition), "Source chapter transition %d supplies landmark fixture" % transition)
	ui.busy = false
	ui.batch_running = false
	ui.held_direction = Vector2i.ZERO
	ui.instant_mode = false
	ui.view = "world"

func landmark(node: int, previous: int) -> void:
	ui.game.world_node = node
	ui.game.previous_world_node = previous
	ui.game.route_positions[ui.game.route] = node
	ui.game.flags.erase("world_route_previous_nodes")
	ui.view = "world"

func drain() -> void:
	var hub = ui.hub_controller
	var turns := 0
	while turns < 1800:
		if ui.view == "hub_dialogue":
			hub.reveal = 10000
			key(KEY_ENTER)
		elif ui.view == "hub_choice" and hub.choice_title.contains("记录进度"):
			key(KEY_ESCAPE)
		elif ui.view == "hub" and (hub.script_id >= 0 or hub.motion_left > 0 or hub.timer > 0):
			advance(1)
		else:
			break
		turns += 1
	check(turns < 1800, "Timed source dialogue/walk/wait releases its continuation")

func path_to(goal: Vector2i) -> Array:
	var hub = ui.hub_controller
	var origin: Vector2i = ui.game.hub_position
	var queue: Array[Vector2i] = [origin]
	var parents: Dictionary = {origin: origin}
	var head := 0
	while head < queue.size():
		var at: Vector2i = queue[head]
		head += 1
		if at == goal:
			var result: Array = []
			while at != origin:
				var before: Vector2i = parents[at]
				result.push_front(at - before)
				at = before
			return result
		for dir in [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]:
			var next: Vector2i = at + dir
			if next.x <= 0 or next.y <= 0 or next.x >= int(hub.room.width)-1 or next.y >= int(hub.room.height)-1:
				continue
			if parents.has(next) or hub._actor_at(next) > 0 or not (hub._ground(next) or hub._door(next)):
				continue
			parents[next] = at
			queue.append(next)
	return []

func walk_to(goal: Vector2i, destination_room: int = -1) -> bool:
	var hub = ui.hub_controller
	for _step in range(300):
		if destination_room >= 0 and ui.game.hub_id == destination_room:
			return true
		if ui.game.hub_position == goal and destination_room < 0:
			return true
		if ui.view != "hub" or hub.script_id >= 0:
			drain()
			if ui.view != "hub": return false
		var directions := path_to(goal)
		if directions.is_empty(): return false
		var dir: Vector2i = directions[0]
		var code := KEY_UP if dir == Vector2i.UP else KEY_RIGHT if dir == Vector2i.RIGHT else KEY_DOWN if dir == Vector2i.DOWN else KEY_LEFT
		key(code)
		walk_inputs += 1
		advance()
	return false

func test_source_approaches() -> void:
	reset(4)
	var variants := 0
	for node in [52, 54, 57, 63, 69]:
		var entry: Dictionary = ui.game.hubs.world_entries[str(node)]
		for previous in entry.approach_entries:
			var expected: Dictionary = entry.approach_entries[previous]
			landmark(node, int(previous))
			check(ui.hub_controller.enter_world(), "Source conditional entry %d from %s exists" % [node, previous])
			check(ui.game.hub_position == Vector2i(expected.spawn[0], expected.spawn[1]), "Source conditional entry %d from %s uses original triple position" % [node, previous])
			check(ui.hub_controller.facing == ui.hub_controller.DIRS[int(expected.facing)], "Source conditional entry %d from %s uses original packed facing" % [node, previous])
			variants += 1
	check(variants == 11, "All eleven source approach triples are decoded once")
	scenarios.append("Five conditional world entries / eleven original L0CB5B8 triples and facing values")

func test_harbor_south() -> void:
	reset(2)
	# This road landmark represents returning immediately to harbor from gate7.
	# The original gate army remains intact; travel_to uses the real return path.
	landmark(7, 57)
	check(ui.game.travel_to(57), "Chapter2 real travel gate7 -> harbor57 without changing its army")
	check(ui.hub_controller.enter_world(), "Real harbor command enters source hub9")
	check(ui.game.hub_position == Vector2i(3, 12), "Chapter2 south approach lands inside the harbor")
	check(ui.hub_controller._tile(Vector2i(3, 1)) == 207, "Source northern gate remains closed in chapter2")
	key(KEY_UP); advance()
	check(ui.game.hub_position == Vector2i(3, 11), "Actual UP input now leaves the old stuck exterior spawn")
	check(walk_to(Vector2i(11, 8)), "Actual source steps reach harbor NPC across room9")
	key(KEY_UP); key(KEY_ENTER)
	check(ui.view == "hub_dialogue", "Accessible harbor NPC responds through real dialogue dispatch")
	drain()
	check(ui.view == "hub" and ui.hub_controller.script_id < 0, "Harbor conversation returns to walking")
	var saved_position: Vector2i = ui.game.hub_position
	check(ui.game.save_game() and ui.game.load_game(), "Isolated harbor save reloads through production validation")
	ui.hub_controller.resume()
	check(ui.view == "hub" and ui.game.hub_position == saved_position, "Reload retains the reachable harbor position")
	check(walk_to(Vector2i(3, 12)), "Reloaded harbor permits the actual return walk")
	key(KEY_DOWN); advance(); key(KEY_DOWN)
	check(ui.view == "hub_choice" and int(ui.hub_controller.choices[0].value) == 7, "Real south gate proposes source world node7")
	key(KEY_ESCAPE)
	check(ui.view == "hub" and ui.hub_controller.script_id < 0, "Cancel south exit preserves exploration input")
	key(KEY_DOWN); key(KEY_ENTER)
	check(ui.view == "world" and ui.game.world_node == 7, "Confirm south exit returns to the original gate7")
	check(int(ui.game.flags.world_route_previous_nodes.celica) == 57, "Real hub exit remembers this route's source predecessor")
	scenarios.append("Chapter2 real gate7->harbor travel; UP/walk/NPC/save/reload/cancel/confirm south exit")

func test_harbor_north_and_fallback() -> void:
	reset(3)
	check(ui.game.switch_route(), "Chapter3 switches to Celica using real route API")
	landmark(19, 57)
	check(ui.game.travel_to(57), "Chapter3 real return travel western road19 -> harbor57")
	check(ui.hub_controller.enter_world() and ui.game.hub_position == Vector2i(3, 3), "Opposite harbor approach uses the north entrance")
	check(ui.hub_controller._tile(Vector2i(3, 13)) == 207, "Source south gate stays closed after chapter3")
	check(walk_to(Vector2i(11, 8)), "North harbor entrance also reaches real harbor content")
	check(walk_to(Vector2i(3, 2)), "North harbor path returns to its original gate")
	key(KEY_UP); advance(); key(KEY_UP); key(KEY_ENTER)
	check(ui.view == "world" and ui.game.world_node == 19, "Actual north exit returns to original road19")
	check(ui.game.travel_to(57), "Actual return from north exit restores harbor world command")
	check(ui.game.switch_route() and ui.game.switch_route(), "Real round-trip route switches preserve each army's approach")
	check(ui.game.previous_world_node == 19, "Celica's northern approach survives visiting Alm's route")
	check(ui.game.save_game() and ui.game.load_game(), "Isolated world save reloads the per-route approach")
	check(ui.hub_controller.enter_world() and ui.game.hub_position == Vector2i(3, 3), "Route switch and world reload still land inside the open north gate")
	for chapter in [2, 3]:
		reset(chapter)
		landmark(57, 57)
		check(ui.hub_controller.enter_world(), "Old entry without an approach can still open harbor")
		var expected := Vector2i(3, 12) if chapter == 2 else Vector2i(3, 3)
		check(ui.game.hub_position == expected and not path_to(Vector2i(11, 8)).is_empty(), "Missing predecessor fallback stays behind the open chapter%d gate" % chapter)
	scenarios.append("Chapter3 opposite harbor approach / closed south gate / actual north exit / route-switch and world-reload approach persistence / old missing-approach fallback")

func test_mila_gate_and_timed_vm() -> void:
	reset(3)
	check(ui.game.switch_route(), "Mila fixture uses real Celica route switch")
	landmark(61, 24)
	check(ui.hub_controller.enter_world(), "Source promotion village entry opens room13")
	check(walk_to(Vector2i(11, 8)), "Original village walk and door trigger promotion event37")
	drain()
	check(ui.game.flags.get("celica_promoted", false) and ui.game.flags.get("source_flag_46", false), "Actual timed source promotion unlocks Mila sluice conversation")
	landmark(26, 63)
	check(ui.game.travel_to(63), "Real return travel temple battlefield26 -> temple hub63")
	check(ui.hub_controller.enter_world() and ui.game.hub_position == Vector2i(11, 19), "Chapter3 Mila entry lands below the closed north gate")
	check(not ui.hub_controller._ground(Vector2i(11, 1)), "Mila's source northern gate stays closed before chapter4")
	check(walk_to(Vector2i(2, 11), 45), "Actual walk opens source door and reaches Mila sluice portal")
	check(walk_to(Vector2i(8, 8)), "Actual walking reaches sluice NPC2")
	key(KEY_UP); key(KEY_ENTER)
	check(ui.view == "hub_dialogue" and ui.hub_controller.script_id == 36, "Actual NPC accept dispatches source sluice script36")
	drain()
	check(ui.view == "hub" and ui.hub_controller.script_id < 0, "Non-instant NPC walk, wait and sluice animation return control")
	check(ui.game.flags.get("mila_visited", false) and ui.game.flags.get("source_flag_48", false), "Source Mila script unlocks the chapter-transition NPC")
	check(ui.game.hub_used.get("45:0", false), "Source sluice pattern remains persisted after timed animation")
	check(ui.game.save_game() and ui.game.load_game(), "Completed sluice state saves and reloads without a pending wait")
	ui.hub_controller.resume()
	check(ui.view == "hub" and ui.hub_controller.script_id < 0 and ui.hub_controller.timer == 0, "Reloaded sluice retains idle walking input")
	check(walk_to(Vector2i(10, 16), 15), "Reloaded sluice has a working real return portal")
	check(walk_to(Vector2i(11, 20)), "Actual Mila return walk reaches the southern exit")
	key(KEY_DOWN); key(KEY_ENTER)
	check(ui.view == "world" and ui.game.world_node == 26, "Actual Mila exit returns to temple battlefield26")
	check(ui.game.switch_route(), "Sluice completion permits actual return to Alm route")
	landmark(67, 32)
	check(ui.hub_controller.enter_world(), "Alm transition NPC room is entered from its real world command")
	check(walk_to(Vector2i(8, 8)), "Actual walking reaches newly unlocked transition NPC")
	key(KEY_UP); key(KEY_ENTER)
	check(ui.hub_controller.script_id == 38, "Actual sluice NPC dispatches source chapter-transition38")
	drain()
	check(ui.view == "chapter" and ui.game.chapter == 4 and ui.hub_controller.script_id < 0, "Timed source NPC path/wait/gate animation reaches chapter4")
	scenarios.append("Real source37 promotion walk -> correct Mila entrance -> source36 sluice/NPC walk/wait -> save/reload/return portal -> source38 chapter4")

func test_old_world_harbor_save() -> void:
	reset(3)
	check(ui.game.switch_route(), "Old world save fixture retains real chapter3 Celica party")
	landmark(57, 57)
	ui.game.mode = "world"
	check(ui.game.save_game(), "Write only the isolated version3 world save fixture")
	var saved: Dictionary = ui.game.read_json(SAVE)
	saved.flags.erase("world_route_previous_nodes")
	saved.flags.erase("world_route_encounters")
	saved.previous_world_node = 57
	var file := FileAccess.open(SAVE, FileAccess.WRITE)
	file.store_string(JSON.stringify(saved))
	file.close()
	check(ui.game.load_game(), "Authentic old v3 world save without per-route approach loads")
	check(ui.hub_controller.enter_world(), "Old world save can use its real harbor command")
	old_world_recovery = {"previous_node": ui.game.previous_world_node, "position": [ui.game.hub_position.x, ui.game.hub_position.y]}
	check(ui.game.hub_position in [Vector2i(3,3), Vector2i(3,12), Vector2i(11,10)] and ui.game.world_neighbors().has(ui.game.previous_world_node), "Recovered old harbor uses a source interior entrance and legal clear return road")
	check(walk_to(Vector2i(11, 8)), "Recovered old world save can actually walk into harbor content")
	check(walk_to(Vector2i(3, 2)), "Recovered old world save walks to the original open north exit")
	key(KEY_UP); advance(); key(KEY_UP); key(KEY_ENTER)
	check(ui.view == "world" and ui.game.world_node == 19 and ui.game.can_enter_stage(19), "Recovered old save can continue to the original western road encounter")
	scenarios.append("Old version3 chapter3 world harbor save with self previous-node and missing per-route approach; production load, source interior entrance, legal return road and actual content walk")

func test_old_hub_entry_save() -> void:
	for case in [
		{"chapter": 2, "world": 57, "room": 9, "raw": Vector2i(2,0), "old": Vector2i(2,0), "fixed": Vector2i(3,12), "goal": Vector2i(11,8)},
		{"chapter": 3, "world": 63, "room": 15, "raw": Vector2i(4,0), "old": Vector2i(4,1), "fixed": Vector2i(11,19), "goal": Vector2i(10,7)}
	]:
		reset(int(case.chapter))
		if int(case.chapter) >= 3: check(ui.game.switch_route(), "Old Mila fixture uses actual Celica party")
		landmark(int(case.world), int(case.world))
		# Replay the previous implementation's literal selector -> _setup flow.
		ui.game.enter_hub(int(case.room), case.raw)
		ui.hub_controller._setup(true)
		check(ui.game.hub_position == case.old, "Original selector reproduces the old trapped hub%d coordinate" % int(case.room))
		check(path_to(case.goal).is_empty(), "Legacy hub%d exterior cannot reach source content" % int(case.room))
		if int(case.room) == 15:
			key(KEY_RIGHT); advance()
			check(ui.game.hub_position == Vector2i(5,1), "Legacy Mila character can move while progression remains blocked")
			check(path_to(case.goal).is_empty(), "Mila remains outside its closed source gate after legal movement")
		var progress: Dictionary = JSON.parse_string(JSON.stringify({"flags": ui.game.hub_flags, "used": ui.game.hub_used, "changes": ui.game.hub_changes}))
		check(ui.game.save_game() and ui.game.load_game(), "Production validation accepts the genuine legacy hub coordinate")
		ui.hub_controller.resume()
		check(ui.game.hub_position == case.fixed, "Resume recovers only the impossible closed hub%d gate exterior" % int(case.room))
		check(JSON.parse_string(JSON.stringify({"flags": ui.game.hub_flags, "used": ui.game.hub_used, "changes": ui.game.hub_changes})) == progress, "Recovery preserves source NPC, feature and tile progress")
		check(walk_to(case.goal), "Recovered old hub%d save reaches its actual source content by keys" % int(case.room))
	# The same Mila coordinates are reachable normally once the source gate opens.
	reset(4)
	landmark(63, 43)
	ui.game.enter_hub(15, Vector2i(4,0))
	ui.hub_controller._setup(true)
	check(ui.game.save_game() and ui.game.load_game(), "Open Mila gate position has a valid normal save")
	ui.hub_controller.resume()
	check(ui.game.hub_position == Vector2i(4,1), "Recovery leaves the legitimately open source gate exterior unchanged")
	check(walk_to(Vector2i(10,7)), "Open Mila source gate remains traversable without relocation")
	scenarios.append("Old literal selector -> harbor/Mila closed exterior -> production save/load -> limited recovery and real content walking; open gate stays at its saved position")

func test_training_cancel_timed() -> void:
	reset(1)
	check(ui.hub_controller.enter(1, Vector2i(5, 10)), "Original new-game training tile enters source VM")
	check(ui.view == "hub_choice" and ui.hub_controller.script_id == 0, "Training's original progress choice owns input")
	key(KEY_ESCAPE)
	check(ui.view == "hub" and ui.hub_controller.motion_left > 0, "Cancelling progress choice starts the original timed walk")
	drain()
	check(ui.view == "hub" and ui.hub_controller.script_id < 0 and ui.game.hub_position == Vector2i(5, 10), "Six real timed training steps finish at their original location")
	check(ui.game.flags.get("source_flag_17", false), "Timed training finishes the original progression flag")
	scenarios.append("Original training choice cancel -> six non-instant steps -> source final dialogue/flag -> input release")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.set_process(false)
	ui.set_physics_process(false)
	test_source_approaches()
	test_harbor_south()
	test_harbor_north_and_fallback()
	test_mila_gate_and_timed_vm()
	test_old_world_harbor_save()
	test_old_hub_entry_save()
	test_training_cancel_timed()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("res://reports/round4-hub-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "scenarios": scenarios,
		"real_keyboard_walk_inputs": walk_inputs, "non_instant_simulated_ticks": simulated_ticks,
		"old_world_missing_approach_recovery": old_world_recovery,
		"user_save_accessed": false, "visible_or_focused_window": false,
		"scope": "Actual Main keyboard/controller, production travel/route/save APIs, original NPC/event programs, timed movement and source gates.",
		"limits": "Road/chapter landmarks skip preceding battles; no HP/enemy/reward changes and no claim of a natural full-campaign playthrough or graphical rendering."}, "\t") + "\n")
	file.close()
	print("ROUND4 HUB: ", checks, " checks, ", failures.size(), " failures; ", walk_inputs, " actual walking inputs")
	quit(0 if failures.is_empty() else 1)
