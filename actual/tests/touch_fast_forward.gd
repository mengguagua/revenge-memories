extends SceneTree
## Timed touch-speed regression. Test fixtures never write player journals.
const OUT="res://reports/iphone-layout-20261022/touch-speed-checks.json"
class ObservedAnimation extends "res://core/battle_animation.gd":
	var original_clock=true
	var ticks=[]
	func sprite(unit:Dictionary)->Dictionary:
		var graphic=super.sprite(unit).duplicate(true)
		graphic.original_motion=original_clock
		return graphic
	func _source_frame(event:Dictionary,frame:Dictionary,tick:int,sounds:bool)->void:
		ticks.append(tick)
		super._source_frame(event,frame,tick,sounds)
var ui
var viewport
var checks=[]
var errors=[]
var times={}
var samples=[]

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func timed_wait(source_seconds:float)->float:
	ui.wait_accumulated=0.0;ui.combat_wait_accumulated=0.0
	var start=Time.get_ticks_usec();await ui._wait(source_seconds)
	return float(Time.get_ticks_usec()-start)/1000000.0
func motion(original:bool,fast:bool,release_after:float=-1.0)->Dictionary:
	ui.game.new_game();ui.game.save_path="/private/tmp/revenge-touch-speed-unused.json"
	var actor=ui.game.characters.hunapu.duplicate(true)
	actor.id="speed_actor";actor.side="player";actor.hp=30;actor.max_hp=30;actor.acted=false;actor.position=[4,4]
	var target=actor.duplicate(true);target.id="speed_target";target.side="enemy";target.class_id=6;target.position=[5,4]
	ui.game.units=[actor,target];ui.view="combat";ui.busy=true;ui.instant_mode=false
	ui.combat={"attacker":actor.id,"defender":target.id,"distance":1,"initiative_side":"player"}
	ui.combat_hp={actor.id:30,target.id:30};ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear()
	ui.wait_accumulated=0.0;ui.combat_wait_accumulated=0.0
	ui.battle_animation=ObservedAnimation.new(ui);ui.battle_animation.original_clock=original
	var event={"attacker":actor.id,"defender":target.id,"weapon_index":0,"critical":false,"hit":true,"damage":1,"hp_before":30,"hp_after":29}
	var chosen=ui.battle_animation.selection(event)
	check(str(chosen.kind)=="source","real source animation selected "+str(original)+"/"+str(fast))
	var before=ui.game.roster.duplicate(true)
	ui.set_touch_fast_forward(fast)
	if release_after>=0.0:create_timer(release_after).timeout.connect(func():ui.set_touch_fast_forward(false))
	var start=Time.get_ticks_usec();await ui.battle_animation.play(event)
	var result={"original_clock":original,"held":fast,"release_after":release_after,"seconds":float(Time.get_ticks_usec()-start)/1000000.0,
		"variant":str(chosen.key),"frames":chosen.variant.frames.size(),"ticks":ui.battle_animation.ticks.duplicate(),
		"contacts":ui.battle_animation.contact_calls,"target_hp":target.hp,"actor_hp":actor.hp,"kills":ui.game.kills}
	check(result.contacts==1 and result.target_hp==29 and result.actor_hp==30,"exactly one real HP commit "+str(original)+"/"+str(fast))
	check(result.ticks==range(result.frames),"all source ticks run once in order "+str(original)+"/"+str(fast))
	check(ui.game.roster==before and ui.battle_animation.effects.is_empty() and ui.combat_offsets[actor.id]==Vector2.ZERO,"animation cleanup and persistent roster remain intact "+str(original)+"/"+str(fast))
	ui.set_touch_fast_forward(false);samples.append(result);return result

