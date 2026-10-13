class_name FeHubController
extends RefCounted
## Native town/dungeon walker and bank013 event VM. See data/hubs.json sources.
const Items = preload("res://core/item_rules.gd")
const Progression = preload("res://core/unit_progression.gd")
const DIRS := [Vector2i.ZERO, Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]
const TILE := 16.0
const STEP := 16.0 / 60.0988
var ui
var game
var room: Dictionary = {}
var actors: Dictionary = {}
var texts: Dictionary = {}
var facing := Vector2i.DOWN
var render_position := Vector2.ZERO
var motion_origin := Vector2.ZERO
var motion_target := Vector2.ZERO
var motion_left := 0.0
var motion_duration := STEP
var motion_actor := 1
var timer := 0.0
var clock := 0.0
var script_id := -1
var pc := 0
var program: Array = []
var script_actor := 1
var walking_steps := 0
var walking_ticks := 16
var pages: Array = []
var page_index := 0
var reveal := 0.0
var after_dialogue: Callable
var choices: Array = []
var choice_index := 0
var choice_title := ""
var after_choice: Callable
var on_choice_cancel: Callable
var menu_context := ""
var notice := ""
var notice_left := 0.0
var camera_override := Vector2(-1,-1)
var flash_left := 0.0
var shake_left := 0.0
var active_actor_variant := -1
var last_wander_tick := -1
var entry_guard := false
var portal_guard_position := Vector2i(-1,-1)

func _init(owner) -> void:
	ui = owner
	game = ui.game
	texts = game.read_json("res://data/dialogue_zh.json")

func enter_world() -> bool:
	game.hub_used["dungeon_visited"] = 0
	if not game.enter_world_hub():
		return false
	var entry: Dictionary = game.world_hub_entry()
	facing = DIRS[clampi(int(entry.get("facing",3)),1,4)]
	_setup(true)
	return true

func enter(id: int, position: Vector2i) -> bool:
	if not game.enter_hub(id, position):
		return false
	_setup(true)
	return true

func resume() -> void:
	var saved_facing: Array = game.hub_used.get("leader_facing",[0,1])
	facing = Vector2i(int(saved_facing[0]),int(saved_facing[1]))
	_setup(false)
	var vm: Dictionary = game.hub_used.get("event_vm", {})
	if not vm.is_empty() and int(vm.get("hub_id",0)) == game.hub_id:
		script_id = int(vm.script_id)
		program = game.hubs.scripts.get(str(script_id), {}).get("instructions", [])
		pc = int(vm.pc)
		for key in vm.get("actors", {}):
			actors[int(key)] = vm.actors[key].duplicate(true)
		_run()

func _setup(check_entry: bool) -> void:
	room = game.hub_room()
	_apply_feature_states()
	actors.clear()
	active_actor_variant = -1
	_refresh_actors()
	script_id = -1
	program = []
	pc = 0
	pages = []
	choices = []
	after_dialogue = Callable()
	after_choice = Callable()
	on_choice_cancel = Callable()
	motion_left = 0
	walking_steps = 0
	timer = 0
	camera_override = Vector2(-1,-1)
	ui.busy = false
	ui.menu_items.clear()
	ui.view = "hub"
	game.mode = "hub"
	# Internal portals can still use source boundary shorthand coordinates.
	if not check_entry and game.hub_used.get("event_vm", {}).is_empty():
		game.hub_position = _recover_closed_gate_exterior(game.hub_position)
	game.hub_position = _entry_position(game.hub_position)
	render_position = Vector2(game.hub_position) * TILE
	portal_guard_position = game.hub_position
	ui.audio.play_hub(game.hub_id)
	if check_entry:
		game.hub_used.erase("event_vm")
		_check_room_encounter()
		if ui.view == "hub":
			_check_cell()

func _recover_closed_gate_exterior(at: Vector2i) -> Vector2i:
	# Older world-entry decoding interpreted a conditional-entry selector as
	# a coordinate. Recover only the resulting isolated, closed gate exterior;
	# ordinary room positions, open gates and resumable source scripts stay put.
	if not _ground(at):
		return at
	if game.hub_id == 9 and at.x >= 0 and at.x < 9:
		if at.y <= 1 and _tile(Vector2i(3,1)) == 207:
			return Vector2i(3,12)
		if at.y >= 13 and _tile(Vector2i(3,13)) == 207:
			return Vector2i(3,3)
	if game.hub_id == 15 and at.y <= 1 and not _ground(Vector2i(11,1)):
		return Vector2i(11,19)
	return at

func _entry_position(at: Vector2i) -> Vector2i:
	var p := at
	p.x = clampi(p.x,0,int(room.width)-1)
	p.y = clampi(p.y,0,int(room.height)-1)
	if _ground(p):
		return p
	# Source gates may place the camera-side coordinate at0. Walkable cells
	# on the same entrance row/column are used; never relocate story actors.
	var best := p
	var distance := 99999
	for y in range(int(room.height)):
		for x in range(int(room.width)):
			var cell := Vector2i(x,y)
			if _ground(cell) and _actor_at(cell) == 0:
				var d := absi(x-p.x)+absi(y-p.y)
				if d < distance:
					distance = d
					best = cell
	return best

