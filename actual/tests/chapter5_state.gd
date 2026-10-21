extends SceneTree
const State=preload("res://core/game_state.gd")
const SOURCE="res://reports/chapter4/play/round2-chapter-end.json"
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func base():
 var g=State.new();g.save_path=SOURCE;check(g.load_game(),"authentic chapter4 checkpoint loads")
 g.save_path="res://reports/chapter5/state-working.json";check(g.begin_chapter_five(),"chapter5 begins");return g
func fixture(id):
 var g=base();g.flags.M51_confirmed=true;g.flags.east_network_ready=true
 if id in [502,533,534]:g.cleared_stages.append(501)
 if id in [504,511,533,534]:g.cleared_stages.append(503)
 if id in [511,533,534]:g.cleared_stages.append(504);g.flags.east_palace_gate=true;g.flags.S51_invited=true
 if id in [533,534]:
  g.cleared_stages.append(502);g.flags.west_palace_gate=true;g.route_positions={"alm":15,"celica":15};g.flags.chapter5_ready={"alm":true,"celica":true};g.ChapterFive.selection(g,"alm");g.ChapterFive.selection(g,"celica");check(g.ChapterFive.merge(g),"merge fixture")
 if id==534:g.cleared_stages.append(533);g.flags.final_access=true
 if id not in [533,534]:g.route=g.stages[id].route;g.party=g.parties[g.route].duplicate()
 g.world_node=int(g.stages[id].node);g.route_positions[g.route]=g.world_node
 check(g.start_battle(id),str(id)+" fixture entry");return g
func use(g,id):
 var hero=g.find_unit(g.leader_id());hero.acted=false
 for o in g.battle_data.objects:
  if o.id!=id:continue
  var at=o.get("approach",o.position);hero.position=at.duplicate();g.selected_id=hero.id;check(g.interact(id),str(g.stage_id)+" interaction "+id);return
 check(false,"object exists "+id)
func run():
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/chapter5"))
 var g=base();var original=g.roster.duplicate(true);var convoy=g.convoy.duplicate(true);var sources=g.treatment_remaining()
 check(not g.begin_chapter_five(),"cannot restart chapter")
 check(g.switch_route() and g.world_node==29 and g.route=="celica","east starts at the actual shrine")
 check(g.roster==original and g.convoy==convoy and g.treatment_remaining()==sources,"no injury growth inventory or treatment reset")
 check(g.save_game(),"opening writes");var loaded=State.new();loaded.save_path=g.save_path;check(loaded.load_game(),"opening reloads")
 for id in g.ChapterFive.STAGES:
  var b=fixture(id);var occupied={}
  for u in b.units:
   check(not occupied.has(State.pos(u)),str(id)+" unique spawn "+u.id);occupied[State.pos(u)]=true
   check(b.movement_cost(u,State.pos(u))<255,str(id)+" legal spawn "+u.id)
  check(b.check_outcome()=="",str(id)+" cannot instantly win")
  check(b.save_game(),str(id)+" battle writes");loaded.save_path=b.save_path;check(loaded.load_game(),str(id)+" battle reloads")
  check(loaded.retry_battle() and loaded.turn==1,str(id)+" retry restores")
  if id==511:
   use(b,"archive_exit");check(not b.flags.quest.objects.get("archive_exit",false),"cannot exit without record and boss")
  for o in b.battle_data.objects:
   if o.id!="archive_exit":use(b,o.id)
  if id==501:
   var u=b.find_unit("royal_wounded0");u.position=b.battle_data.exit.duplicate();b.mark_wait(u.id)
  if id==503:b.turn+=1;b.phase="player";b.ChapterFive.after_phase(b)
  b.find_unit(str(b.battle_data.boss_id)).hp=0
  if id==511:use(b,"archive_exit")
  check(b.check_outcome()=="victory",str(id)+" complete objectives win")
  check(b.complete_battle(),str(id)+" settlement once")
  var inventory=b.convoy.duplicate(true);var roster=b.roster.duplicate(true)
  check(not b.complete_battle() and b.convoy==inventory and b.roster==roster,str(id)+" no repeat rewards")
  b.mode="victory";check(b.save_game(),str(id)+" completed save");loaded.save_path=b.save_path;check(loaded.load_game(),str(id)+" completed reload")
  if id in [533,534]:
   check(b.parties.alm.has("hunapu") and b.parties.celica.has("eileen") and b.party==b.parties[b.route],"joint fight preserves original ownership")
   check(b.roster.eileen.exp!=original.eileen.exp or b.roster.eileen.level!=original.eileen.level,"east joint experience settled")
 g=fixture(534);var boss=g.find_unit("J54_boss");boss.hp=int(boss.max_hp)/2;g.check_outcome();var count=g.units.size();var strength=boss.strength;g.check_outcome()
 check(g.flags.quest.final_phase and g.units.size()==count and boss.strength==strength,"half health wave and strength occur once")
 check(int(boss.hp)==int(boss.max_hp)/2 and g.units.filter(func(u):return str(u.id).begins_with("J54_summon")).size()==3,"boss does not heal and summons exactly three")
 check(g.save_game(),"phase save");loaded.save_path=g.save_path;check(loaded.load_game(),"phase reload");loaded.check_outcome();check(loaded.units.size()==count,"reload does not repeat wave")
 for uid in ["hunapu","eileen"]:
  var hero=g.find_unit(uid);var candidate=hero.duplicate(true);candidate.position=[16,9]
  var damage=g.Rules.attack_stats(candidate,boss,0)
  check(int(damage.damage)>0,"ordinary attack harms final boss "+uid)
 var before=g.roster.duplicate(true);check(g.return_to_preparation() and g.world_node==15,"joint retry returns to real shared preparation")
 check(g.roster==g.battle_start_snapshot.roster,"preparation restores prebattle injuries and equipment")
 g=fixture(501);g.find_unit("royal_wounded0").hp=0;g.find_unit("royal_wounded1").hp=0;check(g.check_outcome()=="defeat","both wounded lost fails")
 g=fixture(503);g.find_unit("repair_team0").hp=0;check(g.check_outcome()=="defeat","repair worker loss fails")
 g=fixture(534);g.find_unit("eileen").hp=0;check(g.check_outcome()=="defeat","east hero dying fails joint battle")
 g=fixture(533);var entries=preload("res://core/chapter5_endings.gd").entries(g);check(entries.size()==22,"eighteen character outcomes and four world pages")
 var ill=entries.filter(func(p):return p.title=="米蕾")[0];check(str(ill.text).contains("照护") and not str(ill.text).contains("遇难"),"persistent dying does not become death")
 var f=FileAccess.open("res://reports/chapter5/state-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"fixture":true},"  "));f.close()
 print("CH5_STATE ",checks.size()," checks ",errors);quit(0 if errors.is_empty() else 1)
