from pathlib import Path
p=Path('scripts/game.gd')
s=p.read_text(encoding='utf-8')
old='''        if mask == 15:\n            _add_box_collision(body,Vector2(cx*32+16,cy*32+16),Vector2(32,32))\n        else:\n            # PGMMV wall bits: top=1, left=2, right=4, bottom=8.\n            if (mask & 1) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+2),Vector2(32,4))\n            if (mask & 2) != 0: _add_box_collision(body,Vector2(cx*32+2,cy*32+16),Vector2(4,32))\n            if (mask & 4) != 0: _add_box_collision(body,Vector2(cx*32+30,cy*32+16),Vector2(4,32))\n            if (mask & 8) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+30),Vector2(32,4))\n\nfunc _add_box_collision(parent: Node, pos: Vector2, size: Vector2) -> void:\n    var sh := RectangleShape2D.new(); sh.size = size\n    var cs := CollisionShape2D.new(); cs.position = pos; cs.shape = sh; parent.add_child(cs)\n'''
new='''        if mask == 15:\n            _add_box_collision(body,Vector2(cx*32+16,cy*32+16),Vector2(32,32))\n        elif mask == 1:\n            # PGMMV top-only tiles are jump-through platforms. A normal Godot\n            # rectangle blocks from both sides and creates ceiling traps under them.\n            _add_one_way_top_collision(body,Vector2(cx*32+16,cy*32+2),Vector2(32,4))\n        else:\n            # Rare partial walls keep ordinary solid edge behaviour.\n            if (mask & 1) != 0: _add_one_way_top_collision(body,Vector2(cx*32+16,cy*32+2),Vector2(32,4))\n            if (mask & 2) != 0: _add_box_collision(body,Vector2(cx*32+2,cy*32+16),Vector2(4,32))\n            if (mask & 4) != 0: _add_box_collision(body,Vector2(cx*32+30,cy*32+16),Vector2(4,32))\n            if (mask & 8) != 0: _add_box_collision(body,Vector2(cx*32+16,cy*32+30),Vector2(32,4))\n\nfunc _add_box_collision(parent: Node, pos: Vector2, size: Vector2) -> void:\n    var sh := RectangleShape2D.new(); sh.size = size\n    var cs := CollisionShape2D.new(); cs.position = pos; cs.shape = sh; parent.add_child(cs)\n\nfunc _add_one_way_top_collision(parent: Node, pos: Vector2, size: Vector2) -> void:\n    var sh := RectangleShape2D.new(); sh.size = size\n    var cs := CollisionShape2D.new()\n    cs.position = pos\n    cs.shape = sh\n    cs.one_way_collision = true\n    cs.one_way_collision_margin = 8.0\n    parent.add_child(cs)\n'''
if old not in s:
    raise SystemExit('collision source block not found')
s=s.replace(old,new,1)
# Slightly reduce the physics safe margin so narrow solid corridors do not snag on corners.
old2='player = CharacterBody2D.new(); player.name = "ほんにょん"; player.collision_layer = 2; player.collision_mask = 1; add_child(player)'
new2='player = CharacterBody2D.new(); player.name = "ほんにょん"; player.collision_layer = 2; player.collision_mask = 1; player.safe_margin = 0.02; add_child(player)'
if old2 not in s:
    raise SystemExit('player CharacterBody2D line not found')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('V12 one-way platform collision patch applied')
