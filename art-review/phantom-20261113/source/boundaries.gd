extends "/Users/gcc/gaocc/project/revenge-memories/art-review/phantom-20261113/source/round1.gd"
func run()->void:
 DirAccess.make_dir_recursive_absolute("/private/tmp/phantom-preview-20261113")
 var records=[]
 for progress in [6,12]:
  var label="rank2" if progress==6 else "rank3-capacity"
  phantom_screen=SubViewport.new();phantom_screen.size=Vector2i(1334,750);phantom_screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(phantom_screen)
  phantom_phone=Phone.new();phantom_phone.journal_directory_override="/private/tmp/phantom-preview-20261113";phantom_screen.add_child(phantom_phone);await process_frame
  ui=phantom_phone.game_ui;ui.instant_mode=true;ui.game.save_path=PHANTOM_SOURCE;assert(ui.game.load_game());ui.game.save_path="/private/tmp/phantom-preview-20261113/"+label+".json";assert(ui.game.retry_battle())
  ui._resume_journey();await settle();ui.set_physics_process(false)
  var g=ui.game;var c=g.find_unit("mireille");g.flags.phantom_training={"mireille":progress};g.flags.phantom_maps={}
  if progress==12:
   var normal=g.living("player").size();var cells=[]
   for y in range(g.battle_data.map.height):
    for x in range(g.battle_data.map.width):
     var at=Vector2i(x,y)
     if absi(x-g.pos(c).x)+absi(y-g.pos(c).y)>6 and g.unit_at(at).is_empty() and g.movement_cost(c,at)<255:cells.append(at)
   var n=0
   while normal<20:
    var ally=c.duplicate(true);ally.id="capacity_friend_"+str(n);ally.name_zh="边界测试友军";ally.neutral=true;ally.controllable=false;ally.player_slot=normal;ally.position=[cells[n].x,cells[n].y];g.units.append(ally);normal+=1;n+=1
   for seed in range(1,256):
    g.rng_state=seed
    if g.Phantoms.plan(g,c,true)[0].class_id==5:g.rng_state=seed;break
  phantom_recorder=Recorder.new();phantom_recorder.ui=ui;phantom_recorder.screen=phantom_screen;root.add_child(phantom_recorder);ui.phantom_recorder=phantom_recorder;phantom_recorder.experience_recorded=true
  cursor_to(State.pos(c));key(KEY_Z);key(KEY_Z);choose("magic")
  while str(ui.menu_actions[ui.menu_selected])!="spell:45":key(KEY_DOWN)
  await phantom_recorder.shot(label+"-spell")
  phantom_recorder.start(label+"-summon");ui.instant_mode=false
  await create_timer(1.0).timeout
  var before=c.hp;choose("spell:45");await settle();await create_timer(1.5).timeout
  var bodies=g.units.filter(func(u):return g.Phantoms.is_phantom(u))
  assert(bodies.size()==(4 if progress==6 else 6) and c.hp==before-10)
  await phantom_recorder.shot(label+"-summoned");phantom_recorder.stop()
  if progress==12:
   assert(g.living("player").size()==26)
   var falcon=bodies.filter(func(u):return int(u.class_id)==5)[0]
   cursor_to(g.pos(falcon));key(KEY_TAB);await phantom_recorder.shot(label+"-falcon")
   assert(ui.ui_mode=="status" or ui.view.contains("status"))
   key(KEY_X)
  assert(g.save_game());var loaded=State.new();loaded.save_path=g.save_path;assert(loaded.load_game())
  records.append({"label":label,"passed":true,"fixture":true,"ordinary_friendly_count":g.living("player").size()-bodies.size(),"phantoms":bodies,"clips":phantom_recorder.clips,"phone_errors":phantom_phone.layout_errors,"layout_errors":ui.layout_errors,"scope":"Controlled skill/capacity fixture over genuine F32 checkpoint; cast through real keyboard/menu, existing runtime stats/animations. Not a natural campaign playthrough."})
  ui.phantom_recorder=null;phantom_phone.queue_free();phantom_recorder.queue_free();phantom_screen.queue_free();await process_frame
 var out=FileAccess.open(PHANTOM_OUT+"boundaries.json",FileAccess.WRITE);out.store_string(JSON.stringify({"passed":true,"records":records},"  "));out.close()
 print("PHANTOM_BOUNDARIES PASS rank2=4 rank3=6 capacity=26 save/load")
 quit()
