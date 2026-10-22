extends SceneTree
const State=preload("res://core/game_state.gd")
const SOURCE="res://reports/chapter2/play/natural-chapter-end-save.json"
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok,label):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func base():
	var g=State.new();g.save_path=SOURCE;check(g.load_game(),"authentic schema2 checkpoint migrates")
	g.save_path="res://reports/map-polish-late-20261022/fixtures/chapter3-state-save.json";check(g.begin_chapter_three(),"chapter three begins once")
	g.flags.D31_done=true;return g
func fixture(id):
	var g=base();g.route=g.stages[id].route;g.party=g.parties[g.route].duplicate();g.world_node=int(g.stages[id].node);g.route_positions[g.route]=g.world_node
	g.mode="world";check(g.start_battle(id),str(id)+" fixture starts with authored formation");return g
func use(g,id):
	var hero=g.find_unit(g.leader_id());hero.acted=false
	for o in g.battle_data.objects:
		if o.id!=id:continue
		var p=Vector2i(o.position[0],o.position[1])
		var at=Vector2i(o.approach[0],o.approach[1]) if o.has("approach") else p+Vector2i.DOWN if o.adjacent else p
		hero.position=[at.x,at.y];g.selected_id=hero.id;check(g.interact(id),str(g.stage_id)+" interaction "+id);return
	check(false,"missing interaction "+id)
