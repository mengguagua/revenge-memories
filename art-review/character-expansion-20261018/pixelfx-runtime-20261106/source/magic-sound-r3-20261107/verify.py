"""Check source-frame preservation, effect bounds, sound timings, and preview assets."""

from array import array
import base64
from collections import Counter
import hashlib
from html.parser import HTMLParser
from io import BytesIO
import json
from math import floor
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit
import wave

from PIL import Image

from build_gallery import (
    ADDITIVE, END_REPLACEMENT, OUT, R2, RECOLOR, ROOT, read_case, read_js, sound_family,
)
from qa_render import Painter, plate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, subject):
    if not condition:
        raise AssertionError(subject)


def frames(root, effect):
    width, height = effect["frameSize"]
    columns = effect["columns"]
    with Image.open(root / effect["path"]) as source:
        image = source.convert("RGBA")
    for frame in range(effect["frames"]):
        x, y = frame % columns * width, frame // columns * height
        yield image.crop((x, y, x + width, y + height))


def palette_value(images):
    totals = pixels = 0
    for image in images:
        opaque = image.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
        hist = image.convert("L").histogram(mask=opaque)
        totals += sum(value * count for value, count in enumerate(hist))
        pixels += sum(hist)
    require(pixels > 0, "missing visible pixels")
    return round(totals / pixels, 2)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in {"href", "src"})


def verify_links():
    checked = 0
    for page in OUT.glob("*.html"):
        parser = Links()
        parser.feed(page.read_text())
        for url in parser.urls:
            parts = urlsplit(url)
            if parts.scheme or not parts.path:
                continue
            target = page.parent / unquote(parts.path)
            # The verification report is created as the last step below.
            require(target.exists() or target == OUT / "qa/verification.json", f"{page.name}: {url}")
            checked += 1
    return checked


def verify_audio(tracks, bank):
    require(set(tracks) == set(bank), "bank inventory")
    seen = set()
    for key, row in tracks.items():
        raw = base64.b64decode(bank[key]["wav"], validate=True)
        checksum = hashlib.sha256(raw).hexdigest()
        require(checksum == row["sha256"] and checksum not in seen, key + " digest")
        require(sha(ROOT / row["master"]) == checksum, key + " master")
        seen.add(checksum)
        receipt = json.loads((ROOT / row["model_source"]).read_text())
        require(receipt["offline"] and sha(ROOT / receipt["source"]) == receipt["sha256"],
                key + " local model provenance")
        with wave.open(BytesIO(raw)) as file:
            require((file.getnchannels(), file.getframerate(), file.getsampwidth()) == (1, 44100, 2),
                    key + " PCM format")
            require(abs(file.getnframes() / 44100 - bank[key]["duration"]) < 1e-6, key + " length")
            signal = array("h", file.readframes(file.getnframes()))
        require(400 < max(abs(sample) for sample in signal) < 18000, key + " amplitude")
        require(row["active_onset_ms"] <= 10 and row["last_10ms_rms_dbfs"] < -60, key + " edges")


