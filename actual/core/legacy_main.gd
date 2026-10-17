extends Control
## Native five-chapter campaign flow. Art/sound are decoded originals; gameplay is GDScript.
const GameState = preload("res://core/game_state.gd")
const OriginalAudio = preload("res://core/original_audio.gd")
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Progression = preload("res://core/unit_progression.gd")
const TILE := 16
const NATIVE := Vector2(256, 240)

var game = GameState.new()
var audio
var hub_controller
var battle_animation
var map_effects
var source_dialogues: Dictionary = {}
var source_dialogue_meta: Dictionary = {}
var ending_data: Dictionary = {}
var story_return_view := "battle"
var campaign_chapter := false
var camp_first := ""
var camp_context := "world"
var loot_choice := ""
var chosen_spell := 0
var support_target := ""
var menu_scroll := 0
var ending_pages: Array = []
var ending_index := 0
var graphics: Dictionary
var chinese_font: Dictionary
var cursors: Dictionary
var health_ui: Dictionary
var world: Dictionary
var textures: Dictionary = {}
var view: String = "title"
var ui_mode: String = "inspect"
var elapsed := 0.0
var chapter_elapsed := 0.0
var lore_y := 244.0
var lore_scroll := 8.0
var title_selected := 0
var title_menu := false
var dialogue_key := ""
var dialogue_pages: Array = []
var dialogue_index := 0
var dialogue_reveal := 0.0
var dialogue_actor := ""
var dialogue_finish: Callable
var menu_items: Array = []
var menu_actions: Array = []
var menu_selected := 0
var menu_context := ""
var menu_position := Vector2(8, 72)
var target_ids: Array = []
var target_index := 0
var status_id := ""
var notice := ""
var notice_time := 0.0
var phase_banner := ""
var phase_time := 0.0
var busy := false
var batch_running := false
var result_sequence_running := false
var instant_mode := false
var animation_speed := 1.0
var wait_accumulated := 0.0
var map_actor_alpha: Dictionary = {}
var map_flash := false
var map_offset := Vector2.ZERO
var moving_id := ""
var moving_position := Vector2.ZERO
var combat: Dictionary = {}
var combat_poses: Dictionary = {}
var combat_offsets: Dictionary = {}
var combat_hp: Dictionary = {}
var combat_fades: Dictionary = {}
var combat_hit_id := ""
var combat_hit_time := 0.0
var combat_shake := 0.0
var combat_message := ""
var reward: Dictionary = {}
var reward_elapsed := 0.0
var reward_dismissed := false
var health_checks: Array = []
var safe_panels: Array[Rect2] = []
var text_checks: Array = []
var layout_errors: Array[String] = []
var repeat_timer := 0.0
var held_direction := Vector2i.ZERO
var camera_x := 0.0
var world_selected := 0
const WORLD_NODES := [49, 1, 2]
var battle_camera := Vector2.ZERO
var combat_projectile: Dictionary = {}
var village_render_position := Vector2(80, 160)
var village_step_origin := Vector2(80, 160)
var village_step_target := Vector2(80, 160)
var village_motion_time := 0.0
const VILLAGE_STEP_SECONDS := 16.0 / 60.0988
var moving_direction := Vector2i.DOWN
var moving_frame := 0
var enemy_range_key := ""
var enemy_range_cells: Array = []
var presentation_audit: Dictionary = {}

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_window().title = "火焰之纹章 外传 · 原生复刻 0.6"
	graphics = GameState.read_json("res://data/legacy/graphics.json")
	chinese_font = GameState.read_json("res://data/legacy/font_zh.json")
	cursors = GameState.read_json("res://data/legacy/cursors.json")
	health_ui = GameState.read_json("res://data/legacy/health_ui.json")
	world = GameState.read_json("res://data/legacy/world_map.json")
	if not game.catalog.is_empty():
		world.nodes = game.catalog.world_nodes
	source_dialogues = GameState.read_json("res://data/legacy/battle_event_zh.json")
	source_dialogue_meta = GameState.read_json("res://data/legacy/battle_event_dialogues.json")
	ending_data = GameState.read_json("res://data/legacy/ending_zh.json")
	audio = OriginalAudio.new()
	add_child(audio)
	hub_controller = load("res://core/story_hub.gd").new(self)
	battle_animation = load("res://core/battle_animation.gd").new(self)
	map_effects = load("res://core/map_effects.gd").new(self)
	audio.play_music("title")
	set_process_input(true)
	queue_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	chapter_elapsed += delta
	dialogue_reveal += delta * 28.0
	notice_time = maxf(0.0, notice_time - delta)
	phase_time = maxf(0.0, phase_time - delta)
	combat_hit_time = maxf(0.0, combat_hit_time - delta)
	if view.begins_with("hub"):
		hub_controller.process(delta)
	if view == "reward":
		var previous_points = mini(int(reward.get("gain", 0)), int(reward_elapsed * 60.0))
		reward_elapsed += delta
		var current_points = mini(int(reward.get("gain", 0)), int(reward_elapsed * 60.0))
		if current_points > previous_points and (previous_points == 0 or current_points / 4 > previous_points / 4):
			audio.play_sfx("hp_tick")
		if not instant_mode and not batch_running and not bool(reward.get("leveled", false)) and reward_elapsed >= 2.0:
			_accept()
	if village_motion_time > 0.0:
		village_motion_time = maxf(0.0, village_motion_time - delta)
		village_render_position = village_step_origin.lerp(village_step_target, 1.0 - village_motion_time / VILLAGE_STEP_SECONDS)
	if view == "lore":
		lore_y -= delta * lore_scroll
		if lore_y < -_lore_height():
			_show_title()
	if not busy and not batch_running and held_direction != Vector2i.ZERO and view in ["village", "battle"] and menu_items.is_empty() and ui_mode not in ["action", "target", "status"]:
		if view == "village":
			# Chain walking at tile boundaries; keyboard repeat never gates it.
			if village_motion_time <= 0.0:
				_direction(held_direction)
		else:
			repeat_timer -= delta
			if repeat_timer <= 0.0:
				repeat_timer = 0.14
				_direction(held_direction)
	queue_redraw()

func _physics_process(_delta: float) -> void:
	if view in ["village", "dialogue", "battle", "combat"] or view.begins_with("hub"):
		game.tick()

func _input(event: InputEvent) -> void:
	if event is InputEventKey:
		var key = event.physical_keycode
		var direction := Vector2i.ZERO
		match key:
			KEY_UP, KEY_W: direction = Vector2i.UP
			KEY_DOWN: direction = Vector2i.DOWN
			KEY_LEFT: direction = Vector2i.LEFT
			KEY_RIGHT, KEY_D: direction = Vector2i.RIGHT
		if direction != Vector2i.ZERO:
			# OS echo can arrive faster than the delay and otherwise starve motion.
			if event.echo:
				get_viewport().set_input_as_handled()
				return
			if event.pressed:
				held_direction = direction
				repeat_timer = 0.30
				_direction(direction)
			elif held_direction == direction:
				held_direction = Vector2i.ZERO
			get_viewport().set_input_as_handled()
			return
		if not event.pressed or event.echo:
			return
		if key in [KEY_Z, KEY_ENTER, KEY_SPACE]:
			_accept()
		elif key in [KEY_X, KEY_ESCAPE]:
			_cancel()
		elif key in [KEY_TAB, KEY_A]:
			_show_status()
		elif key in [KEY_Q, KEY_E]:
			_cycle_ready_unit(-1 if key == KEY_Q else 1)
		elif key == KEY_S:
			_open_system_menu()
		elif key == KEY_M:
			audio.set_music_enabled(not audio.music_enabled)
		elif key == KEY_F1:
			_show_help()
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			_cancel()
		elif event.button_index == MOUSE_BUTTON_LEFT:
			_mouse_accept(event.position)

func _direction(direction: Vector2i) -> void:
	if _status_open():
		if direction.x != 0: _cycle_status(direction.x)
		return
	if view in ["loot", "loot_confirm"]:
		menu_selected = posmod(menu_selected + (direction.x if direction.x != 0 else direction.y), menu_items.size())
		return
	if view.begins_with("hub"):
		hub_controller.direction(direction)
		return
	if busy or batch_running:
		return
	if not menu_items.is_empty():
		menu_selected = posmod(menu_selected + (direction.x if direction.x != 0 else direction.y), menu_items.size())
		menu_scroll = clampi(menu_scroll, maxi(0, menu_selected - 9), menu_selected)
		audio.play_sfx("menu_move")
		return
	if view == "title":
		title_menu = true
		title_selected = 1 - title_selected
		audio.play_sfx("menu_move")
	elif view == "lore":
		lore_scroll = 40.0 if direction.y > 0 else 8.0
	elif view == "village":
		if village_motion_time > 0.0:
			return
		game.village_facing = direction
		var next = game.village_position + direction
		if (next.y >= 14 or next.y <= 0 or next.x <= 0 or next.x >= 23) and _village_passable(next):
			_open_menu("depart", ["离开村庄", "留在村庄"], ["depart", "close"], Vector2(64, 88))
			return
		if _village_passable(next):
			game.village_position = next
			village_step_origin = village_render_position
			village_step_target = Vector2(next) * TILE
			village_motion_time = 0.0 if instant_mode else VILLAGE_STEP_SECONDS
			if instant_mode:
				village_render_position = village_step_target
	elif view == "world":
		var best = -1
		var score = -INF
		var current: Array = world.nodes[str(game.world_node)].position
		for node in game.world_neighbors():
			var position: Array = world.nodes[str(node)].position
			var delta = Vector2(position[0] - current[0], position[1] - current[1])
			var dot = delta.normalized().dot(Vector2(direction))
			if dot > 0.1 and dot * 100.0 - delta.length() > score:
				score = dot * 100.0 - delta.length()
				best = node
		if best > 0 and game.travel_to(best):
			world_selected = WORLD_NODES.find(game.world_node)
			audio.play_sfx("menu_move")
			game.save_game()
	elif view == "battle":
		if ui_mode == "status":
			return
		if ui_mode == "target":
			target_index = posmod(target_index + (direction.x if direction.x != 0 else direction.y), target_ids.size())
			game.cursor = GameState.pos(game.find_unit(target_ids[target_index]))
		elif ui_mode == "support_target":
			target_index = posmod(target_index + (direction.x if direction.x != 0 else direction.y), target_ids.size())
			game.cursor = GameState.pos(game.find_unit(target_ids[target_index]))
		else:
			game.cursor.x = clampi(game.cursor.x + direction.x, 0, int(game.battle_data.map.width) - 1)
			game.cursor.y = clampi(game.cursor.y + direction.y, 0, int(game.battle_data.map.height) - 1)
		_focus_battle(game.cursor)
		audio.play_sfx("menu_move")

func _accept() -> void:
	if view in ["loot", "loot_confirm"]:
		_loot_accept()
		return
	if view.begins_with("hub"):
		hub_controller.accept()
		return
	if view == "battle_story":
		_next_source_dialogue()
		return
	if view == "ending":
		ending_index += 1
		if ending_index >= ending_pages.size():
			_show_title()
		return
	if view == "reward" and batch_running:
		reward_dismissed = true
		return
	if busy or batch_running:
		return
	if not menu_items.is_empty():
		var action = str(menu_actions[menu_selected])
		var context = menu_context
		_clear_menu()
		audio.play_sfx("menu_confirm")
		_menu_action(action, context)
		return
	match view:
		"title":
			if not title_menu:
				title_menu = true
				audio.play_sfx("menu_confirm")
			elif title_selected == 0:
				_new_game()
			elif game.load_game():
				view = game.mode
				if view == "battle" and not game.battle_outcome.is_empty():
					view = game.battle_outcome
				game.mode = view
				_sync_village_position()
				ui_mode = "inspect"
				world_selected = WORLD_NODES.find(game.world_node)
				world_selected = maxi(0, world_selected)
				_focus_battle(game.cursor, true)
				if view == "hub":
					if bool(game.flags.get("chapter_intro_pending", false)):
						_show_campaign_chapter()
					else:
						hub_controller.resume()
				elif view == "world":
					audio.play_world(game.chapter)
				elif view in ["battle", "victory", "defeat"]:
					_play_phase_music()
					if game.needs_terrain_recovery():
						_notice("旧版地形位置异常\nS菜单可重试本关", 6.0)
				elif view == "ending":
					_start_ending()
				else:
					audio.play_music("village")
				if view in ["victory", "defeat"]:
					_show_result()
				elif view in ["battle", "world"]:
					await _resolve_pending_loot()
					await _play_story_events()
					if view == "battle" and game.can_return_to_final_preparation():
						_notice("无法终结多玛。按S选择返回准备，重置本战。", 8.0)
					if game.phase == "enemy" and view == "battle": _enemy_phase()
			else:
				_notice("存档无法读取" if FileAccess.file_exists(game.save_path) else "暂无存档")
		"lore": _show_title()
		"chapter":
			if campaign_chapter:
				game.flags.erase("chapter_intro_pending")
				hub_controller.enter(game.hub_id, game.hub_position)
			else:
				_enter_village()
		"village":
			if village_motion_time <= 0.0:
				_talk()
		"village_status": view = "village"
		"dialogue": _next_dialogue()
		"world":
			if game.world_has_battle(game.world_node):
				_enter_battle(game.world_node)
			elif game.world_node >= 49:
				hub_controller.enter_world()
			else:
				_open_camp_menu()
		"camp_status": view = camp_context
		"battle": _battle_accept()
		"reward":
			view = "battle"
			_finish_turn_action()
		"victory", "defeat":
			var items: Array = ["重试本关", "返回标题"]
			var actions: Array = ["retry", "title"]
			if game.can_return_to_final_preparation():
				items.push_front("返回准备（重置本战）")
				actions.push_front("final_prepare")
			if view == "victory":
				items.push_front("继续前进")
				actions.push_front("continue_world")
			_open_menu("result", items, actions, Vector2(64, 152))

