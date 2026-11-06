extends SceneTree
## Authored-map counterexamples; isolated fixtures, never player journal files.
const State=preload("res://core/game_state.gd")
const Tactics=preload("res://core/battlefield_tactics.gd")
const OUT="res://reports/tactical-expansion-20261025/battlefield-checks.json"
var checks:Array=[]
var errors:Array=[]

func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fixture(stage:int):
	var g=State.new();g.new_game();g.stage_id=stage;g.battle_data=g.stages[stage].duplicate(true)
	g.chapter=int(g.battle_data.chapter);g.route=str(g.battle_data.route);g.world_node=int(g.battle_data.node)
	g.mode="battle";g.phase="player";g.turn=1;g.story_events.clear();g.units=[]
	g.flags.quest={"objects":{},"evacuated":[],"freed":[],"reinforced":true,"final_phase":false,"summon_wave":false}
	return g
func player(g,at:Vector2i,id:String="hunapu") -> Dictionary:
	var unit=g._initial_character(id);unit.position=[at.x,at.y];unit.hp=unit.max_hp;unit.acted=false;return unit
func enemy(g,id:String) -> Dictionary:
	var unit=g.battle_data.enemies.filter(func(u):return str(u.id)==id)[0].duplicate(true)
	unit.acted=false;return unit
func same(a,b)->bool:return JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))

func telegraph_checks():
	var g=fixture(202);var bow=enemy(g,"F22_e8");var target=player(g,Vector2i(13,14));g.units=[bow,target]+g.battle_data.npc_units.duplicate(true)
	var rng=g.rng_state;Tactics.initialize(g)
	check(Tactics.warning_cells(g).is_empty(),"F22 has no unannounced first-turn special attack")
	g.turn=2;Tactics.after_phase(g)
	check(not Tactics.warning_cells(g).is_empty(),"F22 announces its narrow shot before the player acts")
	check(g.rng_state==rng,"previews never consume random combat values")
	var saved=g.flags.quest.battlefield.duplicate(true);var marked=Tactics.warning_cells(g)
	check(marked.all(func(m):return Tactics._distance(g.pos(bow),Tactics._point(m.position))<=3),"F22 volley does not extend the bow's three-tile reach")
	g.flags.quest.battlefield=JSON.parse_string(JSON.stringify(saved));Tactics.restore(g)
	check(same(saved,g.flags.quest.battlefield),"JSON restore keeps exact announced cells and damage counter")
	target.position=[10,14];g.phase="enemy"
	var action=Tactics.action(g,bow)
	var before=int(target.hp);var shot=Tactics.apply_special(g,bow,action)
	check(shot.changed.is_empty() and int(target.hp)==before,"moving out of the announced cells avoids damage without retargeting")
	check(bow.acted and Tactics.action(g,bow).is_empty(),"volley spends the actor's complete action")
	g.phase="player";g.turn=3;bow.acted=false;target.position=[13,14];Tactics.after_phase(g)
	check(Tactics.warning_cells(g).is_empty(),"ordinary turns remain between special attacks")
	g.turn=5;Tactics.after_phase(g);check(not Tactics.warning_cells(g).is_empty(),"special attack becomes available again after its stated interval")
	bow.position=[12,12];g.phase="enemy"
	check(Tactics.warning_cells(g).is_empty(),"moving the source immediately clears the threat overlay")
	check(Tactics.apply_special(g,bow,Tactics.action(g,bow)).interrupted,"knockback interrupts the prepared shot")
	check(int(target.hp)==before,"interrupted shot deals no damage")

