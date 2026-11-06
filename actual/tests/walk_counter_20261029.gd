extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const OUT="res://reports/walk-counter-20261029/"
var checks=[]
var errors=[]
var shots=[]
var ui
var phone
var screen
var visual=false
var cache="/private/tmp/revenge-walk-counter-20261029/"
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path=cache+"fixture.json";g.world_node=3;g.start_battle(102);g.story_events.clear();return g
func fixture(cid:int,distance:int,item:int=0,guard:bool=true):
	var g=fresh();var enemy=g.find_unit("M12_boss").duplicate(true);var ally=g.characters.daan.duplicate(true)
	enemy.class_id=cid;enemy.item_id=item;enemy.position=[8,10];enemy.hp=52;enemy.max_hp=52;enemy.defence=20;enemy.speed=0;enemy.strength=11;enemy.resistance=3;enemy.behavior="guard" if guard else "chase"
	ally.id="daan";ally.side="player";ally.item_id=22;ally.position=[8-distance,10];ally.hp=52;ally.max_hp=52;ally.strength=1;ally.speed=0;ally.defence=20;ally.resistance=3;ally.acted=false
	g.units=[ally,enemy];return g
func domain():
	for cid in [1,2,4,6,7,22,8,9,10]:
		for distance in [1,2,3,4]:
			var g=fixture(cid,distance);var enemy=g.find_unit("M12_boss");var before=enemy.duplicate(true);var reply=Rules.default_counter(enemy,distance)
			var expected=4 if cid in [1,2,4,6,7,22] else 15
			check(enemy==before,"counter choice does not alter saved equipment "+str(cid)+"/"+str(distance))
			check(Rules.weapon_index(reply)==(0 if distance==1 else expected),"distance selects the actual melee/ranged weapon "+str(cid)+"/"+str(distance))
			check(Rules.can_attack(reply,distance)==(distance<=3),"guard counter keeps 1–3 reach "+str(cid)+"/"+str(distance))
			check(Rules.attack_range(enemy).y==1,"active melee reach stays unchanged "+str(cid)+"/"+str(distance))
			if distance<=3:
				var plan=g.plan_combat("daan","M12_boss");var stats=plan.stats.M12_boss
				check(int(stats.weapon_index)==(0 if distance==1 else expected),"real forecast uses the counter weapon "+str(cid)+"/"+str(distance))
				var replies=plan.events.filter(func(e):return str(e.attacker)=="M12_boss")
				check(not replies.is_empty() and replies.all(func(e):return int(e.weapon_index)==int(stats.weapon_index)),"strike events and forecast select the same weapon "+str(cid)+"/"+str(distance))
				if distance>1:check(bool(stats.magic)==(expected==15),"ranged weapon uses matching physical/magic defence "+str(cid)+"/"+str(distance))
	for pair in [[2,4],[8,15],[12,22]]:
		var g=fixture(pair[0],3,pair[1]);var enemy=g.find_unit("M12_boss")
		check(Rules.weapon_index(Rules.default_counter(enemy,3))==pair[1],"existing ranged armament is retained "+str(pair))
	var g=fixture(6,3,62);var enemy=g.find_unit("M12_boss")
	check(int(enemy.item_id)==62 and Rules.weapon_index(Rules.default_counter(enemy,3))==4,"armoured commander retains loot while using counter-only javelin")
	check(not Rules.can_attack(Rules.default_counter(fixture(6,2,0,false).find_unit("M12_boss"),2),2),"ordinary melee cannot gain the guard-only ranged counter")
	var body=fixture(3,3).find_unit("M12_boss");check(Rules.weapon_index(Rules.default_counter(body,3))==Rules.Body.STONE_SPIT,"stone creature counters at range with its spit rather than a distant claw")
	var a=g.units[0].duplicate(true);a.class_id=8;a.item_id=11;a.strength=10;a.skill=5
	var damages=[]
	for cid in [1,6,8]:
		var b=enemy.duplicate(true);b.class_id=cid;b.item_id=0;b.defence=5;b.speed=0;damages.append(Rules.attack_stats(a,b,0).damage)
	check(damages[0]==damages[1] and damages[1]==damages[2],"ordinary sword has no weapon-triangle damage bonus against lances/swords")
	check(Rules.Items.effective_against(6,{"class_id":1}) and not Rules.Items.effective_against(6,{"class_id":8}),"existing anti-cavalry equipment effectiveness remains")
func frame(name:String,save:bool=false):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
	if visual:
		await RenderingServer.frame_post_draw
		check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph/touch bounds "+str(ui.layout_errors))
		if save:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func setup():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=false