func _cancel() -> void:
	if view == "loot_confirm":
		_show_loot_menu()
		return
	if view == "loot": return
	if view.begins_with("hub"):
		hub_controller.cancel()
		return
	if busy or batch_running:
		return
	if not menu_items.is_empty():
		var context = menu_context
		_clear_menu()
		if context in ["magic", "exchange"]:
			_unit_action_menu()
		elif context == "unit_action":
			game.cancel_move()
			_focus_battle(game.cursor)
			ui_mode = "inspect"
		audio.play_sfx("menu_cancel")
		return
	if view == "title":
		title_menu = false
	elif view == "lore":
		_show_title()
	elif view == "battle":
		match ui_mode:
			"move":
				game.selected_id = ""
				ui_mode = "inspect"
			"target": _unit_action_menu()
			"support_target", "warp": _unit_action_menu()
			"status": ui_mode = "inspect"
			_: _open_system_menu()
	elif view == "village":
		_open_system_menu()
	elif view == "village_status":
		view = "village"
	elif view == "world":
		_open_camp_menu()
	elif view == "camp_status":
		view = camp_context
	audio.play_sfx("menu_cancel")

func _mouse_accept(point: Vector2) -> void:
	if view.begins_with("hub"):
		hub_controller.mouse_accept(point)
		return
	if view in ["loot", "loot_confirm"]:
		var index = _menu_pointer_index(point)
		if index >= 0:
			menu_selected = index
			_loot_accept()
		return
	if view in ["battle_story", "hub_dialogue", "ending", "reward"]:
		_accept()
		return
	if busy or batch_running:
		return
	if view == "title" and title_menu:
		if Rect2(56, 180, 144, 56).has_point(point):
			title_selected = 0 if point.y < 208 else 1
			_accept()
		return
	if not menu_items.is_empty():
		var index = _menu_pointer_index(point)
		if index >= 0:
			menu_selected = index
			_accept()
		return
	if view == "battle" and ui_mode not in ["status", "action"]:
		if not Rect2(Vector2.ZERO, NATIVE).has_point(point):
			return
		var cell = _battle_screen_cell(point)
		if game.in_bounds(cell):
			if ui_mode in ["target", "support_target"]:
				var candidate = game.unit_at(cell)
				if not candidate.is_empty() and target_ids.has(candidate.id):
					target_index = target_ids.find(candidate.id)
					game.cursor = cell
					_focus_battle(cell)
					_accept()
			else:
				game.cursor = cell
				_focus_battle(cell)
				_accept()
	else:
		_accept()

func _new_game() -> void:
	game.new_game()
	view = "chapter"
	chapter_elapsed = 0.0
	campaign_chapter = false
	title_menu = false
	held_direction = Vector2i.ZERO
	audio.stop_all()
	audio.play_music("opening")

func _show_title() -> void:
	view = "title"
	game.mode = "title"
	title_menu = false
	elapsed = 0.0
	_clear_menu()
	audio.play_music("title")

func _show_lore() -> void:
	view = "lore"
	lore_y = 244.0
	lore_scroll = 8.0
	audio.play_music("opening")

func _enter_village() -> void:
	view = "village"
	game.mode = "village"
	_sync_village_position()
	audio.play_music("village")
	_start_dialogue("training", "mycen")

func _start_dialogue(key: String, actor: String = "", completion: Callable = Callable()) -> void:
	dialogue_key = key
	dialogue_actor = actor
	dialogue_pages = []
	for source_page in game.opening.dialogues.get(key, []):
		var lines = _wrapped_lines(str(source_page.get("text_zh", "")), 152.0)
		for start in range(0, lines.size(), 4):
			var page = source_page.duplicate(true)
			page.display_text = "\n".join(lines.slice(start, mini(start + 4, lines.size())))
			dialogue_pages.append(page)
	dialogue_index = 0
	dialogue_reveal = 0.0
	dialogue_finish = completion
	view = "dialogue"
	held_direction = Vector2i.ZERO

func _next_dialogue() -> void:
	if dialogue_pages.is_empty():
		_end_dialogue()
		return
	var text = str(dialogue_pages[dialogue_index].display_text)
	if int(dialogue_reveal) < text.length():
		dialogue_reveal = float(text.length())
		return
	dialogue_index += 1
	dialogue_reveal = 0.0
	audio.play_sfx("dialogue")
	if dialogue_index >= dialogue_pages.size():
		_end_dialogue()

func _end_dialogue() -> void:
	game.complete_dialogue(dialogue_key)
	view = "village"
	game.mode = "village"
	game.save_game()
	if dialogue_finish.is_valid():
		var callback = dialogue_finish
		dialogue_finish = Callable()
		callback.call()

func _talk() -> void:
	var facing = game.village_position + game.village_facing
	var nearest = ""
	for npc in game.opening.village.npcs:
		if not _npc_present(str(npc.id)):
			continue
		var at = Vector2i(npc.position[0], npc.position[1])
		if at == facing:
			nearest = str(npc.id)
			break
	if not nearest.is_empty():
		audio.play_sfx("menu_confirm")
		_start_dialogue(game.dialogue_for_npc(nearest), nearest)
	else:
		_open_system_menu()

func _village_passable(cell: Vector2i) -> bool:
	if cell.x < 0 or cell.y < 0 or cell.x >= 24 or cell.y >= 15:
		return false
	for npc in game.opening.village.npcs:
		if _npc_present(str(npc.id)) and Vector2i(npc.position[0], npc.position[1]) == cell:
			return false
	var tile = int(game.opening.village.tiles[cell.y * 24 + cell.x])
	for object in game.opening.village.objects:
		var local = cell - Vector2i(object.x, object.y)
		var object_map = object.map
		if local.x >= 0 and local.y >= 0 and local.x < int(object_map.width) and local.y < int(object_map.height):
			tile = int(object_map.tiles[local.y * int(object_map.width) + local.x])
	return tile < 102 or tile >= 232

func _npc_present(id: String) -> bool:
	# Original event opcode60 removes recruited actors from the village.
	return id == "mycen" or not game.party.has(id)

func _depart() -> void:
	view = "world"
	game.mode = "world"
	world_selected = 0
	game.world_node = 49
	game._bridge_opening_flags()
	audio.play_world(game.chapter)
	held_direction = Vector2i.ZERO
	game.save_game()

func _continue_world() -> void:
	if str(game.battle_return.get("mode", "world")) == "hub":
		var at: Array = game.battle_return.get("position", [5, 10])
		hub_controller.enter(int(game.battle_return.hub_id), Vector2i(at[0], at[1]))
		return
	view = "world"
	game.mode = "world"
	world_selected = WORLD_NODES.find(game.world_node)
	_clear_menu()
	held_direction = Vector2i.ZERO
	audio.play_world(game.chapter)
	game.save_game()

func _enter_battle(stage: int = 1, retry: bool = false) -> void:
	var entered: bool
	if retry:
		entered = game.retry_battle()
	else:
		entered = game.start_battle(stage)
	if not entered:
		_notice("暂时无法进入此关")
		return
	_begin_existing_battle()

func _begin_existing_battle() -> void:
	if game.mode == "world":
		view = "world"
		_clear_menu()
		audio.play_world(game.chapter)
		await _play_story_events()
		return
	if game.mode == "hub":
		hub_controller.resume()
		return
	view = "battle"
	ui_mode = "inspect"
	battle_camera = Vector2.ZERO
	_focus_battle(game.cursor, true)
	held_direction = Vector2i.ZERO
	_clear_menu()
	_play_phase_music()
	phase_banner = "我方回合"
	phase_time = 1.5
	game.save_game()
	_play_story_events()

func _show_campaign_chapter() -> void:
	campaign_chapter = true
	game.flags.chapter_intro_pending = true
	game.save_game()
	view = "chapter"
	chapter_elapsed = 0.0
	audio.play_world(game.chapter)

func _play_phase_music() -> void:
	var final_phase = game.units.any(func(unit): return int(unit.get("character_id", 0)) == 167 and int(unit.hp) < 52)
	audio.play_battle(game.route, game.phase, game.living("enemy").size(), game.stage_id == 62, final_phase)

func _battle_accept() -> void:
	if game.phase != "player":
		return
	match ui_mode:
		"status": ui_mode = "inspect"
		"inspect":
			var unit = game.unit_at(game.cursor)
			if not unit.is_empty() and unit.side == "player":
				if game.select_unit(str(unit.id)):
					ui_mode = "move"
					audio.play_sfx("menu_confirm")
				else:
					status_id = str(unit.id)
					ui_mode = "status"
			elif not unit.is_empty():
				status_id = str(unit.id)
				ui_mode = "status"
			else:
				_open_system_menu()
		"move":
			var unit = game.find_unit(game.selected_id)
			var path = game.path_to(unit, game.cursor)
			if not path.is_empty() and game.can_stop(unit, game.cursor):
				_animate_move(unit, path, true)
		"target":
			if not target_ids.is_empty():
				_play_combat(game.selected_id, str(target_ids[target_index]))
		"support_target":
			support_target = str(target_ids[target_index])
			if chosen_spell == 43:
				ui_mode = "warp"
				_notice("选择传送落点")
			else:
				_play_support(game.selected_id, chosen_spell, support_target)
		"warp": _play_support(game.selected_id, chosen_spell, support_target, game.cursor)

func _unit_action_menu() -> void:
	var unit = game.find_unit(game.selected_id)
	if unit.is_empty():
		ui_mode = "inspect"
		_clear_menu()
		return
	ui_mode = "action"
	game.cursor = GameState.pos(unit)
	_focus_battle(game.cursor)
	unit.erase("weapon_index")
	var items: Array = []
	var actions: Array = []
	if not game.targets(unit).is_empty():
		items.append("攻击")
		actions.append("attack")
	if not Items.spells(unit).is_empty():
		items.append("魔法")
		actions.append("magic")
	if game.living("player").any(func(other): return Inventory.can_exchange(unit, other)):
		items.append("交换装备")
		actions.append("exchange")
	items.append("待机")
	actions.append("wait")
	var x = 8 if _battle_cell_screen(game.cursor).x > 112 else 160
	_open_menu("unit_action", items, actions, Vector2(x, 112))

func _open_system_menu() -> void:
	if view.begins_with("hub"):
		hub_controller.open_system_menu()
		return
	if view == "world" and not busy:
		_open_camp_menu()
		return
	if busy or batch_running or view not in ["village", "battle"]:
		return
	if view == "battle":
		if ui_mode in ["move", "target", "action", "support_target", "warp"]:
			return
		_open_menu("system", ["结束回合", "自动进攻", "集合队伍", "人物状态", "保存进度"],
			["end_turn", "assault", "gather", "roster", "save"], Vector2(8, 72))
		if Inventory.can_retreat(game):
			menu_items.append("撤退")
			menu_actions.append("retreat")
		if game.can_return_to_final_preparation():
			menu_items.append("返回准备（重置本战）")
			menu_actions.append("final_prepare")
		if game.needs_terrain_recovery():
			menu_items.append("重试本关")
			menu_actions.append("terrain_retry")
	else:
		var items: Array = ["人物状态", "保存进度"]
		var actions: Array = ["roster", "save"]
		if bool(game.flags.get("joined_deliverance", false)):
			items.append("离开村庄")
			actions.append("depart")
		items.append("返回标题")
		actions.append("title")
		_open_menu("village", items, actions, Vector2(64, 72))

