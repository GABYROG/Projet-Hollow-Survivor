"""
renderer.py — Tout le rendu graphique de la partie en cours.

Fonctions publiques :
  draw_game(surf, gs)       — dessine une frame complete de jeu
  draw_weapon_icon(...)     — icone arme pour l'ecran de selection

Fonctions internes :
  _draw_decors              — arbres, rochers, buissons, clotures
  _draw_baskets             — paniers de fruits
  _draw_enemy / _draw_player
  _draw_weapon / _draw_arrows
  _draw_hud
"""

import math
import pygame

from settings import (
    WIDTH, HEIGHT,
    C_PLAYER, C_PLAYER_OUT, C_ENEMY, C_ENEMY_OUT,
    C_WHITE, C_GOLD, C_RED, C_GREEN, C_ORANGE, C_HUD_BG, C_GREY,C_BLUE,
    BASKET_W, BASKET_H,
    WEAPONS,
)



#  POINT D'ENTREE

def draw_game(surf: pygame.Surface, gs, fonts: dict):
    """Dessine une frame complete de la partie en cours."""
    cam_x, cam_y = gs.get_camera()

    # 1. Sol pre-rendu
    surf.blit(gs.map_data.surface, (0, 0), (cam_x, cam_y, WIDTH, HEIGHT))

    # 2. Decors (arbres, rochers, buissons, clotures)
    _draw_decors(surf, gs.map_data, cam_x, cam_y)

    # 3. Paniers de fruits
    _draw_baskets(surf, gs.baskets, cam_x, cam_y, fonts["tiny"])

    # 4. Ennemis
    for enemy in gs.enemies:
        _draw_enemy(surf, enemy, cam_x, cam_y, fonts["tiny"])

    # 5. Joueur + arme + fleches
    _draw_player(surf, gs.player, cam_x, cam_y)
    _draw_weapon(surf, gs.player)
    _draw_arrows(surf, gs.arrows, cam_x, cam_y)

    # 6. HUD
    _draw_hud(surf, gs, fonts)



#  DECORS


def _draw_decors(surf, map_data, cam_x, cam_y):
    _draw_fences(surf, map_data.fences, cam_x, cam_y)
    _draw_bushes(surf, map_data.bushes, cam_x, cam_y)
    _draw_rocks(surf,  map_data.rocks,  cam_x, cam_y)
    _draw_trees(surf,  map_data.trees,  cam_x, cam_y)


def _draw_fences(surf, fences, cam_x, cam_y):
    for (x1, y1, x2, y2) in fences:
        sx1, sy1 = x1 - cam_x, y1 - cam_y
        sx2, sy2 = x2 - cam_x, y2 - cam_y
        if not (-20 <= sx1 <= WIDTH + 20 and -20 <= sy1 <= HEIGHT + 20):
            continue
        col_post  = (139, 105, 20)
        col_plank = (160, 120, 74)
        pygame.draw.rect(surf, col_post,  (sx1 - 3, sy1 - 3, 6, 19))
        pygame.draw.rect(surf, col_post,  (sx2 - 3, sy2 - 3, 6, 19))
        pygame.draw.line(surf, col_plank, (sx1, sy1 + 6),  (sx2, sy2 + 6),  3)
        pygame.draw.line(surf, col_plank, (sx1, sy1 + 12), (sx2, sy2 + 12), 2)


