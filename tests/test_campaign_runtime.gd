extends SceneTree
const State=preload("res://core/game_state.gd")
var checks=0
var errors: Array=[]
func check(ok: bool, label: String):
	checks+=1
	if not ok: errors.append(label); push_error(label)
func _initialize():call_deferred("run")
func run():
	var game=State.new()
	game.save_path="res://reports/test-campaign-runtime-save.json"
	var loaded=State.new()
	loaded.save_path=game.save_path
	for stage in range(1,81):
		game.new_game()
		game.chapter=5
		game.world_armies.clear()
		game.route="alm"
		for id in ["lukas","gray","silque","clair","clive","python","luthier","delthea","tatiana"]:game.recruit(id)
		game.parties.alm=game.party.duplicate()
		game.route="celica"
		game.party=[]
		for id in ["celica","mae","boey","genny","saber","valbar","leo","kamui","palla","catria"]:game.recruit(id)
		game.parties.celica=game.party.duplicate()
		game.route="alm"
		game.party=game.parties.alm.duplicate()
		game.world_node=stage if stage<49 else 77
		if stage==62:game.flags.scenario_final_merge_ready=true
		check(game.start_battle(stage,[],true),"stage %d starts"%stage)
		check(game.mode=="battle" and not game.units.is_empty(),"stage %d stays playable"%stage)
		var occupied: Dictionary={}
		for unit in game.units:
			var cell=game.pos(unit)
			check(game.in_bounds(cell),"stage %d %s fits map"%[stage,unit.id])
			check(not occupied.has(cell),"stage %d collision %s / %s at %s"%[stage,unit.id,occupied.get(cell,""),cell])
			occupied[cell]=unit.id
			check(game._valid_unit(unit,true),"stage %d unit %s valid save"%[stage,unit.id])
		check(game.save_game(),"stage %d save"%stage)
		check(loaded.load_game(),"stage %d load"%stage)
		check(loaded.units.size()==game.units.size(),"stage %d army retained"%stage)
		for unit in game.living("enemy"):
			unit.hp=0
		game.battle_outcome="victory"
		check(game.complete_battle(),"stage %d settlement"%stage)
		check(not game.complete_battle(),"stage %d no duplicate reward"%stage)
		check(game.save_game() and loaded.load_game(),"stage %d result suspend"%stage)
	var out=FileAccess.open("res://reports/campaign-runtime-verification.json",FileAccess.WRITE)
	out.store_string(JSON.stringify({"checks":checks,"errors":errors,"scope":"all 80 native maps: actual unit deployment, collisions, save/resume, idempotent victory; does not simulate a natural full playthrough"},"\t"))
	out.close()
	DirAccess.remove_absolute(game.save_path)
	print("FE2 FULL RUNTIME ",checks," checks, ",errors.size()," failures")
	quit(0 if errors.is_empty() else 1)
