from pathlib import Path
import json
import subprocess
import sys
from PIL import Image, ImageChops, ImageStat

root=Path(__file__).resolve().parents[1]
captures=Path("/private/tmp/map-ambient-20261112")
mode=sys.argv[1]
report=json.loads((captures/f"{mode}-captures.json").read_text())
assert report["passed"]
rows=[]
for entry in report["maps"]:
    assert entry['frames']==96, 'Only encode completed eight-second captures'
    code=entry["code"]
    before=captures/mode/code/"before"
    after=captures/mode/code/"after"
    target=root/"media"/f"{code}-{mode}.mp4"
    # Integer enlargement before 4:2:0 encoding keeps logical pixel edges aligned
    # to chroma blocks while retaining mobile-browser MP4 compatibility.
    scale="scale=iw*2:ih*2:flags=neighbor," if mode=="map" else ""
    if not target.exists() or target.stat().st_mtime < (after/f'{entry["frames"]-1:04d}.png').stat().st_mtime:
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg","-hide_banner","-loglevel","error","-y",
            "-framerate","12","-i",str(before/"%04d.png"),
            "-framerate","12","-i",str(after/"%04d.png"),
            "-filter_complex",f"[0:v][1:v]hstack,{scale}format=yuv420p[v]",
            "-map","[v]","-frames:v",str(entry["frames"]),
            "-c:v","libx264","-preset","fast","-crf","16",
            "-movflags","+faststart","-an",str(target)
        ],check=True)
    a=Image.open(before/"0000.png").convert("RGB")
    b=Image.open(after/"0000.png").convert("RGB")
    side=Image.new("RGB",(a.width*2,a.height))
    side.paste(a,(0,0));side.paste(b,(a.width,0))
    poster=root/"media"/f"{code}-{mode}.webp"
    side.save(poster,format="WEBP",lossless=True,method=6)
    delta=ImageChops.difference(a,b)
    changed=sum(max(pixel)>8 for pixel in delta.getdata())
    last=min(entry["frames"]-1,17)
    c=Image.open(before/f"{last:04d}.png").convert("RGB")
    d=Image.open(after/f"{last:04d}.png").convert("RGB")
    motion=ImageChops.difference(delta,ImageChops.difference(c,d))
    assert delta.getbbox() and motion.getbbox(), f"{code} has no animated environmental change"
    assert entry["source_unchanged"] and entry["game_state_unchanged"]
    entry.update(presentation_revision="all40-reduced-treetop-20261112",video_bytes=target.stat().st_size,poster_bytes=poster.stat().st_size,
                 environmental_pixels_over_8=changed,
                 changed_bbox=list(delta.getbbox()),motion_bbox=list(motion.getbbox()))
    if poster.stat().st_size >= 200_000:
        entry["poster_quality_note"]="Lossless paired native-pixel reference retained for fine terrain and edge clarity."
    rows.append(entry)
    print(mode,code,changed,target.stat().st_size,flush=True)
(root/f"{mode}-verification.json").write_text(json.dumps(
    {"passed":True,"capture":report["capture"],"mode":mode,"maps":rows},ensure_ascii=False,indent=2)+"\n")
