from pathlib import Path
p=Path('scripts/game.gd')
s=p.read_text(encoding='utf-8')

def rep(a,b,n=1):
    global s
    if a not in s:
        raise SystemExit('Missing source block:\n'+a[:300])
    s=s.replace(a,b,n)

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

rep('player_frames = _load_frames("res://data/player_v3_animations.json")','player_frames = _load_frames("res://data/player_v10_animations.json")')
s=s.replace('    _bind_key("strong_attack", KEY_K)\n','')
rep('    elif state.begins_with("attack") or state.begins_with("strong") or state == "damage": player.velocity.x = move_toward(player.velocity.x,0.0,1300.0*delta)\n','    elif state.begins_with("attack") or state == "damage": player.velocity.x = move_toward(player.velocity.x,0.0,1300.0*delta)\n')
rep('''        if Input.is_action_just_pressed("attack"): _begin_attack(false)
        elif Input.is_action_just_pressed("strong_attack"): _begin_attack(true)
        elif Input.is_action_just_pressed("dash"): state = "dash"; state_timer = 0.22; player_sprite.play("dash")
''','''        if Input.is_action_just_pressed("attack"): _begin_attack()
        elif Input.is_action_just_pressed("dash"): state = "dash"; state_timer = 0.22; player_sprite.play("dash")
''')
rep('''func _begin_attack(strong: bool) -> void:
    attack_hit_ids.clear(); (attack_area.get_child(0) as CollisionShape2D).set_deferred("disabled",false)
    if strong:
        state = "strong1"; state_timer = 0.42; combo_step = 0; player_sprite.play("strong1")
    else:
        combo_step = combo_step+1 if combo_window>0.0 and combo_step<3 else 1
        combo_window = 0.48; state = "attack%d" % combo_step; state_timer = 0.30; player_sprite.play("attack%d" % combo_step)
    _play_sfx("res://assets/audio/swing.ogg")
''','''func _begin_attack() -> void:
    attack_hit_ids.clear()
    (attack_area.get_child(0) as CollisionShape2D).set_deferred("disabled",false)
    state = "attack1"
    state_timer = 0.31
    combo_step = 0
    combo_window = 0.0
    player_sprite.play("attack1")
    _play_sfx("res://assets/audio/swing.ogg")
''')
rep('''func _attack_damage() -> int:
    if TEST_MODE:
        return TEST_ATTACK_POWER
    var base := 20 if state.begins_with("strong") else 10
    if bool(flags.get("hands",false)): base += 20
    return base
''','''func _attack_damage() -> int:
    if TEST_MODE:
        return TEST_ATTACK_POWER
    var base := 10
    if bool(flags.get("hands",false)): base += 20
    return base
''')
rep('''func _update_attack_area_transform() -> void:
    if not attack_area:
        return
    var shape_node := attack_area.get_child(0) as CollisionShape2D
    var rect := shape_node.shape as RectangleShape2D
    if state.begins_with("strong"):
        rect.size = Vector2(250,150)
        attack_area.position = Vector2(115.0*facing,-70)
    else:
        rect.size = Vector2(180,120)
        attack_area.position = Vector2(88.0*facing,-60)
''','''func _update_attack_area_transform() -> void:
    if not attack_area:
        return
    var shape_node := attack_area.get_child(0) as CollisionShape2D
    var rect := shape_node.shape as RectangleShape2D
    rect.size = Vector2(150,100)
    attack_area.position = Vector2(78.0*facing,-55)
''')
rep('if not (state.begins_with("attack") or state.begins_with("strong")): return','if not state.begins_with("attack"): return')
s=s.replace('title.text="ホンブギの冒険  Android Test V8"','title.text="ホンブギの冒険  Android Test V10"')
rep('    _touch_button(layer,"JUMP",Vector2(1010,650),"jump",52); _touch_button(layer,"ATK",Vector2(1150,690),"attack",52); _touch_button(layer,"STR",Vector2(1160,565),"strong_attack",48); _touch_button(layer,"DODGE",Vector2(890,700),"dodge",48); _touch_button(layer,"DASH",Vector2(905,590),"dash",45)\n','    _touch_button(layer,"JUMP",Vector2(1010,650),"jump",52); _touch_button(layer,"ATK",Vector2(1150,690),"attack",52); _touch_button(layer,"DODGE",Vector2(890,700),"dodge",48); _touch_button(layer,"DASH",Vector2(905,590),"dash",45)\n')
p.write_text(s,encoding='utf-8')
print('V10 game patch applied')
