extends SceneTree
## Round5 hub intent/input/result and real timed source progression checks.
const SAVE := "res://reports/test-round5-hub-save.json"
var ui
var checks := 0
var failures: Array[String] = []
var scenarios: Array[String] = []
var simulated_ticks := 0
var walk_inputs := 0
var paging_result: Dictionary = {}

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

func click(at: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.position = at
	event.pressed = true
	ui._input(event)

func advance(ticks: int = 20) -> void:
	for _i in range(ticks):
		ui.hub_controller.process(1.0 / 60.0988)
		simulated_ticks += 1

func reset(chapter: int = 1) -> void:
	ui.game.new_game()
	for transition in range(1, chapter):
		check(ui.game.next_chapter(transition), "Source chapter landmark %d exists" % transition)
	ui.busy = false
	ui.batch_running = false
	ui.held_direction = Vector2i.ZERO
	ui.instant_mode = false
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
	check(turns < 1800, "Non-instant source VM releases input")

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
		if destination_room >= 0 and ui.game.hub_id == destination_room: return true
		if ui.game.hub_position == goal and destination_room < 0: return true
		if ui.view != "hub" or hub.script_id >= 0:
			drain()
			if ui.view != "hub": return false
		var path := path_to(goal)
		if path.is_empty(): return false
		var dir: Vector2i = path[0]
		var code := KEY_UP if dir == Vector2i.UP else KEY_RIGHT if dir == Vector2i.RIGHT else KEY_DOWN if dir == Vector2i.DOWN else KEY_LEFT
		key(code)
		walk_inputs += 1
		advance()
	return false

func add_alm_party() -> void:
	for id in ["lukas", "gray", "tobin", "kliff", "silque", "clair", "clive", "forsyth", "python"]:
		ui.game.recruit(id)
	check(ui.game.party.size() == 10, "Ten actual Alm members supply the paged character fixture")

func test_paging() -> void:
	reset()
	add_alm_party()
	ui.hub_controller.enter(3, Vector2i(7, 3))
	key(KEY_TAB)
	var hub = ui.hub_controller
	check(ui.view == "hub_choice" and hub.choices.size() == 10, "Actual status shortcut opens two source character pages")
	click(Vector2(230, 214))
	paging_result = {"choices": hub.choices.size(), "right_arrow_index": hub.choice_index, "right_arrow_page": int(hub.choice_index / 5) + 1}
	check(int(hub.choice_index / 5) == 1, "Displayed next-page arrow advances to page2")
	check(hub.choice_index == 5, "Mouse next-page arrow selects the first entry on its new page")
	click(Vector2(230, 214))
	check(hub.choice_index == 5, "Hidden next-page arrow does not change the last page")
	key(KEY_DOWN)
	check(hub.choice_index == 6, "Actual DOWN selects the next person within page2")
	key(KEY_LEFT)
	check(hub.choice_index == 1, "Actual LEFT page key preserves the selection row on page1")
	click(Vector2(24, 214))
	check(hub.choice_index == 1, "Hidden previous-page arrow leaves the first page unchanged")
	key(KEY_RIGHT)
	check(hub.choice_index == 6, "Actual RIGHT key agrees with the visible page-arrow operation")
	var selected: String = str(hub.choices[6].value)
	click(Vector2(124, 102))
	check(ui.view == "hub_dialogue" and str(hub.pages[0].text).contains(hub._unit_name(selected)), "Mouse second row on page2 opens the corresponding selected person's status")
	drain()
	check(ui.view == "hub" and hub.script_id < 0, "Paged status result returns control to exploration")
	# The same visible arrows page the actual forty-slot convoy list.
	ui.game.convoy.alm = []
	for _i in range(40): ui.game.convoy.alm.append(1)
	key(KEY_S); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER)
	check(ui.view == "hub_choice" and hub.choice_title == "整理行囊", "Actual system menu opens convoy management")
	key(KEY_ENTER)
	check(ui.view == "hub_choice" and hub.choices.size() == 40, "Actual take-item choice displays forty source inventory entries")
	for page in range(1, 8):
		click(Vector2(230, 214))
		check(int(hub.choice_index / 5) == page, "Convoy next-page arrow reaches page%d" % (page+1))
	click(Vector2(230, 214))
	check(hub.choice_index == 35, "Forty-slot convoy arrow stops at its genuine last page")
	key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN)
	check(hub.choice_index == 39, "Actual DOWN selects convoy item40")
	key(KEY_ENTER)
	check(ui.view == "hub_choice" and hub.choice_title == "交给谁？", "Confirm item40 selects its recipient instead of another page")
	key(KEY_ESCAPE)
	check(ui.game.convoy.alm.size() == 40, "Cancelling the recipient leaves every convoy item intact")
	key(KEY_TAB)
	ui.game.party.pop_back()
	ui.game.parties.alm = ui.game.party.duplicate()
	key(KEY_ESCAPE); key(KEY_TAB)
	check(hub.choices.size() == 9, "Nine source characters give a shorter second page")
	key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_RIGHT)
	check(hub.choice_index == 8, "Page key clamps the fifth row to the fourth item on a shorter final page")
	key(KEY_LEFT)
	check(hub.choice_index == 3, "Returning from a short page retains its actual visible row")
	key(KEY_ESCAPE)
	key(KEY_S); key(KEY_RIGHT)
	check(not hub.choices.any(func(choice): return choice.value == "joint_prepare"), "Ordinary chapter1 hub menu does not expose final-only captured-party preparation")
	check(hub.choices[hub.choice_index].value == "close", "Actual page key reaches the continuing-exploration choice in the expanded system menu")
	key(KEY_ENTER)
	check(ui.view == "hub" and hub.choices.is_empty(), "Displayed continuing-exploration choice resumes walking")
	scenarios.append("Actual Main status mouse arrows and LEFT/RIGHT pages, UP/DOWN row selection, second-page target activation, first/last/short-page boundaries, forty-slot convoy paging and cancelled recipient transaction")

