from pathlib import Path
from PIL import Image
from collections import deque
import json, shutil

ROOT = Path('.')
SRC = ROOT / 'assets/player_v9'
OUT = ROOT / 'assets/player_v11'
DATA = ROOT / 'data/player_v11_animations.json'
SCALE = 0.46
CENTER_X = 256
FOOT_Y = 400

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
    for idx, value in enumerate(data):
        if value <= 16 or seen[idx]:
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
                if 0 <= nx < w and 0 <= ny < h:
                    ni = ny*w + nx
                    if not seen[ni] and data[ni] > 16:
                        seen[ni] = 1
                        q.append(ni)
        if len(comp) > len(largest):
            largest = comp
    keep = bytearray(w*h)
    for i in largest:
        keep[i] = data[i]
    out = im.copy()
    out.putalpha(Image.frombytes('L', (w,h), bytes(keep)))
    return out

def snap_bottom(canvas: Image.Image, foot: int = FOOT_Y) -> Image.Image:
    bbox = canvas.getchannel('A').getbbox()
    if not bbox:
        return canvas
    shift = foot - (bbox[3] - 1)
    if shift == 0:
        return canvas
    out = Image.new('RGBA', (512,512), (0,0,0,0))
    out.alpha_composite(canvas, (0, shift))
    return out

def place(src: Path, pivot_y: float, dx: float = 0, scale: float = SCALE) -> Image.Image:
    im = largest_component(Image.open(src))
    im = im.resize((round(512*scale), round(512*scale)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (512,512), (0,0,0,0))
    x = round(CENTER_X + dx - 256*scale)
    y = round(FOOT_Y - pivot_y*scale)
    canvas.alpha_composite(im, (x,y))
    return snap_bottom(canvas)

def save_anim(name: str, images):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    files = []
    for i, im in enumerate(images):
        p = d / f'{i:02d}.png'
        im.save(p, optimize=True)
        files.append(str(p.relative_to(ROOT)).replace('\\','/'))
    return files

# Stable single-frame idle: generated idle variants drift horizontally, so do not cycle them.
idle_img = place(SRC/'idle/00.webp', 417)
idle = save_anim('idle', [idle_img])

# Walk: preserve the original shared 512 coordinate system instead of recentering each frame independently.
walk = save_anim('walk', [place(p, 420) for p in sorted((SRC/'walk').glob('*.webp'))])

# Jump: one clean pose. largest_component removes detached image fragments near the canvas edge.
jump_img = place(SRC/'jump/00.webp', 418)
jump = save_anim('jump', [jump_img])

# Damage: compact clean pose with no skill/effect animation.
damage = save_anim('damage', [place(SRC/'damage/01.webp', 420)])

# Dash: three forward-leaning walk poses, no added visual effects.
dash = save_anim('dash', [
    place(SRC/'walk/03.webp', 420),
    place(SRC/'walk/04.webp', 420, dx=4),
    place(SRC/'walk/05.webp', 420),
])

# Dodge/roll: rotate one clean character cutout. Each frame is pinned to the same ground baseline.
base = largest_component(Image.open(SRC/'jump/00.webp'))
bbox = base.getchannel('A').getbbox()
base = base.crop(bbox)
roll_h = 96
roll_w = max(1, round(base.width * roll_h / base.height))
base = base.resize((roll_w, roll_h), Image.Resampling.LANCZOS)
roll_frames = []
for angle in (0, -60, -120, -180, -240, -300):
    r = base.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    canvas = Image.new('RGBA', (512,512), (0,0,0,0))
    canvas.alpha_composite(r, (CENTER_X-r.width//2, FOOT_Y-r.height+1))
    roll_frames.append(canvas)
dodge = save_anim('dodge', roll_frames)

# Attack: simple character-only lunge/crouch/return sequence. No slash arc, particles or skill frames.
attack = save_anim('attack1', [
    place(SRC/'idle/00.webp', 417),
    place(SRC/'walk/05.webp', 420, dx=4),
    place(SRC/'attack3/00.webp', 427, dx=8),
    place(SRC/'walk/00.webp', 420, dx=4),
    place(SRC/'idle/00.webp', 417),
])

save_pose = save_anim('save_pose', [idle_img.copy()])

def anim(files, duration300, loop=False):
    return {'loop': loop, 'frames': [{'file': f, 'duration300': duration300} for f in files]}

root = {
    'idle': anim(idle, 90, True),
    'walk': anim(walk, 18, True),
    'jump': anim(jump, 300, False),
    'damage': anim(damage, 60, False),
    'attack1': anim(attack, 16, False),
    'dash': anim(dash, 18, True),
    'dodge': anim(dodge, 16, False),
    'save_pose': anim(save_pose, 60, False),
}
DATA.write_text(json.dumps(root, ensure_ascii=False, indent=2), encoding='utf-8')
print('V11 manual-pivot frames created:', sum(len(v['frames']) for v in root.values()))
