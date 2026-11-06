extends SceneTree
const State=preload("res://core/game_state.gd")
const Map=preload("res://core/map_skills.gd")
const Strong=preload("res://core/strong_body.gd")
const Items=preload("res://core/item_rules.gd")
const Rules=preload("res://core/combat_rules.gd")
const Stats=preload("res://core/equipment_comparison.gd")
const OUT="res://reports/healer-map-20261104/"
var checks=[]
var errors=[]
var timings=[]
var audio_errors=[]
var ui
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g=State.new();g.new_game();g.save_path="/private/tmp/revenge-healer-map-20261104/check.json";g.world_node=3;g.start_battle(102);g.story_events.clear();return g
func fixture(advanced=false):
	var g=fresh();var caster=g._initial_character("celine" if advanced else "fula")
	caster.side="player";caster.acted=false;caster.position=[6,10];caster.no_experience=true;caster.item_id=0
	caster.strength=9;caster.max_hp=32;caster.hp=32;caster.move=4;Map.clear(caster)
	var target=g._initial_character("hunapu");target.side="player";target.acted=false;target.position=[10,10];target.hp=1;target.item_id=0
	var friend=g._initial_character("otto");friend.side="player";friend.acted=false;friend.position=[10,11];friend.hp=1;friend.item_id=0
	var foe=g.find_unit("M12_boss").duplicate(true);foe.position=[11,10];foe.item_id=0;foe.strength=25;foe.class_id=6
	g.units=[caster,target,friend,foe];g.party=[caster.id,target.id,friend.id];g.selected_id=caster.id;g.cursor=g.pos(target);g.move_origin=g.pos(caster)
	return g
