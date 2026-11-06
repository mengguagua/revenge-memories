extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/weapon-spell-feedback-20261102/"
const CACHE="/private/tmp/weapon-spell-feedback-20261102/"
var checks=[];var errors=[];var shots=[];var screen;var phone;var ui;var visual=false
var learned_game;var learned_receipt;var healing_game;var healing_receipt;var training_game;var training_receipt
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func same(a,b):return JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))
func fresh():
 var g=State.new();g.new_game();g.save_path=CACHE+"battle.json"
 for id in ["hervi","fula"]:g.party.append(id);g.roster[id]=g._initial_character(id)
 g.parties.alm=g.party.duplicate();g.roster.hunapu.item_id=60;g.world_node=6;g.previous_world_node=5;g.route_positions.alm=6
 check(g.start_battle(105),"enter current M15 without touching player journal");g.story_events.clear();return g
func domain():
 var g=fresh();var rules=g.Rules
 for spec in [[59,21,"铜剑"],[60,21,"铁剑"],[61,6,"铜枪"],[62,6,"铁枪"],[63,12,"铜弓"],[64,12,"铁弓"]]:
  var actor=g._initial_character("hunapu");actor.class_id=spec[1];actor.item_id=spec[0]
  var before=rules.attack_stats(actor,g.find_unit("M15_e6"),0);var frozen=actor.duplicate(true)
  check(rules.weapon_name(actor)==spec[2],"adapted base attack resolves actual equipped name: "+str(spec[0]))
  check(g.EquipmentComparison.attack_name(actor)==spec[2],"equipment forecast shares same attack name: "+str(spec[0]))
  check(same(actor,frozen) and same(before,rules.attack_stats(actor,g.find_unit("M15_e6"),0)),"name lookup cannot alter weapon or combat stats: "+str(spec[0]))
 var hero=g.find_unit("hunapu").duplicate(true);hero.item_id=53
 check(rules.weapon_name(hero)=="普通剑","shield is not mislabeled as an attacking weapon")
 hero.class_id=6;hero.item_id=60;check(rules.weapon_name(hero)=="普通枪","incompatible sword falls back to actual class weapon")
 var guard=g.find_unit("M15_e6").duplicate(true);guard.item_id=62;guard.behavior="guard"
 check(rules.weapon_name(guard,4)=="投枪" and guard.item_id==62,"ranged counter name follows counter weapon without replacing held item")
 var caster=g.find_unit("hervi").duplicate(true);caster.weapon_index=24
 check(rules.weapon_name(caster)=="雷电" and caster.item_id==66,"focus-enhanced spell displays spell name")
 var unit=g._initial_character("hervi");check(not g.Items.spells(unit).has(24),"Hervi does not start with Thunder")
 for i in range(3):
  var receipt=g.CampaignExperience.award(g,unit,100)
  check(unit.level==4+i and unit.magic_level==1+i,"each actual level-up advances personal training exactly once: "+str(i))
  check(receipt.learned==([24] if i==2 else []),"Thunder is learned on third level-up only: "+str(i))
 check(unit.level==6 and g.Items.spells(unit).has(24),"Hervi normally learns Thunder at displayed level6")
 var snapshot=unit.duplicate(true);var no_level=g.CampaignExperience.award(g,unit,1)
 check(not no_level.leveled and no_level.learned.is_empty() and unit.magic_level==snapshot.magic_level,"experience without a level cannot relearn or advance training")
 g=fresh();var a=g.find_unit("hervi");var b=g.find_unit("M15_e6")
 a.level=5;a.magic_level=2;a.exp=99;a.hp=52;a.max_hp=52;a.position=[15,21];a.weapon_index=27;a.acted=false
 b.position=[16,21];b.hp=52;b.max_hp=52;b.defence=0;b.resistance=0;b.strength=0;b.speed=0
 var exchange=g.plan_combat(a.id,b.id);check(not exchange.events.is_empty(),"real combat produces strike plan for learning boundary")
 for event in exchange.events:g.commit_strike(event)
 var receipt=g.finish_exchange(exchange)
 check(receipt.leveled and receipt.learned==[24] and a.level==6,"ordinary combat reward carries newly learned Thunder")
 check(g.save_game(),"completed combat with newly learned spell saves")
 var loaded=State.new();loaded.save_path=g.save_path
 check(loaded.load_game() and loaded.Items.spells(loaded.find_unit("hervi")).has(24),"learned spell persists without awarding another level")
 learned_game=g;learned_receipt=receipt
 g=fresh();a=g.find_unit("fula");b=g.find_unit("hunapu")
 a.level=6;a.magic_level=5;a.exp=99;a.acted=false;a.position=[17,22];b.position=[18,22];b.hp=int(b.max_hp)-10
 var support=g.use_support(a.id,40,b.id)
 check(support.get("reward",{}).get("learned",[])==[43] and a.level==7,"healing level-up reports learned support spell Teleport")
 healing_game=g;healing_receipt=support.get("reward",{})
 g=State.new();g.save_path="res://reports/full-assessment-20261025/campaign-final-r1/ch1/chain-M13-victory.json"
 check(g.load_game(),"historical M13 source loads read-only for training fixture")
 g.save_path=CACHE+"training.json";g.mode="world";g.story_events=[];g.flags.erase("active_plot");g.battle_outcome="";g.battle_settled=false;g.units=[];g.battle_start_snapshot={}
 a=g._initial_character("hervi");a.level=5;a.magic_level=2;a.exp=99;g.roster.hervi=a
 if not g.party.has("hervi"):g.party.append("hervi");g.parties.alm=g.party.duplicate()
 check(g.Training.start(g,191),"training starts through ordinary menu rules")
 g.story_events=[];g.battle_outcome="victory";check(g.complete_battle(),"training reward settles normally")
 var found=g.victory_rewards.filter(func(r):return r.unit=="hervi")
 check(found.size()==1 and found[0].learned==[24],"training success receipt carries newly learned spell")
 check(g.save_game(),"pending training reward with learned spell saves")
 loaded=State.new();loaded.save_path=g.save_path
 check(loaded.load_game() and loaded.victory_rewards.filter(func(r):return r.unit=="hervi")[0].learned.map(func(id):return int(id))==[24],"saved clear/training reward retains learned notification data")
 training_game=g;training_receipt=found[0]