func _refresh_actors() -> void:
	var state: Dictionary = game.hub_flags.get(str(game.hub_id), {})
	var variant := 1 if int(state.get("actors",0)) & 128 else 0
	var fresh: Array = game.hub_actors()
	var present: Array[int] = []
	for actor in fresh:
		var id := int(actor.actor_id)
		present.append(id)
		if not actors.has(id) or variant != active_actor_variant:
			actors[id] = actor.duplicate(true)
			actors[id].facing = _initial_facing(int(actor.movement_flags))
			actors[id].hidden = false
	for id in actors:
		if (int(state.get("actors",0)) & (1 << (int(id)-2))) or (not present.has(int(id)) and not bool(actors[id].get("spawned",false))):
			actors[id].hidden = true
	active_actor_variant = variant

func process(delta: float) -> void:
	clock += delta
	reveal += delta * 28
	notice_left = maxf(0,notice_left-delta)
	flash_left = maxf(0,flash_left-delta)
	shake_left = maxf(0,shake_left-delta)
	if motion_left > 0:
		motion_left = maxf(0,motion_left-delta)
		var location := motion_origin.lerp(motion_target,1.0-motion_left/motion_duration)
		if motion_actor == 1:
			render_position = location
		else:
			actors[motion_actor].render_position = [location.x,location.y]
		if motion_left == 0:
			_motion_done()
	if timer > 0:
		timer = maxf(0,timer-delta)
		if timer == 0:
			_run()
	if ui.view == "hub" and script_id < 0 and motion_left == 0 and not entry_guard:
		if ui.held_direction != Vector2i.ZERO:
			direction(ui.held_direction)
		else:
			_wander()

func direction(dir: Vector2i) -> void:
	if ui.view == "hub_choice":
		if not choices.is_empty():
			choice_index = posmod(choice_index + (dir.y if dir.y else dir.x),choices.size())
			ui.audio.play_sfx("menu_move")
		return
	if ui.view != "hub" or script_id >= 0 or motion_left > 0:
		return
	facing = dir
	game.hub_used.leader_facing = [dir.x,dir.y]
	var next: Vector2i = game.hub_position + dir
	if next.x <= 0 or next.y <= 0 or next.x >= int(room.width)-1 or next.y >= int(room.height)-1:
		if _inside(next) and not _ground(next):
			return
		_cross_edge(dir)
		return
	if _actor_at(next) > 0:
		return
	if _ground(next):
		_start_motion(1,next,STEP)
	elif _door(next):
		_open_door(next)

func accept() -> void:
	if ui.view == "hub_dialogue":
		if pages.is_empty():
			return
		var text: String = str(pages[page_index].text)
		if reveal < text.length():
			reveal = text.length()
			return
		page_index += 1
		reveal = 0
		ui.audio.play_sfx("dialogue")
		if page_index >= pages.size():
			pages.clear()
			ui.view = "hub"
			var done := after_dialogue
			after_dialogue = Callable()
			if done.is_valid():
				done.call()
		return
	if ui.view == "hub_choice":
		if choices.is_empty():
			return
		var selected: Dictionary = choices[choice_index]
		if not bool(selected.get("enabled",true)):
			ui.audio.play_sfx("menu_cancel")
			return
		var done := after_choice
		after_choice = Callable()
		on_choice_cancel = Callable()
		choices = []
		ui.view = "hub"
		ui.audio.play_sfx("menu_confirm")
		if done.is_valid():
			done.call(selected.get("value",choice_index))
		return
	if ui.view != "hub" or script_id >= 0 or motion_left > 0:
		return
	var front: Vector2i = game.hub_position + facing
	var actor := _actor_at(front)
	# Original96..101 counters/windows allow talking straight across one
	# intervening tile, still strictly in the direction the leader faces.
	if actor == 0 and _tile(front) >= 96 and _tile(front) < 102:
		actor = _actor_at(front+facing)
	if actor > 0:
		_talk(actor)
		return
	if _feature(front):
		return
	if _door(front):
		_open_door(front)
		return
	open_system_menu()

func cancel() -> void:
	if ui.view == "hub_dialogue":
		accept()
	elif ui.view == "hub_choice":
		var callback := on_choice_cancel
		after_choice = Callable()
		on_choice_cancel = Callable()
		choices.clear()
		ui.view = "hub"
		ui.audio.play_sfx("menu_cancel")
		if callback.is_valid():
			callback.call()
	elif ui.view == "hub" and script_id < 0:
		open_system_menu()

func _start_motion(actor: int, destination: Vector2i, seconds: float) -> void:
	motion_actor = actor
	motion_origin = Vector2(game.hub_position if actor == 1 else _position(actors[actor])) * TILE
	motion_target = Vector2(destination) * TILE
	motion_duration = maxf(0.001,seconds)
	motion_left = 0 if ui.instant_mode else motion_duration
	if actor == 1:
		# A reciprocal portal must be suppressed only until the leader steps
		# away from its landing. Keeping this coordinate for the whole visit
		# permanently disabled the way back (e.g. rooms25/26 and31/97).
		if destination != portal_guard_position:
			portal_guard_position = Vector2i(-1,-1)
		game.hub_position = destination
		if ui.instant_mode:
			render_position = motion_target
	else:
		actors[actor].position = [destination.x,destination.y]
		actors[actor].render_position = [motion_origin.x,motion_origin.y]
	if ui.instant_mode:
		_motion_done()