func domain():
	for advanced in [false,true]:
		var g=fixture(advanced);var a=g.units[0];var t=g.units[1];var neighbour=g.units[2];var id=str(a.id);var spec=Map.profile(a)
		check(Map.eligible(a) and spec.support and spec.reach==(10 if advanced else 8),"class eligibility and reach "+id)
		for who in ["fula","mireille","celine"]:
			var member=g._initial_character(who);member.side="player"
			check(Map.eligible(member),"all named friendly healer/saint eligible "+who)
		var enemy=a.duplicate(true);enemy.side="enemy";check(not Map.eligible(enemy),"enemy healers get no player MAP")
		var initial=g.units.duplicate(true);var rng=g.rng_state;var plan=Map.preview(g,id,g.pos(t))
		check(plan.valid and g.units==initial and g.rng_state==rng,"pure forecast "+id)
		for distance in [int(spec.reach),int(spec.reach)+1]:
			t.position=[6+distance,10];check(Map.preview(g,id,g.pos(t)).valid==(distance==int(spec.reach)),"inclusive Manhattan distance "+id+"/"+str(distance))
		t.position=[10,10]
		for invalid in [g.pos(a),g.pos(g.units[3]),Vector2i(8,10)]:
			initial=g.units.duplicate(true);check(not Map.apply(g,id,invalid).valid and initial==g.units,"invalid self/enemy/empty is atomic "+id+str(invalid))
		for flag in ["neutral","event_object","dead","hidden","escaped","retreated"]:
			t[flag]=true;check(not Map.preview(g,id,g.pos(t)).valid,"reject invalid recipient "+flag);t.erase(flag)
		t.hp=0;check(not Map.preview(g,id,g.pos(t)).valid,"no resurrection");t.hp=1
		for tier in range(3):
			a.acted=false;a.hp=a.max_hp;t.hp=1;g.selected_id=id;var before=int(a.hp);var other=int(neighbour.hp)
			plan=Map.preview(g,id,g.pos(t));var receipt=Map.apply(g,id,g.pos(t))
			check(receipt.valid and receipt.targets.size()==1 and Map.used(a)==tier+1 and a.acted,"single target/action/use "+id+str(tier))
			check(receipt.heal==9+([2,6,10] if advanced else [0,3,6])[tier] and int(t.hp)==1+int(receipt.heal),"tier heal uses raw strength "+id+str(tier))
			check(int(a.hp)==before-[0,5,8][tier] and int(receipt.cost)==[0,5,8][tier],"ceil HP cost "+id+str(tier))
			check(int(neighbour.hp)==other and not t.acted and not neighbour.has("strong_body_until_turn"),"no splash or target action consumption "+id+str(tier))
			check(Strong.remaining(t,g.turn)==2 and Items.physical_defence_bonus(t)==2,"refresh strong body +2 only "+id+str(tier))
			initial=g.units.duplicate(true);check(not Map.apply(g,id,g.pos(t)).valid and initial==g.units,"double confirm rejected "+id+str(tier))
		a.acted=false;check(not Map.preview(g,id,g.pos(t)).valid,"no fourth use "+id)
		check(a.has("map_move_penalty_until_turn") and not a.has("map_fatigue_until_turn") and Items.movement(a)==2,"third use gives only movement penalty "+id)
		var plain=a.duplicate(true);plain.erase("map_move_penalty_until_turn")
		check(Rules.attack_stats(a,g.units[3],0).damage==Rules.attack_stats(plain,g.units[3],0).damage,"movement cost does not weaken attacks "+id)
		Map.expire_after_player_phase(g);check(a.has("map_move_penalty_until_turn"),"penalty survives cast phase")
		g.phase="enemy";g.turn+=1;Map.expire_after_player_phase(g);check(a.has("map_move_penalty_until_turn"),"penalty survives enemy phase")
		g.phase="player";Map.expire_after_player_phase(g);check(not a.has("map_move_penalty_until_turn"),"penalty clears next player end")
	var g=fixture();var a=g.units[0];var t=g.units[1]
	a.map_uses=1;a.hp=5;var before=g.units.duplicate(true)
	check(not Map.apply(g,a.id,g.pos(t)).valid and before==g.units,"cost cannot kill caster")
	a.hp=6;check(Map.apply(g,a.id,g.pos(t)).valid and int(a.hp)==1,"cost may leave exactly 1 HP")
	g=fixture();a=g.units[0];t=g.units[1];a.no_experience=false;a.exp=0;t.hp=t.max_hp
	var r=Map.apply(g,a.id,g.pos(t));check(r.valid and r.targets[0].heal==0 and r.reward.is_empty() and Strong.bonus(t)==2,"full HP can gain buff without EXP")
	a.acted=false;before=g.units.duplicate(true);check(not Map.apply(g,a.id,g.pos(t)).valid and before==g.units,"full HP plus current full buff consumes nothing")
	g.turn+=1;check(Map.apply(g,a.id,g.pos(t)).valid and Strong.remaining(t,g.turn)==2,"remaining one refreshes to two without stacking")
	g=fixture();a=g.units[0];t=g.units[1];a.no_experience=false;a.exp=0
	var expected=Rules.healing_experience_gain(a,9);r=Map.apply(g,a.id,g.pos(t))
	check(r.reward.gain==expected and int(a.exp)==expected,"one normal healing EXP reward")
	for held in [0,48,51,53,59]:
		t.item_id=held;Strong.clear(t);var equipped=Items.physical_defence_bonus(t,g.units[3]);var base=Stats.stats(t).defence;var defence=int(t.defence)
		var physical=Rules.attack_stats(g.units[3],t,0).damage;var mr=Items.magic_defence(t)
		Strong.apply(t,g.turn)
		check(Items.physical_defence_bonus(t,g.units[3])==equipped+2 and Stats.stats(t).defence==base+2 and int(t.defence)==defence,"equipment and status DEF stack, base stays unchanged "+str(held))
		check(Rules.attack_stats(g.units[3],t,0).damage==maxi(1,physical-2) and Items.magic_defence(t)==mr,"physical takes effect, magic unaffected "+str(held))
	g=fixture();a=g.units[0];a.map_move_penalty_until_turn=2;a.map_fatigue_until_turn=2;a.move=2
	check(Items.movement(a)==1,"movement floor one and penalties do not subtract twice")
	g=fixture();a=g.units[0];t=g.units[1];a.map_uses=1;a.class_id=17
	check(Map.profile(a).advanced and Map.profile(a).tier==1 and Map.profile(a).heal==15,"promotion strengthens MAP without resetting allowance")
	var foe=g.units[3];foe.class_id=15;foe.weapon_index=24
	Strong.clear(t);var magic=Rules.attack_stats(foe,t,0).damage;Strong.apply(t,g.turn)
	check(Rules.attack_stats(foe,t,0).damage==magic,"actual offensive magic ignores strong body")
	a.class_id=21;a.item_id=14;a.luck=0;a.strength=20;Strong.clear(a)
	var recoil=Rules.strike_effect(a,foe,true,false,0,1,0).self_damage
	Strong.apply(a,g.turn)
	check(Rules.strike_effect(a,foe,true,false,0,1,0).self_damage==recoil-2,"physical devil sword recoil respects strong body")
	g=fixture();a=g.units[0];t=g.units[1]
	Strong.clear(t);var hero=g._initial_character("hunapu");hero.side="player";hero.acted=false;hero.position=[9,10];hero.item_id=0
	var victim=g.units[3];victim.position=[10,10];victim.side="enemy";victim.hp=50;victim.max_hp=50;victim.defence=1;g.units=[hero,victim]
	var damage=Map.preview(g,hero.id,Vector2i(10,10)).targets[0].damage;Strong.apply(victim,g.turn)
	check(Map.preview(g,hero.id,Vector2i(10,10)).targets[0].damage==maxi(1,damage-2),"physical protagonist MAP shares strong body defence")

