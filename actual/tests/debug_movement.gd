extends SceneTree
func _initialize():
	var g=load("res://core/game_state.gd").new();g.new_game();g.world_node=2;g.start_battle(101)
	for id in g.party:
		var u=g.find_unit(id);var graph=g.reachable(u)
		print(id," move ",u.move," class ",u.class_id," cells ",graph.costs.size()," costs ",g.movement_cost(u,g.pos(u)+Vector2i.UP)," category ",g.category(g.pos(u)+Vector2i.UP))
	quit()
