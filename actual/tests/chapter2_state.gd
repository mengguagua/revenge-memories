extends SceneTree
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func western():
	var g=State.new();g.save_path="res://reports/campaign/natural-chapter-end-save.json"
	check(g.load_game(),"real shipped schema-1 chapter-end checkpoint loads")
	g.save_path="res://reports/chapter2/state-check-save.json";return g
func fixture(id: int):
	var g=western();check(g.begin_chapter_two(),"fixture enters eastern chapter")
	g.world_node=int(g.stages[id].node);g.previous_world_node=17
	check(g.start_battle(id),str(id)+" starts with real stage/party data");return g
func boss_dead(g) -> void:g.find_unit(str(g.battle_data.boss_id)).hp=0
func all_dead(g) -> void:
	for enemy in g.living("enemy"):enemy.hp=0
func interact(g,id: String) -> void:
	for obj in g.battle_data.objects:
		if str(obj.id)!=id:continue
		var hero=g.find_unit("eileen");var p=Vector2i(obj.position[0],obj.position[1]);hero.position=[p.x,p.y+1] if obj.adjacent else [p.x,p.y];hero.acted=false
		g.selected_id="eileen";check(g.interact(id),str(g.stage_id)+" explicit interaction "+id);return
	check(false,str(g.stage_id)+" expected object "+id)
func evacuate(g,ids: Array) -> void:
	for id in ids:
		var u=g.find_unit(str(id));u.locked=false;u.position=g.battle_data.exit.duplicate();g.mark_wait(str(id))