func frame(name:String,capture:bool=true):
 ui.notice_time=0;ui.phase_time=0;ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await process_frame
 if visual:
  await RenderingServer.frame_post_draw
  check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" glyph and bitmap safe areas: "+str(ui.layout_errors))
  if capture:screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func combat_frame(g,attacker:String,defender:String,name:String):
 ui.game=g;ui.view="combat";ui.busy=true;ui.combat=g.plan_combat(attacker,defender);ui.combat_hp={};ui.combat_poses={};ui.combat_offsets={};ui.combat_fades={};ui.combat_message="";ui.battle_animation.reset()
 for id in [attacker,defender]:ui.combat_hp[id]=g.find_unit(id).hp;ui.combat_poses[id]=int(ui._battle_sprite(g.find_unit(id)).sequences.idle[0]);ui.combat_offsets[id]=Vector2.ZERO;ui.combat_fades[id]=1.0
 var before=ui.combat.duplicate(true);await frame(name)
 check(same(before,ui.combat),name+" drawing never changes exchange")
 if visual:
  for id in [attacker,defender]:
   var stats=ui.combat.stats[id]
   if not stats.can_strike:continue
   var row=ui.presentation_audit.combat_weapons[id];var unit=g.find_unit(id)
   check(row.name==g.Rules.weapon_name(unit,int(stats.weapon_index)) and row.font_px==12,name+" actual attack name uses readable twelve-pixel font: "+id)
   check(row.bounds.end.y<=178 and row.bounds.size.x<=104,name+" weapon row clears HP region and side borders: "+id)
