#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, sys, math
from pathlib import Path
from PIL import Image

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
SRC=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT/'source'/'hongbuki'/'Resources'
P=json.load(open(SRC/'data/project.json',encoding='utf8'))

def flat(xs):
    out=[]
    for x in xs:
        if x.get('folder'): out.extend(flat(x.get('children',[])))
        else: out.append(x)
    return out
scenes={s['id']:s for s in flat(P['sceneList'])}
objs={o['id']:o for o in P['objectList'] if not o.get('folder')}
anims={a['id']:a for a in flat(P['animationList'])}
imgs={i['id']:i for i in P['imageList'] if not i.get('folder')}
tilesets={t['id']:t for t in P['tilesetList'] if not t.get('folder')}

def load_img(iid):
    e=imgs[iid]
    return Image.open(SRC/e['filename']).convert('RGBA')

def get_motion(anim_id,mid):
    a=anims[int(anim_id)]
    m=next((x for x in a['motionList'] if int(x['id'])==int(mid)),None)
    if not m: raise KeyError(f'motion {mid} missing in animation {anim_id}')
    d=next((x for x in m.get('directionList',[]) if x.get('frameList') and int(x.get('directionBit',0))==64),None)
    if d is None: d=next((x for x in m.get('directionList',[]) if x.get('frameList')),None)
    if not d: raise KeyError(f'no frame direction: anim={anim_id} motion={mid}')
    ri=next(r for r in a['resourceInfoList'] if int(r['id'])==int(d['resourceInfoId']))
    src=load_img(int(ri['imageId']))
    tw=src.width//int(ri['hdivCount']); th=src.height//int(ri['vdivCount'])
    return m,d,ri,src,tw,th

def save_motion(anim_id,mid,frames_spec,pad_512=False):
    m,d,ri,src,tw,th=get_motion(anim_id,mid)
    if len(frames_spec)!=len(d['frameList']):
        if len(frames_spec)>len(d['frameList']):
            raise ValueError(f'frame count mismatch anim={anim_id} motion={mid}: manifest {len(frames_spec)} source {len(d["frameList"])}')
    for i,outfr in enumerate(frames_spec):
        fr=d['frameList'][i]
        x=int(fr['imageTileX'])*tw; y=int(fr['imageTileY'])*th
        crop=src.crop((x,y,x+tw,y+th))
        dest=ROOT/outfr['file']; dest.parent.mkdir(parents=True,exist_ok=True)
        if pad_512:
            canvas=Image.new('RGBA',(512,512),(0,0,0,0))
            if fr.get('flipX'): crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if fr.get('flipY'): crop=crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            px=256 + math.floor(float(fr.get('offsetX',0))) - math.floor(float(fr.get('centerX',0)))
            py=400 + math.floor(float(fr.get('offsetY',0))) - math.floor(float(fr.get('centerY',0)))
            canvas.alpha_composite(crop,(px,py))
            canvas.save(dest,optimize=True)
        else:
            crop.save(dest,optimize=True)

def render_scene(s):
    W=int(s['horzScreenCount'])*int(P['screenWidth']); H=int(s['vertScreenCount'])*int(P['screenHeight'])
    if s.get('setBgImageFlag') and int(s.get('bgImageId',-1))>=0:
        bg=load_img(int(s['bgImageId']))
        screen=bg.resize((int(P['screenWidth']),int(P['screenHeight'])),Image.Resampling.NEAREST)
        canvas=Image.new('RGBA',(W,H),(int(s.get('bgColorR',0)),int(s.get('bgColorG',0)),int(s.get('bgColorB',0)),255))
        for y in range(0,H,int(P['screenHeight'])):
            for x in range(0,W,int(P['screenWidth'])):
                canvas.alpha_composite(screen,(x,y))
    else:
        canvas=Image.new('RGBA',(W,H),(int(s.get('bgColorR',0)),int(s.get('bgColorG',0)),int(s.get('bgColorB',0)),255))
    cache={}
    for li in range(13,0,-1):
        lay=s.get(f'layer{li}',{})
        tilemap=lay.get('tile',{}) if isinstance(lay,dict) else {}
        for key,tile in tilemap.items():
            dx,dy=map(int,key.split(',')); tid=int(tile['tilesetId']); sx=int(tile['x']); sy=int(tile['y'])
            tse=tilesets[tid]; iid=int(tse['imageId'])
            if iid not in cache: cache[iid]=load_img(iid)
            src=cache[iid]
            crop=src.crop((sx*32,sy*32,sx*32+32,sy*32+32))
            canvas.alpha_composite(crop,(dx*32,dy*32))
    return canvas