func final_fixture() -> void:
	reset(5)
	ui.game.world_node = 48
	ui.game.route_positions.alm = 48
	ui.game.flags.scenario_celica_story_phase = 3
	ui.game.flags.celica_captive = true
	ui.game.apply_hub_flag(81)
	ui.hub_controller.enter(37, Vector2i(11, 25))

func approach_final_gate() -> void:
	key(KEY_UP); advance()
	key(KEY_UP); advance()
	key(KEY_UP); advance()

func test_final_preparation() -> void:
	final_fixture()
	var hub = ui.hub_controller
	check(not ui.game.final_battle_readiness().ready, "Skipped source sword and healers genuinely have no deployed Duma finisher")
	approach_final_gate()
	check(ui.view == "hub_dialogue" and hub.script_id < 0 and ui.game.stage_id != 62, "Real UP door walk stops at the preparation explanation before final battle62")
	check(not ui.game.flags.get("source_flag_82", false) and not ui.game.flags.get("scenario_final_merge_ready", false), "Unprepared final entry preserves its source merge trigger and story flags")
	check(ui.game.hub_position == Vector2i(11,24), "Preparation interruption returns to the actual southern approach tile")
	var all_text := ""
	for page in hub.pages: all_text += str(page.text)
	all_text = all_text.replace("\n", "")
	check(all_text.contains("法尔西昂") and all_text.contains("吸血") and all_text.contains("无法撤退") and all_text.contains("回迷宫取剑"), "Visible explanation names the required finisher, irreversible battle and usable next action")
	drain()
	check(ui.game.save_game() and ui.game.load_game(), "Unprepared final-door checkpoint remains a valid production exploration save")
	hub.resume()
	check(ui.game.hub_position == Vector2i(11,24) and ui.view == "hub", "Reload retains the playable southern approach outside final battle")
	check(walk_to(Vector2i(6,27), 95), "Actual walk can return through the original final-room portal to prepare")
	final_fixture()
	ui.game.convoy.alm.append(17)
	approach_final_gate()
	check(ui.view == "hub_dialogue" and ui.game.stage_id != 62, "Falchion in the convoy cannot be mistaken for deployed equipment")
	all_text = ""
	for page in hub.pages: all_text += str(page.text).replace("\n", "")
	check(all_text.contains("行囊") and all_text.contains("取出") and all_text.contains("阿尔姆") and all_text.contains("双方整备"), "Stored Falchion message identifies the reachable item preparation menu and recipient")
	drain()
	key(KEY_S); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER); key(KEY_ENTER); key(KEY_ENTER); key(KEY_ENTER)
	check(int(ui.game.roster.alm.get("item_id",0)) == 17 and ui.game.convoy.alm.is_empty(), "Actual system/convoy/recipient inputs retrieve Falchion for Alm")
	check(ui.game.final_battle_readiness().ready, "The player's displayed preparation operation supplies the real finisher")
	key(KEY_UP); advance()
	check(ui.game.stage_id == 62 and ui.game.flags.get("scenario_final_merge_ready", false) and ui.view in ["battle", "battle_story"], "Returning to the same gate after preparation starts the source merged battle62")
	for _i in range(300):
		await process_frame
		if ui.view == "battle_story":
			ui.dialogue_reveal = 10000
			key(KEY_ENTER)
		elif ui.view == "battle" and not ui.busy: break
	check(ui.view == "battle" and not ui.busy and ui.game.flags.get("final_parties_merged",false), "Actual reunion dialogue confirm returns control to the prepared final battle")
	scenarios.append("Actual source55 final door: no-finisher explanation before irreversible merge; southern approach/save/reload/return portal; convoy Falchion explanation -> real item retrieval -> same final gate admits merged62")

