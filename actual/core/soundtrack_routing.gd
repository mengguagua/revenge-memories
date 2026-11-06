extends RefCounted
## Pure selection rules for the original score; source request numbers are only
## compatibility aliases. Actual campaign stage/room identity takes priority.

static func context_track(score: Dictionary, context: Dictionary) -> String:
	var routing: Dictionary = score.get("routing", {})
	var view := str(context.get("view", ""))
	var mode := str(context.get("mode", ""))
	if view in ["journal", "journal_confirm"]:
		if str(context.get("journal_intent", "load")) == "save":
			view = str(context.get("journal_return_view", mode))
		else:
			return "rm_title"
	if view == "title":
		return "rm_title"
	if view == "ending" or mode == "ending":
		return "rm_ending"
	if view == "combat" and not bool(context.get("combat_support",false)):
		var duel=str(routing.get("duel_attack",""))
		if not duel.is_empty():return duel
	if view == "plot":
		var story: Dictionary = routing.get("story_by_existing_callback", {})
		var callback := str(context.get("plot_callback", ""))
		if story.has(callback):
			return str(story[callback])
		view = str(context.get("plot_return", mode))
	if view in ["hub", "village", "dialogue"] or mode == "hub":
		return str(routing.get("hub_by_id", {}).get(str(context.get("hub_record", "")), "rm_hub_hearth"))
	if view in ["world", "overview", "chapter", "chapter_end"] or mode == "world":
		return str(routing.get("world_by_chapter", {}).get(str(context.get("chapter", 1)), "rm_world_ch1"))
	if view in ["battle", "combat", "battle_story", "reward", "victory", "defeat", "loot", "loot_confirm"] or mode in ["battle", "victory", "defeat"]:
		return stage_track(score, int(context.get("stage_id", 0)))
	return ""

static func stage_track(score: Dictionary, stage_id: int) -> String:
	return str(score.get("routing", {}).get("stage_by_id", {}).get(str(stage_id), ""))

static func resolve(score: Dictionary, key: String, context: Dictionary = {}) -> String:
	var tracks: Dictionary = score.get("tracks", {}).duplicate(false)
	tracks.merge(score.get("additional_tracks",{}))
	if tracks.has(key):
		return key
	var routing: Dictionary = score.get("routing", {})
	var mapped := ""
	if key.begins_with("request_"):
		mapped = str(routing.get("legacy_music_requests", {}).get(key.substr(8).to_upper(), ""))
	else:
		mapped = str(routing.get("legacy_named_aliases", {}).get(key, ""))
	if mapped.is_empty() or not tracks.has(mapped):
		return ""
	# Short event cues never turn into the current background track.
	if str(tracks[mapped].get("kind", "bgm")) == "jingle":
		return mapped
	var current := context_track(score, context)
	return current if not current.is_empty() else mapped