func final_boss_checks():
	var g=fixture(534);var boss=enemy(g,"J54_boss");var target=player(g,Vector2i(16,14));g.units=[boss,target]
	g.turn=2;Tactics.initialize(g)
	check(Tactics.warning_cells(g).size()==5,"J54 marks a local five-cell cross rather than the whole party")
	check(Tactics.status(g).any(func(t):return "18" in t),"non-displacement interrupt threshold is disclosed")
	Tactics.record_damage(g,str(boss.id),10)
	check(not Tactics.warning_cells(g).is_empty(),"partial pressure leaves a visible charged attack")
	Tactics.record_damage(g,str(boss.id),8)
	check(Tactics.warning_cells(g).is_empty(),"cumulative real damage interrupts the divine body")
	g.flags.quest.battlefield=JSON.parse_string(JSON.stringify(g.flags.quest.battlefield));Tactics.restore(g)
	check(Tactics.warning_cells(g).is_empty() and Tactics.status(g).has("聚光震荡：已打断"),"damage interruption remains canceled and disclosed after JSON restore")
	g.phase="enemy";var before=int(target.hp)
	check(Tactics.apply_special(g,boss,Tactics.action(g,boss)).interrupted and int(target.hp)==before,"damage interrupt cancels release while preserving ordinary HP")
	g=fixture(534);boss=enemy(g,"J54_boss");target=player(g,Vector2i(16,14));g.units=[boss,target];g.turn=2;Tactics.initialize(g);g.phase="enemy"
	before=int(target.hp);var release=Tactics.apply_special(g,boss,Tactics.action(g,boss))
	check(not release.interrupted and release.changed.size()==1 and int(target.hp)<before,"standing in the marked cell receives the special hit")
	check(release.changed[0].damage is Dictionary,"special damage goes through the shared cover-aware damage entry")
	g=fixture(534);boss=enemy(g,"J54_boss");target=player(g,Vector2i(16,14));g.units=[boss,target];g.turn=2;Tactics.initialize(g);boss.hp=0
	check(Tactics.warning_cells(g).is_empty() and Tactics.action(g,boss).is_empty(),"defeating the source removes its danger and action")
	g=fixture(534);boss=enemy(g,"J54_boss");target=player(g,Vector2i(16,14));g.units=[boss,target];g.turn=2;Tactics.initialize(g)
	boss.position=[17,8];g.flags.quest.battlefield=JSON.parse_string(JSON.stringify(g.flags.quest.battlefield));Tactics.restore(g)
	check(Tactics.warning_cells(g).is_empty() and Tactics.status(g).has("聚光震荡：已打断"),"source displacement remains an interrupt after JSON restore")
	g.phase="enemy";check(Tactics.apply_special(g,boss,Tactics.action(g,boss)).interrupted,"restored displacement cancellation spends the prepared action without damage")
	g=fixture(534);boss=enemy(g,"J54_boss");target=player(g,Vector2i(16,14));g.units=[boss,target];g.turn=2;Tactics.initialize(g)
	g.turn=3;Tactics.restore(g)
	check(Tactics.warning_cells(g).is_empty() and Tactics.action(g,boss).is_empty(),"expired special cannot release on a later turn after restore")

func command_checks():
	var g=fixture(402);var boss=enemy(g,"M42_boss");var rider=enemy(g,"M42_e6");var target=player(g,Vector2i(4,24));g.units=[boss,rider,target]
	Tactics.initialize(g)
	check(Tactics.action(g,rider).is_empty(),"M42 riders preserve opening grace before the announced order")
	g.turn=2;Tactics.after_phase(g)
	var action=Tactics.action(g,rider)
	check(not action.is_empty() and action.destination!=g.pos(rider),"M42 order makes a posted cavalry unit advance toward the station")
	check(g.reachable(rider).costs.has(action.destination),"ordered movement stays within actual movement budget")
	g.flags.quest.objects.transfer_station=true
	check(Tactics.action(g,rider).is_empty(),"cutting the station disables the coordinated override")
	check(rider.guard_alerted,"released cavalry remain alert instead of becoming immobile targets")
	g.flags.quest.objects.transfer_station=false;boss.hp=0
	check(Tactics.action(g,rider).is_empty(),"defeating the commander also stops coordinated orders")

func obstacle_checks():
	for stage in [202,402]:
		var g=fixture(stage);var obstacle:Dictionary=g.battle_data.breakable_obstacles[0]
		var cell=Tactics._point(obstacle.position);var actor=player(g,cell+Vector2i.LEFT)
		g.units=[actor];g.selected_id=str(actor.id);Tactics.initialize(g)
		var before=int(g.battle_data.map.tiles[cell.y*int(g.battle_data.map.width)+cell.x])
		check(g.movement_cost(actor,cell)>=255,"intact authored obstacle blocks movement: "+str(stage))
		var choices=Tactics.interactions_for(g,actor)
		check(choices.size()==1 and "敌我" in str(choices[0].confirm_text),"confirmation exposes both sides' new route: "+str(stage))
		actor.acted=true;check(Tactics.interactions_for(g,actor).is_empty(),"spent actors cannot break obstacles: "+str(stage));actor.acted=false
		check(Tactics.interact(g,str(obstacle.id)),"adjacent melee actor can dismantle the optional obstacle: "+str(stage))
		check(actor.acted and g.movement_cost(actor,cell)<255,"breaking consumes action and opens only its local tile: "+str(stage))
		check(int(g.battle_data.map.tiles[cell.y*int(g.battle_data.map.width)+cell.x])!=before,"broken geometry changes: "+str(stage))
		check(g.flags.quest.objects.is_empty(),"breaking does not bypass required switches: "+str(stage))
		check(not Tactics.interact(g,str(obstacle.id)),"repeated break cannot repeat effects: "+str(stage))
		var state=g.flags.quest.battlefield.duplicate(true)
		g.battle_data=g.stages[stage].duplicate(true);g.flags.quest.battlefield=JSON.parse_string(JSON.stringify(state));Tactics.restore(g)
		check(g.movement_cost(actor,cell)<255,"reload reconstructs the broken route: "+str(stage))
		check(g.battle_data.art_layers[1][cell.y][cell.x]==null and g.battle_data.art_layers[2][cell.y][cell.x]==null,"reload removes the intact obstacle art: "+str(stage))
		check(Tactics.hint(g,cell).text=="已破坏 · 敌我可通行","broken hover explains resulting route: "+str(stage))
		Tactics.initialize(g,true)
		g.battle_data=g.stages[stage].duplicate(true)
		check(Tactics._state(g).broken.is_empty() and g.movement_cost(actor,cell)>=255,"new attempt restores intact initial layout: "+str(stage))