func test_reserve_formation() -> void:
	final_fixture()
	for id in ["lukas", "gray", "tobin", "kliff", "clair", "clive", "forsyth", "python", "luthier", "tatiana"]: ui.game.recruit(id)
	var hub = ui.hub_controller
	check(not ui.game.final_battle_readiness().ready and ui.game.final_battle_readiness().reason == "reserve_nosferatu", "Real eleventh member Tatiana has usable Nosferatu but is outside the ten deployed Alm slots")
	approach_final_gate()
	check(ui.view == "hub_dialogue" and ui.game.stage_id != 62, "Undeployed healer receives the final preparation explanation")
	var text := ""
	for page in hub.pages: text += str(page.text).replace("\n", "")
	check(text.contains("出战顺序") and text.contains("双方整备"), "Alm's own reserve healer message names the now available formation operation")
	drain()
	var original_party: Array = ui.game.party.duplicate()
	var celica_party: Array = ui.game.parties.celica.duplicate()
	key(KEY_S)
	check(hub.choices.any(func(choice): return choice.value == "formation"), "Actual hub system menu exposes the displayed adjustment instruction")
	key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER)
	check(hub.choices.size() == 10 and hub.choices.any(func(choice): return choice.value == "tatiana"), "Formation chooser includes every living reserve member")
	check(not hub.choices.any(func(choice): return choice.value == "alm"), "Actual order choices keep the leader fixed at the first slot")
	key(KEY_ESCAPE)
	check(ui.game.party == original_party, "Cancel first formation choice preserves the party order")
	key(KEY_S); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER)
	key(KEY_RIGHT); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN)
	check(hub.choices[hub.choice_index].value == "tatiana", "Real page and row inputs select the eleventh actual member")
	key(KEY_ENTER)
	check(hub.choice_title == "选择交换顺序的队员" and not hub.choices.any(func(choice): return choice.value in ["alm", "tatiana"]), "Second choice excludes the leader and the first participant")
	key(KEY_ESCAPE)
	check(ui.game.party == original_party, "Cancel second formation choice preserves the party order")
	key(KEY_S); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER)
	key(KEY_RIGHT); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_DOWN); key(KEY_ENTER); key(KEY_ENTER)
	check(ui.game.party[0] == "alm" and ui.game.party[1] == "tatiana" and ui.game.party[10] == "lukas", "Confirmed real choices exchange only the actual selected member slots")
	check(ui.game.parties.alm == ui.game.party and ui.game.parties.celica == celica_party, "Formation persists the current army without changing the captured other army")
	check(ui.game.final_battle_readiness().ready and ui.game.final_battle_readiness().reason == "nosferatu", "The hinted local operation genuinely deploys the required final-form spell")
	drain()
	check(ui.game.load_game(), "Confirmed formation saved through the production game save path")
	hub.resume()
	check(ui.game.party[1] == "tatiana" and ui.game.final_battle_readiness().ready, "Reload preserves the actual prepared deployment order")
	key(KEY_UP); advance()
	check(ui.game.stage_id == 62 and ui.game.flags.get("final_parties_merged",false), "Returning to the same source door admits the prepared reserve healer")
	for _i in range(300):
		await process_frame
		if ui.view == "battle_story":
			ui.dialogue_reveal = 10000
			key(KEY_ENTER)
		elif ui.view == "battle" and not ui.busy: break
	check(ui.view == "battle" and not ui.busy and not ui.game.find_unit("tatiana").is_empty() and ui.game.find_unit("lukas").is_empty(), "Prepared final encounter deploys the chosen front ten and releases battle input")
	scenarios.append("Source final preparation explanation -> new hub order entry -> complete reserve chooser/paging -> both cancel boundaries -> actual Tatiana/Lukas swap with leader fixed and Celica intact -> save/reload -> same door -> actual final deployment and reunion input")