func run() -> void:
	for checkpoint in ["natural-prologue","natural-M15-deployment","natural-S12-victory","natural-chapter-end"]:
		var old=State.new();old.save_path="res://reports/campaign/"+checkpoint+"-save.json"
		check(old.load_game(),"actual schema-1 migration: "+checkpoint)
	var g=western();var west_party=g.party.duplicate();var west_roster=g.roster.duplicate(true);var west_convoy=g.convoy.alm.duplicate();var old_position=g.world_node
	check(g.begin_chapter_two(),"chapter one confirms transition to two")
	check(g.chapter==2 and g.route=="celica" and g.world_node==17 and g.hub_record=="H21","eastern timeline starts at wind-lamp island")
	check(g.party==["eileen","mireille","lisa","carlo"],"four eastern starters are independent")
	check(g.parties.alm==west_party and g.convoy.alm==west_convoy and g.route_positions.alm==old_position,"western party items and position preserved")
	for id in west_roster:check(g.roster[id]==west_roster[id],"western actual growth/equipment/death preserved: "+id)
	check(not g.begin_chapter_two(),"chapter initialization cannot repeat or reset eastern growth")
	check(g.allowed_world_nodes()==[17],"east departure requires island confirmation")
	g.flags.east_departure_ready=true;check(g.allowed_world_nodes()==[17,18],"first sea battle opens after departure")
	g.cleared_stages.append(201);check(not g.allowed_world_nodes().has(19),"F21 win alone waits for route confirmation")
	g.flags.F21_confirmed=true;check(g.allowed_world_nodes().has(19) and not g.allowed_world_nodes().has(33),"F21 confirmation opens main route before optional invitation")
	g.flags.S21_invited=true;check(g.allowed_world_nodes().has(33),"fishing invitation opens optional rescue")
	g.cleared_stages.append(202);g.flags.F22_confirmed=true;g.cleared_stages.append(203);g.flags.F23_confirmed=true;g.flags.S22_invited=true
	check(g.allowed_world_nodes().has(21) and g.allowed_world_nodes().has(34),"reef confirmation opens lighthouse and cave")
	g.cleared_stages.append(204);check(not g.allowed_world_nodes().has(22),"lighthouse victory waits for islanders settlement")
	g.flags.islanders_settled=true;g.cleared_stages.append(205);g.flags.sea_chart_collected=true
	check(not g.allowed_world_nodes().has(23),"chart alone waits for sidequest closure consent")
	g.flags.east_departure_confirmed=true;check(g.allowed_world_nodes().has(23) and not g.allowed_world_nodes().has(33) and not g.allowed_world_nodes().has(34),"ancient route opens and uncompleted sidequests close explicitly")
	check(not g.can_switch_route() and not g.allowed_world_nodes().has(24),"no third chapter or cross-route inventory access")
	check(g.save_game(),"schema-2 atomic save succeeds")
	var reloaded=State.new();reloaded.save_path=g.save_path
	check(reloaded.load_game() and reloaded.party==g.party and reloaded.roster==g.roster,"schema-2 reload keeps both actual armies")
	var base=State.read_json(g.save_path);var corruptions=[]
	var bad=base.duplicate(true);bad.chapter=3;corruptions.append(bad)
	bad=base.duplicate(true);bad.party.append("hunapu");corruptions.append(bad)
	bad=base.duplicate(true);bad.convoy.celica.append(-1);corruptions.append(bad)
	bad=base.duplicate(true);bad.roster.eileen.hp="invalid";corruptions.append(bad)
	bad=base.duplicate(true);bad.flags.active_plot={"pages":[],"index":0};corruptions.append(bad)
	bad=base.duplicate(true);bad.cleared_stages.append(999);corruptions.append(bad)
	for invalid in corruptions:
		var f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(JSON.stringify(invalid));f.close()
		var previous=reloaded.roster.duplicate(true)
		check(not reloaded.load_game() and reloaded.roster==previous,"malformed checkpoint rejected atomically")
	for id in [201,202,203,204,205,206,211,212]:
		var b=fixture(id);var slots={};var occupied={}
		for u in b.units:
			check(b.in_bounds(State.pos(u)) and b.movement_cost(u,State.pos(u))<255,str(id)+" legal deployment "+str(u.id))
			check(not occupied.has(State.pos(u)),str(id)+" unique starting cell "+str(u.id));occupied[State.pos(u)]=true
			if u.side=="player":check(not slots.has(int(u.player_slot)),str(id)+" nonoverlapping player/event slot "+str(u.id));slots[int(u.player_slot)]=true
		check(b.living("player").size()<=20 and b.living("enemy").size()<=20,str(id)+" original army limits")
		check(not b.objective_status().is_empty(),str(id)+" player-readable current objective")
		check(b.save_game(),str(id)+" tactical checkpoint saves")
		var resumed=State.new();resumed.save_path=b.save_path
		check(resumed.load_game() and resumed.units==JSON.parse_string(JSON.stringify(b.units)) and resumed.flags.quest==JSON.parse_string(JSON.stringify(b.flags.quest)),str(id)+" tactical and objective checkpoint reload")
		var eastern=b.find_unit("lisa");eastern.item_id=11;eastern.hp=0
		var before_west=b.convoy.alm.duplicate();var before_east=b.convoy.celica.size()
		b.Inventory.on_death(b,eastern,b.find_unit(str(b.battle_data.boss_id)))
		check(b.convoy.alm==before_west and b.convoy.celica.size()==before_east+1 and eastern.item_id==0,str(id)+" eastern casualty item returns to eastern convoy only")
		b.Inventory.on_death(b,eastern,{})
		check(b.convoy.celica.size()==before_east+1,str(id)+" death item cannot duplicate")
		check(b.retry_battle() and int(b.find_unit("lisa").hp)>0 and b.convoy.celica.size()==before_east,str(id)+" retry restores party death items and objectives")
		if id==201:
			b.find_unit("friendly_ship").hp=0;check(b.check_outcome()=="defeat","ship destruction fails even with hero alive");b.retry_battle();boss_dead(b)
		elif id==202:
			b.find_unit("lord").hp=0;b.story_on_death(b.find_unit("lord"));check(b.check_outcome().is_empty(),"optional Lord death leaves main rescue possible")
			interact(b,"prison_door");evacuate(b,["prisoners_0","prisoners_1","prisoners_2"]);boss_dead(b)
		elif id==203:
			boss_dead(b);check(b.check_outcome().is_empty(),"reef boss death alone does not replace full monster clear");all_dead(b)
		elif id==204:
			boss_dead(b);b.turn=5;check(b.check_outcome().is_empty(),"lighthouse cannot finish before turn six");b.turn=6;b.phase="enemy";check(b.check_outcome().is_empty(),"lighthouse waits for sixth player phase");b.phase="player"
		elif id==205:
			boss_dead(b);check(b.check_outcome().is_empty(),"Pesa defeat does not auto-open prison or collect box");interact(b,"pilot_prison");interact(b,"myth_box")
		elif id==206:
			boss_dead(b);check(b.check_outcome().is_empty(),"sea-pass boss defeat still waits for actual boat arrival")
			all_dead(b)
			for step in range(80):
				if not b.battle_outcome.is_empty():break
				b.next_phase()
			check(b.event_boats().any(func(boat):return boat.arrived),"event ship follows real water path and arrives through phase progression")
		elif id==211:
			boss_dead(b);check(b.check_outcome().is_empty(),"patients must reach safe mooring");evacuate(b,["patients0"]);check(b.check_outcome().is_empty(),"fishing rescue still requires remaining monsters cleared");all_dead(b)
		elif id==212:
			b.find_unit("old_sailor").hp=0;all_dead(b);interact(b,"relics")
		check(b.check_outcome()=="victory",str(id)+" complete explicit objective resolves")
		check(b.complete_battle(),str(id)+" settles victory once")
		var party_count=b.party.size();var rewards=b.convoy.duplicate(true);var roster=b.roster.duplicate(true)
		check(not b.complete_battle() and b.convoy==rewards and b.roster==roster,str(id)+" repeat settlement produces no reward")
		check(b.party.size()==party_count,str(id)+" victory never silently recruits an NPC")
		if id==202:
			b.recruit("lord");check(not b.party.has("lord") and b.roster.lord.dead,"dead optional recruit cannot resurrect in hub")
		if id==212:check(not b.flags.sailor_rescued and not b.flags.carlo_promise_completed,"dead sailor records lost promise while main side clear succeeds")
		check(b.save_game(),str(id)+" settled victory checkpoint saves")
		resumed=State.new();resumed.save_path=b.save_path;check(resumed.load_game(),str(id)+" settled victory checkpoint reloads")
	for reward_spec in [[202,49],[204,2],[211,4],[212,49]]:
		var loot=fixture(reward_spec[0]);var carrier=loot.find_unit(str(loot.battle_data.boss_id));var hero=loot.find_unit("eileen")
		check(int(carrier.item_id)==int(reward_spec[1]),str(loot.stage_id)+" exact documented carried reward")
		# Boundary fixture: force the successful roll, not a guaranteed drop rule.
		loot.rng_state=201
		hero.item_id=16;carrier.hp=0;var reward=loot.Inventory.on_death(loot,carrier,hero)
		check(reward.get("destination","")=="pending" and loot.flags.pending_loot.size()==1,str(loot.stage_id)+" full hand opens explicit loot choice")
		check(loot.Inventory.on_death(loot,carrier,hero).is_empty() and loot.flags.pending_loot.size()==1,str(loot.stage_id)+" no repeated boss drop")
		var western_items=loot.convoy.alm.duplicate();check(loot.Inventory.resolve_loot(loot,"store") and loot.convoy.celica.has(reward_spec[1]) and loot.convoy.alm==western_items,str(loot.stage_id)+" loot stored only in east convoy")
		check(loot.retry_battle() and int(loot.find_unit(str(loot.battle_data.boss_id)).item_id)==int(reward_spec[1]) and not loot.convoy.celica.has(reward_spec[1]),str(loot.stage_id)+" retry reverses exact item transfer")
	var ship_hit=fixture(206);var boat_before=int(ship_hit.flags.quest.boats[0].hp);var shooter=ship_hit.find_unit(str(ship_hit.battle_data.boss_id));var boat_at=Vector2i(ship_hit.flags.quest.boats[0].position[0],ship_hit.flags.quest.boats[0].position[1]);shooter.position=[boat_at.x+1,boat_at.y];ship_hit.turn=int(ship_hit.flags.quest.boats[0].get("delay",0))+1;ship_hit.phase="enemy";ship_hit.next_phase()
	check(int(ship_hit.flags.quest.boats[0].hp)<boat_before,"enemy in actual attack range damages exposed event boat")
	check(ship_hit.save_game(),"event damage checkpoint saves");var ship_reload=State.new();ship_reload.save_path=ship_hit.save_path;check(ship_reload.load_game() and int(ship_reload.event_boats()[0].hp)==int(ship_hit.event_boats()[0].hp),"ship damage survives checkpoint resume")
	var snapshot=State.read_json(ship_hit.save_path);snapshot.flags.quest.boats[0].speed=99;var badfile=FileAccess.open(ship_hit.save_path,FileAccess.WRITE);badfile.store_string(JSON.stringify(snapshot));badfile.close();check(not ship_reload.load_game(),"tampered ship movement contract rejected")
	for spec in [[202,"prison_door",["prisoners_0","prisoners_1","prisoners_2","lord"]],[212,"hideout",["old_sailor","wounded"]]]:
		var rescued=fixture(spec[0]);all_dead(rescued);interact(rescued,spec[1])
		for id in spec[2]:
			var escorted=rescued.find_unit(id);var exit_cell=Vector2i(rescued.battle_data.exit[0],rescued.battle_data.exit[1])
			check(not escorted.locked and rescued.reachable(escorted,true).costs.has(exit_cell),str(rescued.stage_id)+" opened rescue has actual reachable exit: "+str(id))
			for step in range(100):
				if rescued.flags.quest.evacuated.has(id):break
				escorted.acted=false;var action=rescued.ai_action(escorted);var path=rescued.path_to(escorted,action.destination)
				check(not path.is_empty(),str(rescued.stage_id)+" escorted movement uses a real legal path")
				escorted.position=[action.destination.x,action.destination.y];rescued.mark_wait(id)
			check(rescued.flags.quest.evacuated.has(id),str(rescued.stage_id)+" escort naturally walks to shared exit: "+str(id))
	var bridge=fixture(202);var cells=bridge.battle_data.objects[1].opens;var foot=bridge.find_unit("carlo")
	check(cells.any(func(p):return bridge.movement_cost(foot,Vector2i(p[0],p[1]))>=255),"reserve gangplank contains an impassable water gap before lever")
	interact(bridge,"reserve_bridge");check(cells.all(func(p):return bridge.movement_cost(foot,Vector2i(p[0],p[1]))<255),"lever creates actual continuous foot-passable gangplank")
	var assault=fixture(204);var beacon_at=Vector2i(assault.battle_data.targets[0][0],assault.battle_data.targets[0][1]);var seizure=assault.find_unit("F24_e4")
	check(seizure.get("objective_role","")=="seize_beacon" and assault.reachable(seizure,true).costs.has(beacon_at),"beacon assault unit has an actual ground route")
	# Isolate destination choice from combat targeting while retaining every wall/water cell.
	for unit in assault.units:
		if unit.id!=seizure.id:unit.hp=0
	for step in range(60):
		if State.pos(seizure)==beacon_at:break
		seizure.acted=false;var action=assault.ai_action(seizure);var path=assault.path_to(seizure,action.destination)
		check(not path.is_empty(),"beacon attacker travels by ordinary reachable path")
		seizure.position=[action.destination.x,action.destination.y]
	check(State.pos(seizure)==beacon_at,"beacon assault AI reaches and holds target instead of chasing an absent unit")
	var magic=fixture(201);var healer=magic.find_unit("mireille");var patient=magic.find_unit("carlo");healer.position=[4,16];patient.position=[5,16];patient.hp=maxi(1,int(patient.max_hp)-5)
	var heal_spell=-1
	for spell in magic.Items.spells(healer):
		if magic.Items.spell(spell).get("action","")=="recover":heal_spell=spell;break
	check(heal_spell>=0,"eastern healer has original recovery spell")
	if heal_spell>=0:
		var before_hp=int(healer.hp);var before_patient=int(patient.hp);var effect=magic.use_support("mireille",heal_spell,"carlo")
		check(not effect.is_empty() and int(healer.hp)<before_hp and int(patient.hp)>before_patient,"renamed eastern healer pays actual HP to heal ally")
	var rein=fixture(202);rein.turn=4;rein.next_phase();var enemies=rein.units.size();rein.next_phase();rein.turn=4;rein.next_phase()
	check(rein.units.size()==enemies and rein.flags.quest.reinforced,"finite reinforcement cannot replay")
	var beacon=fixture(204);var enemy=beacon.find_unit(str(beacon.battle_data.boss_id));enemy.position=beacon.battle_data.targets[0].duplicate();beacon.turn=2
	beacon.next_phase();beacon.next_phase();check(beacon.battle_outcome.is_empty() and beacon.flags.quest.beacon_contested,"first completed enemy occupation gives one full round to reclaim")
	beacon.next_phase();beacon.next_phase();check(beacon.battle_outcome=="defeat","unbroken full-round lighthouse occupation fails")
	var reclaimed=fixture(204);enemy=reclaimed.find_unit(str(reclaimed.battle_data.boss_id));enemy.position=reclaimed.battle_data.targets[0].duplicate();reclaimed.turn=2;reclaimed.next_phase();reclaimed.next_phase();enemy.hp=0;reclaimed.check_outcome();reclaimed.next_phase();reclaimed.next_phase()
	check(reclaimed.battle_outcome.is_empty() and not reclaimed.flags.quest.beacon_contested,"reclaiming beacon clears pending occupation failure")
	var done=fixture(206);all_dead(done)
	for step in range(80):
		if not done.battle_outcome.is_empty():break
		done.next_phase()
	done.complete_battle();var inventory=done.convoy.duplicate(true);var growth=done.roster.duplicate(true)
	check(done.finish_chapter_two() and done.mode=="chapter_end" and done.chapter==2 and done.world_node==6 and done.route_positions.celica==6 and done.allowed_world_nodes()==[6],"chapter-two finale arrives at Strait City and stops before chapter three")
	check(done.convoy==inventory and done.roster==growth and not done.finish_chapter_two(),"captivity neither confiscates growth/items nor repeats completion")
	var report={"scope":"Directed objective/save/retry fixtures, not natural play victories","checks":checks.size(),"errors":errors,"passed":errors.is_empty()}
	var f=FileAccess.open("res://reports/chapter2/state-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("CHAPTER2_STATE ",JSON.stringify(report));quit(0 if errors.is_empty() else 1)