func _motion_done() -> void:
	if motion_actor > 1 and actors.has(motion_actor):
		actors[motion_actor].erase("render_position")
	if walking_steps > 0:
		walking_steps -= 1
		if walking_steps > 0:
			_walk_script_step()
		else:
			_run()
	elif script_id >= 0:
		_run()
	else:
		_check_cell()

func _check_cell() -> void:
	if entry_guard or ui.view != "hub":
		return
	var at: Vector2i = game.hub_position
	for portal in room.get("portals",[]):
		if _position(portal) == at and at != portal_guard_position:
			enter(int(portal.destination),Vector2i(portal.spawn[0],portal.spawn[1]))
			return
	var tile := _tile(at)
	if at != portal_guard_position and tile >= 232 and (int(game.hubs.tile_actions[tile-232]) >> 4) == 5:
		_leave_world(15 if game.hub_id == 9 else 9)
		return
	var id: int = game.hub_script(0,at)
	if id >= 0:
		_start_script(id)

func _check_room_encounter() -> void:
	var encounter: Dictionary = game.hubs.get("room_encounters",{}).get(str(game.hub_id),{})
	if encounter.is_empty():
		return
	var bit := int(encounter.visited_bit)
	if int(game.hub_used.get("dungeon_visited",0)) & bit:
		return
	game.hub_used.dungeon_visited = int(game.hub_used.get("dungeon_visited",0)) | bit
	if game.enter_dungeon_battle(int(encounter.encounter)):
		ui._begin_existing_battle()

func _cross_edge(dir: Vector2i) -> void:
	var side := 0 if dir == Vector2i.UP else 1 if dir == Vector2i.DOWN else 2 if dir == Vector2i.LEFT else 3
	var edges: Array = room.get("edges",[0,0,0,0])
	var destination := int(edges[side])
	if destination == 0:
		return
	if destination >= 50:
		var next_room: Dictionary = game.hubs.rooms.get(str(destination-50),{})
		if next_room.is_empty():
			return
		var spawn: Vector2i = game.hub_position
		if side == 0: spawn.y = int(next_room.height)-2
		elif side == 1: spawn.y = 1
		elif side == 2: spawn.x = int(next_room.width)-2
		else: spawn.x = 1
		enter(destination-50,spawn)
		return
	if destination == 43 and game.chapter < 4:
		_message("水位尚未下降，无法向北通行。")
		return
	_choose("离开这里？",[{"label":"离开","value":destination},{"label":"留下","value":0}],func(value):
		if int(value) > 0:
			_leave_world(int(value)))

func _leave_world(destination: int = 0) -> void:
	if destination > 0:
		game.previous_world_node = game.world_node
		game.world_node = destination
		game.route_positions[game.route] = destination
	game.remember_world_approach()
	game.mode = "world"
	game.hub_used.erase("event_vm")
	ui.view = "world"
	ui.busy = false
	ui.audio.play_world(game.chapter)
	game.save_game()

func _talk(actor: int) -> void:
	actors[actor].facing = DIRS.find(-facing)
	var id: int = game.hub_script(actor)
	if id >= 0:
		if id == 35:
			# The source relocates Mycen when Lukas is first approached;
			# his normal report remains the conversation of that interaction.
			_dialogue(2,func(): _start_script(id))
		else:
			_start_script(id)
		return
	var rows: Array = room.get("npc_dialogues",[])
	var index := actor-2
	if index < 0 or index >= rows.size():
		return
	var state: Dictionary = game.hub_flags.get(str(game.hub_id),{})
	var variant := 1 if int(state.get("talk",0)) & (1 << index) else 0
	var text_id := int(rows[index][variant])
	if text_id == 255:
		return
	_dialogue(text_id,func():
		var flag := int(actors[actor].get("interaction_flags",0))
		if flag:
			game.apply_hub_flag(flag)
			_refresh_actors()
		game.save_game())

func _start_script(id: int) -> void:
	script_id = id
	program = game.hubs.scripts.get(str(id),{}).get("instructions",[])
	pc = 0
	_run()

