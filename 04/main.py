"""
main.py — Point d'entree + menus du jeu.

Contient :
  - Les ecrans (menu, choix arme, game over)
  - La gestion des evenements
  - La boucle principale

Architecture des autres fichiers :
  settings.py   — constantes, couleurs, armes, polices
  entities.py   — classes Player, Enemy, Arrow, Basket, Rect
  world.py      — generation procedurale de la map (MapData)
  game_state.py — classe GameState (etat complet de la session)
  physics.py    — update : deplacement, collisions, attaques
  renderer.py   — dessin du jeu en cours

Lancer avec :  python main.py
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
pygame.init()

from settings import (
    WIDTH, HEIGHT, FPS,
    WEAPONS, WEAPON_ORDER, load_fonts,
    C_WHITE, C_GOLD, C_RED, C_DARK, C_GREY, C_GREY_DARK,
)
from world      import MapData
from game_state import GameState
from physics    import update, do_attack
from renderer   import draw_game, draw_weapon_icon



#  INITIALISATION


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trial of Death")
clock  = pygame.time.Clock()
fonts  = load_fonts()

map_data = MapData()
gs       = GameState(map_data)



#  DESSIN MENU PRINCIPAL


def draw_menu(surf):
    surf.fill(C_DARK)
    cx = WIDTH // 2

    def bc(text, font, col, y):
        s = font.render(text, True, col)
        surf.blit(s, (cx - s.get_width() // 2, y))

    bc("Trial of Death",                     fonts["big"],  C_WHITE,     70)
    bc(f"Meilleur score : {gs.high_score}",  fonts["med"],  C_WHITE,    130)
    bc(f"Or : {gs.gold}",                    fonts["med"],  C_GOLD,     158)
    bc(f"PV max : {gs.player.max_hp if gs.player else 5}",
     fonts["med"],  C_RED,      186)
    bc("Ameliorations :", fonts["upg"],  C_WHITE,    240)

    upgrades = [
        "1 : +2 vitesse joueur  — 100 or",
        "2 : +5 or par kill     — 100 or",
        "3 : +1 PV max          — 100 or",
    ]
    for i, text in enumerate(upgrades):
        bc(text, fonts["med"], C_GREY, 280 + i * 32)

    bc("Appuie sur ENTREE pour jouer",       fonts["med"],   C_WHITE,     400)
    bc("(choix de l'arme avant la partie)",  fonts["small"], C_GREY_DARK, 432)



#  DESSIN ECRAN CHOIX D'ARME


_CARD_W   = 210
_CARD_H   = 175
_CARD_GAP = 28
_CARD_Y   = 135


def draw_weapon_select(surf) -> dict:
    """Affiche l'ecran de selection. Retourne le layout pour la detection du clic."""
    surf.fill(C_DARK)
    cx = WIDTH // 2

    title = fonts["big"].render("Choisissez votre arme", True, C_WHITE)
    surf.blit(title, (cx - title.get_width() // 2, 50))

    sub = fonts["small"].render("Cliquez sur une carte ou appuyez sur 1 / 2 / 3 / 4", True, C_GREY)
    surf.blit(sub, (cx - sub.get_width() // 2, 92))

    total_w = len(WEAPON_ORDER) * _CARD_W + (len(WEAPON_ORDER) - 1) * _CARD_GAP
    start_x = cx - total_w // 2

    for idx, wid in enumerate(WEAPON_ORDER):
        bx  = start_x + idx * (_CARD_W + _CARD_GAP)
        w   = WEAPONS[wid]
        col = w["couleur"]

        pygame.draw.rect(surf, (26, 26, 46), (bx, _CARD_Y, _CARD_W, _CARD_H))
        pygame.draw.rect(surf, col,          (bx, _CARD_Y, _CARD_W, _CARD_H), 2)

        draw_weapon_icon(surf, wid, bx + _CARD_W // 2, _CARD_Y + 48, col)

        nm = fonts["card"].render(f"[{idx+1}]  {w['nom']}", True, col)
        surf.blit(nm, (bx + _CARD_W // 2 - nm.get_width() // 2, _CARD_Y + 93))

        dc = fonts["tiny"].render(w["desc"], True, C_GREY)
        surf.blit(dc, (bx + _CARD_W // 2 - dc.get_width() // 2, _CARD_Y + 116))

        portee_txt = str(w["portee"]) if w["portee"] else "infinie"
        st = fonts["tiny"].render(
            f"Degats {w['degats']}  |  Portee {portee_txt}  |  CD {w['cooldown']}ms",
            True, C_GREY_DARK,
        )
        surf.blit(st, (bx + _CARD_W // 2 - st.get_width() // 2, _CARD_Y + 148))

    return {"start_x": start_x, "y": _CARD_Y,
            "card_w": _CARD_W, "card_h": _CARD_H, "card_gap": _CARD_GAP}


def get_weapon_at_click(mouse_pos, layout) -> str:
    """Retourne l'arme cliquee ou None."""
    if layout is None:
        return None
    mx, my = mouse_pos
    for idx, wid in enumerate(WEAPON_ORDER):
        bx = layout["start_x"] + idx * (layout["card_w"] + layout["card_gap"])
        if bx <= mx <= bx + layout["card_w"] and layout["y"] <= my <= layout["y"] + layout["card_h"]:
            return wid
    return None



#  DESSIN GAME OVER


def draw_game_over(surf):
    surf.fill(C_DARK)
    cx, cy = WIDTH // 2, HEIGHT // 3

    def bc(text, font, col, y):
        s = font.render(text, True, col)
        surf.blit(s, (cx - s.get_width() // 2, y))

    bc("GAME OVER",                fonts["title"], C_RED,   cy)
    bc(f"Score final : {gs.score}", fonts["med"],  C_WHITE, cy + 60)
    bc("ECHAP → menu",             fonts["small"], C_GREY,  cy + 110)



#  GESTION DES EVENEMENTS


def handle_menu_event(event):
    if event.type != pygame.KEYDOWN:
        return
    if event.key == pygame.K_RETURN:
        gs.screen_state = "weapon_select"
    elif event.key == pygame.K_1:
        gs.buy_speed()
    elif event.key == pygame.K_2:
        gs.buy_gold_gain()
    elif event.key == pygame.K_3:
        gs.buy_max_hp()


def handle_weapon_select_event(event):
    key_map = {
        pygame.K_1: WEAPON_ORDER[0], pygame.K_2: WEAPON_ORDER[1],
        pygame.K_3: WEAPON_ORDER[2], pygame.K_4: WEAPON_ORDER[3],
    }
    if event.type == pygame.KEYDOWN:
        wid = key_map.get(event.key)
        if wid:
            gs.start_new_game(wid)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        wid = get_weapon_at_click(event.pos, gs.weapon_select_layout)
        if wid:
            gs.start_new_game(wid)


def handle_playing_event(event):
    player = gs.player
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q: player.move_left  = True
        if event.key == pygame.K_d: player.move_right = True
        if event.key == pygame.K_z: player.move_up    = True
        if event.key == pygame.K_s: player.move_down  = True
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_q: player.move_left  = False
        if event.key == pygame.K_d: player.move_right = False
        if event.key == pygame.K_z: player.move_up    = False
        if event.key == pygame.K_s: player.move_down  = False
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        player.mouse_held = True
        if WEAPONS[player.weapon]["type"] == "melee":
            do_attack(gs)
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        player.mouse_held = False


def handle_game_over_event(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        gs.screen_state = "menu"


EVENT_HANDLERS = {
    "menu":          handle_menu_event,
    "weapon_select": handle_weapon_select_event,
    "playing":       handle_playing_event,
    "game_over":     handle_game_over_event,
}



#  BOUCLE PRINCIPALE

def main():
    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            handler = EVENT_HANDLERS.get(gs.screen_state)
            if handler:
                handler(event)

        state = gs.screen_state

        if state == "playing":
            if not update(gs):
                gs.screen_state = "game_over"
            draw_game(screen, gs, fonts)

        elif state == "menu":
            draw_menu(screen)

        elif state == "weapon_select":
            gs.weapon_select_layout = draw_weapon_select(screen)

        elif state == "game_over":
            draw_game_over(screen)

        pygame.display.flip()


if __name__ == "__main__":
    main()