from pathlib import Path
from PIL import Image
import numpy as np
import json, shutil

SRC = Path('assets/player_v10')
OUT = Path('assets/player_v11')
if OUT.exists():
    shutil.rmtree(OUT)
for sub in ['idle','walk','jump','dodge','attack1','dash','damage','save_pose']:
    (OUT/sub).mkdir(parents=True, exist_ok=True)

def alpha_bbox(im):
    return im.getchannel('A').getbbox()

def head_center_x(im):
    a = np.array(im.getchannel('A'))
    b = im.getchannel('A').getbbox()
    if not b:
        return 256.0
    x0,y0,x1,y1 = b
    h = y1-y0
    yend = min(y1, y0 + max(20, int(h*0.62)))
    mask = a[y0:yend,:] > 20
    xs = np.where(mask)[1]
    return float(np.median(xs)) if len(xs) else (x0+x1)/2.0

def normalize_existing(path, target_bottom=400, target_head_x=256, x_extra=0):
    im = Image.open(path).convert('RGBA')
    b = alpha_bbox(im)
    if not b:
        return im
    hc = head_center_x(im)
    dx = int(round(target_head_x - hc + x_extra))
    dy = int(round(target_bottom - b[3]))
    canvas = Image.new('RGBA',(512,512),(0,0,0,0))
    canvas.alpha_composite(im,(dx,dy))
    return canvas

# IDLE: one stable full frame only. This intentionally removes the wobbling V10 idle cycle.
idle = normalize_existing(SRC/'idle/00.png')
idle.save(OUT/'idle/00.png')

# WALK: keep the six complete walking frames, but normalize body center and foot line.
for i,p in enumerate(sorted((SRC/'walk').glob('*.png'))):
    normalize_existing(p).save(OUT/f'walk/{i:02d}.png')

# JUMP: V10 jump/02 is clipped in the source. Use only the complete airborne frame.
normalize_existing(SRC/'jump/01.png').save(OUT/'jump/00.png')

# DAMAGE: two complete frames.
for i,p in enumerate(sorted((SRC/'damage').glob('*.png'))[:2]):
    normalize_existing(p).save(OUT/f'damage/{i:02d}.png')

# DASH: three complete lean/run frames.
for i,p in enumerate(sorted((SRC/'dash').glob('*.png'))):
    normalize_existing(p).save(OUT/f'dash/{i:02d}.png')

# ATTACK: a deliberately simple, consistent four-frame lunge.
# No V9/V10 special effects, no unrelated attack poses.
attack_idle = normalize_existing(SRC/'idle/00.png')
lunge = normalize_existing(SRC/'attack1/00.png')
lunge_forward = normalize_existing(SRC/'attack1/00.png', x_extra=10)
for i,im in enumerate([attack_idle,lunge,lunge_forward,attack_idle]):
    im.save(OUT/f'attack1/{i:02d}.png')

# DODGE/ROLL: create a real visible roll from ONE complete compact pose.
# Rotating one consistent pose avoids the old jump-frame substitution.
roll_src = normalize_existing(SRC/'attack1/00.png')
b = alpha_bbox(roll_src)
crop = roll_src.crop(b)
for i,ang in enumerate([0,-60,-120,-180,-240,-300]):
    r = crop.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)
    rb = r.getchannel('A').getbbox()
    if rb:
        r = r.crop(rb)
    max_side = max(r.size)
    if max_side > 135:
        scale = 135.0/max_side
        r = r.resize((max(1,int(r.width*scale)), max(1,int(r.height*scale))), Image.Resampling.LANCZOS)
    rb = r.getchannel('A').getbbox()
    if rb:
        r = r.crop(rb)
    canvas = Image.new('RGBA',(512,512),(0,0,0,0))
    x = 256-r.width//2
    y = 400-r.height
    canvas.alpha_composite(r,(x,y))
    canvas.save(OUT/f'dodge/{i:02d}.png')

idle.save(OUT/'save_pose/00.png')

anims = {
    'idle': {'loop': True, 'frames':[{'file':'assets/player_v11/idle/00.png','duration300':300}]},
    'walk': {'loop': True, 'frames':[{'file':f'assets/player_v11/walk/{i:02d}.png','duration300':18} for i in range(6)]},
    'jump': {'loop': True, 'frames':[{'file':'assets/player_v11/jump/00.png','duration300':300}]},
    'damage': {'loop': False, 'frames':[{'file':f'assets/player_v11/damage/{i:02d}.png','duration300':30} for i in range(2)]},
    'attack1': {'loop': False, 'frames':[{'file':f'assets/player_v11/attack1/{i:02d}.png','duration300':22} for i in range(4)]},
    'dash': {'loop': True, 'frames':[{'file':f'assets/player_v11/dash/{i:02d}.png','duration300':18} for i in range(3)]},
    'dodge': {'loop': False, 'frames':[{'file':f'assets/player_v11/dodge/{i:02d}.png','duration300':16} for i in range(6)]},
    'save_pose': {'loop': False, 'frames':[{'file':'assets/player_v11/save_pose/00.png','duration300':30}]},
}
Path('data/player_v11_animations.json').write_text(json.dumps(anims,ensure_ascii=False,indent=2),encoding='utf-8')

p = Path('scripts/game.gd')
s = p.read_text(encoding='utf-8')
s = s.replace('res://data/player_v10_animations.json','res://data/player_v11_animations.json')
s = s.replace('Android Test V10','Android Test V11')
start = s.index('const PLAYER_FRAME_BOTTOMS := {')
end = s.index('\n}\n',start)+3
newdict = '''const PLAYER_FRAME_BOTTOMS := {
    "idle": [400],
    "walk": [400,400,400,400,400,400],
    "jump": [400],
    "attack1": [400,400,400,400],
    "dash": [400,400,400],
    "dodge": [400,400,400,400,400,400],
    "damage": [400,400],
    "save_pose": [400]
}
'''
s = s[:start] + newdict + s[end:]
p.write_text(s,encoding='utf-8')

# Validate every produced frame: 512 canvas, non-empty, not touching canvas edges.
files = sorted(OUT.glob('*/*.png'))
for fp in files:
    im = Image.open(fp).convert('RGBA')
    if im.size != (512,512):
        raise SystemExit(f'bad canvas: {fp} {im.size}')
    b = im.getchannel('A').getbbox()
    if not b:
        raise SystemExit(f'empty frame: {fp}')
    if b[0] <= 8 or b[2] >= 504 or b[1] <= 8 or b[3] >= 504:
        raise SystemExit(f'frame touches canvas edge: {fp} {b}')
print('V11 frames created:', len(files))
print('V11 game patch applied')