func _open_menu(context: String, items: Array, actions: Array, at: Vector2) -> void:
	menu_context = context
	menu_items = items
	menu_actions = actions
	menu_selected = 0
	menu_scroll = 0
	menu_position = at
	held_direction = Vector2i.ZERO

func _clear_menu() -> void:
	menu_items = []
	menu_actions = []
	menu_context = ""

func _menu_action(action: String, _context: String) -> void:
	if action.begins_with("exchange:"):
		if Inventory.exchange(game, game.selected_id, action.substr(9)):
			ui_mode = "inspect"
			_notice("道具已交换")
			_finish_turn_action()
		return
	if action.begins_with("spell:"):
		_choose_spell(int(action.get_slice(":", 1)))
		return
	if action.begins_with("camp:"):
		_camp_action(action.substr(5))
		return
	match action:
		"depart": _depart()
		"title": _show_title()
		"retry": _enter_battle(game.stage_id, true)
		"terrain_retry":
			if game.needs_terrain_recovery():
				_open_menu("terrain_retry_confirm", ["取消", "重试本关"], ["terrain_retry_cancel", "retry"], Vector2(64, 80))
				_notice("重试将重置本战进度", 6.0)
		"terrain_retry_cancel": _open_system_menu()
		"final_prepare":
			if game.return_to_final_preparation():
				ui_mode = "inspect"
				result_sequence_running = false
				hub_controller.resume()
				game.save_game()
		"continue_world": _continue_world()
		"save":
			game.mode = "battle" if view == "battle" else "village"
			_notice("进度已保存" if game.save_game() else "保存失败")
		"retreat":
			if Inventory.retreat(game):
				_continue_world()
		"exchange":
			var source = game.find_unit(game.selected_id)
			var members = game.living("player").filter(func(unit): return Inventory.can_exchange(source, unit))
			_open_menu("exchange", members.map(func(unit): return unit.name_zh), members.map(func(unit): return "exchange:" + str(unit.id)), Vector2(64, 64))
		"end_turn": _enemy_phase()
		"assault": _auto_player(false)
		"gather": _auto_player(true)
		"roster":
			if view == "village":
				status_id = game.party[0]
				_open_menu("roster", game.party.map(func(id): return game.opening.characters[id].name_zh),
					game.party.map(func(id): return "member:" + id), Vector2(64, 56))
			else:
				status_id = str(game.unit_at(game.cursor).get("id", game.leader_id()))
				ui_mode = "status"
		"attack":
			target_ids = game.targets(game.find_unit(game.selected_id)).map(func(unit): return str(unit.id))
			target_index = 0
			ui_mode = "target"
			game.cursor = GameState.pos(game.find_unit(target_ids[0]))
			_focus_battle(game.cursor)
		"magic":
			var caster = game.find_unit(game.selected_id)
			var spells = Items.spells(caster)
			_open_menu("magic", spells.map(func(id): return str(Items.spell(id).name_zh) + " " + str(Items.cost(id)) + "HP"), spells.map(func(id): return "spell:" + str(id)), Vector2(64, 40))
		"wait":
			game.mark_wait(game.selected_id)
			ui_mode = "inspect"
			_finish_turn_action()
		"close": pass
		_:
			if action.begins_with("member:"):
				var id = action.substr(7)
				status_id = id
				view = "village_status"

func _show_status() -> void:
	if view.begins_with("hub"):
		hub_controller.open_status()
		return
	if busy or batch_running or not menu_items.is_empty():
		return
	if view == "village" and village_motion_time <= 0.0:
		_menu_action("roster", "village")
	elif view == "world":
		_camp_members("status")
	elif view == "battle":
		if ui_mode not in ["inspect", "status"]:
			return
		var unit = game.unit_at(game.cursor)
		if not unit.is_empty():
			status_id = str(unit.id)
			ui_mode = "inspect" if ui_mode == "status" else "status"

func _status_open() -> bool:
	return view in ["camp_status", "village_status"] or (view == "battle" and ui_mode == "status")

func _status_members() -> Array:
	# An enemy/NPC inspection never exposes the other army or switches sides.
	if view == "battle" and not game.party.has(status_id): return []
	return game.party.filter(func(id): return game.roster.has(id) and (view != "battle" or not game.find_unit(str(id)).is_empty()))

func _status_unit(id: String) -> Dictionary:
	return game.find_unit(id) if view == "battle" else game.roster.get(id, {})

func _cycle_status(step: int) -> void:
	if busy or batch_running or not menu_items.is_empty(): return
	var members = _status_members()
	if members.size() < 2: return
	status_id = str(members[posmod(members.find(status_id) + step, members.size())])
	if view == "battle":
		game.cursor = GameState.pos(_status_unit(status_id))
		_focus_battle(game.cursor, true)
	audio.play_sfx("menu_move")

func _cycle_ready_unit(step: int = 1) -> void:
	if view != "battle" or busy or batch_running or game.phase != "player" or not menu_items.is_empty() or ui_mode not in ["inspect", "move"]: return
	var ready: Array = []
	for id in game.party:
		var unit = game.find_unit(str(id))
		if not unit.is_empty() and int(unit.hp) > 0 and not bool(unit.get("hidden", false)) and not bool(unit.acted) and bool(unit.get("controllable", true)):
			ready.append(str(id))
	if ready.is_empty():
		_notice("本回合没有未行动队员")
		return
	var current = game.unit_at(game.cursor)
	var index = ready.find(str(current.get("id", "")))
	# Move mode has only a proposed cursor destination; the unit has not moved.
	# Clear that selection without rewriting even the source position array.
	var next = str(ready[posmod(index + step, ready.size()) if index >= 0 else (0 if step > 0 else ready.size() - 1)])
	game.selected_id = ""
	game.cursor = GameState.pos(game.find_unit(next))
	ui_mode = "inspect"
	_focus_battle(game.cursor, true)
	audio.play_sfx("menu_move")

func _focus_player_leader() -> void:
	var available = game.living("player").filter(func(u): return bool(u.get("controllable", true)) and not bool(u.get("hidden", false)))
	if available.is_empty(): return
	var unit = game.find_unit(game.leader_id())
	if unit.is_empty() or not available.has(unit):
		unit = available[0]
		for id in game.party:
			var candidate = game.find_unit(str(id))
			if available.has(candidate):
				unit = candidate
				break
	game.selected_id = ""
	game.cursor = GameState.pos(unit)
	_focus_battle(game.cursor, true)

func _open_camp_menu() -> void:
	var items: Array = ["部队状态", "交换装备", "装备行囊", "调整顺序", "保存进度"]
	var actions: Array = ["camp:roster", "camp:trade", "camp:convoy", "camp:formation", "camp:save"]
	if game.can_switch_route():
		items.append("切换队伍")
		actions.append("camp:switch")
	items.append("返回标题")
	actions.append("title")
	_open_menu("camp", items, actions, Vector2(64, 48))

func _camp_members(action: String, except_id: String = "") -> void:
	var members = game.party.filter(func(id): return str(id) != except_id and (action=="status" or game.can_deploy(game.roster[id])))
	if members.is_empty():
		_open_camp_menu()
		_notice("没有其他队员")
		return
	_open_menu("camp_members", members.map(func(id): return str(game.roster[id].name_zh) + (" 濒死 · 不可出阵" if game.is_dying(game.roster[id]) else "")),
		members.map(func(id): return "camp:" + action + ":" + str(id)), Vector2(64, 32))

func _camp_action(action: String) -> void:
	var part = action.split(":")
	if part.size()>1 and part[0] in ["trade_first","trade_second","formation_first","formation_second","deposit_member","withdraw_member"]:
		if not game.can_deploy(game.roster.get(part[1],{})):
			_notice("濒死成员仍在队伍中，暂不能出阵或分配装备");return
	match part[0]:
		"roster": _camp_members("status")
		"status":
			status_id = part[1]
			if view in ["world", "hub"]: camp_context = view
			view = "camp_status"
		"trade": _camp_members("trade_first")
		"trade_first":
			camp_first = part[1]
			_camp_members("trade_second", camp_first)
		"trade_second":
			_notice("道具已交换" if game.exchange_items(camp_first, part[1]) else "无法交换")
			game.save_game()
		"formation": _camp_members("formation_first")
		"formation_first":
			camp_first = part[1]
			_camp_members("formation_second", camp_first)
		"formation_second":
			if camp_first == game.leader_id() or part[1] == game.leader_id():
				_notice("领队保持首位")
			else:
				var first = game.party.find(camp_first)
				var second = game.party.find(part[1])
				game.party[first] = part[1]
				game.party[second] = camp_first
				game.parties[game.route] = game.party.duplicate()
				_notice("出战顺序已调整")
				game.save_game()
		"convoy":
			_open_menu("convoy", ["存放装备", "领取装备"], ["camp:deposit", "camp:withdraw"], Vector2(64, 72))
		"deposit": _camp_members("deposit_member")
		"deposit_member":
			var unit = game.roster[part[1]]
			if game.convoy[game.route].size() >= 40:
				_notice("仓库已满")
				return
			if int(unit.item_id) > 0 and not bool(unit.get("dead", false)):
				game.convoy[game.route].append(int(unit.item_id))
				unit.item_id = 0
				game.save_game()
				_notice("已存入仓库")
		"withdraw":
			var stored: Array = game.convoy[game.route]
			if stored.is_empty():
				_notice("仓库没有道具")
			else:
				_open_menu("stored_items", stored.map(func(id): return Items.item(int(id)).name_zh), range(stored.size()).map(func(i): return "camp:withdraw_item:" + str(i)), Vector2(64, 32))
		"withdraw_item":
			camp_first = part[1]
			_camp_members("withdraw_member")
		"withdraw_member":
			var unit = game.roster[part[1]]
			if int(unit.item_id) == 0 and not bool(unit.get("dead", false)):
				unit.item_id = game.convoy[game.route].pop_at(int(camp_first))
				game.save_game()
				_notice("已领取道具")
			else:
				_notice("该角色无法领取")
		"switch":
			if game.switch_route():
				audio.play_world(game.chapter)
				game.save_game()
			else:
				_notice("另一支队伍暂时无法行动")
		"save":
			game.mode = "world"
			_notice("进度已保存" if game.save_game() else "保存失败")

func _choose_spell(id: int) -> void:
	var caster = game.find_unit(game.selected_id)
	if int(caster.hp) <= Items.cost(id):
		_notice("生命不足以施放")
		_unit_action_menu()
		return
	chosen_spell = id
	if Items.is_support(id):
		var kind = str(Items.spell(id).action)
		if kind in ["fortify", "invoke", "conjure", "expel"]:
			_play_support(str(caster.id), id)
			return
		target_ids = game.support_targets(caster, id).map(func(unit): return str(unit.id))
		ui_mode = "support_target"
	else:
		caster.weapon_index = id
		target_ids = game.targets(caster).map(func(unit): return str(unit.id))
		ui_mode = "target"
	if target_ids.is_empty():
		_notice("范围内没有合适目标")
		_unit_action_menu()
		return
	target_index = 0
	game.cursor = GameState.pos(game.find_unit(str(target_ids[0])))
	_focus_battle(game.cursor)

