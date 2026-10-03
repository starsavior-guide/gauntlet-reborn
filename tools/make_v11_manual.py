from pathlib import Path
from PIL import Image
import json, shutil

ROOT = Path('.')
SRC = ROOT / 'assets/player_v10'
OUT = ROOT / 'assets/player_v11'
DATA = ROOT / 'data/player_v11_animations.json'
CANVAS = (512, 512)
BODY_X = 256
FOOT_Y = 400

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

def bbox(im: Image.Image):
    return im.getchannel('A').getbbox()

def body_x(im: Image.Image) -> int:
    a = im.getchannel('A')
    px = a.load()
    xs = []
    for y in range(292, 366):
        for x in range(80, 440):
            if px[x, y] > 80:
                xs.append(x)
    if not xs:
        b = bbox(im)
        return (b[0] + b[2]) // 2
    xs.sort()
    return xs[len(xs)//2]

def normalize(src: Path, scale: float = 1.0, angle: float = 0.0, dx: int = 0, dy: int = 0) -> Image.Image:
    im = Image.open(src).convert('RGBA')
    b = bbox(im)
    if not b:
        raise SystemExit(f'Empty source frame: {src}')
    bx = body_x(im)
    bottom = b[3] - 1
    tmp = Image.new('RGBA', CANVAS, (0,0,0,0))
    tmp.alpha_composite(im, (BODY_X - bx, FOOT_Y - bottom))
    if abs(scale - 1.0) > 1e-4:
        w = max(1, round(512 * scale)); h = max(1, round(512 * scale))
        rs = tmp.resize((w, h), Image.Resampling.LANCZOS)
        out = Image.new('RGBA', CANVAS, (0,0,0,0))
        ox = round(BODY_X - BODY_X * scale)
        oy = round(FOOT_Y - FOOT_Y * scale)
        out.alpha_composite(rs, (ox, oy)); tmp = out
    if abs(angle) > 1e-4:
        tmp = tmp.rotate(angle, resample=Image.Resampling.BICUBIC, center=(BODY_X, FOOT_Y - 54), expand=False)
    if dx or dy:
        out = Image.new('RGBA', CANVAS, (0,0,0,0))
        out.alpha_composite(tmp, (dx, dy)); tmp = out
    b = bbox(tmp)
    if b:
        shift_y = FOOT_Y - (b[3] - 1)
        if shift_y:
            out = Image.new('RGBA', CANVAS, (0,0,0,0))
            out.alpha_composite(tmp, (0, shift_y)); tmp = out
    return tmp

def save_motion(name: str, images):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    files = []
    for i, im in enumerate(images):
        p = d / f'{i:02d}.png'
        im.save(p, optimize=True)
        files.append(str(p).replace('\\', '/'))
    return files

base = SRC / 'idle/00.png'
idle = save_motion('idle', [normalize(base)])
walk = save_motion('walk', [normalize(base, angle=a, dy=dy) for a,dy in [(-1,0),(0,-2),(1,-3),(0,-2),(-1,0),(0,1)]])
jump = save_motion('jump', [normalize(base, angle=-3, dy=-2)])
dash = save_motion('dash', [normalize(base, angle=-6, dx=2), normalize(base, angle=-9, dx=5), normalize(base, angle=-6, dx=2)])
dodge = save_motion('dodge', [normalize(base, scale=0.92, angle=a, dy=5) for a in (0,60,120,180,240,300)])
damage = save_motion('damage', [normalize(SRC/'damage/00.png'), normalize(SRC/'damage/01.png')])
# Use only complete effect-free V10 poses; attack1/01 is intentionally skipped.
attack = save_motion('attack1', [normalize(base), normalize(SRC/'attack1/03.png'), normalize(SRC/'attack1/02.png'), normalize(SRC/'attack1/00.png'), normalize(base)])
save_pose = save_motion('save_pose', [normalize(base)])

settings = {
    'idle': (True, 45), 'walk': (True, 18), 'jump': (False, 60),
    'dash': (True, 18), 'dodge': (False, 16), 'damage': (False, 30),
    'attack1': (False, 18), 'save_pose': (False, 30),
}
files_by_motion = {'idle':idle,'walk':walk,'jump':jump,'dash':dash,'dodge':dodge,'damage':damage,'attack1':attack,'save_pose':save_pose}
root = {}
for name, files in files_by_motion.items():
    loop, dur = settings[name]
    root[name] = {'loop': loop, 'frames': [{'file': f, 'duration300': dur} for f in files]}
DATA.write_text(json.dumps(root, ensure_ascii=False, indent=2), encoding='utf-8')

for p in sorted(OUT.glob('*/*.png')):
    im = Image.open(p).convert('RGBA')
    b = bbox(im)
    if not b:
        raise SystemExit(f'Empty V11 frame {p}')
    if b[0] <= 2 or b[1] <= 2 or b[2] >= 510 or b[3] >= 510:
        raise SystemExit(f'V11 frame touches edge {p}: {b}')
    if b[3] - 1 != FOOT_Y:
        raise SystemExit(f'V11 baseline mismatch {p}: {b}')
print('V11 stable frames created:', sum(len(v) for v in files_by_motion.values()))
