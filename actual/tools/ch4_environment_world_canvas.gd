extends "res://core/main.gd"
func _ready():
 world=game.formal_world
 for sprite in GameState.read_json("res://assets/nature/nature.json").get("sprites",[]):nature_sprites[str(sprite.key)]=sprite
 game.chapter=4;game.flags={"F22_confirmed":true,"chapter1_complete":true};game.flags.island_loop_safe=OS.get_environment("CH4_WORLD_PHASE") in ["trial","verified"];game.flags.D42_done=OS.get_environment("CH4_WORLD_PHASE")=="verified";set_process(false);set_process_input(false)
func _canvas_offset()->Vector2:return Vector2.ZERO
func _draw():
 if not is_node_ready():return
 draw_set_transform(Vector2.ZERO)
 _draw_second_chapter_world(_world_visual_data(),Vector2.ZERO)
