"""
entities.py — Classes representant chaque entite du jeu.

Classes :
  Rect    — hitbox rectangulaire avec detection de collision
  Player  — joueur (position, PV, mouvement, arme,exp)
  Enemy   — ennemi (position, PV, IA basique)
  Arrow   — projectile tire par l'arc
  Basket  — panier de fruits (soin)
"""

import math
import random
import pygame

from settings import (
    MAP_W, MAP_H,
    PLAYER_W, PLAYER_H, PLAYER_SPEED, PLAYER_MAX_HP,
    ENEMY_W, ENEMY_H, ENEMY_SPEED, ENEMY_HP_MAX, ENEMY_ATK_SPEED,
    ARROW_SPEED,
    BASKET_W, BASKET_H, BASKET_HEAL,
    SAFE_RADIUS,
)



#  HITBOX


class Rect:
    """Hitbox rectangulaire axe-alignee (AABB)."""

    def __init__(self, x: float, y: float, w: float, h: float):
        self.x, self.y, self.w, self.h = x, y, w, h

    def collides(self, other: "Rect") -> bool:
        return (
            self.x < other.x + other.w and self.x + self.w > other.x and
            self.y < other.y + other.h and self.y + self.h > other.y
        )

    def center(self) -> tuple:
        return self.x + self.w / 2, self.y + self.h / 2

    def overlap(self, other: "Rect") -> tuple:
        """Retourne la penetration minimale (ox, oy) entre deux Rect."""
        ox = min(self.x + self.w, other.x + other.w) - max(self.x, other.x)
        oy = min(self.y + self.h, other.y + other.h) - max(self.y, other.y)
        return ox, oy



#  JOUEUR

class Player:
    """Represente le personnage controle par le joueur."""

    def __init__(self):
        self.x          = float(MAP_W // 2)
        self.y          = float(MAP_H // 2)
        self.speed      = PLAYER_SPEED
        self.max_hp     = PLAYER_MAX_HP
        self.hp         = self.max_hp
        self.aim_angle  = 0.0

        # Touches de deplacement actives
        self.move_left  = False
        self.move_right = False
        self.move_up    = False
        self.move_down  = False

        # Arme equiper
        self.weapon         = "epee"
        self.attack_active  = False
        self.attack_start   = 0    
        self.attack_last    = 0    
        self.mouse_held     = False 

    def hitbox(self) -> Rect:
        return Rect(self.x, self.y, PLAYER_W, PLAYER_H)

    def center(self) -> tuple:
        return self.x + PLAYER_W / 2, self.y + PLAYER_H / 2

    def move(self):
        """Applique le deplacement selon les touches actives."""
        if self.move_left  and self.x > 0:              self.x -= self.speed
        if self.move_right and self.x < MAP_W - PLAYER_W: self.x += self.speed
        if self.move_up    and self.y > 0:              self.y -= self.speed
        if self.move_down  and self.y < MAP_H - PLAYER_H: self.y += self.speed

    def update_aim(self, mouse_pos: tuple, cam_x: int, cam_y: int):
        """Recalcule l'angle de visee vers la souris."""
        mx, my = mouse_pos
        pcx, pcy = self.center()
        self.aim_angle = math.atan2((my + cam_y) - pcy, (mx + cam_x) - pcx)

    def clamp(self):
        """Empeche le joueur de sortir de la map."""
        self.x = max(0.0, min(self.x, float(MAP_W - PLAYER_W)))
        self.y = max(0.0, min(self.y, float(MAP_H - PLAYER_H)))

    def is_alive(self) -> bool:
        return self.hp > 0



#  ENNEMI


class Enemy:
    """Un ennemi qui pourchasse le joueur."""

    def __init__(self, x: float, y: float):
        self.x        = x
        self.y        = y
        self.hp       = ENEMY_HP_MAX
        self.last_atk = 0  

    def hitbox(self) -> Rect:
        return Rect(self.x, self.y, ENEMY_W, ENEMY_H)

    def center(self) -> tuple:
        return self.x + ENEMY_W / 2, self.y + ENEMY_H / 2

    def move_toward(self, tx: float, ty: float):
        """Avance vers la cible (tx, ty)."""
        ecx, ecy = self.center()
        dx, dy   = tx - ecx, ty - ecy
        dist     = math.hypot(dx, dy)
        if dist:
            step = min(ENEMY_SPEED, dist)
            self.x += dx / dist * step
            self.y += dy / dist * step

    def apply_knockback(self, angle: float, force: float):
        self.x += math.cos(angle) * force
        self.y += math.sin(angle) * force
        self.clamp()

    def clamp(self):
        self.x = max(0.0, min(self.x, float(MAP_W - ENEMY_W)))
        self.y = max(0.0, min(self.y, float(MAP_H - ENEMY_H)))

    def can_attack(self, now: int) -> bool:
        return now - self.last_atk >= ENEMY_ATK_SPEED

    def is_dead(self) -> bool:
        return self.hp <= 0

    @staticmethod
    def spawn_far_from(px: float, py: float) -> "Enemy | None":
        """Cree un ennemi a distance aleatoire du joueur. Retourne None si echec."""
        for _ in range(200):
            x = random.randint(0, MAP_W - ENEMY_W)
            y = random.randint(0, MAP_H - ENEMY_H)
            if 300 < math.hypot(x - px, y - py) < 3000:
                return Enemy(float(x), float(y))
        return None



#  FLECHE


class Arrow:
    """Projectile tire par l'arc."""

    SIZE = 4   # demi-taille de la hitbox

    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x     = x
        self.y     = y
        self.vx    = vx
        self.vy    = vy
        self.angle = math.atan2(vy, vx)

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def hitbox(self) -> Rect:
        s = self.SIZE
        return Rect(self.x - s, self.y - s, s * 2, s * 2)

    def in_bounds(self) -> bool:
        return 0 <= self.x <= MAP_W and 0 <= self.y <= MAP_H

    @staticmethod
    def create(player: Player, cam_x: int, cam_y: int) -> "Arrow | None":
        """Cree une fleche depuis le joueur vers la souris."""
        mx, my   = pygame.mouse.get_pos()
        pcx, pcy = player.center()
        tx, ty   = mx + cam_x, my + cam_y
        d        = math.hypot(tx - pcx, ty - pcy)
        if d == 0:
            return None
        vx = (tx - pcx) / d * ARROW_SPEED
        vy = (ty - pcy) / d * ARROW_SPEED
        return Arrow(pcx, pcy, vx, vy)



#  PANIER DE FRUITS


class Basket:
    """Panier de fruits qui soigne le joueur au contact."""

    def __init__(self, x: float, y: float):
        self.x      = x
        self.y      = y
        self.active = True

    def hitbox(self) -> Rect:
        return Rect(self.x - BASKET_W // 2, self.y - BASKET_H // 2, BASKET_W, BASKET_H)

    def try_heal(self, player: Player) -> bool:
        """
        Soigne le joueur s'il touche le panier.
        Retourne True si le soin a ete applique.
        """
        if not self.active:
            return False
        if player.hitbox().collides(self.hitbox()):
            player.hp = min(player.max_hp, player.hp + BASKET_HEAL)
            self.active = False
            return True
        return False

    def reset(self):
        self.active = True
