extends SceneTree
const State=preload("res://core/game_state.gd")
const Review=preload("res://core/promotion_review.gd")
const Tasks=preload("res://core/current_task.gd")
const OUT="res://reports/chapel-journal-20261030/"
var checks=[];var errors=[];var shots=[];var ui;var phone;var screen;var visual=false
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func frame(name:String):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
	if visual:
		await RenderingServer.frame_post_draw
		check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph/touch safe: "+str(ui.layout_errors))
		screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func domain():
	var g=State.new();g.new_game();g.save_path="/private/tmp/chapel-journal-20261030/domain.json"
	g.flags.prologue_done=true;g.flags.village_ready=true;g.cleared_stages=[101,102]
	check(Tasks.entry(g).text.contains("粮车"),"task journal catches grain-sharing road gate")
	g.flags.grain_shared=true;g.cleared_stages.append(103)
	check(Tasks.entry(g).text.contains("军令箱"),"task journal points to uncollected orders")
	g.flags.orders_collected=true;check(Tasks.entry(g).text.contains("旧塔教堂"),"task journal points to Herlan cooperation gate")
	g.flags.cooperation_done=true;check(Tasks.entry(g).text.contains("旧塔外营"),"task updates after cooperation")
	var u=g.roster.otto;u.level=6;var before=u.duplicate(true)
	var preview=Review.preview(g,"otto",2);check(not preview.valid and preview.reason.contains("还差1级"),"ineligible member sees exact missing level")
	check(u==before,"preview cannot mutate stats, HP or items")
	u.level=7;preview=Review.preview(g,"otto",2);check(preview.valid and preview.after.class_id==2 and preview.rows.size()==8,"eligible preview has all eight numeric comparisons")
	check(Review.commit(g,preview).valid,"confirmed promotion succeeds")
	check(g.roster.otto.level==1 and g.roster.otto.exp==0 and g.roster.otto.hp==g.roster.otto.max_hp,"ordinary promotion resets level/EXP and restores HP")
	check(not Review.commit(g,preview).valid,"duplicate confirmation cannot promote twice")
	var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.roster.otto.class_id==2,"confirmed promotion persists and reloads")
	g.roster.otto.level=10;preview=Review.preview(g,"otto",22);g.roster.otto.item_id=0
	if preview.before.item_id==0:g.roster.otto.strength+=1
	check(not Review.commit(g,preview).valid,"stale preview is rejected")
	g.roster.otto.dying=true;check(not Review.preview(g,"otto",22).valid,"dying member cannot advance")
	g.roster.otto.dead=true;check(Review.preview(g,"otto",22).reason.contains("已阵亡"),"dead member explanation never promises revival")
	g.chapter=4;g.route="alm";g.cleared_stages.append(403);check(Tasks.entry(g).text.contains("切换东队"),"task explains cross-route observation prerequisite")
	var rows=[];var rules=g.Progression.Items.data()
	var definitions=rules.promotions.duplicate(true)
	for target in rules.villager_options:definitions.append({"from_class":14,"to_class":target,"level":3})
	for p in definitions:
		var actor=g.characters.otto.duplicate(true);actor.class_id=int(p.from_class);actor.level=int(p.level);actor.hp=20;actor.max_hp=20;actor.resistance=4;actor.personal_resistance=4
		var result=g.Progression.promote(actor,int(p.to_class));check(result.valid,"promotion route executes "+str(p.from_class)+"→"+str(p.to_class))
		rows.append({"from":int(p.from_class),"to":int(p.to_class),"level":int(p.level),"bases":rules.promotion_bases[str(int(p.to_class))],"move_before":rules.class_move[int(p.from_class)-1],"move_after":rules.class_move[int(p.to_class)-1],"example_before":actor,"example_after":result.unit})
	var enemies=[]
	for stage in g.stages.values():
		var actors=stage.enemies.duplicate(true);actors.append_array(stage.get("reinforcements",[]).duplicate(true));g.EnemyBalance.prepare(int(stage.id),actors)
		for enemy in actors:enemies.append({"stage":stage.code,"stage_id":stage.id,"unit":enemy})
	var file=FileAccess.open(OUT+"balance-data.json",FileAccess.WRITE);file.store_string(JSON.stringify({"classes":g.catalog.classes,"promotions":rows,"hero_professions":g.HeroProfessions.DEFINITIONS,"enemies":enemies},"  "));file.close()
