extends Node
var ui
var screen
var output="/private/tmp/phantom-preview-20261113/"
var clip=""
var clips=[]
var frames=0
var next_frame=0
var capturing=false
var hold_reward=false
var experience_recorded=false
var label=""
var receipts=[]
var phantom_actions=[]
func start(name:String):
 clip=name;frames=0;next_frame=0;DirAccess.make_dir_recursive_absolute(output+name)
func stop():
 if not clip.is_empty():clips.append({"name":clip,"frames":frames,"fps":12,"size":[screen.size.x,screen.size.y]})
 clip=""
func _process(_delta):
 if clip.is_empty() or capturing or Time.get_ticks_msec()<next_frame:return
 next_frame=Time.get_ticks_msec()+83;capture()
func capture():
 capturing=true
 await RenderingServer.frame_post_draw
 if not clip.is_empty():screen.get_texture().get_image().save_png(output+clip+"/%04d.png"%frames);frames+=1
 capturing=false
func shot(name:String):
 await get_tree().process_frame;await RenderingServer.frame_post_draw
 screen.get_texture().get_image().save_png(output+name+".png")
func begin_exchange(a:String,d:String)->bool:
 var actor=ui.game.find_unit(a);var target=ui.game.find_unit(d)
 if ui.game.Phantoms.is_phantom(actor):phantom_actions.append({"unit":a,"turn":ui.game.turn,"born":actor.phantom_born_turn})
 if not experience_recorded and ui.game.Phantoms.is_phantom(actor):
  experience_recorded=true;start(label+"-experience");return true
 return false
func end_exchange(was_recording:bool):
 if not ui.reward.get("phantom_source","").is_empty():receipts.append(ui.reward.duplicate(true))
 if was_recording:
  hold_reward=true
  await get_tree().create_timer(1.3).timeout
  await shot(label+"-experience")
  stop();hold_reward=false
