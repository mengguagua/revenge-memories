"""Technical compositing of generated complete arm regions over locked heads/legs."""
from pathlib import Path
from PIL import Image
import json,subprocess
V=Path(__file__).resolve().parents[1];P=V.parent/'map-motion-review-v2'
G='/opt/homebrew/bin/magick';C=V/'candidates';O=V/'deliverables'
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def patch(base,source,box,target):
    x,y,r,b=box
    # Source rectangle includes transparency so old forearms are completely removed.
    run(base,'(',source,'-crop',f'{r-x}x{b-y}+{x}+{y}','+repage',')',
        '-geometry',f'+{x}+{y}','-define','compose:outside-overlay=false','-compose','Src','-composite',target)

# Use the first edit's forward-swinging full sleeve in phase B; the cleanup
# generation accidentally restored a backwards sleeve. Copy only its cleaned
# obsolete third-hand area from the second edit.
patch(C/'v1-cell-1.png',C/'v2-cell-1.png',(60,74,66,79),C/'story-b-clean.png')
specs=[('story',4,0,'v2-cell-0.png'),('story',5,1,'story-b-clean.png'),
       ('tactical',2,2,'v2-cell-2.png'),('tactical',3,3,'v2-cell-3.png')]
for kind,slot,cell,candidate in specs:
    folder='hunapu-story' if kind=='story'else'hunapu'
    old=P/'deliverables'/folder/f'frame-{slot:02}.png'
    out=O/f'{kind}-{slot:02}.png'
    # Full forearms, wrists, hands and shield, including their swept silhouette.
    # Story needs the sheath/forearm overlap cleared down to y81. No horizontal
    # colour rules are used: these are actual rendered ImageGen pixels.
    box=(38,58,99,81) if kind=='story'else(56,56,92,78)
    patch(old,C/candidate,box,out)
    run(out,'-background','black','-alpha','background',out)

# Side heads, feet, sword and sword-holding arm remain the exact accepted source.
# Fix the exposed central tunic patch between the moving arms across story poses.
# Arms may occlude the torso. Only the truly uncovered chest core is locked.
patch(O/'story-05.png',O/'story-04.png',(69,59,76,65),O/'story-05.png')
patch(O/'story-05.png',O/'story-04.png',(66,74,80,81),O/'story-05.png')
# The previous side mask mistook part of the sword arm for the shield arm.
# Lock the full sword-side arm to phase A, and lock the uncovered tunic too.
patch(O/'tactical-03.png',O/'tactical-02.png',(0,0,70,78),O/'tactical-03.png')
# Tactical left direction is the source's cross-phase horizontal reflection.
for dst,src in [(6,3),(7,2)]:run(O/f'tactical-{src:02}.png','-flop',O/f'tactical-{dst:02}.png')
reports=[]
for kind,slot,cell,candidate in specs:
    folder='hunapu-story'if kind=='story'else'hunapu'
    old=Image.open(P/'deliverables'/folder/f'frame-{slot:02}.png').convert('RGBA')
    im=Image.open(O/f'{kind}-{slot:02}.png').convert('RGBA')
    y=58 if kind=='story'else 54
    head=old.crop((0,0,128,y)).tobytes()==im.crop((0,0,128,y)).tobytes()
    legs=old.crop((0,81 if kind=='story'else 78,128,96)).tobytes()==im.crop((0,81 if kind=='story'else 78,128,96)).tobytes()
    # Both accepted heads were already identical. Sword-side arm is now fixed
    # to phase A; leg animation remains byte-identical to the existing phase.
    assert head and legs
    assert set(im.getchannel('A').getdata())=={0,255}
    assert len({p[:3]for p in im.getdata()if p[3]})==4
    reports.append({'kind':kind,'frame':slot,'head_unchanged':head,'legs_unchanged':legs,'changed_pixels':sum(a!=b for a,b in zip(old.getdata(),im.getdata()))})
(V/'side-motion-qa.json').write_text(json.dumps(reports,indent=2)+'\n')
for background,name in [('#d9d6c9','light'),('#26343b','dark')]:
    run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[O/f'{kind}-{slot:02}.png'for kind,slot in [('story',4),('story',5),('tactical',2),('tactical',3),('tactical',6),('tactical',7)]],'-tile','2x3','-geometry','128x96+8+8','-background',background,V/f'reviews/side-{name}.png')
    run(V/f'reviews/side-{name}.png','-filter','point','-resize','400%',V/f'reviews/side-{name}-4x.png')
print(json.dumps(reports))