func _run() -> void:
	if script_id < 0 or ui.view != "hub" or timer > 0 or motion_left > 0 or walking_steps > 0:
		return
	var safety := 0
	while pc < program.size() and safety < 512:
		safety += 1
		var op: Dictionary = program[pc]
		pc += 1
		script_actor = int(op.actor)
		match str(op.kind):
			"wait":
				if not ui.instant_mode:
					timer = float(op.ticks)/60.0988
					return
			"face":
				if script_actor == 1: facing = DIRS[clampi(int(op.direction),1,4)]
				elif actors.has(script_actor): actors[script_actor].facing = int(op.direction)
			"walk":
				walking_steps = int(op.steps)
				walking_ticks = int(op.ticks_per_tile)
				if script_actor != 1 and not actors.has(script_actor): walking_steps = 0
				if walking_steps > 0:
					_walk_script_step()
					return
			"dialogue":
				_checkpoint(pc-1)
				_dialogue(int(op.dialogue_id),_run)
				return
			"recruit":
				var id := _character_key(int(op.character_id))
				if not id.is_empty():
					game.recruit(id)
					_notice(_unit_name(id)+"加入了队伍")
					ui.audio.play_sfx("menu_confirm")
			"flag":
				game.apply_hub_flag(int(op.flag_id))
				_refresh_actors()
			"actor_sprite":
				if actors.has(script_actor):
					actors[script_actor].sprite_id = int(op.sprite_id)
					actors[script_actor].hidden = int(op.sprite_id) == 0
			"spawn_actor":
				var template: Dictionary = game.hubs.get("spawn_templates",{}).get(str(int(op.template)),{})
				if not template.is_empty():
					actors[script_actor] = template.duplicate(true)
					actors[script_actor].actor_id = script_actor
					actors[script_actor].facing = _initial_facing(int(template.movement_flags))
					actors[script_actor].spawned = true
			"audio":
				ui.audio.play_request(int(op.sound_id))
			"camera":
				camera_override = Vector2(op.position[0],op.position[1])*TILE
			"choice":
				_checkpoint(pc)
				_choose("第%d章 · 记录进度" % int(op.choice_id),[{"label":"记录","value":1},{"label":"继续","value":0}],func(value):
					if int(value) == 1: game.save_game()
					_run(),_run)
				return
			"item_give":
				_courier()
				return
			"special":
				if _special(int(op.effect)):
					return
			"chapter_transition":
				_finish_script()
				if game.next_chapter(int(op.transition)):
					ui._show_campaign_chapter()
				return
	_finish_script()

func _walk_script_step() -> void:
	var dir: Vector2i = facing if script_actor == 1 else DIRS[clampi(int(actors[script_actor].get("facing",3)),1,4)]
	var at: Vector2i = game.hub_position if script_actor == 1 else _position(actors[script_actor])
	_start_motion(script_actor,at+dir,float(walking_ticks)/60.0988)

func _finish_script() -> void:
	script_id = -1
	program = []
	walking_steps = 0
	game.hub_used.erase("event_vm")
	camera_override = Vector2(-1,-1)
	game.save_game()

func _abort_script() -> void:
	_finish_script()
	ui.view = "hub"

func _checkpoint(at_pc: int) -> void:
	game.hub_used.event_vm = {"script_id":script_id,"pc":at_pc,"hub_id":game.hub_id,"actors":actors.duplicate(true)}
	game.save_game()

func _special(effect: int) -> bool:
	match effect:
		0: flash_left = 8.0/60.0988
		1:
			game.flags["sluice_animation_"+str(game.hub_id)] = true
			# Original sluice graphics use L0D9A1A's four water/gate columns.
			for y in range(1,4):
				for x in range(7,10): _set_tile(Vector2i(x,y),0)
			# L0CAB0B persists feature bit0 at the end of the gate animation.
			if not room.get("features",[]).is_empty() and int(room.features[0].kind) == 3:
				_use_feature(0)
			shake_left = 0.5
		2:
			game.flags.celica_promoted = true
			if game.roster.has("celica"):
				game.roster.celica.level = 1
				game.roster.celica.promoted = true
		3: shake_left = 160.0/60.0988
		4:
			game.flags.celica_captive = true
			game.remember_world_approach()
			game.parties[game.route] = game.party.duplicate()
			game.route = "alm"
			game.party = game.parties.alm.duplicate()
			game.world_node = int(game.route_positions.alm)
			game.restore_world_approach()
			_finish_script()
			_leave_world()
			return true
		5,8:
			if effect == 8: game.flags.scenario_final_merge_ready = true
			_finish_script()
			if game.enter_dungeon_battle(22):
				ui._begin_existing_battle()
			return true
		6:
			var health: Dictionary = {}
			for id in game.parties.get("celica",[]):
				health[id] = int(game.roster[id].get("hp",game.roster[id].max_hp))
			game.flags.celica_captive_hp = health
		7:
			game.flags.celica_captive = true
			_stamp_pattern(Vector2i(0,5),7)
		9:
			# Halcyon's source promotion targets Alm even while Celica leads.
			if game.roster.has("alm"):
				var changed: Dictionary = Progression.promote(game.roster.alm,23,true)
				if changed.valid:
					game.roster.alm = changed.unit
					game.flags.alm_promoted = true
		10: flash_left = 64.0/60.0988
	if not ui.instant_mode and effect in [0,1,3,7,10]:
		timer = 0.35 if effect != 3 else 160.0/60.0988
		return true
	return false

func _feature(at: Vector2i) -> bool:
	for i in range(room.get("features",[]).size()):
		var feature: Dictionary = room.features[i]
		if _position(feature) != at:
			continue
		var key := "%d:%d" % [game.hub_id,i]
		if bool(game.hub_used.get(key,false)):
			return false
		match int(feature.kind):
			0: _take_item(feature,i)
			1: _spring(feature,i)
			2: _dialogue(int(feature.value))
			_: return false
		return true
	var tile := _tile(at)
	if tile >= 232:
		var low := int(game.hubs.tile_actions[tile-232]) & 15
		if low == 6:
			_shrine()
			return true
	return false

