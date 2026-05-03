"""settings.py — Constantes, couleurs, polices, armes style Vampire Survivors."""

import pygame

WIDTH, HEIGHT  = 1280, 720
MAP_W,  MAP_H  = 4096, 4096
MAP_SEED       = 42
FPS            = 60

PLAYER_W       = 32
PLAYER_H       = 32
PLAYER_SPEED   = 4.0
PLAYER_MAX_HP  = 100

ENEMY_MASS     = 0.12
MAX_ENEMIES    = 80
GOLD_GAIN_BASE = 8

BASKET_W, BASKET_H = 28, 24
BASKET_HEAL        = 40
BASKET_COUNT       = 14
SAFE_RADIUS        = 320

ARROW_SPEED    = 13

# ── Couleurs ──
C_BG        = (12,   8,  20)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0,     0,   0)
C_GOLD      = (255, 210,  50)
C_RED       = (220,  55,  55)
C_GREEN     = (70,  200,  90)
C_ORANGE    = (230, 130,  40)
C_PURPLE    = (160,  60, 220)
C_BLUE      = (60,  140, 220)
C_CYAN      = (60,  220, 210)
C_DARK      = (10,   6,  18)
C_GREY      = (155, 155, 165)
C_GREY_DARK = (80,   80,  90)
C_HUD_BG    = (8,    5,  15)
C_XP_BAR    = (60,  180, 255)
C_VIGNETTE  = (0,    0,   0)


def load_fonts():
    return {
        "title":  pygame.font.SysFont("Arial", 46, bold=True),
        "big":    pygame.font.SysFont("Arial", 26, bold=True),
        "med":    pygame.font.SysFont("Arial", 17),
        "small":  pygame.font.SysFont("Arial", 12),
        "tiny":   pygame.font.SysFont("Arial", 10),
        "card":   pygame.font.SysFont("Arial", 15, bold=True),
        "timer":  pygame.font.SysFont("Arial", 30, bold=True),
        "damage": pygame.font.SysFont("Arial", 20, bold=True),
        "upg":    pygame.font.SysFont("Arial", 18, bold=True),
    }



#  ARMES  (toutes automatiques, style VS)
#
#  types :
#    melee_swing  — arc devant le joueur (epee, faux)
#    melee_area   — zone circulaire (ail, marteau)
#    melee_orbit  — tourne autour du joueur (bouclier, bible)
#    projectile   — tire vers l'ennemi le plus proche (arc, baguette, couteau)
#    whip         — fouet horizontal


WEAPONS = {
    # ── Melee swing ──
    "epee": {
        "nom": "Epee", "icon": "⚔",
        "desc": "Coup en arc devant le joueur. Classique et efficace.",
        "couleur": (180, 180, 255),
        "type": "melee_swing",
        "degats": 8, "portee": 85, "largeur": 22,
        "cooldown": 650, "swing_dur": 200, "knockback": 10,
    },
    "faux": {
        "nom": "Faux", "icon": "☽",
        "desc": "Coup en arc large, blessure qui saigne (+2 dps pendant 3s).",
        "couleur": (180, 230, 150),
        "type": "melee_swing",
        "degats": 12, "portee": 110, "largeur": 28,
        "cooldown": 1200, "swing_dur": 320, "knockback": 14,
        "bleed": True,
    },
    # ── Whip ──
    "fouet": {
        "nom": "Fouet", "icon": "〜",
        "desc": "Claque horizontale qui traverse tous les ennemis.",
        "couleur": (220, 160, 60),
        "type": "whip",
        "degats": 10, "portee": 160, "largeur": 24,
        "cooldown": 900, "swing_dur": 180, "knockback": 8,
    },
    # ── Area ──
    "ail": {
        "nom": "Ail", "icon": "✿",
        "desc": "Nuage de puanteur autour du joueur. Repousse et empoisonne.",
        "couleur": (200, 230, 100),
        "type": "melee_area",
        "degats": 5, "portee": 90, "largeur": 90,
        "cooldown": 500, "swing_dur": 100, "knockback": 6,
        "poison": True,
    },
    "marteau": {
        "nom": "Marteau de Guerre", "icon": "🔨",
        "desc": "Frappe devastatrice en zone. Enorme knockback.",
        "couleur": (200, 80, 80),
        "type": "melee_area",
        "degats": 22, "portee": 80, "largeur": 80,
        "cooldown": 2000, "swing_dur": 450, "knockback": 55,
    },
    # ── Orbit ──
    "bible": {
        "nom": "Bible Sainte", "icon": "✝",
        "desc": "Trois bibles orbitent et brulent les ennemis au contact.",
        "couleur": (255, 240, 120),
        "type": "melee_orbit",
        "degats": 7, "portee": 90, "largeur": 18,
        "cooldown": 200, "swing_dur": 0, "knockback": 5,
        "orbit_count": 3, "orbit_speed": 2.5,
    },
    "bouclier": {
        "nom": "Bouclier Runique", "icon": "🛡",
        "desc": "Deux boucliers tournants qui absorbent et renvoient les degats.",
        "couleur": (100, 160, 255),
        "type": "melee_orbit",
        "degats": 15, "portee": 70, "largeur": 22,
        "cooldown": 150, "swing_dur": 0, "knockback": 20,
        "orbit_count": 2, "orbit_speed": 1.8,
    },
    # ── Projectile ──
    "couteau": {
        "nom": "Couteau", "icon": "🗡",
        "desc": "Lance des couteaux rapides vers l'ennemi le plus proche.",
        "couleur": (210, 210, 255),
        "type": "projectile",
        "degats": 5, "portee": 0, "largeur": 0,
        "cooldown": 380, "swing_dur": 0, "knockback": 2,
        "proj_speed": 15, "proj_r": 5, "proj_color": (210, 210, 255),
    },
    "arc": {
        "nom": "Arc Long", "icon": "🏹",
        "desc": "Fleche puissante qui traverse les ennemis.",
        "couleur": (180, 130, 50),
        "type": "projectile",
        "degats": 14, "portee": 0, "largeur": 0,
        "cooldown": 900, "swing_dur": 0, "knockback": 5,
        "proj_speed": 18, "proj_r": 7, "proj_color": (200, 160, 60),
        "pierce": 2,
    },
    "baguette": {
        "nom": "Baguette Magique", "icon": "✨",
        "desc": "Orbe magique qui explose a l'impact.",
        "couleur": (160, 80, 255),
        "type": "projectile",
        "degats": 18, "portee": 0, "largeur": 0,
        "cooldown": 1100, "swing_dur": 0, "knockback": 8,
        "proj_speed": 11, "proj_r": 10, "proj_color": (180, 100, 255),
        "explode": True,
    },
    "foudre": {
        "nom": "Orbe de Foudre", "icon": "⚡",
        "desc": "Chaine sur 4 ennemis. Etourdit.",
        "couleur": (180, 220, 255),
        "type": "projectile",
        "degats": 10, "portee": 0, "largeur": 0,
        "cooldown": 700, "swing_dur": 0, "knockback": 3,
        "proj_speed": 20, "proj_r": 8, "proj_color": (180, 220, 255),
        "chain": 3,
    },
}

WEAPON_ORDER = ["epee", "faux", "fouet", "ail", "marteau",
                "bible", "bouclier", "couteau", "arc", "baguette", "foudre"]
MAX_WEAPONS  = 6   # max d'armes simultanees style VS
