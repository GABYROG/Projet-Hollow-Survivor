"""physics.py — Logique de jeu style Vampire Survivors."""

import math, random, pygame
from settings  import (MAP_W, MAP_H, PLAYER_W, PLAYER_H, ENEMY_MASS,
                       WEAPONS, ARROW_SPEED, MAX_ENEMIES)
from entities  import Rect, Projectile, Particle, DamageNumber, BasicEnemy

SLOWMO = 0.10   # facteur de temps pendant level-up



#  UPDATE PRINCIPAL

def update(gs) -> bool:
    now     = pygame.time.get_ticks()
    slowmo  = (gs.screen_state == "level_up")
    spd_f   = SLOWMO if slowmo else 1.0
    player  = gs.player
    dt_s    = (1/60) * spd_f

    player.tick(now, dt_s)

    # Vitesse avec bonus items
    base_speed = player.speed
    if gs.item_system:
        player.speed = base_speed * gs.item_system.get_speed_mult(now)

    if not slowmo:
        player.move()
        player.clamp()
    else:
        player.speed *= 0.3
        player.move()
        player.speed = base_speed * gs.item_system.get_speed_mult(now) if gs.item_system else base_speed
        player.clamp()

    player.speed = base_speed  # restaure pour le prochain frame

    # Items tick
    if gs.item_system:
        gs.item_system.tick(player, gs.enemies, gs, now, dt_s)

    # Toutes les armes tirent automatiquement
    _auto_weapons(gs, now, spd_f)

    # Pickup gemmes
    if gs.xp_system:
        leveled = gs.xp_system.update_pickup(player)
        if gs.xp_system.pending_offer and gs.screen_state == "playing":
            _freeze_movement(player)
            gs.screen_state = "level_up"

    # Vagues
    gs.wave_manager.update(gs, now, spd_f)
    if gs.wave_manager.game_won:
        gs.screen_state = "victory"; return True

    if not _update_enemies(gs, now, spd_f): return False
    if gs.boss and not _update_boss(gs, now, spd_f): return False

    _resolve_push(gs)
    _update_projectiles(gs, spd_f, now)
    _update_orbits(gs, now, spd_f)
    _update_baskets(gs)
    _update_fx(gs)
    if gs.camera_shake > 0: gs.camera_shake -= 1
    return True


def _freeze_movement(player):
    player.move_left = player.move_right = player.move_up = player.move_down = False



#  ARMES AUTOMATIQUES


def _auto_weapons(gs, now, spd_f):
    player = gs.player
    for wid in player.weapons:
        w = WEAPONS.get(wid)
        if not w: continue
        cd   = max(80, int(w["cooldown"] * player.atk_speed_mult))
        last = player.weapon_timers.get(wid, 0)
        if now - last >= cd:
            player.weapon_timers[wid] = now
            wtype = w["type"]
            if wtype == "melee_swing":  _swing(gs, wid, w, now)
            elif wtype == "whip":       _whip(gs, wid, w, now)
            elif wtype == "melee_area": _area(gs, wid, w, now)
            elif wtype == "projectile": _shoot(gs, wid, w, now, spd_f)
            # melee_orbit is handled by _update_orbits


def _nearest_enemy(gs):
    """Retourne l'ennemi le plus proche du joueur."""
    pcx, pcy = gs.player.center()
    best, bd = None, float("inf")
    for e in gs.enemies + ([gs.boss] if gs.boss else []):
        d = math.hypot(*[a-b for a,b in zip(e.center(),(pcx,pcy))])
        if d < bd: bd=d; best=e
    return best


def _calc_dmg(gs, base):
    player = gs.player
    dmg    = base + player.bonus_dmg
    # Bonus items (cardio, lame brulante, etc.)
    if gs.item_system:
        dmg = int(dmg * gs.item_system.get_dmg_mult(player, pygame.time.get_ticks()))
    crit   = random.random() < player.crit_chance
    if crit: dmg = int(dmg * 2.0)
    return max(1, dmg), crit


