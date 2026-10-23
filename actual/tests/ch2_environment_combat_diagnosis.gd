extends SceneTree
const State=preload("res://core/game_state.gd")
func _initialize():
 var g=State.new();g.save_path="res://reports/chapter2-environment-20261023/play/continuous-final/working-journey.json";g.load_game()
 var boss=g.find_unit("F22_boss")
 for id in ["eileen","lisa","carlo"]:
  var u=g.find_unit(id)
  for item in [-1]+g.Items.spells(u):
   if item>=0 and g.Items.is_support(item):continue
   var candidate=u.duplicate(true)
   if item>=0:candidate.weapon_index=item
   print(id," spell ",item," hp ",u.hp," canuse ",g.Items.can_use(u,item)if item>=0 else true," stats ",JSON.stringify(g.Rules.attack_stats(candidate,boss,g.terrain_avoid(g.pos(boss))))," boss counter ",JSON.stringify(g.Rules.attack_stats(boss,candidate,0)))
 quit()
