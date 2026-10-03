from pathlib import Path
from PIL import Image
from collections import deque
import json, shutil

ROOT = Path('.')
SRC = ROOT / 'assets/player_v9'
OUT = ROOT / 'assets/player_v10'
TARGET_H = 108
FOOT_Y = 400
CENTER_X = 256

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

def largest_component(im: Image.Image) -> Image.Image:
    im = im.convert('RGBA')
    alpha = im.getchannel('A')
    w, h = im.size
    data = list(alpha.getdata())
    seen = bytearray(w * h)
    largest = []
    for idx, a in enumerate(data):
        if a <= 15 or seen[idx]:
            continue
        q = deque([idx])
        seen[idx] = 1
        comp = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            x = cur % w
            y = cur // w
            for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    continue
                ni = ny*w + nx
                if not seen[ni] and data[ni] > 15:
                    seen[ni] = 1
                    q.append(ni)
        if len(comp) > len(largest):
            largest = comp
    keep = bytearray(w*h)
    for i in largest:
        keep[i] = data[i]
    new_alpha = Image.frombytes('L', (w,h), bytes(keep))
    out = im.copy()
    out.putalpha(new_alpha)
    return out

def normalize(src: Path) -> Image.Image:
    im = largest_component(Image.open(src))
    bbox = im.getchannel('A').getbbox()
    if not bbox:
        raise RuntimeError(f'No sprite content: {src}')
    spr = im.crop(bbox)
    w, h = spr.size
    nw = max(1, round(w * TARGET_H / h))
    spr = spr.resize((nw, TARGET_H), Image.Resampling.LANCZOS)
    a = spr.getchannel('A')
    pix = a.load()
    xs = []
    ys = []
    for y in range(spr.height):
        for x in range(spr.width):
            if pix[x,y] > 24:
                xs.append(x); ys.append(y)
    y0, y1 = min(ys), max(ys)
    limit = y0 + 0.60 * (y1-y0+1)
    ux = sorted(x for x,y in zip(xs,ys) if y <= limit)
    anchor_x = ux[len(ux)//2] if ux else sorted(xs)[len(xs)//2]
    bottom = a.getbbox()[3] - 1
    px = round(CENTER_X - anchor_x)
    py = round(FOOT_Y - bottom)
    canvas = Image.new('RGBA', (512,512), (0,0,0,0))
    canvas.alpha_composite(spr, (px,py))
    return canvas

def save_anim(name, sources):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    files=[]
    for i, src in enumerate(sources):
        dst = d / f'{i:02d}.png'
        normalize(src).save(dst, optimize=True)
        files.append(str(dst.as_posix()))
    return files

idle = save_anim('idle', sorted((SRC/'idle').glob('*.webp')))
walk = save_anim('walk', sorted((SRC/'walk').glob('*.webp')))
jump = save_anim('jump', sorted((SRC/'jump').glob('*.webp')))
damage = save_anim('damage', sorted((SRC/'damage').glob('*.webp')))
# Simple character-only attack poses; no skill/strong/effect animation is used.
attack = save_anim('attack1', [SRC/'attack1/00.webp', SRC/'attack5/00.webp', SRC/'attack3/00.webp', SRC/'idle/00.webp'])
dash = save_anim('dash', [SRC/'walk/02.webp', SRC/'walk/03.webp', SRC/'walk/04.webp'])
dodge = save_anim('dodge', [SRC/'jump/00.webp', SRC/'jump/01.webp', SRC/'jump/02.webp'])
save = save_anim('save_pose', [SRC/'idle/00.webp'])

def anim(files, dur, loop=False):
    return {'loop':loop,'frames':[{'file':f,'duration300':dur} for f in files]}

root = {
    'idle': anim(idle,30,True),
    'walk': anim(walk,18,True),
    'jump': anim(jump,28,False),
    'damage': anim(damage,30,False),
    'attack1': anim(attack,22,False),
    'dash': anim(dash,18,True),
    'dodge': anim(dodge,22,False),
    'save_pose': anim(save,30,False),
}
(ROOT/'data/player_v10_animations.json').write_text(json.dumps(root,ensure_ascii=False,indent=2),encoding='utf-8')
print('V10 simple sprites created:', sum(len(x['frames']) for x in root.values()))