func run():
	DirAccess.make_dir_recursive_absolute("/private/tmp/chapel-journal-20261030/slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1";domain()
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override="/private/tmp/chapel-journal-20261030/slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.game.new_game();ui.game.save_path="/private/tmp/chapel-journal-20261030/ui.json"
	ui.view="world";ui.game.mode="world";ui.game.flags.prologue_done=true;ui.game.flags.village_ready=true;ui.game.cleared_stages=[101,102,103];ui.game.flags.grain_shared=true;ui.game.flags.orders_collected=true
	ui._open_system_menu();check(ui.menu_items[1]=="当前任务","world menu places journal below party preparation");await frame("world-menu")
	ui._menu_action("new:tasks","world_system");check(ui.view=="field_notes" and ui.field_notes.record.text.contains("教堂"),"actual menu opens current next-action journal");await frame("current-task");ui._cancel();check(ui.view=="world","journal returns to world")
	ui.hub_controller.enter_room("H03");await frame("lena-pegasus")
	var lena=ui._party_hub_sprite({"action":"lena","name":"蕾娜"},{})
	check(str(lena.reviewed_profile).contains("class-3-ally"),"Lena is the approved pegasus profession before recruitment")
	ui.game.hub_position=Vector2i(10,5);ui.hub_controller.enter_room("H04",true);check(ui.game.hub_position==Vector2i(6,7),"old chapel save inside a new pew relocates to clear entrance");await frame("old-chapel")
	check(ui._party_hub_sprite({"action":"cooperate","name":"赫兰"},{}).path==ui.prologue_scene.cast_art.herlan.path,"Herlan exactly reuses the prologue silhouette")
	check(str(ui._party_hub_sprite({"action":"lance","name":"兰斯"},{}).reviewed_profile).contains("class-1-ally"),"Lance uses his cavalry profession")
	var reached={Vector2i(6,7):true};var todo=[Vector2i(6,7)]
	while not todo.is_empty():
		var p=todo.pop_front()
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var n=p+d
			if n.x<1 or n.x>12 or n.y<1 or n.y>7 or reached.has(n):continue
			if ui.hub_controller.objects.any(func(o):return ui.hub_controller.object_occupies(o,n)) or ui.hub_controller.scenery.any(func(o):return o.rect.has_point(n)):continue
			reached[n]=true;todo.append(n)
	for o in ui.hub_controller.objects:
		var p=Vector2i(o.position[0],o.position[1]);check([Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT].any(func(d):return reached.has(p+d)),str(o.name)+" has an accessible facing-interaction tile")
	ui.hub_controller._east_action("east_promotions");check(ui.view=="field_notes","eastern promotion entry uses the same review flow");ui.field_notes.cancel();ui.game.roster.otto.level=6;ui.hub_controller.action("shrine");await frame("promotion-list")
	var notes=ui.field_notes
	notes.selected=notes.entries.find({"id":"otto","target":2});notes.accept();check(notes.mode=="preview" and not notes.record.valid,"altar opens conditions before committing");await frame("promotion-locked")
	notes.cancel();ui.game.roster.otto.level=7;notes.accept();await frame("promotion-preview")
	var original=ui.game.roster.otto.duplicate(true);notes.accept();check(notes.mode=="confirm" and ui.game.roster.otto==original,"first acceptance opens second confirmation without changing stats");await frame("promotion-confirm")
	notes.cancel();check(ui.game.roster.otto==original,"return from confirmation keeps original member")
	notes.accept();notes.direction(Vector2i.RIGHT);notes.accept();check(ui.game.roster.otto.class_id==2,"explicit confirmation commits previewed profession");await frame("promotion-done")
	if visual:
		screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout();ui.game.roster.otto.level=10;notes.selected=notes.entries.find({"id":"otto","target":22});notes.accept();await frame("compact-preview")
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"screenshots":shots},"  "));file.close();print("CHAPEL_JOURNAL ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
