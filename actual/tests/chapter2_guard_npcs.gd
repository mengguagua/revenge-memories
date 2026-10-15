extends SceneTree
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func fixture(stage: int):
	var g=State.new();g.save_path="res://reports/campaign/natural-chapter-end-save.json";check(g.load_game(),"actual west completion loads")
	check(g.begin_chapter_two(),"east party initializes normally");g.world_node=int(g.stages[stage].node);check(g.start_battle(stage),"current guard stage starts");return g
func run() -> void:
	for spec in [[203,"roan"],[204,"shia"]]:
		var g=fixture(spec[0]);var guard=g.find_unit(spec[1]);var original=g.characters[spec[1]];var start=State.pos(guard)
		check(guard.get("battle_guard",false) and not guard.get("no_counter",true),str(spec[1])+" is a combat-capable volunteer guard")
		check(guard.get("neutral",false) and not guard.get("controllable",true) and guard.get("no_experience",false),str(spec[1])+" stays non-player-controlled and unrecruited")
		for field in ["hp","max_hp","strength","defence","resistance","speed","skill","luck","move","class_id","item_id","level"]:
			check(guard[field]==original[field],str(spec[1])+" original character attribute unchanged: "+field)
		var waiting=g.ai_action(guard)
		check(waiting.destination==start and str(waiting.target).is_empty(),str(spec[1])+" stays at assigned post without a target")
		var enemy=g.living("enemy")[1];var valid=Vector2i(-1,-1)
		for d in g.DIRECTIONS:
			var at=start+d
			if g.in_bounds(at) and g.movement_cost(enemy,at)<255 and g.unit_at(at).is_empty():valid=at;break
		check(valid!=Vector2i(-1,-1),str(spec[1])+" has legal adjacent test ground")
		enemy.position=[valid.x,valid.y]
		var defending=g.ai_action(guard)
		check(defending.destination==start and not str(defending.target).is_empty(),str(spec[1])+" selects in-range enemy without pursuit")
		check(int(guard.move)==int(original.move),str(spec[1])+" guard AI never rewrites movement attribute")
		check(g.Rules.can_attack(guard,1) and g.Rules.strike_sequence(enemy,guard,1).has("defender"),str(spec[1])+" responds through ordinary counterattack rules")
		var before_exp=int(guard.get("exp",0));var exchange=g.plan_combat(str(guard.id),str(defending.target))
		check(not exchange.is_empty(),str(spec[1])+" ordinary weapon exchange is valid")
		for event in exchange.get("events",[]):g.commit_strike(event)
		g.finish_exchange(exchange)
		check(guard.acted and int(guard.get("exp",0))==before_exp,str(spec[1])+" one normal action and no pre-recruit growth")
		check(not g.party.has(str(guard.id)),str(spec[1])+" combat never auto-recruits")
		g.ChapterTwo.on_victory(g)
		check(g.flags.east_recruit_ready.get(str(guard.id),false) and not g.party.has(str(guard.id)),str(spec[1])+" living guard earns only post-battle invitation eligibility")
		var casualty=fixture(spec[0]);var fallen=casualty.find_unit(spec[1]);fallen.hp=0;casualty.story_on_death(fallen);casualty.ChapterTwo.on_victory(casualty);casualty.recruit(str(fallen.id))
		check(casualty.roster[str(fallen.id)].dead and not casualty.flags.east_recruit_ready.get(str(fallen.id),false) and not casualty.party.has(str(fallen.id)),str(spec[1])+" guard death remains permanent and cannot be recruited")
		var civilian=g.find_unit("fishers" if spec[0]==203 else "islanders")
		var civilian_action=g.ai_action(civilian)
		check(civilian.get("no_counter",false) and civilian_action.destination==State.pos(civilian) and str(civilian_action.target).is_empty(),"ordinary civilians retain noncombatant behavior")
	var report={"scope":"Directed original-stat guard/counter/idle checks; targeted enemy adjacency fixtures, not natural play victories","checks":checks.size(),"passed":failures.is_empty(),"failures":failures}
	var f=FileAccess.open("res://reports/chapter2/guard-npc-check.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("GUARD_NPC ",JSON.stringify(report));quit(0 if failures.is_empty() else 1)
