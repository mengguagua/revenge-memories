extends SceneTree
const State = preload("res://core/game_state.gd")
const OUT = "res://reports/casualty-0.4.0/"
const CACHE = "res://.cache/casualty-0.4.0/"
var checks: Array = []
var failures: Array = []

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(CACHE))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(CACHE+"legacy.json.pre-casualty.bak"))
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks.append(label)
	if not ok: failures.append(label); push_error(label)

func fresh():
	var g=State.new();g.new_game();g.save_path=CACHE+"working.json";return g

func write_checkpoint(state: Dictionary) -> String:
	var path=CACHE+"legacy.json"
	var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(state));f.close();return path

func legacy_fields(state: Dictionary) -> void:
	state.schema=2
	state.flags.erase("treatment_sources");state.flags.erase("treatment_used")
	for unit in state.roster.values()+state.units:
		for key in ["dying","ever_dying","treatment_count"]:unit.erase(key)
	if not state.get("battle_start_snapshot",{}).is_empty():legacy_fields(state.battle_start_snapshot)

func unlock_west(g) -> void:
	g.cleared_stages.append_array([101,102,103]);g.flags.cooperation_done=true;g.ensure_treatment_sources()
	g.mode="hub";g.hub_record="H04"

func growth(unit: Dictionary) -> Dictionary:
	var result={}
	for key in ["level","exp","max_hp","strength","skill","speed","luck","defence","class_id","magic_flags","magic_level","growths","resistance"]:
		if unit.has(key):result[key]=unit[key]
	return result

