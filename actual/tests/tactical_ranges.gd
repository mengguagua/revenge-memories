extends SceneTree
const State=preload("res://core/game_state.gd")
const Ranges=preload("res://core/tactical_ranges.gd")
var checks=[]
var errors=[]
func _initialize():
	var g=State.new();g.new_game();g.battle_data=g.stages[101].duplicate(true)
	g.battle_data.map.tiles.fill(208);g.battle_data.terrain.tile_categories["208"]=0
	var u=g.roster.hunapu.duplicate(true);u.position=[10,10];u.move=2;u.item_id=0;g.units=[u]
	check(Ranges.preview(g,u).attack.has(Vector2i(13,10)),"two-tile move plus one-tile melee")
	u.weapon_index=24
	check(not Ranges.preview(g,u).attack.has(Vector2i(15,10)),"stale selected spell cannot expand equipped attack range")
	u.erase("weapon_index");u.class_id=15;u.hp=30;u.magic_flags=2
	check(Ranges.preview(g,u).attack.has(Vector2i(15,10)),"unlocked lightning extends attack envelope")
	u.magic_flags=0;u.weapon_index=24
	check(not Ranges.preview(g,u).attack.has(Vector2i(15,10)),"locked spell remains excluded even with stale weapon_index")
	check(u.weapon_index==24,"range preview does not mutate live action state")
	u.hp=1
	check(Ranges.preview(g,u).attack.is_empty(),"unaffordable spell cannot create green cells")
	u.erase("weapon_index");u.class_id=21;u.item_id=0;u.hp=28
	g.battle_data.terrain.tile_categories["209"]=12
	for y in range(int(g.battle_data.map.height)):g.battle_data.map.tiles[y*int(g.battle_data.map.width)+12]=209
	var result=Ranges.preview(g,u)
	check(not result.movement.has(Vector2i(12,10)),"impassable column cannot be used as a landing")
	check(not result.attack.has(Vector2i(13,10)),"attack envelope cannot invent movement through the impassable column")
	check(result.attack.all(func(p):return not result.movement.has(p)),"attack and movement colors remain disjoint")
	var f=FileAccess.open("res://reports/iphone16-feedback-20261024/range-checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"scope":"Range preview only: locked/stale spells, HP affordability, legal origins, no gameplay or save mutation."},"  "));f.close()
	print("TACTICAL_RANGES ",checks.size()," checks; errors: ",errors)
	quit(0 if errors.is_empty() else 1)
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
