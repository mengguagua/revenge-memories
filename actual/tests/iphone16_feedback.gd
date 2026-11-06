extends SceneTree
## Incremental reproduction of the nine device findings. No device access.
const OUT="res://reports/iphone16-feedback-20261024/"
const RangePreview=preload("res://core/tactical_ranges.gd")
var checks=[]
var errors=[]
var shots=[]
var geometry=[]
var phone
var ui
var screen
var visual=false
var cache=""

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func tap(key:int):
	for button in phone.buttons:
		if int(button.key)!=key:continue
		var p=phone.safe_area.position+button.rect.get_center()*phone.pixel_scale
		phone._finger(91,p,true);phone._finger(91,p,false);return
func fresh_stage(id:int):
	ui.game.new_game();ui.game.save_path=cache+"working.json"
	ui.game.world_node=int(ui.game.stages[id].node)
	check(ui.game.start_battle(id),"stage fixture enters "+str(id))
	ui.game.story_events.clear();ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false
	ui.phase_time=0;ui.notice_time=0;ui._clear_menu();ui._focus_battle(ui.game.cursor,true);phone._sync_controls()
func frame(label:String,save_image:bool=false):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw()
	for i in range(4):await process_frame
	if visual:
		await RenderingServer.frame_post_draw
		check(ui.layout_errors.is_empty(),label+" text lies inside content-safe panels: "+str(ui.layout_errors))
		check(phone.layout_errors.is_empty(),label+" controls do not overlap: "+str(phone.layout_errors))
		if save_image:
			screen.get_texture().get_image().save_png(OUT+label+".png")
			shots.append({"file":label+".png","errors":ui.layout_errors.duplicate()+phone.layout_errors.duplicate()})