(ROOT/'data').mkdir(exist_ok=True)
shutil.copy2(SRC/'data/project.json', ROOT/'data/original_project.json')

manifest=json.load(open(ROOT/'data/stage_manifest_v5.json',encoding='utf8'))
for key,e in manifest.items():
    sid=int(e['scene_id']); dest=ROOT/e['image']; dest.parent.mkdir(parents=True,exist_ok=True)
    render_scene(scenes[sid]).save(dest,optimize=True)

for fn in ['player_v3_animations.json','enemy_v3_animations.json','item_v3_animations.json']:
    d=json.load(open(ROOT/'data'/fn,encoding='utf8'))
    for name,v in d.items():
        save_motion(int(v['source_animation_id']),int(v['source_motion_id']),v['frames'],pad_512=True)

boss_info={
    'boss_crab_animations.json':74,
    'boss_harvester_animations.json':101,
    'boss_chamber_animations.json':111,
    'boss_black_animations.json':158,
}
crab_legacy={'crab_idle':1,'crab_hurt':2,'crab_recover':4,'crab_jump':6,'crab_attack':7,'crab_attack2':8}
for fn,oid in boss_info.items():
    d=json.load(open(ROOT/'data'/fn,encoding='utf8')); aid=int(objs[oid]['animationId'])
    for name,v in d.items():
        mid=v.get('source_motion_id')
        if mid is None and fn=='boss_crab_animations.json': mid=crab_legacy.get(name)
        if mid is None: raise KeyError(f'{fn}:{name} has no source motion')
        save_motion(aid,int(mid),v['frames'])

env=json.load(open(ROOT/'data/enemy_visuals_v4.json',encoding='utf8'))
for kind,v in env.items():
    oid=int(v['object_id']); o=objs[oid]; init=int(o['initialActionId'])
    act=next(a for a in o['actionList'] if int(a['id'])==init)
    mid=int(act['animMotionId']); m,d,ri,src,tw,th=get_motion(int(o['animationId']),mid); fr=d['frameList'][0]
    x=int(fr['imageTileX'])*tw; y=int(fr['imageTileY'])*th; dest=ROOT/v['file']; dest.parent.mkdir(parents=True,exist_ok=True)
    src.crop((x,y,x+tw,y+th)).save(dest,optimize=True)

pick_motion={'max_hp':21,'map':24,'alcohol':26,'turtle':27,'body':28,'feet':37,'head':38,'candle':41,'hands':42,'ufo':44,'turtle_jump':71,'ps5':76}
iv=json.load(open(ROOT/'data/item_visuals_v4.json',encoding='utf8')); aid=int(objs[49]['animationId'])
for name,v in iv.items():
    mid=pick_motion[name]; m,d,ri,src,tw,th=get_motion(aid,mid); fr=d['frameList'][0]
    x=int(fr['imageTileX'])*tw; y=int(fr['imageTileY'])*th; dest=ROOT/v['file']; dest.parent.mkdir(parents=True,exist_ok=True)
    src.crop((x,y,x+tw,y+th)).save(dest,optimize=True)

required_audio={
 'audio_v4':{'se069.ogg','bgm013.ogg','bgm016.ogg','bgm010.ogg','bgm002.ogg','se039.ogg'},
 'audio_v5':{'bgm009.ogg','bgm006.ogg','bgm015.ogg','bgm003.ogg','bgm005.ogg','bgm013.ogg','bgm016.ogg','bgm010.ogg','bgm002.ogg','bgm011.ogg','bgm001.ogg','bgm012.ogg'},
 'audio_v6':{'se082.ogg','se069.ogg','se015.ogg','se054.ogg','se051.ogg','se058.ogg','se067.ogg','se068.ogg'},
}
for folder,names in required_audio.items():
    target=ROOT/'assets'/folder; target.mkdir(parents=True,exist_ok=True)
    for name in names:
        src=SRC/'audio'/name
        if not src.exists(): raise FileNotFoundError(src)
        shutil.copy2(src,target/name)

aliases={'box_open.ogg':'se031.ogg','cave.ogg':'bgm013.ogg','fire.ogg':'se025.ogg','hit.ogg':'se015.ogg','item_get.ogg':'se039.ogg','jump.ogg':'se022.ogg','outside.ogg':'bgm016.ogg','shot.ogg':'se020.ogg','swing.ogg':'se009.ogg'}
for dst,srcname in aliases.items():
    out=ROOT/'assets/audio'/dst; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(SRC/'audio'/srcname,out)

print('V7 source-backed assets rebuilt')
