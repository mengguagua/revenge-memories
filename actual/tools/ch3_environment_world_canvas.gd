extends "res://core/main.gd"
func _ready():
 world=game.formal_world
 for sprite in GameState.read_json("res://assets/nature/nature.json").get("sprites",[]):nature_sprites[str(sprite.key)]=sprite
 game.chapter=3;game.flags={"F22_confirmed":true,"chapter1_complete":true};set_process(false);set_process_input(false)
func _canvas_offset()->Vector2:return Vector2.ZERO
func _draw():
 if not is_node_ready():return
 draw_set_transform(Vector2.ZERO)
 _draw_second_chapter_world(_world_visual_data(),Vector2.ZERO)
