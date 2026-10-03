from pathlib import Path
import re

p=Path('scripts/game.gd')
s=p.read_text(encoding='utf-8')

# Fixed V8-style 512x512 player frames. Every V10 frame's opaque bottom is y=400.
start=s.index('const PLAYER_FRAME_BOTTOMS := {')
end=s.index('\n}\n',start)+3
s=s[:start]+'''const PLAYER_FRAME_BOTTOMS := {
    "idle": [400,400,400,400],
    "walk": [400,400,400,400,400,400],
    "jump": [400,400,400],
    "attack1": [400,400,400,400],
    "dash": [400,400,400],
    "dodge": [400,400,400],
    "damage": [400,400],
    "save_pose": [400]
}
'''+s[end:]

s=s.replace('player_frames = _load_frames("res://data/player_v3_animations.json")','player_frames = _load_frames("res://data/player_v10_animations.json")')
s=s.replace('    _bind_key("strong_attack", KEY_K)\n','')
s=s.replace('    elif state.begins_with("attack") or state.begins_with("strong") or state == "damage": player.velocity.x = move_toward(player.velocity.x,0.0,1300.0*delta)\n','    elif state.begins_with("attack") or state == "damage": player.velocity.x = move_toward(player.velocity.x,0.0,1300.0*delta)\n')
s=s.replace('''        if Input.is_action_just_pressed("attack"): _begin_attack(false)
        elif Input.is_action_just_pressed("strong_attack"): _begin_attack(true)
        elif Input.is_action_just_pressed("dash"): state = "dash"; state_timer = 0.22; player_sprite.play("dash")
''','''        if Input.is_action_just_pressed("attack"): _begin_attack()
        elif Input.is_action_just_pressed("dash"): state = "dash"; state_timer = 0.22; player_sprite.play("dash")
''')

s,n=re.subn(r'func _begin_attack\(strong: bool\) -> void:\n.*?(?=\nfunc _attack_damage\(\) -> int:)', '''func _begin_attack() -> void:
    attack_hit_ids.clear()
    (attack_area.get_child(0) as CollisionShape2D).set_deferred("disabled",false)
    state = "attack1"
    state_timer = 0.31
    combo_step = 0
    combo_window = 0.0
    player_sprite.play("attack1")
    _play_sfx("res://assets/audio/swing.ogg")
''', s, count=1, flags=re.S)
if n!=1: raise SystemExit('Could not replace _begin_attack')

s,n=re.subn(r'func _attack_damage\(\) -> int:\n.*?(?=\nfunc _update_attack_area_transform\(\) -> void:)', '''func _attack_damage() -> int:
    if TEST_MODE:
        return TEST_ATTACK_POWER
    var base := 10
    if bool(flags.get("hands",false)): base += 20
    return base
''', s, count=1, flags=re.S)
if n!=1: raise SystemExit('Could not replace _attack_damage')

s,n=re.subn(r'func _update_attack_area_transform\(\) -> void:\n.*?(?=\nfunc _process_attack_hits\(\) -> void:)', '''func _update_attack_area_transform() -> void:
    if not attack_area:
        return
    var shape_node := attack_area.get_child(0) as CollisionShape2D
    var rect := shape_node.shape as RectangleShape2D
    rect.size = Vector2(150,100)
    attack_area.position = Vector2(78.0*facing,-55)
''', s, count=1, flags=re.S)
if n!=1: raise SystemExit('Could not replace _update_attack_area_transform')

s=s.replace('if not (state.begins_with("attack") or state.begins_with("strong")): return','if not state.begins_with("attack"): return')
s=s.replace('title.text="ホンブギの冒険  Android Test V8"','title.text="ホンブギの冒険  Android Test V10"')
s=s.replace('    _touch_button(layer,"JUMP",Vector2(1010,650),"jump",52); _touch_button(layer,"ATK",Vector2(1150,690),"attack",52); _touch_button(layer,"STR",Vector2(1160,565),"strong_attack",48); _touch_button(layer,"DODGE",Vector2(890,700),"dodge",48); _touch_button(layer,"DASH",Vector2(905,590),"dash",45)\n','    _touch_button(layer,"JUMP",Vector2(1010,650),"jump",52); _touch_button(layer,"ATK",Vector2(1150,690),"attack",52); _touch_button(layer,"DODGE",Vector2(890,700),"dodge",48); _touch_button(layer,"DASH",Vector2(905,590),"dash",45)\n')

# Hard fail if any skill/strong input survived in runtime code.
if 'strong_attack' in s or '"STR"' in s:
    raise SystemExit('STR/strong_attack survived V10 patch')

p.write_text(s,encoding='utf-8')
print('V10 game patch applied')
