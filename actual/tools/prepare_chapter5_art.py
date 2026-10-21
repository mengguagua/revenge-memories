from pathlib import Path
from PIL import Image
import json, shutil, subprocess
R=Path(__file__).resolve().parents[1]
src=Path('/Users/gcc/.codex/generated_images/01a14ae1-aea8-7f82-b9a5-f624cf3aba3f/exec-a61a90bd-c316-4d2c-98bd-a5a423f35b71.png')
if (R/'source/chapter5/architecture-original.png').exists():src=R/'source/chapter5/architecture-original.png'
out=R/'assets/chapter5';out.mkdir(exist_ok=True)
original=R/'source/chapter5';original.mkdir(parents=True,exist_ok=True);
if src.resolve()!=(original/'architecture-original.png').resolve():shutil.copy2(src,original/'architecture-original.png')
if (original/'architecture-muted-original.png').exists():src=original/'architecture-muted-original.png'
im=Image.open(src).convert('RGBA');assert im.size in [(1774,887),(1773,887)], 'Re-check atlas boundaries before changing source size'
print(im.size)
# Whole independently generated objects; scale uniformly inside native tile footprints.
boxes=[('palace',(0,0,496,443),(112,112)),('infirmary',(497,0,949,443),(96,96)),('sun_gate',(950,0,1348,443),(80,96)),('archive',(1350,0,1774,443),(96,96)),('regulator',(0,445,488,887),(64,64)),('stair',(490,445,949,887),(64,64)),('column',(1076,445,1240,868),(32,80)),('throne',(1335,445,1774,887),(96,96))]
report=[]
for name,box,size in boxes:
 cut=im.crop(box);bbox=cut.getchannel('A').getbbox();cut=cut.crop(bbox)
 cut.thumbnail((size[0]-4,size[1]-4),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',size);canvas.alpha_composite(cut,((size[0]-cut.width)//2,size[1]-cut.height-2))
 path=out/(name+'.png');canvas.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','4',str(path)],check=True)
 report.append(dict(name=name,path='res://assets/chapter5/'+path.name,size=size,bytes=path.stat().st_size,source_box=box,uniform_scale=True,palette='muted-v2' if 'muted' in src.name else 'original',source='source/chapter5/'+src.name))
(out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(report)