func reward_frame(g,receipt:Dictionary,name:String):
 ui.game=g;ui.reward=receipt;ui.reward_elapsed=1;ui.view="reward";ui.busy=false;ui.batch_running=false;ui.training_reward_open=false
 await frame(name)
 if visual:
  var audit=ui.presentation_audit.learned_spells
  check(not audit.names.is_empty() and ui.text_checks.any(func(t):return str(t.text).begins_with("学会：")),name+" learned spell is explicitly visible")
  for r in audit.bounds:
   check(audit.panel.grow(-10).encloses(r) and r.end.y<=202,name+" learned text stays clear of panel border and confirmation")
   check(audit.stats.all(func(s):return not s.intersects(r)),name+" learned text does not overlap stats")
func run():
 DirAccess.make_dir_recursive_absolute(CACHE+"slots");visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1";domain()
 screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if visual else SubViewport.UPDATE_DISABLED;root.add_child(screen)
 phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
 ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
 var g=fresh();g.find_unit("hunapu").position=[15,21];g.find_unit("M15_e6").position=[16,21]
 await combat_frame(g,"M15_e6","hunapu","iron-sword-counter")
 g=fresh();g.find_unit("otto").position=[15,21];g.find_unit("M15_e6").position=[16,21];g.find_unit("otto").item_id=62
 await combat_frame(g,"otto","M15_e6","iron-lance-attack")
 g=fresh();g.find_unit("hervi").position=[15,21];g.find_unit("M15_e6").position=[17,21];g.find_unit("hervi").weapon_index=24;g.find_unit("hervi").magic_flags=19
 await combat_frame(g,"hervi","M15_e6","thunder-and-counter")
 await reward_frame(learned_game,learned_receipt,"combat-learn-thunder")
 await reward_frame(healing_game,healing_receipt,"healing-learn-teleport")
 await reward_frame(training_game,training_receipt,"training-learn-thunder")
 ui.training_reward_open=true;ui._accept();check(ui.view=="victory" and not ui.training_reward_open,"learning reward confirmation preserves training result flow")
 var receipt=learned_receipt.duplicate(true);receipt.learned=[24,43]
 await reward_frame(learned_game,receipt,"multiple-new-spells")
 if visual:
  var spells=[]
  for entries in g.Items.data().spell_learning.values():
   for entry in entries:
    if not spells.has(int(entry.spell_id)):spells.append(int(entry.spell_id))
  for id in spells:
   receipt=learned_receipt.duplicate(true);receipt.learned=[id];ui.reward=receipt;await frame("learned-spell-"+str(id),false)
   check(ui.presentation_audit.learned_spells.names==[str(g.Items.spell(id).name_zh)],"all personal level-up spell names render: "+str(id))
  receipt=learned_receipt.duplicate(true);receipt.learned=[];ui.reward=receipt;await frame("level-without-new-spell",false)
  check(not ui.presentation_audit.has("learned_spells"),"ordinary level-up does not show a false learned prompt")
  ui._accept();check(ui.view=="battle" and not ui.busy,"ordinary level-up confirmation preserves battle flow")
  screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout()
  await reward_frame(learned_game,learned_receipt,"compact-learn-thunder")
  g=fresh();g.find_unit("hunapu").position=[15,21];g.find_unit("M15_e6").position=[16,21];await combat_frame(g,"M15_e6","hunapu","compact-iron-sword")
 ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(.25).timeout
 var file=FileAccess.open(OUT+("visual.json" if visual else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"checks":checks.size(),"labels":checks,"errors":errors,"screenshots":shots},"  "));file.close();print("WEAPON_SPELL_FEEDBACK ",checks.size()," checks; ",errors);quit(0 if errors.is_empty() else 1)