func _play_support(caster_id: String, spell_id: int, target_id: String = "", destination: Vector2i = Vector2i(-1, -1)) -> void:
	var previous: Dictionary = {}
	for unit in game.units:
		previous[str(unit.id)] = int(unit.hp)
	var result = game.use_support(caster_id, spell_id, target_id, destination)
	if result.is_empty():
		_notice("无法施放此魔法")
		if not game.selected_id.is_empty(): _unit_action_menu()
		else: game.mark_wait(caster_id)
		return
	busy = true
	_clear_menu()
	var caster = game.find_unit(caster_id)
	if spell_id in [35, 36, 37, 45, 46]:
		await _map_spell_feedback(caster, result)
		ui_mode = "inspect"
		busy = false
		_finish_turn_action()
		return
	if target_id.is_empty():
		var allies = game.living(str(caster.side)).filter(func(unit): return str(unit.id) != caster_id)
		target_id = str(allies[0].id) if not allies.is_empty() else caster_id
	var target = game.find_unit(target_id)
	combat = {"attacker": caster_id, "defender": target_id, "distance": 1, "initiative_side": caster.side, "support": true}
	combat_poses.clear()
	combat_offsets.clear()
	combat_fades.clear()
	combat_hp.clear()
	for id in [caster_id, target_id]:
		combat_poses[id] = int(_battle_sprite(game.find_unit(id)).sequences.idle[0])
		combat_offsets[id] = Vector2.ZERO
		combat_fades[id] = 1.0
		combat_hp[id] = int(previous.get(id, game.find_unit(id).hp))
	battle_animation.reset()
	view = "combat"
	audio.play_combat(caster, target, false, true, game.stage_id == 62)
	await battle_animation.play({"attacker": caster_id, "defender": target_id, "weapon_index": spell_id, "visual_only": true,
		"hit": true, "critical": false, "damage": 0, "hp_before": int(previous.get(target_id, target.hp)), "hp_after": int(target.hp),
		"source_hp_before": int(previous[caster_id]), "source_hp_after": int(caster.hp), "hp_cost": Items.cost(spell_id)})
	view = "battle"
	ui_mode = "inspect"
	busy = false
	_play_phase_music()
	game.save_game()
	_finish_turn_action()

func _next_source_dialogue() -> void:
	if dialogue_pages.is_empty():
		view = story_return_view
		return
	var text = str(dialogue_pages[dialogue_index].display_text)
	if int(dialogue_reveal) < text.length():
		dialogue_reveal = text.length()
		return
	dialogue_index += 1
	dialogue_reveal = 0.0
	if dialogue_index >= dialogue_pages.size():
		view = story_return_view

func _play_story_events() -> void:
	var was_busy = busy
	busy = true
	while not game.story_events.is_empty():
		var event: Dictionary = game.story_events.pop_front()
		if str(event.get("kind", "")) == "ending":
			_start_ending()
			return
		var group = str(event.get("group", "events"))
		var key = str(event.get("key", ""))
		var raw: Array = source_dialogues.get(group, {}).get(key, [])
		var meta: Array = source_dialogue_meta.get(group, {}).get(key, {}).get("pages", [])
		if raw.is_empty() or instant_mode: continue
		dialogue_pages.clear()
		for i in range(raw.size()):
			var page: Dictionary = meta[i] if i < meta.size() else {}
			var speaker = int(page.get("speaker_id", 0))
			var text = str(raw[i]).replace("%2", _character_name(speaker))
			var lines = _wrapped_lines(text, 152.0)
			for start in range(0, lines.size(), 4):
				dialogue_pages.append({"speaker_id": speaker, "face_id": int(page.get("face_id", speaker)), "display_text": "\n".join(lines.slice(start, mini(start + 4, lines.size())))})
		dialogue_index = 0
		dialogue_reveal = 0
		story_return_view = view
		view = "battle_story"
		while view == "battle_story": await get_tree().process_frame
	busy = was_busy
	game.save_game()

func _character_name(source_id: int) -> String:
	var key = game.character_key(source_id)
	if not key.is_empty(): return str(game.characters[key].name_zh)
	for group in game.catalog.enemy_groups.values():
		for enemy in group.get("enemies", []):
			if int(enemy.get("character_id", 0)) == source_id: return str(enemy.name_zh)
	return ""

func _portrait(source_id: int) -> Dictionary:
	if source_id <= 0 or not graphics.character_portraits.has(str(source_id)): return {}
	var index = int(graphics.character_portraits[str(source_id)])
	if source_id == 1 and bool(game.roster.get("alm", {}).get("promoted", false)): index = int(graphics.character_portraits["36"])
	if source_id == 2 and bool(game.flags.get("celica_promoted", false)): index = int(graphics.character_portraits["37"])
	return graphics.portraits_by_index.get(str(index), {})

func _start_ending() -> void:
	busy = false
	batch_running = false
	_clear_menu()
	ending_pages.clear()
	for page in ending_data.final_words:
		_ending_page("多玛", str(page.text_zh), 167)
	for page in ending_data.narration:
		_ending_page("瓦伦西亚的黎明", str(page.text_zh))
	for cid in ending_data.display_order:
		var id = game.character_key(int(cid))
		if id.is_empty() or not game.roster.has(id): continue
		var unit: Dictionary = game.roster[id]
		var selector: Dictionary = ending_data.characters.get(str(int(cid)), {})
		var text_id = int(selector.get("ending_id", selector.get("default_ending_id", 1)))
		if bool(unit.get("dead", false)):
			text_id = 1
		elif str(selector.get("kind", "")) == "dependent_survival":
			var mask = 0
			for i in range(selector.related_character_ids.size()):
				var related = game.character_key(int(selector.related_character_ids[i]))
				if game.roster.has(related) and not bool(game.roster[related].get("dead", false)): mask |= 8 >> i
			for rule in selector.rules:
				if int(rule.living_mask) == mask: text_id = int(rule.ending_id)
		var text = str(ending_data.texts.get(str(text_id), {}).get("text_zh", ""))
		text = text.replace("{death_place}", str(unit.get("death_place", "曾经的战场")))
		_ending_page(str(unit.name_zh), text, int(cid))
	_ending_page("全篇结束", "感谢你走完这段旅程。")
	ending_index = 0
	view = "ending"
	game.mode = "ending"
	audio.play_ending()
	game.save_game()

func _ending_page(title: String, text: String, source_id: int = 0) -> void:
	var lines = _wrapped_lines(text, 200)
	for start in range(0, lines.size(), 5):
		ending_pages.append({"title": title, "text": "\n".join(lines.slice(start, mini(start + 5, lines.size()))), "source_id": source_id})

func _draw_ending() -> void:
	if ending_pages.is_empty(): return
	var page: Dictionary = ending_pages[clampi(ending_index, 0, ending_pages.size()-1)]
	_panel(Rect2(8, 8, 240, 224))
	_center_text(str(page.title), Rect2(20, 22, 216, 24))
	var face = _portrait(int(page.source_id))
	if not face.is_empty(): draw_texture(_tex(face.path), Vector2(104, 54))
	_center_text(str(page.text), Rect2(24, 112, 208, 80))
	_center_text("确认继续", Rect2(24, 204, 208, 16))

func _show_help() -> void:
	_notice("Z确认 X返回 S菜单\nTab状态 左右切换队员\nQ/E定位未行动友军", 4.0)

func _notice(text: String, seconds: float = 2.0) -> void:
	notice = text
	notice_time = seconds

func _animate_move(unit: Dictionary, path: Array, open_action: bool = false) -> void:
	busy = true
	moving_id = str(unit.id)
	moving_position = Vector2(GameState.pos(unit)) * TILE
	for i in range(1, path.size()):
		var from = Vector2(path[i - 1]) * TILE
		var to = Vector2(path[i]) * TILE
		moving_direction = path[i] - path[i - 1]
		var native_ticks=int(_map_unit_sprite(unit).get("native_move_ticks",4))
		for tick in range(native_ticks):
			moving_frame = (int(elapsed*60.0988)>>4)&1 if native_ticks==16 else tick / 2
			moving_position = from.lerp(to, float(tick + 1) / float(native_ticks))
			_focus_battle(Vector2i(moving_position / TILE))
			await _wait(1.0/60.0988 if native_ticks==16 else 0.035)
	unit.position = [path[-1].x, path[-1].y]
	game.cursor = path[-1]
	_focus_battle(game.cursor)
	moving_id = ""
	busy = false
	if open_action:
		_unit_action_menu()

func _play_combat(attacker_id: String, defender_id: String) -> void:
	var exchange = game.plan_combat(attacker_id, defender_id)
	if exchange.is_empty():
		return
	busy = true
	held_direction = Vector2i.ZERO
	_clear_menu()
	combat = exchange
	combat_poses.clear()
	combat_offsets.clear()
	combat_hp.clear()
	combat_fades.clear()
	combat_message = ""
	combat_shake = 0.0
	combat_projectile.clear()
	battle_animation.reset()
	for id in [attacker_id, defender_id]:
		combat_poses[id] = int(_battle_sprite(game.find_unit(id)).sequences.idle[0])
		combat_offsets[id] = Vector2.ZERO
		combat_hp[id] = int(game.find_unit(id).hp)
		combat_fades[id] = 1.0
	view = "combat"
	var attacker = game.find_unit(attacker_id)
	var defender = game.find_unit(defender_id)
	audio.play_combat(attacker if attacker.side == "player" else defender, defender if attacker.side == "player" else attacker, attacker.side == "enemy", false, game.stage_id == 62)
	await _wait(0.3)
	for event in exchange.events:
		await _animate_strike(event)
	reward = game.finish_exchange(exchange)
	game.save_game()
	await _resolve_pending_loot()
	await _wait(0.3)
	view = "battle"
	ui_mode = "inspect"
	await _play_story_events()
	busy = false
	_play_phase_music()
	if not reward.is_empty() and int(reward.gain) > 0:
		view = "reward"
		reward_elapsed = 0.0
		reward_dismissed = false
		if bool(reward.leveled):
			audio.play_jingle("levelup")
	elif game.battle_outcome != "":
		_show_result()
	else:
		_finish_turn_action()

func _animate_strike(event: Dictionary) -> void:
	await battle_animation.play(event)

func _animate_ranged_strike(event: Dictionary, _sprite: Dictionary) -> void:
	await battle_animation.play(event)

func _contact(event: Dictionary) -> void:
	var target_id = str(event.defender)
	if not bool(event.get("visual_only", false)):
		game.commit_strike(event)
	if bool(event.get("visual_only", false)):
		combat_message = str(Items.spell(int(event.get("weapon_index", 40))).get("name_zh", ""))
		combat_hp[target_id] = int(event.hp_after)
		await _wait(0.3)
		return
	if not bool(event.hit):
		combat_message = "未命中"
		audio.play_sfx("miss")
		await _wait(0.45)
		return
	var recoil = int(event.get("self_damage", 0)) > 0
	var feedback_id = str(event.attacker) if recoil else target_id
	var feedback_before = int(event.source_hp_before) - int(event.get("hp_cost", 0)) if recoil else int(event.hp_before)
	var feedback_after = int(event.source_hp_after) if recoil else int(event.hp_after)
	combat_message = "反噬" if recoil else ("必杀" if bool(event.critical) else "")
	combat_hit_id = feedback_id
	combat_hit_time = 0.5
	audio.play_sfx("hit")
	# Original PPU horizontal-scroll hit feedback, one step per NTSC frame.
	for displacement in [3, 1, 2, 1, 3, 1, 2, 4, 2, 1, 0]:
		combat_shake = float(displacement)
		await _wait(1.0 / 60.0988)
	combat_shake = 0.0
	for hp in range(feedback_before - 1, feedback_after - 1, -1):
		combat_hp[feedback_id] = hp
		audio.play_sfx("hp_tick")
		await _wait(1.0 / 60.0988)
	await _wait(16.0 / 60.0988)
	if feedback_after == 0:
		for step in range(4):
			combat_fades[feedback_id] = 1.0 - float(step + 1) / 4.0
			await _wait(8.0 / 60.0988)
		if game.find_unit(feedback_id).side == "player" and feedback_id not in ["alm", "celica"]:
			audio.play_jingle("unit_death")

func _wait(seconds: float) -> void:
	if instant_mode:
		return
	var speed = animation_speed
	if Input.is_physical_key_pressed(KEY_Z) or Input.is_physical_key_pressed(KEY_SPACE):
		speed *= 3.0
	# Batch accelerated source ticks; a per-tick Timer cannot run faster
	# than the renderer and otherwise makes the speed key ineffective.
	wait_accumulated += seconds / speed
	if wait_accumulated < 1.0 / 60.0988: return
	var duration = wait_accumulated
	wait_accumulated = 0.0
	await get_tree().create_timer(maxf(0.001, duration)).timeout

func _wait_for_reward() -> void:
	if instant_mode:
		return
	# Normal EXP stays visible; a level-up waits for an explicit confirmation.
	while view == "reward" and not reward_dismissed:
		if not bool(reward.leveled) and reward_elapsed >= 2.0:
			return
		await get_tree().process_frame