func phase_and_saves():
	var g=fresh();var a=g.find_unit("fula");var t=g.find_unit("hunapu")
	Strong.apply(t,g.turn);a.map_move_penalty_until_turn=g.turn+1;a.map_uses=3
	g.next_phase();check(g.phase=="enemy" and Strong.remaining(t,g.turn)==2 and Strong.bonus(t)==2,"buff protects cast turn enemy phase")
	g.next_phase();check(g.phase=="player" and Strong.remaining(t,g.turn)==1 and Strong.bonus(t)==2 and a.has("map_move_penalty_until_turn"),"buff one and movement penalty at next player start")
	check(g.save_game(),"active buff and movement checkpoint validates")
	var loaded=State.new();loaded.save_path=g.save_path
	var resumed=loaded.load_game()
	check(resumed and Strong.remaining(loaded.find_unit("hunapu"),loaded.turn)==1 and Map.used(loaded.find_unit("fula"))==3 and Items.movement(loaded.find_unit("fula"))==Items.movement(a),"save/load retains buff, count and movement")
	g.next_phase();check(Strong.bonus(t)==2 and not a.has("map_move_penalty_until_turn"),"second enemy phase still protected, caster movement recovers")
	g.next_phase();check(g.phase=="player" and Strong.bonus(t)==0 and not t.has("strong_body_until_turn"),"second next player start removes buff")
	check(g.battle_rewind.starts[-1].units.filter(func(u):return u.id=="hunapu")[0].get("strong_body_until_turn",0)==0,"rewind records after expiration")
	check(g.Rewind.commit(g) and g.turn==2 and Strong.remaining(g.find_unit("hunapu"),g.turn)==1 and Map.used(g.find_unit("fula"))==3,"rewind restores prior buff/cost/count together")
	check(g.Rewind.commit(g) and g.turn==1 and Strong.bonus(g.find_unit("hunapu"))==0 and Map.used(g.find_unit("fula"))==0,"rewind before cast removes all MAP state")
	loaded.retry_battle();check(Strong.bonus(loaded.find_unit("hunapu"))==0 and Map.used(loaded.find_unit("fula"))==0,"retry clears temporary state")
	g=fresh();t=g.find_unit("hunapu");Strong.apply(t,g.turn);t.map_move_penalty_until_turn=2;t.map_uses=3;g.Inventory._persist_participants(g)
	check(Strong.bonus(g.roster.hunapu)==0 and not g.roster.hunapu.has("map_move_penalty_until_turn") and not g.roster.hunapu.has("map_uses"),"retreat roster excludes temporary state")
	for field in ["map_uses","strong_body_until_turn","map_move_penalty_until_turn"]:
		for value in [-1,"bad",4 if field=="map_uses" else 2147483648]:
			var bad=t.duplicate(true);bad[field]=value;check(not g.SaveValidation._unit(bad,true),"reject malformed optional status "+field+str(value))
	var valid=g.Rewind._capture(g);valid.battle_start_snapshot=g.battle_start_snapshot
	for field in ["map_uses","strong_body_until_turn","map_move_penalty_until_turn"]:
		var bad=valid.duplicate(true);bad.units[0][field]="bad"
		check(not g.SaveValidation.campaign_valid(g,bad,g.SAVE_FIELDS),"actual campaign loader rejects malformed "+field)
	Map.clear(t);check(g.SaveValidation._unit(t,true),"old save without optional MAP fields remains valid")
	var fixture_path="res://reports/campaign-final-r1/ch1/chain-M13-victory.json"
	if FileAccess.file_exists(fixture_path):
		g=State.new();g.save_path=fixture_path
		check(g.load_game(),"training origin loads")
		g.save_path="/private/tmp/revenge-healer-map-20261104/training.json"
		check(g.Training.start(g,191),"start actual training")
		t=g.living("player")[0];Strong.apply(t,g.turn);g.next_phase();g.next_phase();check(Strong.remaining(t,g.turn)==1,"training countdown one")
		g.next_phase();g.next_phase();check(Strong.bonus(t)==0,"training expiration uses same phase hook")
