extends SceneTree
## Formula audit of all current encounters against genuine contemporary rosters.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const OUT="res://reports/combat-balance-20261025/"
func _initialize():call_deferred("run")
func median(values:Array)->float:
	var v=values.duplicate();v.sort();return float(v[v.size()/2]) if v.size()%2 else (float(v[v.size()/2-1])+float(v[v.size()/2]))/2.0
func damage(enemy:Dictionary,target:Dictionary)->Dictionary:
	var best={"damage":0,"hit":0,"magic":false,"exchange":0,"weapon":0}
	var modes=[-1]
	for spell in Items.spells(enemy):
		if not Items.is_support(spell):modes.append(spell)
	for mode in modes:
		var actor=enemy.duplicate(true);actor.erase("weapon_index")
		if mode>=0:actor.weapon_index=mode
		for distance in range(1,6):
			if not Rules.can_attack(actor,distance):continue
			var stats=Rules.attack_stats(actor,target,0)
			if not stats.can_attack:continue
			var strikes=Rules.strike_sequence(actor,Rules.default_counter(target,distance),distance)
			if int(stats.damage)>int(best.damage):best={"damage":stats.damage,"hit":stats.hit,"magic":stats.magic,"exchange":int(stats.damage)*strikes.count("attacker"),"weapon":stats.weapon_index}
	return best
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var label="baseline"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--label="):label=arg.trim_prefix("--label=")
	var coverage=State.read_json("res://reports/full-playtest-20261023/coverage-summary.json")
	var rows=[];var errors=[]
	for record in coverage.battles:
		var proof=State.read_json(str(record.report).replace("actual/","res://"))
		var entry=proof.get("checkpoints",[]).filter(func(c):return str(c.name) in [str(record.code)+"-entry","entry-"+str(record.code),str(record.code)+"-deployment"])
		var g=State.new();g.save_path=str(entry[0].path) if not entry.is_empty() else str(record.source)
		if not g.load_game():errors.append(str(record.code)+" load");continue
		var source_path=g.save_path
		g.save_path="/private/tmp/combat-balance-probe.json"
		var definition={}
		for stage in g.stages.values():
			if str(stage.code)==str(record.code):definition=stage;break
		# Later sources are pre-travel checkpoints. This is a controlled formula
		# deployment, so only travel metadata changes; the real roster is retained.
		if entry.is_empty():
			g.chapter=int(definition.chapter);g.route=str(definition.route) if str(definition.route) in g.parties else "alm";g.party=g.parties[g.route].duplicate();g.world_node=int(definition.node)
		if not g.start_battle(int(definition.id)):errors.append(str(record.code)+" reenter");continue
		var players=g.living("player").filter(func(u):return not u.get("neutral",false) and not u.get("temporary",false))
		var stage={"code":record.code,"chapter":g.chapter,"players":[],"enemies":[],"source":source_path}
		for p in players:stage.players.append({"id":p.id,"hp":p.max_hp,"defence":p.defence,"resistance":p.get("resistance",0),"item_id":p.item_id})
		for e in g.living("enemy"):
			var actual=[];var bare=[];var pairs=[]
			for p in players:
				var naked=p.duplicate(true);naked.item_id=0
				var a=damage(e,p);var b=damage(e,naked);actual.append(int(a.damage));bare.append(int(b.damage))
				pairs.append({"player":p.id,"actual":a,"without_gear":b})
			stage.enemies.append({"id":e.id,"name":e.name_zh,"class_id":e.class_id,"strength":e.strength,"defence":e.defence,"resistance":e.get("resistance",0),"hp":e.max_hp,"item_id":e.item_id,"boss":str(e.id)==str(g.battle_data.boss_id),"role":e.get("campaign_role",""),"median_actual":median(actual),"median_bare":median(bare),"floor_actual":actual.count(1),"pair_count":actual.size(),"pairs":pairs})
		rows.append(stage)
	var f=FileAccess.open(OUT+label+".json",FileAccess.WRITE);f.store_string(JSON.stringify({"stages":rows,"errors":errors,"scope":"All 40 current deployments with genuine historical rosters. Maximum affordable single-hit damage per enemy/player across legal attack modes with actual class/item effectiveness, zero terrain avoidance, no critical or hit-probability weighting; counterpart without gear isolates tank equipment. Formula audit, not natural play."},"  "));f.close()
	print("DIFFICULTY_PROBE ",rows.size()," stages ",errors)
	quit(0 if errors.is_empty() else 1)
