from pathlib import Path
p=Path("scripts/game.gd")
s=p.read_text(encoding="utf-8")
def r(a,b):
    global s
    if a not in s: raise SystemExit("missing:"+a[:80])
    s=s.replace(a,b,1)

start=s.find('func _try_save_at_statue() -> void:\n')
end=s.find('func _save_game(from_statue: bool) -> void:\n',start)
if start!=-1 and end!=-1:
    s=s[:start]+s[end:]

s=s.replace('if player.position.distance_to(p)<130.0: save_hint.text="USE / E : SAVE"; return',
            'if player.position.distance_to(p)<130.0: save_hint.text="SAVE 가능"; return')
s=s.replace('_touch_button(layer,"USE",Vector2(1080,455),"interact",40); ','')
s=s.replace('title.text="ホンブギの冒険  Android Port V7"',
            'title.text="ホンブギの冒険  Android Test V8"')
s=s.replace('if hp_label: hp_label.text="HP %d / %d" % [player_hp,player_max_hp]',
            'if hp_label: hp_label.text="HP %d / %d   ATK %d [TEST]" % [player_hp,player_max_hp,TEST_ATTACK_POWER if TEST_MODE else _attack_damage()]')

r('''    player_hp=int(d.get("hp",100)); player_max_hp=int(d.get("max_hp",100)); credits=int(d.get("credits",100)); alcohol=int(d.get("alcohol",0)); flags=d.get("flags",flags); collected=d.get("collected",{}); checkpoint_stage=String(d.get("checkpoint_stage",d.get("stage","outside"))); checkpoint_pos=Vector2(float(d.get("checkpoint_x",d.get("x",2002))),float(d.get("checkpoint_y",d.get("y",453))))
''',
'''    player_hp=int(d.get("hp",100)); player_max_hp=int(d.get("max_hp",100)); credits=int(d.get("credits",100)); alcohol=int(d.get("alcohol",0)); flags=d.get("flags",flags); collected=d.get("collected",{}); checkpoint_stage=String(d.get("checkpoint_stage",d.get("stage","outside"))); checkpoint_pos=Vector2(float(d.get("checkpoint_x",d.get("x",2002))),float(d.get("checkpoint_y",d.get("y",453))))
    if TEST_MODE:
        player_max_hp=TEST_MAX_HP
        player_hp=TEST_MAX_HP
''')

r('''                if spawn.y<80.0: spawn.y += 90.0
                elif spawn.y>th-80.0: spawn.y -= 90.0
                _load_stage(target_stage,spawn); return
''',
'''                if spawn.y<80.0: spawn.y += 90.0
                elif spawn.y>th-80.0: spawn.y -= 90.0
                spawn.y -= 12.0
                _load_stage(target_stage,spawn); return
''')

p.write_text(s,encoding="utf-8")
