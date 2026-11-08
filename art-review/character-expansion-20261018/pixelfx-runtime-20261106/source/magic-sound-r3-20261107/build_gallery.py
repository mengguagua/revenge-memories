"""Build R3 from the frozen R2 engine frames and review cases."""

from bisect import bisect_right
from collections import Counter
import json
from math import ceil, floor
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent.parent
OUT = BASE / ROOT.name
R2 = BASE / "weapon-magic-r2-20261107"
R2_CAPTURES = ROOT.parent / R2.name / "captures"
R1_SOURCE = ROOT.parent / "full-battle-20261107"
R1_CAPTURES = R1_SOURCE / "captures"
FPS = 60

VISUAL_DIRECTIONS = {
    "fire": ("深红焰核", "火球的蓄势、飞行和爆燃使用深绯红、砖红与橘红。核心仅留少量暖橙亮点。"),
    "ragnarok": ("绯红熔火", "地面聚焰与喷发统一用深红和热橘色。高光集中在焰核与裂口。"),
    "holy": ("启羽与散辉", "原来的圣光飞羽和命中完整保留。开场补一圈灰青羽芒，收尾留下轻薄的碎光。"),
    "rain": ("银芒开场与落屑", "原来的箭群、轨迹和命中完整保留。开场补短银芒，收尾是落点少量银屑。"),
    "halo": ("蓝环舒展", "开场和命中前的原环纹保持原样。结果出现时接上向外舒展的蓝弧，最后化为碎光。"),
    "slime": ("蓝胶塌缩", "原蓝色胶团的开场、抛射和包覆完整保留。结算时胶壳塌缩，蓝色胶滴落地消散。"),
    "drain": ("绯红起纹与消散", "原吸取、回流和生命变化完整保留。开场补一圈暗红收束纹，结束只留短暂的余光。"),
}
ADDITIVE = {"holy", "rain", "drain"}
END_REPLACEMENT = {"halo", "slime"}
RECOLOR = {"fire", "ragnarok"}
MIN_TAIL_DELAY = {"holy": .15, "rain": .065, "drain": .16}

MAP_VOICES = {
    "召唤": "summon", "驱邪": "expel", "幻影": "phantom", "传送": "warp",
    "恢复": "heal", "愈护之环": "heal", "济世·愈护之环": "heal",
    "地震": "quake", "地图伤害": "quake", "焰环": "fieldfire", "引光·焰环": "fieldfire",
}
MONSTER_VOICES = {"日冠聚光": "suncrown", "碎岩喷吐": "rockspit", "蚀息": "rotbreath"}


def read_js(path):
    return json.loads(path.read_text().split("=", 1)[1].rstrip(";\n"))


def read_case(root, key):
    path = root / "cases" / f"{key}.js"
    return json.loads(path.read_text().split("]=", 1)[1].rstrip(";\n"))


def write_js(path, name, value):
    path.write_text(name + "=" + json.dumps(value, ensure_ascii=False, separators=(",", ":")) + ";\n")


def write_case(case):
    prefix = "window.PIXELFX_CASES=window.PIXELFX_CASES||{};window.PIXELFX_CASES["
    path = OUT / "cases" / (case["key"] + ".js")
    write_js(path, prefix + json.dumps(case["key"]) + "]", case)


def capture(key):
    path = next((root / key / "capture.json" for root in (R2_CAPTURES, R1_CAPTURES)
                 if (root / key / "capture.json").is_file()), None)
    if path is None:
        raise FileNotFoundError(key)
    return json.loads(path.read_text())


def source_rows(case, data):
    frames = data["frames"]
    times = [row["t"] for row in frames]
    return [frames[max(0, bisect_right(times, n / FPS + 1e-8) - 1)]
            for n in range(len(case["timeline"]))]


def center_of(effects):
    centers = [(x + w / 2, y + h / 2) for x, y, w, h in (e["rect"] for e in effects)]
    return [median(point[0] for point in centers), median(point[1] for point in centers)]


def first_visible_fx(data, cinema):
    if cinema:
        return next(row for row in data["frames"]
                    if row.get("cinema", {}).get("show", 0) > .95 and row["cinema"].get("effects"))
    return next(row for row in data["frames"] if row.get("effects"))