func presentation():
	ui.game.new_game();ui.game.save_path=cache+"hub.json";ui.hub_controller.enter_room("P00")
	ui.prologue_scene.state={"clock":999.0};ui.prologue_scene.active=false
	var walk_frames={}
	ui.hub_controller.direction(Vector2i.RIGHT)
	for n in range(6):
		ui.hub_controller.process(.04);await frame("walk-tap-"+str(n),n in [0,4])
		if visual:walk_frames[ui.prologue_scene.audit.hero_travel_frame]=true
	if visual:check(walk_frames.size()==2,"one ordinary P00 tap plays both foot phases despite an old scene clock")
	var scene=ui.prologue_scene;scene.active=true;scene.state={"step":3,"time":.66,"clock":4.0,"sounds":{}};ui.view="prologue_scene"
	for step in [3,7]:
		walk_frames={}
		for n in range(5):
			scene.state.step=step;scene.state.time=(.67+n*.12 if step==3 else .03+n*.12);await frame("story-walk-"+str(step)+"-"+str(n),n in [0,3])
			if visual and scene.audit.hero_walking:walk_frames[scene.audit.hero_travel_frame]=true
		if visual:check(walk_frames.size()==2,"cinematic translation plays actual alternating foot frames in shot "+str(step))
	scene.active=false
	for cid in [6,2,8,10]:
		for distance in [2,3]:
			ui.game=fixture(cid,distance);ui.view="combat";ui.busy=true;ui.combat=ui.game.plan_combat("daan","M12_boss");ui.combat_hp={"daan":52,"M12_boss":52}
			var event=ui.combat.events.filter(func(e):return str(e.attacker)=="M12_boss")[0]
			ui.battle_animation.reset();ui.battle_animation.active_event=event
			var selected=ui.battle_animation.selection(event)
			check(str(selected.kind)=="source","ranged counter has a complete source animation "+str(cid)+"/"+str(distance))
			check(str(selected.get("key","")).contains("javelin" if cid in [6,2] else "levin"),"matching throwing/lightning animation "+str(cid)+"/"+str(distance))
			if str(selected.kind)!="source":continue
			for tick in [14,22,int(selected.variant.contact_tick)]:
				check(ui.battle_animation.show_frame(event,tick),"runtime frame selected "+str(cid)+"/"+str(distance)+"/"+str(tick))
				await frame("counter-%d-%d-%d"%[cid,distance,tick],distance==3)
				var art=ui.battle_animation.sprite(ui.game.find_unit("M12_boss"));var slot=int(ui.combat_poses.M12_boss)
				check(slot<int(art.frames),"counter pose stays inside its own actor atlas")
				if visual:check(ui.text_checks.any(func(t):return str(t.text)=="反击："+Rules.weapon_name(Rules.default_counter(ui.game.find_unit("M12_boss"),distance))),"combat HUD displays selected counter weapon")
			if distance==3:
				ui.instant_mode=true;ui.battle_animation.reset();await ui.battle_animation.play(event)
				check(ui.battle_animation.contact_calls==1 and int(ui.game.find_unit("daan").hp)==int(event.hp_after),"one actual contact applies exactly the planned counter damage "+str(cid))
				ui.instant_mode=false
	ui.game=fixture(6,3,62);ui.view="battle";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui.ui_mode="target";ui.game.selected_id="daan";ui.target_ids=["M12_boss"];ui.target_index=0;ui.game.cursor=ui.game.pos(ui.game.find_unit("M12_boss"));ui._focus_battle(ui.game.cursor,true)
	await frame("javelin-forecast",true)
	if visual:check(ui.battle_preview_audit.text_rows.any(func(r):return str(r.text).contains("投枪")),"forecast shows the javelin before committing")
	ui.status_id="M12_boss";ui.ui_mode="status";await frame("javelin-status",true)
	if visual:check(ui.text_checks.any(func(t):return str(t.text).contains("远反：投枪")),"status describes the ranged counter without replacing equipped armour")
	if visual:
		screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout();ui.ui_mode="target";await frame("compact-forecast",true)
func run():
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	domain();await setup();await presentation()
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	var report={"checks":checks.size(),"labels":checks,"errors":errors,"screenshots":shots,"visual":visual,"scope":"P00 tap walk and D00 moving feet; real counter plan/weapon/physical-magic profile; own javelin/Levin animation and HUD; guard boundaries, existing equipment and effectiveness. No iPhone update."}
	var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();print("WALK_COUNTER ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