func run():
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.hide();ui.game.slot_directory="/private/tmp/revenge-touch-speed-slots";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.game.new_game();ui.view="combat";ui.instant_mode=false;ui.animation_speed=1.0
	check(is_equal_approx(ui.effective_animation_speed(),1.0),"normal animation speed starts at 1x")
	var selected=ui.menu_selected;var actions=ui.menu_actions.duplicate();var original_view=ui.view
	ui.set_touch_fast_forward(true)
	check(ui.touch_fast_forward and is_equal_approx(ui.effective_animation_speed(),3.0),"touch hold enables 3x")
	check(ui.menu_selected==selected and ui.menu_actions==actions and ui.view==original_view,"dedicated hold emits no confirmation action")
	ui.set_touch_fast_forward(false);check(not ui.touch_fast_forward and is_equal_approx(ui.effective_animation_speed(),1.0),"finger release restores normal rate immediately")
	for notification in [Node.NOTIFICATION_APPLICATION_FOCUS_OUT,Node.NOTIFICATION_APPLICATION_PAUSED]:
		ui.set_touch_fast_forward(true);ui._notification(notification)
		check(not ui.touch_fast_forward and is_equal_approx(ui.effective_animation_speed(),1.0),"focus loss releases hold "+str(notification))
	ui.set_touch_fast_forward(true);ui.view="reward";ui.reward_dismissed=false
	check(is_equal_approx(ui.effective_animation_speed(),1.0) and not ui.touch_fast_forward and not ui.reward_dismissed,"leaving combat clears hold without dismissing reward")
	ui.set_touch_fast_forward(true);check(not ui.touch_fast_forward,"reward screen cannot enable combat speed")
	ui.view="combat";check(is_equal_approx(ui.effective_animation_speed(),1.0),"next combat requires a new hold")
	times.normal=await timed_wait(0.9)
	ui.set_touch_fast_forward(true);times.held=await timed_wait(0.9)
	ui.set_touch_fast_forward(false)
	check(times.normal>0.8 and times.normal<1.3 and times.held>0.24 and times.held<0.45,"ordinary waits measure approximately 3x while held")
	create_timer(0.15).timeout.connect(func():ui.set_touch_fast_forward(true))
	times.press_during_wait=await timed_wait(0.9)
	check(times.press_during_wait>0.3 and times.press_during_wait<0.58,"press accelerates an already-running wait")
	ui.set_touch_fast_forward(true)
	create_timer(0.12).timeout.connect(func():ui.set_touch_fast_forward(false))
	times.release_during_wait=await timed_wait(0.9)
	check(times.release_during_wait>0.5 and times.release_during_wait<0.84,"release slows an already-running wait without skipping its remainder")
	var original_reference={}
	for original in [true,false]:
		var normal=await motion(original,false);var held=await motion(original,true)
		if original:original_reference=normal
		check(held.seconds<normal.seconds*0.48 and held.seconds>normal.seconds*0.22,"actual source animation measures approximately 3x "+str(original))
		check(normal.variant==held.variant and normal.ticks==held.ticks and normal.contacts==held.contacts and normal.target_hp==held.target_hp and normal.actor_hp==held.actor_hp and normal.kills==held.kills,"hold changes timing only "+str(original))
	var released=await motion(true,true,0.15)
	check(released.seconds>original_reference.seconds*0.75 and released.seconds<original_reference.seconds*1.1,"original-frame playback resumes normal speed when released during the action")
	check(released.ticks==original_reference.ticks and released.contacts==1 and not ui.touch_fast_forward,"mid-action release preserves frame order and single contact")
	ui.view="world";ui._process(0.0)
	check(not ui.touch_fast_forward and ui.combat_wait_accumulated==0.0,"scene transition clears leftover combat timing")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT.get_base_dir()))
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"wait_seconds":times,"motions":samples,"user_saves_touched":false,"scope":"Headless timed real animation/controller fixtures, held/released/in-progress waits; physical iPhone touch dispatch tested separately."},"  "));f.close()
	print("TOUCH_SPEED ",checks.size()," checks; timings ",times,"; errors ",errors)
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