func _finish_turn_action() -> void:
	game.save_game()
	if game.battle_outcome != "":
		_show_result()
	elif not batch_running and game.phase == "player" and game.phase_finished():
		_enemy_phase()

func _run_ai_unit(unit: Dictionary, gather: bool = false) -> void:
	if int(unit.hp) <= 0 or bool(unit.acted): return
	var action = game.ai_action(unit, gather)
	if bool(action.get("teleport", false)):
		await map_effects.teleport(unit, action.teleport_position)
	var path = game.path_to(unit, action.destination)
	if not path.is_empty(): await _animate_move(unit, path)
	busy = true
	if action.has("special"):
		var result = game.apply_ai_special(unit, action)
		await _map_spell_feedback(unit, result)
	elif bool(action.get("support", false)):
		await _play_support(str(unit.id), int(action.spell_id), str(action.target))
	elif str(action.target) != "":
		if int(action.get("spell_id", -1)) >= 0: unit.weapon_index = int(action.spell_id)
		else: unit.erase("weapon_index")
		await _play_combat(str(unit.id), str(action.target))
		if view == "reward":
			await _wait_for_reward()
			view = "battle"
	else:
		game.mark_wait(str(unit.id))
	busy = true

func _enemy_phase() -> void:
	if busy or batch_running or view != "battle": return
	batch_running = true
	busy = true
	if game.phase == "player":
		# Source slot order includes newly invoked allies in this same phase.
		for slot in range(20):
			for unit in game.living("player"):
				if int(unit.get("player_slot", -1)) == slot and not bool(unit.get("controllable", true)):
					await _run_ai_unit(unit)
					if game.battle_outcome != "": break
			if game.battle_outcome != "": break
		if game.battle_outcome != "":
			busy = false
			batch_running = false
			_show_result()
			return
		game.next_phase()
		await _play_story_events()
	var forced = Inventory.forced_retreat(game)
	if bool(forced.get("triggered", false)):
		busy = false
		batch_running = false
		_continue_world()
		_notice("进攻方撤退了")
		return
	phase_banner = "敌方回合"
	phase_time = 1.2
	_play_phase_music()
	await _wait(1.0)
	for slot in range(20):
		# Re-query each source slot: Cantor summons can occupy a later slot.
		for unit in game.living("enemy"):
			if int(unit.get("enemy_slot", game.units.find(unit))) != slot: continue
			await _run_ai_unit(unit)
			if game.battle_outcome != "": break
		if game.battle_outcome != "": break
		await _wait(0.08)
	busy = false
	batch_running = false
	if game.battle_outcome != "":
		_show_result()
		return
	game.next_phase()
	view = "battle"
	ui_mode = "inspect"
	phase_banner = "我方回合"
	phase_time = 1.2
	_focus_player_leader()
	_play_phase_music()
	game.save_game()
	await _play_story_events()

func _auto_player(gather: bool) -> void:
	if busy or batch_running or view != "battle" or game.battle_outcome != "" or game.phase != "player": return
	batch_running = true
	busy = true
	for unit in game.living("player"):
		if not bool(unit.get("controllable", true)): continue
		await _run_ai_unit(unit, gather)
		if game.battle_outcome != "": break
	busy = false
	batch_running = false
	if game.battle_outcome != "": _show_result()
	else: await _enemy_phase()

func _map_spell_feedback(caster: Dictionary, result: Dictionary) -> void:
	view = "battle"
	busy = true
	_focus_battle(GameState.pos(caster), true)
	var kind = str(result.get("action", ""))
	if kind in ["summon", "invoke", "conjure"]:
		for id in result.get("spawned", []): map_actor_alpha[str(id)] = 0.0
		if not bool(result.get("divide", false)): await map_effects.flash("invoke")
		for id in result.get("spawned", []):
			var unit = game.find_unit(str(id))
			await map_effects.play_program(map_effects.summon_program(unit), unit)
			map_actor_alpha.erase(str(id))
	elif kind == "expel":
		await map_effects.flash("expel")
		for change in result.get("changed", []):
			var unit = game.find_unit(str(change.id))
			await map_effects.play_program(map_effects.summon_program(unit, true), unit)
	elif kind == "quake":
		await map_effects.flash("quake")
		for change in result.get("changed", []):
			if int(change.before) != int(change.after): await map_effects.play_program(9, game.find_unit(str(change.id)))
	else:
		for change in result.get("changed", []):
			if int(change.get("before", 0)) != int(change.get("after", 0)): await map_effects.play_program(10, game.find_unit(str(change.id)))
	map_effects.reset()
	_play_phase_music()
	game.save_game()

func _show_result() -> void:
	# An AI exchange and its outer phase may both request result display.
	# Keep a pending dialogue/ending sequence single-owned and resumable.
	if result_sequence_running: return
	if bool(game.flags.get("campaign_complete", false)) and game.battle_settled:
		if view != "ending": _start_ending()
		return
	result_sequence_running = true
	view = game.battle_outcome
	game.mode = view
	busy = false
	_clear_menu()
	if view == "victory":
		var settled=game.complete_battle()
		if settled and has_method("play_victory_rewards"):await call("play_victory_rewards")
	else:
		audio.stop_all()
		audio.play_jingle("unit_death")
	game.save_game()
	await _resolve_pending_loot()
	await _play_story_events()
	result_sequence_running = false

func _battle_sprite(unit: Dictionary) -> Dictionary:
	return battle_animation.sprite(unit)

func _tex(path: String) -> Texture2D:
	if not textures.has(path):
		textures[path] = load(path)
	return textures[path]

func _draw() -> void:
	if graphics.is_empty():
		return
	safe_panels.clear()
	text_checks.clear()
	layout_errors.clear()
	health_checks.clear()
	draw_set_transform(Vector2.ZERO)
	draw_rect(get_viewport_rect(), Color.BLACK)
	draw_set_transform(_canvas_offset())
	if view.begins_with("hub"):
		hub_controller.draw()
	match view:
		"title": _draw_title()
		"lore": _draw_lore()
		"chapter": _draw_chapter()
		"village", "dialogue", "village_status": _draw_village()
		"world": _draw_world()
		"battle", "reward", "victory", "defeat", "loot", "loot_confirm": _draw_battle()
		"combat": _draw_combat()
		"battle_story":
			if not game.units.is_empty(): _draw_battle()
			_draw_dialogue()
		"camp_status":
			_draw_world()
			_draw_status(game.roster.get(status_id, {}))
		"ending": _draw_ending()
	if view == "dialogue":
		_draw_dialogue()
	if view == "village_status":
		var unit: Dictionary = game.roster.get(status_id, game.opening.characters[status_id]).duplicate(true)
		unit.id = status_id
		_draw_status(unit)
	if view == "reward":
		_draw_reward()
	if view in ["victory", "defeat"]:
		_draw_result()
	if view in ["loot", "loot_confirm"]:
		var record: Dictionary = game.flags.get("pending_loot", [{}])[0]
		_panel(Rect2(16, 24, 224, 80))
		_center_text("获得" + str(Items.item(int(record.item_id)).name_zh), Rect2(28, 38, 200, 20))
		_center_text("确认丢弃？" if view == "loot_confirm" else "请选择道具的去向", Rect2(28, 68, 200, 20))
	if not menu_items.is_empty():
		_draw_menu()
	# Ambient map notices must not cover modal statistics or combat information.
	if notice_time > 0.0 and not _status_open() and view not in ["combat", "reward"] and ui_mode not in ["target", "support_target", "warp"]:
		var lines = _wrapped_lines(notice, 208.0)
		var rect = Rect2(8, 232 - (28 + lines.size() * 16), 240, 28 + lines.size() * 16)
		_panel(rect)
		_text("\n".join(lines), rect.position + Vector2(16, 16))

func _canvas_offset() -> Vector2:
	return Vector2.ZERO

func _panel(rect: Rect2) -> void:
	var image = _tex(graphics.panel.path)
	var positions_x = [rect.position.x, rect.position.x + 8, rect.end.x - 8]
	var positions_y = [rect.position.y, rect.position.y + 8, rect.end.y - 8]
	var widths = [8.0, rect.size.x - 16, 8.0]
	var heights = [8.0, rect.size.y - 16, 8.0]
	for y in range(3):
		for x in range(3):
			draw_texture_rect_region(image, Rect2(positions_x[x], positions_y[y], widths[x], heights[y]), Rect2(x * 8, y * 8, 8, 8))
	safe_panels.append(rect.grow(-10))

func _glyph(code: int, at: Vector2, color: Color = Color.WHITE) -> void:
	var source = Rect2((code % 16) * 8, (code / 16) * 8, 8, 8)
	draw_texture_rect_region(_tex(graphics.font.path), Rect2(at.round(), Vector2(8, 8)), source, color)

func _zh_glyph(character: String) -> Dictionary:
	# The original Japanese atlas has no ASCII arithmetic signs. Reuse the
	# existing pixel-font signs at their 7 px ink width, keeping 8 px spacing.
	var symbol={"+":"＋","-":"－"}.get(character,"")
	if not symbol.is_empty():
		var glyph: Dictionary=chinese_font.get("glyphs",{}).get(symbol,{}).duplicate(true)
		if not glyph.is_empty():
			glyph.rect[0]+=2;glyph.rect[2]=8;glyph.advance=8
			return glyph
	if character.unicode_at(0) <= 127:
		return {}
	return chinese_font.get("glyphs", {}).get(character, {})

func _character_width(character: String) -> float:
	var glyph = _zh_glyph(character)
	return float(glyph.advance) if not glyph.is_empty() else 8.0

func _text_width(text: String) -> float:
	var width := 0.0
	var maximum := 0.0
	for character in text:
		if character == "\n":
			maximum = maxf(maximum, width)
			width = 0.0
		else:
			width += _character_width(character)
	return maxf(maximum, width)

func _text_height(text: String) -> float:
	var height := 8.0
	for character in text:
		if character != "\n" and not _zh_glyph(character).is_empty():
			height = 12.0
	return (text.split("\n").size() - 1) * 16.0 + height

func _wrapped_lines(text: String, maximum_width: float) -> Array[String]:
	var lines: Array[String] = []
	var line := ""
	for character in text:
		if character == "\n":
			lines.append(line)
			line = ""
			continue
		if not line.is_empty() and _text_width(line + character) > maximum_width:
			# Closing punctuation follows its word instead of beginning a line.
			if character in ["，", "。", "！", "？", "：", "；", "、", "）", "》", "”", "…"] and line.length() > 1:
				var carry = line.right(1)
				lines.append(line.left(line.length() - 1))
				line = carry
			else:
				lines.append(line)
				line = ""
		line += character
	lines.append(line)
	return lines

func _text(text: String, at: Vector2, color: Color = Color.WHITE, audit: bool = true, max_width: float = 0.0) -> void:
	var rendered = "\n".join(_wrapped_lines(text, max_width)) if max_width > 0.0 else text
	var start = at.round()
	var cursor = start
	var height = 12.0 if _text_height(rendered) > (rendered.split("\n").size() - 1) * 16 + 8 else 8.0
	var minimum_y = start.y
	for character in rendered:
		if character == "\n":
			cursor = Vector2(start.x, cursor.y + 16)
			continue
		var glyph = _zh_glyph(character)
		if not glyph.is_empty():
			var r: Array = glyph.rect
			draw_texture_rect_region(_tex(chinese_font.path), Rect2(cursor, Vector2(r[2], r[3])), Rect2(r[0], r[1], r[2], r[3]), color)
			cursor.x += float(glyph.advance)
		else:
			var codes: Array = graphics.font.char_codes.get(character, [0x9c])
			for code_value in codes:
				var code = int(code_value)
				if code in [15, 31]:
					_glyph(code, cursor - Vector2(8, 8), color)
					minimum_y = minf(minimum_y, cursor.y - 8)
				else:
					_glyph(code, cursor + Vector2(0, (height - 8) / 2), color)
					cursor.x += 8
	if audit and not text.is_empty():
		var bounds = Rect2(Vector2(start.x, minimum_y), Vector2(_text_width(rendered), _text_height(rendered) + start.y - minimum_y))
		text_checks.append({"text": text, "bounds": bounds})
		if not safe_panels.is_empty() and not safe_panels[-1].encloses(bounds):
			layout_errors.append("Text outside content-safe rectangle: " + text)

