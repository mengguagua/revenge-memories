extends RefCounted
# Isolated new-story hooks. No original flags or boss restrictions.
static func on_battle_start(_game) -> void: pass
static func on_unit_death(game,unit: Dictionary) -> void: game.story_on_death(unit)
static func on_victory(game) -> void: game.story_on_victory()
static func can_travel(_game,_from: int,_to: int) -> bool: return true
static func on_travel(_game) -> void: pass
static func on_chapter(_game,_old: int,_new: int) -> void: pass
static func after_hub_flag(_game,_flag: int) -> void: pass
