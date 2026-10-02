from pathlib import Path
p=Path("scripts/game.gd")
s=p.read_text(encoding="utf-8")
def r(a,b):
    global s
    if a not in s: raise SystemExit("missing:"+a[:80])
    s=s.replace(a,b,1)

r('const LEGACY_SAVE_PATH := "user://honbugi_v6_save.json"\n',
'''const LEGACY_SAVE_PATH := "user://honbugi_v6_save.json"
const TEST_MODE := true
const TEST_MAX_HP := 99999
const TEST_ATTACK_POWER := 9999
const PLAYER_FRAME_BOTTOMS := {
    "idle":[401,401,401],
    "walk":[512,512,512,512,512,512,512,512,512],
    "jump":[512,512],
    "attack1":[512,512,512,512,512,512],
    "attack2":[512,512,512,512,512,512],
    "attack3":[512,512,512,512,512,512],
    "strong1":[392,512],
    "dash":[443,443,444,443],
    "dodge":[392,392,393,392,394,393,393,393,392,397,392],
    "damage":[512,512],
    "save_pose":[512,512]
}
''')
r('    _create_ui()\n    _load_stage("outside", Vector2(2002,453))\n',
'''    _create_ui()
    if TEST_MODE:
        player_max_hp=TEST_MAX_HP
        player_hp=TEST_MAX_HP
    _load_stage("outside", Vector2(2002,453))
''')
s=s.replace('    _bind_key("interact", KEY_E)\n','')
r('''            if (mask & 1) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+2),Vector2(32,4))
            if (mask & 2) != 0: _add_box_collision(body,Vector2(cx*32+30,cy*32+16),Vector2(4,32))
            if (mask & 4) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+30),Vector2(32,4))
            if (mask & 8) != 0: _add_box_collision(body,Vector2(cx*32+2,cy*32+16),Vector2(4,32))
''',
'''            # PGMMV: top=1,left=2,right=4,bottom=8
            if (mask & 1) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+2),Vector2(32,4))
            if (mask & 2) != 0: _add_box_collision(body,Vector2(cx*32+2,cy*32+16),Vector2(4,32))
            if (mask & 4) != 0: _add_box_collision(body,Vector2(cx*32+30,cy*32+16),Vector2(4,32))
            if (mask & 8) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+30),Vector2(32,4))
''')
r('player_sprite = AnimatedSprite2D.new(); player_sprite.sprite_frames = player_frames; player_sprite.position = Vector2(0,-144); player_sprite.play("idle"); player.add_child(player_sprite)',
  'player_sprite = AnimatedSprite2D.new(); player_sprite.sprite_frames = player_frames; player_sprite.position = Vector2(0,-145); player_sprite.play("idle"); player.add_child(player_sprite); _apply_player_visual_anchor()')
s=s.replace('    if Input.is_action_just_pressed("interact"): _try_save_at_statue()\n','')
r('    player.move_and_slide(); player_sprite.flip_h = facing < 0; attack_area.position = Vector2(78*facing,-55)\n    _process_attack_hits(); _update_player_animation(); _update_enemies(delta);',
  '    player.move_and_slide(); player_sprite.flip_h = facing < 0; _update_attack_area_transform()\n    _process_attack_hits(); _update_player_animation(); _apply_player_visual_anchor(); _update_enemies(delta);')
r('''func _attack_damage() -> int:
    var base := 20 if state.begins_with("strong") else 10
    if bool(flags.get("hands",false)): base += 20
    return base
''',
'''func _attack_damage() -> int:
    if TEST_MODE: return TEST_ATTACK_POWER
    var base := 20 if state.begins_with("strong") else 10
    if bool(flags.get("hands",false)): base += 20
    return base

func _update_attack_area_transform() -> void:
    if not attack_area: return
    var sn:=attack_area.get_child(0) as CollisionShape2D
    var rect:=sn.shape as RectangleShape2D
    if state.begins_with("strong"):
        rect.size=Vector2(250,150)
        attack_area.position=Vector2(115.0*facing,-70)
    else:
        rect.size=Vector2(180,120)
        attack_area.position=Vector2(88.0*facing,-60)
''')
p.write_text(s,encoding="utf-8")
