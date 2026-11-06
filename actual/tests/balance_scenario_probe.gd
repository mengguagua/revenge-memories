extends SceneTree
## Five historical deployment rosters against current encounters; formula probes,
## not a natural playthrough. Only hypothetical held items / attack modes change.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const Roles=preload("res://core/campaign_enemy_roles.gd")
const FIXTURES={
	"F33":"chapter3-environment-20261023/play/round2/round2-F33-deployment.json",
	"F43":"chapter4-redesign-20261022/play/continuous-final/continuous-final-F43-deployment.json",
	"S42":"chapter4-redesign-20261022/play/continuous-final/continuous-final-S42-deployment.json",
	"J53":"chapter5-environment-20261023/play/final-round2/final-round2-J53-deployment.json",
	"J54":"chapter5-environment-20261023/play/final-round2/final-round2-J54-deployment.json",
}
const TEST_ITEMS={"F33":[],"F43":[15],"S42":[15,17],"J53":[7,9,10,15,17,18,53,55],"J54":[7,9,10,15,17,18,53,55]}
const ITEM_ROUTES={7:"celica",9:"alm",10:"celica",15:"celica",17:"celica",18:"alm",53:"alm",55:"alm"}
const OUT="/private/tmp/revenge-balance-scenario-probe-20261023.json"
var report={"scope":"Historical rosters reopened through current start_battle. Controlled zero-avoid formula comparisons with hypothetical equipment restricted to the source party before joint deployment; J53/J54 include cross-party gear available after adjacent battlefield exchange. No natural-map or victory claims. Formula samples do not edit stored stats, HP or positions; normal deployment restores HP. Separate exchange checks relocate Eileen to a legal adjacent tile and inject one hypothetical acquired accessory on Hunapu, then invoke the real battlefield exchange API. S42 item17 appears only if historical flags authorize Eileen's profession. J54 phase2 copies the boss with existing +3 strength. Sequence damage ceilings ignore early death/HP affordability and are not resolved combat totals.","stages":[],"errors":[]}

func _initialize():call_deferred("run")

func compact(u:Dictionary)->Dictionary:
	var out={}
	for key in ["id","name_zh","class_id","hero_profession","promoted","level","exp","hp","max_hp","strength","skill","speed","luck","defence","resistance","item_id","move","position","temporary","neutral","battle_guard"]:
		if u.has(key):out[key]=u[key]
	return out

func exchanges(attacker:Dictionary,defender:Dictionary,distance:int)->Dictionary:
	var a=Rules.attack_context(attacker,distance)
	var d=Rules.default_counter(defender,distance)
	var sequence=Rules.strike_sequence(a,d,distance)
	var attack=Rules.attack_stats(a,d,0)
	var counter=Rules.attack_stats(d,a,0)
	return {"range":distance,"sequence":sequence,"attack":attack,"counter":counter,
		"noncritical_connected_damage_ceiling":int(attack.damage)*sequence.count("attacker"),
		"noncritical_connected_counter_ceiling":int(counter.damage)*sequence.count("defender")}

func run():
	for code in FIXTURES:
		var g=State.new();g.save_path="res://reports/"+str(FIXTURES[code])
		if not g.load_game():report.errors.append(code+" checkpoint does not load");continue
		g.save_path="/private/tmp/revenge-balance-scenario-probe-"+str(code)+".json"
		if not g.start_battle(g.stage_id):report.errors.append(code+" current deployment does not start");continue
		var stage={"code":code,"goal":g.battle_data.goal,"fixture":FIXTURES[code],"players":[],"enemies":[],"pairs":[],"enemy_slots":g.Summons.available_slots(g,"enemy")}
		for u in g.living("player"):stage.players.append(compact(u))
		for u in g.living("enemy"):stage.enemies.append(compact(u))
		for original in g.living("player"):
			if not g.roster.has(original.id):continue
			var variants=[int(original.item_id)]
			for item_id in TEST_ITEMS[code]:
				if code not in ["J53","J54"] and ITEM_ROUTES[item_id]!=g.Casualties.owner({"parties":g.parties},str(original.id)):continue
				if int(item_id)==17 and not g.HeroProfessions.advanced(original):continue
				if Items.can_use(original,item_id) and not variants.has(item_id):variants.append(item_id)
			for item_id in variants:
				var player=original.duplicate(true);player.item_id=item_id;player.erase("weapon_index")
				var modes=[-1]
				for spell in Items.spells(player):
					if not Items.is_support(spell):modes.append(spell)
				var enemies=g.living("enemy").duplicate()
				if code=="J54":
					var phase2=g.find_unit("J54_boss").duplicate(true)
					phase2.strength+=3;phase2.id="J54_boss_phase2";enemies.append(phase2)
				for enemy in enemies:
					for mode in modes:
						var actor=player.duplicate(true)
						if mode>=0:actor.weapon_index=mode
						for distance in [1,2,3,5]:
							if not Rules.can_attack(actor,distance):continue
							var row=exchanges(actor,enemy,distance)
							row.player=original.id;row.item_id=item_id;row.baseline_item=int(original.item_id);row.spell_id=mode;row.enemy=enemy.id
							row.enemy_initiates=exchanges(enemy,player,distance) if Rules.can_attack(enemy,distance) else {}
							stage.pairs.append(row)
		if code in ["J53","J54"]:
			stage.cross_party_exchanges=[]
			for item_id in [53,55]:
				var proof=State.new();proof.save_path="res://reports/"+str(FIXTURES[code]);proof.load_game()
				proof.save_path="/private/tmp/revenge-balance-scenario-exchange.json";proof.start_battle(proof.stage_id)
				var first=proof.find_unit("hunapu");var second=proof.find_unit("eileen")
				var original_position=second.position.duplicate();var found=false
				for offset in [Vector2i.UP,Vector2i.LEFT,Vector2i.DOWN,Vector2i.RIGHT]:
					var cell=proof.pos(first)+offset
					if proof.in_bounds(cell) and proof.unit_at(cell).is_empty() and proof.movement_cost(second,cell)<255:
						second.position=[cell.x,cell.y];found=true;break
				first.item_id=item_id
				var second_before=int(second.item_id)
				var exchanged=found and proof.Inventory.exchange(proof,"hunapu","eileen")
				var synced=exchanged and int(proof.roster.eileen.item_id)==item_id and int(proof.roster.hunapu.item_id)==second_before and first.acted
				if not synced:report.errors.append(code+" actual adjacent cross-party accessory exchange "+str(item_id))
				stage.cross_party_exchanges.append({"controlled":true,"item_id":item_id,"source_route":first.route,"recipient_route":second.route,"original_position":original_position,"controlled_position":second.position,"exchanged_and_roster_synced":synced})
		if code=="F43":
			stage.scripted_wave_size=3
			stage.bounded_minion_ceiling=5
			stage.maximum_bodies_without_casualties=g.living("enemy").size()+8
			stage.minions=[]
			for enemy in g.living("enemy"):
				if enemy.get("campaign_role","") not in ["bounded_summoner","bounded_divider"]:continue
				g.turn=3
				var a=Roles.action(g,enemy)
				if not a.has("source_summon"):continue
				var spec=a.source_summon
				stage.minions.append(compact(g.Summons.spawn_unit(enemy,spec.class_id,spec,g.route)))
			report.stages.append(stage)
		else:report.stages.append(stage)
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	print("BALANCE_SCENARIO_PROBE ",report.stages.size()," stages; errors=",report.errors," output=",OUT)
	quit(0 if report.errors.is_empty() else 1)