def verify_cases(catalog, tracks):
    previous = read_js(R2 / "catalog.js")
    require([c["key"] for c in catalog["cases"]] == [c["key"] for c in previous["cases"]], "inventory order")
    original_assets, used_cues = set(), set()
    count, cue_count = Counter(), 0
    stable = ("source", "contact", "duration", "timeline", "atlasFrames", "atlasCols",
              "atlases", "layerSpecs", "layerMap", "field", "crop", "size")
    original_ranges = 0
    for meta in catalog["cases"]:
        if meta.get("legacy"):
            continue
        key = meta["key"]
        case, old = read_case(OUT, key), read_case(R2, key)
        require(all(case.get(field) == old.get(field) for field in stable), key + " source data")
        original_assets.update(path for paths in case["atlases"].values() for path in paths)
        for plan in case["fxPlan"]:
            require(plan["effect"] in catalog["effects"], key + " unknown effect")
            if "track" in plan:
                require(len(plan["track"]) == len(case["timeline"]), key + " track length")
        kind = case.get("visualRevision")
        if kind in ADDITIVE:
            opening, ending = case["fxPlan"][:2]
            require(case["composition"] == "additive" and not case.get("fullReplacement")
                    and not case.get("suppressFlash") and "replaceEffectsFrom" not in case,
                    key + " original layer")
            require(opening["until"] <= case["spellPhases"]["release"]
                    and ending["start"] > case["spellPhases"]["originalFxLastVisible"]
                    and ending["start"] > case["contact"], key + " opening/ending time")
            require(all(cue["effect"].endswith("-end") for cue in case["fxPlan"][1:]), key + " end cues")
            original_ranges += floor((ending["start"] - opening["until"]) * 60)
            count["additive"] += 1
        elif kind in END_REPLACEMENT:
            require(not case.get("fullReplacement") and not case.get("suppressFlash")
                    and "clean" in case["atlases"] and case["replaceEffectsFrom"] == case["contact"],
                    key + " conditional replacement")
            require(len(case["fxPlan"]) == 1 and case["fxPlan"][0]["start"] == case["contact"],
                    key + " one ending cue")
            original_ranges += floor(case["contact"] * 60)
            count["end_replacement"] += 1
        elif kind in RECOLOR:
            expected = [{**cue, "effect": cue["effect"].replace("r2-", "r3-", 1)} for cue in old["fxPlan"]]
            require(expected == case["fxPlan"] and case.get("fullReplacement") == old.get("fullReplacement"),
                    key + " fire palette-only timing")
            count["recolor"] += 1
        else:
            require(case["fxPlan"] == old["fxPlan"] and case.get("fullReplacement") == old.get("fullReplacement"),
                    key + " untouched visual choreography")
        family = sound_family(case)
        cues = case.get("audioCues", [])
        require(bool(family) == bool(cues), key + " missing or unrelated sound")
        if not cues:
            continue
        count["audio"] += 1
        cue_count += len(cues)
        require(len(cues) >= 2, key + " sound stages")
        require(all(cue["id"] in tracks and cue["id"].startswith(family + "-") for cue in cues),
                key + " audio references")
        require(all(cue["at"] >= 0 and cue["at"] + cue["duration"] <= case["duration"] + 1e-5
                    and cue["duration"] <= tracks[cue["id"]]["duration"] + 1e-6 and 0 < cue["gain"] <= 1
                    for cue in cues), key + " cue bounds")
        contacts = [cue for cue in cues if cue["id"].endswith("-resolve") and cue["label"] != "现身"]
        require(len(contacts) == 1 and abs(contacts[0]["at"] - case["contact"]) < 1e-6,
                key + " one sound at original result")
        require(not any(cue["label"] == "现身" for cue in cues) or key == "map-warp", key + " teleport timing")
        if kind in ADDITIVE:
            require(cues[-1]["id"].endswith("-tail") and abs(cues[-1]["at"] - case["spellPhases"]["ending"]) < 1e-6,
                    key + " finishing sound")
        used_cues.update(cue["id"] for cue in cues)
    require(set(tracks) == used_cues, "all generated sounds used")
    for path in original_assets:
        require(sha(OUT / path) == sha(R2 / path), path + " preserved source/clean atlas")
    for name in ("approved-data.js", "water-palette.js"):
        require(sha(OUT / name) == sha(R2 / name), name)
    return dict(count), len(original_assets), original_ranges, cue_count


