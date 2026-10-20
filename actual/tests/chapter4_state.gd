extends SceneTree
const State=preload("res://core/game_state.gd")
const SOURCE="res://reports/chapter3/play/round1final-chapter-end.json"
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func base():
 var g=State.new();g.save_path=SOURCE;check(g.load_game(),"authentic chapter3 completion loads")
 g.save_path="res://reports/chapter4/state-working.json";check(g.begin_chapter_four(),"chapter4 begins");return g
func fixture(id):
 var g=base();g.flags.M41_confirmed=true;g.flags.F41_confirmed=true;g.flags.F43_confirmed=true;g.flags.S41_invited=true;g.flags.S42_invited=true
 if id in [403,404]:g.cleared_stages.append(402)
 if id in [404,407,408,412]:g.cleared_stages.append(406);g.flags.obs_steps_ready=true
 if id==404:g.cleared_stages.append(403);g.flags.west_tower_safe=true;g.flags.m43_seized=true
 g.route=g.stages[id].route;g.party=g.parties[g.route].duplicate();g.world_node=int(g.stages[id].node);g.route_positions[g.route]=g.world_node
 check(g.start_battle(id),str(id)+" fixture entry");return g
func use(g,id):
 var hero=g.find_unit(g.leader_id());hero.acted=false
 for o in g.battle_data.objects:
  if o.id!=id:continue
  var p=Vector2i(o.position[0],o.position[1]);var at=Vector2i(o.approach[0],o.approach[1]) if o.has("approach") else p+Vector2i.DOWN if o.adjacent else p
  hero.position=[at.x,at.y];g.selected_id=hero.id;check(g.interact(id),str(g.stage_id)+" use "+id);return
 check(false,"missing object "+id)
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/chapter4"))
 var g=base();var roster=g.roster.duplicate(true);var items=g.convoy.duplicate(true)
 check(not g.begin_chapter_four(),"chapter cannot restart")
 check(g.switch_route() and g.route=="celica" and g.world_node==9,"both teams begin at shared camp")
 check(g.roster==roster and g.convoy==items,"route switch preserves injuries, training, inventory")
 check(g.save_game(),"start save writes");var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"chapter4 save loads")
 for id in g.ChapterFour.STAGES:
  var b=fixture(id);var occupied={}
  for u in b.units:
   check(not occupied.has(State.pos(u)),str(id)+" unique deployment "+u.id);occupied[State.pos(u)]=true
   check(b.movement_cost(u,State.pos(u))<255,str(id)+" legal deployment "+u.id)
  check(b.save_game(),str(id)+" battle save")
  loaded.save_path=b.save_path;check(loaded.load_game(),str(id)+" battle load")
  check(loaded.retry_battle() and loaded.turn==1,str(id)+" retry restores")
  check(b.check_outcome()=="",str(id)+" no initial win")
  for o in b.battle_data.objects:
   if not o.get("optional",false):use(b,str(o.id))
  if id in [401,407,412]:
   var prefix="snow_group" if id==401 else "marsh_group" if id==407 else "island_group"
   for i in range(2):var u=b.find_unit(prefix+str(i));u.position=b.battle_data.exit.duplicate();b.mark_wait(u.id)
  if id==405:b.turn=6
  if id==408:b.turn+=1
  b.find_unit(str(b.battle_data.boss_id)).hp=0
  check(b.check_outcome()=="victory",str(id)+" full objective wins")
  check(b.complete_battle(),str(id)+" settlement")
  var after=b.convoy.duplicate(true);check(not b.complete_battle() and b.convoy==after,str(id)+" settlement idempotent")
  b.mode="world";check(b.save_game(),str(id)+" complete save");loaded.save_path=b.save_path;check(loaded.load_game(),str(id)+" complete reload")
  if id==404:check(b.find_unit("M44_boss").hp==1 and b.find_unit("M44_boss").surrendered and not b.party.has("M44_boss"),"Herlan survives, no recruitment")
 g=fixture(403);g.find_unit("M43_boss").hp=0;use(g,"outer_court");use(g,"tower_control");g.complete_battle()
 check(g.flags.m43_seized and not g.flags.get("west_tower_safe",false),"tower may be seized before eastern records")
 g.mode="world";check(g.can_switch_route(),"waiting tower allows route switch")
 g=fixture(408);g.flags.transfer_cut=true
 check(not g.flags.quest.transfer_cut_snapshot and g.battle_data.reinforcements.size()==2,"late transport letter does not remove current wave")
 g.save_game();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.battle_data.reinforcements.size()==2,"uncut snapshot persists")
 g=base();g.flags.transfer_cut=true;g.flags.F43_confirmed=true;g.route="celica";g.party=g.parties.celica.duplicate();g.world_node=29;g.route_positions.celica=29;g.start_battle(408)
 check(g.flags.quest.transfer_cut_snapshot and g.battle_data.reinforcements.is_empty(),"cut snapshot removes announced wave at entry")
 g.save_game();loaded.save_path=g.save_path;check(loaded.load_game() and loaded.battle_data.reinforcements.is_empty(),"cut snapshot remains removed after load")
 g=fixture(405);var e=g.find_unit("F41_e1");e.position=[5,6];g.phase="player";g.turn=2;g.ChapterFour.after_phase(g)
 check(g.flags.quest.wells.well_n,"one arrival does not lose well")
 g.turn=3;g.ChapterFour.after_phase(g);check(not g.flags.quest.wells.well_n and g.check_outcome()=="","one lost well does not fail")
 e.position=[7,6];g.find_unit("eileen").position=[5,6];g.phase="enemy";g.ChapterFour.after_phase(g);check(g.flags.quest.wells.well_n,"standing back on well recaptures")
 g.flags.quest.wells={"well_n":false,"well_s":false};check(g.check_outcome()=="defeat","both wells lost fails")
 for id in [406,411]:
  g=fixture(id);var burner=g.units.filter(func(u):return u.get("ch4_burner",false))[0];burner.position=g.battle_data.burn_target;g.turn=int(g.battle_data.burn_start)
  g.ChapterFour.after_wait(g,burner);check(not g.flags.quest.record_lost,str(id)+" first burn warns")
  g.ChapterFour.after_wait(g,burner);check(g.flags.quest.record_lost,str(id)+" second burn destroys")
  var actor=g.find_unit(g.leader_id());actor.position=g.battle_data.burn_target.duplicate();actor.acted=false;g.selected_id=actor.id
  var record_id="observatory_record" if id==406 else "black_register"
  check(not g.interact(record_id) and not g.ChapterFour.done(g,record_id),str(id)+" burned record cannot be protected again from its doorway")
  g.find_unit(str(g.battle_data.boss_id)).hp=0
  check(g.check_outcome()==("defeat" if id==406 else "victory"),str(id)+" record loss correct severity")
 g=fixture(407);g.turn=3;g.phase="enemy";g.ChapterFour.after_phase(g);check(g.units.filter(func(u):return u.has("summoner_id")).size()==3,"bounded single summon wave")
 g.find_unit("F43_boss").hp=0;g.check_outcome();check(g.living("enemy").size()==9,"summoner defeat retains natural opponents only")
 g=base();var initial=g.roster.hunapu.duplicate(true);g.ChapterFour.promote_hero(g,"hunapu");check(g.roster.hunapu.level==initial.level and g.roster.hunapu.exp==initial.exp and g.roster.hunapu.hp==initial.hp,"hero progression retains experience and HP")
 var upgraded=g.roster.hunapu.duplicate(true);g.ChapterFour.promote_hero(g,"hunapu");check(g.roster.hunapu==upgraded,"hero progression once")
 var original=g.treatment_remaining();g.flags.west_tower_safe=true;g.flags.island_loop_safe=true;g.ensure_treatment_sources();check(g.treatment_remaining()==original,"two nodes alone do not grant last resource")
 g.flags.D42_done=true;g.ensure_treatment_sources();g.ensure_treatment_sources();check(g.treatment_remaining()==original+1 and g.flags.treatment_sources.size()==4,"D42 grants exactly fourth source once")
 check(g.roster.fula.dying and g.roster.lisa.dying,"node repair does not cure injured members")
 var f=FileAccess.open("res://reports/chapter4/state-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"fixture":true},"  "));f.close()
 print("CH4_STATE ",checks.size()," checks ",errors);quit(0 if errors.is_empty() else 1)