func select_choice(value) -> void:
	var hub = ui.hub_controller
	var index := -1
	for i in range(hub.choices.size()):
		if hub.choices[i].value == value:
			index = i
			break
	check(ui.view == "hub_choice" and index >= 0, "Actual selectable option exists: " + str(value))
	if index < 0: return
	var steps := 0
	while hub.choice_index != index and steps < hub.choices.size():
		key(KEY_DOWN)
		steps += 1
	key(KEY_ENTER)

func joint_sword_choice() -> void:
	key(KEY_S)
	select_choice("joint_prepare")
	select_choice("convoy")
	select_choice("celica")
	select_choice(39)
	select_choice("alm")

func test_joint_inventory_cancellation() -> void:
	final_fixture()
	ui.game.roster.alm.item_id = 1
	ui.game.convoy.alm = []
	ui.game.convoy.celica = []
	for _i in range(40):
		ui.game.convoy.alm.append(1)
		ui.game.convoy.celica.append(17 if _i == 39 else 1)
	ui.game.hub_used["40:0"] = true
	var convoy_before: Dictionary = ui.game.convoy.duplicate(true)
	joint_sword_choice()
	var hub = ui.hub_controller
	check(hub.choices.any(func(choice): return choice.value == "swap" and choice.label == "交换携带道具"), "Full hands require a visible explicit equipment exchange choice")
	key(KEY_ESCAPE)
	check(ui.game.convoy == convoy_before and int(ui.game.roster.alm.item_id) == 1, "Escape at the explicit exchange preserves the unique remote sword and both full stores")
	joint_sword_choice()
	select_choice("cancel")
	check(ui.game.convoy == convoy_before and int(ui.game.roster.alm.item_id) == 1, "Selecting the visible Cancel operation also preserves every item")
	joint_sword_choice()
	select_choice("swap")
	check(ui.game.convoy.alm == convoy_before.alm and ui.game.convoy.celica.size() == 40 and int(ui.game.convoy.celica[39]) == 1 and int(ui.game.roster.alm.item_id) == 17, "Explicit swap returns the previous carried item into the original remote sword slot at full capacity")
	var sword_count := int(int(ui.game.roster.alm.item_id) == 17)
	for army in ui.game.convoy:
		for item in ui.game.convoy[army]: sword_count += int(int(item) == 17)
	check(sword_count == 1 and ui.game.final_battle_readiness().ready, "The unique source sword is conserved and genuinely available after the displayed operation")
	check(ui.game.route == "alm" and ui.game.flags.celica_captive and not ui.game.flags.get("source_flag_82",false), "Local joint preparation retains the captured route and unopened final merge")
	drain()
	check(ui.game.load_game(), "Explicit full-capacity joint exchange persisted through production save validation")
	hub.resume()
	check(ui.game.convoy.celica.size() == 40 and ui.game.roster.alm.item_id == 17 and ui.game.final_battle_readiness().ready, "Saved remote-slot exchange reloads without a lost item or full-store dead end")
	scenarios.append("Final-only local joint inventory: both stores40 plus full hands, actual remote sword selection, Escape/Cancel preserve items, explicit source-slot exchange preserves unique17 and full capacity, captivity/route unchanged, production save/reload")

