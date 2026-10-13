#!/usr/bin/env python3
"""Add the opening's reviewed Chinese translation without changing source text or rules."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "alm": "阿尔姆",
    "mycen": "麦森",
    "lukas": "卢卡斯",
    "gray": "格雷",
    "tobin": "托宾",
    "kliff": "克里夫",
}

DIALOGUES = {
    "training": [
        "阿尔姆，休息一下吧。",
        "今天的剑术修行就到这里。你可以去玩了。",
        "不过，不许到村子外面去。",
        "最近，连这附近也有山贼出没。",
    ],
    "friends_greeting": [
        "嗨，阿尔姆，你来得正好。",
        "你也来听听这位先生说的事吧。",
    ],
    "lukas_report": [
        "那个臭名昭著的德赛将军，终于发动了政变。",
        "索菲亚城被德赛的军队占领，国王也惨遭杀害。",
        "德赛是个残暴的人。每天都有许多人遭受他的迫害。",
        "我们组织了解放军，与德赛作战。可惜，战况一直不顺利。",
        "所以，我来这里，是想请麦森将军助我们一臂之力。",
    ],
    "kliff_reaction": [
        "哎，你爷爷以前居然是个将军啊？",
    ],
    "tobin_encouragement": [
        "阿尔姆，全国的人都在受苦。我们一起去帮他们吧！",
    ],
    "gray_advice": [
        "我们在这里等你，你去求求爷爷吧。",
    ],
    "mycen_refusal": [
        "什么？你说要加入解放军！",
        "不行！我绝不允许！",
        "你不能去战斗，那只会让你伤心。",
    ],
    "alm_volunteers": [
        "他不肯答应吗……真遗憾。",
        "看来麦森将军上了年纪，也变得胆怯了。",
        "他曾是索菲亚最出色的勇士，深受国民敬重啊……",
        "等等！我替爷爷加入解放军！",
        "什么！你愿意代替麦森将军，跟我们一起去吗？",
        "谢谢你！伙伴们也一定会很高兴。",
        "那就跟我一起，去解放军的据点吧。",
    ],
    "lukas_join_repeat": [
        "谢谢你！伙伴们也一定会很高兴。",
        "那就跟我一起，去解放军的据点吧。",
    ],
    "gray_joins": [
        "阿尔姆，我也去。",
        "这座拉姆村，迟早也会遭到袭击吧？",
        "既然这样，我们先去打倒那个叫德赛的家伙！",
    ],
    "tobin_joins": [
        "阿尔姆，你可是我们的领头人。我们当然不能让你一个人去！",
        "一起夺回索菲亚城吧！",
    ],
    "kliff_joins": [
        "我！？……让我想想……",
        "好吧，我也跟你们一起去。",
        "不过，遇到危险的时候，可一定要救我啊。",
        "我们不像你，还不太会战斗呢。",
    ],
}

INTRO = [
    "很久以前，这片大地上存在着被称为神的生命。",
    "在名为瓦伦西亚的偏远岛屿上，也有多玛与米拉这对兄妹神。",
    "然而……",
    "多玛坚信力量高于一切，绝不允许人们堕落。",
    "而他的妹妹米拉，梦想着一个万物都能自由嬉戏的乐园。为此，兄妹之间展开了激烈的争斗。",
    "经过漫长、漫长的黑暗岁月……",
    "他们终于缔结了一项盟约。",
    "将瓦伦西亚一分为二：北方由多玛统治，南方由米拉统治……",
    "此后，数千年的时光流逝。",
    "在两位神各自的统治下，诞生了两个王国。",
    "南方的索菲亚王国，因富足而堕落。",
    "北方的利盖尔帝国，因强大而忘却了温柔。",
    "两个国家各自埋藏着矛盾，岁月不断流逝。",
    "终于……",
    "利盖尔与索菲亚的王室中，诞生了两个将改变瓦伦西亚命运的生命。",
    "从那一天起，瓦伦西亚的历史再次转动，迎来了战火纷飞的时代。",
]

UI = {
    "attack": "攻击",
    "wait": "待机",
    "end_turn": "结束回合",
    "retreat": "撤退",
    "auto_assault": "全军突击",
    "gather": "全军集合",
    "status": "部队状态",
    "suspend": "中断存档",
    "player_phase": "我方回合",
    "enemy_phase": "敌方回合",
    "level": "等级：",
    "hp": "生命：",
    "strength": "力量：",
    "skill": "技巧：",
    "speed": "速度：",
    "luck": "幸运：",
    "defence": "防御：",
    "move": "移动：",
    "game_over": "战斗失败",
    "no_item": "无道具",
}


def without_zh(value):
    """Exclude localized fields so all source/rule values can be compared."""
    if isinstance(value, dict):
        return {key: without_zh(item) for key, item in value.items() if not key.endswith("_zh")}
    if isinstance(value, list):
        return [without_zh(item) for item in value]
    return value


def localize():
    opening_path = ROOT / "data/opening.json"
    battle_path = ROOT / "data/first_battle.json"
    opening = json.loads(opening_path.read_text())
    battle = json.loads(battle_path.read_text())
    source_opening = without_zh(opening)
    source_battle = without_zh(battle)
    assert set(DIALOGUES) == set(opening["dialogues"])
    page_count = 0
    for key, translations in DIALOGUES.items():
        pages = opening["dialogues"][key]
        assert len(pages) == len(translations), key
        for page, chinese in zip(pages, translations):
            page["text_zh"] = chinese
            page_count += 1
        source_label = pages[0]["source_label"]
        labelled_pages = opening["dialogues_by_label"][source_label]
        assert len(labelled_pages) == len(translations), source_label
        for page, chinese in zip(labelled_pages, translations):
            page["text_zh"] = chinese
    assert page_count == 35
    assert len(INTRO) == len(opening["attract_intro"]["paragraphs_ja"]) == 16
    opening["attract_intro"]["paragraphs_zh"] = INTRO
    opening["title"]["options_zh"] = ["开始新游戏", "继续游戏"]
    opening["chapter"]["title_zh"] = "前往索菲亚！"
    for data in (opening, battle):
        for character, entry in data["characters"].items():
            entry["name_zh"] = NAMES[character]
    for enemy in battle["enemies"]:
        enemy["name_zh"] = "山贼"
    assert set(UI) == set(battle["ui_ja"])
    battle["ui_zh"] = {
        key: {**value, "text": UI[key]} for key, value in battle["ui_ja"].items()
    }
    assert without_zh(opening) == source_opening, "Opening source fields changed"
    assert without_zh(battle) == source_battle, "Battle source/rule fields changed"
    opening_path.write_text(json.dumps(opening, ensure_ascii=False, indent=2) + "\n")
    battle_path.write_text(json.dumps(battle, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "dialogue_groups": len(DIALOGUES),
        "dialogue_pages_zh": page_count,
        "labelled_dialogue_pages_zh": sum(len(pages) for pages in opening["dialogues_by_label"].values()),
        "intro_paragraphs_zh": len(INTRO),
        "title_options_zh": 2,
        "opening_characters_zh": len(opening["characters"]),
        "battle_characters_zh": len(battle["characters"]),
        "enemies_zh": len(battle["enemies"]),
        "battle_ui_entries_zh": len(UI),
        "original_source_and_rules_unchanged": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    localize()
