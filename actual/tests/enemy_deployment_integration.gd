extends SceneTree
## Genuine deployment checkpoints, fresh authored deployment, isolated resume/retry.
## Combat probes relocate two actual units; they are not natural full-map play.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const CACHE="/private/tmp/revenge-enemy-integration-20261023/"
const OUT="res://reports/enemy-deployment-20261023/integration-checks.json"
const FIXTURES={
	"S11":"chapter1-climate-20261022/play/continuous-final/continuous-final-S11-deployment.json",
	"S21":"chapter2-environment-20261023/play/continuous-after-shore/continuous-after-shore-S21-deployment.json",
	"S22":"chapter2-environment-20261023/play/continuous-after-shore/continuous-after-shore-S22-deployment.json",
	"M32":"chapter3-environment-20261023/play/round2/round2-M32-deployment.json",
	"F32":"chapter3-environment-20261023/play/round2/round2-F32-deployment.json",
	"M33":"chapter3-environment-20261023/play/round2/round2-M33-deployment.json",
	"F33":"chapter3-environment-20261023/play/round2/round2-F33-deployment.json",
	"F42":"chapter4-redesign-20261022/play/continuous-final/continuous-final-F42-deployment.json",
	"F43":"chapter4-redesign-20261022/play/continuous-final/continuous-final-F43-deployment.json",
	"S42":"chapter4-redesign-20261022/play/continuous-final/continuous-final-S42-deployment.json",
	"J53":"chapter5-environment-20261023/play/final-round2/final-round2-J53-deployment.json",
	"J54":"chapter5-environment-20261023/play/final-round2/final-round2-J54-deployment.json",
}
const FIELDS=["class_id","character_id","source_enemy_character_id","item_id","body_attack","body_armour","recoverable_item_id","campaign_role","campaign_final_boss","no_drop"]
const NEW_CLASSES=[4,5,9,10,13,14,16,17,18,19,21]
var checks=[]
var errors=[]
var maps=[]
var combat=[]
var covered={}
func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE);call_deferred("run")
func check(value:bool,label:String):
	checks.append(label)
	if not value:errors.append(label);push_error(label)
func same_fields(actual:Dictionary,expected:Dictionary) -> bool:
	for field in FIELDS:
		if actual.get(field)!=expected.get(field):return false
	return true
func validate_units(g,code:String,context:String):
	for expected in g.stages[g.stage_id].enemies:
		var actual=g.find_unit(str(expected.id))
		check(not actual.is_empty() and same_fields(actual,expected),code+" "+context+" current enemy matches authored identity/attack/recovery/AI: "+str(expected.id))
		var snapshot=g.battle_start_snapshot.get("units",[]).filter(func(u):return u.id==expected.id)
		check(snapshot.size()==1 and same_fields(snapshot[0],expected),code+" "+context+" opening snapshot matches: "+str(expected.id))
func probe_combat(g,code:String,enemy_id:String,distance:int):
	var enemy=g.find_unit(enemy_id).duplicate(true)
	var target=g.find_unit(g.leader_id()).duplicate(true)
	if target.is_empty():check(false,code+" probe leader exists");return
	# Controlled positions retain actual stage terrain; no invented class/unit stat sheet.
	var destination=Vector2i(-1,-1)
	for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
		var cell=g.pos(enemy)+d*distance
		if g.in_bounds(cell) and g.movement_cost(target,cell)<255:destination=cell;break
	if destination==Vector2i(-1,-1):
		check(false,code+" controlled legal target location for "+enemy_id);return
	target.position=[destination.x,destination.y];target.hp=int(target.max_hp);target.acted=false
	enemy.hp=int(enemy.max_hp);enemy.acted=false
	g.units=[target,enemy];g.battle_outcome="";g.selected_id=""
	var plan=g.plan_combat(enemy_id,str(target.id))
	check(not plan.is_empty() and not plan.get("events",[]).is_empty(),code+" real plan_combat produces events for class "+str(enemy.class_id)+" at distance "+str(distance))
	if plan.is_empty():return
	var own=plan.events.filter(func(e):return e.attacker==enemy_id)
	check(not own.is_empty(),code+" new profession actually attacks: "+enemy_id+" distance "+str(distance))
	var positions={str(enemy.id):enemy.position.duplicate(),str(target.id):target.position.duplicate()}
	for event in plan.events:g.commit_strike(event)
	check(enemy.position==positions[str(enemy.id)] and target.position==positions[str(target.id)],code+" strike animation/combat does not move tactical positions: "+enemy_id)
	for actor in [enemy,target]:
		var authored=plan.events.filter(func(e):return e.attacker==actor.id or e.defender==actor.id)
		if authored.is_empty():continue
		var last=authored[-1];var expected_hp=int(last.source_hp_after) if last.attacker==actor.id else int(last.hp_after)
		check(int(actor.hp)==expected_hp,code+" committed HP follows planned strike events: "+str(actor.id))
	covered[int(enemy.class_id)]=true
	combat.append({"stage":code,"unit":enemy_id,"class_id":int(enemy.class_id),"distance":distance,"controlled":true,"events":plan.events})
func run():
	for code in FIXTURES:
		var g=State.new();g.save_path="res://reports/"+str(FIXTURES[code])
		var loaded=g.load_game();check(loaded,code+" genuine existing deployment checkpoint loads")
		if not loaded:continue
		var id=int(g.stage_id);g.save_path=CACHE+str(code)+".json"
		check(g.start_battle(id),code+" normal start_battle redeploys current JSON")
		check(g.mode=="battle" and g.turn==1 and g.battle_outcome.is_empty(),code+" fresh battle state")
		validate_units(g,code,"fresh")
		check(g.save_game(),code+" fresh deployment saves to isolated path")
		var resumed=State.new();resumed.save_path=g.save_path
		var resumed_ok=resumed.load_game();check(resumed_ok,code+" fresh deployment reloads")
		if not resumed_ok:continue
		validate_units(resumed,code,"resumed")
		check(resumed.retry_battle(),code+" retry restores opening snapshot")
		validate_units(resumed,code,"retry")
		maps.append({"code":code,"stage_id":id,"fixture":"res://reports/"+str(FIXTURES[code]),"isolated_checkpoint":g.save_path,"enemy_count":g.battle_data.enemies.size(),"classes":g.battle_data.enemies.map(func(u):return int(u.class_id))})
		for raw in g.battle_data.enemies:
			var cid=int(raw.class_id)
			if cid not in NEW_CLASSES or covered.has(cid):continue
			var probe=State.new();probe.save_path=g.save_path
			if not probe.load_game():check(false,code+" combat fixture reload");continue
			probe_combat(probe,code,str(raw.id),1)
			if cid in [5,21]:
				probe=State.new();probe.save_path=g.save_path;probe.load_game();probe_combat(probe,code,str(raw.id),2)
		if code=="S21":
			var probe=State.new();probe.save_path=g.save_path;probe.load_game();probe_combat(probe,code,"S21_boss",2)
	for cid in NEW_CLASSES:check(covered.has(cid),"new profession exercised through actual plan_combat: "+str(cid))
	var report={"scope":"12 genuine historical deployment checkpoints -> current start_battle -> isolated save/reload/retry; controlled combat samples for all eleven previously absent enemy professions, plus body ranged modes. Not a natural full-map playthrough.","passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"maps":maps,"combat_samples":combat,"labels":checks}
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	print("ENEMY_INTEGRATION_CHECKS ",checks.size()," maps=",maps.size()," samples=",combat.size()," errors=",errors)
	quit(1 if not errors.is_empty() else 0)
