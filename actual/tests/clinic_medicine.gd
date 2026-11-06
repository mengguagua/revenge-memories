extends SceneTree
## Targeted scenario/save checks and unique background-only presentation captures.
const State=preload("res://core/game_state.gd")
const Art=preload("res://core/party_sprites.gd")
const OUT="res://reports/clinic-medicine-20261024/"
var checks=[]
var failures=[]
var shots=[]
var cache=""
var ui
var phone
var screen
var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path=cache+"working.json";g.world_node=32
	check(g.start_battle(112),"enter current S12")
	return g
func domain():
	var g=fresh();var h=g.find_unit("hervi");var w=g.find_unit("medicine_wagon")
	check(g.pos(h)==Vector2i(24,5) and h.side=="neutral" and h.quest_kind=="clinic_staff","Hervi is stationed at the clinic as noncombat staff")
	check(not g.select_unit("hervi") and g.ai_action(h).destination==g.pos(h),"clinic duty is stationary and not player controllable")
	check(not g.living("player").has(h) and g.living("player").has(w),"clinic staff are excluded from combat AI; transport remains an ordinary escort target")
	check(g.units.filter(func(u):return str(u.id)=="medicine_wagon").size()==1 and g.units.size()==g.party.size()+g.battle_data.enemies.size()+2,"visible transport worker adds no second unit, HP pool or blocking cell")
	var goal=Vector2i(g.battle_data.targets[0][0],g.battle_data.targets[0][1]);var fronts=[]
	for o in g.battle_data.objects:fronts.append_array(g.visit_fronts(o))
	check(g.pos(h)!=goal and not fronts.has(g.pos(h)) and g.movement_cost(h,g.pos(h))<255,"clinic duty leaves delivery and visit approaches open")
	var rng=g.rng_state;var enemy=g.living("enemy")[0]
	check(not g.can_attack(enemy,h) and str(g.ai_action(enemy).get("target",""))!="hervi","enemy attack intent cannot turn the clinic worker into a combat objective")
	check(g.rng_state==rng,"role and intent checks consume no battle RNG")
	var original=g.pos(w);enemy.position=[original.x+1,original.y]
	check(g.ai_action(w).destination==original and g.escort_hint(w).contains("敌近"),"transport worker waits near danger and explains the pause")
	for id in ["map","map_move","hub"]:
		var sp=Art.data().classes.civilian[id]
		check(str(sp.get("reviewed_profile","")).begins_with("professions-class-14-ally-") and ResourceLoader.exists(sp.path),"civilian fallback uses approved new profession art: "+id)
	for file in ["map","walk","hub"]:check(not FileAccess.file_exists("res://assets/party-0.7.0/civilian/"+file+".png"),"retired old runtime image removed: "+file)
	check(str(Art.sprite("map",h,1).get("reviewed_profile","")).contains("professions-class-15-ally-maps-tactical-idle"),"neutral clinic Hervi retains the new mage body")
	# Recruitment is enforced below the UI, including stale menu submissions.
	g.recruit("hervi");check(not g.party.has("hervi"),"cannot invite before delivery victory")
	g.flags.clinic_staffed=true;g.recruit("hervi");check(not g.party.has("hervi"),"staff flag alone cannot bypass delivery")
	g.flags.clinic_staffed=false;g.cleared_stages.append(112);g.recruit("hervi");check(not g.party.has("hervi"),"victory alone cannot bypass medical handover")
	g.flags.clinic_staffed=true;check(g.can_invite_hervi(),"victory and completed handover permit invitation")
	h.hp=0;g.recruit("hervi");check(not g.party.has("hervi"),"a dead legacy clinic NPC cannot be recruited")
	h.hp=24;g.recruit("hervi");check(g.party.has("hervi") and g.roster.hervi.controllable and not g.roster.hervi.neutral,"invitation grants the normal playable companion")
	# Emulate only pre-change NPC metadata in an isolated valid current-map save.
	g=fresh();h=g.find_unit("hervi");w=g.find_unit("medicine_wagon")
	h.position=[6,20];h.side="player";h.quest_kind="witness";h.erase("clinic_duty_revision");h.hp=19
	w.position=[11,20];w.hp=21;g.turn=4;g.rng_state=123
	for actor in g.battle_start_snapshot.units:
		if str(actor.id)=="hervi":actor.position=[6,20];actor.side="player";actor.quest_kind="witness";actor.erase("clinic_duty_revision")
	var tiles=g.battle_data.map.tiles.duplicate();var other_positions={}
	for actor in g.units:
		if str(actor.id)!="hervi":other_positions[str(actor.id)]=g.pos(actor)
	check(g.save_game(),"write isolated pre-change NPC checkpoint")
	var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"old active S12 checkpoint loads")
	check(loaded.pos(loaded.find_unit("hervi"))==Vector2i(24,5) and int(loaded.find_unit("hervi").hp)==19,"save migration moves only the living NPC and preserves wounds")
	check(loaded.turn==4 and loaded.rng_state==123 and loaded.battle_data.map.tiles==tiles,"save migration preserves turn, RNG and map geometry")
	check(loaded.units.all(func(u):return str(u.id)=="hervi" or loaded.pos(u)==other_positions[str(u.id)]),"save migration preserves wagon progress and all other actors")
	check(int(loaded.find_unit("medicine_wagon").hp)==21 and loaded.story_events.any(func(e):return str(e.get("key",""))=="S12-CLINIC-DUTY"),"migration preserves wagon damage and explains the new duty")
	check(loaded.save_game() and loaded.load_game() and loaded.retry_battle(),"migrated checkpoint supports save, load and retry")
	check(loaded.pos(loaded.find_unit("hervi"))==Vector2i(24,5) and loaded.find_unit("hervi").side=="neutral","retry snapshot uses the same clinic duty")
	# An occupied clinic side cell must not move another actor or block the doorway.
	g=fresh();h=g.find_unit("hervi");var blocker=g.find_unit("hunapu");blocker.position=[24,5]
	h.erase("clinic_duty_revision");h.position=[6,20];g.Medicine.prepare(g,g.units)
	check(g.pos(h)!=Vector2i(24,5) and g.pos(blocker)==Vector2i(24,5) and g.pos(h)!=goal and not fronts.has(g.pos(h)),"occupied legacy clinic station chooses a legal side cell without shifting others")
	g=fresh();h=g.find_unit("hervi");h.hp=0;h.position=[6,20];h.erase("clinic_duty_revision")
	check(not g.Medicine.prepare(g,g.units) and g.pos(h)==Vector2i(6,20) and int(h.hp)==0,"migration does not move or revive a dead NPC")
	g=fresh();h=g.find_unit("hervi");h.neutral=false;h.controllable=true;h.position=[6,20];h.erase("clinic_duty_revision")
	check(not g.Medicine.prepare(g,g.units) and g.pos(h)==Vector2i(6,20),"migration leaves an already recruited Hervi untouched")
	g.stage_id=101;h.neutral=true;h.controllable=false
	check(not g.Medicine.prepare(g,g.units),"clinic migration has no effect in other stages")