func run() -> void:
	var g=fresh()
	check(g.treatment_remaining()==0,"New western game has no premature source")
	g.world_node=2;check(g.start_battle(101),"Ordinary first battle starts")
	var victim=g.find_unit("daan");victim.level=4;victim.exp=73;victim.strength+=2;victim.item_id=11
	var before=growth(victim);var stored=g.convoy.alm.count(11);var membership=g.party.duplicate()
	g.commit_strike({"attacker":str(g.battle_data.boss_id),"defender":"daan","hp_after":0})
	check(g.is_dying(victim) and not victim.dead,"Fatal strike records dying, never death")
	check(g.party==membership and g.parties.alm.has("daan"),"Dying member remains in original party")
	check(growth(g.roster.daan)==before,"Immediate injury persistence retains current battle growth and EXP")
	check(victim.item_id==0 and g.roster.daan.item_id==0 and g.convoy.alm.count(11)==stored+1,"Held equipment returns once to original convoy")
	g.Inventory.on_death(g,victim)
	check(g.convoy.alm.count(11)==stored+1,"Repeated injury processing cannot duplicate equipment")
	check(not g.exchange_items("daan","otto"),"Dying member cannot exchange gear")
	check(not g.promote_unit("daan",2).get("valid",false),"Dying member cannot promote")
	check(not g.support_targets(g.find_unit("hunapu"),35).has(victim),"Ordinary healing cannot target dying member")
	check(g.save_game(),"Active injured battle saves schema 3")
	var reload=State.new();reload.save_path=g.save_path
	check(reload.load_game() and reload.is_dying(reload.roster.daan),"Active injured battle reloads")
	check(reload.retry_battle() and not reload.is_dying(reload.roster.daan) and int(reload.find_unit("daan").hp)>0,"Retry reverses only injury caused in current battle")
	g.battle_outcome="victory";check(g.complete_battle(),"Victory settles with injured participant")
	check(growth(g.roster.daan)==before and not g.victory_rewards.any(func(r):return r.unit=="daan"),"Dying participant receives no victory EXP and loses no earned EXP")
	g.mode="world";g.world_node=3
	check(g.start_battle(102) and g.find_unit("daan").is_empty(),"Next battle excludes dying member without removing roster")
	check(g.retry_battle() and g.is_dying(g.roster.daan) and g.find_unit("daan").is_empty(),"Retry retains injury predating battle")
	check(not g.treat_member("daan").valid,"Treatment cannot occur in battle")
	g=fresh();g.roster.otto.level=6;g.roster.otto.exp=89;g.roster.otto.strength+=5;g.roster.otto.hp=0;g.roster.otto.dead=true;g.roster.otto.item_id=11
	g.roster.beck=g._initial_character("beck");g.roster.beck.dead=true;g.roster.beck.hp=0
	unlock_west(g);g.save_game();var raw=State.read_json(g.save_path);legacy_fields(raw)
	var legacy_growth=growth(raw.roster.otto);var old_bag=raw.convoy.alm.count(11)
	reload=State.new();reload.save_path=write_checkpoint(raw)
	check(reload.load_game(),"Schema 2 legacy casualty checkpoint migrates")
	check(reload.is_dying(reload.roster.otto) and not reload.roster.otto.dead and reload.party.has("otto"),"Only recruited casualty becomes dying and remains in party")
	check(reload.roster.beck.dead and not reload.roster.beck.dying and not reload.party.has("beck"),"Unrecruited NPC's actual death remains irreversible")
	check(growth(reload.roster.otto)==legacy_growth,"Legacy migration preserves growth and current EXP")
	check(reload.convoy.alm.count(11)==old_bag+1 and reload.roster.otto.item_id==0,"Legacy held equipment is preserved in original convoy")
	check(reload.treatment_remaining()==1,"Already completed D12 grants one western share")
	var convicted=reload.roster.beck.duplicate(true)
	check(not reload.treat_member("beck").valid and reload.roster.beck==convicted,"Spring cannot resurrect an unrecruited NPC")
	var treatment=reload.treat_member("otto")
	check(treatment.valid and reload.treatment_remaining()==0,"Western spring consumes exactly one share")
	check(not reload.is_dying(reload.roster.otto) and reload.roster.otto.hp==reload.roster.otto.max_hp,"Spring restores full HP and battle eligibility")
	check(growth(reload.roster.otto)==legacy_growth and reload.roster.otto.treatment_count==1,"Treatment preserves EXP and all growth; records personal use")
	var backup=State.read_json(reload.save_path+".pre-casualty.bak")
	check(FileAccess.get_file_as_string(reload.save_path+".pre-casualty.bak")==JSON.stringify(raw),"First migrated write keeps exact original checkpoint in backup")
	check(not reload.treat_member("otto").valid,"Repeated confirmation cannot consume or duplicate treatment")
	var inventory=reload.convoy.duplicate(true)
	var saved=reload.save_game();var loaded=reload.load_game()
	check(saved and loaded and reload.convoy==JSON.parse_string(JSON.stringify(inventory)) and reload.treatment_remaining()==0,"Schema 3 reload neither duplicates equipment nor replenishes used share")
	check(State.read_json(reload.save_path+".pre-casualty.bak")==backup,"Later saves do not overwrite original migration backup")
	reload.roster.otto.hp=0;reload.story_on_death(reload.roster.otto)
	check(reload.is_dying(reload.roster.otto) and reload.party.has("otto") and not reload.treat_member("otto").valid,"Second injury remains in party but cannot be treated twice")
	check(reload.save_game() and reload.load_game(),"Second-injury record persists")
	var original=State.read_json(reload.save_path)
	for kind in ["dying_type","personal_limit","quota_negative","future_source"]:
		var invalid=original.duplicate(true)
		match kind:
			"dying_type":invalid.roster.otto.dying="yes"
			"personal_limit":invalid.roster.otto.treatment_count=2
			"quota_negative":invalid.flags.treatment_used.alm=-1
			"future_source":invalid.flags.treatment_sources.meeting_camp=true
		var preserved=reload.roster.duplicate(true);reload.save_path=write_checkpoint(invalid)
		check(not reload.load_game() and reload.roster==preserved,"Corrupt injury save rejected atomically: "+kind)
	g=fresh();g.world_node=2;g.start_battle(101);g.find_unit("daan").level=5;g.find_unit("daan").exp=84;g.find_unit("daan").hp=0;g.Inventory.on_death(g,g.find_unit("daan"));g.save_game()
	raw=State.read_json(g.save_path);legacy_fields(raw);raw.roster.daan.dead=false;raw.roster.daan.hp=raw.roster.daan.max_hp
	reload=State.new();reload.save_path=write_checkpoint(raw)
	check(reload.load_game() and reload.roster.daan.level==5 and reload.roster.daan.exp==84 and reload.is_dying(reload.roster.daan),"Legacy in-progress zero-HP actor preserves newer tactical growth")
	check(reload.retry_battle() and not reload.is_dying(reload.roster.daan),"Migrated retry snapshot retains pre-injury state")
	var chapter_end=fresh();chapter_end.save_path="res://reports/campaign/natural-chapter-end-save.json"
	check(chapter_end.load_game(),"Real shipped schema-1 western chapter-end save migrates")
	chapter_end.save_path=CACHE+"chapter-transition.json";var west=chapter_end.roster.duplicate(true);var west_stock=chapter_end.flags.treatment_used.duplicate(true)
	check(chapter_end.begin_chapter_two() and chapter_end.roster.otto==west.otto and chapter_end.flags.treatment_used==west_stock,"Chapter transition preserves western wounds growth equipment and stock")
	check(chapter_end.treatment_remaining()==0,"Eastern source remains locked before F24 and settlement")
	chapter_end.cleared_stages.append(204);chapter_end.flags.islanders_settled=true;chapter_end.ensure_treatment_sources()
	chapter_end.mode="hub";chapter_end.hub_record="H25";var east=chapter_end.roster.lisa;east.hp=0;east.exp=67;east.level=4;chapter_end.story_on_death(east);chapter_end.Inventory.on_death(chapter_end,east)
	var eastern=growth(east);var west_unchanged=chapter_end.convoy.alm.duplicate()
	check(chapter_end.treatment_remaining()==1 and chapter_end.treat_member("lisa").valid,"F24 settlement opens independent eastern share")
	check(growth(chapter_end.roster.lisa)==eastern and chapter_end.convoy.alm==west_unchanged,"Eastern treatment preserves growth and western inventory")
	chapter_end.ensure_treatment_sources();check(chapter_end.treatment_remaining()==0,"Repeated island settlement does not replenish share")
	var real=State.new();real.save_path="res://reports/chapter2/play/natural-chapter-end-save.json"
	check(real.load_game(),"Real shipped eastern end save migrates")
	for id in ["lisa","mireille"]:
		check(real.party.has(id) and real.is_dying(real.roster[id]) and not real.roster[id].dead,"Real legacy eastern casualty retained as dying: "+id)
	check(real.flags.treatment_sources.size()<=2,"Only first-two-chapter sources exist")
	var failure=fresh();unlock_west(failure);failure.roster.otto.hp=0;failure.story_on_death(failure.roster.otto)
	var prior=failure.roster.duplicate(true);var shares=failure.flags.treatment_used.duplicate(true)
	failure.save_path=CACHE+"missing-parent/no-save.json"
	check(not failure.treat_member("otto").valid and failure.roster==prior and failure.flags.treatment_used==shares,"Failed save rolls back treatment and stock atomically")
	var hero=fresh();hero.world_node=2;hero.start_battle(101);hero.find_unit("hunapu").hp=0;hero.story_on_death(hero.find_unit("hunapu"))
	check(hero.check_outcome()=="defeat" and "濒死" in str(hero.flags.quest.failed_reason),"Leader injury still fails battle with dying wording")
	check(hero.flags.treatment_used=={"alm":0,"celica":0},"Leader failure never consumes treatment")
	var story=State.new();story.save_path="res://reports/chapter2/play/natural-after-204-save.json"
	check(story.load_game(),"Story branch uses genuine eastern checkpoint")
	story.units.clear()
	story.roster.carlo.hp=0;story.story_on_death(story.roster.carlo);story.story_events.clear()
	story.queue_lines("卡洛：这次我去送遗物，报酬先留下。")
	var page=story.story_events[0].pages[0]
	check(page.speaker=="固定舵手" and "接受照护" in page.text and not "留下的船牌" in page.text,"Dying Carlo's commitment is delegated without a false death narrative")
	story.stage_id=212;story.battle_data=story.stages[212].duplicate(true);story.units.clear()
	check("接受照护" in story.ChapterTwo._mid_lines(story),"S22 dialogue acknowledges Carlo's injury instead of relic treatment")
	var report={"passed":failures.is_empty(),"checks":checks,"failures":failures,"scope":"Directed injury, equipment conservation, schema 1/2 migration, retry snapshot, personal/army treatment limits and first-two-chapter gates; no forced natural-play claim."}
	var f=FileAccess.open(OUT+"state-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("CASUALTY_CHECKS ",checks.size()," FAILURES ",failures)
	quit(0 if failures.is_empty() else 1)
