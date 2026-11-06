extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Mechanical=preload("res://core/mechanical_puppets.gd")
const Art=preload("res://core/mechanical_art.gd")
const FIXTURE="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F21-deployment.json"
const OUT="res://reports/mechanical-puppets-20261104/logic-checks.json"
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(value:bool,label:String):
	checks.append(label)
	if not value:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.save_path=FIXTURE
	check(g.load_game(),"Existing real F21 checkpoint loads")
	check(not g.units.any(func(u):return Mechanical.is_puppet(u)),"Old ongoing F21 is not injected mid-battle")
	g.save_path="/private/tmp/revenge-mechanical-test.json"
	check(g.start_battle(201),"Ordinary fresh F21 redeploys authored enemies")
	return g
func arrange(g,distance:int=2):
	var enemy=g.find_unit("F21_water_monkey_1");var player=g.find_unit("eileen")
	player.position=[21-distance,14];enemy.position=[21,14]
	player.hp=52;player.max_hp=52;player.speed=6;player.defence=8;player.resistance=8
	player.strength=8;player.skill=40;player.luck=0;player.acted=false;player.weapon_index=23
	enemy.acted=false;g.rng_state=0;g.battle_outcome=""
	return [player,enemy]
func run():
	var g=fresh();var enemy=g.find_unit("F21_water_monkey_1")
	check(g.battle_data.enemies.size()==10,"F21 adds exactly one puppet, retaining nine enemies")
	check(enemy.class_id==25 and g.pos(enemy)==Vector2i(21,14) and enemy.hp==22 and Mechanical.cannon_hp(enemy)==10,"Independent class, approved location, body and part HP")
	check(Rules.weapon_index(Rules.attack_context(enemy,1))==1007,"Adjacent default is palm")
	for distance in [2,3]:
		var actor=Rules.attack_context(enemy,distance)
		check(Rules.can_attack(actor,distance) and Rules.weapon_index(actor)==1008,"Water cannon actual range "+str(distance))
	check(not Rules.can_attack(enemy,4),"Water cannon cannot hit range4")
	check(Rules.attack_speed(Rules.attack_context(enemy,1))==8 and Rules.attack_speed(Rules.attack_context(enemy,2))==3,"Palm and water have approved different attack speeds")
	var a=arrange(g);var player=a[0];enemy=a[1];player.strength=40
	var units_before=JSON.stringify(g.units)
	var plan=g.plan_combat(str(player.id),str(enemy.id),Mechanical.PART)
	check(not plan.is_empty() and not plan.events.is_empty(),"Part target produces real combat plan")
	check(JSON.stringify(g.units)==units_before,"Planning does not mutate live body, part or state")
	check(plan.events[0].part_hp_after==0 and plan.events[0].hp_after==22,"Part damage capped independently without spill to body")
	check(plan.events.all(func(e):return str(e.attacker)!=str(enemy.id)),"First-hit part break cancels same-exchange ranged counter")
	check(plan.events.filter(func(e):return e.attacker==player.id).size()==1,"Follow-up does not retarget destroyed part")
	var kills=g.kills
	for event in plan.events:g.commit_strike(event)
	check(enemy.hp==22 and Mechanical.cannon_hp(enemy)==0 and g.kills==kills,"Part break does not kill or add kill count")
	check(not g.flags.get("inventory_processed_deaths",{}).has(str(enemy.id)),"Part break does not trigger death loot")
	check(not Rules.can_attack(enemy,2) and Rules.can_attack(enemy,1),"Broken cannon disables ranged attack, preserves palm")
	var reward=g.finish_exchange(plan)
	check(not reward.is_empty() and reward.gain>0,"Part damage still earns finite damage experience")
	check(g.save_game(),"Part-damaged current save writes isolated file")
	var restored=State.new();restored.save_path=g.save_path
	check(restored.load_game(),"New mechanical save loads with strict validation")
	check(Mechanical.cannon_hp(restored.find_unit(str(enemy.id)))==0 and restored.find_unit(str(enemy.id)).hp==22,"Broken state survives save/reload")
	check(restored.retry_battle() and Mechanical.cannon_hp(restored.find_unit(str(enemy.id)))==10,"Retry restores actual initial part durability")
	var bad=State.read_json(g.save_path)
	for u in bad.units:
		if Mechanical.is_puppet(u):u.parts.back_cannon.hp=11
	var invalid=FileAccess.open("/private/tmp/revenge-mechanical-invalid.json",FileAccess.WRITE);invalid.store_string(JSON.stringify(bad));invalid.close()
	var before=JSON.stringify(restored.units);restored.save_path="/private/tmp/revenge-mechanical-invalid.json"
	check(not restored.load_game() and JSON.stringify(restored.units)==before,"Corrupt part state rejected atomically")
	g=fresh();a=arrange(g);player=a[0];enemy=a[1]
	var water=g.plan_combat(str(enemy.id),str(player.id))
	check(water.events.any(func(e):return e.attacker==enemy.id and e.weapon_index==1008 and e.water_slow_applied),"Real water hit carries slow effect")
	for event in water.events:g.commit_strike(event)
	check(player.get("water_slow",false) and Rules.Items.effective_speed(player)==5,"Water hit applies speed6→5")
	g.finish_exchange(water)
	check(player.get("water_slow",false),"Enemy ending action does not clear defender slow")
	enemy.acted=false;enemy.hp=22;player.hp=52;g.rng_state=0
	water=g.plan_combat(str(enemy.id),str(player.id))
	for event in water.events:g.commit_strike(event)
	check(Rules.Items.effective_speed(player)==5,"Repeated water hit never stacks speed penalty")
	player.acted=false;g.mark_wait(str(player.id))
	check(not player.has("water_slow") and Rules.Items.effective_speed(player)==6,"Slow expires after target's next action")
	player.water_slow=true;g._restore_preparation_hp()
	check(not player.has("water_slow"),"Preparation clears temporary water slow")
	var fractional=enemy.duplicate(true);fractional.mechanical_base_move=5.5
	check(not Mechanical.valid_unit(fractional),"Fractional base movement rejected by save validation")
	player.water_slow=true;player.acted=false;player.position=[14,11];g.selected_id=str(player.id)
	check(g.interact("plank_1") and not player.has("water_slow"),"F21 chapter interaction also ends temporary slow")
	player.water_slow=true;g.start_battle(201)
	check(not g.find_unit(str(player.id)).has("water_slow"),"Fresh deployment cannot carry battle-only slow")
	var ordinary=enemy.duplicate(true);ordinary.erase("unit_kind");ordinary.erase("mechanical_model");ordinary.class_id=6
	var novice={"class_id":14,"level":1,"hp":20}
	check(Rules.experience_gain(novice,ordinary,22,0,true)==35 and Rules.experience_gain(novice,enemy,22,0,true)==53,"Mechanical kill experience is ceil35×1.5=53")
	check(Rules.experience_gain(novice,enemy,22,16,false)==ceili(Rules.experience_gain(novice,ordinary,22,16,false)*1.5),"Damage experience uses same multiplier")
	g=fresh();enemy=g.find_unit("F21_water_monkey_1")
	for u in g.units:
		if u.side=="enemy" and not Mechanical.is_puppet(u):u.hp=0
	Mechanical.refresh(g)
	check(enemy.move==8 and enemy.mechanical_retreating,"Only-mechanical side gets move5+3")
	Mechanical.refresh(g);check(enemy.move==8,"Retreat bonus cannot stack")
	var move=g.ai_action(enemy)
	check(move.target=="" and move.destination==Vector2i(29,14),"First retreat chooses nearest east edge, travels8")
	check(g.path_to(enemy,move.destination).size()==9,"Retreat uses a real traversable eight-step path")
	enemy.position=[29,14];enemy.acted=false;move=g.ai_action(enemy)
	check(move.destination==Vector2i(31,14),"Second retreat reaches edge with remaining2")
	enemy.position=[31,14];Mechanical.refresh(g)
	check(enemy.escaped and enemy.hidden and enemy.hp==22 and g.kills==0,"Escape removes living unit without kill or death")
	check(g.living("enemy").is_empty() and g.unit_at(Vector2i(31,14)).is_empty(),"Escaped unit is not targetable or a blocker")
	check(g.flags.get("inventory_processed_deaths",{}).is_empty(),"Escape does not run death/drop callbacks")
	g=fresh();enemy=g.find_unit("F21_water_monkey_1")
	for u in g.units:
		if u.side=="enemy" and not Mechanical.is_puppet(u):u.hp=0
	Mechanical.refresh(g)
	var blocker=g.find_unit("eileen");blocker.position=[31,14];enemy.position=[30,14]
	move=g.ai_action(enemy)
	check(move.destination!=Vector2i(31,14) and not g.path_to(enemy,move.destination).has(Vector2i(31,14)),"Withdrawal reroutes instead of passing through occupied edge")
	var human=g.find_unit("F21_boss");human.hp=1;Mechanical.refresh(g)
	check(enemy.move==5 and not enemy.mechanical_retreating,"Non-mechanical reinforcements restore ordinary movement")
	human.hp=0;check(g.check_outcome()=="victory","F21 commander objective wins without chasing puppet")
	for key in Art.data().variants:
		var variant:Dictionary=Art.data().variants[key]
		for row in variant.frames:
			if int(row.frame)<0 or int(row.frame)>=int(Art.data().battle.frames):check(false,"Animation frame out of packed atlas: "+key)
	check(Art.data().variants.melee.frames.size()==219 and Art.data().variants["broken-melee"].frames.size()==219,"Both confirmed 219-frame melee programs packed")
	check(Art.data().variants.hit.frames.all(func(r):return r.frame==Art.data().idle_frames.intact),"Intact ordinary hit uses fixed pose")
	check(Art.data().variants["broken-hit"].frames.all(func(r):return r.frame==Art.data().idle_frames.broken),"Broken ordinary hit uses fixed broken pose")
	var scene=load("res://scenes/main.tscn");check(scene!=null,"Actual runtime scene and controller parse")
	var result={"checks":checks.size(),"passed":errors.is_empty(),"errors":errors,"labels":checks,"scope":"Real F21 checkpoint and ordinary controller/state APIs; controlled combat and withdrawal probes, not a natural full-map victory."}
	var out=FileAccess.open(OUT,FileAccess.WRITE);out.store_string(JSON.stringify(result,"\t"));out.close()
	print("MECHANICAL_CHECKS ",checks.size()," errors=",errors)
	quit(0 if errors.is_empty() else 1)
