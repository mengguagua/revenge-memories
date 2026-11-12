extends SceneTree
const State=preload("res://core/game_state.gd")
const ENTRY="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-S21-deployment.json"
const SCRATCH="/private/tmp/s21-patient-rescue-20261110/"
var failures: Array[String]=[]

func _initialize() -> void:
	call_deferred("run")

func check(ok:bool,message:String) -> void:
	if not ok:
		failures.append(message)
		push_error(message)

func deployment():
	var g=State.new()
	g.save_path=ENTRY
	check(g.load_game(),"genuine S21 deployment loads")
	g.save_path=SCRATCH+"working.json"
	check(g.retry_battle(),"retry uses the current S21 deployment")
	return g

func arrive(g,id:String) -> void:
	var patient=g.find_unit(id)
	patient.position=g.battle_data.exit.duplicate()
	g.mark_wait(id)

func clear_monsters(g) -> void:
	for enemy in g.living("enemy"):enemy.hp=0

func check_boss_pursuit() -> void:
	var g=State.new()
	g.save_path=ENTRY
	check(g.load_game(),"an existing S21 deployment loads")
	g.save_path=SCRATCH+"working.json"
	var boss=g.find_unit("S21_boss")
	var origin=g.pos(boss)
	var pursuit=g.ai_action(boss)
	check(boss.get("guard_alerted",false) and pursuit.destination!=origin,"an unhurt boss advances on the existing map")
	check(g.path_to(boss,pursuit.destination).size()>1,"the boss uses a legal movement path")

	g=deployment()
	for saved in g.battle_start_snapshot.units:
		if saved.id=="S21_boss":saved.guard_alerted=false
	check(g.retry_battle(),"S21 retries from an old saved boss configuration")
	boss=g.find_unit("S21_boss")
	origin=g.pos(boss)
	check(boss.get("guard_alerted",false),"retry restores the pursuing boss")
	var target=g.find_unit("eileen")
	target.position=[23,9]
	g.phase="enemy"
	pursuit=g.ai_action(boss)
	check(pursuit.destination!=origin and pursuit.target=="eileen","the boss chooses to move and attack in the same turn")
	var path=g.path_to(boss,pursuit.destination)
	check(path.size()>1,"the attacking destination is reachable")
	if path.size()>1 and pursuit.target=="eileen":
		boss.position=[pursuit.destination.x,pursuit.destination.y]
		var exchange=g.plan_combat(str(boss.id),str(target.id))
		check(g.Rules.weapon_index(boss)==g.Rules.Body.STONE_SPIT and not exchange.get("events",[]).is_empty(),"the attack uses the existing stone-spit profile")
	check(g.Rules.attack_range(g.Rules.default_counter(boss,3)).y==3,"the existing three-tile counter is preserved")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(SCRATCH)
	check_boss_pursuit()
	var g=deployment()
	check(g.pos(g.find_unit("patients0"))==Vector2i(18,16),"first patient starts on right deck")
	check(g.pos(g.find_unit("patients1"))==Vector2i(18,18),"second patient starts at the lower right gangway")
	for id in ["patients0","patients1"]:
		var patient=g.find_unit(id)
		check(int(patient.speed)==5 and int(patient.defence)==4 and int(patient.strength)==2 and int(patient.move)==3 and patient.no_counter,"sick patient has the configured combat and movement stats: "+id)
		var action=g.ai_action(patient)
		var path=g.path_to(patient,action.destination)
		check(action.target=="" and path.size()==4 and action.destination.x<g.pos(patient).x,"patient moves three tiles toward shore with monsters present: "+id)
		var foe=g.find_unit("S21_e3")
		foe.position=[19,16] if id=="patients0" else [19,18]
		action=g.ai_action(patient)
		check(action.target=="" and action.destination!=g.pos(patient),"adjacent enemy does not stop evacuation or prompt an attack: "+id)
	clear_monsters(g)
	var active=g.find_unit("patients0")
	var action=g.ai_action(active)
	check(int(active.move)==3 and g.path_to(active,action.destination).size()==4,"clearing the last monster does not give an extra move")

	check(not g.ChapterTwo.can_finish_s21_early(g) and g.check_outcome().is_empty(),"clear field without an evacuation cannot win")
	arrive(g,"patients0")
	check(g.battle_outcome.is_empty() and g.ChapterTwo.can_finish_s21_early(g),"one rescue can finish now or wait for the second")
	check(g.ChapterTwo.finish_s21_early(g) and g.complete_battle(),"one rescue can win without the second")
	check(not g.flags.get("S21_full_rescue_reward",false) and not g.victory_rewards.any(func(r):return r.has("s21_full_rescue_bonus")),"one rescue earns no double-rescue EXP")

	g=deployment()
	clear_monsters(g)
	g.find_unit("patients1").hp=0
	arrive(g,"patients0")
	check(g.battle_outcome=="victory" and g.complete_battle(),"one rescued patient wins automatically when the other dies")
	g=deployment()
	for id in ["patients0","patients1"]:g.find_unit(id).hp=0
	check(g.check_outcome()=="defeat","losing both patients still fails")

	g=deployment()
	clear_monsters(g)
	g.units=g.units.filter(func(u):return u.id!="lord")
	g.roster.lord.exp=90
	g.roster.lord.hp=0
	g.roster.lord.dying=true
	g.roster.lord.ever_dying=true
	g.find_unit("carlo").level=20
	arrive(g,"patients1")
	arrive(g,"patients0")
	check(g.battle_outcome=="victory" and g.complete_battle(),"two rescues win automatically")
	var extras=g.victory_rewards.filter(func(r):return r.has("s21_full_rescue_bonus"))
	var members=extras.map(func(r):return r.unit)
	var expected=g.party.filter(func(id):return id!="carlo")
	check(members==expected and extras.all(func(r):return int(r.gain)==20),"double rescue grants exactly 20 extra XP to each eligible east-team member")
	check("lord" in members and int(g.roster.lord.exp)==10 and int(g.roster.lord.hp)==0,"a reserve can level from the reward without being revived")
	check(not g.complete_battle(),"settlement cannot pay twice")
	g.mode="victory"
	check(g.save_game(),"settled result saves")
	var restored=State.new()
	restored.save_path=g.save_path
	check(restored.load_game() and not restored.complete_battle() and restored.flags.get("S21_full_rescue_reward",false),"restored result keeps its one-time reward")

	print("S21 PATIENT RESCUE ", "PASS" if failures.is_empty() else failures)
	quit(0 if failures.is_empty() else 1)
