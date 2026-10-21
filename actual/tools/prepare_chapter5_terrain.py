from pathlib import Path
from PIL import Image
import shutil,json,subprocess
R=Path(__file__).resolve().parents[1]
src=Path('/Users/gcc/.codex/generated_images/01a14ae1-aea8-7f82-b9a5-f624cf3aba3f/exec-536cd78f-89dc-4590-b123-ff7d209f5515.png')
if (R/'source/chapter5/terrain-original.png').exists():src=R/'source/chapter5/terrain-original.png'
else:shutil.copy2(src,R/'source/chapter5/terrain-original.png')
im=Image.open(src).convert('RGBA');old=Image.open(R/'assets/chapter2/chapter2-tiles.png').convert('RGBA');atlas=Image.new('RGBA',(old.width,old.height+16));atlas.alpha_composite(old);start=(old.height//16)*32
for row in range(4):
 for col in range(4):
  box=(round(col*im.width/4),round(row*im.height/4),round((col+1)*im.width/4),round((row+1)*im.height/4))
  cut=im.crop(box).resize((16,16),Image.Resampling.LANCZOS);atlas.alpha_composite(cut,((row*4+col)*16,old.height))
path=R/'assets/chapter5/temple-tiles.png';atlas.save(path);subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','4',str(path)],check=True)
(R/'assets/chapter5/terrain.json').write_text(json.dumps({'start':start,'columns':32,'size':atlas.size,'bytes':path.stat().st_size,'materials':{'ivory':list(range(start,start+4)),'teal':list(range(start+4,start+8)),'sandstone':list(range(start+8,start+12)),'garden':list(range(start+12,start+16))}},indent=2))
print(atlas.size,path.stat().st_size)
