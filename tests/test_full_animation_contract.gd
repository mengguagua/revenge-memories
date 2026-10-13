extends SceneTree
const BattleAnimation = preload("res://core/battle_animation.gd")

class FakeAudio extends RefCounted:
	var requests: Array = []
	func play_request(value: int) -> void: requests.append(value)

class FakeGame extends RefCounted:
	var units: Array = []
	func find_unit(id: String) -> Dictionary:
		for unit in units:
			if str(unit.id) == id: return unit
		return {}

class FakeUI extends RefCounted:
	var game = FakeGame.new()
	var audio = FakeAudio.new()
	var graphics: Dictionary = {}
	var combat: Dictionary = {}
	var combat_poses: Dictionary = {}
	var combat_offsets: Dictionary = {}
	var combat_hp: Dictionary = {}
	var combat_fades: Dictionary = {}
	var combat_message = ""
	var combat_hit_id = ""
	var combat_hit_time = 0.0
	var elapsed = 0.0
	var instant_mode = true
	var contacts: Array = []
	func queue_redraw() -> void: pass
	func _wait(_seconds: float) -> void: pass
	func _contact(event: Dictionary) -> void:
		contacts.append(event)
		var target = game.find_unit(str(event.defender))
		if not bool(event.get("visual_only", false)): target.hp = int(event.hp_after)
		combat_hp[str(target.id)] = int(target.hp)

var checks = 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		push_error(message)

func unit(id: String, cid: int, side: String = "player") -> Dictionary:
	return {"id": id, "name_zh": id, "class_id": cid, "character_id": 1, "name_id": 1,
		"side": side, "level": 1, "hp": 30, "max_hp": 30, "item_id": 0,
		"strength": 10, "skill": 8, "speed": 6, "luck": 5, "defence": 4}

func event(a: Dictionary, b: Dictionary, weapon: int = 0, distance: int = 1) -> Dictionary:
	return {"attacker": a.id, "defender": b.id, "weapon_index": weapon, "distance": distance,
		"hit": true, "critical": false, "damage": 5, "hp_before": 30, "hp_after": 25,
		"source_hp_before": a.hp, "source_hp_after": a.hp}

