extends SceneTree
var viewport: SubViewport
var ui
var captures: Array = []
var errors: Array = []
var audited_pages := 0
var map_probe_done := false
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	call_deferred("run")
func snap(id: String):
	ui.phase_time = 0
	ui.notice_time = 0
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var path = "res://reports/screenshots/campaign-" + id + ".png"
	viewport.get_texture().get_image().save_png(path)
	for error in ui.layout_errors: errors.append(id + ": " + error)
	captures.append({"id":id,"path":path,"safe_area_errors":ui.layout_errors.duplicate(),"health":ui.health_checks.duplicate(true)})
func party(route: String, ids: Array):
	ui.game.route = route
	ui.game.party = []
	for id in ids: ui.game.recruit(id)
	ui.game.parties[route] = ui.game.party.duplicate()
func battle(stage: int, groups: Array = []):
	ui.game.world_node = stage if stage < 49 else 77
	ui.game.start_battle(stage,groups,true)
	ui.game.story_events.clear()
	ui.view = "battle"
	ui.ui_mode = "inspect"
	ui._clear_menu()
	ui._focus_battle(ui.game.cursor,true)
func actors(a: Dictionary, b: Dictionary, weapon: int):
	ui.game.units = [a,b]
	ui.combat = {"attacker":a.id,"defender":b.id,"distance":2 if weapon>=23 else 1,"initiative_side":a.side}
	ui.combat_poses = {}
	ui.combat_offsets = {}
	ui.combat_hp = {}
	ui.combat_fades = {}
	ui.battle_animation.reset()
	for unit in [a,b]:
		ui.combat_poses[unit.id] = ui._battle_sprite(unit).sequences.idle[0]
		ui.combat_hp[unit.id] = unit.hp
		ui.combat_offsets[unit.id] = Vector2.ZERO
		ui.combat_fades[unit.id] = 1.0
	ui.view = "combat"
	return {"attacker":a.id,"defender":b.id,"weapon_index":weapon,"hit":true,"critical":false,"hp_before":b.hp,"hp_after":b.hp,"damage":0}
