"""Register generated side-arm edits without altering accepted vertical poses."""
from pathlib import Path
from PIL import Image
import subprocess,json
V=Path(__file__).resolve().parents[1]
G='/opt/homebrew/bin/magick'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
o=V/'candidates';o.mkdir(exist_ok=True)
palette=V.parent/'map-motion-review-v2/candidates/hunapu/palette.png'
for version in (1,2):
    raw=V/f'source/side-edit-v{version}.png'
    small=o/f'sheet-v{version}.png'
    run(raw,'-filter','point','-resize','256x192',small)
    run(small,'-alpha','extract','-threshold','50%',o/f'alpha-v{version}.png')
    run(small,'-background','#172638','-alpha','remove','-alpha','off','-dither','None','-remap',palette,o/f'rgb-v{version}.png')
    run(o/f'rgb-v{version}.png',o/f'alpha-v{version}.png','-alpha','off','-compose','CopyOpacity','-composite','-background','black','-alpha','background',o/f'four-color-v{version}.png')
    for f in range(4):
        run(o/f'four-color-v{version}.png','-crop',f'128x96+{128*(f%2)}+{96*(f//2)}','+repage',o/f'v{version}-cell-{f}.png')
run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[o/f'v{version}-cell-{f}.png'for version in (1,2)for f in range(4)],'-tile','4x2','-geometry','128x96+4+4','-background','#d9d6c9',o/'registered-contact.png')
run(o/'registered-contact.png','-filter','point','-resize','400%',V/'reviews/registered-contact-4x.png')
print('Registered 2 generated sheets on the existing 128x96 pixel grid')
