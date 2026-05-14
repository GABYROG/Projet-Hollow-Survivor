"""
main.py — Point d'entree. Boucle principale + tous les ecrans.

Ordre des ecrans :
  menu → weapon_select → map_select → playing / level_up → game_over / victory

Lancer : python main.py
"""

import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
pygame.init()

from settings   import (WIDTH, HEIGHT, FPS, WEAPONS, WEAPON_ORDER,
                         C_WHITE, C_GOLD, C_RED, C_GREEN, C_ORANGE,
                         C_GREY, C_GREY_DARK, C_DARK, C_HUD_BG, load_fonts)
from world      import MapData, LavaMapData, SwampMapData
from game_state import GameState
from physics    import update
from renderer   import draw_game, draw_victory, draw_weapon_icon
from experience import RARITY_COLORS

# ── Init ──
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trial of Death  —  Vampire Style")
clock  = pygame.time.Clock()
fonts  = load_fonts()

print("Chargement des maps...")
_map_foret  = MapData()
_map_volcan = LavaMapData()
_map_marecage = SwampMapData()
print("Maps chargees !")

gs = GameState(_map_foret)


#  DEFINITION DES MAPS


MAPS = [
    {
        "id":       "foret",
        "nom":      "Foret Maudite",
        "desc":     "La map classique. Herbe, arbres et chemins de terre.",
        "bonus":    "+10% XP gagnee",
        "malus":    "Aucun",
        "couleur":  (60, 160, 60),
        "bg":       (20, 45, 20),
        "icon_col": (80, 200, 80),
        "data":     None,   # rempli apres init
        "xp_mult":  1.10,
        "dmg_mult": 1.00,
        "spd_mult": 1.00,
    },
    {
        "id":       "volcan",
        "nom":      "Terres de Lave",
        "desc":     "Sol volcanique. Les ennemis sont plus forts mais valent plus d'or.",
        "bonus":    "+30% or par kill",
        "malus":    "Ennemis +20% PV",
        "couleur":  (210, 70, 10),
        "bg":       (45, 12, 5),
        "icon_col": (255, 120, 30),
        "data":     None,
        "xp_mult":  1.00,
        "dmg_mult": 1.00,
        "spd_mult": 1.00,
        "gold_mult":1.30,
        "enemy_hp_mult": 1.20,
    },
    {
        "id":       "marecage",
        "nom":      "Marecage Sombre",
        "desc":     "Brume epaisse. Le joueur est plus lent mais fait plus de degats.",
        "bonus":    "+25% degats",
        "malus":    "-15% vitesse de deplacement",
        "couleur":  (80, 120, 90),
        "bg":       (15, 28, 20),
        "icon_col": (100, 200, 130),
        "data":     None,
        "xp_mult":  1.00,
        "dmg_mult": 1.25,
        "spd_mult": 0.85,
    },
]

# Assigne les datas map
MAPS[0]["data"] = _map_foret
MAPS[1]["data"] = _map_volcan
MAPS[2]["data"] = _map_marecage

# Map selectionnee (index)
_selected_map = 0



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

    now_ms = pygame.time.get_ticks()
    blink  = int(now_ms/600) % 2 == 0
    bc("▶  Appuie sur ENTREE pour jouer", fonts["big"], C_WHITE if blink else C_GREY, 418)
    bc("(les armes attaquent automatiquement)", fonts["small"], C_GREY_DARK, 458)



#  SELECTION D'ARME


CARD_W, CARD_H = 180, 240
CARD_GAP       = 22
START_WEAPONS  = ["epee", "couteau", "arc", "ail", "bible", "fouet"]