func validation_checks():
	var g=fixture(534);var boss=enemy(g,"J54_boss");var target=player(g,Vector2i(16,14));g.units=[boss,target];g.turn=2;Tactics.initialize(g)
	var valid=g.flags.duplicate(true)
	check(Tactics.validate(g,valid,g.battle_data),"canonical pending intent validates")
	check(Tactics.validate(g,{"quest":{}},g.battle_data),"older saves without tactical state remain compatible")
	var damaged=valid.duplicate(true);damaged.quest.battlefield.intents.J54_boss.cells=[[999,14]]
	check(not Tactics.validate(g,damaged,g.battle_data),"off-map attack cells rejected before load")
	damaged=valid.duplicate(true);damaged.quest.battlefield.intents.J54_boss.cells=[[16,14],[16,14]]
	check(not Tactics.validate(g,damaged,g.battle_data),"duplicate attack cells rejected")
	damaged=valid.duplicate(true);damaged.quest.battlefield.intents.J54_boss.power="18"
	check(not Tactics.validate(g,damaged,g.battle_data),"non-numeric pending attack power rejected")
	damaged=valid.duplicate(true);damaged.quest.battlefield.broken.unknown_door=true
	check(not Tactics.validate(g,damaged,g.battle_data),"unknown obstacle flags cannot open arbitrary quest doors")
	damaged=valid.duplicate(true);damaged.quest.battlefield.last_turn.J54_boss=3
	check(not Tactics.validate(g,damaged,g.battle_data),"mismatched pending and last-use turn rejected")
	for field in ["actor","name","kind"]:
		for malformed in [[],{},0,true,null]:
			damaged=valid.duplicate(true);damaged.quest.battlefield.intents.J54_boss[field]=malformed
			var loaded=JSON.parse_string(JSON.stringify(damaged))
			check(not Tactics.validate(g,loaded,g.battle_data),"JSON identity type rejected before comparison: "+field+" "+type_string(typeof(malformed)))
	for field in ["broken","last_turn","intents"]:
		damaged=valid.duplicate(true);damaged.quest.battlefield[field][123]=true
		check(not Tactics.validate(g,damaged,g.battle_data),"non-string state key rejected: "+field)
		var loaded=JSON.parse_string(JSON.stringify(damaged))
		check(not Tactics.validate(g,loaded,g.battle_data),"unknown JSON state key rejected: "+field)
	damaged=valid.duplicate(true);damaged.quest.battlefield.last_turn.J54_boss=[]
	check(not Tactics.validate(g,JSON.parse_string(JSON.stringify(damaged)),g.battle_data),"array last-turn value rejected before conversion")

func cover_feedback_checks():
	var g=fixture(534);var boss=enemy(g,"J54_boss");var target=player(g,Vector2i(16,14));var guard=player(g,Vector2i(17,14),"otto")
	g.units=[boss,target,guard];g.turn=2;Tactics.initialize(g)
	var initial=int(guard.hp);var power=int(boss.strength)+3
	var direct=maxi(1,power-g.Items.magic_defence(target))
	var own_hit=maxi(1,power-g.Items.magic_defence(guard))
	var share=mini(initial,ceili(float(direct)/2.0))
	target.acted=true
	check(g.Cover.start(g,guard,str(target.id)),"area attack fixture starts actual cover")
	g.phase="enemy";var release=Tactics.apply_special(g,boss,Tactics.action(g,boss))
	var guard_changes=release.changed.filter(func(change):return change.id==guard.id)
	check(guard_changes.size()==1,"guard's shared hit and area hit produce one feedback entry")
	check(int(guard.hp)==maxi(0,initial-share-own_hit),"guard receives only the real share and its own marked-cell hit")
	check(int(guard_changes[0].before)==initial and int(guard_changes[0].after)==int(guard.hp),"merged feedback preserves chronological HP endpoints")
	check(guard_changes[0].events.size()==2,"both actual damage events remain available for audit")
	check(g.story_events.any(func(e):return e.get("pages",[]).any(func(p):return "掩护分担" in str(p.get("text","")))),"cover loss has a visible story notice as well as its hit feedback")

func run():
	telegraph_checks();final_boss_checks();command_checks();obstacle_checks();validation_checks();cover_feedback_checks()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT.get_base_dir()))
	var f=FileAccess.open(OUT,FileAccess.WRITE)
	f.store_string(JSON.stringify({"checks":checks,"errors":errors,"passed":errors.is_empty(),"scope":"Deterministic authored-map state, real shared damage entry, save-state JSON restore; not natural full-stage clears."},"  "));f.close()
	print("BATTLEFIELD_TACTICS ",checks.size()," checks; errors=",errors)
	quit(0 if errors.is_empty() else 1)