func _center_text(text: String, rect: Rect2, color: Color = Color.WHITE, audit: bool = true) -> void:
	var lines = text.split("\n")
	var top = rect.position.y + (rect.size.y - _text_height(text)) / 2.0
	for i in range(lines.size()):
		var line: String = lines[i]
		_text(line, Vector2(rect.position.x + (rect.size.x - _text_width(line)) / 2.0, top + i * 16), color, audit)

func _draw_title() -> void:
	draw_texture(_tex(graphics.title.path), Vector2.ZERO)
	# Localize the original logo area while retaining the source sword art.
	draw_rect(Rect2(52, 110, 158, 20), Color.BLACK)
	_center_text("火焰之纹章 外传", Rect2(32, 106, 192, 28), Color(0.7, 0.85, 1.0), false)
	if title_menu:
		var rect = Rect2(56, 180, 144, 56)
		_panel(rect)
		for i in range(2):
			_center_text(game.opening.title.options_zh[i], Rect2(72, 190 + i * 16, 112, 16), Color.WHITE if i == 0 or FileAccess.file_exists(game.save_path) else Color(0.5, 0.5, 0.5))
		_draw_menu_arrow(Vector2(84, 194 + title_selected * 16))
	elif fmod(elapsed, 1.6) < 1.1:
		_center_text("按确认键开始", Rect2(32, 184, 192, 24), Color.WHITE, false)
	if elapsed > 20.0 and not title_menu:
		call_deferred("_show_lore")

func _draw_chapter() -> void:
	_center_text("第" + ["一", "二", "三", "四", "五"][clampi(game.chapter - 1, 0, 4)] + "章", Rect2(16, 72, 224, 32), Color.WHITE, false)
	_center_text(game.catalog.chapters[clampi(game.chapter - 1, 0, 4)].title_zh, Rect2(16, 112, 224, 32), Color.WHITE, false)
	if chapter_elapsed > 4.0:
		_center_text("Z / ENTER", Rect2(16, 184, 224, 24), Color(0.6, 0.6, 0.6), false)

func _lore_height() -> float:
	var count = 0
	for paragraph in game.opening.attract_intro.paragraphs_zh:
		count += _wrapped_lines(str(paragraph), 224.0).size() + 2
	return count * 16.0

func _draw_lore() -> void:
	var y = lore_y
	for paragraph in game.opening.attract_intro.paragraphs_zh:
		for line in _wrapped_lines(str(paragraph), 224.0):
			if y >= -8 and y <= 248:
				_center_text(line, Rect2(0, y - 8, 256, 16), Color.WHITE, false)
			y += 16
		y += 32

func _draw_map(map: Dictionary, atlas: Texture2D, origin: Vector2) -> void:
	for y in range(int(map.height)):
		for x in range(int(map.width)):
			var target = origin + Vector2(x, y) * TILE
			if target.x < -16 or target.x >= 256 or target.y < -16 or target.y >= 240:
				continue
			var tile = int(map.tiles[y * int(map.width) + x])
			draw_texture_rect_region(atlas, Rect2(target, Vector2(16, 16)), Rect2((tile % 16) * 16, (tile / 16) * 16, 16, 16))

func _draw_village() -> void:
	if village_motion_time <= 0.0 and village_render_position != Vector2(game.village_position) * TILE:
		_sync_village_position()
	camera_x = roundf(clampf(village_render_position.x - 120.0, 0.0, 128.0))
	var origin = Vector2(-camera_x, 0)
	var atlas = _tex("res://assets/original/graphics/maps/buildings.png")
	_draw_map(game.opening.village, atlas, origin)
	for object in game.opening.village.objects:
		_draw_map(object.map, atlas, origin + Vector2(object.x, object.y) * TILE)
	for npc in game.opening.village.npcs:
		if _npc_present(str(npc.id)):
			_draw_village_unit(str(npc.id), Vector2(npc.position[0], npc.position[1]) * TILE + origin, "down")
	var direction = "up" if game.village_facing.y < 0 else ("side" if game.village_facing.x != 0 else "down")
	_draw_village_unit("alm", village_render_position + origin, direction, _village_side_flip(game.village_facing), village_motion_time > 0.0)

func _village_side_flip(facing: Vector2i) -> bool:
	# The original CHR30 side poses face right; only left needs mirroring.
	return facing.x < 0

func _sync_village_position() -> void:
	village_render_position = Vector2(game.village_position) * TILE
	village_step_origin = village_render_position
	village_step_target = village_render_position
	village_motion_time = 0.0

func _draw_village_unit(id: String, at: Vector2, direction: String, flip: bool = false, walking: bool = false) -> void:
	var sprite = graphics.village_units[id]
	var step = (int(elapsed * 60.0988) >> 4) & 1 if walking else 0
	var frame = int(sprite.directions[direction][step])
	_draw_frame(sprite, frame, at - Vector2(4, 4), flip)

func _draw_frame(sprite: Dictionary, frame: int, at: Vector2, flip: bool = false, color: Color = Color.WHITE) -> void:
	var source_size = Vector2(sprite.frame_size[0], sprite.frame_size[1])
	var size = source_size / maxf(1.0, float(sprite.get("native_density", 1)))
	var destination = Rect2(at.round(), size)
	if flip:
		# Godot makes a negative width positive and sets FLIP_H at this origin.
		# Adding the frame width here shifts every enemy sprite out of place.
		destination.size.x = -size.x
	draw_texture_rect_region(_tex(sprite.path), destination, Rect2(frame * source_size.x, 0, source_size.x, source_size.y), color)

func _draw_dialogue() -> void:
	if dialogue_pages.is_empty():
		return
	var page = dialogue_pages[mini(dialogue_index, dialogue_pages.size() - 1)]
	# PAGE can reuse a previously loaded portrait when NAME changes speakers.
	var id = str(page.get("speaker", ""))
	if id.is_empty():
		id = str(page.get("face", ""))
	if id.is_empty():
		id = dialogue_actor
	if page.has("speaker_id"):
		_panel(Rect2(8, 128, 240, 104))
		var face = _portrait(int(page.get("face_id", page.speaker_id)))
		if not face.is_empty(): draw_texture(_tex(face.path), Vector2(20, 164))
		_center_text(_character_name(int(page.speaker_id)), Rect2(20, 138, 216, 16))
		var text = str(page.display_text)
		_text(text.left(int(dialogue_reveal)), Vector2(80, 160))
		if int(dialogue_reveal) >= text.length() and fmod(elapsed, 0.8) < 0.5:
			_draw_indicator("down", Vector2(232, 216))
		return
	var rect = Rect2(8, 136, 240, 96)
	_panel(rect)
	if graphics.portraits.has(id):
		draw_texture(_tex(graphics.portraits[id].path), Vector2(20, 168))
		var name = str(game.opening.characters.get(id, {}).get("name_zh", ""))
		_text(name, Vector2(20, 152))
	var raw = str(page.display_text)
	var shown = raw.left(int(dialogue_reveal))
	_text(shown, Vector2(80, 152))
	if int(dialogue_reveal) >= raw.length() and fmod(elapsed, 0.8) < 0.5:
		_draw_indicator("down", Vector2(232, 216))

func _draw_world() -> void:
	var node: Dictionary = world.nodes[str(game.world_node)]
	var cell = Vector2(node.position[0], node.position[1])
	var camera = cell * TILE - Vector2(120, 96)
	camera.x = clampf(camera.x, 0, int(world.width) * TILE - 256)
	camera.y = clampf(camera.y, 0, int(world.height) * TILE - 240)
	var origin = -camera.round()
	_draw_map(world, _tex("res://assets/original/graphics/maps/worldtiles.png"), origin)
	for node_id in game.world_armies:
		var enemy_node: Dictionary = world.nodes.get(str(node_id), {})
		if enemy_node.is_empty() or not int(node_id) in game.allowed_world_nodes(): continue
		var at = Vector2(enemy_node.position[0], enemy_node.position[1]) * TILE + origin
		if at.x < -16 or at.x > 256 or at.y < -16 or at.y > 160: continue
		var sprite: Dictionary = graphics.map_units.class_6_enemy
		_draw_frame(sprite, int(sprite.directions.down[0]), at - Vector2(4, 4))
	var leader_sprite: Dictionary = graphics.village_sprites["2" if game.route == "celica" else "1"]
	var leader_at = cell * TILE + origin
	_draw_frame(leader_sprite, int(leader_sprite.directions.up[0]), leader_at - Vector2(leader_sprite.tile_origin[0], leader_sprite.tile_origin[1]))
	_draw_indicator("down", leader_at + Vector2(4, -8))
	for neighbor in game.world_neighbors():
		var point: Array = world.nodes[str(neighbor)].position
		var delta = Vector2(point[0], point[1]) - cell
		var direction = ("right" if delta.x > 0 else "left") if absf(delta.x) > absf(delta.y) else ("down" if delta.y > 0 else "up")
		_draw_indicator(direction, leader_at + delta.normalized() * 22 + Vector2(4, 4))
	_panel(Rect2(16, 160, 224, 72))
	_center_text(str(node.name_zh), Rect2(28, 170, 200, 16))
	_center_text("阿尔姆军" if game.route == "alm" else "赛莉卡军", Rect2(28, 188, 200, 16))
	var action = "确认进入战斗" if game.world_has_battle(game.world_node) else ("确认进入据点" if game.world_node >= 49 else "确认整备部队")
	_center_text(action + "  S菜单", Rect2(28, 206, 200, 16))

func _battle_cell_screen(cell: Vector2i) -> Vector2:
	return Vector2(cell) * TILE - battle_camera

func _battle_screen_cell(point: Vector2) -> Vector2i:
	return Vector2i(floori((point.x + battle_camera.x) / TILE), floori((point.y + battle_camera.y) / TILE))

func _focus_battle(cell: Vector2i, force: bool = false) -> void:
	var pixel = Vector2(cell) * TILE
	if force:
		battle_camera = pixel - Vector2(7, 7) * TILE
	else:
		var local = pixel - battle_camera
		if local.x < 3 * TILE:
			battle_camera.x = pixel.x - 3 * TILE
		elif local.x > 12 * TILE:
			battle_camera.x = pixel.x - 12 * TILE
		if local.y < 3 * TILE:
			battle_camera.y = pixel.y - 3 * TILE
		elif local.y > 11 * TILE:
			battle_camera.y = pixel.y - 11 * TILE
	var maximum = Vector2(int(game.battle_data.map.width) * TILE, int(game.battle_data.map.height) * TILE) - NATIVE
	battle_camera.x = roundf(clampf(battle_camera.x, 0, maxf(0, maximum.x)))
	battle_camera.y = roundf(clampf(battle_camera.y, 0, maxf(0, maximum.y)))

