"""
physics.py — Toute la logique de mise a jour du jeu.

Fonctions :
  update(gs)        — point d'entree principal appele chaque frame
  do_attack(gs)     — declenche une attaque selon l'arme equipee
  _update_enemies   — deplacement + attaque des ennemis
  _resolve_push     — separation physique joueur/ennemis
  _update_arrows    — deplacement + collision des fleches
  _update_baskets   — detection contact paniers
"""

import math
import pygame

from settings import (
    MAP_W, MAP_H,
    PLAYER_W, PLAYER_H,
    ENEMY_W, ENEMY_H, ENEMY_SPEED, ENEMY_ATK_SPEED,
    SPAWN_INTERVAL, MAX_ENEMIES,
    ARROW_KNOCKBACK, ARROW_KB_RESIST,
    ENEMY_MASS,
    WEAPONS,
)
from entities import Rect, Arrow, Enemy



#  POINT D'ENTREE


def update(gs) -> bool:
    """
    Met a jour tout l'etat de la partie pour une frame.
    Retourne False si le joueur est mort (game over), True sinon.
    """
    player = gs.player
    now    = pygame.time.get_ticks()

    # Deplacement joueur
    player.move()
    player.clamp()

    # Angle de visee vers la souris
    cam_x, cam_y = gs.get_camera()
    player.update_aim(pygame.mouse.get_pos(), cam_x, cam_y)

    # Tir continu arc (clic maintenu)
    if player.mouse_held and WEAPONS[player.weapon]["type"] == "range":
        do_attack(gs)
    # Tir continu armes cc (clic maintenu)
    if player.mouse_held and WEAPONS[player.weapon]["type"] == "melee":
        do_attack(gs)
    # Spawn ennemis
    gs.tick_spawn(now, SPAWN_INTERVAL, MAX_ENEMIES)

    # Logique ennemis
    alive = _update_enemies(gs, now)
    if not alive:
        return False

    # Separation physique joueur/ennemis
    _resolve_push(gs)

    # Fleches
    _update_arrows(gs)

    # Paniers de fruits
    _update_baskets(gs)

    return True



#  ATTAQUE


def do_attack(gs):
    """Declenche une attaque (melee ou fleche) selon l'arme equipee."""
    player = gs.player
    now    = pygame.time.get_ticks()
    w      = WEAPONS[player.weapon]

    # Cooldown
    if now - player.attack_last < w["cooldown"]:
        return
    player.attack_last = now

    if w["type"] == "range":
        _fire_arrow(gs)
    else:
        _melee_attack(gs, w, now)


def _fire_arrow(gs):
    """Cree une fleche depuis le joueur vers la souris."""
    cam_x, cam_y = gs.get_camera()
    arrow = Arrow.create(gs.player, cam_x, cam_y)
    if arrow:
        gs.arrows.append(arrow)


def _melee_attack(gs, weapon: dict, now: int):
    """Applique une attaque melee dans la direction visee."""
    player = gs.player
    player.attack_active = True
    player.attack_start  = now

    pcx, pcy = player.center()
    a        = player.aim_angle
    reach    = weapon["portee"] 
    hw       = weapon["largeur"] * 2

    # Hitbox d'attaque devant le joueur
    hcx = pcx + math.cos(a) * (reach / 2 + PLAYER_W )
    hcy = pcy + math.sin(a) * (reach / 2 + PLAYER_H )
    atk = Rect(hcx - hw, hcy - reach / 2, hw * 2, reach)

    dead = []
    for i, enemy in enumerate(gs.enemies):
        if atk.collides(enemy.hitbox()):
            enemy.hp -= weapon["degats"]
            enemy.apply_knockback(a, weapon["knockback"])
            if enemy.is_dead():
                dead.append(i)

    for i in reversed(dead):
        gs.enemies.pop(i)
        gs.on_kill()



#  ENNEMIS


def _update_enemies(gs, now: int) -> bool:
    """
    Deplace les ennemis et leur fait infliger des degats au contact.
    Retourne False si le joueur est mort.
    """
    player    = gs.player
    pcx, pcy  = player.center()
    ph        = player.hitbox()

    for enemy in gs.enemies:
        # Deplacement vers le joueur
        enemy.move_toward(pcx, pcy)

        # Degats au contact
        if ph.collides(enemy.hitbox()) and enemy.can_attack(now):
            enemy.last_atk = now
            player.hp -= 1
            if not player.is_alive():
                return False

    return True



#  COLLISION PHYSIQUE JOUEUR / ENNEMIS


def _resolve_push(gs):
    """
    Separe le joueur et les ennemis quand ils se chevauchent.
    L'ennemi absorbe ENEMY_MASS de la correction, le joueur le reste.
    """
    player = gs.player
    ph     = player.hitbox()

    for enemy in gs.enemies:
        eh = enemy.hitbox()
        if not ph.collides(eh):
            continue

        ox, oy = ph.overlap(eh)

        if ox < oy:
            d = 1 if ph.center()[0] < eh.center()[0] else -1
            player.x -= d * ox * (1 - ENEMY_MASS)
            enemy.x  += d * ox * ENEMY_MASS
        else:
            d = 1 if ph.center()[1] < eh.center()[1] else -1
            player.y -= d * oy * (1 - ENEMY_MASS)
            enemy.y  += d * oy * ENEMY_MASS

        player.clamp()
        enemy.clamp()
        ph = player.hitbox()   # recalcule apres correction


#  FLECHES

def _update_arrows(gs):
    """Deplace les fleches et teste les collisions avec les ennemis."""
    to_remove = []

    for i, arrow in enumerate(gs.arrows):
        arrow.update()

        if not arrow.in_bounds():
            to_remove.append(i)
            continue

        ar   = arrow.hitbox()
        hit  = False
        dead = []

        for j, enemy in enumerate(gs.enemies):
            if ar.collides(enemy.hitbox()):
                # Degats
                enemy.hp -= WEAPONS["arc"]["degats"]

                # Knockback reduit
                kb   = ARROW_KNOCKBACK * ARROW_KB_RESIST
                dist = math.hypot(arrow.vx, arrow.vy)
                if dist:
                    enemy.x += (arrow.vx / dist) * kb
                    enemy.y += (arrow.vy / dist) * kb
                    enemy.clamp()

                if enemy.is_dead():
                    dead.append(j)

                hit = True
                break   # une fleche ne touche qu'un ennemi

        for j in reversed(dead):
            gs.enemies.pop(j)
            gs.on_kill()

        if hit:
            to_remove.append(i)

    for i in reversed(to_remove):
        gs.arrows.pop(i)



#  PANIERS DE FRUITS


def _update_baskets(gs):
    """Soigne le joueur s'il marche sur un panier actif."""
    for basket in gs.baskets:
        basket.try_heal(gs.player)
