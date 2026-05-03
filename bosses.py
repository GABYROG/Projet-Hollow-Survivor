"""
bosses.py — Les 5 boss du jeu, chacun avec un pattern unique.

Boss 1 — Le Berserker  (rapide, charge en ligne droite)
Boss 2 — Le Golem      (tank immense, frappe le sol en zone)
Boss 3 — Le Mage       (tir en spirale + bouclier periodique)
Boss 4 — Le Necromant  (invoque des ennemis, reste loin)
Boss 5 — Le Titan      (combine tout + phase de rage a 50% PV)
"""

import math
import random
import pygame

from settings import MAP_W, MAP_H



#  BASE BOSS


class BaseBoss:
    SIZE    = 80
    COLOR   = (200, 0, 0)
    OUTLINE = (120, 0, 0)
    NAME    = "Boss"
    MAX_HP  = 50

    def __init__(self, px, py):
        # Spawn sur un bord de l'ecran loin du joueur
        side = random.randint(0, 3)
        margin = 150
        if side == 0:   x, y = random.randint(margin, MAP_W-margin), margin
        elif side == 1: x, y = MAP_W-margin, random.randint(margin, MAP_H-margin)
        elif side == 2: x, y = random.randint(margin, MAP_W-margin), MAP_H-margin
        else:           x, y = margin, random.randint(margin, MAP_H-margin)

        self.x, self.y    = float(x), float(y)
        self.hp           = self.MAX_HP
        self.last_atk     = 0
        self.projectiles  = []   # {x,y,vx,vy,dmg,r}
        self.summons      = []   # ennemis invoques (ajoutes a gs.enemies)
        self.phase        = 1    # certains boss ont 2 phases
        self._timer       = 0   # timer interne multi-usage

    def hitbox(self):
        from entities import Rect
        s = self.SIZE
        return Rect(self.x, self.y, s, s)

    def center(self):
        s = self.SIZE
        return self.x + s/2, self.y + s/2

    def is_dead(self): return self.hp <= 0
    def clamp(self):
        s = self.SIZE
        self.x = max(0.0, min(self.x, float(MAP_W-s)))
        self.y = max(0.0, min(self.y, float(MAP_H-s)))

    def apply_knockback(self, angle, force):
        # Les boss resistent au knockback
        self.x += math.cos(angle) * force * 0.1
        self.y += math.sin(angle) * force * 0.1
        self.clamp()

    def move_toward(self, tx, ty, speed):
        bcx, bcy = self.center()
        dx, dy = tx-bcx, ty-bcy
        dist = math.hypot(dx, dy)
        if dist:
            step = min(speed, dist)
            self.x += dx/dist*step; self.y += dy/dist*step
        self.clamp()

    def update(self, pcx, pcy, now, gs):
        """Surcharger dans chaque boss."""
        pass

    def _move_proj(self):
        for p in self.projectiles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
        self.projectiles = [p for p in self.projectiles
                            if 0 <= p["x"] <= MAP_W and 0 <= p["y"] <= MAP_H]



#  BOSS 1 — LE BERSERKER  (rapide, charge)


class BossBerserker(BaseBoss):
    NAME = "Berserker"; COLOR = (255, 80, 0); OUTLINE = (180, 40, 0)
    MAX_HP = 60; SIZE = 60

    def __init__(self, px, py):
        super().__init__(px, py)
        self._charge_vx = 0.0
        self._charge_vy = 0.0
        self._charging  = False
        self._charge_timer = 0

    def update(self, pcx, pcy, now, gs):
        # Phase de rage a 50% PV
        speed = 5.0 if self.hp > self.MAX_HP * 0.5 else 8.0

        if self._charging:
            # Charge en ligne droite pendant 600ms
            self.x += self._charge_vx; self.y += self._charge_vy
            self.clamp()
            if now - self._charge_timer > 600:
                self._charging = False
        else:
            self.move_toward(pcx, pcy, speed)
            # Declenche une charge toutes les 2.5s
            if now - self.last_atk > 2500:
                self.last_atk = now
                bcx, bcy = self.center()
                angle = math.atan2(pcy-bcy, pcx-bcx)
                self._charge_vx = math.cos(angle) * 18
                self._charge_vy = math.sin(angle) * 18
                self._charging  = True
                self._charge_timer = now

        self._move_proj()



#  BOSS 2 — LE GOLEM  (tank, frappe en zone)


class BossGolem(BaseBoss):
    NAME = "Golem"; COLOR = (100, 100, 180); OUTLINE = (50, 50, 120)
    MAX_HP = 150; SIZE = 90

    def __init__(self, px, py):
        super().__init__(px, py)
        self._shockwave_timer = 0

    def update(self, pcx, pcy, now, gs):
        self.move_toward(pcx, pcy, 1.2)

        # Onde de choc toutes les 3s : 8 projectiles en etoile
        if now - self._shockwave_timer > 3000:
            self._shockwave_timer = now
            for i in range(8):
                angle = i * math.pi / 4
                self.projectiles.append({
                    "x": self.x + self.SIZE/2, "y": self.y + self.SIZE/2,
                    "vx": math.cos(angle)*5, "vy": math.sin(angle)*5,
                    "dmg": 2, "r": 10,
                })

        self._move_proj()



#  BOSS 3 — LE MAGE  (spirale + bouclier)


