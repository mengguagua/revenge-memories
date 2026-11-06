extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/field-feedback-20261026/"
var ui
var checks=[]
var failures=[]
var events=[]
var cache="/private/tmp/dialogue-sync-branches/"
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append({"label":label,"passed":ok})
 if not ok:failures.append(label);push_error(label)
func key(code:int):
 var e=InputEventKey.new();e.physical_keycode=code;e.pressed=true;ui._input(e)
 e=InputEventKey.new();e.physical_keycode=code;ui._input(e)
func choose(action:String):
 check(ui.menu_actions.has(action),"choice present: "+action)
 if not ui.menu_actions.has(action):return
 while ui.menu_actions[ui.menu_selected]!=action:key(KEY_DOWN)
 key(KEY_Z)
func finish():
 var deadline=Time.get_ticks_msec()+6000
 while Time.get_ticks_msec()<deadline:
  if ui.view=="plot" and not ui.recruitment_paused():key(KEY_Z)
  await process_frame
  if ui.view!="plot" and not ui.busy and not ui.recruitment_paused():return
 check(false,"dialogue returns control")
func text()->String:return "".join(ui.plot_pages.map(func(p):return str(p.text).replace("\n","")))
func setup(source:String="",room:String="H01"):
 if ui!=null:ui.queue_free();await process_frame;ui=null
 var g=State.new();g.slot_directory=cache+"slots";g.save_path=source if not source.is_empty() else cache+"fresh.json"
 if source.is_empty():g.new_game()
 else:check(g.load_game(),"fixture or checkpoint loads: "+source.get_file())
 g.save_path=cache+"working.json"
 ui=load("res://scenes/main.tscn").instantiate();ui.game=g;root.add_child(ui);await process_frame;ui.instant_mode=true
 ui.hub_controller.enter_room(room,true,false)
 g.character_recruited.connect(func(id):events.append(id))