func settle_pages():
	for i in range(100):
		if ui.view!="plot":break
		ui._advance_plot();await process_frame
	check(ui.view!="plot" and not ui.busy,"dialogue returns player control")
func frame(label:String,save_image:bool=true):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	for i in range(4):await process_frame
	if not visual:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),label+" text and controls respect safe content bounds: "+str(ui.layout_errors))
	if save_image and (OS.get_environment("CLINIC_CAPTURE_FILTER").is_empty() or OS.get_environment("CLINIC_CAPTURE_FILTER").split(",").has(label)):
		screen.get_texture().get_image().save_png(OUT+label+".png");shots.append(label+".png")
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4
	ui.game.new_game();ui.game.save_path=cache+"ui.json";ui.game.world_node=32;ui.game.start_battle(112);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.phase_time=0;ui.notice_time=0
	var h=ui.game.find_unit("hervi");var w=ui.game.find_unit("medicine_wagon")
	ui.game.cursor=ui.game.pos(h);ui._focus_battle(ui.game.cursor,true)
	await frame("01-clinic-duty")
	if visual:check(ui.text_checks.any(func(t):return str(t.text).contains("核对药单")),"clinic card displays the actual duty")
	ui.game.cursor=ui.game.pos(w);ui._focus_battle(ui.game.cursor,true)
	ui.moving_id=str(w.id);ui.moving_position=Vector2(w.position[0],w.position[1])*16;ui.moving_direction=Vector2i.RIGHT;ui.moving_frame=1
	await frame("02-visible-transport")
	if visual:check(ui.presentation_audit.medicine_transport.moving and str(ui.presentation_audit.medicine_transport.worker)==str(Art.Reviewed.data().maps["14_ally"]["tactical-walk"].path),"visible transport uses approved new walking art")
	ui.moving_id="";ui.hub_controller.enter_room("H09");ui.game.mode="hub";ui.view="hub";ui.busy=false
	if not visual:
		ui.hub_controller.action("staff");check(not ui.game.flags.get("clinic_staffed",false) and ui.view=="hub","administrator cannot hand over before the medicine victory")
		ui.hub_controller.action("recruit_hervi");check(not ui.game.party.has("hervi"),"stale invitation action cannot bypass delivery")
	ui.game.cleared_stages.append(112);ui.hub_controller.enter_room("H09")
	if not visual:
		ui.hub_controller.action("hervi");await settle_pages();check(not ui.menu_actions.has("hub:recruit_hervi"),"Hervi explains the pending handover before showing an invitation")
	ui.hub_controller.action("staff");check(not ui.game.flags.get("clinic_staffed",false) and ui.plot_callback=="clinic_handover","medical handover stays pending until dialogue finishes")
	if not visual:
		check(ui.game.save_game(),"handover in progress can be saved")
		var saved=State.new();saved.save_path=ui.game.save_path;check(saved.load_game() and str(saved.flags.active_plot.callback)=="clinic_handover" and not saved.flags.get("clinic_staffed",false),"mid-dialogue save preserves the pending handover callback")
	await settle_pages()
	check(ui.game.flags.get("clinic_staffed",false) and not ui.game.party.has("hervi"),"completed handover enables invitation without automatically recruiting")
	ui.game.hub_position=Vector2i(6,7);ui.hub_controller.facing=Vector2i.UP;ui.hub_controller.render_position=Vector2(ui.game.hub_position)*16
	await frame("03-handover-ready")
	if visual:check(ui.text_checks.any(func(t):return str(t.text).contains("管理员已接手")),"completed handover guidance is visible at the clinic entrance")
	check(str(ui._party_hub_sprite({"action":"hervi"},{}).get("reviewed_profile","")).contains("professions-class-15-ally-maps-tactical-idle") and str(ui._party_hub_sprite({"action":"transport"},{}).get("reviewed_profile","")).contains("professions-class-14-ally-maps-tactical-idle"),"both clinic NPCs use the new profession artwork")
	check(str(ui._party_hub_sprite({"action":"staff"},{}).get("reviewed_profile","")).contains("professions-class-18-ally-maps-tactical-idle"),"clinic administrator also uses the approved new healer body")
	if not visual:
		ui.hub_controller.action("hervi");check(ui.menu_actions.has("hub:recruit_hervi"),"player can explicitly invite after handover")
		ui._clear_menu();ui.hub_controller.action("recruit_hervi");await settle_pages()
		check(ui.game.party.has("hervi") and ui.hub_controller.hint.contains("赫维已同行"),"confirmed invitation joins the party and updates the clinic hint")
	phone.queue_free();await process_frame;screen.queue_free();await process_frame
func run():
	cache="/private/tmp/clinic-medicine-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	if not visual:domain()
	await presentation()
	var file=FileAccess.open(OUT+("visual-checks.json" if visual else "checks.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"screenshots":shots,"background_guard":visual,"device_updated":false,"scope":"S12 role, delivery/recruitment gates, save/retry migration, new profession art, unique phone-layout viewport captures. Full S12 victory is recorded separately by the real-input driver."},"  "));file.close()
	print("CLINIC_MEDICINE ",checks.size()," checks, ",failures.size()," failures")
	quit(0 if failures.is_empty() else 1)
