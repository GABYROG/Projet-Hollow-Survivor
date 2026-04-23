"""
settings.py — Constantes globales, couleurs, polices, definition des armes.
Importe par tous les autres modules.
"""

import pygame


#  FENETRE & MAP


WIDTH      = 1264
HEIGHT     = 700
MAP_W      = 3000
MAP_H      = 3000
MAP_SEED   = 42
FPS        = 60


#  COULEURS


C_BG         = (74,  124, 89)
C_PLAYER     = (52,  152, 219)
C_PLAYER_OUT = (41,  128, 185)
C_ENEMY      = (231, 76,  60)
C_ENEMY_OUT  = (192, 57,  43)
C_WHITE      = (255, 255, 255)
C_BLACK      = (0,   0,   0)
C_GOLD       = (241, 196, 15)
C_RED        = (231, 76,  60)
C_GREEN      = (46,  204, 113)
C_ORANGE     = (230, 126, 34)
C_HUD_BG     = (17,  17,  17)
C_DARK       = (30,  30,  30)
C_GREY       = (189, 195, 199)
C_GREY_DARK  = (127, 140, 141)

#  POLICES  (initialisees apres pygame.init())


def load_fonts():
    """Retourne un dict de polices. Appeler apres pygame.init()."""
    return {
        "big":   pygame.font.SysFont("Arial", 30, bold=True),
        "med":   pygame.font.SysFont("Arial", 18),
        "small": pygame.font.SysFont("Arial", 13),
        "tiny":  pygame.font.SysFont("Arial", 10),
        "title": pygame.font.SysFont("Arial", 40, bold=True),
        "card":  pygame.font.SysFont("Arial", 15, bold=True),
        "upg":   pygame.font.SysFont("Arial", 20, bold=True),
    }


#  ARMES


WEAPONS = {
    "epee": {
        "nom":       "Epee",
        "desc":      "Equilibree — bons degats, portee moyenne",
        "couleur":   (170, 170, 255),
        "degats":    2,
        "portee":    70,
        "largeur":   14,
        "cooldown":  500,
        "swing_dur": 200,
        "knockback": 18,
        "type":      "melee",
    },
    "lance": {
        "nom":       "Lance",
        "desc":      "Grande portee, poussee directe, lente",
        "couleur":   (255, 170, 68),
        "degats":    1,
        "portee":    110,
        "largeur":   8,
        "cooldown":  800,
        "swing_dur": 300,
        "knockback": 30,
        "type":      "melee",
    },
    "poignard": {
        "nom":       "Poignard",
        "desc":      "Tres rapide, faible portee",
        "couleur":   (68, 255, 170),
        "degats":    1,
        "portee":    40,
        "largeur":   8,
        "cooldown":  220,
        "swing_dur": 100,
        "knockback": 6,
        "type":      "melee",
    },
    "arc": {
        "nom":       "Arc",
        "desc":      "Maintien clic = tir continu",
        "couleur":   (139, 69, 19),
        "degats":    1,
        "portee":    0,
        "largeur":   0,
        "cooldown":  350,
        "swing_dur": 0,
        "knockback": 5,
        "type":      "range",
    },
}

WEAPON_ORDER = ["epee", "lance", "poignard", "arc"]


#  ENTITES — valeurs par defaut


PLAYER_W        = 50
PLAYER_H        = 50
PLAYER_SPEED    = 10
PLAYER_MAX_HP   = 5

ENEMY_W         = 40
ENEMY_H         = 40
ENEMY_SPEED     = 3
ENEMY_HP_MAX    = 3
ENEMY_ATK_SPEED = 800  
ENEMY_KNOCKBACK = 0.15   # resistance knockback fleches
SPAWN_INTERVAL  = 3000  
MAX_ENEMIES     = 8

ARROW_SPEED     = 18
ARROW_KNOCKBACK = 5
ARROW_KB_RESIST = 0.15

BASKET_W        = 32
BASKET_H        = 28
BASKET_HEAL     = 20
BASKET_COUNT    = 10

SAFE_RADIUS     = 250    # zone sans decors autour du spawn
ENEMY_MASS      = 0.18   # fraction du recul transmise a l'ennemi
GOLD_GAIN_BASE  = 100