func run():
	DirAccess.make_dir_recursive_absolute("res://reports/screenshots")
	viewport=SubViewport.new()
	viewport.size=Vector2i(256,240)
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate()
	viewport.add_child(ui)
	ui.game.save_path="res://reports/campaign-capture-save.json"
	ui.instant_mode=true
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.game.new_game()
	party("alm",["alm","lukas","gray","tobin","kliff","silque","clair","clive","forsyth","python"])
	ui.game.chapter=3
	ui.game.world_node=27
	ui.game.route_positions.alm=27
	ui.view="world"
	await snap("01-world-alm")
	battle(7)
	await snap("02-castle-map")
	ui.status_id=ui.game.living("enemy")[0].id
	ui.ui_mode="status"
	await snap("03-boss-status")
	party("celica",["celica","mae","boey","genny","saber","valbar","leo","kamui","palla","catria","atlas"])
	ui.game.chapter=2
	ui._show_campaign_chapter()
	await snap("04-chapter")
	ui.hub_controller.enter(5,Vector2i(7,2))
	await snap("05-priory")
	ui.game.chapter=3
	ui.game.world_node=24
	ui.view="world"
	await snap("06-world-celica")
	ui._camp_members("status")
	ui.menu_selected=10
	ui.menu_scroll=1
	await snap("07-roster-scroll")
	ui._clear_menu()
	battle(20)
	await snap("08-desert")
	var mage=ui.game.find_unit("mae")
	var foe=ui.game.living("enemy")[0]
	var event=actors(mage,foe,24)
	var selected=ui.battle_animation.selection(event)
	if selected.kind=="source":
		ui.battle_animation.show_frame(event,maxi(0,int(selected.variant.contact_tick)-8))
	await snap("09-thunder")
	ui.game.new_game()
	party("alm",["alm","lukas","silque"])
	party("celica",["celica","mae","genny"])
	ui.game.route="alm"
	ui.game.party=ui.game.parties.alm.duplicate()
	ui.game.chapter=5
	ui.game.flags.scenario_final_merge_ready=true
	battle(62)
	var duma: Dictionary={}
	for enemy in ui.game.living("enemy"):
		if int(enemy.character_id)==167:duma=enemy
	ui.game.cursor=ui.game.pos(duma)
	ui._focus_battle(ui.game.cursor,true)
	await snap("10-final-map")
	ui.status_id=duma.id
	ui.ui_mode="status"
	await snap("11-duma-status")
	var alm=ui.game.find_unit("alm")
	event=actors(duma,alm,19)
	await snap("12-duma-idle")
	selected=ui.battle_animation.selection(event)
	if selected.kind=="source":ui.battle_animation.show_frame(event,maxi(0,int(selected.variant.contact_tick)-4))
	await snap("13-duma-effect")
	ui._start_ending()
	await snap("14-ending")
	ui.ending_index=mini(ending_pages_size()-1,20)
	await snap("15-character-ending")
	ui.game.new_game()
	battle(20)
	ui.game.story_events.clear()
	var map_actor = ui.game.living("enemy")[0]
	map_actor.class_id=5
	map_actor.position=[8,8]
	ui._focus_battle(Vector2i(8,8),true)
	ui.instant_mode=false
	ui.animation_speed=1.0
	ui.busy=true
	for program in [3, 10, 2, 1]:
		map_probe_done=false
		map_probe(program,map_actor)
		for _tick in range(6): await process_frame
		await snap("map-effect-"+str(program))
		while not map_probe_done: await process_frame
	ui.map_effects.reset()
	ui.busy=false
	ui.instant_mode=true
	# Render every translated battle/death page with its real source portrait.
	ui.game.new_game()
	battle(7)
	ui.view = "battle_story"
	for group in ["events", "death_quotes"]:
		for key in ui.source_dialogues[group]:
			var texts: Array = ui.source_dialogues[group][key]
			var metadata: Array = ui.source_dialogue_meta[group][key].pages
			for i in range(texts.size()):
				var page: Dictionary = metadata[i]
				var content = str(texts[i]).replace("%2", ui._character_name(int(page.get("speaker_id", 0))))
				var lines = ui._wrapped_lines(content,152)
				for start in range(0,lines.size(),4):
					ui.dialogue_pages = [{"speaker_id":int(page.get("speaker_id",0)),"face_id":int(page.get("face_id",0)),"display_text":"\n".join(lines.slice(start,mini(start+4,lines.size())))}]
					ui.dialogue_index=0
					ui.dialogue_reveal=100000
					await audit_page(group+":"+str(key)+":"+str(i))
					if group=="events" and str(key)=="0" and i==0 and start==0: await snap("16-boss-dialogue")
	ui.game.roster.alm.promoted = true
	ui.view = "camp_status"
	ui.status_id = "alm"
	await snap("17-promoted-portrait")
	ui._start_ending()
	for i in range(ui.ending_pages.size()):
		ui.ending_index=i
		await audit_page("ending:"+str(i))
	var out=FileAccess.open("res://reports/campaign-visual-verification.json",FileAccess.WRITE)
	out.store_string(JSON.stringify({"guarded_offscreen":true,"captures":captures,"safe_area_errors":errors,"audited_translated_pages":audited_pages},"\t"))
	out.close()
	print("FE2_CAMPAIGN_CAPTURE screens=",captures.size()," errors=",errors)
	ui.audio.stop_all()
	ui.queue_free()
	await create_timer(0.3).timeout
	DirAccess.remove_absolute("res://reports/campaign-capture-save.json")
	quit(0 if errors.is_empty() else 1)
func ending_pages_size():return ui.ending_pages.size()

func audit_page(label: String):
	ui.queue_redraw()
	await process_frame
	await process_frame
	RenderingServer.force_draw(false)
	audited_pages+=1
	for error in ui.layout_errors: errors.append(label+": "+error)

func map_probe(program: int, unit: Dictionary):
	await ui.map_effects.play_program(program,unit)
	map_probe_done=true