func run():
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	cache="/private/tmp/revenge-feedback-"+str(Time.get_ticks_usec())+"/"
	DirAccess.make_dir_recursive_absolute(cache+"slots")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116)
	phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	check(ui.title_selected==0,"empty boot selects New Game")
	ui.game.new_game();check(ui.game.save_to_slot(1),"create valid isolated journal")
	ui._show_title();check(ui.title_selected==1,"valid saved journal defaults to Continue")
	var bad=ui.game.Journals.path_for(ui.game.slot_directory,2)
	var f=FileAccess.open(bad,FileAccess.WRITE);f.store_string("invalid");f.close()
	ui._show_title();check(ui.title_selected==1,"corrupt second journal does not displace valid Continue")
	ui.elapsed=1.0 # Inspect settled selection, not the intentional entry fade.
	await frame("01-title-continue",true)
	if OS.get_environment("FEEDBACK_VISUAL_DELTA")=="1":
		fresh_stage(101)
		var visitor=ui.game.find_unit("hunapu");visitor.position=[10,4]
		ui.game.cursor=Vector2i(10,4);ui._focus_battle(ui.game.cursor,true)
		await frame("occupied-building-approach")
		check(ui.text_checks.any(func(t):return str(t.text).contains("可访问")),"unit card keeps visit hint visible when an actor occupies approach")
		var delta_report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"shots":shots,"scope":"Settled title and occupied-entrance hint only; previous menu/range/NPC images reused."}
		var delta_file=FileAccess.open(OUT+"visual-delta-checks.json",FileAccess.WRITE);delta_file.store_string(JSON.stringify(delta_report,"  "));delta_file.close()
		phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0 if errors.is_empty() else 1);return
	if OS.get_environment("FEEDBACK_TITLE_ONLY")=="1":
		phone.queue_free();await process_frame;screen.queue_free();await process_frame;quit(0);return
	DirAccess.remove_absolute(ui.game.Journals.path_for(ui.game.slot_directory,1))
	ui._show_title();check(ui.title_selected==0,"only corrupt records do not default to Continue")
	# All touch geometry remains outside game/notch/home-indicator safe areas.
	for spec in [[Vector2i(2556,1179),Rect2(177,0,2202,1116)],[Vector2i(1334,750),Rect2()],[Vector2i(1136,640),Rect2()]]:
		screen.size=spec[0];phone.safe_area_override=spec[1];ui.view="battle";phone._layout()
		for i in range(phone.buttons.size()):
			var b=phone.buttons[i];var rect=Rect2(phone.safe_area.position+b.hit_rect.position*phone.pixel_scale,b.hit_rect.size*phone.pixel_scale)
			check(phone.safe_area.encloses(rect) and not phone.game_rect.intersects(rect),"safe control "+str(spec[0])+"/"+str(b.key))
			if int(b.key) in phone.DIRECTION_KEYS:check(b.rect.size==Vector2(43,43),"equal enlarged direction key "+str(b.key))
			for j in range(i):check(not b.hit_rect.intersects(phone.buttons[j].hit_rect),"disjoint controls "+str(spec[0])+"/"+str(i)+"/"+str(j))
		geometry.append({"screen":spec[0],"buttons":phone.buttons.duplicate(true),"game_rect":phone.game_rect})
	screen.size=Vector2i(2556,1179);phone.safe_area_override=Rect2(177,0,2202,1116);phone._layout()
	check(phone.pixel_scale==4 and phone.game_view.size_2d_override==Vector2i(364,240),"iPhone16 game canvas is unchanged")
	fresh_stage(101)
	ui._open_system_menu()
	check(ui.menu_items.size()<=ui._menu_capacity() and ui._menu_row_height()==20,"normal battle system menu is compact and unpaged")
	check(ui._visible_native_rect().grow(-8).encloses(ui._menu_rect()),"full system menu fits phone safe canvas")
	for i in range(ui.menu_items.size()):check(ui._menu_pointer_index(ui._menu_row_rect(i).get_center())==i,"system menu row tap "+str(i))
	for i in range(ui.menu_items.size()-1):tap(KEY_DOWN)
	check(ui.menu_actions[ui.menu_selected]=="new:battle_title" and ui.menu_scroll==0,"last system action is reachable on same page")
	await frame("02-compact-menu",true)
	ui._clear_menu();ui.game.select_unit("hunapu");ui._unit_action_menu()
	check(ui._menu_rect().size.y==ui.menu_items.size()*20+24,"short unit action popup shrinks to its content")
	await frame("unit-action-popup")
	ui._open_menu("overflow",["一","二","三","四","五","六","七","八","九","十","十一"],range(11),Vector2(24,24))
	check(ui._menu_capacity()==9 and ui._visible_native_rect().grow(-8).encloses(ui._menu_rect()),"exceptional long menu uses bounded overflow")
	check(ui._menu_pointer_index(ui._menu_page_arrow_rect(1).get_center())==-1 and ui.menu_scroll>0,"overflow tap pages without confirming an action")
	ui._clear_menu()
	# A plain controlled arena tests reachable origins, spell unlocks, HP and blockers.
	var hero=ui.game.find_unit("hunapu");hero.position=[10,10];hero.move=2
	ui.game.units=[hero];ui.game.battle_data.map.tiles.fill(208)
	ui.game.battle_data.terrain.tile_categories["208"]=0
	var melee=RangePreview.preview(ui.game,hero)
	check(melee.movement.has(Vector2i(12,10)) and not melee.movement.has(Vector2i(13,10)),"movement uses actual two-tile budget")
	check(melee.attack.has(Vector2i(13,10)) and not melee.attack.has(Vector2i(14,10)),"melee adds only one-tile outer attack ring")
	check(melee.attack.all(func(p):return not melee.movement.has(p)),"green ring never repaints blue movement cells")
	var bow=hero.duplicate(true);bow.class_id=12;bow.item_id=21;ui.game.units=[bow]
	var ranged=RangePreview.preview(ui.game,bow)
	check(ranged.attack.has(Vector2i(17,10)) and not ranged.attack.has(Vector2i(18,10)),"equipped long bow extends outer ring to five tiles")
	var mage=hero.duplicate(true);mage.class_id=15;mage.item_id=0;mage.magic_flags=2;mage.hp=30;ui.game.units=[mage]
	var spells=RangePreview.preview(ui.game,mage)
	check(spells.attack.has(Vector2i(15,10)),"unlocked three-tile lightning is included")
	mage.magic_flags=0
	check(not RangePreview.preview(ui.game,mage).attack.has(Vector2i(15,10)),"locked lightning cannot inflate preview")
	mage.magic_flags=2;mage.hp=1
	check(RangePreview.preview(ui.game,mage).attack.is_empty(),"unaffordable magic does not show an attack ring")
	fresh_stage(101)
	hero=ui.game.find_unit("hunapu");hero.position=[10,5];ui.game.select_unit("hunapu");ui.ui_mode="move"
	ui.game.cursor=Vector2i(10,3);ui._focus_battle(ui.game.cursor,true)
	check(ui.game.interaction_hint(ui.game.cursor).text.contains("可访问"),"building under cursor advertises visitability")
	await frame("03-move-attack-visit",true)
	hero.position=[10,4];ui.game.cursor=Vector2i(10,4);ui.ui_mode="inspect"
	await frame("occupied-building-approach")
	if visual:check(ui.text_checks.any(func(t):return str(t.text).contains("可访问")),"unit card keeps visit hint visible when an actor occupies approach")
	# Existing escort semantics, including the reported stationary prospective companion.
	fresh_stage(112)
	var wagon=ui.game.find_unit("medicine_wagon");var hervi=ui.game.find_unit("hervi")
	var original_hervi=ui.game.pos(hervi)
	check(not ui.game.select_unit("hervi") and ui.game.ai_action(hervi).destination==original_hervi,"Hervi is a stationary non-controllable witness until delivery")
	var idle=ui._map_unit_sprite(hervi)
	check(str(idle.path).contains("professions-class-15-ally-maps-tactical-idle"),"prospective neutral Hervi uses approved new mage idle")
	ui.moving_id="hervi";ui.moving_direction=Vector2i.LEFT
	check(str(ui._map_unit_sprite(hervi).path).contains("professions-class-15-ally-maps-tactical-walk"),"same NPC identity resolves new movement art")
	ui.moving_id=""
	var rng_before=ui.game.rng_state
	var visit=ui.game.battle_data.objects[0]
	for cell in [Vector2i(22,4),Vector2i(22,5),Vector2i(21,3)]:check(ui.game.interaction_hint(cell).get("available",false),"entrance approach and footprint advertise same visit "+str(cell))
	ui.game.flags.quest.objects[visit.id]=true
	check(not ui.game.interaction_hint(Vector2i(22,4)).available,"visited building is not advertised as available")
	ui.game.flags.quest.objects.erase(visit.id)
	check(not ui.game.interaction_hint(Vector2i(25,4)).get("available",false),"decorative cottage does not advertise a visit")
	check(ui.game.rng_state==rng_before,"hover descriptions consume no RNG")
	var enemy=ui.game.living("enemy")[0];enemy.position=[8,20]
	check(ui.game.ai_action(wagon).destination==ui.game.pos(wagon) and ui.game.escort_hint(wagon).contains("敌近"),"medicine cart waits when enemies approach and explains why")
	ui.game.cursor=original_hervi;ui._focus_battle(ui.game.cursor,true)
	await frame("04-hervi-new-art-guidance",true)
	for e in ui.game.living("enemy"):e.hp=0
	ui.game.battle_data.reinforcements=[]
	var delivered=false;var steps=0
	for turn_ in range(35):
		wagon.acted=false
		var action=ui.game.ai_action(wagon);var destination:Vector2i=action.destination
		check(ui.game.can_stop(wagon,destination) and not ui.game.path_to(wagon,destination).is_empty(),"cart has a legal landing and route "+str(turn_))
		wagon.position=[destination.x,destination.y];ui.game.mark_wait("medicine_wagon");steps+=1
		check(ui.game.pos(hervi)==original_hervi,"stationary witness does not follow the cart "+str(turn_))
		if wagon.side=="evacuated":delivered=true;break
		ui.game.turn+=1
	check(delivered and ui.game.flags.quest.evacuated.has("medicine_wagon") and ui.game.battle_outcome=="victory","cleared-road escort reaches clinic and unlocks victory without moving Hervi")
	# Dedicated movement audio uses real streams and respects muting/objects.
	var heard=[];ui.audio.sfx_played.connect(func(key):heard.append(key))
	ui.audio._last_map_step_ms=-1000;ui.audio.play_map_step(hervi)
	check(heard==["map_step"] and ui.audio._step_player.playing,"human movement starts dedicated step voice")
	ui.audio.play_sfx("menu_move")
	check(ui.audio._step_player.playing,"UI cue cannot replace the dedicated movement voice")
	ui.audio.play_map_step(wagon);check(heard.count("map_step")==1,"event cart does not emit human footsteps")
	ui.audio.set_sfx_enabled(false);ui.audio._last_map_step_ms=-1000;ui.audio.play_map_step(hervi)
	check(not ui.audio._step_player.playing and heard.count("map_step")==1,"SFX mute stops and suppresses movement sound")
	ui.audio.set_sfx_enabled(true)
	fresh_stage(101);hero=ui.game.find_unit("hunapu")
	var route=ui.game.reachable(hero).costs.keys().filter(func(p):return ui.game.can_stop(hero,p) and ui.game.pos(hero)!=p)
	check(not route.is_empty(),"walking fixture has a legal destination")
	if not route.is_empty():
		var path=ui.game.path_to(hero,route[0]);var before_steps=heard.count("map_step")
		ui.audio._last_map_step_ms=-1000;ui.instant_mode=false
		await ui._animate_move(hero,path)
		ui.instant_mode=true
		check(heard.count("map_step")>before_steps,"real tile movement controller triggers movement sound")
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"geometry":geometry,"shots":shots,
		"escort_turns_after_road_clear":steps,"background_render":visual,"device_accessed":false,"user_saves_read":false,"user_saves_written":false,
		"scope":"Targeted nine-device-findings reproduction; isolated journals, controlled S12 clear-road escort, no full campaign replay or iPhone installation."}
	f=FileAccess.open(OUT+("visual-checks.json" if visual else "logic-checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("IPHONE_FEEDBACK ",checks.size()," checks; errors: ",errors)
	phone.queue_free();await process_frame;screen.queue_free();await process_frame
	quit(0 if errors.is_empty() else 1)
