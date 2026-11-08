"""Inspect the affected review cases at their recorded native pixel size."""

from math import floor
from pathlib import Path
from PIL import Image, ImageDraw

from build_gallery import OUT, R2, read_case, read_js


class Painter:
    def __init__(self, case, root):
        self.case = case
        self.root = root
        self.effects = read_js(root / "catalog.js")["effects"]
        self.images = {}

    def image(self, path):
        if path not in self.images:
            with Image.open(self.root / path) as image:
                self.images[path] = image.convert("RGBA")
        return self.images[path]

    def layer(self, destination, name, index):
        case = self.case
        mapping = case.get("layerMap", {}).get(name)
        tile = mapping[index] if mapping is not None else index
        spec = case.get("layerSpecs", {}).get(name, {"size": [592, 240], "at": [0, 0]})
        width, height = spec["size"]
        sheet = self.image(case["atlases"][name][tile // case["atlasFrames"]])
        local = tile % case["atlasFrames"]
        x = local % case["atlasCols"] * width
        y = local // case["atlasCols"] * height
        destination.alpha_composite(sheet.crop((x, y, x + width, y + height)), tuple(spec["at"]))

    def effect(self, overlay, plan, time, frame):
        elapsed = time - plan["start"]
        if elapsed < 0 or time >= plan.get("until", float("inf")):
            return
        point = plan["track"][frame] if "track" in plan else plan["anchor"]
        if point is None:
            return
        effect = self.effects[plan["effect"]]
        n = floor(elapsed * effect["fps"] + 1e-6)
        if not effect["loop"] and n >= effect["frames"]:
            return
        n %= effect["frames"]
        width, height = effect["frameSize"]
        pivot_x, pivot_y = effect["pivot"]
        sheet_x = n % effect["columns"] * width
        sheet_y = n // effect["columns"] * height
        im = self.image(effect["path"]).crop((sheet_x, sheet_y, sheet_x + width, sheet_y + height))
        if plan.get("flip"):
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            pivot_x = width - pivot_x
        alpha = plan.get("alpha", 1)
        if "fadeIn" in plan:
            alpha *= min(1, elapsed / plan["fadeIn"])
        if "fadeOut" in plan:
            alpha *= min(1, (plan["until"] - time) / plan["fadeOut"])
        if alpha < 1:
            im.putalpha(im.getchannel("A").point(lambda channel: round(alpha * channel)))
        overlay.alpha_composite(im, (round(point[0]) - pivot_x, round(point[1]) - pivot_y))

    def render(self, time):
        case = self.case
        frame = min(len(case["timeline"]) - 1, max(0, floor(time * 60 + 1e-6)))
        index = case["timeline"][frame]
        before = Image.new("RGBA", (592, 240))
        if "plate" in case["atlases"]:
            self.layer(before, "plate", index)
        self.layer(before, "current", index)
        after = before.copy()
        if case.get("fullReplacement") or case.get("suppressFlash") or time >= case.get("replaceEffectsFrom", float("inf")):
            self.layer(after, "clean", index)
        overlay = Image.new("RGBA", (592, 240))
        for plan in case["fxPlan"]:
            self.effect(overlay, plan, time, frame)
        x, y, width, height = case["field"]
        after.alpha_composite(overlay.crop((x, y, x + width, y + height)), (x, y))
        return before, after


def plate(rows, filename, scale=1):
    width = max(cell[1].width for row in rows for cell in row)
    height = max(cell[1].height for row in rows for cell in row)
    columns = max(len(row) for row in rows)
    cell_width, cell_height = width * scale + 12, height * scale + 29
    output = Image.new("RGB", (columns * cell_width + 12, len(rows) * cell_height + 12), "#18262f")
    draw = ImageDraw.Draw(output)
    for row_no, row in enumerate(rows):
        for col_no, (label, tile) in enumerate(row):
            x, y = 10 + col_no * cell_width, 7 + row_no * cell_height
            draw.text((x, y), label, fill="#e4ebe6")
            if scale != 1:
                tile = tile.resize((tile.width * scale, tile.height * scale), Image.Resampling.NEAREST)
            output.paste(tile, (x, y + 17))
    output.save(OUT / "qa" / filename)


def close_tile(painter, t, candidate=True):
    im = painter.render(t)[int(candidate)]
    x, y, width, _ = painter.case["crop"]
    height = 240 if painter.case["family"] == "cinema" else 128
    return im.crop((x, y, x + width, y + height))


def make_sheets():
    catalog = read_js(OUT / "catalog.js")
    featured = {row["name"]: row["case"] for row in catalog["revisionRows"]}
    fire_rows = []
    for name, key in [("Fire", featured["火球"]), ("Ragnarok", featured["诸神黄昏"])]:
        for root, version in [(R2, "R2"), (OUT, "R3")]:
            case = read_case(root, key)
            painter = Painter(case, root)
            fire_rows.append([(name + " " + version + " " + phase, close_tile(painter, t))
                              for phase, t in [("charge", case["chargeTime"]), ("flight", case["actionTime"]),
                                               ("contact", case["impactTime"])]])
    plate(fire_rows, "fire-palette-ab.png")

    stages = []
    for name, label in [("圣光", "Holy"), ("箭雨", "Arrow rain"), ("吸血", "Drain")]:
        case = read_case(OUT, featured[name])
        painter = Painter(case, OUT)
        stages.append([
            (label + " / new opening", close_tile(painter, case["chargeTime"])),
            ("Original animation", close_tile(painter, case["actionTime"], False)),
            ("R3 same animation", close_tile(painter, case["actionTime"])),
            ("New ending", close_tile(painter, case["impactTime"])),
        ])
    plate(stages, "preserved-spell-stages.png")

    endings = []
    for name, label in [("光环", "Halo"), ("史莱姆", "Slime")]:
        case = read_case(OUT, featured[name])
        painter = Painter(case, OUT)
        endings.append([
            (label + " / original opening", close_tile(painter, case["chargeTime"])),
            ("Preserved before contact", close_tile(painter, case["contact"] - .07)),
            ("New contact ending", close_tile(painter, case["impactTime"])),
            ("New decay", close_tile(painter, case["contact"] + .49)),
        ])
    plate(endings, "custom-endings.png")

    cinema = []
    for name in ["fire", "holy"]:
        case = read_case(OUT, f"cinema-eileen-{name}-advanced")
        painter = Painter(case, OUT)
        cinema.append([(name + " opening", close_tile(painter, case["chargeTime"])),
                       (name + " result", close_tile(painter, case["impactTime"]))])
    plate(cinema, "cinema-spells.png")


if __name__ == "__main__":
    make_sheets()
