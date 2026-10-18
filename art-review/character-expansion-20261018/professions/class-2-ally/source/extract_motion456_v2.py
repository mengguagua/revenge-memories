"""Separate three generated sprites; preserve every nonzero-alpha source pixel."""
from pathlib import Path
from PIL import Image
from collections import deque
import json

P = Path(__file__).resolve().parent
im = Image.open(P / 'motion-4-5-6-v2-generated.png').convert('RGBA')
w, h = im.size
rgba = list(im.getdata())
remaining = {i for i, p in enumerate(rgba) if p[3] >= 32}
groups = []
while remaining:
    first = remaining.pop()
    stack, group = [first], [first]
    while stack:
        i = stack.pop()
        x, y = i % w, i // w
        neighbours = ([i - 1] if x else []) + ([i + 1] if x + 1 < w else []) + ([i - w] if y else []) + ([i + w] if y + 1 < h else [])
        for n in neighbours:
            if n in remaining:
                remaining.remove(n)
                stack.append(n)
                group.append(n)
    groups.append(group)
groups = sorted(sorted(groups, key=len, reverse=True)[:3], key=lambda g: sum(i % w for i in g) / len(g))
labels = bytearray(w * h)
queue = deque()
for label, group in enumerate(groups, 1):
    for i in group:
        labels[i] = label
        queue.append(i)
# Threshold only identifies each object. Nearest-component assignment retains
# the original alpha values, including faint antialiasing and detached pixels.
while queue:
    i = queue.popleft()
    x, y = i % w, i // w
    neighbours = ([i - 1] if x else []) + ([i + 1] if x + 1 < w else []) + ([i - w] if y else []) + ([i + w] if y + 1 < h else [])
    for n in neighbours:
        if not labels[n]:
            labels[n] = labels[i]
            queue.append(n)
parts, records = [], []
for label, frame in enumerate([4, 5, 6], 1):
    part = Image.new('RGBA', im.size)
    part.putdata([p if labels[i] == label else (0, 0, 0, 0) for i, p in enumerate(rgba)])
    parts.append(part)
    box = part.getchannel('A').getbbox()
    part.crop(box).save(P / f'motion-{frame}-v2-extracted.png')
    records.append({'frame': frame, 'crop': box, 'opaque_component_pixels': len(groups[label - 1])})
reconstructed = Image.new('RGBA', im.size)
for part in parts:
    reconstructed.alpha_composite(part)
assert all(a == b for a, b in zip(rgba, reconstructed.getdata()) if a[3])
(P / 'motion456-v2-extraction.json').write_text(json.dumps({'method': 'Opaque connected components and nearest-component technical extraction; no body drawing or alpha removal.', 'nonzero_rgba_reconstruction_exact': True, 'frames': records}, indent=2) + '\n')
print(records)