func _take_item(feature: Dictionary, feature_index: int) -> void:
	var available := false
	for id in game.party:
		if not bool(game.roster[id].get("dead",false)) and int(game.roster[id].get("item_id",0)) == 0:
			available = true
	if not available:
		_set_tile(_position(feature),235)
		_message("大家都已携带道具。请先整理行囊，再来取走。")
		return
	var item_id := int(feature.value)
	game.give_item(item_id)
	_use_feature(feature_index)
	# Dragon shrine original mutually exclusive silver/holy shield pair.
	if game.hub_id == 48 and feature_index in [1,2]:
		_use_feature(1)
		_use_feature(2)
	ui.audio.play_sfx("menu_confirm")
	_message("获得了"+str(Items.item(item_id).get("name_zh","道具"))+"。")
	game.save_game()

func _use_feature(index: int) -> void:
	var feature: Dictionary = room.features[index]
	game.hub_used["%d:%d" % [game.hub_id,index]] = true
	_stamp_pattern(_position(feature),int(feature.kind))

func _apply_feature_states() -> void:
	# L0D8C59/L0D8C86: the third feature byte selects a tile pattern,
	# not an interaction opcode. Chapter flags change ports/statues/gates
	# even when no player interaction consumed the feature in this session.
	var original: Dictionary = game.hubs.rooms.get(str(game.hub_id),{})
	for i in range(room.get("features",[]).size()):
		var feature: Dictionary = room.features[i]
		var used := bool(game.hub_used.get("%d:%d" % [game.hub_id,i],false))
		if used:
			_stamp_pattern(_position(feature),int(feature.kind))
		elif int(feature.kind) in [3,4,6]:
			# Some chapter transitions clear a bit (e.g. Sofia north gate).
			# Restore only that pattern footprint from the original room.
			var pattern: Array = game.hubs.tile_change_patterns.get(str(int(feature.kind)),[])
			for j in range(pattern.size()):
				var at := _position(feature)+Vector2i(int(j/4),j%4)
				if _inside(at): _set_tile(at,int(original.tiles[at.y*int(original.width)+at.x]))

func _spring(feature: Dictionary, feature_index: int) -> void:
	var id := int(feature.value)
	var pool := id >> 1
	var pool_key := "spring_"+str(pool)
	var initial: Array = game.hubs.spring_initial_uses
	var remaining := int(game.hub_used.get(pool_key,initial[pool] if pool < initial.size() else 3))
	if remaining <= 0:
		_message("泉水已经干涸了。")
		return
	var effect := int(game.hubs.spring_effects[id])
	var labels := ["防御","力量","幸运","速度","技巧","最大生命","经验","复活"]
	var candidates: Array = []
	for key in game.roster:
		var unit: Dictionary = game.roster[key]
		var dead := bool(unit.get("dead",false))
		if (effect == 7 and dead) or (effect != 7 and not dead and game.party.has(key)):
			candidates.append({"label":_unit_name(key),"value":key})
	if candidates.is_empty():
		_message("没有能够接受泉水祝福的人。")
		return
	_choose(labels[effect]+"之泉 · 剩余"+str(remaining)+"次",candidates,func(key):
		var unit: Dictionary = game.roster[key]
		var changed := false
		if effect == 7:
			unit.dead = false
			unit.hp = int(unit.max_hp)
			unit.exp = 0
			unit.item_id = 0
			if not game.party.has(key):
				game.party.append(key)
				game.parties[game.route] = game.party.duplicate()
			for army in game.parties:
				if army != game.route: game.parties[army].erase(key)
			changed = true
		elif effect == 6:
			changed = int(unit.get("exp",0)) < 99
			unit.exp = 99
		else:
			var stats := ["defence","strength","luck","speed","skill","max_hp"]
			var stat: String = stats[effect]
			var maximum := 52 if effect == 5 else 40
			var before := int(unit.get(stat,0))
			unit[stat] = mini(maximum,before+1)
			changed = int(unit[stat]) > before
			if effect == 5 and changed: unit.hp = mini(int(unit.max_hp),int(unit.hp)+1)
		# Original charges a use even when the selected stat is capped.
		game.hub_used[pool_key] = remaining-1
		if remaining == 1:
			for i in range(room.features.size()):
				if int(room.features[i].kind) == 1 and (int(room.features[i].value) >> 1) == pool: _use_feature(i)
		game.save_game()
		_message(_unit_name(str(key))+("获得了泉水的祝福。" if changed else "已经达到成长上限。")))

func _shrine() -> void:
	var candidates: Array = []
	for id in game.party:
		var unit: Dictionary = game.roster[id]
		if not bool(unit.get("dead",false)) and not Progression.promotion_options(unit).is_empty():
			candidates.append({"label":_unit_name(id),"value":id})
	if candidates.is_empty():
		_message("女神米拉守护着这里。队伍中暂时没有达到转职条件的人。")
		return
	_choose("选择接受转职的人",candidates,func(id):
		var options: Array = []
		for option in Progression.promotion_options(game.roster[id]):
			var cid := int(option.class_id)
			options.append({"label":str(game.catalog.classes[str(cid)].get("name_zh",game.catalog.classes[str(cid)].get("player_name_zh","职业"))),"value":cid})
		_choose(_unit_name(str(id))+" · 转职",options,func(cid):
			var result: Dictionary = game.promote_unit(str(id),int(cid))
			if bool(result.get("valid",false)):
				game.save_game()
				ui.audio.play_jingle("levelup")
				_message(_unit_name(str(id))+"完成了转职。")))

