extends "res://tests/character_art_sync.gd"
## Reuse the frozen accepted-art selectors, without loading all motions in gameplay.
const Programs = preload("res://core/animation_programs.gd")
const REPORT = "res://reports/full-assessment-20261025/performance/animation-streaming.json"
var runtime_memory: Dictionary = {}
var equivalence: Dictionary = {}

func run():
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OUT+"import.json"))
	var data = Reviewed.metadata()
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/revenge-performance-20261025/slots";ui.game.save_path="/private/tmp/revenge-performance-20261025/animation.json";root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.game.new_game();ui.instant_mode=true;ui.audio.stop_all();ui.audio.set_process(false)
	var initial_memory = int(Performance.get_monitor(Performance.MEMORY_STATIC))
	var profile_art: Dictionary = {};var samples: Dictionary = {}
	for item in expected.inventory:
		if item.context == "battle":profile_art[item.profile]=data.battle[item.key]
	var max_load_usec = 0;var select_usec = 0
	for item in expected.actions:
		if item.kind != "attack":continue
		if item.key=="5_enemy" and str(item.id).ends_with("--original_class_5_enemy_normal"):continue
		if item.profile=="hunapu-battle" and str(item.id).ends_with("--original_class_21_promoted"):continue
		var art: Dictionary = profile_art[item.profile];var event=fixture(item,art)
		var started=Time.get_ticks_usec();var chosen=ui.battle_animation.selection(event);var elapsed_us=Time.get_ticks_usec()-started
		max_load_usec=maxi(max_load_usec,elapsed_us);select_usec+=elapsed_us
		check(chosen.get("key","")==item.runtime_key,"streamed selector "+item.id)
		if chosen.get("key","")!=item.runtime_key:continue
		selected+=1
		check(chosen.variant.frames.size()==int(item.frames) and int(chosen.variant.contact_tick)==int(item.contact_tick) and float(chosen.variant.native_fps)==float(item.fps),"streamed frame count/contact/clock "+item.id)
		if not samples.has(item.profile):samples[item.profile]=item
	for profile in samples:
		var item:Dictionary=samples[profile];var art:Dictionary=profile_art[profile];var event=fixture(item,art)
		ui.battle_animation.reset();await ui.battle_animation.play(event)
		check(ui.battle_animation.contact_calls==1 and ui.game.find_unit(event.defender).hp==29,"single contact after streamed play "+profile)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[event.attacker]==Vector2.ZERO,"streamed cleanup "+profile)
		for kind in ["miss","hit","exit"]:check(await ui.battle_animation.reaction(event.attacker,kind),"streamed reaction "+profile+"/"+kind)
	ui.instant_mode=false;ui.animation_speed=20.0
	for profile in ["hunapu-promoted-battle","professions-class-17-enemy-battle","professions-class-16-enemy-battle"]:
		var item:Dictionary=samples[profile];var event=fixture(item,profile_art[profile]);ui.battle_animation.reset();await ui.battle_animation.play(event)
		check(ui.battle_animation.contact_calls==1 and ui.game.find_unit(event.defender).hp==29,"timed streamed contact "+profile)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[event.attacker]==Vector2.ZERO,"timed streamed cleanup "+profile)
	check(Reviewed.cache.is_empty() and ui.battle_animation._source_cache.is_empty(),"actual gameplay never requests whole animation libraries")
	check(Programs.recent.size()<=Programs.CACHE_ENTRIES and Programs.cached_bytes<=Programs.CACHE_BYTES,"streamed programs respect entry and raw-byte budgets")
	var hot_key=str(samples.values()[0].runtime_key);Programs.variant("reviewed",hot_key);var reads=Programs.disk_reads
	for i in range(100):Programs.variant("reviewed",hot_key)
	check(Programs.disk_reads==reads,"100 hot animation lookups perform no file reads")
	runtime_memory={"before_selection":initial_memory,"after_all_current_attack_selectors":int(Performance.get_monitor(Performance.MEMORY_STATIC)),"retained_variants":Programs.recent.size(),"retained_raw_bytes":Programs.cached_bytes,"disk_reads":Programs.disk_reads,"maximum_single_selector_usec":max_load_usec,"total_selector_usec":select_usec}
	# Exhaustive offline equivalence, kept separate from the runtime memory sample.
	for group in ["reviewed","legacy","party"]:
		var path={"reviewed":"res://data/reviewed_animations.json","legacy":"res://data/legacy/full_animation_effects.json","party":"res://data/m11_party_motion.json"}[group]
		var original:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path));var different:Array=[];var frames_checked=0
		for key in original.variants:
			var actual=Programs.variant(group,str(key))
			if actual!=original.variants[key]:different.append(key)
			frames_checked+=actual.get("frames",[]).size()
		var expected_meta=original.duplicate(false);expected_meta.erase("variants")
		check(Programs.metadata(group)==expected_meta,"all source metadata exactly preserved "+group)
		check(different.is_empty(),"all indexed programs deeply equal original JSON "+group)
		equivalence[group]={"variants":original.variants.size(),"frames":frames_checked,"differences":different}
		original.clear();expected_meta.clear();print("ANIMATION_EQUIVALENCE ",group," ",JSON.stringify(equivalence[group]));await process_frame
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"selected_attacks":selected,"played_profiles":samples.size(),"timed_profiles":3,"runtime":runtime_memory,"offline_equivalence":equivalence,"device_measured":false}
	var file=FileAccess.open(REPORT,FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("ANIMATION_STREAMING ",JSON.stringify(result));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
