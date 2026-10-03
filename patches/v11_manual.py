from pathlib import Path

p = Path('scripts/game.gd')
s = p.read_text(encoding='utf-8')

def rep(a, b, count=1):
    global s
    if a not in s:
        raise SystemExit('Missing source block: ' + a[:180])
    s = s.replace(a, b, count)

rep('player_frames = _load_frames("res://data/player_v10_animations.json")',
    'player_frames = _load_frames("res://data/player_v11_animations.json")')
rep('title.text="ホンブギの冒険  Android Test V10"',
    'title.text="ホンブギの冒険  Android Test V11"')

# Always draw the player above stage enemies/items/background so jump/roll frames
# cannot look chopped when overlapping foreground sprites.
rep('player = CharacterBody2D.new(); player.name = "ほんにょん"; player.collision_layer = 2; player.collision_mask = 1; add_child(player)',
    'player = CharacterBody2D.new(); player.name = "ほんにょん"; player.collision_layer = 2; player.collision_mask = 1; player.z_index = 20; add_child(player)')

# V11 frames are authored in one fixed 512x512 coordinate system. Disable all
# per-frame automatic anchor correction and use one fixed visual origin.
rep('player_sprite = AnimatedSprite2D.new(); player_sprite.sprite_frames = player_frames; player_sprite.position = Vector2(0,-145); player_sprite.play("idle"); player.add_child(player_sprite); _apply_player_visual_anchor()',
    'player_sprite = AnimatedSprite2D.new(); player_sprite.sprite_frames = player_frames; player_sprite.position = Vector2(0,-144); player_sprite.z_index = 1; player_sprite.play("idle"); player.add_child(player_sprite)')
rep('_process_attack_hits(); _update_player_animation(); _apply_player_visual_anchor(); _update_enemies(delta);',
    '_process_attack_hits(); _update_player_animation(); _update_enemies(delta);')

start = s.find('func _apply_player_visual_anchor() -> void:\n')
if start != -1:
    end = s.find('\nfunc ', start + 5)
    if end == -1:
        raise SystemExit('Could not locate end of _apply_player_visual_anchor')
    s = s[:start] + '''func _apply_player_visual_anchor() -> void:\n    if player_sprite:\n        player_sprite.position = Vector2(0,-144)\n\n''' + s[end+1:]

# 5 attack frames x 16/300 sec = 0.267 sec. Keep state just long enough
# to display the return pose before normal movement resumes.
s = s.replace('state_timer = 0.31\n    combo_step = 0', 'state_timer = 0.30\n    combo_step = 0', 1)

p.write_text(s, encoding='utf-8')
print('V11 manual-pivot game patch applied')
