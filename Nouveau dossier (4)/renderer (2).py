"""renderer.py — Rendu graphique complet style Vampire Survivors."""

import math, random, pygame
from settings import (WIDTH, HEIGHT, MAP_W, MAP_H,
                      C_WHITE, C_GOLD, C_RED, C_GREEN, C_ORANGE,
                      C_GREY, C_HUD_BG, C_XP_BAR, C_DARK, WEAPONS)

_vignette = None

def _make_vignette():
    global _vignette
    if _vignette: return _vignette
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = WIDTH//2, HEIGHT//2
    maxr   = math.hypot(cx, cy)
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            d = math.hypot(x-cx, y-cy)
            a = int(200 * max(0, (d/maxr - 0.40) / 0.60))
            if a > 0:
                pygame.draw.rect(s, (0,0,0,a), (x,y,2,2))
    _vignette = s
    return s



#  POINT D'ENTREE


def draw_game(surf, gs, fonts):
    cam_x, cam_y = gs.get_camera()

    # Sol pre-rendu
    surf.blit(gs.map_data.surface, (0,0), (cam_x, cam_y, WIDTH, HEIGHT))

    # Decors
    _draw_decors(surf, gs.map_data, cam_x, cam_y)
    _draw_baskets(surf, gs.baskets, cam_x, cam_y, fonts["tiny"])

    # Gemmes XP
    if gs.xp_system:
        _draw_gems(surf, gs.xp_system.gems, cam_x, cam_y)

    # Ennemis
    for e in gs.enemies:
        _draw_enemy(surf, e, cam_x, cam_y, fonts["tiny"])
    if gs.boss:
        _draw_boss(surf, gs.boss, cam_x, cam_y, fonts)

    # Joueur
    _draw_player(surf, gs.player, cam_x, cam_y)

    # Effets d'armes en orbite et swing
    _draw_orbit_weapons(surf, gs, cam_x, cam_y)
    _draw_swing_effects(surf, gs, cam_x, cam_y)
    _draw_item_effects(surf, gs, cam_x, cam_y)

    # Projectiles
    _draw_projectiles(surf, gs.projectiles, cam_x, cam_y)

    # Particules (au-dessus de tout)
    for p in gs.particles:
        p.draw(surf, cam_x, cam_y)
    for d in gs.damage_nums:
        d.draw(surf, cam_x, cam_y, fonts["damage"])

    # Vignette
    surf.blit(_make_vignette(), (0,0))

    # Flash rouge (hit)
    if gs.player.hit_flash > 0:
        a = int(90 * gs.player.hit_flash / 10)
        fl = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        fl.fill((200,20,20,a))
        surf.blit(fl,(0,0))

    # HUD
    _draw_hud(surf, gs, fonts)
    _draw_xp_bar(surf, gs, fonts)
    _draw_weapon_slots(surf, gs, fonts)
    _draw_item_hud(surf, gs, fonts)
    _draw_timer(surf, gs, fonts)
    if gs.boss: _draw_boss_bar(surf, gs.boss, fonts)
    _draw_boss_announcement(surf, gs, fonts)