def check_fx(catalog):
    manifest = json.loads((OUT / "assets/fx/manifest.json").read_text())
    native_cells = {}
    palette = {}
    for key in manifest["newEffects"]:
        effect = catalog["effects"][key]
        tiles = list(frames(OUT, effect))
        width, height = effect["frameSize"]
        for tile in tiles:
            box = tile.getchannel("A").getbbox()
            if box:
                require(0 < box[0] and box[2] < width and 0 < box[1] and box[3] < height,
                        key + " touches atlas boundary")
        if not effect["loop"]:
            require(tiles[-1].getchannel("A").getbbox() is None, key + " final transparent frame")
        peak = max(tiles, key=lambda image: sum(a * n for a, n in enumerate(image.getchannel("A").histogram())))
        require(peak.getchannel("A").getbbox() is not None, key + " entirely transparent")
        native_cells[key] = peak
        if "fire" in key or "ragnarok" in key:
            old_id = key.replace("r3-", "r2-", 1)
            old_mean = palette_value(frames(R2, catalog["effects"][old_id]))
            new_mean = palette_value(tiles)
            require(new_mean < old_mean * .94, key + " reduction of pale highlights")
            palette[key] = {"r2_visible_luma": old_mean, "r3_visible_luma": new_mean}
    contrast_ids = ["fire-charge", "ragnarok-travel", "holy-open", "rain-end", "halo-end", "slime-end", "drain-end"]
    rows = []
    for key in contrast_ids:
        tile = native_cells["r3-" + key]
        samples = []
        for name, color in [("dark", "#101a25"), ("light", "#c9c9bd")]:
            background = Image.new("RGBA", (144, 118), color)
            background.alpha_composite(tile, ((144 - tile.width) // 2, (118 - tile.height) // 2))
            samples.append((key + " / " + name, background))
        if not rows or len(rows[-1]) == 4:
            rows.append(samples)
        else:
            rows[-1] += samples
    plate(rows, "native-contrast.png")
    return len(native_cells), palette


def verify_key_stages(catalog):
    checked = 0
    keys = [row["case"] for row in catalog["revisionRows"]]
    keys += ["cinema-eileen-holy", "cinema-eileen-holy-advanced"]
    for key in keys:
        case = read_case(OUT, key)
        painter = Painter(case, OUT)
        if not case.get("composition"):
            continue
        for stamp in [case["actionTime"], case["contact"] - .034]:
            original, new = painter.render(stamp)
            require(original.tobytes() == new.tobytes(), key + " original motion pixels")
            checked += 1
        if case["composition"] == "new-ending":
            original, new = painter.render(case["chargeTime"])
            require(original.tobytes() == new.tobytes(), key + " original opening pixels")
            checked += 1
        else:
            original, new = painter.render(case["chargeTime"])
            require(original.tobytes() != new.tobytes(), key + " visible new opening")
        original, new = painter.render(case["impactTime"])
        require(original.tobytes() != new.tobytes(), key + " visible new ending")
        x, y, width, height = case["field"]
        if y + height < 240:
            hud = (0, y + height, 592, 240)
            require(original.crop(hud).tobytes() == new.crop(hud).tobytes(), key + " HUD pixels")
    return checked


def optimize_images():
    rows = []
    paths = sorted((OUT / "assets/fx").glob("r3-*.png")) + sorted((OUT / "qa").glob("*.png"))
    for path in paths:
        with Image.open(path) as im:
            width, height = im.size
            pixels = hashlib.sha256(im.convert("RGBA").tobytes()).digest()
        before = path.stat().st_size
        subprocess.run(["/opt/homebrew/bin/oxipng", "-o", "2", "--strip", "safe", "-t", "1",
                        "--quiet", str(path)], check=True)
        with Image.open(path) as im:
            require(im.size == (width, height) and hashlib.sha256(im.convert("RGBA").tobytes()).digest() == pixels,
                    path.name + " lossless")
        row = {"path": str(path.relative_to(OUT)), "width": width, "height": height,
               "purpose": "QA comparison" if path.parent.name == "qa" else "Native PixelFX atlas",
               "before_bytes": before, "bytes": path.stat().st_size, "lossless": True}
        if row["bytes"] >= 200000:
            row["quality_note"] = "Full-resolution comparison frames retained to preserve detail."
        rows.append(row)
    (OUT / "qa/image-inventory.json").write_text(json.dumps(rows, indent=2) + "\n")
    return len(rows)


def main():
    catalog = read_js(OUT / "catalog.js")
    audio = json.loads((OUT / "qa/audio-generation.json").read_text())
    tracks = {t["id"]: t for t in audio["tracks"]}
    verify_audio(tracks, read_js(OUT / "spell-audio-bank.js"))
    coverage, originals, ranges, cues = verify_cases(catalog, tracks)
    native_atlases, palette = check_fx(catalog)
    comparisons = verify_key_stages(catalog)
    links = verify_links()
    images = optimize_images()
    result = {
        "passed": True, "cases": len(catalog["cases"]), "coverage": coverage,
        "original_atlas_hash_matches": originals, "preserved_source_frame_ranges": ranges,
        "rendered_preserved_stage_comparisons": comparisons,
        "audio_clips": len(tracks), "cue_instances": cues, "native_fx_atlases": native_atlases,
        "fire_palette_luma": palette, "lossless_images": images, "html_links": links,
        "baseline": "R2's frozen, background Godot sampling; no new production writes.",
    }
    (OUT / "qa/verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