def draw_weapon_select():
    screen.fill(C_DARK)
    cx = WIDTH // 2

    def bc(t, f, c, y):
        s = f.render(t, True, c)
        screen.blit(s, (cx - s.get_width()//2, y))

    bc("Choisissez votre arme de depart", fonts["title"], C_GOLD, 32)
    bc("Les armes attaquent seules — collectez les gemmes XP pour monter de niveau",
       fonts["small"], C_GREY, 90)

    total = len(START_WEAPONS)*CARD_W + (len(START_WEAPONS)-1)*CARD_GAP
    sx0   = cx - total//2
    by0   = 120

    for idx, wid in enumerate(START_WEAPONS):
        w   = WEAPONS[wid]
        col = w["couleur"]
        bx  = sx0 + idx*(CARD_W+CARD_GAP)

        bg = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        bg.fill((14, 9, 28, 210))
        screen.blit(bg, (bx, by0))
        pygame.draw.rect(screen, col, (bx, by0, CARD_W, CARD_H), 2, border_radius=6)

        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, 40), (30, 30), 28)
        screen.blit(glow, (bx+CARD_W//2-30, by0+35))
        draw_weapon_icon(screen, wid, bx+CARD_W//2, by0+62, col)

        nm = fonts["card"].render(f"[{idx+1}]  {w['nom']}", True, col)
        screen.blit(nm, (bx+CARD_W//2-nm.get_width()//2, by0+108))

        words = w["desc"].split()
        lines, line = [], ""
        for word in words:
            test = (line+" "+word).strip()
            if fonts["tiny"].size(test)[0] < CARD_W-14: line = test
            else: lines.append(line); line = word
        lines.append(line)
        for j, ln in enumerate(lines[:3]):
            d = fonts["tiny"].render(ln, True, C_GREY)
            screen.blit(d, (bx+CARD_W//2-d.get_width()//2, by0+134+j*16))

        type_labels = {
            "melee_swing":"Corps-a-corps","whip":"Fouet",
            "melee_area":"Zone","melee_orbit":"Orbital","projectile":"Projectile",
        }
        tl  = type_labels.get(w["type"], w["type"])
        tls = fonts["tiny"].render(tl, True, col)
        screen.blit(tls, (bx+CARD_W//2-tls.get_width()//2, by0+CARD_H-22))

    return {"sx0":sx0,"by0":by0,"cw":CARD_W,"ch":CARD_H,"gap":CARD_GAP}


def get_weapon_clicked(pos, layout):
    mx, my = pos
    for idx, wid in enumerate(START_WEAPONS):
        bx = layout["sx0"] + idx*(layout["cw"]+layout["gap"])
        if bx <= mx <= bx+layout["cw"] and layout["by0"] <= my <= layout["by0"]+layout["ch"]:
            return wid
    return None



#  SELECTION DE MAP


MAP_CARD_W = 320
MAP_CARD_H = 340
MAP_CARD_GAP = 36


def draw_map_select():
    """Affiche l'ecran de choix de map. Retourne le layout pour detection clic."""
    screen.fill(C_DARK)
    cx = WIDTH // 2

    def bc(t, f, c, y):
        s = f.render(t, True, c)
        screen.blit(s, (cx - s.get_width()//2, y))

    bc("Choisissez votre terrain", fonts["title"], C_GOLD, 28)
    bc("Chaque map a ses propres bonus et malus", fonts["small"], C_GREY, 84)

    total  = len(MAPS)*MAP_CARD_W + (len(MAPS)-1)*MAP_CARD_GAP
    sx0    = cx - total//2
    by0    = 112

    now = pygame.time.get_ticks()

    for idx, m in enumerate(MAPS):
        bx  = sx0 + idx*(MAP_CARD_W+MAP_CARD_GAP)
        col = m["couleur"]
        bg_col = m["bg"]

        # Fond de la carte avec couleur de la map
        bg = pygame.Surface((MAP_CARD_W, MAP_CARD_H), pygame.SRCALPHA)
        bg.fill((*bg_col, 220))
        screen.blit(bg, (bx, by0))

        # Bordure (pulsante si selectionnee)
        is_hovered = (bx <= pygame.mouse.get_pos()[0] <= bx+MAP_CARD_W and
                      by0 <= pygame.mouse.get_pos()[1] <= by0+MAP_CARD_H)
        border_w = 3 if is_hovered else 2
        pulse_col = tuple(max(0, min(255, c + int(40*math.sin(now/300)))) for c in col)
        pygame.draw.rect(screen, pulse_col if is_hovered else col,
                         (bx, by0, MAP_CARD_W, MAP_CARD_H), border_w, border_radius=8)

        # Miniature de la map (rectangle avec motif)
        mini_x, mini_y = bx+16, by0+16
        mini_w, mini_h = MAP_CARD_W-32, 120
        pygame.draw.rect(screen, bg_col, (mini_x, mini_y, mini_w, mini_h), border_radius=4)
        pygame.draw.rect(screen, col,    (mini_x, mini_y, mini_w, mini_h), 1, border_radius=4)
        _draw_map_preview(screen, m, mini_x, mini_y, mini_w, mini_h, now)

        # Touche
        key_s = fonts["big"].render(f"[{idx+1}]", True, col)
        screen.blit(key_s, (bx+MAP_CARD_W//2-key_s.get_width()//2, by0+148))

        # Nom
        nm = fonts["big"].render(m["nom"], True, C_WHITE)
        screen.blit(nm, (bx+MAP_CARD_W//2-nm.get_width()//2, by0+178))

        # Description
        desc_s = fonts["small"].render(m["desc"], True, C_GREY)
        screen.blit(desc_s, (bx+MAP_CARD_W//2-desc_s.get_width()//2, by0+210))

        # Separateur
        pygame.draw.line(screen, (*col, 100),
                         (bx+20, by0+234), (bx+MAP_CARD_W-20, by0+234), 1)

        # Bonus (vert)
        bonus_icon = fonts["small"].render("✦ " + m["bonus"], True, C_GREEN)
        screen.blit(bonus_icon, (bx+20, by0+244))

        # Malus (rouge)
        malus_icon = fonts["small"].render("✖ " + m["malus"], True, C_RED)
        screen.blit(malus_icon, (bx+20, by0+268))

        # Indicateur clic
        hint_col = col if is_hovered else C_GREY_DARK
        hint_s = fonts["small"].render("Cliquez pour choisir", True, hint_col)
        screen.blit(hint_s, (bx+MAP_CARD_W//2-hint_s.get_width()//2, by0+MAP_CARD_H-28))

    return {"sx0":sx0,"by0":by0,"cw":MAP_CARD_W,"ch":MAP_CARD_H,"gap":MAP_CARD_GAP}


def _draw_map_preview(surf, m, x, y, w, h, now):
    """Dessine une miniature animee de la map dans le rectangle donne."""
    mid = x + w//2

    if m["id"] == "foret":
        # Sol vert avec quelques arbres
        pygame.draw.rect(surf, (80, 140, 60), (x+2, y+h//2, w-4, h//2-2), border_radius=2)
        pygame.draw.rect(surf, (150, 110, 60),(x+2, y+h//2+8, w-4, 8))
        for i, tx in enumerate([x+30, x+80, x+160, x+240, x+290]):
            bob = int(math.sin(now/800 + i) * 2)
            pygame.draw.rect(surf, (70, 45, 25), (tx-3, y+h//2-12+bob, 6, 14))
            pygame.draw.circle(surf, (45,130,45),(tx, y+h//2-20+bob), 14)
            pygame.draw.circle(surf, (65,165,65),(tx-3, y+h//2-26+bob), 9)
        # Fleurs
        for i, (fx, fy, fc) in enumerate([(x+50,y+h//2+4,(255,100,150)),
                                            (x+130,y+h//2+2,(255,220,0)),
                                            (x+200,y+h//2+5,(100,200,255))]):
            pygame.draw.circle(surf, fc, (fx, fy), 3)

    elif m["id"] == "volcan":
        # Sol noir avec veines de lave
        pygame.draw.rect(surf, (28, 10, 5), (x+2, y+2, w-4, h-4), border_radius=2)
        # Chemins de lave
        lava_pulse = int(200 + 55*math.sin(now/400))
        for lx in [x+40, x+120, x+210, x+280]:
            pygame.draw.line(surf, (lava_pulse, 60, 5), (lx, y+h-4), (lx+20, y+4), 4)
        # Rochers
        for rx, ry in [(x+20,y+h-20),(x+90,y+h-16),(x+180,y+h-22),(x+260,y+h-18)]:
            pygame.draw.ellipse(surf, (55, 18, 5), (rx, ry, 24, 14))
            pygame.draw.ellipse(surf, (80, 30, 8), (rx+2, ry+2, 18, 8))
        # Braises flottantes
        for i in range(6):
            bx2 = x + 20 + i*50 + int(math.sin(now/300+i)*8)
            by2 = y + 30 + int(math.sin(now/200+i*1.5)*15)
            pygame.draw.circle(surf, (255, 100+i*20, 0), (bx2, by2), 3)

    elif m["id"] == "marecage":
        # Sol boueux tres sombre
        pygame.draw.rect(surf, (16, 20, 12), (x+2, y+2, w-4, h-4), border_radius=2)
        # Flaques d'eau stagnante
        for wx2, wy2, wr in [(x+35,y+h-20,28),(x+130,y+h-16,20),(x+220,y+h-22,24),(x+290,y+h-14,16)]:
            pygame.draw.ellipse(surf, (18,32,22), (wx2, wy2, wr*2, wr//2))
            pygame.draw.ellipse(surf, (25,42,30), (wx2+2, wy2+1, wr*2-4, wr//2-2), 1)
        # Arbres morts (troncs fins, pas de feuilles)
        for tx2, th2 in [(x+55,18),(x+100,24),(x+175,20),(x+250,22),(x+300,16)]:
            pygame.draw.line(surf, (20,25,15), (tx2, y+h), (tx2+int(math.sin(now/800)*2), y+th2), 2)
            # Branches mortes
            pygame.draw.line(surf, (18,22,13), (tx2, y+th2+8), (tx2-8, y+th2), 1)
            pygame.draw.line(surf, (18,22,13), (tx2, y+th2+8), (tx2+7, y+th2+2), 1)
        # Roseaux
        for rx2, rh2 in [(x+80,28),(x+150,22),(x+200,30),(x+270,25)]:
            pygame.draw.line(surf, (22,38,20), (rx2, y+h), (rx2, y+rh2), 1)
            pygame.draw.ellipse(surf, (30,45,22), (rx2-2, y+rh2-5, 4, 7))
        # Brume verte tres sombre (overlay)
        fog = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(4):
            fx2 = w//5 + i*w//4 + int(math.sin(now/600+i)*12)
            fy2 = h//2 + int(math.cos(now/400+i)*6)
            pygame.draw.circle(fog, (15,28,18,30),(fx2,fy2),50)
        surf.blit(fog, (x, y))
        # Petites bulles de gaz
        for i in range(5):
            bx3 = x + 40 + i*55 + int(math.sin(now/300+i)*5)
            by3 = y + h-8 - int((now//100 + i*20) % (h-16))
            pygame.draw.circle(surf, (20,35,22), (bx3, by3), 2)


def get_map_clicked(pos, layout):
    """Retourne l'index de la map cliquee ou None."""
    mx, my = pos
    for idx in range(len(MAPS)):
        bx = layout["sx0"] + idx*(layout["cw"]+layout["gap"])
        if bx <= mx <= bx+layout["cw"] and layout["by0"] <= my <= layout["by0"]+layout["ch"]:
            return idx
    return None



#  ECRAN LEVEL-UP


def draw_level_up():
    xp    = gs.xp_system
    offer = xp.pending_offer
    if not offer:
        gs.screen_state = "playing"; return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((4, 2, 14, 185))
    screen.blit(overlay, (0, 0))

    band = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
    band.fill((20, 10, 50, 220))
    screen.blit(band, (0, 0))

    cx = WIDTH // 2
    def bc(t, f, c, y):
        s = f.render(t, True, c)
        screen.blit(s, (cx - s.get_width()//2, y))

    bc(f"NIVEAU  {xp.level} !", fonts["title"], C_GOLD, 8)
    pygame.draw.rect(screen, (40,30,80),(40,56,WIDTH-80,6),border_radius=3)
    pygame.draw.rect(screen, C_GOLD,   (40,56,WIDTH-80,6),border_radius=3)
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

        glow_s = pygame.Surface((cw+20, ch+20), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*col, 25),(0,0,cw+20,ch+20),border_radius=10)
        screen.blit(glow_s,(bx-10,cy0-10))

        bg = pygame.Surface((cw, ch), pygame.SRCALPHA)
        bg.fill((10,6,22,230)); screen.blit(bg,(bx,cy0))
        pygame.draw.rect(screen,col,(bx,cy0,cw,ch),2,border_radius=6)

        rar_s = fonts["small"].render(rarity.upper(),True,col)
        screen.blit(rar_s,(bx+cw//2-rar_s.get_width()//2,cy0+8))

        utype = upg.get("type","stat")
        if utype == "weapon_upgrade":
            wid_tag = upg.get("weapon","?")
            lvl_tag = upg.get("level","?")
            w_data  = WEAPONS.get(wid_tag,{})
            tag_col = w_data.get("couleur", C_GREY)
            tag_s   = fonts["tiny"].render(f"{w_data.get('nom',wid_tag).upper()}  niv.{lvl_tag}",True,tag_col)
            screen.blit(tag_s,(bx+cw//2-tag_s.get_width()//2,cy0+28))
            draw_weapon_icon(screen,wid_tag,bx+cw//2,cy0+68,tag_col)
        elif utype == "new_weapon":
            wid_new = upg.get("weapon_id","?")
            w_data  = WEAPONS.get(wid_new,{})
            tag_col = w_data.get("couleur", C_GOLD)
            new_s   = fonts["tiny"].render("NOUVELLE ARME",True,C_GOLD)
            screen.blit(new_s,(bx+cw//2-new_s.get_width()//2,cy0+28))
            draw_weapon_icon(screen,wid_new,bx+cw//2,cy0+68,tag_col)
        elif utype == "item":
            from items import ITEM_DEFS
            defn    = ITEM_DEFS.get(upg.get("item_id",""),{})
            item_col= defn.get("color",(100,100,200))
            icon_s  = fonts["big"].render(defn.get("icon","?"),True,item_col)
            screen.blit(icon_s,(bx+cw//2-icon_s.get_width()//2,cy0+48))
            tag_s   = fonts["tiny"].render("ITEM PASSIF",True,item_col)
            screen.blit(tag_s,(bx+cw//2-tag_s.get_width()//2,cy0+28))
        else:
            glyph_s = pygame.Surface((36,36),pygame.SRCALPHA)
            pygame.draw.circle(glyph_s,(*col,180),(18,18),17)
            pygame.draw.circle(glyph_s,C_WHITE,(18,18),17,2)
            screen.blit(glyph_s,(bx+cw//2-18,cy0+50))
            stat_icons={"hp_up":"♥","spd_up":"⚡","dmg_up":"⚔","cd_up":"⏱",
                        "area_up":"◎","crit_up":"★","regen":"✚","pickup":"◉",
                        "xp_mult":"✦","proj_spd":"➤"}
            icon = stat_icons.get(upg.get("id",""),"?")
            ic_s = fonts["big"].render(icon,True,C_WHITE)
            screen.blit(ic_s,(bx+cw//2-ic_s.get_width()//2,cy0+52))

        nom_s = fonts["card"].render(upg["nom"],True,C_WHITE)
        screen.blit(nom_s,(bx+cw//2-nom_s.get_width()//2,cy0+100))

        words = upg["desc"].split()
        lines, line = [], ""
        for word in words:
            test=(line+" "+word).strip()
            if fonts["small"].size(test)[0]<cw-16: line=test
            else: lines.append(line); line=word
        lines.append(line)
        for j,ln in enumerate(lines[:3]):
            d=fonts["small"].render(ln,True,C_GREY)
            screen.blit(d,(bx+cw//2-d.get_width()//2,cy0+124+j*20))

        key_s=fonts["big"].render(str(i+1),True,col)
        screen.blit(key_s,(bx+cw//2-key_s.get_width()//2,cy0+ch-32))

    reroll_col = C_GOLD if gs.gold >= xp.reroll_cost else (80,70,70)
    rc = fonts["small"].render(
        f"[R] Reroll  —  {xp.reroll_cost} or     (Or disponible : {gs.gold})",
        True, reroll_col)
    screen.blit(rc,(cx-rc.get_width()//2, cy0+ch+18))



#  GAME OVER


def draw_game_over():
    screen.fill(C_DARK)
    cx, cy = WIDTH//2, HEIGHT//3
    def bc(t, f, c, y):
        s=f.render(t,True,c); screen.blit(s,(cx-s.get_width()//2,y))
    bc("GAME OVER",                   fonts["title"], C_RED,   cy)
    bc(f"Score : {gs.score}",         fonts["big"],   C_WHITE, cy+72)
    bc(f"Or gagne : {gs.gold}",       fonts["big"],   C_GOLD,  cy+108)
    if gs.wave_manager:
        bc(f"Temps survecu : {gs.wave_manager.time_str()}", fonts["med"], C_GREY, cy+146)
    bc("ENTREE → rejouer   |   ECHAP → menu", fonts["small"], C_GREY, cy+190)



#  GESTION EVENEMENTS


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
    keys = {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2,
            pygame.K_4:3,pygame.K_5:4,pygame.K_6:5}
    if event.type == pygame.KEYDOWN and event.key in keys:
        idx = keys[event.key]
        if idx < len(START_WEAPONS):
            # Arme choisie → passe a la selection de map
            gs._chosen_weapon = START_WEAPONS[idx]
            gs.screen_state   = "map_select"
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        wid = get_weapon_clicked(event.pos, layout)
        if wid:
            gs._chosen_weapon = wid
            gs.screen_state   = "map_select"


def handle_map_select(event, layout):
    global _selected_map
    keys = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2}
    if event.type == pygame.KEYDOWN and event.key in keys:
        idx = keys.get(event.key)
        if idx is not None and idx < len(MAPS):
            _launch(getattr(gs,"_chosen_weapon","epee"), idx)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        idx = get_map_clicked(event.pos, layout)
        if idx is not None:
            _launch(getattr(gs,"_chosen_weapon","epee"), idx)


def handle_playing(event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE: gs.screen_state = "menu"


def _update_movement():
    if gs.player is None: return
    if gs.screen_state not in ("playing","level_up"): return
    keys = pygame.key.get_pressed()
    p = gs.player
    p.move_left  = bool(keys[pygame.K_q])
    p.move_right = bool(keys[pygame.K_d])
    p.move_up    = bool(keys[pygame.K_z])
    p.move_down  = bool(keys[pygame.K_s])


def handle_level_up(event):
    if event.type != pygame.KEYDOWN: return
    xp = gs.xp_system
    key_map = {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2}
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


def handle_level_up_keyup(event): pass


def handle_game_over(event):
    if event.type != pygame.KEYDOWN: return
    if event.key == pygame.K_ESCAPE:
        gs.screen_state = "menu"
    elif event.key == pygame.K_RETURN:
        gs.screen_state = "weapon_select"


def handle_victory(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        gs.screen_state = "menu"



#  HELPERS

def _launch(weapon, map_idx=0):
    """Lance la partie avec l'arme et la map choisies."""
    m = MAPS[map_idx]

    # Change la map dans le game state
    gs.map_data = m["data"]

    gs.start_new_game(weapon)

    # Applique les bonus meta
    speed_b = getattr(gs,"_speed_bonus",0)
    hp_b    = getattr(gs,"_hp_bonus",0)
    if speed_b: gs.player.speed  += speed_b
    if hp_b:    gs.player.max_hp += hp_b; gs.player.hp = gs.player.max_hp

    # Applique les modificateurs de la map
    gs.player.xp_mult   *= m.get("xp_mult",  1.0)
    gs.player.bonus_dmg  = int(gs.player.bonus_dmg * m.get("dmg_mult", 1.0))
    gs.player.speed     *= m.get("spd_mult",  1.0)
    if m.get("gold_mult"): gs.gold_gain = int(gs.gold_gain * m["gold_mult"])

    # Malus PV ennemis (volcan) stocke dans wave_manager
    gs.wave_manager._enemy_hp_mult = m.get("enemy_hp_mult", 1.0)



#  BOUCLE PRINCIPALE


def main():
    weapon_layout = None
    map_layout    = None

    while True:
        clock.tick(FPS)
        state = gs.screen_state

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if state == "menu":
                handle_menu(event)
            elif state == "weapon_select":
                handle_weapon_select(event, weapon_layout)
            elif state == "map_select":
                handle_map_select(event, map_layout)
            elif state == "playing":
                handle_playing(event)
            elif state == "level_up":
                if event.type == pygame.KEYDOWN: handle_level_up(event)
                elif event.type == pygame.KEYUP:  handle_level_up_keyup(event)
            elif state == "game_over":
                handle_game_over(event)
            elif state == "victory":
                handle_victory(event)

        state = gs.screen_state
        _update_movement()

        if state in ("playing","level_up"):
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
        elif state == "map_select":
            map_layout = draw_map_select()
        elif state == "game_over":
            draw_game_over()
        elif state == "victory":
            draw_victory(screen, gs, fonts)

        pygame.display.flip()


if __name__ == "__main__":
    main()