func test_source_40_unmask() -> void:
	reset(2)
	ui.game.apply_hub_flag(43)
	check(ui.game.next_chapter(2), "Source chapter3 milestone applies the same prior flag43")
	check(ui.hub_controller.enter(44, Vector2i(6, 6)), "Original source chapter3 room44 entry exists")
	drain()
	check(walk_to(Vector2i(3, 13), 4), "Real walking uses source room44 portal into Sofia room4")
	check(ui.hub_controller.script_id == 40 and ui.view == "hub", "Actual arrival cell starts source landslide VM40")
	drain()
	var hub = ui.hub_controller
	check(ui.view == "hub" and hub.script_id < 0, "Non-instant shake/walk/dialogue releases Sofia exploration")
	check(ui.game.flags.get("source_flag_53", false), "Source final flag53 unblocks the ordinary town NPCs")
	check(int(hub.actors[3].sprite_id) == 0 and bool(hub.actors[3].hidden), "Source messenger departure remains hidden after flag53")
	for actor in [4, 5, 6, 7, 8]:
		check(hub.actors.has(actor) and not bool(hub.actors[actor].get("hidden", false)), "Source NPC%d becomes visible when flag53 clears its mask" % actor)
	check(walk_to(Vector2i(10, 11)), "Newly visible source town NPC remains reachable by keys")
	key(KEY_UP); key(KEY_ENTER)
	check(ui.view == "hub_dialogue", "Correctly facing source NPC shows its genuine town dialogue")
	drain()
	check(ui.game.save_game() and ui.game.load_game(), "Completed source40 checkpoint is a valid production save")
	ui.hub_controller.resume()
	check(walk_to(Vector2i(11, 20)), "Reloaded town permits its original south departure walk")
	key(KEY_DOWN); advance(); key(KEY_DOWN); key(KEY_ENTER)
	check(ui.view == "world" and ui.game.world_node == 7, "Actual confirm returns to source southern road7")
	scenarios.append("Chapter3 room44 portal -> source40 timed shake/walk/dialogue -> flag53 NPCs -> actual talk -> save/load -> world exit; previous same-variant hidden candidate ruled out for normal progression")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.set_process(false)
	ui.set_physics_process(false)
	test_paging()
	test_source_40_unmask()
	await test_final_preparation()
	await test_reserve_formation()
	test_joint_inventory_cancellation()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("res://reports/round5-hub-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures, "scenarios": scenarios,
		"paging_result": paging_result, "walk_inputs": walk_inputs, "simulated_ticks": simulated_ticks,
		"user_save_accessed": false, "visible_or_focused_window": false}, "\t") + "\n")
	file.close()
	print("ROUND5 HUB: ", checks, " checks, ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