func act(action:String):ui.hub_controller.action(action);await process_frame
func run():
 DirAccess.make_dir_recursive_absolute(cache+"slots")
 await setup()
 await act("grave");check(text().contains("哥，我相信不是你的错，明天我就出发。") and text().contains("凯尔的名字还没刻完。") and not text().contains("林路上那一队"),"D11 uses the approved grave dialogue without prior rescue knowledge")
 await finish();check(ui.game.flags.get("village_ready",false),"grave completion retains departure gate")
 await act("grave");check(text().contains("我去找科兰。等我回来，再把你的名字刻完。"),"unfinished M11 grave repeat does not foresee rescue");await finish()
 await act("daan");check(text().contains("开家店") and not ui.game.flags.get("daan_companionship_seen",false),"Daan first conversation records only after completion")
 ui.game.save_path=cache+"daan-mid.json";check(ui.game.save_game(),"Daan active dialogue saves")
 await setup(cache+"daan-mid.json");ui._resume_journey();await finish()
 check(ui.game.flags.get("daan_companionship_seen",false),"resumed Daan conversation commits seen flag")
 await act("daan");check(not text().contains("开家店") and text().contains("先去丘堡"),"Daan repeat is short");await finish()
 for tools in [false,true]:
  await setup("res://reports/campaign/natural-S11-victory-save.json","H08")
  ui.game.flags.tools_reward=tools;events.clear()
  await act("tools");check(text().contains("工具也找回来了") if tools else text().contains("有些工具还落在洞里"),"tools report matches the actual recovery "+str(tools));await finish()
  await act("beck");check(text().contains("不能再让军队乱押人。") and not text().contains("工具"),"Beck's invitation no longer repeats the tools report")
  check(not ui.game.party.has("beck") and ui.menu_items.is_empty(),"Beck is not recruited by starting dialogue")
  ui.game.save_path=cache+"beck-mid.json";check(ui.game.save_game(),"Beck pre-invitation saves")
  await setup(cache+"beck-mid.json","H08");ui._resume_journey();await finish()
  check(ui.menu_actions.has("hub:recruit_beck") and ui.game.flags.get("beck_invitation_seen",false),"Beck restored final page opens invitation")
  choose("hub:decline_beck");await process_frame;check(text().contains("先帮他们收拾"),"Beck decline has authored response");await finish()
  await act("beck");check(text().contains("需要我帮忙吗") and not text().contains("我爹"),"Beck second invitation skips autobiography");await finish()
  choose("hub:recruit_beck");await finish()
  check(ui.game.party.has("beck") and events==["beck"],"Beck success signal occurs once")
  check(not ui.hub_controller.objects.any(func(o):return o.action=="beck") and ui.hub_controller.objects.any(func(o):return o.action=="mine_survivor"),"Beck leaves post-battle scene on joining")
  ui.hub_controller.action("recruit_beck");await process_frame;check(events==["beck"] and ui.view=="hub","stale Beck recruit cannot replay success")
 await setup("res://reports/campaign/natural-S12-victory-save.json","H09")
 ui.game.flags.clinic_staffed=false
 await act("hervi");check(text().contains("伤者没人接手。我走不开。") and ui.menu_items.is_empty(),"Hervi remains on duty before handover");await finish()
 await act("staff");await finish();check(ui.game.flags.get("clinic_staffed",false),"normal staff dialogue completes handover")
 await act("hervi");check(text().contains("多学点术法") and text().contains("看看那里的药店"),"Hervi motivation is explained before invitation")
 ui.game.save_path=cache+"hervi-mid.json";check(ui.game.save_game(),"Hervi pre-invitation saves")
 await setup(cache+"hervi-mid.json","H09");ui._resume_journey();await finish()
 check(ui.menu_actions.has("hub:recruit_hervi"),"Hervi restored final page opens invitation")
 choose("hub:decline_hervi");await process_frame;check(text().contains("路上小心"),"Hervi decline has authored response");await finish()
 await act("hervi");check(text().contains("我现在能走。") and not text().contains("多学点术法"),"Hervi repeat is short");await finish()
 events.clear();choose("hub:recruit_hervi");await finish();check(events==["hervi"] and ui.game.party.has("hervi"),"Hervi invitation joins exactly once")
 await act("hervi");check(text().contains("沿路见到的法术和药方"),"Hervi joined branch retains personal goal");await finish()
 ui.game.roster.hervi.hp=0;ui.game.roster.hervi.condition="dying"
 check(not ui.hub_controller._companion_invitable("hervi"),"unavailable or joined Hervi cannot be re-recruited")
 await setup("res://reports/campaign/natural-S11-victory-save.json","H08")
 ui.game.find_unit("beck").hp=0;check(not ui.hub_controller._companion_invitable("beck"),"unrescued Beck cannot be invited")
 await setup("res://reports/campaign/natural-S12-victory-save.json","H09")
 ui.game.flags.clinic_staffed=true;ui.game.flags.clinic_hervi_unavailable=true
 await act("hervi");check(ui.menu_items.is_empty() and ui.view=="hub","unrescued Hervi cannot open invitation")
 await setup();ui.game.flags.grain_shared=false;ui.hub_controller.enter_room("H02",true,false)
 await act("fula");check(text().contains("请先到那边的粮车") and ui.menu_items.is_empty(),"Fula still waits for grain dispatch");await finish()
 await act("grain");check(text().contains("我给他捎个信。") and text().ends_with("胡纳普。"),"first dispatch introduces Herlan and reports Hunapu's name");await finish()
 await act("grain");check(text()=="粮车走了，给赫兰大人的信也送出去了。","dispatch repeat uses the short report");await finish()
 await act("fula");check(text().contains("你们路上缺个医者吧？"),"Fula uses the approved pre-prison invitation");await finish()
 check(ui.menu_actions.has("hub:recruit_fula"),"grain dispatch unlocks normal Fula invitation")
 ui._clear_menu();await act("fula");ui.game.save_path=cache+"fula-mid.json";check(ui.game.save_game(),"Fula invitation dialogue saves")
 await setup(cache+"fula-mid.json","H02");ui._resume_journey();await finish()
 check(ui.menu_actions.has("hub:recruit_fula"),"Fula restored final page preserves invitation")
 await setup("","H04")
 await act("cooperate")
 check(ui.view=="hub" and not ui.game.party.has("lance"),"Herlan's first dialogue waits for the order box")
 ui.game.flags.orders_collected=true
 await act("cooperate");check(text().contains("粮站的信里提过你。") and text().contains("王都让他守港，让我主持日返仪式。"),"D12 connects the grain letter and the two jurisdictions")
 await finish();check(ui.game.flags.get("cooperation_done",false) and ui.game.party.has("lance"),"D12 completion still opens the route with Lance")
 var missing=State.new();missing.new_game();missing.flags.village_ready=true;missing.world_node=2;check(missing.start_battle(101),"M11 fallback fixture enters actual stage");missing.find_unit("otto").hp=0;missing.story_events.clear();missing.queue_lines(str(missing.battle_data.before))
 check(missing.story_events[0].pages.any(func(p):return p.speaker=="村民" and p.text=="往前就到了。科兰的兵来过粮站，那儿能打听到消息。"),"M11 unavailable Otto keeps the route clue with a villager")
 missing.find_unit("daan").hp=0
 var pages=missing.dialogue_pages(str(missing.battle_data.before))
 check(pages.any(func(p):return p.text=="我也来帮忙。") and not pages.any(func(p):return p.speaker=="达恩" or p.text.contains("达恩，护住他们")),"M11 does not ask an unavailable Daan to fight")
 for id in [111,112]:
  var g=State.new();g.save_path="res://reports/campaign/natural-"+("S11" if id==111 else "S12")+"-victory-save.json";check(g.load_game(),"side victory fixture loads");g.save_path=cache+"stage.json";g.story_events.clear();g.flags.erase("seen_"+str(g.battle_data.code)+"-END");g.story_on_victory()
  var who="贝克" if id==111 else "赫维";var all=[]
  for event in g.story_events:all.append_array(event.pages)
  check(all.any(func(p):return p.speaker==who),"surviving side companion has victory dialogue "+who)
  var companion="beck" if id==111 else "hervi";g.find_unit(companion).hp=0;g.story_events.clear();g.flags.erase("seen_"+str(g.battle_data.code)+"-END");g.story_on_victory()
  check(not g.story_events.any(func(e):return e.pages.any(func(p):return p.speaker==who)),"unrescued companion does not speak in victory "+who)
 var f=FileAccess.open(OUT+"branch-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"fixture_tests_only":true},"  "));f.close()
 print("DIALOGUE_BRANCHES ",checks.size()," checks; failures=",JSON.stringify(failures));ui.queue_free();await process_frame;ui=null;quit(0 if failures.is_empty() else 1)