def _draw_bushes(surf, bushes, cam_x, cam_y):
    for (cx, cy, r, col) in bushes:
        sx, sy = cx - cam_x, cy - cam_y
        if not (-r - 5 <= sx <= WIDTH + r + 5 and -r - 5 <= sy <= HEIGHT + r + 5):
            continue
        dark = tuple(max(0, c - 40) for c in col)
        pygame.draw.ellipse(surf, dark, (sx - r,     sy - r // 2, r * 2,       r + r // 2))
        pygame.draw.ellipse(surf, col,  (sx - r + 4, sy - r,      (r - 4) * 2, r + r // 2))
        pygame.draw.ellipse(surf, (76, 175, 80), (sx - r // 2, sy - r + 2, r, r // 2))


def _draw_rocks(surf, rocks, cam_x, cam_y):
    for (cx, cy, rx, ry, col) in rocks:
        sx, sy = cx - cam_x, cy - cam_y
        if not (-rx - 5 <= sx <= WIDTH + rx + 5 and -ry - 5 <= sy <= HEIGHT + ry + 5):
            continue
        pygame.draw.ellipse(surf, (51, 51, 51),   (sx - rx + 3, sy - ry + 5, rx * 2, ry * 2))
        pygame.draw.ellipse(surf, col,             (sx - rx,     sy - ry,     rx * 2, ry * 2))
        pygame.draw.ellipse(surf, (187, 187, 187), (sx - rx//2,  sy - ry//2,  rx//2,  ry//2))


def _draw_trees(surf, trees, cam_x, cam_y):
    for (cx, cy, r_t, r_f, col) in trees:
        sx, sy = cx - cam_x, cy - cam_y
        if not (-r_f - 10 <= sx <= WIDTH + r_f + 10 and -r_f - 10 <= sy <= HEIGHT + r_f + 10):
            continue
        shadow = tuple(max(0, c - 60) for c in col)
        dark   = tuple(max(0, c - 30) for c in col)
        pygame.draw.ellipse(surf, shadow, (sx - r_f // 2, sy + r_t - 2, r_f, 12))
        pygame.draw.rect(surf, (107, 58, 42), (sx - r_t, sy - r_t, r_t * 2, r_t + 10))
        pygame.draw.ellipse(surf, dark, (sx - r_f,     sy - r_f,     r_f * 2,       r_f + r_f // 2))
        pygame.draw.ellipse(surf, col,  (sx - r_f + 4, sy - r_f - 6, (r_f - 4) * 2, r_f + r_f // 2 - 4))
        pygame.draw.ellipse(surf, (92, 214, 92), (sx - r_f // 2, sy - r_f - 4, r_f, r_f // 3 * 2))



#  PANIERS


def _draw_baskets(surf, baskets, cam_x, cam_y, font_tiny):
    for basket in baskets:
        if not basket.active:
            continue
        sx, sy = basket.x - cam_x, basket.y - cam_y
        if not (-40 <= sx <= WIDTH + 40 and -40 <= sy <= HEIGHT + 40):
            continue
        bx, by = int(sx) - BASKET_W // 2, int(sy) - BASKET_H // 2
        _draw_single_basket(surf, bx, by, font_tiny)


def _draw_single_basket(surf, bx, by, font_tiny):
    body_y = by + BASKET_H // 3
    body_h = BASKET_H * 2 // 3
    pygame.draw.rect(surf,   (196, 160, 80), (bx, body_y, BASKET_W, body_h))
    pygame.draw.ellipse(surf,(196, 160, 80), (bx, body_y - 4, BASKET_W, 12))
    pygame.draw.rect(surf,   (139, 105, 20), (bx, body_y, BASKET_W, body_h), 2)
    for i in range(1, 4):
        yy = body_y + i * body_h // 4
        pygame.draw.line(surf, (139, 105, 20), (bx + 2, yy), (bx + BASKET_W - 2, yy), 1)
    pygame.draw.arc(surf, (139, 105, 20), (bx + 4, by - 4, BASKET_W - 8, BASKET_H // 2 + 4), 0, math.pi, 3)
    pygame.draw.circle(surf, (255, 65,  54),  (bx + 8,  by + 6), 6)
    pygame.draw.circle(surf, (255, 220, 0),   (bx + 16, by + 4), 6)
    pygame.draw.circle(surf, (255, 133, 27),  (bx + 24, by + 6), 5)
    lbl = font_tiny.render("+20 PV", True, (0, 255, 136))
    surf.blit(lbl, (bx + BASKET_W // 2 - lbl.get_width() // 2, by - 14))



#  ENNEMIS


def _draw_enemy(surf, enemy, cam_x, cam_y, font_tiny):
    ex, ey = int(enemy.x - cam_x), int(enemy.y - cam_y)
    pygame.draw.rect(surf, C_ENEMY,     (ex, ey, 40, 40))
    pygame.draw.rect(surf, C_ENEMY_OUT, (ex, ey, 40, 40), 2)
    ratio = max(0, enemy.hp / 3)
    pygame.draw.rect(surf, (85, 85, 85), (ex, ey - 12, 40, 6))
    pygame.draw.rect(surf, C_RED,        (ex, ey - 12, int(40 * ratio), 6))
    lbl = font_tiny.render(f"{enemy.hp}/3", True, C_RED)
    surf.blit(lbl, (ex + 20 - lbl.get_width() // 2, ey - 22))



#
#  JOUEUR


def _draw_player(surf, player, cam_x, cam_y):
    px, py = int(player.x - cam_x), int(player.y - cam_y)
    pygame.draw.rect(surf, C_PLAYER,     (px, py, 50, 50))
    pygame.draw.rect(surf, C_PLAYER_OUT, (px, py, 50, 50), 2)


#  ARME DU JOUEUR


def _pt(cx, cy, angle, dist, perp_off=0):
    """Point a distance `dist` dans la direction `angle`, decale de `perp_off`."""
    pa = angle + math.pi / 2
    return (
        int(cx + math.cos(angle) * dist + math.cos(pa) * perp_off),
        int(cy + math.sin(angle) * dist + math.sin(pa) * perp_off),
    )


def _draw_weapon(surf, player):
    """Calcule l'animation et dispatche vers la bonne fonction de dessin."""
    cam_x, cam_y = 0, 0   # coordonnees deja en espace ecran via player.x/y
    # On recalcule la position ecran du joueur a partir du centre
    from settings import WIDTH, HEIGHT, MAP_W, MAP_H
    cx = max(0, min(int(player.x) - WIDTH  // 2, MAP_W - WIDTH))
    cy = max(0, min(int(player.y) - HEIGHT // 2, MAP_H - HEIGHT))
    pcx = player.x - cx + 25
    pcy = player.y - cy + 25

    w   = WEAPONS[player.weapon]
    now = pygame.time.get_ticks()
    sp  = 0.0

    if player.attack_active and w["swing_dur"] > 0:
        sp = min(1.0, (now - player.attack_start) / w["swing_dur"])
        if sp >= 1.0:
            player.attack_active = False

    col = w["couleur"]
    a   = player.aim_angle

    if player.weapon == "arc":
        _draw_bow(surf, pcx, pcy, a, col)
    elif player.weapon == "lance":
        _draw_lance(surf, pcx, pcy, a, col, math.sin(sp * math.pi) * 40)
    elif player.weapon == "epee":
        _draw_sword(surf, pcx, pcy, a + math.sin(sp * math.pi) * 0.55, col)
    elif player.weapon == "poignard":
        _draw_dagger(surf, pcx, pcy, a + math.sin(sp * math.pi) * 0.4, col)


def _draw_bow(surf, sx, sy, a, col):
    R  = 30
    bx, by = sx + math.cos(a) * R, sy + math.sin(a) * R
    perp = a + math.pi / 2
    half = 14
    x1, y1 = bx + math.cos(perp)*half, by + math.sin(perp)*half
    x2, y2 = bx - math.cos(perp)*half, by - math.sin(perp)*half
    tx, ty = bx + math.cos(a)*10,      by + math.sin(a)*10
    pygame.draw.line(surf, col,          (int(x1),int(y1)), (int(tx),int(ty)), 3)
    pygame.draw.line(surf, col,          (int(x2),int(y2)), (int(tx),int(ty)), 3)
    pygame.draw.line(surf, (245,222,179),(int(x1),int(y1)), (int(x2),int(y2)), 1)


def _draw_sword(surf, sx, sy, a, col):
    perp   = a + math.pi / 2
    gx, gy = sx + math.cos(a)*22, sy + math.sin(a)*22
    pygame.draw.line(surf, (136,136,136),
        (int(gx+math.cos(perp)*10), int(gy+math.sin(perp)*10)),
        (int(gx-math.cos(perp)*10), int(gy-math.sin(perp)*10)), 4)
    tip = _pt(sx, sy, a, 70)
    pygame.draw.line(surf, col, _pt(sx,sy,a,20), tip, 5)
    pygame.draw.polygon(surf, col, [tip, _pt(sx,sy,a,60,4), _pt(sx,sy,a,60,-4)])


def _draw_lance(surf, sx, sy, a, col, thrust=0.0):
    base = _pt(sx, sy, a, -18)
    tip  = _pt(sx, sy, a, 105 + thrust)
    pygame.draw.line(surf, (139,69,19), base, tip, 5)
    mid  = _pt(sx, sy, a, 30)
    perp = a + math.pi / 2
    pygame.draw.line(surf, (170,170,170),
        (int(mid[0]+math.cos(perp)*5), int(mid[1]+math.sin(perp)*5)),
        (int(mid[0]-math.cos(perp)*5), int(mid[1]-math.sin(perp)*5)), 4)
    tip_d = int(105 + thrust)
    pts   = [tip, _pt(sx,sy,a,tip_d-20,5), _pt(sx,sy,a,tip_d-20,-5)]
    pygame.draw.polygon(surf, col,           pts)
    pygame.draw.polygon(surf, (204,136,51),  pts, 1)


def _draw_dagger(surf, sx, sy, a, col):
    perp   = a + math.pi / 2
    gx, gy = sx + math.cos(a)*16, sy + math.sin(a)*16
    pygame.draw.line(surf, (136,136,136),
        (int(gx+math.cos(perp)*7), int(gy+math.sin(perp)*7)),
        (int(gx-math.cos(perp)*7), int(gy-math.sin(perp)*7)), 3)
    pygame.draw.line(surf, col, _pt(sx,sy,a,14), _pt(sx,sy,a,38), 4)


def _draw_arrows(surf, arrows, cam_x, cam_y):
    for arrow in arrows:
        ax, ay = arrow.x - cam_x, arrow.y - cam_y
        ang    = arrow.angle
        tip    = (int(ax + math.cos(ang)*18), int(ay + math.sin(ang)*18))
        tail   = (int(ax - math.cos(ang)*4),  int(ay - math.sin(ang)*4))
        pygame.draw.line(surf, (210,105,30), tail, tip, 2)
        perp = ang + math.pi / 2
        pts  = [
            tip,
            (int(tip[0]-math.cos(ang)*6+math.cos(perp)*3),
             int(tip[1]-math.sin(ang)*6+math.sin(perp)*3)),
            (int(tip[0]-math.cos(ang)*6-math.cos(perp)*3),
             int(tip[1]-math.sin(ang)*6-math.sin(perp)*3)),
        ]
        pygame.draw.polygon(surf, (44,44,44), pts)



#  ICONE ARME (ecran de selection)


def draw_weapon_icon(surf, wid: str, cx: int, cy: int, col: tuple):
    """Dessine une icone simplifiee de l'arme, utilisee sur l'ecran de selection."""
    if wid == "epee":
        pygame.draw.line(surf, col, (cx, cy+28), (cx, cy-28), 5)
        pygame.draw.line(surf, (136,136,136), (cx-12, cy+10), (cx+12, cy+10), 4)
    elif wid == "lance":
        pygame.draw.line(surf, (139,69,19), (cx-28, cy+16), (cx+28, cy-16), 4)
        pygame.draw.polygon(surf, col, [(cx+28,cy-16),(cx+12,cy-9),(cx+18,cy-24)])
    elif wid == "poignard":
        pygame.draw.line(surf, col, (cx, cy+18), (cx, cy-18), 4)
        pygame.draw.line(surf, (136,136,136), (cx-8, cy+6), (cx+8, cy+6), 3)
    elif wid == "arc":
        pygame.draw.arc(surf, col, (cx-18, cy-24, 36, 48),
                        math.radians(60), math.radians(300), 4)
        pygame.draw.line(surf, (245,222,179), (cx-9, cy-21), (cx-9, cy+21), 1)



#  HUD

def _draw_hud(surf, gs, fonts):
    player = gs.player
    w      = WEAPONS[player.weapon]

    pygame.draw.rect(surf, C_HUD_BG, (0, 0, 210, 170))

    lines = [
        (fonts["med"],   f"Score: {gs.score}",                    C_WHITE),
        (fonts["med"],   f"High Score: {gs.high_score}",          C_GOLD),
        (fonts["med"],   f"PV: {player.hp}/{player.max_hp}",      C_RED),
        (fonts["med"],   f"Or: {gs.gold}",                        C_GOLD),
        (fonts["small"], f"Arme: {w['nom']}",                     w["couleur"]),
        (fonts["small"], f"Ennemis: {len(gs.enemies)}",           C_GREY),
    ]
    for i, (font, text, col) in enumerate(lines):
        surf.blit(font.render(text, True, col), (10, 10 + i * 26))

    # Barre de vie
    ratio  = max(0, player.hp / player.max_hp)
    hp_col = C_GREEN if ratio > 0.5 else C_ORANGE if ratio > 0.25 else C_RED
    pygame.draw.rect(surf, (51, 51, 51), (10, 158, 190, 10))
    pygame.draw.rect(surf, hp_col,       (10, 158, int(190 * ratio), 10))

    ratio  =( gs.exp / gs.nextlevel)
    exp_col = C_BLUE 
    pygame.draw.rect(surf, (55, 55, 55), (10, 180, 190, 10))
    pygame.draw.rect(surf, exp_col,       (10, 180, gs.exp/gs.nextlevel, 10))

    # Hint commande
    hint = "[Clic] Attaquer" if w["type"] == "melee" else "[Maintien clic] Tirer"
    ht   = fonts["small"].render(hint, True, C_GREY)
    surf.blit(ht, (WIDTH - 10 - ht.get_width(), 10))