func _draw_battle() -> void:
	draw_set_transform(_canvas_offset()+map_offset)
	_draw_map(game.battle_data.map, _tex("res://assets/original/graphics/maps/tileset.png"), -battle_camera)
	presentation_audit.enemy_range = []
	if view == "battle" and ui_mode == "inspect" and menu_items.is_empty() and not busy and not batch_running and phase_time <= 0.0:
		var hovered = game.unit_at(game.cursor)
		if str(hovered.get("side", "")) == "enemy" and not bool(hovered.get("event_object", false)):
			var cells = _enemy_movement_cells(hovered)
			for cell in cells:
				draw_rect(Rect2(_battle_cell_screen(cell), Vector2(16, 16)), Color(0.92, 0.17, 0.17, 0.32))
			presentation_audit.enemy_range = cells
	if ui_mode == "move" and game.selected_id != "":
		var graph = game.reachable(game.find_unit(game.selected_id))
		for cell in graph.costs:
			if game.can_stop(game.find_unit(game.selected_id), cell):
				draw_rect(Rect2(_battle_cell_screen(cell), Vector2(16, 16)), Color(0.2, 0.35, 1.0, 0.3))
	for unit in game.units:
		if int(unit.hp) <= 0 or bool(unit.get("hidden", false)):
			continue
		if unit.has("sprite_path"):
			var object_at=moving_position-battle_camera if moving_id==str(unit.id) else _battle_cell_screen(GameState.pos(unit))
			var object_texture=_tex(str(unit.sprite_path))
			var object_offset=Vector2((object_texture.get_width()-16)/2,object_texture.get_height()-16)
			if unit.has("sprite_offset"):object_offset=-Vector2(unit.sprite_offset[0],unit.sprite_offset[1])
			draw_texture(object_texture,object_at-object_offset)
			continue
		if str(unit.id)=="medicine_wagon":
			var wagon_at=moving_position-battle_camera if moving_id==str(unit.id) else _battle_cell_screen(GameState.pos(unit))
			draw_texture(_tex("res://assets/battle_tiles/modules/medicine_wagon.png"),wagon_at-Vector2(8,0))
			continue
		var sprite = _map_unit_sprite(unit)
		var at = moving_position - battle_camera if moving_id == str(unit.id) else _battle_cell_screen(GameState.pos(unit))
		if unit.get("surrendered",false) or unit.get("offering_surrender",false):draw_texture(_tex("res://assets/battle_tiles/modules/white_flag.png"),at-Vector2(2,8))
		var direction = "up" if moving_direction.y < 0 else ("side" if moving_direction.x != 0 else "down")
		var is_moving = moving_id == str(unit.id)
		var frame = _native_map_pose(sprite) if sprite.has("native_cycle") else int(sprite.directions[direction][moving_frame]) if is_moving else int(sprite.directions.down[0])
		var tile_origin=sprite.get("tile_origin",[4,4])
		var map_flip=not sprite.get("static_facing",false) and is_moving and (moving_direction.x > 0 if sprite.get("default_facing","right")=="left" else moving_direction.x < 0)
		_draw_frame(sprite, frame, at - Vector2(tile_origin[0],tile_origin[1]), map_flip, Color(1, 1, 1, float(map_actor_alpha.get(str(unit.id), 1.0))))
	if view == "battle":
		if ui_mode == "status":
			_draw_status(game.find_unit(status_id))
		elif ui_mode == "target":
			_draw_preview()
		elif ui_mode in ["support_target", "warp"]:
			_draw_support_preview()
		elif ui_mode != "whole_capture":
			var at = _battle_cell_screen(game.cursor)
			var selected_unit=game.unit_at(game.cursor)
			var arrow_y=-3
			if not selected_unit.is_empty():
				var selected_sprite=_map_unit_sprite(selected_unit)
				arrow_y=-int(selected_sprite.get("tile_origin",[4,4])[1])-9
			_draw_indicator("down", at + Vector2(4, arrow_y + int(sin(elapsed * 6.0))))
			if ui_mode == "inspect" and menu_items.is_empty():
				var unit = game.unit_at(game.cursor)
				if not unit.is_empty():
					_draw_unit_card(unit)
	map_effects.draw()
	draw_set_transform(_canvas_offset())
	if phase_time > 0.0 and view == "battle" and ui_mode == "inspect" and menu_items.is_empty():
		var rect = Rect2(64, 96, 128, 48)
		_panel(rect)
		_center_text(phase_banner, rect.grow(-10))

func _enemy_movement_cells(unit: Dictionary) -> Array:
	var blockers: Array = []
	for other in game.units:
		blockers.append([other.id, other.position, other.hp, other.get("hidden", false), other.side])
	var stamp = str([game.stage_id, game.turn, game.battle_data.map.tiles.hash(), blockers.hash(), unit.id, unit.get("move", 0), unit.get("item_id", 0)])
	if stamp != enemy_range_key:
		enemy_range_key = stamp
		enemy_range_cells = game.reachable(unit).costs.keys().filter(func(cell): return game.can_stop(unit, cell))
	return enemy_range_cells

func _map_unit_sprite(unit: Dictionary) -> Dictionary:
	var key = "class_" + str(int(unit.class_id)) + ("_ally" if unit.side in ["player", "neutral"] else "_enemy")
	var sprite: Dictionary = graphics.map_units[key]
	if not bool(unit.acted) or not sprite.has("acted_variant"): return sprite
	sprite = graphics.map_units[str(sprite.acted_variant)]
	if unit.side != "enemy": return sprite
	# Preserve every source pixel/alpha; only the two grey palette entries change.
	var cache_key = str(sprite.path) + ":enemy_rest"
	if not textures.has(cache_key):
		var image = _tex(str(sprite.path)).get_image()
		image.convert(Image.FORMAT_RGBA8)
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var color = image.get_pixel(x, y)
				if color.a <= 0.0 or color.r < 0.1: continue
				image.set_pixel(x, y, Color8(184, 124, 123) if color.r > 0.55 else Color8(118, 69, 72))
		textures[cache_key] = ImageTexture.create_from_image(image)
	var result = sprite.duplicate()
	result.path = cache_key
	return result

func _native_map_pose(sprite: Dictionary) -> int:
	var period=0
	for ticks in sprite.get("cycle_ticks",[]):period+=int(ticks)
	if period<=0:return 0
	var at=int(elapsed*60.0988)%period
	for i in range(sprite.native_cycle.size()):
		if at<int(sprite.cycle_ticks[i]):return int(sprite.native_cycle[i])
		at-=int(sprite.cycle_ticks[i])
	return 0

func _draw_unit_card(unit: Dictionary) -> void:
	var screen = _battle_cell_screen(game.cursor)
	var x = 120 if screen.x < 128 else 8
	var y = 8 if screen.y > 80 else 136
	var rect = Rect2(x, y, 128, 96)
	_panel(rect)
	_text(str(unit.name_zh), Vector2(x + 12, y + 14))
	var rank = "等级" + str(int(unit.level))
	if unit.side == "player":
		rank += " 经验" + str(int(unit.get("exp", 0)))
	_text(rank, Vector2(x + 12, y + 30))
	_text("生命" + str(int(unit.hp)) + "/" + str(int(unit.max_hp)), Vector2(x + 12, y + 46))
	_draw_health(int(unit.hp), int(unit.max_hp), Vector2(x + 12, y + 66), "ally" if unit.side == "player" else "enemy")

func _draw_preview() -> void:
	var attacker = game.find_unit(game.selected_id)
	var defender = game.find_unit(target_ids[target_index])
	var distance = absi(GameState.pos(attacker).x - GameState.pos(defender).x) + absi(GameState.pos(attacker).y - GameState.pos(defender).y)
	var reply = Rules.default_counter(defender, distance)
	# Map cursor belongs below every preview window, including its opaque fill.
	_draw_indicator("down", _battle_cell_screen(game.cursor) + Vector2(4, -4))
	attacker = attacker.duplicate(true)
	for unit in [attacker, reply]:
		if int(unit.get("character_id", 0)) == 167: unit.weapon_index = Rules.boss_weapon(unit, game.frame_counter)
	var rect = Rect2(8, 8, 240, 116)
	_panel(rect)
	for i in range(2):
		var unit = attacker.duplicate(true) if i == 0 else reply.duplicate(true)
		var other = reply if i == 0 else attacker
		unit.triangle_attack = Rules.combat_support(unit, other, game.living(str(unit.side)), distance)
		other = other.duplicate(true)
		other.story_invulnerable = Rules.boss_guard(other, game.turn)
		var stats = Rules.attack_stats(unit, other, game.terrain_avoid(GameState.pos(other)))
		var can_attack = Rules.can_attack(unit, distance)
		var blocked = Rules.attack_blocked(unit, other)
		var x = 20 + i * 112
		_text(str(unit.name_zh), Vector2(x, 28))
		_text("生命" + str(int(unit.hp)), Vector2(x, 44))
		_text("攻击无效" if blocked else ("伤害" + str(stats.damage) + " 命中" + str(stats.hit) + "%" if can_attack else "无法反击"), Vector2(x, 60))
		_text("不能造成伤害" if blocked else ("必杀" + str(stats.critical) + "%" if can_attack else "超出攻击范围"), Vector2(x, 76))
		_draw_health(int(unit.hp), int(unit.max_hp), Vector2(x, 94), "ally" if unit.side == "player" else "enemy")
	if target_ids.size() > 1:
		_draw_indicator("left", Vector2(120, 30))
		_draw_indicator("right", Vector2(228, 30))

func _draw_support_preview() -> void:
	_draw_indicator("down", _battle_cell_screen(game.cursor) + Vector2(4, -4))
	var rect = Rect2(16, 8, 224, 64)
	_panel(rect)
	var spell: Dictionary = Items.spell(chosen_spell)
	_center_text(str(spell.name_zh) + " 消耗生命" + str(Items.cost(chosen_spell)), Rect2(28, 20, 200, 16))
	var instruction = "选择传送目的地" if ui_mode == "warp" else "选择支援对象"
	if ui_mode == "warp":
		var target = game.find_unit(support_target)
		instruction = "传送" + str(target.get("name_zh", "")) + "至选定格"
	if ui_mode == "support_target" and not target_ids.is_empty():
		var target = game.find_unit(str(target_ids[target_index]))
		instruction = str(target.name_zh) + " " + str(int(target.hp)) + "/" + str(int(target.max_hp))
	_center_text(instruction, Rect2(28, 40, 200, 16))

func _draw_status(unit: Dictionary) -> void:
	if unit.is_empty():
		return
	var rect = Rect2(8, 16, 240, 208)
	_panel(rect)
	var members = _status_members()
	if members.size() > 1:
		_center_text("队伍 %d/%d" % [members.find(status_id) + 1, members.size()], Rect2(40, 27, 176, 10))
		_draw_indicator("left", Vector2(24, 28))
		_draw_indicator("right", Vector2(224, 28))
	var portrait = _portrait(int(unit.get("character_id", 0)))
	if has_method("_unit_portrait"):portrait=call("_unit_portrait",unit)
	if not portrait.is_empty():
		draw_texture(_tex(portrait.path), Vector2(24, 40))
	_text(str(unit.name_zh), Vector2(96, 40))
	_text("等级" + str(int(unit.level)) + " 经验" + str(int(unit.get("exp", 0))), Vector2(96, 56))
	_text("生命" + str(int(unit.hp)) + "/" + str(int(unit.max_hp)), Vector2(96, 72))
	_draw_health(int(unit.hp), int(unit.max_hp), Vector2(96, 88), "ally" if unit.get("side", "player") == "player" else "enemy")
	var stats = [["攻击", "strength"], ["技巧", "skill"], ["速度", "speed"], ["幸运", "luck"], ["防御", "defence"], ["移动", "move"]]
	var dying := game.is_dying(unit)
	var care_layout := unit.has("dying")
	for i in range(stats.size()):
		var row_y := 108+int(i/2)*24 if care_layout else 108+i*16
		var label_x := 32+104*(i%2) if care_layout else 32
		var value_x := 104+104*(i%2) if care_layout else 200
		if care_layout and has_method("_small_text"):
			call("_small_text",stats[i][0],Vector2(label_x,row_y+2))
		else:_text(stats[i][0], Vector2(label_x, row_y))
		_text(str(int(unit[stats[i][1]])), Vector2(value_x, row_y))
	var held = int(unit.get("item_id", 0))
	var footer = "装备：" + str(Items.item(held).get("name_zh", "")) if held > 0 else "未携带装备（职业默认）"
	if held <= 0 and unit.get("side", "player") == "enemy": footer = "未携带装备"
	if held > 0 and not Items.can_use(unit, held): footer += "（不适用）"
	if dying:
		_center_text("濒死 · 不可出阵",Rect2(24,181,208,16))
		_center_text("已救治过，无法再次救治" if int(unit.get("treatment_count",0))>0 else "可使用本队救治泉",Rect2(24,197,208,16))
		return
	if bool(unit.get("dead", false)):
		footer = "已阵亡"
	_center_text(footer, Rect2(24, 181 if care_layout else 201, 208, 16 if care_layout else 13))
	if care_layout and int(unit.get("treatment_count",0))>0:
		_center_text("已接受一次救治",Rect2(24,197,208,16))

