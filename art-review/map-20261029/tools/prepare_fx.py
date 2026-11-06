"""Technical sprite-sheet slicing; source alpha and full cells are preserved."""
import json, shutil, sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'source/map-20261029'
SOURCE.mkdir(parents=True,exist_ok=True)
mapping=json.loads((OUT/'sources/generated-files.json').read_text())
manifest_path=OUT/'sources/fx-manifest.json'
records=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
only=set(sys.argv[1:])
for key,path in mapping.items():
    if only and key not in only:continue
    original=Path(path);image=Image.open(original).convert('RGBA')
    assert image.size==(1536,1024),image.size
    assert image.getchannel('A').getextrema()[0]==0,'Opaque source'
    shutil.copy2(original,SOURCE/(key+'-original.png'))
    atlas=Image.new('RGBA',(384,256))
    for i in range(6):
        x=i%3*512;y=i//3*512
        if key=='hunapu-advanced-color-v3':
            # The generated bottom-row peak extends beyond nominal column 1.
            # Cut at the measured transparent gaps, retaining the full taper,
            # then register each frame to its original world-space anchor.
            # This is atlas extraction only; paint colors/alpha stay untouched.
            bounds=[(0,0,512,512),(512,0,1024,512),(1024,0,1536,512),
                    (0,512,577,1024),(577,512,1056,1024),(1056,512,1536,1024)][i]
            cell=Image.new('RGBA',(640,640))
            crop=image.crop(bounds)
            cell.paste(crop,(bounds[0]-x+64,64))
            cell=cell.resize((128,128),Image.Resampling.LANCZOS)
        else:
            cell=image.crop((x,y,x+512,y+512)).resize((128,128),Image.Resampling.LANCZOS)
        atlas.paste(cell,(i%3*128,i//3*128))
    target=OUT/'assets'/(key+'-fx.png');atlas.save(target,optimize=True)
    records=[r for r in records if r['path']!=str(target.relative_to(OUT))]
    records.append(dict(path=str(target.relative_to(OUT)),purpose='MAP专用六阶段透明特效图集',pixels=list(atlas.size),bytes=target.stat().st_size,source=str((SOURCE/(key+'-original.png')).relative_to(ROOT)),original_pixels=list(image.size),alpha=atlas.getchannel('A').getextrema(),quality_note='原图离线保留；六格完整等比采样，128px单格覆盖实际显示分辨率，保留透明辉光。'))
manifest_path.write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps(records,ensure_ascii=False))