func interface():
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	ui.audio.playback_failed.connect(func(key,reason):audio_errors.append([key,reason]))
	var stream=ui.audio._get_stream("sfx","rm_sfx_21");check(stream!=null and stream.get_length()>0,"confirmed recovery sound loads")
	for advanced in [false,true]:
		ui.game=fixture(advanced);ui.view="battle";ui.busy=false;ui.notice_time=0;ui.phase_time=0
		ui._unit_action_menu();check(ui.menu_actions.has("map:choose"),"healer action menu includes MAP")
		ui._choose_map_skill();check(ui.ui_mode=="map_target" and ui.hero_map_animation.forecast.valid,"auto-select legal ally")
		var before=ui.game.units.duplicate(true);ui._cancel();check(before==ui.game.units and ui.ui_mode=="action","cancel targeting costs nothing")
		ui._choose_map_skill();ui.game.cursor=ui.game.pos(ui.game.units[1]);ui._refresh_map_forecast();await ui._play_map_skill()
		var audit=ui.hero_map_animation.audit;check(audit.contacts.size()==1 and audit.sounds.size()==1 and audit.sounds[0].key=="rm_sfx_21","one healing contact and recovery cue")
		check(not ui.busy and not ui.hero_map_animation.active and ui.map_actor_alpha.is_empty() and ui.view=="battle","short presentation returns control and restores masks")
	ui.instant_mode=false;ui.animation_speed=1.
	for advanced in [false,true]:
		ui.game=fixture(advanced);ui.view="battle";ui.busy=false;ui.game.cursor=ui.game.pos(ui.game.units[1])
		var start=Time.get_ticks_usec();await ui._play_map_skill();var wall=float(Time.get_ticks_usec()-start)/1000000.
		var planned=1.4 if advanced else 1.2;timings.append({"key":"saint" if advanced else "healer","planned":planned,"actual":wall})
		check(wall>=planned-.03 and wall<=planned+.15,"real play has no leading/trailing waits "+str(advanced))
	check(audio_errors.is_empty(),"real recovery sound plays without errors")
	ui.audio.stop_all();ui.queue_free();ui=null;await process_frame;await process_frame
func run():
	DirAccess.make_dir_recursive_absolute("/private/tmp/revenge-healer-map-20261104")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	domain();phase_and_saves();await interface()
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"count":checks.size(),"errors":errors,"checks":checks,"timings":timings},"\t"));f.close()
	print("HEALER_MAP_CHECKS=",checks.size()," ERRORS=",errors.size());quit(0 if errors.is_empty() else 1)
