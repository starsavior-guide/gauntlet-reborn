from pathlib import Path

p = Path('scripts/game.gd')
s = p.read_text(encoding='utf-8')

def rep(a, b, count=1):
    global s
    if a not in s:
        raise SystemExit('Missing source block: ' + a[:180])
    s = s.replace(a, b, count)

rep('const JUMP_VELOCITY := -510.0', 'const JUMP_VELOCITY := -550.0\nconst WALL_JUMP_VELOCITY := -570.0\nconst WALL_JUMP_PUSH := 330.0')

start = s.index('const PLAYER_FRAME_BOTTOMS := {')
end = s.index('\n}\n', start) + 3
s = s[:start] + '''const PLAYER_FRAME_BOTTOMS := {\n    "idle": [400],\n    "walk": [400,400,400,400,400,400],\n    "jump": [400],\n    "attack1": [400,400,400,400,400],\n    "dash": [400,400,400],\n    "dodge": [400,400,400,400,400,400],\n    "damage": [400,400],\n    "save_pose": [400]\n}\n''' + s[end:]

rep('player_frames = _load_frames("res://data/player_v10_animations.json")', 'player_frames = _load_frames("res://data/player_v11_animations.json")')
rep('title.text="ホンブギの冒険  Android Test V10"', 'title.text="ホンブギの冒険  Android Test V11"')

rep('player = CharacterBody2D.new(); player.name = "ほんにょん"; player.collision_layer = 2; player.collision_mask = 1; add_child(player)',
    'player = CharacterBody2D.new(); player.name = "ほんにょん"; player.collision_layer = 2; player.collision_mask = 1; player.z_index = 20; add_child(player)')
rep('var col := CollisionShape2D.new(); var sh := CapsuleShape2D.new(); sh.radius = 26; sh.height = 104; col.shape = sh; col.position = Vector2(0,-52); player.add_child(col)',
    'var col := CollisionShape2D.new(); var sh := CapsuleShape2D.new(); sh.radius = 22; sh.height = 92; col.shape = sh; col.position = Vector2(0,-46); player.add_child(col)\n        player.safe_margin = 0.02; player.floor_snap_length = 6.0')

rep('player_sprite = AnimatedSprite2D.new(); player_sprite.sprite_frames = player_frames; player_sprite.position = Vector2(0,-145); player_sprite.play("idle"); player.add_child(player_sprite); _apply_player_visual_anchor()',
    'player_sprite = AnimatedSprite2D.new(); player_sprite.sprite_frames = player_frames; player_sprite.position = Vector2(0,-144); player_sprite.z_index = 1; player_sprite.play("idle"); player.add_child(player_sprite)')
rep('_process_attack_hits(); _update_player_animation(); _apply_player_visual_anchor(); _update_enemies(delta);',
    '_process_attack_hits(); _update_player_animation(); _update_enemies(delta);')

old_jump = '''        if Input.is_action_just_pressed("jump"):\n            var can_double := bool(flags.get("turtle_jump",false)) and jump_count < 2\n            if player.is_on_floor() or can_double:\n                player.velocity.y = JUMP_VELOCITY; jump_count += 1; _play_sfx("res://assets/audio/jump.ogg")\n'''
new_jump = '''        if Input.is_action_just_pressed("jump"):\n            var can_double := bool(flags.get("turtle_jump",false)) and jump_count < 2\n            if player.is_on_floor() or can_double:\n                player.velocity.y = JUMP_VELOCITY; jump_count += 1; _play_sfx("res://assets/audio/jump.ogg")\n            elif player.is_on_wall():\n                # Escape assist for narrow shafts / Scene 3 softlock locations.\n                var wall_n := player.get_wall_normal()\n                var push_dir := wall_n.x if absf(wall_n.x) > 0.1 else -facing\n                player.velocity.y = WALL_JUMP_VELOCITY\n                player.velocity.x = push_dir * WALL_JUMP_PUSH\n                facing = signf(push_dir)\n                jump_count = 1\n                _play_sfx("res://assets/audio/jump.ogg")\n'''
rep(old_jump, new_jump)

# 5-frame basic attack, no skill/effect state.
s = s.replace('state_timer = 0.31\n    combo_step = 0', 'state_timer = 0.30\n    combo_step = 0', 1)

p.write_text(s, encoding='utf-8')
print('V11 stable motion + wall-jump patch applied')