def draw_victory(surf, gs, fonts):
    surf.fill((5,20,5))
    cx, cy = WIDTH//2, HEIGHT//3
    def bc(t,f,c,y):
        s=f.render(t,True,c); surf.blit(s,(cx-s.get_width()//2,y))
    bc("VICTOIRE !",               fonts["title"], C_GOLD,  cy)
    bc("Tu as survecu 10 minutes", fonts["big"],   C_WHITE, cy+72)
    bc(f"Score : {gs.score}",      fonts["big"],   C_GOLD,  cy+110)
    bc("ECHAP → menu",             fonts["small"], C_GREY,  cy+165)

#  JOUEUR  (sprite anime)


def _draw_player(surf, player, cam_x, cam_y):
    px = int(player.x - cam_x)
    py = int(player.y - cam_y)
    cx = px + 16; cy = py + 16
    hit = player.hit_flash > 0

    # Ombre au sol
    pygame.draw.ellipse(surf, (8,5,18), (px+4, py+30, 24, 8))

    # Animation marche (bobbing)
    bob = int(math.sin(player.walk_cycle) * 2)

    # Cape
    cape_col = (180,30,30) if hit else (100,40,180)
    cape_pts = [(cx-10,py+14+bob),(cx+10,py+14+bob),(cx+6,py+34+bob),(cx-6,py+34+bob)]
    pygame.draw.polygon(surf, cape_col, cape_pts)

    # Corps
    body_col = (255,100,100) if hit else (210,210,240)
    pygame.draw.ellipse(surf, body_col, (px+5, py+12+bob, 22, 18))

    # Tete
    head_col = (255,180,180) if hit else (240,200,160)
    pygame.draw.circle(surf, head_col, (cx, py+7+bob), 9)

    # Cheveux
    hair_col = (255,80,80) if hit else (60,30,120)
    pygame.draw.arc(surf, hair_col,
                    (cx-9, py+bob, 18, 16), math.radians(20), math.radians(160), 4)

    # Yeux
    eye_off = 3 * player.facing
    pygame.draw.circle(surf, (20,20,50), (cx+eye_off, py+6+bob), 2)
    pygame.draw.circle(surf, (255,255,200), (cx+eye_off+1, py+5+bob), 1)


#  ARMES EN ORBITE


def _draw_orbit_weapons(surf, gs, cam_x, cam_y):
    player = gs.player
    pcx = int(player.x - cam_x + 16)
    pcy = int(player.y - cam_y + 16)

    for wid in player.weapons:
        w = WEAPONS.get(wid)
        if not w or w["type"] != "melee_orbit": continue

        count  = player.weapon_mods.get(f"{wid}_count",  w.get("orbit_count",2))
        spd_w  = player.weapon_mods.get(f"{wid}_speed",  w.get("orbit_speed",2.0))
        radius = player.weapon_mods.get(f"{wid}_radius", w.get("portee",80))
        radius = int(radius * player.area_mult)
        angle  = player.orbit_angles.get(f"orbit_{wid}", 0.0)
        col    = w["couleur"]
        sz     = w["largeur"]

        for k in range(count):
            a  = angle + k*(math.pi*2/count)
            ox = int(pcx + math.cos(a)*radius)
            oy = int(pcy + math.sin(a)*radius)

            if wid == "bible":
                # Livre lumineux
                glow = pygame.Surface((sz*4,sz*4), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*col,40), (0,0,sz*4,sz*4), border_radius=4)
                pygame.draw.rect(glow, (*col,160),(sz,sz,sz*2,sz*2), border_radius=3)
                surf.blit(glow, (ox-sz*2, oy-sz*2))
                # Croix
                pygame.draw.line(surf, C_WHITE, (ox-sz//2,oy),(ox+sz//2,oy),2)
                pygame.draw.line(surf, C_WHITE, (ox,oy-sz//2),(ox,oy+sz//2),2)

            elif wid == "bouclier":
                # Bouclier hexagonal
                pts = [(int(ox+math.cos(a+i*math.pi/3)*sz),
                        int(oy+math.sin(a+i*math.pi/3)*sz)) for i in range(6)]
                glow_s = pygame.Surface((sz*4,sz*4), pygame.SRCALPHA)
                pygame.draw.polygon(glow_s, (*col,50),
                    [(p[0]-ox+sz*2, p[1]-oy+sz*2) for p in pts])
                surf.blit(glow_s,(ox-sz*2,oy-sz*2))
                pygame.draw.polygon(surf, col, pts, 3)

            # Trainee
            for t in range(5):
                ta = a - t*0.18
                tx = int(pcx + math.cos(ta)*radius)
                ty = int(pcy + math.sin(ta)*radius)
                alpha = int(100*(1-t/5))
                trail = pygame.Surface((6,6), pygame.SRCALPHA)
                pygame.draw.circle(trail, (*col,alpha),(3,3),3)
                surf.blit(trail,(tx-3,ty-3))



#  EFFETS DE SWING

def _draw_bow_ingame(surf, cx, cy, angle, col, now, last_shot, cd):
    """
    Dessine l'arc tenu par le joueur, visant dans la direction de la souris.
    Animation de tension de la corde quand l'arc se recharge.
    """
    # Cooldown progress 0→1 (1 = pret a tirer)
    ready = min(1.0, (now - last_shot) / max(1, cd))

    # L'arc est perpendiculaire a la direction de tir
    perp  = angle + math.pi / 2
    # Distance du joueur
    dist  = 22

    # Centre de l'arc
    ax = cx + math.cos(angle) * dist
    ay = cy + math.sin(angle) * dist

    bow_half = 16   # demi-hauteur de l'arc

    # Extremites du bois
    top_x = int(ax + math.cos(perp) * bow_half)
    top_y = int(ay + math.sin(perp) * bow_half)
    bot_x = int(ax - math.cos(perp) * bow_half)
    bot_y = int(ay - math.sin(perp) * bow_half)

    # Bois de l'arc (deux segments courbes simulés)
    mid_top_x = int(ax + math.cos(perp)*bow_half*0.5 - math.cos(angle)*5)
    mid_top_y = int(ay + math.sin(perp)*bow_half*0.5 - math.sin(angle)*5)
    mid_bot_x = int(ax - math.cos(perp)*bow_half*0.5 - math.cos(angle)*5)
    mid_bot_y = int(ay - math.sin(perp)*bow_half*0.5 - math.sin(angle)*5)

    wood_col = (139, 90, 43)
    pygame.draw.line(surf, wood_col, (top_x, top_y), (mid_top_x, mid_top_y), 3)
    pygame.draw.line(surf, wood_col, (mid_top_x, mid_top_y), (int(ax), int(ay)), 3)
    pygame.draw.line(surf, wood_col, (bot_x, bot_y), (mid_bot_x, mid_bot_y), 3)
    pygame.draw.line(surf, wood_col, (mid_bot_x, mid_bot_y), (int(ax), int(ay)), 3)

    # Corde tendue : plus tirée en arrière si rechargée
    pull = ready * 8   # tension max 8px vers l'arriere
    str_x = int(ax - math.cos(angle) * pull)
    str_y = int(ay - math.sin(angle) * pull)
    str_col = (230, 210, 160)
    pygame.draw.line(surf, str_col, (top_x, top_y), (str_x, str_y), 1)
    pygame.draw.line(surf, str_col, (bot_x, bot_y), (str_x, str_y), 1)

    # Fleche sur la corde (visible uniquement quand pret)
    if ready > 0.3:
        arrow_alpha = int(255 * min(1.0, (ready-0.3)/0.7))
        arr_tip_x = int(ax + math.cos(angle) * 14)
        arr_tip_y = int(ay + math.sin(angle) * 14)
        # Corps
        arr_surf = pygame.Surface((40, 8), pygame.SRCALPHA)
        arr_len  = int(20 * ready)
        shaft_s  = pygame.Surface((arr_len+10, 4), pygame.SRCALPHA)
        pygame.draw.line(shaft_s, (160,110,50,arrow_alpha), (0,2), (arr_len,2), 2)
        surf.blit(shaft_s, (str_x, str_y-2))
        # Pointe
        perp2 = angle + math.pi/2
        pt1 = arr_tip_x, arr_tip_y
        pt2 = (int(arr_tip_x-math.cos(angle)*6+math.cos(perp2)*3),
               int(arr_tip_y-math.sin(angle)*6+math.sin(perp2)*3))
        pt3 = (int(arr_tip_x-math.cos(angle)*6-math.cos(perp2)*3),
               int(arr_tip_y-math.sin(angle)*6-math.sin(perp2)*3))
        pts_surf = pygame.Surface((20,20), pygame.SRCALPHA)
        tri = [(p[0]-arr_tip_x+10, p[1]-arr_tip_y+10) for p in [pt1,pt2,pt3]]
        pygame.draw.polygon(pts_surf, (*col, arrow_alpha), tri)
        surf.blit(pts_surf, (arr_tip_x-10, arr_tip_y-10))

        # Glow si pret a tirer
        if ready >= 0.95:
            glow = pygame.Surface((20,20), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*col, 100), (10,10), 10)
            surf.blit(glow, (str_x-10, str_y-10))


def _draw_swing_effects(surf, gs, cam_x, cam_y):
    player = gs.player
    now    = pygame.time.get_ticks()
    pcx    = int(player.x - cam_x + 16)
    pcy    = int(player.y - cam_y + 16)

    # Calcule l'angle souris UNE FOIS (meme logique que physics._swing)
    mx, my   = pygame.mouse.get_pos()
    mouse_wx = mx + cam_x
    mouse_wy = my + cam_y
    dx = mouse_wx - (player.x + 16)
    dy = mouse_wy - (player.y + 16)
    mouse_angle = math.atan2(dy, dx) if (abs(dx)>5 or abs(dy)>5) else 0.0

    for wid in player.weapons:
        w = WEAPONS.get(wid)
        if not w or w["type"] not in ("melee_swing","whip","melee_area","projectile"): continue
        last = player.weapon_timers.get(wid, 0)
        age  = now - last
        cd   = max(80, int(w.get("cooldown",500) * player.atk_speed_mult))

        # L'arc est toujours visible (pas de swing_dur)
        if w["type"] == "projectile" and wid == "arc":
            _draw_bow_ingame(surf, pcx, pcy, mouse_angle, w["couleur"], now, last, cd)
            continue

        if age > w.get("swing_dur", 200): continue
        prog = age / max(1, w.get("swing_dur", 200))

        col   = w["couleur"]
        alpha = int(200*(1-prog))

        if w["type"] == "melee_swing":
            angle  = mouse_angle
            spread = 0.75
            reach  = int(w["portee"] * player.area_mult)
            swing  = math.sin(prog*math.pi) * spread

            for i in range(14):
                t  = i / 13
                a  = angle - spread + t*2*spread + swing*0.4
                x1 = int(pcx + math.cos(a)*10)
                y1 = int(pcy + math.sin(a)*10)
                x2 = int(pcx + math.cos(a)*reach)
                y2 = int(pcy + math.sin(a)*reach)
                line_a = int(alpha*(1 - t*0.3))
                width  = max(1, int(5*(1-prog)))
                if line_a > 10:
                    pygame.draw.line(surf, (*col, line_a), (x1,y1), (x2,y2), width)

            # Bout lumineux
            tip_x = int(pcx + math.cos(angle)*reach)
            tip_y = int(pcy + math.sin(angle)*reach)
            if alpha > 30:
                glow = pygame.Surface((20,20), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*col, alpha//2), (10,10), 10)
                surf.blit(glow, (tip_x-10, tip_y-10))

        elif w["type"] == "whip":
            angle = mouse_angle
            reach = int(w["portee"]*player.area_mult +
                        player.weapon_mods.get("fouet_range",0))
            # Dessine le fouet dans la direction de la souris
            for side in (-1, 1):
                perp = angle + math.pi/2
                mid_x = int(pcx + math.cos(angle)*reach//2 + math.cos(perp)*side*12*math.sin(prog*math.pi))
                mid_y = int(pcy + math.sin(angle)*reach//2 + math.sin(perp)*side*12*math.sin(prog*math.pi))
                end_x = int(pcx + math.cos(angle)*reach)
                end_y = int(pcy + math.sin(angle)*reach)
                pts = [(pcx,pcy),(mid_x,mid_y),(end_x,end_y)]
                if alpha > 10:
                    pygame.draw.lines(surf, (*col,alpha), False, pts, max(1,int(4*(1-prog))))

        elif w["type"] == "melee_area":
            r = int(w["portee"]*player.area_mult*max(0.1, math.sin(prog*math.pi)))
            if r > 2:
                area_s = pygame.Surface((r*2+4,r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(area_s, (*col,int(alpha*0.35)), (r+2,r+2), r)
                pygame.draw.circle(area_s, (*col,alpha),           (r+2,r+2), r, 2)
                surf.blit(area_s, (pcx-r-2, pcy-r-2))



#  ENNEMIS


def _draw_enemy(surf, enemy, cam_x, cam_y, font_tiny):
    s  = enemy.SIZE
    ex = int(enemy.x - cam_x)
    ey = int(enemy.y - cam_y)
    if not (-s-10 <= ex <= WIDTH+s+10 and -s-10 <= ey <= HEIGHT+s+10): return

    col = (255,255,255) if enemy.flash > 0 else enemy.COLOR
    out = enemy.OUTLINE

    # Ombre
    pygame.draw.ellipse(surf,(8,5,18),(ex+s//6, ey+s-4, s*2//3, 10))

    # Corps
    pygame.draw.ellipse(surf, col,  (ex, ey, s, s))
    pygame.draw.ellipse(surf, out,  (ex, ey, s, s), 2)

    # Yeux (en fonction de la direction vers le joueur)
    ecx = ex+s//2; ecy = ey+s//3
    pygame.draw.circle(surf, (20,10,30),(ecx-s//6, ecy), max(2,s//8))
    pygame.draw.circle(surf, (20,10,30),(ecx+s//6, ecy), max(2,s//8))
    pygame.draw.circle(surf, (255,200,50),(ecx-s//6+1,ecy-1),max(1,s//14))
    pygame.draw.circle(surf, (255,200,50),(ecx+s//6+1,ecy-1),max(1,s//14))

    # Barre de vie
    ratio = max(0, enemy.hp/enemy.HP)
    bw=s; bh=4
    pygame.draw.rect(surf,(40,10,10),(ex,ey-10,bw,bh))
    bar_col = C_GREEN if ratio>0.5 else C_ORANGE if ratio>0.25 else C_RED
    if ratio > 0:
        pygame.draw.rect(surf,bar_col,(ex,ey-10,max(1,int(bw*ratio)),bh))

    # Dot bleed (teinte rouge)
    now = pygame.time.get_ticks()
    if enemy.bleed_end > now:
        bl = pygame.Surface((s,s),pygame.SRCALPHA)
        pygame.draw.ellipse(bl,(200,0,0,60),(0,0,s,s))
        surf.blit(bl,(ex,ey))
    if enemy.poison_end > now:
        po = pygame.Surface((s,s),pygame.SRCALPHA)
        pygame.draw.ellipse(po,(0,180,0,60),(0,0,s,s))
        surf.blit(po,(ex,ey))

    # Projectiles des ranged
    for p in enemy.projectiles:
        px2=int(p["x"]-cam_x); py2=int(p["y"]-cam_y)
        r=p.get("r",7)
        if -r-2<=px2<=WIDTH+r+2 and -r-2<=py2<=HEIGHT+r+2:
            glow=pygame.Surface((r*4,r*4),pygame.SRCALPHA)
            pygame.draw.circle(glow,(160,60,220,50),(r*2,r*2),r*2)
            pygame.draw.circle(glow,(200,100,255,200),(r*2,r*2),r)
            surf.blit(glow,(px2-r*2,py2-r*2))



#  BOSS


def _draw_boss(surf, boss, cam_x, cam_y, fonts):
    sz = boss.SIZE
    bx = int(boss.x-cam_x); by=int(boss.y-cam_y)
    if not(-sz<=bx<=WIDTH+sz and -sz<=by<=HEIGHT+sz): return

    col  = boss.COLOR
    dark = tuple(max(0,c-60) for c in col)
    now  = pygame.time.get_ticks()

    # Aura pulsante
    pulse = int(18 + math.sin(now/200)*8)
    aura  = pygame.Surface((sz+pulse*2,sz+pulse*2),pygame.SRCALPHA)
    pygame.draw.ellipse(aura,(*col,40),(0,0,sz+pulse*2,sz+pulse*2))
    surf.blit(aura,(bx-pulse,by-pulse))

    # Ombre
    pygame.draw.ellipse(surf,(8,5,18),(bx+sz//8,by+sz-8,sz*3//4,16))

    # Corps
    pygame.draw.ellipse(surf,col,(bx,by,sz,sz))
    pygame.draw.ellipse(surf,dark,(bx,by,sz,sz),4)

    # Couronne
    bcx=bx+sz//2
    pts=[(bcx-sz//2,by),(bcx-sz//3,by-22),(bcx-sz//6,by-10),
         (bcx,by-26),(bcx+sz//6,by-10),(bcx+sz//3,by-22),(bcx+sz//2,by)]
    pygame.draw.polygon(surf,C_GOLD,pts)
    pygame.draw.polygon(surf,(200,160,0),pts,2)

    # Yeux rouges
    pygame.draw.circle(surf,(255,50,50),(bx+sz//3,by+sz//3),sz//8)
    pygame.draw.circle(surf,(255,50,50),(bx+sz*2//3,by+sz//3),sz//8)
    pygame.draw.circle(surf,(255,200,0),(bx+sz//3+2,by+sz//3-2),sz//16)
    pygame.draw.circle(surf,(255,200,0),(bx+sz*2//3+2,by+sz//3-2),sz//16)

    # Nom
    from bosses import BossMage
    if isinstance(boss,BossMage) and boss._shield_active:
        shield_s = pygame.Surface((sz+50,sz+50),pygame.SRCALPHA)
        pygame.draw.ellipse(shield_s,(80,80,255,80),(0,0,sz+50,sz+50))
        pygame.draw.ellipse(shield_s,(120,120,255,200),(0,0,sz+50,sz+50),3)
        surf.blit(shield_s,(bx-25,by-25))

    nm=fonts["small"].render(boss.NAME,True,C_WHITE)
    surf.blit(nm,(bx+sz//2-nm.get_width()//2,by-38))

    # Projectiles
    for p in boss.projectiles:
        px2=int(p["x"]-cam_x); py2=int(p["y"]-cam_y)
        r=p.get("r",8)
        if -r-2<=px2<=WIDTH+r+2 and -r-2<=py2<=HEIGHT+r+2:
            glow=pygame.Surface((r*4,r*4),pygame.SRCALPHA)
            pygame.draw.circle(glow,(220,50,50,60),(r*2,r*2),r*2)
            pygame.draw.circle(glow,(255,80,80,220),(r*2,r*2),r)
            pygame.draw.circle(glow,(255,200,200,240),(r*2,r*2),max(1,r//2))
            surf.blit(glow,(px2-r*2,py2-r*2))


def _draw_boss_bar(surf, boss, fonts):
    bw=WIDTH-120; bh=24; hx=60; hy=HEIGHT-54
    ratio=max(0,boss.hp/boss.MAX_HP)
    hp_col=C_GREEN if ratio>0.6 else C_ORANGE if ratio>0.3 else C_RED
    # Fond
    pygame.draw.rect(surf,(20,5,5),(hx-2,hy-2,bw+4,bh+4),border_radius=4)
    pygame.draw.rect(surf,(50,15,15),(hx,hy,bw,bh),border_radius=3)
    # Remplissage
    if ratio>0:
        pygame.draw.rect(surf,hp_col,(hx,hy,max(1,int(bw*ratio)),bh),border_radius=3)
    pygame.draw.rect(surf,C_WHITE,(hx,hy,bw,bh),2,border_radius=3)
    # Texte
    lbl=fonts["med"].render(f"⚡ {boss.NAME}   {max(0,boss.hp)} / {boss.MAX_HP}",True,C_WHITE)
    surf.blit(lbl,(hx+bw//2-lbl.get_width()//2,hy-22))



#  PROJECTILES JOUEUR


def _draw_projectiles(surf, projectiles, cam_x, cam_y):
    for proj in projectiles:
        px = int(proj.x - cam_x)
        py = int(proj.y - cam_y)
        r  = proj.r
        if not (-r-20 <= px <= WIDTH+r+20 and -r-20 <= py <= HEIGHT+r+20):
            continue
        col   = proj.color
        angle = proj.angle

        # Detecte si c'est une fleche (couleur bois/or) ou un orbe magique
        is_arrow = col in ((210,210,255),(200,160,60)) or (
            col[0] > 150 and 80 < col[1] < 180 and col[2] < 100)

        if is_arrow:
            _draw_arrow_projectile(surf, px, py, angle, r, col)
        else:
            _draw_orb_projectile(surf, px, py, angle, r, col)


def _draw_arrow_projectile(surf, px, py, angle, r, col):
    """Fleche avec empennage, pointe et trainee."""
    length = max(14, r * 3)

    # Trainee lumineuse derriere la fleche
    for t in range(1, 7):
        frac  = t / 7
        tx    = int(px - math.cos(angle) * t * length * 0.28)
        ty    = int(py - math.sin(angle) * t * length * 0.28)
        alpha = int(140 * (1 - frac))
        w_t   = max(1, int((r * 0.6) * (1 - frac)))
        trail = pygame.Surface((w_t*2+2, w_t*2+2), pygame.SRCALPHA)
        pygame.draw.circle(trail, (*col, alpha), (w_t+1, w_t+1), w_t)
        surf.blit(trail, (tx - w_t - 1, ty - w_t - 1))

    # Corps de la fleche (ligne epaisse)
    tip_x  = int(px + math.cos(angle) * length * 0.5)
    tip_y  = int(py + math.sin(angle) * length * 0.5)
    tail_x = int(px - math.cos(angle) * length * 0.5)
    tail_y = int(py - math.sin(angle) * length * 0.5)

    # Ombre portee
    pygame.draw.line(surf, (20, 15, 30),
                     (tail_x+2, tail_y+2), (tip_x+2, tip_y+2), max(1, r-1))
    # Corps bois
    shaft_col = (160, 110, 50)
    pygame.draw.line(surf, shaft_col, (tail_x, tail_y), (tip_x, tip_y), max(1, r))

    # Pointe metallique (triangle)
    perp = angle + math.pi/2
    pt1  = tip_x, tip_y
    pt2  = (int(tip_x - math.cos(angle)*r*2.2 + math.cos(perp)*r*0.9),
            int(tip_y - math.sin(angle)*r*2.2 + math.sin(perp)*r*0.9))
    pt3  = (int(tip_x - math.cos(angle)*r*2.2 - math.cos(perp)*r*0.9),
            int(tip_y - math.sin(angle)*r*2.2 - math.sin(perp)*r*0.9))
    pygame.draw.polygon(surf, col,           [pt1, pt2, pt3])
    pygame.draw.polygon(surf, (255,255,255), [pt1, pt2, pt3], 1)

    # Empennage (plumes au bout)
    perp2 = angle + math.pi/2
    for side in (1, -1):
        fx1 = int(tail_x + math.cos(perp2)*side*r*1.6)
        fy1 = int(tail_y + math.sin(perp2)*side*r*1.6)
        fx2 = int(tail_x - math.cos(angle)*r*1.5)
        fy2 = int(tail_y - math.sin(angle)*r*1.5)
        feather_col = (220, 80, 80) if col[0] > 150 else (100, 180, 100)
        pygame.draw.line(surf, feather_col, (tail_x, tail_y), (fx1, fy1), max(1,r-1))
        pygame.draw.line(surf, feather_col, (tail_x, tail_y), (fx2, fy2), max(1,r-1))

    # Reflet sur la pointe
    glow = pygame.Surface((r*3, r*3), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*col, 120), (r*3//2, r*3//2), r)
    surf.blit(glow, (tip_x - r*3//2, tip_y - r*3//2))


def _draw_orb_projectile(surf, px, py, angle, r, col):
    """Orbe magique avec glow, noyau lumineux et trainee."""
    # Glow externe large
    glow_r = r * 2 + 4
    glow   = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*col, 35), (glow_r, glow_r), glow_r)
    pygame.draw.circle(glow, (*col, 90), (glow_r, glow_r), r+2)
    surf.blit(glow, (px - glow_r, py - glow_r))

    # Corps de l'orbe
    pygame.draw.circle(surf, col, (px, py), r)

    # Noyau blanc brillant
    pygame.draw.circle(surf, (255, 255, 255), (px - r//3, py - r//3), max(1, r//3))

    # Trainee
    for t in range(1, 7):
        frac  = t / 7
        tx    = int(px - math.cos(angle) * t * r * 1.2)
        ty    = int(py - math.sin(angle) * t * r * 1.2)
        alpha = int(160 * (1 - frac))
        tr_r  = max(1, int(r * (1 - frac * 0.7)))
        trail = pygame.Surface((tr_r*2+2, tr_r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(trail, (*col, alpha), (tr_r+1, tr_r+1), tr_r)
        surf.blit(trail, (tx - tr_r - 1, ty - tr_r - 1))



#  GEMMES XP


def _draw_gems(surf, gems, cam_x, cam_y):
    now = pygame.time.get_ticks()/1000.0
    for gem in gems:
        sx=int(gem.x-cam_x); sy=int(gem.y-cam_y)
        if not(-15<=sx<=WIDTH+15 and -15<=sy<=HEIGHT+15): continue
        bob=math.sin(now*4+gem.bob_offset)*3
        sy2=int(sy+bob); r=gem.radius; col=gem.color
        # Glow
        glow=pygame.Surface((r*5,r*5),pygame.SRCALPHA)
        pygame.draw.circle(glow,(*col,40),(r*5//2,r*5//2),r*2)
        surf.blit(glow,(sx-r*5//2,sy2-r*5//2))
        # Losange
        pts=[(sx,sy2-r),(sx+r,sy2),(sx,sy2+r),(sx-r,sy2)]
        pygame.draw.polygon(surf,col,pts)
        bright=tuple(min(255,c+90) for c in col)
        pygame.draw.polygon(surf,bright,[(sx,sy2-r),(sx+r//2,sy2-r//3),(sx,sy2)])
        # Ombre
        pygame.draw.ellipse(surf,(8,5,18),(sx-r,sy2+r-1,r*2,r))



#  DECORS


def _draw_decors(surf, md, cam_x, cam_y):
    # Clotures
    for (x1,y1,x2,y2) in md.fences:
        sx1,sy1=x1-cam_x,y1-cam_y; sx2,sy2=x2-cam_x,y2-cam_y
        if not(-20<=sx1<=WIDTH+20 and -20<=sy1<=HEIGHT+20): continue
        pygame.draw.rect(surf,(90,65,20),(sx1-3,sy1-3,6,18))
        pygame.draw.rect(surf,(90,65,20),(sx2-3,sy2-3,6,18))
        pygame.draw.line(surf,(120,88,35),(sx1,sy1+6),(sx2,sy2+6),3)
        pygame.draw.line(surf,(120,88,35),(sx1,sy1+12),(sx2,sy2+12),2)
    # Buissons
    for (cx,cy,r,col) in md.bushes:
        sx,sy=cx-cam_x,cy-cam_y
        if not(-r<=sx<=WIDTH+r and -r<=sy<=HEIGHT+r): continue
        dark=tuple(max(0,c-50) for c in col)
        pygame.draw.ellipse(surf,dark,(sx-r,sy-r//2,r*2,r+r//2))
        pygame.draw.ellipse(surf,col,(sx-r+3,sy-r,(r-3)*2,r+r//2))
        lite=tuple(min(255,c+40) for c in col)
        pygame.draw.ellipse(surf,lite,(sx-r//3,sy-r,r//2,r//3))
    # Rochers
    for (cx,cy,rx,ry,col) in md.rocks:
        sx,sy=cx-cam_x,cy-cam_y
        if not(-rx<=sx<=WIDTH+rx and -ry<=sy<=HEIGHT+ry): continue
        pygame.draw.ellipse(surf,(15,10,28),(sx-rx+3,sy-ry+5,rx*2,ry*2))
        pygame.draw.ellipse(surf,col,(sx-rx,sy-ry,rx*2,ry*2))
        pygame.draw.ellipse(surf,tuple(min(255,c+60) for c in col),(sx-rx//2,sy-ry//2,rx//2,ry//2))
    # Arbres
    for (cx,cy,rt,rf,col) in md.trees:
        sx,sy=cx-cam_x,cy-cam_y
        if not(-rf<=sx<=WIDTH+rf and -rf<=sy<=HEIGHT+rf): continue
        shadow=tuple(max(0,c-70) for c in col)
        dark=tuple(max(0,c-30) for c in col)
        lite=tuple(min(255,c+50) for c in col)
        pygame.draw.ellipse(surf,shadow,(sx-rf//2,sy+rt,rf,12))
        pygame.draw.rect(surf,(70,40,22),(sx-rt,sy-rt,rt*2,rt+10))
        pygame.draw.ellipse(surf,dark,(sx-rf,sy-rf,rf*2,rf+rf//2))
        pygame.draw.ellipse(surf,col,(sx-rf+4,sy-rf-5,(rf-4)*2,rf+rf//2-4))
        pygame.draw.ellipse(surf,lite,(sx-rf//3,sy-rf-4,rf//2,rf//3))


def _draw_baskets(surf, baskets, cam_x, cam_y, font_tiny):
    from settings import BASKET_W, BASKET_H, BASKET_HEAL
    for b in baskets:
        if not b.active: continue
        sx,sy=b.x-cam_x,b.y-cam_y
        if not(-40<=sx<=WIDTH+40 and -40<=sy<=HEIGHT+40): continue
        bx,by=int(sx)-BASKET_W//2,int(sy)-BASKET_H//2
        by2=by+BASKET_H//3; bh2=BASKET_H*2//3
        pygame.draw.rect(surf,(150,110,45),(bx,by2,BASKET_W,bh2))
        pygame.draw.ellipse(surf,(150,110,45),(bx,by2-4,BASKET_W,10))
        pygame.draw.rect(surf,(90,60,18),(bx,by2,BASKET_W,bh2),2)
        pygame.draw.arc(surf,(90,60,18),(bx+4,by-4,BASKET_W-8,BASKET_H//2+4),0,math.pi,2)
        pygame.draw.circle(surf,(210,45,45),(bx+8,by+6),5)
        pygame.draw.circle(surf,(210,190,0),(bx+15,by+4),5)
        pygame.draw.circle(surf,(210,95,18),(bx+22,by+6),4)
        lbl=font_tiny.render(f"+{BASKET_HEAL}PV",True,(60,255,100))
        surf.blit(lbl,(bx+BASKET_W//2-lbl.get_width()//2,by-14))



#  HUD STYLE VS


def _draw_hud(surf, gs, fonts):
    player=gs.player
    # Panneau semi-transparent
    panel=pygame.Surface((195,70),pygame.SRCALPHA)
    panel.fill((8,5,15,210))
    surf.blit(panel,(0,0))
    pygame.draw.rect(surf,(50,35,80),(0,0,195,70),1,border_radius=3)

    # Barre HP
    ratio=max(0.0,player.hp/player.max_hp)
    hp_col=C_GREEN if ratio>0.5 else C_ORANGE if ratio>0.25 else C_RED
    pygame.draw.rect(surf,(40,10,10),(10,10,175,14),border_radius=3)
    if ratio>0: pygame.draw.rect(surf,hp_col,(10,10,max(1,int(175*ratio)),14),border_radius=3)
    pygame.draw.rect(surf,C_WHITE,(10,10,175,14),1,border_radius=3)
    hp_lbl=fonts["small"].render(f"♥  {int(player.hp)} / {int(player.max_hp)}",True,C_WHITE)
    surf.blit(hp_lbl,(12,11))

    surf.blit(fonts["small"].render(f"Score : {gs.score}",True,C_WHITE),(10,32))
    surf.blit(fonts["small"].render(f"Or : {gs.gold}",True,C_GOLD),(10,50))


def _draw_xp_bar(surf, gs, fonts):
    if not gs.xp_system: return
    xp_cur,xp_nxt=gs.xp_system.progress()
    ratio=xp_cur/xp_nxt if xp_nxt else 0
    bh=16; by=HEIGHT-bh
    # Fond
    pygame.draw.rect(surf,(8,5,25),(0,by,WIDTH,bh))
    # Remplissage
    if ratio>0:
        pygame.draw.rect(surf,C_XP_BAR,(0,by,int(WIDTH*ratio),bh))
        # Reflet
        refl=pygame.Surface((int(WIDTH*ratio),bh//2),pygame.SRCALPHA)
        refl.fill((255,255,255,30))
        surf.blit(refl,(0,by))
    pygame.draw.rect(surf,(40,30,80),(0,by,WIDTH,bh),1)
    lbl=fonts["small"].render(
        f"Niveau {gs.xp_system.level}   ·   {xp_cur} / {xp_nxt} XP",True,C_WHITE)
    surf.blit(lbl,(WIDTH//2-lbl.get_width()//2,by+2))


def _draw_weapon_slots(surf, gs, fonts):
    player=gs.player
    sz=48; gap=6; sx=10; sy=HEIGHT-16-sz-2
    for i,wid in enumerate(player.weapons[:6]):
        w=WEAPONS.get(wid,{}); col=w.get("couleur",(120,120,140))
        bx=sx+i*(sz+gap)
        # Fond
        bg=pygame.Surface((sz,sz),pygame.SRCALPHA)
        bg.fill((12,8,25,200))
        surf.blit(bg,(bx,sy))
        pygame.draw.rect(surf,col,(bx,sy,sz,sz),2,border_radius=4)
        # Icone arme
        draw_weapon_icon(surf,wid,bx+sz//2,sy+sz//2-4,col)
        # Niveau
        lvl=player.weapon_levels.get(wid,0)
        for star in range(min(lvl+1,5)):
            sx2=bx+4+star*8; sy2=sy+sz-10
            pygame.draw.circle(surf,C_GOLD,(sx2,sy2),3)


def _draw_timer(surf, gs, fonts):
    wm=gs.wave_manager
    # Timer central
    t_str=wm.time_str()
    ts=fonts["timer"].render(t_str,True,C_WHITE)
    # Fond
    tbg=pygame.Surface((ts.get_width()+20,ts.get_height()+6),pygame.SRCALPHA)
    tbg.fill((8,5,15,180))
    surf.blit(tbg,(WIDTH//2-ts.get_width()//2-10,4))
    surf.blit(ts,(WIDTH//2-ts.get_width()//2,6))

    # Avertissement boss
    nb=wm.next_boss_in()
    if 0<nb<45:
        blink=int(pygame.time.get_ticks()/400)%2==0
        if blink:
            warn=fonts["small"].render(f"⚠  BOSS dans {int(nb)}s  ⚠",True,C_RED)
            surf.blit(warn,(WIDTH//2-warn.get_width()//2,46))

    # Ennemis
    en_lbl=fonts["tiny"].render(f"Ennemis : {len(gs.enemies)}",True,(120,120,140))
    surf.blit(en_lbl,(WIDTH-en_lbl.get_width()-8,8))


def _draw_boss_announcement(surf, gs, fonts):
    if not gs.boss_announcement: return
    ts,name=gs.boss_announcement
    el=pygame.time.get_ticks()-ts
    if el>3800: gs.boss_announcement=None; return
    # Fond
    alpha=min(255,int(255*min(1,(3800-el)/800)))
    panel=pygame.Surface((WIDTH,90),pygame.SRCALPHA)
    panel.fill((80,5,5,int(alpha*0.7)))
    surf.blit(panel,(0,HEIGHT//2-45))
    # Texte
    s=fonts["title"].render(f"⚠   {name}   ⚠",True,(255,60,60))
    s.set_alpha(alpha)
    surf.blit(s,(WIDTH//2-s.get_width()//2,HEIGHT//2-s.get_height()//2))



#  ICONE ARME  (pour les slots et le menu)


def _draw_item_effects(surf, gs, cam_x, cam_y):
    """Dessine les effets visuels des items actifs."""
    if not gs.item_system: return
    its  = gs.item_system
    now  = pygame.time.get_ticks()
    pcx  = int(gs.player.x - cam_x + 16)
    pcy  = int(gs.player.y - cam_y + 16)

    # Cercle d'ombre
    if its.has("cercle_ombre"):
        from items import ITEM_DEFS
        r = ITEM_DEFS["cercle_ombre"]["radius"][its.level("cercle_ombre")]
        r = int(r * gs.player.area_mult)
        pulse = math.sin(now/300) * 6
        aura_s = pygame.Surface((r*2+20, r*2+20), pygame.SRCALPHA)
        pygame.draw.circle(aura_s,(80,0,160,25),(r+10,r+10),r+int(pulse))
        pygame.draw.circle(aura_s,(120,40,220,80),(r+10,r+10),r,2)
        surf.blit(aura_s,(pcx-r-10,pcy-r-10))

    # Boule de feu
    if its.fireball_active:
        from items import ITEM_DEFS
        r     = ITEM_DEFS["boule_feu"]["orbit_r"]
        angle = its.fireball_angle
        fx    = int(pcx + math.cos(angle)*r)
        fy    = int(pcy + math.sin(angle)*r)
        for t in range(8):
            ta = angle - t*0.2
            tx = int(pcx+math.cos(ta)*r); ty = int(pcy+math.sin(ta)*r)
            a  = int(180*(1-t/8))
            fs = pygame.Surface((12,12),pygame.SRCALPHA)
            pygame.draw.circle(fs,(255,120,20,a),(6,6),max(1,6-t//2))
            surf.blit(fs,(tx-6,ty-6))
        glow = pygame.Surface((32,32),pygame.SRCALPHA)
        pygame.draw.circle(glow,(255,80,0,60),(16,16),16)
        pygame.draw.circle(glow,(255,140,40,200),(16,16),9)
        pygame.draw.circle(glow,(255,220,120,240),(16,16),4)
        surf.blit(glow,(fx-16,fy-16))

    # Phaseur actif
    if now < its.invincible_end and int(now/120)%2==0:
        inv_s = pygame.Surface((40,40),pygame.SRCALPHA)
        pygame.draw.ellipse(inv_s,(100,180,255,80),(0,0,40,40))
        pygame.draw.ellipse(inv_s,(200,230,255,200),(0,0,40,40),2)
        surf.blit(inv_s,(pcx-20,pcy-20))

    # Boost vitesse — trainee
    if now < its.speed_boost_end:
        for t in range(4):
            ts = pygame.Surface((8,8),pygame.SRCALPHA)
            pygame.draw.circle(ts,(200,50,50,int(120*(1-t/4))),(4,4),4)
            surf.blit(ts,(pcx-4+t*2,pcy+12+t*3))


def _draw_item_hud(surf, gs, fonts):
    """Affiche les items equipes en bas a droite."""
    if not gs.item_system: return
    its   = gs.item_system
    items = list(its.equipped.items())
    if not items: return
    from items import ITEM_DEFS
    sz = 32; gap = 4
    sx = WIDTH - (sz+gap)*min(len(items),8) - 8
    sy = HEIGHT - 14 - sz - 58
    for i,(item_id,lvl) in enumerate(items[:8]):
        defn = ITEM_DEFS.get(item_id,{})
        col  = defn.get("color",(100,100,100))
        icon = defn.get("icon","?")
        bx   = sx + i*(sz+gap)
        bg = pygame.Surface((sz,sz),pygame.SRCALPHA)
        bg.fill((10,6,22,200)); surf.blit(bg,(bx,sy))
        pygame.draw.rect(surf,col,(bx,sy,sz,sz),1,border_radius=3)
        ic = fonts["small"].render(icon,True,col)
        surf.blit(ic,(bx+sz//2-ic.get_width()//2,sy+4))
        lv = fonts["tiny"].render(f"{lvl+1}",True,C_GOLD)
        surf.blit(lv,(bx+sz-lv.get_width()-2,sy+sz-12))


def draw_weapon_icon(surf, wid, cx, cy, col):
    if wid=="epee":
        pygame.draw.line(surf,col,(cx,cy+14),(cx,cy-14),4)
        pygame.draw.line(surf,(160,160,180),(cx-8,cy+4),(cx+8,cy+4),3)
        pygame.draw.polygon(surf,col,[(cx,cy-14),(cx-3,cy-10),(cx+3,cy-10)])
    elif wid=="faux":
        pygame.draw.line(surf,(100,70,30),(cx+10,cy+12),(cx-6,cy-12),3)
        pygame.draw.arc(surf,col,(cx-14,cy-14,20,20),math.radians(0),math.radians(200),4)
    elif wid=="fouet":
        pts=[(cx-14,cy),(cx-4,cy-8),(cx+4,cy+8),(cx+14,cy)]
        pygame.draw.lines(surf,col,False,pts,3)
    elif wid=="ail":
        for i in range(5):
            a=i*math.pi*2/5
            pygame.draw.circle(surf,col,(int(cx+math.cos(a)*7),int(cy+math.sin(a)*7)),4)
        pygame.draw.circle(surf,col,(cx,cy),3)
    elif wid=="marteau":
        pygame.draw.rect(surf,col,(cx-8,cy-10,16,10),border_radius=2)
        pygame.draw.line(surf,(120,90,60),(cx,cy),(cx,cy+12),3)
    elif wid=="bible":
        pygame.draw.rect(surf,col,(cx-6,cy-8,12,10),border_radius=2)
        pygame.draw.line(surf,C_WHITE,(cx-4,cy-4),(cx+4,cy-4),1)
        pygame.draw.line(surf,C_WHITE,(cx,cy-8),(cx,cy+2),1)
    elif wid=="bouclier":
        pts=[(cx,cy-12),(cx+10,cy-4),(cx+8,cy+10),(cx-8,cy+10),(cx-10,cy-4)]
        pygame.draw.polygon(surf,col,pts,3)
    elif wid=="couteau":
        pygame.draw.line(surf,col,(cx,cy+10),(cx,cy-10),3)
        pygame.draw.polygon(surf,col,[(cx,cy-10),(cx-3,cy-5),(cx+3,cy-5)])
        pygame.draw.line(surf,(140,140,160),(cx-4,cy+6),(cx+4,cy+6),2)
    elif wid=="arc":
        # Arc en bois (courbe epaisse)
        pygame.draw.arc(surf, (139,90,43), (cx-13,cy-14,26,28),
                        math.radians(50), math.radians(310), 4)
        # Corde
        pygame.draw.line(surf, (220,200,150), (cx-3,cy-13),(cx-3,cy+13), 1)
        # Fleche sur l'arc
        pygame.draw.line(surf, (160,110,50), (cx-3,cy), (cx+12,cy), 2)
        # Pointe de la fleche
        pygame.draw.polygon(surf, col,
            [(cx+12,cy),(cx+7,cy-3),(cx+7,cy+3)])
        # Empennage
        pygame.draw.line(surf, (200,60,60), (cx-3,cy),(cx-7,cy-4), 1)
        pygame.draw.line(surf, (200,60,60), (cx-3,cy),(cx-7,cy+4), 1)
    elif wid=="baguette":
        pygame.draw.line(surf,(160,120,200),(cx-10,cy+10),(cx+10,cy-10),3)
        glow=pygame.Surface((10,10),pygame.SRCALPHA)
        pygame.draw.circle(glow,(*col,200),(5,5),5)
        surf.blit(glow,(cx+6,cy-15))
    elif wid=="foudre":
        pts=[(cx+4,cy-12),(cx-2,cy-2),(cx+6,cy-2),(cx-4,cy+12)]
        pygame.draw.lines(surf,col,False,pts,3)