func _courier() -> void:
	var options: Array = []
	for id in game.party:
		var item_id := int(game.roster[id].get("item_id",0))
		if item_id and not bool(game.roster[id].get("dead",false)):
			options.append({"label":_unit_name(id)+" · "+str(Items.item(item_id).name_zh),"value":id})
	if options.is_empty():
		_message("没有能够托运的道具。",_abort_script)
		return
	_choose("托运给另一支队伍",options,func(id):
		var item_id := int(game.roster[id].item_id)
		var other := "alm" if game.route == "celica" else "celica"
		if game.convoy[other].size() >= 40:
			_message("对方的行囊已满，无法托运。",_abort_script)
			return
		game.roster[id].item_id = 0
		game.convoy[other].append(item_id)
		_message(str(Items.item(item_id).name_zh)+"已送交另一支队伍的行囊。",_run),_abort_script)

func _sail() -> void:
	var destination := 15 if game.hub_id == 9 else 9
	_choose("乘船出发？",[{"label":"出发","value":1},{"label":"留下","value":0}],func(value):
		if int(value): _leave_world(destination))

func open_system_menu() -> void:
	if ui.view != "hub" or script_id >= 0 or motion_left > 0:
		return
	_choose("队伍",[{"label":"查看人物","value":"status"},{"label":"交换道具","value":"exchange"},{"label":"整理行囊","value":"convoy"},{"label":"记录进度","value":"save"},{"label":"继续探索","value":"close"}],func(value):
		match str(value):
			"status": open_status()
			"exchange": _exchange_first()
			"convoy": _convoy_menu()
			"save":
				_message("进度已经记录。" if game.save_game() else "保存失败，请重试。")
		return)

func open_status() -> void:
	# Dialogue/choice callbacks and movement retain input until they finish.
	# Replacing them with a shortcut menu can strand the active source VM.
	if ui.view != "hub" or script_id >= 0 or motion_left > 0:
		return
	var options: Array = []
	for id in game.party:
		if not bool(game.roster[id].get("dead",false)):
			options.append({"label":_unit_name(id),"value":id})
	_choose("查看人物",options,func(id):
		var u: Dictionary = game.roster[id]
		var cls: Dictionary = game.catalog.classes.get(str(int(u.class_id)),{})
		var equipment := str(Items.item(int(u.get("item_id",0))).get("name_zh","无")) if int(u.get("item_id",0)) else "无"
		_message("%s  %s\n等级%d  经验%d\n生命%d/%d\n力量%d 技巧%d 速度%d\n幸运%d 防御%d 抗性%d\n携带：%s" % [_unit_name(id),str(cls.get("player_name_zh",cls.get("name_zh",""))),int(u.level),int(u.exp),int(u.hp),int(u.max_hp),int(u.strength),int(u.skill),int(u.speed),int(u.luck),int(u.defence),int(u.get("resistance",0)),equipment],Callable(),int(u.character_id)))

func _exchange_first() -> void:
	var options: Array = []
	for id in game.party:
		if not bool(game.roster[id].get("dead",false)): options.append({"label":_unit_name(id),"value":id})
	_choose("交换道具：选择第一人",options,func(first):
		var others: Array = []
		for id in game.party:
			if id != first and not bool(game.roster[id].get("dead",false)): others.append({"label":_unit_name(id),"value":id})
		_choose("选择交换对象",others,func(second):
			if game.exchange_items(str(first),str(second)):
				game.save_game()
				_message("两人的道具已经交换。")))

func _convoy_menu() -> void:
	_choose("整理行囊",[{"label":"取出道具","value":"take"},{"label":"存入道具","value":"put"}],func(value):
		if str(value) == "put":
			var options: Array = []
			for id in game.party:
				var item_id := int(game.roster[id].get("item_id",0))
				if item_id: options.append({"label":_unit_name(id)+" · "+str(Items.item(item_id).name_zh),"value":id})
			_choose("存入道具",options,func(id):
				if game.convoy[game.route].size() >= 40:
					_message("行囊已满，无法存入。")
					return
				game.convoy[game.route].append(int(game.roster[id].item_id))
				game.roster[id].item_id = 0
				game.save_game())
		else:
			var options: Array = []
			for i in range(game.convoy[game.route].size()):
				options.append({"label":str(Items.item(int(game.convoy[game.route][i])).name_zh),"value":i})
			_choose("选择取出的道具",options,func(index):
				var people: Array = []
				for id in game.party:
					if not bool(game.roster[id].get("dead",false)) and int(game.roster[id].get("item_id",0)) == 0: people.append({"label":_unit_name(id),"value":id})
				_choose("交给谁？",people,func(id):
					game.roster[id].item_id = int(game.convoy[game.route][int(index)])
					game.convoy[game.route].remove_at(int(index))
					game.save_game())))

func _dialogue(id: int, done: Callable = Callable()) -> void:
	var source: Array = game.hubs.dialogues.get(str(id),{}).get("pages",[])
	var translated: Array = texts.get(str(id),[])
	pages = []
	for i in range(mini(source.size(),translated.size())):
		_append_pages(str(translated[i]),int(source[i].get("face_id",0)),int(source[i].get("speaker_id",0)))
	if pages.is_empty():
		if done.is_valid(): done.call()
		return
	page_index = 0
	reveal = 0
	after_dialogue = done
	ui.view = "hub_dialogue"