func exchange(ui, a: Dictionary, b: Dictionary, distance: int = 1, support: bool = false) -> void:
	ui.game.units = [a, b]
	ui.combat = {"attacker": a.id, "defender": b.id, "distance": distance, "initiative_side": a.side, "support": support}
	ui.combat_hp = {str(a.id): a.hp, str(b.id): b.hp}
	ui.contacts.clear()

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var ui = FakeUI.new()
	ui.graphics = JSON.parse_string(FileAccess.get_file_as_string("res://data/graphics.json"))
	var animation = BattleAnimation.new(ui)
	for cid in range(1, 23):
		for side in ["player", "enemy"]:
			var actor = unit("unit", cid, side)
			var graphic = animation.sprite(actor)
			check(not bool(graphic.get("missing", false)), "class identity present %d/%s" % [cid, side])
			check(int(graphic.class_id) == cid, "no class silhouette substitution %d/%s" % [cid, side])
	for cid in [1, 2, 3, 8]:
		var a = unit("a", cid)
		var b = unit("b", 14, "enemy")
		exchange(ui, a, b)
		animation.reset()
		var e = event(a, b)
		var chosen = animation.selection(e)
		check(chosen.kind == "melee", "recovered native body timeline for class%d" % cid)
		ui.instant_mode = false # Fake timer advances synchronously; exercise every body frame.
		await animation.play(e)
		ui.instant_mode = true
		check(ui.contacts.size() == 1 and animation.contact_calls == 1, "class%d commits one strike" % cid)
		check(ui.game.find_unit("b").hp == 25, "class%d real contact outcome" % cid)
		check(animation.effects.is_empty() and ui.combat_offsets.a == Vector2.ZERO, "class%d animation cleanup" % cid)
	var archer = unit("archer", 12)
	var enemy_archer = unit("enemy_archer", 12, "enemy")
	exchange(ui, archer, enemy_archer, 5)
	var shot = event(archer, enemy_archer, 1, 5)
	var reply = event(enemy_archer, archer, 1, 5)
	var fire = animation.selection(shot)
	var counter = animation.selection(reply)
	check(str(fire.key).ends_with("far_ally"), "range5 uses source far-initiator arrangement")
	check(str(counter.key).ends_with("far_ally"), "counterattack preserves original initiator arrangement")
	check(animation.origin(archer, ui.combat) == Vector2(208, 128), "range5 ally source origin208")
	check(animation.origin(enemy_archer, ui.combat) == Vector2(64, 128), "ranged defender remains64")
	check(int(fire.variant.contact_tick) == 56, "source far arrow contact tick56")
	exchange(ui, enemy_archer, archer, 3)
	check(animation.origin(enemy_archer, ui.combat) == Vector2(32, 128), "enemy initiating ranged combat retreats32")
	check(animation.origin(archer, ui.combat) == Vector2(176, 128), "ally counter remains176")
	var paladin = unit("paladin", 4, "enemy")
	exchange(ui, archer, paladin, 5)
	var heavy_shot = animation.selection(event(archer, paladin, 1, 5))
	check(str(heavy_shot.key).ends_with("far_ally_vs_heavy"), "heavy class geometry selects separately executed timeline")
	check(int(heavy_shot.variant.contact_tick) == 57, "heavy target has its own contact timing")
	for cid in [1, 2, 3, 6, 7, 22]:
		var a = unit("thrower", cid)
		var b = unit("target", 14, "enemy")
		exchange(ui, a, b, 2)
		var chosen = animation.selection(event(a, b, 4, 2))
		check(chosen.kind == "source" and "javelin" in str(chosen.key), "class%d uses original javelin" % cid)
		check(int(chosen.variant.source_class_id) == cid, "class%d keeps throwing silhouette" % cid)
	var mage = unit("mage", 15)
	var brigand = unit("brigand", 14, "enemy")
	exchange(ui, mage, brigand, 3)
	var thunder = event(mage, brigand, 24, 3)
	thunder.hp_cost = 2
	thunder.source_hp_after = 28
	var lightning = animation.selection(thunder)
	check("item_24" in str(lightning.key), "Thunder is not replaced by Fire")
	var effect_tick = -1
	for tick in range(lightning.variant.frames.size()):
		if not lightning.variant.frames[tick].effects.is_empty():
			effect_tick = tick
			break
	check(effect_tick >= 0 and animation.show_frame(thunder, effect_tick), "source preview exposes real spell OAM")
	var effect_count = animation.effects.size()
	animation.reset()
	check(animation.show_frame(thunder, effect_tick) and animation.effects.size() == effect_count, "reset never mutates cached original effects")
	check(thunder.has("attacker"), "reset never clears planned strike dictionary")
	animation.reset()
	ui.instant_mode = false
	await animation.play(thunder)
	ui.instant_mode = true
	check(ui.contacts.size() == 1 and ui.combat_hp.mage == 28, "spell contact once and HP cost display retained")
	check(not ui.audio.requests.is_empty(), "real source sound requests reach original audio adapter")
	var sorcerer = unit("sorcerer", 15, "enemy")
	exchange(ui, sorcerer, mage, 2)
	check("item_34" in str(animation.selection(event(sorcerer, mage, 34, 2)).key), "enemy Medusa keeps correct effect")
	var duma = unit("duma", 21, "enemy")
	duma.character_id = 167
	duma.name_id = 167
	duma.hp = 182
	duma.max_hp = 182
	var alm = unit("alm", 21)
	exchange(ui, duma, alm)
	var boss = animation.sprite(duma)
	check(boss.name == "duma", "final boss never uses Alm art")
	check(int(boss.sequences.idle[0]) == int(boss.background_frame_offset) + 9, "intact Duma uses post-entry standing pose9")
	for weapon in [19, 38, 39]:
		var selected = animation.selection(event(duma, alm, weapon))
		check(selected.kind == "source" and "item_%d" % weapon in str(selected.key), "Duma source weapon%d selects its original program" % weapon)
	duma.hp = 30
	boss = animation.sprite(duma)
	check(int(boss.sequences.idle[0]) == int(boss.background_frame_offset) + 5, "weakened Duma standing pose5")
	var priest = unit("priest", 18)
	var friend = unit("friend", 6)
	exchange(ui, priest, friend, 1, true)
	check(animation.origin(priest, ui.combat) == Vector2(176, 128), "support caster stays right")
	check(animation.origin(friend, ui.combat) == Vector2(64, 128), "support ally target occupies left")
	check(str(animation.sprite(friend).side) == "ally", "support target retains ally palette")
	var heal = event(priest, friend, 40)
	heal.visual_only = true
	var healing = animation.selection(heal)
	check(healing.kind == "source" and "item_40" in str(healing.key), "recovery uses actual source support effect")
	animation.reset()
	await animation.play(heal)
	check(ui.contacts.size() == 1 and friend.hp == 30, "visual support does not apply damage again")
	priest.hp = 28
	ui.combat_hp.priest = 28
	heal.hp_cost = 2
	heal.erase("source_hp_before")
	heal.erase("source_hp_after")
	await animation.play(heal)
	check(ui.combat_hp.priest == 28, "already settled support does not display a second HP cost")
	var cursed = event(alm, brigand, 14)
	cursed.source_hp_after = 0
	cursed.self_damage = 30
	cursed.hp_after = 30
	exchange(ui, alm, brigand)
	await animation.play(cursed)
	check(ui.combat_fades.alm == 0.0 and ui.combat_hp.alm == 0, "self-damage death cannot leave a living actor visible")
	alm.promoted = true
	alm.character_id = 36
	check(int(animation.sprite(alm).sequences.idle[0]) == 91, "promoted Alm source pose31 plus OAM60")
	var elite = unit("elite", 12, "enemy")
	elite.level = 10
	check(int(animation.sprite(elite).source_palette_id) == 104, "elite enemy original palette class+92")
	for cid in [1, 6, 14, 21]:
		var phantom = unit("phantom", cid)
		phantom.character_id = 35
		check(int(animation.sprite(phantom).source_palette_id) == 38, "summoned class%d keeps source Shadow palette" % cid)
	check(ui.graphics.character_portraits["43"] == 52 and ui.graphics.character_portraits["134"] == 42 and ui.graphics.character_portraits["141"] == 31, "named NPC/enemy original portrait lookup")
	check(not ui.graphics.character_portraits.has("35") and not ui.graphics.character_portraits.has("38"), "zero portrait sentinel remains hidden")
	var region = animation.clipped_region({"frame_size": [80, 64]}, 2, Vector2(-5, 96), true)
	check(region.destination == Rect2(0, 96, 75, 32), "actors clipped to upper battlefield")
	check(region.source == Rect2(160, 0, 75, 32), "flipped left-edge clipping preserves correct source pixels")
	check(animation.missing_animations.is_empty(), "all covered animation cases have original assets")
	var report = {"checks": checks, "failures": failures, "scope": "headless renderer contract:44 identities,4 melee families, far counter formation, heavy target timing, javelin, distinct spells,3 Duma attacks, support, promoted identity, clipping"}
	var f = FileAccess.open("res://reports/full-animation-contract.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "\t"))
	print(JSON.stringify(report))
	quit(1 if not failures.is_empty() else 0)
