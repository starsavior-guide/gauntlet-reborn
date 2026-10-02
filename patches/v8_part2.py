from pathlib import Path
p=Path("scripts/game.gd")
s=p.read_text(encoding="utf-8")
def r(a,b):
    global s
    if a not in s: raise SystemExit("missing:"+a[:80])
    s=s.replace(a,b,1)

r('''    sp.position = Vector2(0,-maxf(55.0,visual_height))
    sp.scale = Vector2(scale_v,scale_v)
    b.add_child(sp)
    b.set_meta("kind",kind); b.set_meta("hp",maxi(1,source_hp)); b.set_meta("max_hp",maxi(1,source_hp)); b.set_meta("dir",-1.0); b.set_meta("cooldown",randf_range(0.2,1.0)); b.set_meta("hurt",0.0)
''',
'''    sp.name="Visual"
    sp.position = Vector2(0,-maxf(55.0,visual_height))
    sp.scale = Vector2(scale_v,scale_v)
    b.add_child(sp)
    var ehp:=ProgressBar.new()
    ehp.name="HPBar"
    ehp.position=Vector2(-45,-135)
    ehp.size=Vector2(90,8)
    ehp.show_percentage=false
    ehp.max_value=maxi(1,source_hp)
    ehp.value=maxi(1,source_hp)
    b.add_child(ehp)
    b.set_meta("kind",kind); b.set_meta("hp",maxi(1,source_hp)); b.set_meta("max_hp",maxi(1,source_hp)); b.set_meta("dir",-1.0); b.set_meta("cooldown",randf_range(0.2,1.0)); b.set_meta("hurt",0.0)
''')

r('''func _damage_enemy(body: CharacterBody2D, amount: int) -> void:
    var hp := int(body.get_meta("hp",1))-amount; body.set_meta("hp",hp); body.set_meta("hurt",0.18); body.velocity.x = facing*280.0; body.velocity.y = -110.0; _play_sfx("res://assets/audio/hit.ogg")
    if hp <= 0:
''',
'''func _damage_enemy(body: CharacterBody2D, amount: int) -> void:
    var max_hp:=int(body.get_meta("max_hp",1))
    var hp:=int(body.get_meta("hp",1))-amount
    body.set_meta("hp",hp); body.set_meta("hurt",0.18); body.velocity.x=facing*280.0; body.velocity.y=-110.0
    var bar:=body.get_node_or_null("HPBar") as ProgressBar
    if bar: bar.value=maxi(0,hp)
    var visual:=body.get_node_or_null("Visual") as Sprite2D
    if visual: visual.modulate=Color(1.0,0.35,0.35,1.0)
    _show_damage_number(body.position+Vector2(0,-125),amount,maxi(0,hp),max_hp)
    _play_sfx("res://assets/audio/hit.ogg")
    if hp <= 0:
''')

r('    boss_bar.value=maxi(0,hp); boss_label.text="%s  %d / %d" % [String(boss.get_meta("display_name","BOSS")),maxi(0,hp),max_hp]; _play_sfx("res://assets/audio/hit.ogg")\n',
  '    boss_bar.value=maxi(0,hp); boss_label.text="%s  %d / %d" % [String(boss.get_meta("display_name","BOSS")),maxi(0,hp),max_hp]; _show_damage_number(boss.position+Vector2(0,-230),amount,maxi(0,hp),max_hp); _play_sfx("res://assets/audio/hit.ogg")\n')

r('    var hurt_anim := {"boss_crab":"crab_hurt","boss_chamber":"chamber_hurt"}.get(kind,"")\n',
  '    var hurt_anim: String = String({"boss_crab":"crab_hurt","boss_chamber":"chamber_hurt"}.get(kind,""))\n')
r('        var dist := e.position.distance_to(player.position); var flying := bool(e.get_meta("flying",false))\n',
  '        var dist: float = e.position.distance_to(player.position); var flying := bool(e.get_meta("flying",false))\n')

r('''        var kind := String(e.get_meta("kind")); var hurt := maxf(0.0,float(e.get_meta("hurt",0.0))-delta); e.set_meta("hurt",hurt)
        var cooldown := maxf(0.0,float(e.get_meta("cooldown",0.0))-delta); e.set_meta("cooldown",cooldown)
''',
'''        var kind := String(e.get_meta("kind")); var hurt := maxf(0.0,float(e.get_meta("hurt",0.0))-delta); e.set_meta("hurt",hurt)
        var enemy_sp:=e.get_node_or_null("Visual") as Sprite2D
        if enemy_sp:
            enemy_sp.modulate=Color(1.0,0.35,0.35,1.0) if hurt>0.0 else Color.WHITE
        var cooldown := maxf(0.0,float(e.get_meta("cooldown",0.0))-delta); e.set_meta("cooldown",cooldown)
''')

marker='func _update_player_animation() -> void:\n'
if marker not in s: raise SystemExit("animation marker missing")
helper='''func _apply_player_visual_anchor() -> void:
    if not player_sprite: return
    var anim:=String(player_sprite.animation)
    if not PLAYER_FRAME_BOTTOMS.has(anim):
        player_sprite.position.y=-145.0
        return
    var bottoms:Array=PLAYER_FRAME_BOTTOMS[anim]
    if bottoms.is_empty(): return
    var idx:=clampi(player_sprite.frame,0,bottoms.size()-1)
    player_sprite.position.y=256.0-float(bottoms[idx])

func _show_damage_number(world_pos:Vector2,amount:int,hp_left:int,max_hp:int) -> void:
    if not stage_node or not is_instance_valid(stage_node): return
    var lab:=Label.new()
    lab.text="-%d   HP %d/%d" % [amount,hp_left,max_hp]
    lab.position=world_pos+Vector2(-55,-10)
    lab.z_index=50
    lab.add_theme_font_size_override("font_size",18)
    lab.add_theme_color_override("font_color",Color.WHITE)
    lab.add_theme_color_override("font_outline_color",Color.BLACK)
    lab.add_theme_constant_override("outline_size",4)
    stage_node.add_child(lab)
    var tw:=create_tween()
    tw.set_parallel(true)
    tw.tween_property(lab,"position",lab.position+Vector2(0,-38),0.55)
    tw.tween_property(lab,"modulate:a",0.0,0.55)
    tw.chain().tween_callback(lab.queue_free)

'''
s=s.replace(marker,helper+marker,1)
p.write_text(s,encoding="utf-8")
