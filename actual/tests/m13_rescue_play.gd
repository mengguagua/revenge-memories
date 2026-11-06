extends "res://tests/field_feedback.gd"
const RESCUE_OUT="res://reports/M13-rescue-20261028/"
var watching=false
var lena_moves=[]
var saw_reinforcements=false
var menu_probe_done=false
func snapshot(name:String):
 if abort or not (name.ends_with("-deployment") or name.ends_with("-victory")):return
 var old=ui.game.save_path;ui.game.save_path=RESCUE_OUT+name+".json";check(ui.game.save_game(),"checkpoint "+name);ui.game.save_path=old
func write_progress():
 var f=FileAccess.open(RESCUE_OUT+"native-play.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"passed":not abort and not battles.is_empty() and battles[-1].outcome=="victory" and ui.game.party.has("lena"),"checks":checks,"failures":failures,"battles":battles,"Lena_moves":lena_moves,"saw_reinforcements":saw_reinforcements,"screenshots":shots,"operations":operations,"inputs":inputs,"stat_edits":false,"forced_victories":false,"physical_iphone_tested":false,"iphone_updated":false},"  "));f.close()
func shot(name:String):
 if abort or not rendered or shots.any(func(s):return s.name==name):return
 phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
 check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),"safe areas "+name)
 if abort:return
 var path=RESCUE_OUT+name+".png";screen.get_texture().get_image().save_png(path);shots.append({"name":name,"path":path})
func menu_probe():
 var actor={};var destination=Vector2i.ZERO
 for id in ui.game.party:
  var u=ui.game.find_unit(id)
  if u.is_empty() or u.acted:continue
  for cell in ui.game.reachable(u).costs:
   if not ui.game.can_stop(u,cell):continue
   var candidate=u.duplicate(true);candidate.position=[cell.x,cell.y];candidate.erase("weapon_index")
   if not ui.game.targets(candidate).is_empty():actor=u;destination=cell;break
  if not actor.is_empty():break
 if actor.is_empty():return
 var origin=State.pos(actor)
 cursor_to(origin);key(KEY_Z);cursor_to(destination);key(KEY_Z);await settle()
 check(ui.menu_actions.slice(0,2)==["attack","wait"] and ui.menu_selected==0,"attack comes first and Wait immediately follows when attack is available")
 await shot("01-attack-above-wait")
 key(KEY_X);check(State.pos(actor)==origin and not actor.acted,"menu preview cancels its tentative move cleanly")
 menu_probe_done=true
func watch_lena():
 var previous=State.pos(ui.game.find_unit("lena"))
 while watching and not abort:
  var lena=ui.game.find_unit("lena")
  if not lena.is_empty():
   var at=State.pos(lena)
   if at!=previous:
    lena_moves.append({"turn":ui.game.turn,"from":[previous.x,previous.y],"to":[at.x,at.y],"locked":lena.get("locked",true),"role":lena.get("quest_kind","")})
    print("LENA_AUTO_MOVE ",JSON.stringify(lena_moves[-1]));previous=at
    if ui.view=="battle":await shot("02-lena-automatic-movement")
  for id in ["M13_r0","M13_r1"]:
   var u=ui.game.find_unit(id)
   if not u.is_empty() and not saw_reinforcements:
    check(u.level==3 and u.strength==9,"actual arriving mercenary is level3 strength9");saw_reinforcements=true
  await process_frame
func act(id:String):
 if not menu_probe_done:await menu_probe()
 await super.act(id)
func run():
 rendered=DisplayServer.get_name()!="headless"
 if rendered and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(RESCUE_OUT))
 await setup();await load_own("res://reports/campaign/natural-M13-deployment-save.json")
 key(KEY_S);choose("new:prepare");await settle();await go(4)
 await equip_from_convoy("hunapu",49);await equip_from_convoy("daan",64)
 key(KEY_Z);choose("new:battle");await settle()
 check(ui.game.stage_id==103 and ui.game.find_unit("lena").locked,"actual current M13 starts with Lena captive")
 watching=true;watch_lena()
 await battle(false);watching=false;await process_frame
 check(not battles.is_empty() and battles[-1].outcome=="victory","normal M13 combat and both doors reach victory")
 check(not lena_moves.is_empty() and lena_moves.all(func(m):return not m.locked and m.role=="escort"),"released Lena really moves during automatic friendly actions")
 check(saw_reinforcements,"scheduled mercenary reinforcements actually arrived")
 if not abort:
  enter_hub();await settle();await hub_action("orders");await hub_action("lena")
  check(ui.menu_actions.has("hub:recruit_lena"),"surviving Lena can still be invited after battle")
  if not abort:choose("hub:recruit_lena");await settle()
  check(ui.game.party.has("lena") and not ui.busy,"Lena invitation completes without blocking")
  await shot("03-lena-joined-after-battle")
 write_progress();print("M13_RESCUE_PLAY ",JSON.stringify({"failed":failures,"battles":battles.size(),"moves":lena_moves.size(),"reinforcements":saw_reinforcements}))
 screen.queue_free();await process_frame;ui=null;quit(1 if abort else 0)
