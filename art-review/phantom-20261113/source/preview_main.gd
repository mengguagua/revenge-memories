extends "res://core/main.gd"
var phantom_recorder
var phantom_queue_checks=[]
func _run_ai_unit(unit:Dictionary,gather:bool=false)->void:
 var tracking=game.Phantoms.is_phantom(unit) and int(unit.hp)>0 and not unit.acted
 var started_turn=game.turn
 await super._run_ai_unit(unit,gather)
 if tracking:phantom_queue_checks.append({"unit":str(unit.id),"turn":started_turn,"born":int(unit.phantom_born_turn),"acted":bool(unit.acted)})
func _play_combat(a:String,d:String,part:String="")->void:
 var recording=phantom_recorder.begin_exchange(a,d) if phantom_recorder!=null else false
 var prior=instant_mode
 if recording:instant_mode=false;animation_speed=3.0
 await super._play_combat(a,d,part)
 if phantom_recorder!=null:await phantom_recorder.end_exchange(recording)
 instant_mode=prior
