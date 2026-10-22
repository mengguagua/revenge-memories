extends "res://tools/map_catalog_canvas.gd"
func _ready() -> void:
 super._ready()
 graphics=GameState.read_json("res://data/legacy/graphics.json")
 small_font=GameState.read_json("res://data/legacy/font_small_zh.json")
func _draw() -> void:
 if game.battle_data.is_empty() or not is_node_ready():return
 draw_set_transform(Vector2.ZERO)
 _draw_map(game.battle_data.map,_tex(str(game.battle_data.art_atlas)),Vector2(PAD,PAD))