func kill_boss(g):g.find_unit(str(g.battle_data.boss_id)).hp=0
func run():
	var g=base();var roster=g.roster.duplicate(true);var convoy=g.convoy.duplicate(true)
	check(not g.begin_chapter_three(),"cannot initialize chapter twice")
	check(g.stage_for_node(6)==301 and not g.can_switch_route(),"west street chosen at shared city, opening order locked")
	g.cleared_stages.append(301);g.mode="world";check(g.switch_route(),"east route switch after western escape")
	check(g.stage_for_node(6)==304 and g.units.is_empty() and g.battle_start_snapshot.is_empty(),"shared city selects east dock and clears stale battle")
	check(g.roster==roster and g.convoy==convoy,"switch preserves actual injury, growth and inventory")
	g.cleared_stages.append(304);g.flags.D32_done=true;check(g.allowed_world_nodes().has(24),"salt road opens after reunion")
	g.world_node=24;g.previous_world_node=6;g.switch_route();check(g.world_node==6 and g.previous_world_node==6,"western position restored")
	g.world_node=7;g.previous_world_node=6;g.switch_route();check(g.world_node==24 and g.previous_world_node==6,"eastern position restored")
	check(g.save_game(),"dual route save writes");var resumed=State.new();resumed.save_path=g.save_path
	check(resumed.load_game(),"dual route reload validates");check(resumed.route=="celica" and int(resumed.route_positions.alm)==int(g.route_positions.alm) and int(resumed.route_positions.celica)==int(g.route_positions.celica),"dual route reload positions")
	for id in g.ChapterThree.STAGES:
		var b=fixture(id);var occupied={}
		for u in b.units:
			check(b.in_bounds(State.pos(u)) and b.movement_cost(u,State.pos(u))<255,str(id)+" legal formation "+u.id)
			check(not occupied.has(State.pos(u)),str(id)+" unique cell "+u.id);occupied[State.pos(u)]=true
		check(b.battle_data.map.tiles.all(func(tile):return int(b.battle_data.terrain.tile_categories[str(int(tile))])!=16),str(id)+" no unmarked poison terrain")
		check(not b.can_switch_route(),str(id)+" no route switching in battle")
		check(not b.objective_status().is_empty(),str(id)+" readable objective")
		check(b.save_game(),str(id)+" battle saves")
		var loaded=State.new();loaded.save_path=b.save_path;check(loaded.load_game(),str(id)+" battle reloads")
		check(loaded.retry_battle() and loaded.turn==1 and loaded.battle_outcome=="",str(id)+" retry restores deployment")
		check(b.check_outcome()=="",str(id)+" no premature victory")
		for n in b.units:
			if n.get("locked",false):check(not b.can_attack(b.find_unit(str(b.battle_data.boss_id)),n),str(id)+" guards do not kill their held captive "+n.id)
		kill_boss(b);check(b.check_outcome()=="",str(id)+" boss death alone cannot skip objective")
		for o in b.battle_data.objects:use(b,str(o.id))
		if id==303:
			var hero=b.find_unit("hunapu");var p=b.pos(b.find_unit("german"))+Vector2i.DOWN;hero.position=[p.x,p.y];hero.acted=false;b.selected_id=hero.id
			check(b.interact("german_accept"),"german explicit surrender interaction")
		if id in [301,304,305]:
			var ids=["detained0","detained1"] if id==301 else ["dock_patients0","dock_patients1"] if id==304 else ["salt_guide"]
			for n in ids:
				var u=b.find_unit(n);u.locked=false;u.position=b.battle_data.exit.duplicate();b.mark_wait(n)
		check(b.check_outcome()=="victory",str(id)+" full contract permits victory")
		check(b.complete_battle(),str(id)+" settlement once");var settled=b.convoy.duplicate(true)
		check(not b.complete_battle() and settled==b.convoy,str(id)+" no duplicate rewards")
		b.mode="world";check(b.save_game(),str(id)+" settled save");loaded.save_path=b.save_path;check(loaded.load_game(),str(id)+" settled reload")
	# Transport uses visible occupied cells and deterministic timing, never teleporting through units.
	g=fixture(302);var cart=g.find_unit("transport_cart");var initial=cart.position.duplicate();g.phase="player";g.turn=5;g.ChapterThree.after_phase(g)
	check(cart.position==initial,"cart waits through start of turn5")
	g.turn=6;g.ChapterThree.after_phase(g);check(g.flags.quest.transport_index==1,"cart moves one cell after fifth enemy phase")
	use(g,"station_w");g.turn=7;var parked=cart.position.duplicate();g.ChapterThree.after_phase(g);check(cart.position==parked,"either station stops cart")
	g=fixture(305);g.find_unit("salt_guide").hp=0;kill_boss(g);check(g.check_outcome()=="","dead guide still needs recovered notes")
	use(g,"guide_notes");check(g.check_outcome()=="victory","dead guide has a reachable nonblocking information branch")
	g=fixture(312);g.find_unit("noya_brother").hp=0;kill_boss(g);use(g,"mage_barrack");use(g,"civilian_barrack");g.complete_battle()
	check(g.flags.chapter3_recruits.noya and not g.flags.noya_brother_survived,"sister recruit does not resurrect brother")
	g=fixture(303);var surrendered=g.find_unit("german");surrendered.hp=0
	var loot=g.Inventory.on_death(g,surrendered,g.find_unit("hunapu"))
	check(int(loot.get("item_id",0))==62,"defeated German drops his explicitly carried weapon once")
	check(g.Inventory.on_death(g,surrendered,g.find_unit("hunapu")).is_empty(),"German carried weapon cannot duplicate")
	# Both completion orders and meeting requirements.
	for order in [[303,306],[306,303]]:
		g=base();g.flags.D32_done=true;g.cleared_stages.append_array([301,304]);g.cleared_stages.append(order[0]);g.flags.M33_confirmed=true;g.flags.F33_confirmed=true
		check(not g.allowed_world_nodes().has(9),"one investigation alone cannot open meeting "+str(order))
		g.cleared_stages.append(order[1]);check(g.allowed_world_nodes().has(9),"either investigation order opens meeting "+str(order))
	g=base();g.cleared_stages.append_array([301,304,303,306]);g.flags.D32_done=true;g.flags.D33_done=true;g.ensure_treatment_sources()
	check(g.treatment_remaining()==3,"meeting grants one plus two unused earlier shares")
	g.mode="hub";g.hub_record="H10";var before=g.roster.fula.duplicate(true)
	check(g.treat_member("fula").valid,"shared treatment restores actual western casualty")
	check(g.roster.fula.level==before.level and g.roster.fula.exp==before.exp,"treatment preserves experience and growth")
	g.switch_route();g.mode="hub";g.hub_record="H10";check(g.treatment_remaining()==2,"switch shares one combined stock")
	check(g.treat_member("mireille").valid and g.treatment_remaining()==1,"east consumes same shared stock")
	g.ensure_treatment_sources();check(g.treatment_remaining()==1,"meeting sources idempotent")
	g.route_positions={"alm":9,"celica":9};g.world_node=9
	var source_count=g.convoy.alm.size();var dest_count=g.convoy.celica.size();var transfer=g.ChapterThree.transfer_supply(g,0)
	check(transfer.valid and g.convoy.alm.size()==source_count-1 and g.convoy.celica.size()==dest_count+1,"camp transfer moves one real item between convoys")
	g.route_positions.alm=8;check(not g.ChapterThree.transfer_supply(g,0).valid,"remote party cannot send equipment by letter");g.route_positions.alm=9
	var old_path=g.save_path;g.save_path="/unwritable/chapter3.json";var old_convoy=g.convoy.duplicate(true)
	check(not g.ChapterThree.transfer_supply(g,0).valid and g.convoy==old_convoy,"failed save rolls back physical camp handoff");g.save_path=old_path
	check(g.save_game(),"shared treatment save writes");resumed.save_path=g.save_path;check(resumed.load_game() and resumed.treatment_remaining()==1,"shared treatment survives reload")
	# Malformed route and over-spent stock are rejected before modifying live state.
	var valid=State.read_json(g.save_path)
	for field in ["route","stock"]:
		var bad=valid.duplicate(true)
		if field=="route":bad.route="alm"
		else:bad.flags.treatment_used.celica=99
		var f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(JSON.stringify(bad));f.close()
		var old=resumed.roster.duplicate(true);check(not resumed.load_game() and resumed.roster==old,"invalid "+field+" rejected atomically")
	var f=FileAccess.open("res://reports/map-polish-late-20261022/fixtures/chapter3-state-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"fixture":true},"  "));f.close()
	print("CH3_STATE ",checks.size()," checks, errors ",errors)
	quit(0 if errors.is_empty() else 1)
