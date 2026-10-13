extends SceneTree
## Pure source-contract checks. Runtime campaign consumers have separate tests.

var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("_run")

func _check(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures.append(description)
		push_error(description)

func _read(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))

func _numbers_equal(actual: Variant, expected: Variant) -> bool:
	if actual is Array and expected is Array:
		if actual.size() != expected.size():
			return false
		for i in range(actual.size()):
			if not _numbers_equal(actual[i], expected[i]):
				return false
		return true
	return float(actual) == float(expected)

func _run() -> void:
	var catalog := _read("res://data/campaign.json")
	var content := _read("res://data/campaign_events.json")
	var hubs := _read("res://data/hubs.json")
	var events: Dictionary = content.events
	var choice: Dictionary = events.desert_choice
	_check(choice.branches.size() == 2, "Two mutually exclusive desert outcomes")
	for branch in choice.branches:
		_check(int(branch.defeat_character_id) != int(branch.recruit_character_id), "Defeated desert leader is never the recruit")
		_check(int(branch.retire_group_to_world_node) == 61, "Survivor withdraws to Grieth stronghold")
		_check(hubs.scripts.has(str(int(branch.hub_script_id))), "Survivor original recruit dialogue exists")
	_check(int(choice.branches[0].recruit_character_id) == 25, "Defeating Deen makes Sonya available")
	_check(int(choice.branches[1].recruit_character_id) == 26, "Defeating Sonya makes Deen available")
	var zeke: Dictionary = events.tatiana_zeke
	_check(int(zeke.required_event_flag) == 31, "Zeke checks Tatiana persistent recruitment flag31")
	_check(int(zeke.friendly_group_id) == 34 and int(zeke.hostile_group_id) == 35, "Zeke allies and Jerome enemies remain distinct")
	_check(not bool(zeke.player_controlled_on_conversion), "Zeke's army first becomes green NPCs")
	_check(int(zeke.recruitment.character_id) == 34 and int(zeke.recruitment.hub_id) == 21, "Zeke joins only through Rigel village dialogue")
	_check(int(zeke.npc_name_id_map["139"]) == 39, "Original NPC Zeke name ID remapped separately from recruited34")
	var delthea: Dictionary = events.delthea_rescue
	_check(int(delthea.controller_character_id) == 143 and int(delthea.captive_enemy_character_id) == 145, "Tatara and captive Delthea source identities")
	_check(delthea.effects[0].type == "remove_enemy_without_death", "Freeing Delthea cannot kill her")
	_check(not bool(delthea.captive_dies_instead.recruitment_allowed), "Killing Delthea blocks recruitment")
	_check(int(delthea.recruitment.character_id) == 29, "Rescued Delthea uses playable identity29")
	var rudolf: Dictionary = events.rudolf
	_check(not bool(rudolf.victory_requires_defeating_every_enemy), "Rudolf's death immediately ends battle")
	_check(int(rudolf.map_id) == 42 and int(rudolf.character_id) == 133, "Rudolf battle source identity")
	_check(rudolf.death_effects[1].award_kill_exp == false, "Surrendering soldiers do not produce kill XP")
	_check(int(events.jedah.vulnerable_turn_modulus) == 4, "Jedah vulnerability follows fourth turns")
	_check(int(events.jedah.vulnerable_turn_remainder) == 0, "Jedah vulnerable on4/8/12, not1/5/9")
	var dragon: Dictionary = events.dragon_valley
	_check(int(dragon.generator_index) == 6 and int(dragon.world_node) == 36, "Dragon valley uses its dedicated generator")
	_check(_numbers_equal(dragon.group_progression, [73, 74, 75, 76, 77, 78]), "All source dragon waves retained")
	_check(int(dragon.release.required_story_phase) == 3 and dragon.release.required_party == "celica", "Celica altar progression releases Alm")
	_check(int(dragon.release.clear_world_gate_bits) == 33, "Both valley gates and forced dragon generation cleared")
	var merge: Dictionary = events.final_merge
	_check(int(merge.battle_map_id) == 62, "Correct final tactical map independent of hub numbering")
	_check(int(merge.deployment.celica_layout_index) == 0 and int(merge.deployment.alm_layout_index) == 1, "Original two-army placement order")
	_check(int(merge.deployment.max_per_route) == 10, "Final battle retains ten slots for each route")
	_check(bool(merge.effects[0].keep_rosters_separate), "Final merge preserves both persistent rosters")
	_check(int(events.falchion.item_id) == 17 and int(events.falchion.hub_id) == 40, "Falchion is original underground treasure")
	_check(_numbers_equal(events.falchion.treasure_position, [7, 2]), "Falchion treasure coordinate")
	_check(_numbers_equal(events.falchion.approach_positions, [[7, 3], [8, 3]]), "Falchion approach trigger coordinates not transposed")
	var ending: Dictionary = events.duma_ending
	_check(int(ending.initial_hp) == 182, "Duma retains182HP")
	_check(_numbers_equal(ending.allowed_final_phase_weapon_ids, [17, 42]), "Final phase allows Falchion and Nosferatu")
	_check(not bool(ending.requires_killing_other_enemies), "Duma death ends campaign even with enemies remaining")
	_check(ending.effects[3].preserve_death_and_relationship_flags, "Character ending branches use persistent fates")
	var reward: Dictionary = events.victory_experience
	_check(int(reward.base_enemy_exp_value) == 20 and not bool(reward.can_level_up), "Victory XP source base20 with no levelup")
	_check(reward.result_exp == "min(99, current_exp + award)", "Victory XP caps at99")
	for key in content.chapter_transitions:
		var transition: Dictionary = content.chapter_transitions[key]
		var script: Dictionary = hubs.scripts[str(int(transition.trigger_hub_script))]
		var found := false
		for instruction in script.instructions:
			if instruction.kind == "chapter_transition" and int(instruction.transition) == int(key):
				found = true
		_check(found, "Chapter transition%s ties to actual hub instruction" % key)
	_check(int(content.chapter_transitions["3"].requires_hub_trigger_enabled_by_event_flag) == 48, "Mila visit gates the sluice/chapter4 transition")
	_check(int(content.chapter_transitions["4"].source_chapter_counter) == 4, "Source underground finale does not reinitialize chapter5 armies")
	_check(content.chapter_transitions["2"].feature_state_updates[0].consumed == false and int(content.chapter_transitions["2"].feature_state_updates[0].hub_id) == 9, "Chapter three opens original harbor northern road feature")
	_check(content.chapter_transitions["3"].feature_state_updates[0].consumed == true and int(content.chapter_transitions["3"].feature_state_updates[0].hub_id) == 15, "Chapter four applies original Mila sluice feature state")
	_check(catalog.routes.celica.chapter_nodes["2"].any(func(value): return int(value) == 7), "Celica chapter two includes shared castle gate between harbor and castle")
	_check(content.chapter_transitions["4"].initialize_chapter_armies == null, "Finale preserves existing armies and second-route state")
	_check(content.deployment_sort.swap_two_groups_if == "first_priority >= second_priority", "Equal-priority armies reverse exactly as source")
	_check(catalog.enemy_groups["7"].deployment_priority == catalog.enemy_groups["49"].deployment_priority, "Both Zofia gate armies have equal deployment priority")
	_check(_numbers_equal(content.transit_battlefields.map_ids, [16, 18, 35, 46]), "Transit maps do not invent fixed armies")
	_check(content.battle_allied_npcs.size() == 6, "All six source rescue NPCs included")
	for npc in content.battle_allied_npcs:
		_check(npc.side == "npc" and not bool(npc.player_controlled), "Rescue NPC starts uncontrolled")
		_check(bool(npc.death_is_persistent), "Rescue NPC death affects later recruitment")
		var stage := _read(catalog.stages[str(int(npc.map_id))].path)
		_check(int(npc.position[0]) < int(stage.map.width) and int(npc.position[1]) < int(stage.map.height), "Rescue NPC source position fits map")
	var report := {"checks": checks, "failures": failures, "scope": "pure source catalog and critical campaign precondition contracts"}
	var file := FileAccess.open("res://reports/campaign-content-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	print("CAMPAIGN CONTENT: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