class BossMage(BaseBoss):
    NAME = "Mage"; COLOR = (80, 0, 200); OUTLINE = (40, 0, 140)
    MAX_HP = 80; SIZE = 65

    def __init__(self, px, py):
        super().__init__(px, py)
        self._spiral_angle  = 0.0
        self._spiral_timer  = 0
        self._shield_active = False
        self._shield_timer  = 0
        self._shield_hp     = 0

    def update(self, pcx, pcy, now, gs):
        # Reste a distance ideale
        bcx, bcy = self.center()
        dist = math.hypot(pcx-bcx, pcy-bcy)
        if dist < 280:
            angle = math.atan2(bcy-pcy, bcx-pcx)
            self.x += math.cos(angle)*2.5; self.y += math.sin(angle)*2.5
            self.clamp()
        else:
            self.move_toward(pcx, pcy, 2.0)

        # Bouclier toutes les 15s (absorbe 10 degats)
        if now - self._shield_timer > 15000 and not self._shield_active:
            self._shield_active = True
            self._shield_hp     = 10
            self._shield_timer  = now

        # Spiral de projectiles toutes les 200ms
        if now - self._spiral_timer > 200:
            self._spiral_timer = now
            self._spiral_angle += 0.4
            for offset in (0, math.pi, math.pi/2, 3*math.pi/2):
                a = self._spiral_angle + offset
                self.projectiles.append({
                    "x": bcx, "y": bcy,
                    "vx": math.cos(a)*4, "vy": math.sin(a)*4,
                    "dmg": 1, "r": 7,
                })

        self._move_proj()

    def take_damage(self, dmg):
        if self._shield_active:
            self._shield_hp -= dmg
            if self._shield_hp <= 0:
                self._shield_active = False
        else:
            self.hp -= dmg



#  BOSS 4 — LE NECROMANT  (invoque des ennemis)


class BossNecromant(BaseBoss):
    NAME = "Necromant"; COLOR = (20, 100, 20); OUTLINE = (10, 60, 10)
    MAX_HP = 70; SIZE = 65
    MAX_SUMMONS = 6

    def __init__(self, px, py):
        super().__init__(px, py)
        self._summon_timer = 0
        self._teleport_timer = 0
        self.summon_count = 0

    def update(self, pcx, pcy, now, gs):
        # Teleportation toutes les 8s (loin du joueur)
        if now - self._teleport_timer > 8000:
            self._teleport_timer = now
            for _ in range(50):
                nx = random.randint(100, MAP_W-100)
                ny = random.randint(100, MAP_H-100)
                if math.hypot(nx-pcx, ny-pcy) > 400:
                    self.x, self.y = float(nx), float(ny)
                    break

        # Invocation toutes les 4s (max 6 en meme temps)
        if now - self._summon_timer > 4000 and self.summon_count < self.MAX_SUMMONS:
            self._summon_timer = now
            from entities import BasicEnemy
            for _ in range(2):
                e = BasicEnemy.spawn_at_border(pcx, pcy)
                if e:
                    gs.enemies.append(e)
                    self.summon_count += 1

        # Projectiles en vollee toutes les 3s
        if now - self.last_atk > 3000:
            self.last_atk = now
            bcx, bcy = self.center()
            angle = math.atan2(pcy-bcy, pcx-bcx)
            for spread in (-0.3, 0, 0.3):
                a = angle + spread
                self.projectiles.append({
                    "x": bcx, "y": bcy,
                    "vx": math.cos(a)*5, "vy": math.sin(a)*5,
                    "dmg": 1, "r": 7,
                })

        self._move_proj()


#  BOSS 5 — LE TITAN  (tout combine + phase rage)


class BossTitan(BaseBoss):
    NAME = "TITAN"; COLOR = (180, 0, 180); OUTLINE = (100, 0, 100)
    MAX_HP = 250; SIZE = 100

    def __init__(self, px, py):
        super().__init__(px, py)
        self._spiral_angle  = 0.0
        self._spiral_timer  = 0
        self._charge_vx     = 0.0
        self._charge_vy     = 0.0
        self._charging      = False
        self._charge_timer  = 0
        self._summon_timer  = 0
        self._rage          = False   # active a 50% PV

    def update(self, pcx, pcy, now, gs):
        # Phase rage
        if not self._rage and self.hp <= self.MAX_HP * 0.5:
            self._rage = True

        speed = 4.0 if not self._rage else 7.0

        # Charge
        if self._charging:
            self.x += self._charge_vx; self.y += self._charge_vy
            self.clamp()
            if now - self._charge_timer > 500:
                self._charging = False
        else:
            self.move_toward(pcx, pcy, speed)
            if now - self._charge_timer > 2000:
                self._charge_timer = now
                bcx, bcy = self.center()
                a = math.atan2(pcy-bcy, pcx-bcx)
                self._charge_vx = math.cos(a) * 20
                self._charge_vy = math.sin(a) * 20
                self._charging  = True

        # Spirale (plus dense en phase rage)
        interval = 150 if self._rage else 300
        if now - self._spiral_timer > interval:
            self._spiral_timer = now
            self._spiral_angle += 0.5
            bcx, bcy = self.center()
            arms = 6 if self._rage else 3
            for i in range(arms):
                a = self._spiral_angle + i*(2*math.pi/arms)
                self.projectiles.append({
                    "x": bcx, "y": bcy,
                    "vx": math.cos(a)*5, "vy": math.sin(a)*5,
                    "dmg": 2, "r": 9,
                })

        # Invocation en phase rage uniquement
        if self._rage and now - self._summon_timer > 5000:
            self._summon_timer = now
            from entities import FastEnemy
            for _ in range(3):
                e = FastEnemy.spawn_at_border(pcx, pcy)
                if e: gs.enemies.append(e)

        self._move_proj()



#  TABLE DES BOSS (ordre d'apparition)


BOSS_SEQUENCE = [
    BossBerserker,
    BossGolem,
    BossMage,
    BossNecromant,
    BossTitan,
]