func _message(text: String, done: Callable = Callable(), face: int = 0) -> void:
	pages = []
	_append_pages(text,face,face)
	page_index = 0
	reveal = 0
	after_dialogue = done
	ui.view = "hub_dialogue"

func _append_pages(text: String, face: int, speaker: int) -> void:
	var with_face: bool = face > 0 and ui.graphics.character_portraits.has(str(face))
	var lines: Array[String] = ui._wrapped_lines(text,156.0 if with_face else 216.0)
	var limit := 3 if with_face else 4
	for offset in range(0,lines.size(),limit):
		pages.append({"text":"\n".join(lines.slice(offset,mini(offset+limit,lines.size()))),"face":face,"speaker":speaker,"portrait":with_face})

func _choose(title: String, options: Array, done: Callable, cancelled: Callable = Callable()) -> void:
	if options.is_empty():
		_message("没有可选择的对象。",cancelled)
		return
	choice_title = title
	choices = options
	choice_index = 0
	after_choice = done
	on_choice_cancel = cancelled
	ui.view = "hub_choice"

func draw() -> void:
	if room.is_empty():
		return
	var origin := -_camera()
	if shake_left > 0: origin.x += 1 if int(clock*60)&1 else -1
	ui._draw_map(game.hub_room(),ui._tex("res://assets/original/graphics/maps/buildings.png"),origin)
	for id in actors:
		var actor: Dictionary = actors[id]
		if bool(actor.get("hidden",false)) or int(actor.get("sprite_id",0)) == 0: continue
		var at := Vector2(_position(actor))*TILE
		if actor.has("render_position"): at = Vector2(actor.render_position[0],actor.render_position[1])
		_draw_actor(int(actor.sprite_id),at+origin,DIRS[clampi(int(actor.get("facing",3)),1,4)],motion_left>0 and motion_actor==int(id))
	_draw_actor(2 if game.route=="celica" else 1,render_position+origin,facing,motion_left>0 and motion_actor==1)
	if flash_left > 0 and (int(clock*60)&3)<2:
		ui.draw_rect(Rect2(0,0,256,240),Color(1,1,1,0.3))
	if ui.view == "hub_dialogue" and not pages.is_empty():
		var page: Dictionary = pages[page_index]
		ui._panel(Rect2(8,128,240,104))
		var shown := str(page.text).left(int(reveal))
		if bool(page.portrait):
			var index := str(_portrait_index(int(page.face)))
			var portrait: Dictionary = ui.graphics.portraits_by_index.get(index,{})
			if not portrait.is_empty(): ui.draw_texture(ui._tex(portrait.path),Vector2(20,164))
			var name := _display_name(int(page.speaker))
			if name.is_empty(): name = _display_name(int(page.face))
			ui._center_text(name,Rect2(20,140,216,16))
			ui._text(shown,Vector2(80,164))
		else:
			ui._text(shown,Vector2(20,146))
		if reveal >= str(page.text).length() and fmod(clock,0.8)<0.5: ui._draw_indicator("down",Vector2(228,216))
	elif ui.view == "hub_choice":
		_draw_choices()
	elif notice_left > 0:
		ui._panel(Rect2(8,8,240,40))
		ui._center_text(notice,Rect2(20,20,216,16))

func mouse_accept(point: Vector2) -> void:
	if ui.view != "hub_choice":
		accept()
		return
	if point.y >= 198 and point.y < 228:
		if point.x < 36: direction(Vector2i.LEFT)
		elif point.x > 220: direction(Vector2i.RIGHT)
		return
	var row := int(floor((point.y - 68.0) / 26.0))
	if point.x < 20 or point.x >= 236 or row < 0 or row >= 5:
		return
	var selected := int(choice_index / 5) * 5 + row
	if selected >= choices.size(): return
	choice_index = selected
	accept()

func _draw_choices() -> void:
	ui._panel(Rect2(8,16,240,216))
	var title_lines: Array[String] = ui._wrapped_lines(choice_title,208)
	for i in range(mini(2,title_lines.size())): ui._center_text(title_lines[i],Rect2(24,30+i*16,208,16))
	var page := int(choice_index/5)
	var start := page*5
	for i in range(start,mini(start+5,choices.size())):
		var row := i-start
		var label := str(choices[i].label)
		var lines: Array[String] = ui._wrapped_lines(label,188)
		var y := 72.0+row*26
		if lines.size() > 1:
			ui._text(lines[0],Vector2(40,y-4))
			ui._text(lines[1],Vector2(40,y+9))
		else: ui._center_text(label,Rect2(40,y,188,16))
		if i == choice_index: ui._draw_indicator("right",Vector2(24,y+4))
	ui._center_text("%d / %d" % [page+1,int(ceil(choices.size()/5.0))],Rect2(32,206,192,14),Color(0.7,0.7,0.7))
	if page>0:ui._draw_indicator("left",Vector2(20,210))
	if start+5<choices.size():ui._draw_indicator("right",Vector2(228,210))

func _draw_actor(sprite_id: int, at: Vector2, dir: Vector2i, walking: bool) -> void:
	var sprite: Dictionary = ui.graphics.village_sprites.get(str(sprite_id),{})
	if sprite.is_empty() or at.x < -32 or at.x > 288 or at.y < -32 or at.y > 272:return
	var direction_key := "up" if dir.y<0 else "side" if dir.x else "down"
	var frame := int(sprite.directions[direction_key][(int(clock*60.0988)>>4)&1 if walking else 0])
	var anchor := Vector2(sprite.tile_origin[0],sprite.tile_origin[1])
	ui._draw_frame(sprite,frame,at-anchor,dir.x<0)

