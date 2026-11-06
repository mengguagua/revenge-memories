extends SceneTree
## Exercise the real contact controller, without a scene, save or gameplay mutation.
const UI = preload("res://core/legacy_main.gd")
class GameFixture extends RefCounted:
	var commits := 0
	func commit_strike(_event: Dictionary): commits += 1
class SoundSpy extends RefCounted:
	var sounds: Array = []
	func play_sfx(key: String): sounds.append(key)
	func play_jingle(key: String): sounds.append("jingle:"+key)
class AnimationSpy extends RefCounted:
	var cinema=null
	func reaction(_id:String,_kind:String)->bool:return false
var checks: Array = []
var errors: Array = []
func _initialize(): call_deferred("run")
func check(ok: bool, label: String):
	checks.append(label)
	if not ok: errors.append(label); push_error(label)
func run():
	var ui = UI.new()
	ui.instant_mode = true
	var game = GameFixture.new()
	var audio = SoundSpy.new()
	ui.game = game; ui.audio = audio
	ui.battle_animation=AnimationSpy.new()
	var base = {"attacker":"actor", "defender":"target", "hit":true, "critical":false,
		"hp_before":20, "hp_after":20, "self_damage":0, "source_hp_before":20,
		"source_hp_after":20, "hp_cost":0}
	for row in [
		["zero damage",{},["miss"]],
		["ordinary miss",{"hit":false},["miss"]],
		["two damage",{"hp_after":18},["hit","hp_tick","hp_tick"]],
		["recoil",{"self_damage":3,"source_hp_after":17},["hit","hp_tick","hp_tick","hp_tick"]],
		["visual-only healing",{"visual_only":true,"weapon_index":40,"hp_after":23},["hp_tick","hp_tick","hp_tick"]]
	]:
		var event = base.duplicate(true); event.merge(row[1],true)
		audio.sounds.clear(); var before = game.commits
		await ui._contact(event)
		check(audio.sounds == row[2],str(row[0])+" emits exact expected sound sequence")
		check(game.commits-before == (0 if event.get("visual_only",false) else 1),str(row[0])+" preserves one contact commit")
	var path = "res://reports/audio-scene-review-20261024/contact-feedback-tests.json"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	var f = FileAccess.open(path,FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"player_saves_read":false,"player_saves_written":false},"  "));f.close()
	print("AUDIO_CONTACT_FEEDBACK ",checks.size()," checks; ",errors)
	ui.free()
	quit(0 if errors.is_empty() else 1)
