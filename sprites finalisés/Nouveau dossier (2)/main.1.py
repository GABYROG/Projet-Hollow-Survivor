"""
main.py — Point d'entree. Boucle principale + tous les ecrans.

Lancer : python main.py
"""



import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
pygame.init()

from settings   import (WIDTH, HEIGHT, FPS, WEAPONS, WEAPON_ORDER,
                         C_WHITE, C_GOLD, C_RED, C_GREEN, C_ORANGE,
                         C_GREY, C_GREY_DARK, C_DARK, C_HUD_BG, load_fonts)
from world import MapData
from game_state import GameState
from physics    import update
from renderer   import draw_game, draw_victory, draw_weapon_icon
from experience import RARITY_COLORS

# ── Init ──
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trial of Death  —  Vampire Style")
clock  = pygame.time.Clock()
fonts  = load_fonts()

print("Chargement de la map...")
map_data = MapData()
gs       = GameState(map_data)
print("Pret !")



#  MENU PRINCIPAL


def draw_menu():
    screen.fill(C_DARK)
    cx = WIDTH // 2

    # Fond etoile
    random.seed(99)
    for _ in range(160):
        sx = random.randint(0, WIDTH)
        sy = random.randint(0, HEIGHT)
        sz = random.choice([1, 1, 1, 2])
        a  = random.randint(60, 200)
        s  = pygame.Surface((sz*2, sz*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 200, 255, a), (sz, sz), sz)
        screen.blit(s, (sx, sy))

    def bc(text, font, col, y, alpha=255):
        s = font.render(text, True, col)
        s.set_alpha(alpha)
        screen.blit(s, (cx - s.get_width()//2, y))

    bc("⚔  TRIAL OF DEATH  ⚔", fonts["title"], C_GOLD,  55)
    bc("Style Vampire Survivors",  fonts["small"], C_GREY,  112)

    # Stats
    panel = pygame.Surface((320, 90), pygame.SRCALPHA)
    panel.fill((20, 12, 35, 200))
    screen.blit(panel, (cx - 160, 140))
    pygame.draw.rect(screen, (60, 40, 100), (cx-160, 140, 320, 90), 1, border_radius=4)
    bc(f"Meilleur score : {gs.high_score}", fonts["med"], C_WHITE, 152)
    bc(f"Or total : {gs.gold}",              fonts["med"], C_GOLD,  178)

    # Ameliorations meta
    bc("— Ameliorations permanentes —", fonts["upg"], C_WHITE, 252)
    upgrades_meta = [
        ("1", "+Vitesse de base",    "100 or"),
        ("2", "+Bonus or/kill",      "100 or"),
        ("3", "+PV de depart (+20)", "100 or"),
    ]
    for i, (key, nom, cost) in enumerate(upgrades_meta):
        col = C_GOLD if gs.gold >= 100 else C_GREY_DARK
        bc(f"[{key}]  {nom}  —  {cost}", fonts["med"], col, 290 + i*30)

    # Bouton jouer
    now_ms = pygame.time.get_ticks()
    blink  = int(now_ms/600) % 2 == 0
    bc("▶  Appuie sur ENTREE pour jouer", fonts["big"], C_WHITE if blink else C_GREY, 418)
    bc("(les armes attaquent automatiquement)", fonts["small"], C_GREY_DARK, 458)



#  SELECTION D'ARME DE DEPART


CARD_W, CARD_H = 180, 240
CARD_GAP       = 22
START_WEAPONS  = ["epee", "couteau", "arc", "ail", "bible", "fouet"]


def draw_weapon_select():
    screen.fill(C_DARK)
    cx = WIDTH // 2

    def bc(t, f, c, y):
        s = f.render(t, True, c)
        screen.blit(s, (cx - s.get_width()//2, y))

    bc("Choisissez votre arme de depart", fonts["title"], C_GOLD,  32)
    bc("Les armes attaquent seules — collectez les gemmes XP pour monter de niveau",
       fonts["small"], C_GREY, 90)

    total  = len(START_WEAPONS)*CARD_W + (len(START_WEAPONS)-1)*CARD_GAP
    sx0    = cx - total//2
    by0    = 120

    for idx, wid in enumerate(START_WEAPONS):
        w   = WEAPONS[wid]
        col = w["couleur"]
        bx  = sx0 + idx*(CARD_W+CARD_GAP)

        # Fond carte
        bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        bg.fill((14, 9, 28, 210))
        screen.blit(bg, (bx, by0))
        pygame.draw.rect(screen, col, (bx, by0, CARD_W, CARD_H), 2, border_radius=6)

        # Icone grande
        draw_weapon_icon(screen, wid, bx+CARD_W//2, by0+62, col)

        # Glow autour de l'icone
        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, 40), (30, 30), 28)
        screen.blit(glow, (bx+CARD_W//2-30, by0+35))

        # Nom + touche
        nm = fonts["card"].render(f"[{idx+1}]  {w['nom']}", True, col)
        screen.blit(nm, (bx+CARD_W//2-nm.get_width()//2, by0+108))

        # Description
        words = w["desc"].split()
        lines, line = [], ""
        for word in words:
            test = (line+" "+word).strip()
            if fonts["tiny"].size(test)[0] < CARD_W-14:
                line = test
            else:
                lines.append(line); line = word
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            d = fonts["tiny"].render(ln, True, C_GREY)
            screen.blit(d, (bx+CARD_W//2-d.get_width()//2, by0+134+j*16))

        # Type
        type_labels = {
            "melee_swing": "Corps-a-corps",
            "whip":        "Fouet",
            "melee_area":  "Zone",
            "melee_orbit": "Orbital",
            "projectile":  "Projectile",
        }
        tl  = type_labels.get(w["type"], w["type"])
        tls = fonts["tiny"].render(tl, True, col)
        screen.blit(tls, (bx+CARD_W//2-tls.get_width()//2, by0+CARD_H-22))

    return {"sx0":sx0, "by0":by0, "cw":CARD_W, "ch":CARD_H, "gap":CARD_GAP}


def get_weapon_clicked(pos, layout):
    mx, my = pos
    for idx, wid in enumerate(START_WEAPONS):
        bx = layout["sx0"] + idx*(layout["cw"]+layout["gap"])
        if bx <= mx <= bx+layout["cw"] and layout["by0"] <= my <= layout["by0"]+layout["ch"]:
            return wid
    return None



#  ECRAN LEVEL-UP  (jeu visible derriere, ralenti)


def draw_level_up():
    xp    = gs.xp_system
    offer = xp.pending_offer
    if not offer:
        gs.screen_state = "playing"
        return

    # Fond sombre semi-transparent
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((4, 2, 14, 185))
    screen.blit(overlay, (0, 0))

    # Bandeau haut
    band = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
    band.fill((20, 10, 50, 220))
    screen.blit(band, (0, 0))

    cx = WIDTH // 2

    def bc(t, f, c, y):
        s = f.render(t, True, c)
        screen.blit(s, (cx - s.get_width()//2, y))

    bc(f"NIVEAU  {xp.level} !", fonts["title"], C_GOLD, 8)

    # Barre XP complete (pour montrer la progression)
    pygame.draw.rect(screen, (40, 30, 80), (40, 56, WIDTH-80, 6), border_radius=3)
    pygame.draw.rect(screen, C_GOLD,       (40, 56, WIDTH-80, 6), border_radius=3)

    bc("Choisissez une amelioration", fonts["big"], C_WHITE, 76)
    bc("(les ennemis continuent — le temps est ralenti)", fonts["small"], (130,120,180), 108)

    cw, ch = 260, 228
    gap    = 28
    total  = len(offer)*cw + (len(offer)-1)*gap
    sx0    = cx - total//2
    cy0    = 132

    for i, upg in enumerate(offer):
        bx    = sx0 + i*(cw+gap)
        rarity= upg.get("rarity","Commun")
        col   = RARITY_COLORS.get(rarity, C_GREY)

        # Fond avec lueur coloree
        glow_s = pygame.Surface((cw+20, ch+20), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*col, 25), (0, 0, cw+20, ch+20), border_radius=10)
        screen.blit(glow_s, (bx-10, cy0-10))

        bg = pygame.Surface((cw, ch), pygame.SRCALPHA)
        bg.fill((10, 6, 22, 230))
        screen.blit(bg, (bx, cy0))
        pygame.draw.rect(screen, col, (bx, cy0, cw, ch), 2, border_radius=6)

        # Badge rarete
        rar_s = fonts["small"].render(rarity.upper(), True, col)
        screen.blit(rar_s, (bx+cw//2-rar_s.get_width()//2, cy0+8))

        # Tag arme (si amelioration d'arme)
        utype = upg.get("type","stat")
        if utype == "weapon_upgrade":
            wid_tag = upg.get("weapon","?")
            lvl_tag = upg.get("level","?")
            w_data  = WEAPONS.get(wid_tag,{})
            tag_col = w_data.get("couleur", C_GREY)
            tag_s   = fonts["tiny"].render(
                f"{w_data.get('nom',wid_tag).upper()}  niv.{lvl_tag}", True, tag_col)
            screen.blit(tag_s, (bx+cw//2-tag_s.get_width()//2, cy0+28))
            # Icone arme
            draw_weapon_icon(screen, wid_tag, bx+cw//2, cy0+68, tag_col)
        elif utype == "new_weapon":
            wid_new = upg.get("weapon_id","?")
            w_data  = WEAPONS.get(wid_new,{})
            tag_col = w_data.get("couleur", C_GOLD)
            new_s   = fonts["tiny"].render("NOUVELLE ARME", True, C_GOLD)
            screen.blit(new_s, (bx+cw//2-new_s.get_width()//2, cy0+28))
            draw_weapon_icon(screen, wid_new, bx+cw//2, cy0+68, tag_col)
        else:
            # Icone stat (cercle colore)
            glyph_s = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glyph_s, (*col, 180), (18, 18), 17)
            pygame.draw.circle(glyph_s, C_WHITE, (18, 18), 17, 2)
            screen.blit(glyph_s, (bx+cw//2-18, cy0+50))
            stat_icons = {"hp_up":"♥","spd_up":"⚡","dmg_up":"⚔","cd_up":"⏱",
                          "area_up":"◎","crit_up":"★","regen":"✚","pickup":"◉",
                          "xp_mult":"✦","proj_spd":"➤"}
            icon = stat_icons.get(upg.get("id",""),"?")
            ic_s = fonts["big"].render(icon, True, C_WHITE)
            screen.blit(ic_s, (bx+cw//2-ic_s.get_width()//2, cy0+52))

        # Nom
        nom_s = fonts["card"].render(upg["nom"], True, C_WHITE)
        screen.blit(nom_s, (bx+cw//2-nom_s.get_width()//2, cy0+100))

        # Description
        words = upg["desc"].split()
        lines, line = [], ""
        for word in words:
            test = (line+" "+word).strip()
            if fonts["small"].size(test)[0] < cw-16:
                line = test
            else:
                lines.append(line); line = word
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            d = fonts["small"].render(ln, True, C_GREY)
            screen.blit(d, (bx+cw//2-d.get_width()//2, cy0+124+j*20))

        # Touche
        key_s = fonts["big"].render(str(i+1), True, col)
        screen.blit(key_s, (bx+cw//2-key_s.get_width()//2, cy0+ch-32))

    # Reroll
    reroll_col = C_GOLD if gs.gold >= xp.reroll_cost else (80,70,70)
    rc = fonts["small"].render(
        f"[R] Reroll  —  {xp.reroll_cost} or     (Or disponible : {gs.gold})",
        True, reroll_col)
    screen.blit(rc, (cx-rc.get_width()//2, cy0+ch+18))



#  GAME OVER


def draw_game_over():
    screen.fill(C_DARK)
    cx, cy = WIDTH//2, HEIGHT//3

    # Particules de fond
    random.seed(42)
    for _ in range(80):
        sx = random.randint(0,WIDTH); sy = random.randint(0,HEIGHT)
        pygame.draw.circle(screen,(80,10,10,180),(sx,sy),random.randint(1,3))

    def bc(t,f,c,y):
        s=f.render(t,True,c); screen.blit(s,(cx-s.get_width()//2,y))

    bc("GAME OVER",                   fonts["title"], C_RED,   cy)
    bc(f"Score : {gs.score}",         fonts["big"],   C_WHITE, cy+72)
    bc(f"Or gagne : {gs.gold}",       fonts["big"],   C_GOLD,  cy+108)
    if gs.wave_manager:
        bc(f"Temps survecu : {gs.wave_manager.time_str()}",
           fonts["med"], C_GREY, cy+146)
    bc("ENTREE → rejouer   |   ECHAP → menu", fonts["small"], C_GREY, cy+190)



#  GESTION DES EVENEMENTS


def handle_menu(event):
    if event.type != pygame.KEYDOWN: return
    if event.key == pygame.K_RETURN:
        gs.screen_state = "weapon_select"
    elif event.key == pygame.K_1 and gs.gold >= 100:
        gs.gold -= 100; gs._speed_bonus = getattr(gs,"_speed_bonus",0)+0.4
    elif event.key == pygame.K_2 and gs.gold >= 100:
        gs.gold -= 100; gs.gold_gain += 3
    elif event.key == pygame.K_3 and gs.gold >= 100:
        gs.gold -= 100; gs._hp_bonus = getattr(gs,"_hp_bonus",0)+20


def handle_weapon_select(event, layout):
    keys = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2,
            pygame.K_4:3, pygame.K_5:4, pygame.K_6:5}
    if event.type == pygame.KEYDOWN and event.key in keys:
        idx = keys[event.key]
        if idx < len(START_WEAPONS):
            _launch(START_WEAPONS[idx])
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        wid = get_weapon_clicked(event.pos, layout)
        if wid: _launch(wid)


def handle_playing(event):
    player = gs.player
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE: gs.screen_state = "menu"


def _update_movement():
    """Appele chaque frame — lit l'etat reel des touches au lieu de flags."""
    if gs.player is None: return
    if gs.screen_state not in ("playing", "level_up"): return
    keys = pygame.key.get_pressed()
    p = gs.player
    # En level_up le mouvement est tres reduit (gere dans physics)
    p.move_left  = bool(keys[pygame.K_q])
    p.move_right = bool(keys[pygame.K_d])
    p.move_up    = bool(keys[pygame.K_z])
    p.move_down  = bool(keys[pygame.K_s])


def handle_level_up(event):
    if event.type != pygame.KEYDOWN: return
    xp = gs.xp_system
    key_map = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2}
    idx = key_map.get(event.key)
    if idx is not None and xp and xp.pending_offer:
        if idx < len(xp.pending_offer):
            xp.apply_choice(idx, gs.player, gs)
            if not xp.pending_offer:
                gs.screen_state = "playing"
    elif event.key == pygame.K_r and xp:
        if gs.gold >= xp.reroll_cost:
            gs.gold -= xp.reroll_cost
            xp.reroll(gs.player)
    elif event.key == pygame.K_ESCAPE:
        gs.screen_state = "menu"


def handle_level_up_keyup(event):
    pass   # Plus necessaire — _update_movement lit les touches en temps reel


def handle_game_over(event):
    if event.type != pygame.KEYDOWN: return
    if event.key == pygame.K_ESCAPE: gs.screen_state = "menu"
    elif event.key == pygame.K_RETURN: gs.screen_state = "weapon_select"


def handle_victory(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        gs.screen_state = "menu"



#  HELPERS


def _launch(weapon):
    gs.start_new_game(weapon)
    # Applique les bonus meta
    speed_b = getattr(gs, "_speed_bonus", 0)
    hp_b    = getattr(gs, "_hp_bonus",    0)
    if speed_b: gs.player.speed   += speed_b
    if hp_b:    gs.player.max_hp  += hp_b; gs.player.hp = gs.player.max_hp


#  BOUCLE PRINCIPALE


def main():
    weapon_layout = None

    while True:
        clock.tick(FPS)
        state = gs.screen_state

        # ── Events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if state == "menu":
                handle_menu(event)
            elif state == "weapon_select":
                handle_weapon_select(event, weapon_layout)
            elif state == "playing":
                handle_playing(event)
            elif state == "level_up":
                if event.type == pygame.KEYDOWN:
                    handle_level_up(event)
                elif event.type == pygame.KEYUP:
                    handle_level_up_keyup(event)
            elif state == "game_over":
                handle_game_over(event)
            elif state == "victory":
                handle_victory(event)

        # ── Update & Draw ──
        state = gs.screen_state   # peut avoir change dans les events

        # Lecture des touches de mouvement a chaque frame (evite les touches bloquees)
        _update_movement()

        if state in ("playing", "level_up"):
            alive = update(gs)
            if not alive and gs.screen_state not in ("game_over","victory"):
                gs.screen_state = "game_over"
            draw_game(screen, gs, fonts)
            if gs.screen_state == "level_up":
                draw_level_up()

        elif state == "menu":
            draw_menu()

        elif state == "weapon_select":
            weapon_layout = draw_weapon_select()

        elif state == "game_over":
            draw_game_over()

        elif state == "victory":
            draw_victory(screen, gs, fonts)

        pygame.display.flip()


if __name__ == "__main__":
    main()