func _draw_combat() -> void:
	draw_set_transform(_canvas_offset()+Vector2(combat_shake, 0))
	var attacker = game.find_unit(str(combat.attacker))
	var defender = game.find_unit(str(combat.defender))
	var player = attacker if attacker.side == "player" else defender
	var enemy = defender if attacker.side == "player" else attacker
	if graphics.has("battle_background"):
		draw_texture(_tex(graphics.battle_background.path), Vector2.ZERO)
	else:
		# Original outdoor metatiles supply the ground until the background program is decoded.
		var atlas = _tex("res://assets/original/graphics/maps/tileset.png")
		for x in range(16):
			draw_texture_rect_region(atlas, Rect2(x * 16, 128, 16, 16), Rect2(0, 48, 16, 16))
	battle_animation.draw_actors()
	# Source HUD includes Japanese labels and rules inside its colored texture.
	# Use the clean panel's fixed-size corners instead of stretching those pixels.
	for i in range(2):
		var unit = enemy if i == 0 else player
		var other = player if i == 0 else enemy
		var x = 12 + i * 128
		_panel(Rect2(i * 128, 128, 128, 112))
		safe_panels[-1] = Rect2(x, 138, 104, 92)
		_text(str(unit.name_zh), Vector2(x, 140))
		_text(("耐久" if unit.get("event_object",false) else "生命") + str(int(combat_hp.get(str(unit.id), unit.hp))), Vector2(x, 156))
		var stats = combat.get("stats", {}).get(str(unit.id), Rules.attack_stats(unit, other, game.terrain_avoid(GameState.pos(other))))
		var incoming = combat.get("stats", {}).get(str(other.id), Rules.attack_stats(other, unit, game.terrain_avoid(GameState.pos(unit))))
		var shown_defence = int(incoming.get("defender_defence", unit.defence))
		# Keep the original red/blue bitmap panel and replace embedded labels.
		var background = Color8(181, 49, 32) if i == 0 else Color8(21, 95, 217)
		draw_rect(Rect2(x - 4, 176, 112, 56), background)
		_draw_health(int(combat_hp.get(str(unit.id), unit.hp)), int(unit.max_hp), Vector2(x, 180), "enemy" if i == 0 else "ally")
		if bool(combat.get("support", false)):
			_text("支援魔法", Vector2(x, 202))
		elif bool(stats.get("blocked", false)):
			_text("攻击无效", Vector2(x, 202))
			_text("防御" + str(shown_defence), Vector2(x, 218))
		elif bool(stats.get("can_strike", game.can_attack(unit, other))):
			_text("命中" + str(stats.hit) + "%", Vector2(x, 202))
			_text("伤害" + str(stats.damage) + " 防御" + str(shown_defence), Vector2(x, 218))
		else:
			_text("无法反击", Vector2(x, 202))
			_text("防御" + str(shown_defence), Vector2(x, 218))
	if not combat_message.is_empty():
		_center_text(combat_message, Rect2(16, 24, 224, 24), Color.WHITE, false)
	draw_set_transform(_canvas_offset())

func _draw_reward() -> void:
	var unit = game.find_unit(str(reward.unit))
	var leveled = bool(reward.leveled)
	var rect = Rect2(24, 24, 208, 208) if leveled else Rect2(24, 52, 208, 160)
	_panel(rect)
	_center_text("等级提升" if leveled else "获得经验", Rect2(34, rect.position.y + 10, 188, 24))
	var level_before = int(reward.get("level_before", unit.level))
	var level_after = int(reward.get("level_after", unit.level))
	var name = str(unit.name_zh) + " 等级" + str(level_after)
	if leveled:
		name = str(unit.name_zh) + " 等级" + str(level_before) + "升至" + str(level_after)
	_text(name, Vector2(40, 70 if leveled else 94))
	var exp_before = int(reward.get("exp_before", 0))
	var exp_after = int(reward.get("exp_after", unit.get("exp", 0)))
	var exp_line = "经验" + str(exp_before) + " +" + str(int(reward.gain))
	if leveled:
		exp_line += " 剩余" + str(exp_after)
	_text(exp_line, Vector2(40, 88 if leveled else 116))
	var progress = 1.0 if instant_mode else clampf(reward_elapsed * 60.0 / maxf(1.0, float(reward.gain)), 0.0, 1.0)
	var displayed_exp = exp_before + int(roundf(float(reward.gain) * progress))
	if leveled and displayed_exp >= 100:
		displayed_exp -= 100
	_draw_exp_progress(displayed_exp, Vector2(40, 106 if leveled else 138), 168)
	if not leveled:
		_text("进度" + str(exp_after) + "/100", Vector2(40, 156))
		_center_text("确认可提前继续", Rect2(34, 180, 188, 16))
		return
	var labels = {"hp": "生命", "strength": "攻击", "skill": "技巧", "speed": "速度", "luck": "幸运", "defence": "防御"}
	var index = 0
	for stat in ["hp", "strength", "skill", "speed", "luck", "defence"]:
		_text(labels[stat], Vector2(40, 120 + index * 14))
		_text(str(int(unit.max_hp if stat == "hp" else unit[stat])), Vector2(160, 120 + index * 14))
		if int(reward.growths.get(stat, 0)) > 0:
			_text("+" + str(int(reward.growths[stat])), Vector2(192, 120 + index * 14), Color(0.8, 1, 0.8))
		index += 1
	_center_text("确认继续", Rect2(34, 206, 188, 16))

func _draw_exp_progress(value: int, at: Vector2, width: float) -> void:
	# Fifty discrete two-EXP cells. An odd point fills half the next cell.
	var start = at + Vector2(floorf((width - 150.0) / 2.0), 0)
	var filled = clampi(value, 0, 100)
	for index in range(50):
		var point = start + Vector2(index * 3, 0)
		var state = "filled" if filled >= (index + 1) * 2 else "empty"
		draw_texture_rect(_tex(health_ui.cells.ally[state].path), Rect2(point, Vector2(3, 8)), false)
		if filled == index * 2 + 1:
			draw_texture_rect_region(_tex(health_ui.cells.ally.filled.path), Rect2(point, Vector2(1, 8)), Rect2(0, 0, 1, 8))
	presentation_audit.exp_cells = {"count": 50, "points": filled, "bounds": Rect2(start, Vector2(150, 8))}

func _draw_health(hp: int, maximum: int, at: Vector2, side: String) -> void:
	var count = clampi(maximum, 1, 255)
	var filled = clampi(hp, 0, count)
	var columns = 52 if count > 52 else 26
	var cell_size = Vector2(2, 4) if count > 52 else Vector2(4, 8)
	var rows = ceili(float(count) / columns)
	var bounds = Rect2(at, Vector2(mini(count, columns), rows) * cell_size)
	if not safe_panels.is_empty() and not safe_panels[-1].encloses(bounds):
		layout_errors.append("HP cells outside content-safe rectangle")
	for index in range(count):
		var state = "filled" if index < filled else "empty"
		var position = at + Vector2(index % columns, index / columns) * cell_size
		draw_texture_rect(_tex(health_ui.cells[side][state].path), Rect2(position, cell_size), false)
	health_checks.append({"hp": filled, "maximum": count, "cells": count, "filled_cells": filled, "bounds": bounds})

func _draw_result() -> void:
	var rect = Rect2(24, 40, 208, 112)
	_panel(rect)
	_center_text("战斗胜利" if view == "victory" else "战斗失败", Rect2(34, 50, 188, 32))
	if view == "victory":
		var result_text = "敌军已投降" if game.flags.get("scenario_forced_victory", "") == "rudolf_surrender" else "已击败全部敌军"
		_center_text(str(game.battle_data.get("name_zh", game.catalog.stages.get(str(game.stage_id), {}).get("name_zh", "战场"))) + "\n" + result_text + "\n过关经验已结算", Rect2(34, 86, 188, 48))
	else:
		_center_text("主将倒下了", Rect2(34, 90, 188, 24))
	if menu_items.is_empty():
		_center_text("Z / ENTER", Rect2(32, 168, 192, 32), Color.WHITE, false)

func _menu_rect() -> Rect2:
	var max_width := 0.0
	for item in menu_items:
		max_width = maxf(max_width, _text_width(str(item)))
	var width = maxf(88, max_width + 40)
	var height = mini(10, menu_items.size()) * 16 + 28
	if menu_items.size() > 10:
		width = maxf(120, width)
		height += 16
	var at = menu_position
	at.x = clampf(at.x, 8, 248 - width)
	at.y = clampf(at.y, 8, 232 - height)
	return Rect2(at, Vector2(width, height))

func _menu_page_arrow_rect(step: int) -> Rect2:
	var rect = _menu_rect()
	var x = 10 if step < 0 else rect.size.x - 26
	return Rect2(rect.position + Vector2(x, rect.size.y - 28), Vector2(16, 18))

func _change_menu_page(step: int) -> void:
	var next_scroll = clampi(menu_scroll + step * 10, 0, maxi(0, menu_items.size() - 10))
	if next_scroll == menu_scroll: return
	var row = clampi(menu_selected - menu_scroll, 0, 9)
	menu_scroll = next_scroll
	menu_selected = mini(menu_scroll + row, menu_items.size() - 1)
	audio.play_sfx("menu_move")

func _menu_pointer_index(point: Vector2) -> int:
	if menu_items.is_empty(): return -1
	var rect = _menu_rect()
	if menu_items.size() > 10:
		for step in [-1, 1]:
			if _menu_page_arrow_rect(step).has_point(point):
				_change_menu_page(step)
				return -1
	# Only visible rows accept confirmation. Frame padding, page arrows and
	# the footer must never be interpreted as an unseen or clamped row.
	var rows = Rect2(rect.position + Vector2(10, 16), Vector2(rect.size.x - 20, mini(10, menu_items.size() - menu_scroll) * 16))
	if not rows.has_point(point): return -1
	return menu_scroll + int((point.y - rows.position.y) / 16)

func _draw_menu() -> void:
	var rect = _menu_rect()
	_panel(rect)
	for i in range(menu_scroll, mini(menu_scroll + 10, menu_items.size())):
		_text(str(menu_items[i]), rect.position + Vector2(28, 18 + (i - menu_scroll) * 16))
	_draw_menu_arrow(rect.position + Vector2(12, 20 + (menu_selected - menu_scroll) * 16))
	if menu_items.size() > 10:
		_center_text("%d至%d/%d" % [menu_scroll + 1, mini(menu_scroll + 10, menu_items.size()), menu_items.size()],
			Rect2(rect.position + Vector2(24, rect.size.y - 28), Vector2(rect.size.x - 48, 16)))
		if menu_scroll > 0: _draw_indicator("up", rect.position + Vector2(12, rect.size.y - 24))
		if menu_scroll + 10 < menu_items.size(): _draw_indicator("down", rect.position + Vector2(rect.size.x - 20, rect.size.y - 24))

func _draw_menu_arrow(at: Vector2) -> void:
	_draw_indicator("right", at + Vector2(0, int(sin(elapsed * 5.0))))

func _draw_indicator(direction: String, at: Vector2) -> void:
	draw_texture(_tex(cursors.arrows[direction].path), at.round())

func _exit_tree() -> void:
	if hub_controller != null:
		hub_controller.dispose()
	if battle_animation != null:
		battle_animation.reset()
		battle_animation = null
	if map_effects != null:
		map_effects.dispose()

func _resolve_pending_loot() -> void:
	var return_view = view
	var was_busy = busy
	while not game.flags.get("pending_loot", []).is_empty():
		if instant_mode and Inventory.resolve_loot(game, "store"): continue
		_show_loot_menu()
		while view in ["loot", "loot_confirm"]: await get_tree().process_frame
	_clear_menu()
	view = return_view
	busy = was_busy
	var notices: Array = game.flags.get("loot_notifications", [])
	if not notices.is_empty():
		var found=notices.filter(func(record):return record.get("kind","")!="death_storage")
		_notice("获得"+"、".join(found.map(func(record):return str(Items.item(int(record.item_id)).name_zh))) if not found.is_empty() else "濒死成员的装备已回本队行囊",3.0)
	game.flags.loot_notifications = []
	game.save_game()

func _show_loot_menu() -> void:
	view = "loot"
	var record: Dictionary = game.flags.pending_loot[0]
	if game.convoy.get(str(record.route), []).size() >= 40:
		_open_menu("loot", ["保留原物，丢弃新物", "换上新物，丢弃原物"], ["discard_new", "discard_old"], Vector2(24, 120))
	else:
		_open_menu("loot", ["新道具存入仓库", "换上新道具"], ["store", "new"], Vector2(40, 120))

func _loot_accept() -> void:
	var choice = str(menu_actions[menu_selected])
	if view == "loot_confirm":
		if choice == "cancel":
			_show_loot_menu()
			return
		choice = loot_choice
	elif choice.begins_with("discard"):
		loot_choice = choice
		view = "loot_confirm"
		_open_menu("loot", ["取消", "确认丢弃"], ["cancel", "confirm"], Vector2(64, 120))
		return
	if Inventory.resolve_loot(game, choice):
		_clear_menu()
		view = "battle"
		game.save_game()
	else:
		_show_loot_menu()
