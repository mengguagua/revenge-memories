extends SceneTree

const Rules = preload("res://core/combat_rules.gd")
var failures: int = 0
var checks: int = 0


func _initialize() -> void:
	var file = FileAccess.open("res://data/first_battle.json", FileAccess.READ)
	var data: Dictionary = JSON.parse_string(file.get_as_text())
	var alm: Dictionary = data["characters"]["alm"]
	var enemy: Dictionary = data["enemies"][0]
	var stats: Dictionary = Rules.attack_stats(alm, enemy, 0)
	_check(stats["damage"] == 8, "Alm strength10 minus brigand defence2")
	_check(stats["hit"] == 95, "Alm skill7 +90 - brigand AS2")
	_check(stats["critical"] == 3, "Original double shift gives floor((7+7)/4)")
	_check(stats["attack_speed"] == 6, "Default weapon has zero weight")
	_check(Rules.attack_stats(alm, enemy, 40)["hit"] == 55, "Terrain avoids40 points")
	_check(Rules.default_weapon_index(enemy) == 0, "Brigand axe uses shared basic weapon stats")
	_check(Rules.default_weapon_index({"class_id": 12}) == 1, "Default bow is separate index1")
	_check(Rules.strike_sequence(alm, enemy) == ["attacker", "defender", "attacker"], "One-point or larger AS lead adds one strike")
	_check(Rules.strike_sequence(enemy, alm) == ["attacker", "defender", "defender"], "Faster defender follows its counter")
	_check(Rules.strike_sequence({"speed": 2}, {"speed": 2}) == ["attacker", "defender"], "Equal AS does not follow up")
	_check(Rules.attack_stats({"strength": 0, "skill": 0, "speed": 0}, {"defence": 40, "speed": 40}, 80)["damage"] == 1, "Successful physical strikes have minimum damage1")
	_check(Rules.attack_stats({"strength": 0, "skill": 0, "speed": 0}, {"defence": 40, "speed": 40}, 80)["hit"] == 0, "Hit clamps at zero")
	_check(Rules.attack_speed({"speed": 1, "item_id": 14}) == 0, "Weapon weight cannot create negative AS")
	# Manual arithmetic from the two original lookup tables and enemy value30.
	_check(Rules.experience_gain(alm, enemy, 26, 0, true) == 15, "Alm kill: ceil(5*10*30/100)")
	_check(Rules.experience_gain(data["characters"]["lukas"], enemy, 26, 0, true) == 24, "Lukas kill: ceil(8*10*30/100)")
	_check(Rules.experience_gain(data["characters"]["kliff"], enemy, 26, 0, true) == 30, "Kliff's class coefficient10")
	_check(Rules.experience_gain(data["characters"]["gray"], enemy, 26, 0, true) == 21, "Gray level5 coefficient7")
	_check(Rules.experience_gain(alm, enemy, 26, 18, false) == 3, "Nonkill: ceil(15*8/(26*2))")
	_check(Rules.experience_gain(alm, enemy, 26, 26, false) == 1, "An exchange with no hit earns1")
	_check(Rules.experience_gain(alm, enemy, 3, 0, true) == 15, "Kill reward is not reduced by remaining HP")
	var capped: Dictionary = alm.duplicate(true)
	capped["level"] = 20
	_check(Rules.experience_gain(capped, enemy, 26, 0, true) == 0, "Original level20 cap prevents experience application")
	# Asymmetric rolls catch accidental forward stat iteration and <= growth.
	var growth_unit: Dictionary = {"max_hp": 28, "strength": 10, "skill": 7, "speed": 6, "luck": 7, "defence": 6,
		"growths": {"hp": 50, "defence": 30, "luck": 20, "speed": 30, "skill": 40, "strength": 35}}
	var growth: Dictionary = Rules.growth_result(growth_unit, [50, 29, 20, 30, 40, 35])
	_check(growth["defence"] == 1 and growth["hp"] == 0 and growth["strength"] == 0, "Reverse iteration and growth equality failure")
	_check(Rules.growth_result(growth_unit, [99, 99, 99, 99, 99, 99])["hp"] == 1, "Six failures receive HP consolation")
	growth_unit["defence"] = 40
	var at_cap: Dictionary = Rules.growth_result(growth_unit, [99, 1, 99, 99, 99, 99])
	_check(at_cap["defence"] == 0 and at_cap["hp"] == 0, "A successful capped roll suppresses consolation")
	growth_unit["max_hp"] = 52
	_check(Rules.growth_result(growth_unit, [99, 99, 99, 99, 99, 99])["hp"] == 0, "HP maximum52 applies to consolation")
	var ring: Dictionary = alm.duplicate(true)
	ring["item_id"] = 55
	_check(Rules.growth_result(ring, [1, 1, 1, 1, 1, 1])["hp"] == 2, "Angel Ring growth increment2")
	_check(Rules.phase_recovery({"hp": 12, "max_hp": 28}, 218) == 5, "Original pink recovery tile heals5")
	_check(Rules.phase_recovery({"hp": 27, "max_hp": 28}, 218) == 1, "Recovery cannot exceed maximum HP")
	_check(Rules.phase_recovery({"hp": 0, "max_hp": 28}, 218) == 0, "Recovery cannot revive a defeated unit")
	_check(Rules.phase_recovery({"hp": 12, "max_hp": 28}, 49) == 0, "Ordinary cover does not heal")
	print("FE2 rules: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)


func _check(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(description)