def observed_release(data, first, contact, cinema):
    """The first travel through the space between the two captured actors."""
    for row in data["frames"]:
        if not first + .18 <= row["t"] <= contact - .14:
            continue
        if cinema:
            scene = row.get("cinema", {})
            if not scene.get("actor") or not scene.get("target") or not scene.get("effects"):
                continue
            ax, tx = scene["actor"][0], scene["target"][0]
            centers = [e["rect"][0] + e["rect"][2] / 2 for e in scene["effects"]]
        else:
            ax, tx = row["actor"][0], row["target"][0]
            centers = [e["point"][0] for e in row.get("effects", []) if not e["bound"]]
        if abs(ax - tx) > 10 and any(.28 < (x - ax) / (tx - ax) < .72 for x in centers):
            return row["t"]
    return None


def last_visible_original_fx(case):
    """Find the last substantive original spell pixels after the result."""
    cached = {}
    contact = case["contact"]
    spec = case["layerSpecs"]["current"]
    if spec != case["layerSpecs"]["clean"]:
        raise ValueError(f"Unequal original FX layers: {case['key']}")
    width, height = spec["size"]
    threshold = max(5, round(width * height * .00016))
    count, columns = case["atlasFrames"], case["atlasCols"]

    def tile(layer, index):
        cell = case["layerMap"][layer][index]
        path = case["atlases"][layer][cell // count]
        if path not in cached:
            with Image.open(R2 / path) as image:
                cached[path] = image.convert("RGB")
        x = (cell % count % columns) * width
        y = (cell % count // columns) * height
        return cached[path].crop((x, y, x + width, y + height))

    last = contact
    measured = {}
    begin = floor(contact * FPS)
    stop = min(len(case["timeline"]), ceil((contact + 2.05) * FPS))
    for frame in range(begin, stop):
        index = case["timeline"][frame]
        if index not in measured:
            red, green, blue = ImageChops.difference(tile("current", index), tile("clean", index)).split()
            mask = ImageChops.lighter(red, ImageChops.lighter(green, blue))
            measured[index] = sum(mask.histogram()[22:]) >= threshold
        if measured[index]:
            last = frame / FPS
    return last


def revision_label(case, kind, label):
    direction, description = VISUAL_DIRECTIONS[kind]
    previous = case.get("design", {}).get("name")
    caption = case["subtitle"].removesuffix(" · " + previous) if previous else case["subtitle"]
    case["subtitle"] = caption + " · " + direction
    case["treatment"] = description
    case["revision"] = 3
    case["changeLabel"] = label
    case["visualRevision"] = kind
    if case.get("design"):
        case["design"]["name"] = direction


def recolor(case, kind):
    for cue in case["fxPlan"]:
        cue["effect"] = cue["effect"].replace("r2-", "r3-", 1)
    revision_label(case, kind, "深红橘焰 · R3")


def retained_spell(case, kind, effects):
    data = capture(case["key"])
    rows = source_rows(case, data)
    cinema = case["family"] == "cinema"
    contact = case["contact"]
    phases = case["spellPhases"]
    old_plan = case["fxPlan"]
    first = first_visible_fx(data, cinema)
    start = first["t"]
    variant = "cinema-" if cinema else ""
    case.pop("fullReplacement", None)
    case.pop("suppressFlash", None)
    case.pop("cinemaEffect", None)
    phases["charge"] = start
    if cinema or kind == "drain":
        release = observed_release(data, start, contact, cinema)
        if release is not None:
            phases["release"] = release
            if cinema:
                case["actionTime"] = release + (contact - release) * .55

    if kind in ADDITIVE:
        open_effect = f"r3-{variant}{kind}-open"
        open_at = max(0, start - (.035 if cinema else .065))
        open_duration = effects[open_effect]["options"]["duration"]
        release = phases["release"]
        open_until = min(open_at + open_duration, max(open_at + .15, release - .025))
        original_end = last_visible_original_fx(case)
        end_at = max(contact + MIN_TAIL_DELAY[kind], original_end + 1 / FPS)
        open_cue = {"effect": open_effect, "start": open_at, "until": open_until,
                    "alpha": .88, "fadeOut": .095}
        end_cue = {"effect": f"r3-{variant}{kind}-end", "start": end_at,
                   "alpha": .84}
        if cinema:
            open_cue["track"] = old_plan[0]["track"]
            end_cue["track"] = old_plan[-1]["track"]
        else:
            # Anchor to the original charge cluster, then follow the same unit.
            center = center_of(first["effects"])
            unit = "target" if kind == "drain" else "actor"
            offset = [center[0] - first[unit][0], center[1] - first[unit][1]]
            if kind == "rain":
                offset[1] -= 9
            open_cue["track"] = [
                [round(row[unit][0] + offset[0]), round(row[unit][1] + offset[1])] for row in rows
            ]
            old_impact = next(cue for cue in old_plan if cue["effect"].endswith("-impact"))
            x, y = old_impact["anchor"]
            if kind == "rain":
                y = min(126, rows[round(contact * FPS)]["target"][1] - 2)
            end_cue["anchor"] = [x, y]
        plan = [open_cue, end_cue]
        if kind == "drain" and case["source"]["event"].get("heal", 0) > 0:
            # A low-opacity fade at the original recipient of the returned energy.
            row = rows[round(end_at * FPS)]
            plan.append({**end_cue, "start": end_at + .09, "alpha": .43,
                         "anchor": [round(row["actor"][0]), round(row["actor"][1] - 31)]})
        case["fxPlan"] = plan
        case["chargeTime"] = open_at + min(.21, (open_until - open_at) * .48)
        case["impactTime"] = end_at + .18
        case["composition"] = "additive"
        phases["charge"] = open_at
        phases["chargeEnd"] = open_until
        phases["ending"] = end_at
        phases["originalFxLastVisible"] = original_end
        revision_label(case, kind, "原演出 + 开场收尾 · R3")
    else:
        # The original opening and arrival stay visible up to the actual result.
        # From that moment, the captured clean layer removes only the old FX.
        pre_contact = rows[max(0, int(contact * FPS) - 2)]
        near_target = [
            fx for fx in pre_contact["effects"] if abs(fx["point"][0] - pre_contact["target"][0]) < 30
        ]
        x = center_of(near_target)[0] if near_target else pre_contact["target"][0]
        y = min(127, pre_contact["target"][1] - 1)
        case["replaceEffectsFrom"] = contact
        case["fxPlan"] = [{"effect": f"r3-{kind}-end", "start": contact,
                           "anchor": [round(x), round(y)], "alpha": 1}]
        case["chargeTime"] = min(contact - .1, start + .28)
        case["impactTime"] = contact + (.26 if kind == "slime" else .20)
        case["composition"] = "new-ending"
        phases["ending"] = contact
        revision_label(case, kind, "原开场 + 新收尾 · R3")


def sound_family(case):
    if case.get("spellPhases"):
        return case["spellPhases"]["kind"]
    group, move = case["family"], case["move"]
    if group == "support":
        return "warp" if move == "传送" else "heal"
    if group == "map":
        return MAP_VOICES.get(move)
    if group == "monster":
        return MONSTER_VOICES.get(move)
    if move == "魔剑":
        return "magicblade"
    return None


def attach_sound(case, family, tracks):
    phase = case.get("spellPhases")
    contact = case["contact"]
    duration = case["duration"]
    # Slightly more headroom for contact sounds in short normal attacks.
    weight = .99 if case["family"] == "cinema" else .88
    cues = []

    def cue(stage, at, label, gain, limit=None):
        key = f"{family}-{stage}"
        clip = tracks[key]
        at = round(max(0, at), 6)
        span = min(clip["duration"], duration - at)
        if limit is not None:
            span = min(span, limit)
        if span < .045:
            return
        cues.append({"id": key, "at": at, "duration": round(span, 6),
                     "gain": round(gain * weight, 4), "label": label})

    if phase:
        opening = phase["charge"]
        release = phase["release"]
    elif case["key"] == "map-quake":
        data = json.loads((R1_SOURCE / "map-captures" / case["key"] / "capture.json").read_text())
        opening = data["frames"][0]["t"]
        release = None
    elif case["family"] == "map":
        lead = .28 if family == "fieldfire" else .22
        opening = min([max(0, contact - lead), *(v["start"] for v in case["fxPlan"])])
        release = None
    else:
        opening = max(0, min(case["actionTime"], contact - .23))
        release = None
    charge_limit = release - opening + .06 if release is not None and release > opening else None
    cue("charge", opening, "开场", .76, charge_limit)
    if release is not None and opening + .085 < release < contact - .035:
        cue("release", release, "释放", .82, contact - release + .035)

    event = case["source"].get("event")
    if not event or event.get("hit") or event.get("heal", 0) or event.get("self_damage", 0):
        result = "恢复" if family == "heal" else "落点" if family == "warp" else "结果"
        cue("resolve", contact, result, 1)
        if case["key"] == "map-warp":
            for plan in case["fxPlan"]:
                if plan["start"] > contact + .3:
                    cue("resolve", plan["start"], "现身", .70)
    if phase and family in ADDITIVE:
        cue("tail", phase["ending"], "收尾", .58)

    case["audioCues"] = sorted(cues, key=lambda row: row["at"])
    case["audioFamily"] = family
    case["audioName"] = tracks[f"{family}-resolve"]["name"]
    case["revision"] = 3


def build():
    catalog = read_js(R2 / "catalog.js")
    atlas = json.loads((OUT / "assets/fx/manifest.json").read_text())
    audio = json.loads((OUT / "qa/audio-generation.json").read_text())
    tracks = {track["id"]: track for track in audio["tracks"]}
    visual_counts, audio_counts = Counter(), Counter()
    mapping = []
    for meta in catalog["cases"]:
        if meta.get("legacy"):
            continue
        case = read_case(R2, meta["key"])
        phase = case.get("spellPhases", {})
        kind = phase.get("kind")
        if kind in RECOLOR:
            recolor(case, kind)
        elif kind in ADDITIVE or kind in END_REPLACEMENT:
            retained_spell(case, kind, atlas["effects"])
        family = sound_family(case)
        if family is None:
            continue
        attach_sound(case, family, tracks)
        write_case(case)
        meta.update(revision=3, subtitle=case["subtitle"], audioFamily=family,
                    visualRevision=case.get("visualRevision"))
        if case.get("visualRevision"):
            visual_counts[kind] += 1
        audio_counts[family] += 1
        mapping.append({
            "id": case["key"], "profile": case["profile"], "title": case["title"],
            "move": case["move"], "program": case["source"]["program"],
            "visual": case.get("composition", "recolor" if kind in RECOLOR else "previous"),
            "contact": case["contact"], "callbacks": case["source"]["contacts"],
            "cue_times": case["audioCues"],
        })

    featured = catalog["featured"]
    featured_by_family = {}
    by_key = {row["key"]: row for row in catalog["cases"]}
    for key in featured:
        kind = by_key[key].get("audioFamily")
        if kind:
            featured_by_family.setdefault(kind, key)
    revision_rows = [
        {"case": featured_by_family[kind], "name": name, "subtitle": subtitle}
        for kind, name, subtitle in [
            ("fire", "火球", "深红焰核"),
            ("ragnarok", "诸神黄昏", "绯红熔火"),
            ("holy", "圣光", "原飞羽与新收尾"),
            ("rain", "箭雨", "原箭群与银屑"),
            ("halo", "光环", "原开场与蓝弧"),
            ("slime", "史莱姆", "原蓝胶与新塌缩"),
            ("drain", "吸血", "原回流与暗红余光"),
        ]
    ]
    featured.extend([
        "cinema-eileen-holy-advanced", "map-eileen-advanced", "map-heal-17",
        "map-warp", "map-full-summon", "map-full-expel", "map-phantom", "map-quake",
    ])
    catalog["effects"].update({key: atlas["effects"][key] for key in atlas["newEffects"]})
    catalog.update(revision=3, defaultCase=revision_rows[0]["case"], revisionRows=revision_rows,
                   updatedCases=len(mapping), visualUpdates=sum(visual_counts.values()),
                   audioCases=len(mapping), soundDesigns=len(audio_counts), audioClips=len(tracks))
    write_js(OUT / "catalog.js", "window.PIXELFX_CATALOG", catalog)
    report = {
        "total": len(catalog["cases"]), "visual_updates": dict(visual_counts),
        "audio_cases": len(mapping), "audio_by_family": dict(audio_counts),
        "sound_designs": len(audio_counts), "audio_clips": len(tracks),
        "capture_baseline": "Same Godot sampling snapshot and unchanged original frames as R2",
    }
    (OUT / "qa/build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "action-effect-audio-mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    build()