def _hit_enemy(gs, enemy, dmg, crit, angle, force, bleed=False, poison=False, stun_ms=0, now=0):
    """Applique les degats + effets a un ennemi."""
    enemy.take_hit(dmg, angle, force)
    ecx, ecy = enemy.center()
    color = (255,220,50) if crit else (255,255,255)
    gs.damage_nums.append(DamageNumber(ecx, ecy, dmg, crit, color))
    _spawn_hits(gs, ecx, ecy, enemy.COLOR)
    if bleed and now:
        enemy.apply_bleed(max(1,dmg//4), now+5000)
    if poison and now:
        enemy.apply_poison(max(1,dmg//5), now+4000)
    # Item callback
    if gs.item_system:
        gs.item_system.on_hit_enemy(gs.player, enemy, dmg, now or pygame.time.get_ticks())


def _spawn_hits(gs, x, y, color):
    for _ in range(5):
        gs.particles.append(Particle(x, y, color,
            vx=random.uniform(-2.5,2.5), vy=random.uniform(-2.5,0.5),
            life=20, size=3, glow=True))


def _kill_enemy(gs, i):
    e = gs.enemies.pop(i)
    if gs.xp_system: gs.xp_system.drop_gems(e)
    gs.on_kill(getattr(e,"XP",1))
    # Multiplicateur d'or (Sou fetiche)
    if gs.item_system:
        extra = gs.item_system.get_gold_mult() - 1.0
        if extra > 0:
            gs.gold += int(gs.gold_gain * extra)
        gs.item_system.on_kill(gs.player, pygame.time.get_ticks())
    gs.camera_shake = max(gs.camera_shake, 3)
    ecx, ecy = e.x+e.SIZE//2, e.y+e.SIZE//2
    for _ in range(12):
        gs.particles.append(Particle(ecx, ecy, e.COLOR,
            vx=random.uniform(-3,3), vy=random.uniform(-4,1), life=30, size=5))


# ── Melee swing ──
def _swing(gs, wid, w, now):
    player = gs.player
    pcx, pcy = player.center()

    # PRIORITE : direction de la souris (convertie en coords monde)
    cam_x, cam_y = gs.get_camera()
    mx, my = pygame.mouse.get_pos()
    mouse_wx = mx + cam_x
    mouse_wy = my + cam_y
    dx = mouse_wx - pcx; dy = mouse_wy - pcy
    if abs(dx) > 5 or abs(dy) > 5:
        angle = math.atan2(dy, dx)
    else:
        # Fallback : ennemi le plus proche
        target = _nearest_enemy(gs)
        if target:
            ecx, ecy = target.center()
            angle = math.atan2(ecy-pcy, ecx-pcx)
        else:
            angle = 0.0

    reach  = w["portee"]  * player.area_mult
    hw     = w["largeur"] * player.area_mult / 2
    spread = 0.75

    # Hitbox centrée sur le joueur et s'étendant vers l'avant
    # On part du centre joueur (pas à reach/2 devant) pour couvrir les ennemis proches
    hcx = pcx + math.cos(angle) * reach * 0.5
    hcy = pcy + math.sin(angle) * reach * 0.5
    atk = Rect(hcx - reach*0.6, hcy - reach*0.6, reach*1.2, reach*1.2)

    mods   = player.weapon_mods
    bleed  = w.get("bleed") or mods.get(f"{wid}_bleed_dur")
    double = mods.get(f"{wid}_double")

    dead = []
    for i, e in enumerate(gs.enemies):
        if not atk.collides(e.hitbox()): continue
        ecx, ecy = e.center()
        ha   = math.atan2(ecy-pcy, ecx-pcx)
        diff = abs(math.atan2(math.sin(ha-angle), math.cos(ha-angle)))
        if diff > spread: continue
        dmg, crit = _calc_dmg(gs, w["degats"])
        if double: dmg = int(dmg*1.6)
        _hit_enemy(gs, e, dmg, crit, ha, w["knockback"], bleed=bleed, now=now)
        if e.is_dead(): dead.append(i)
    for i in reversed(dead): _kill_enemy(gs, i)

    # Boss aussi
    if gs.boss:
        eh = gs.boss.hitbox()
        if atk.collides(eh):
            ecx, ecy = gs.boss.center()
            ha = math.atan2(ecy-pcy, ecx-pcx)
            if abs(math.atan2(math.sin(ha-angle), math.cos(ha-angle))) <= spread:
                dmg, crit = _calc_dmg(gs, w["degats"])
                if hasattr(gs.boss, "take_damage"): gs.boss.take_damage(dmg)
                else: gs.boss.hp -= dmg
                gs.damage_nums.append(DamageNumber(ecx, ecy, dmg, crit))
                if gs.boss.is_dead(): gs.on_boss_killed()

    # Particules
    for _ in range(8):
        off  = random.uniform(-spread, spread)
        dist = random.uniform(10, reach)
        px   = pcx + math.cos(angle+off)*dist
        py   = pcy + math.sin(angle+off)*dist
        gs.particles.append(Particle(px, py, w["couleur"],
            vx=math.cos(angle+off+math.pi/2)*2,
            vy=math.sin(angle+off+math.pi/2)*2,
            life=14, size=3, glow=True))


# ── Whip ──
def _whip(gs, wid, w, now):
    player = gs.player
    pcx, pcy = player.center()
    cam_x, cam_y = gs.get_camera()
    mx, my = pygame.mouse.get_pos()
    angle  = math.atan2((my+cam_y)-pcy, (mx+cam_x)-pcx)

    reach  = int(w["portee"]*player.area_mult + player.weapon_mods.get("fouet_range",0))
    hw     = w["largeur"] * player.area_mult / 2
    triple = player.weapon_mods.get("fouet_triple")
    double = player.weapon_mods.get("fouet_double")
    offsets = [0, math.pi/3, -math.pi/3] if triple else ([0, math.pi/4] if double else [0])

    for off in offsets:
        a   = angle + off
        hcx = pcx + math.cos(a)*reach/2
        hcy = pcy + math.sin(a)*reach/2
        atk = Rect(hcx-reach/2, hcy-hw, reach, hw*2)
        dead = []
        for i, e in enumerate(gs.enemies):
            if not atk.collides(e.hitbox()): continue
            ecx,ecy = e.center()
            ha = math.atan2(ecy-pcy, ecx-pcx)
            dmg, crit = _calc_dmg(gs, w["degats"])
            _hit_enemy(gs, e, dmg, crit, ha, w["knockback"], now=now)
            if e.is_dead(): dead.append(i)
        for i in reversed(dead): _kill_enemy(gs, i)

    for _ in range(6):
        gs.particles.append(Particle(
            pcx+math.cos(angle)*random.uniform(10,reach),
            pcy+math.sin(angle)*random.uniform(-hw,hw),
            w["couleur"], life=12, size=4, glow=True))


# ── Area ──
def _area(gs, wid, w, now):
    player = gs.player
    pcx, pcy = player.center()
    r    = w["portee"] * player.area_mult
    atk  = Rect(pcx-r, pcy-r, r*2, r*2)
    slow = player.weapon_mods.get("ail_slow") if wid=="ail" else False
    vuln = player.weapon_mods.get("ail_vuln") if wid=="ail" else False
    kb2  = player.weapon_mods.get("marteau_kb2") if wid=="marteau" else False
    wave = player.weapon_mods.get("marteau_wave") if wid=="marteau" else False
    poison= w.get("poison")

    dead = []
    for i, e in enumerate(gs.enemies):
        if not atk.collides(e.hitbox()): continue
        dmg, crit = _calc_dmg(gs, w["degats"])
        ecx,ecy = e.center()
        ha = math.atan2(ecy-pcy, ecx-pcx)
        kb = w["knockback"] * (2 if kb2 else 1)
        _hit_enemy(gs, e, dmg, crit, ha, kb, poison=poison, now=now)
        if e.is_dead(): dead.append(i)
    for i in reversed(dead): _kill_enemy(gs, i)

    if wave:
        for i in range(4):
            a = i * math.pi/2
            gs.projectiles.append(Projectile(pcx,pcy,
                math.cos(a)*8, math.sin(a)*8,
                player.bonus_dmg+2, w["couleur"], 10))

    for _ in range(14):
        a = random.uniform(0, math.pi*2)
        gs.particles.append(Particle(
            pcx+math.cos(a)*r*0.6, pcy+math.sin(a)*r*0.6,
            w["couleur"], life=22, size=5, glow=True))


# ── Projectile ──
def _shoot(gs, wid, w, now, spd_f):
    player = gs.player
    pcx, pcy = player.center()
    target = _nearest_enemy(gs)
    if not target: return
    ecx,ecy = target.center()
    base_angle = math.atan2(ecy-pcy, ecx-pcx)
    spd = w.get("proj_speed",ARROW_SPEED) * player.proj_speed_mult * spd_f
    dmg_base = w["degats"]
    col = w.get("proj_color", w["couleur"])
    r   = w.get("proj_r", 6)
    pierce  = player.weapon_mods.get(f"{wid}_pierce", w.get("pierce",0))
    explode = w.get("explode") or player.weapon_mods.get(f"{wid}_explode") or player.weapon_mods.get(f"{wid}_burn")
    chain   = player.weapon_mods.get(f"foudre_chain", w.get("chain",0)) if wid=="foudre" else 0

    angles = [base_angle]
    if player.weapon_mods.get(f"{wid}_nova"):
        angles = [base_angle + i*math.pi/4 for i in range(8)]
    elif player.weapon_mods.get(f"{wid}_rain") or player.weapon_mods.get(f"{wid}_quad"):
        angles = [base_angle + off for off in (-0.3,-0.15,0,0.15,0.3)]
    elif player.weapon_mods.get(f"{wid}_triple"):
        angles = [base_angle + off for off in (-0.22,0,0.22)]
    elif player.weapon_mods.get(f"{wid}_double") or player.weapon_mods.get(f"{wid}_fan"):
        angles = [base_angle + off for off in (-0.18,0,0.18)]
    count = player.weapon_mods.get(f"{wid}_count", 1)
    if count > 1:
        step = 0.18
        angles = [base_angle + (i - count//2)*step for i in range(count)]

    for a in angles:
        vx = math.cos(a)*spd; vy = math.sin(a)*spd
        gs.projectiles.append(Projectile(pcx,pcy,vx,vy,
            dmg_base, col, r, pierce, chain, explode))



#  ORBITES (bible, bouclier)


def _update_orbits(gs, now, spd_f):
    player = gs.player
    pcx, pcy = player.center()

    for wid in player.weapons:
        w = WEAPONS.get(wid)
        if not w or w["type"] != "melee_orbit": continue

        count  = player.weapon_mods.get(f"{wid}_count",  w.get("orbit_count", 2))
        spd_w  = player.weapon_mods.get(f"{wid}_speed",  w.get("orbit_speed", 2.0))
        radius = player.weapon_mods.get(f"{wid}_radius", w.get("portee", 80))
        radius *= player.area_mult

        # Angle de base qui tourne
        key = f"orbit_{wid}"
        angle = player.orbit_angles.get(key, 0.0)
        angle += spd_w * spd_f * 0.04
        player.orbit_angles[key] = angle % (math.pi*2)

        cd = max(100, int(w["cooldown"] * player.atk_speed_mult))

        for k in range(count):
            a   = angle + k * (math.pi*2/count)
            ox  = pcx + math.cos(a)*radius
            oy  = pcy + math.sin(a)*radius
            ohb = Rect(ox-w["largeur"]//2, oy-w["largeur"]//2,
                       w["largeur"], w["largeur"])

            last = player.weapon_timers.get(f"{wid}_{k}", 0)
            if now - last < cd: continue

            dead = []
            for i, e in enumerate(gs.enemies):
                if ohb.collides(e.hitbox()):
                    dmg, crit = _calc_dmg(gs, w["degats"])
                    ha = math.atan2(oy-e.center()[1], ox-e.center()[0])
                    _hit_enemy(gs, e, dmg, crit, ha, w["knockback"], now=now)
                    player.weapon_timers[f"{wid}_{k}"] = now
                    if e.is_dead(): dead.append(i)
            for i in reversed(dead): _kill_enemy(gs, i)


#  ENNEMIS


def _update_enemies(gs, now, spd_f) -> bool:
    player   = gs.player
    pcx, pcy = player.center()
    ph       = player.hitbox()
    dead     = []

    for i, e in enumerate(gs.enemies):
        e.update(pcx, pcy, now, gs, spd_f)

        # Projectiles ranged
        for p in list(e.projectiles):
            pr = Rect(p["x"]-p["r"], p["y"]-p["r"], p["r"]*2, p["r"]*2)
            if ph.collides(pr) and p.get("vx",0) != 0:
                dmg = p["dmg"]
                if gs.item_system:
                    dmg = gs.item_system.on_player_hit(player, dmg, gs.enemies, gs, now)
                if dmg > 0:
                    player.take_damage(dmg, now)
                    gs.camera_shake = max(gs.camera_shake, 6)
                p["vx"] = p["vy"] = 0
                if not player.is_alive():
                    if gs.item_system and gs.item_system.try_revive(player): continue
                    return False

        # Contact melee
        if ph.collides(e.hitbox()) and now - e.last_atk >= e.ATK_CD:
            e.last_atk = now
            dmg = e.DMG
            if gs.item_system:
                dmg = gs.item_system.on_player_hit(player, dmg, gs.enemies, gs, now)
            if dmg > 0 and player.take_damage(dmg, now):
                gs.camera_shake = max(gs.camera_shake, 5)
            if not player.is_alive():
                if gs.item_system and gs.item_system.try_revive(player): pass
                else: return False

        if e.is_dead(): dead.append(i)

    for i in reversed(dead): _kill_enemy(gs, i)
    return True


def _update_boss(gs, now, spd_f) -> bool:
    player = gs.player
    ph     = player.hitbox()
    boss   = gs.boss

    boss.update(player.center()[0], player.center()[1], now, gs)

    if ph.collides(boss.hitbox()) and now - boss.last_atk >= 1000:
        boss.last_atk = now
        dmg = 5
        if gs.item_system:
            dmg = gs.item_system.on_player_hit(player, dmg, gs.enemies, gs, now)
        if dmg > 0 and player.take_damage(dmg, now):
            gs.camera_shake = max(gs.camera_shake, 8)
        if not player.is_alive():
            if not (gs.item_system and gs.item_system.try_revive(player)):
                return False

    for j in reversed(range(len(boss.projectiles))):
        p = boss.projectiles[j]
        r = p.get("r",8)
        pr= Rect(p["x"]-r,p["y"]-r,r*2,r*2)
        if ph.collides(pr):
            dmg = p.get("dmg",3)
            if gs.item_system:
                dmg = gs.item_system.on_player_hit(player, dmg, gs.enemies, gs, now)
            if dmg > 0 and player.take_damage(dmg, now):
                gs.camera_shake = max(gs.camera_shake, 7)
            boss.projectiles.pop(j)
            if not player.is_alive():
                if not (gs.item_system and gs.item_system.try_revive(player)):
                    return False

    if boss.is_dead(): gs.on_boss_killed()
    return True



#  RESOLUTION PHYSIQUE


def _resolve_push(gs):
    """Separation physique : le joueur ne bouge JAMAIS, seuls les ennemis reculent."""
    player = gs.player
    ph     = player.hitbox()
    for e in gs.enemies:
        eh = e.hitbox()
        if not ph.collides(eh): continue
        ox, oy = ph.overlap(eh)
        # On pousse UNIQUEMENT l'ennemi hors du joueur
        if ox < oy:
            d = 1 if eh.center()[0] >= ph.center()[0] else -1
            e.x += d * ox
        else:
            d = 1 if eh.center()[1] >= ph.center()[1] else -1
            e.y += d * oy
        e.clamp()



#  PROJECTILES


def _update_projectiles(gs, spd_f, now):
    player    = gs.player
    to_remove = []

    for i, proj in enumerate(gs.projectiles):
        proj.update(spd_f)
        if not proj.in_bounds(): to_remove.append(i); continue

        ph  = proj.hitbox()
        hit = False
        dead = []

        for j, e in enumerate(gs.enemies):
            eid = id(e)
            if eid in proj.hit_ids: continue
            if ph.collides(e.hitbox()):
                dmg, crit = _calc_dmg(gs, proj.dmg)
                ecx,ecy = e.center()
                ha = math.atan2(proj.vy, proj.vx)
                _hit_enemy(gs, e, dmg, crit, ha, 6)
                proj.hit_ids.add(eid)
                if e.is_dead(): dead.append(j)

                # Chaine foudre
                if proj.chain_left > 0:
                    proj.chain_left -= 1
                    _chain_lightning(gs, e, proj, now)

                if proj.pierce_left > 0:
                    proj.pierce_left -= 1
                else:
                    if proj.explode:
                        _explode(gs, ecx, ecy, dmg//2, proj.color)
                    hit = True; break

        for j in reversed(dead): _kill_enemy(gs, j)

        # Boss
        if not hit and gs.boss:
            bid = id(gs.boss)
            if bid not in proj.hit_ids and ph.collides(gs.boss.hitbox()):
                dmg, crit = _calc_dmg(gs, proj.dmg)
                bcx,bcy = gs.boss.center()
                if hasattr(gs.boss,"take_damage"): gs.boss.take_damage(dmg)
                else: gs.boss.hp -= dmg
                gs.damage_nums.append(DamageNumber(bcx,bcy,dmg,crit))
                if proj.explode: _explode(gs, bcx, bcy, dmg//2, proj.color)
                if gs.boss.is_dead(): gs.on_boss_killed()
                proj.hit_ids.add(bid); hit = True

        if hit: to_remove.append(i)

    for i in reversed(to_remove): gs.projectiles.pop(i)


def _chain_lightning(gs, origin, proj, now):
    """Chaine le projectile sur l'ennemi le plus proche non touche."""
    ocx, ocy = origin.center()
    best, bd = None, float("inf")
    for e in gs.enemies:
        if id(e) in proj.hit_ids: continue
        d = math.hypot(*[a-b for a,b in zip(e.center(),(ocx,ocy))])
        if d < bd: bd=d; best=e
    if best and bd < 250:
        ecx,ecy = best.center()
        dmg, crit = _calc_dmg(gs, proj.dmg)
        ha = math.atan2(ecy-ocy, ecx-ocx)
        _hit_enemy(gs, best, dmg, crit, ha, 3)
        proj.hit_ids.add(id(best))
        # Arc de foudre visuel
        for _ in range(6):
            t = random.random()
            lx = ocx + (ecx-ocx)*t + random.uniform(-15,15)
            ly = ocy + (ecy-ocy)*t + random.uniform(-15,15)
            gs.particles.append(Particle(lx,ly,(180,220,255),
                vx=0,vy=0,life=8,size=2,glow=True))
        if best.is_dead():
            for j,e in enumerate(gs.enemies):
                if e is best: _kill_enemy(gs,j); break


def _explode(gs, cx, cy, dmg, color):
    r   = 55 * gs.player.area_mult
    atk = Rect(cx-r, cy-r, r*2, r*2)
    dead = []
    for i, e in enumerate(gs.enemies):
        if atk.collides(e.hitbox()):
            ha = math.atan2(e.center()[1]-cy, e.center()[0]-cx)
            _hit_enemy(gs, e, max(1,dmg), False, ha, 12)
            if e.is_dead(): dead.append(i)
    for i in reversed(dead): _kill_enemy(gs, i)
    for _ in range(18):
        a = random.uniform(0,math.pi*2)
        gs.particles.append(Particle(cx,cy,color,
            vx=math.cos(a)*random.uniform(2,6),
            vy=math.sin(a)*random.uniform(2,6),
            life=28,size=5,glow=True))


#  PANIERS / FX


def _update_baskets(gs):
    for b in gs.baskets: b.try_heal(gs.player)

def _update_fx(gs):
    gs.particles  = [p for p in gs.particles  if p.update()]
    gs.damage_nums= [d for d in gs.damage_nums if d.update()]
