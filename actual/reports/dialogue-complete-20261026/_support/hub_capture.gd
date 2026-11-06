extends "res://core/story_hub.gd"
func _init(owner):super(owner)
func enter_room(id:String,_resuming:bool=false,_checkpoint:bool=true) -> void:
 room=id;ui.game.hub_record=id;ui.game.mode="hub"
func _configure_east_room() -> void:pass