func _camera() -> Vector2:
	var camera := render_position-Vector2(120,112)
	if camera_override.x>=0:camera=camera_override
	return Vector2(roundf(clampf(camera.x,0,maxf(0,int(room.width)*TILE-256))),roundf(clampf(camera.y,0,maxf(0,int(room.height)*TILE-240))))

func _inside(at: Vector2i) -> bool:
	return at.x>=0 and at.y>=0 and at.x<int(room.width) and at.y<int(room.height)

func _tile(at: Vector2i) -> int:
	if not _inside(at):return 255
	return int(game.hub_changes.get(str(game.hub_id),{}).get(str(at.y*int(room.width)+at.x),room.tiles[at.y*int(room.width)+at.x]))

func _ground(at: Vector2i) -> bool:
	if not _inside(at):return false
	var tile := _tile(at)
	return tile<96 or (tile>=232 and (int(game.hubs.tile_actions[tile-232])&15)==0)

func _door(at: Vector2i) -> bool:
	if not _inside(at):return false
	var tile := _tile(at)
	return tile>=232 and (int(game.hubs.tile_actions[tile-232])&15) in [1,7]

func _open_door(at: Vector2i) -> void:
	var tile := _tile(at)
	if (int(game.hubs.tile_actions[tile-232])&15)==7 and game.route != "alm":return
	var start := at-Vector2i(0,1) if tile in [242,244,246,248] else at
	var pattern := 5 if game.hub_id==15 else 8 if game.hub_id==37 else 9 if game.hub_id in [31,110] else 10 if game.hub_id in [1,6,9,10,21] else 2
	_stamp_pattern(start,pattern)
	ui.audio.play_sfx("menu_confirm")
	game.save_game()

func _set_tile(at: Vector2i, tile: int) -> void:
	if not _inside(at):return
	var key := str(game.hub_id)
	if not game.hub_changes.has(key):game.hub_changes[key]={}
	game.hub_changes[key][str(at.y*int(room.width)+at.x)]=tile

func _stamp_pattern(at: Vector2i, pattern_id: int) -> void:
	var pattern: Array = game.hubs.tile_change_patterns.get(str(pattern_id),[])
	for i in range(pattern.size()):_set_tile(at+Vector2i(int(i/4),i%4),int(pattern[i]))

func _actor_at(at: Vector2i) -> int:
	for id in actors:
		if not bool(actors[id].get("hidden",false)) and int(actors[id].get("sprite_id",0)) and _position(actors[id])==at:return int(id)
	return 0

func _position(value: Dictionary) -> Vector2i:
	var pos: Array = value.get("position",[0,0])
	return Vector2i(int(pos[0]),int(pos[1]))

func _character_key(cid: int) -> String:
	# Recruit opcode11 references Clive's duplicate template slot.
	if cid == 11:return "clive"
	for key in game.characters:
		if int(game.characters[key].get("character_id",0))==cid:return str(key)
	return ""

func _unit_name(id: String) -> String:
	return str(game.characters.get(id,{}).get("name_zh",""))

func _notice(text: String) -> void:
	notice=text
	notice_left=2.0

func _wander() -> void:
	var tick := int(clock*60.0988)
	if tick/64 == last_wander_tick:return
	last_wander_tick=tick/64
	for id in actors:
		var actor: Dictionary=actors[id]
		if bool(actor.get("hidden",false)) or not(int(actor.get("movement_flags",0))&128):continue
		var dir: Vector2i=DIRS[game.random_bounded(4)+1]
		var destination:=_position(actor)+dir
		var bounds: Array=actor.get("wander_bounds",[0,0,0,0])
		if destination.x<=int(bounds[0]) or destination.y<=int(bounds[1]) or destination.x>int(bounds[2]) or destination.y>int(bounds[3]):continue
		if not _ground(destination) or _actor_at(destination)>0 or destination==game.hub_position:continue
		actor.facing=DIRS.find(dir)
		_start_motion(int(id),destination,STEP)
		return

func dispose() -> void:
	after_dialogue = Callable()
	after_choice = Callable()
	on_choice_cancel = Callable()
	pages.clear()
	choices.clear()
	ui = null
	game = null

func _initial_facing(flags: int) -> int:
	var direction_code := flags & 15
	return direction_code if direction_code >= 1 and direction_code <= 4 else 4

func _portrait_index(character_id: int) -> int:
	if character_id == 1 and bool(game.roster.get("alm",{}).get("promoted",false)):
		return int(ui.graphics.character_portraits.get("36",0))
	if character_id == 2 and bool(game.flags.get("celica_promoted",false)):
		return int(ui.graphics.character_portraits.get("37",0))
	return int(ui.graphics.character_portraits.get(str(character_id),0))

func _display_name(character_id: int) -> String:
	var name := _unit_name(_character_key(character_id))
	if not name.is_empty(): return name
	return str({36:"女子",37:"男孩",38:"女孩",39:"吉克",43:"哈尔克",134:"朱达",141:"马塞纳"}.get(character_id,""))
