"""
bosses.py — Les 5 boss du jeu (versions renforcées).

Modifications :
  - HP x10, dégâts augmentés sur tous les boss
  - Berserker : ne colle plus (cooldown de charge + séparation physique)
  - Mage : attaque de zone (nova) en plus de la spirale
  - Tous les boss spawns plus rapidement (BOSS_TIMES dans wave_manager)
"""

import math, random, pygame
from settings import MAP_W, MAP_H



#  BASE BOSS

class BaseBoss:
    SIZE    = 80
    COLOR   = (200, 0, 0)
    OUTLINE = (120, 0, 0)
    NAME    = "Boss"
    MAX_HP  = 500   # base x10 vs avant

    def __init__(self, px, py):
        side = random.randint(0, 3)
        margin = 150
        if   side == 0: x, y = random.randint(margin, MAP_W-margin), margin
        elif side == 1: x, y = MAP_W-margin, random.randint(margin, MAP_H-margin)
        elif side == 2: x, y = random.randint(margin, MAP_W-margin), MAP_H-margin
        else:           x, y = margin, random.randint(margin, MAP_H-margin)

        self.x, self.y   = float(x), float(y)
        self.hp          = self.MAX_HP
        self.last_atk    = 0
        self.projectiles = []
        self.phase       = 1
        self._timer      = 0

    def hitbox(self):
        from entities import Rect
        return Rect(self.x, self.y, self.SIZE, self.SIZE)

    def center(self):
        s = self.SIZE
        return self.x + s/2, self.y + s/2

    def is_dead(self): return self.hp <= 0

    def clamp(self):
        s = self.SIZE
        self.x = max(0.0, min(self.x, float(MAP_W-s)))
        self.y = max(0.0, min(self.y, float(MAP_H-s)))

    def apply_knockback(self, angle, force):
        # Boss résistants au knockback (5% seulement)
        self.x += math.cos(angle) * force * 0.05
        self.y += math.sin(angle) * force * 0.05
        self.clamp()

    def move_toward(self, tx, ty, speed):
        bcx, bcy = self.center()
        dx, dy = tx-bcx, ty-bcy
        dist = math.hypot(dx, dy)
        if dist > 1:
            step = min(speed, dist)
            self.x += dx/dist*step
            self.y += dy/dist*step
        self.clamp()

    def update(self, pcx, pcy, now, gs):
        pass

    def _move_proj(self):
        for p in self.projectiles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
        self.projectiles = [p for p in self.projectiles
                            if 0 <= p["x"] <= MAP_W and 0 <= p["y"] <= MAP_H]



#  BOSS 1 — BERSERKER  (charge + pas de collage)


class BossBerserker(BaseBoss):
    NAME = "Berserker"; COLOR = (255, 80, 0); OUTLINE = (180, 40, 0)
    MAX_HP = 600; SIZE = 60

    def __init__(self, px, py):
        super().__init__(px, py)
        self._charge_vx    = 0.0
        self._charge_vy    = 0.0
        self._charging     = False
        self._charge_timer = 0
        self._retreat_timer= 0   # temps de recul après charge

    def update(self, pcx, pcy, now, gs):
        speed = 1.5 if self.hp > self.MAX_HP * 0.5 else 7.0
        bcx, bcy = self.center()
        dist_to_player = math.hypot(pcx-bcx, pcy-bcy)

        if self._charging:
            self.x += self._charge_vx
            self.y += self._charge_vy
            self.clamp()

            # Dégâts au joueur si collision pendant la charge
            from entities import Rect
            ph   = gs.player.hitbox()
            bh   = self.hitbox()
            if ph.collides(bh) and now - self.last_atk > 300:
                self.last_atk = now
                charge_dmg = 35 if self.hp > self.MAX_HP*0.5 else 55
                gs.player.take_damage(charge_dmg, now)
                gs.camera_shake = max(gs.camera_shake, 12)
                # La charge s'arrête au contact
                self._charging      = False
                self._retreat_timer = now
                self._push_away_from_player(pcx, pcy, min_dist=100)

            elif now - self._charge_timer > 500:
                self._charging      = False
                self._retreat_timer = now
                self._push_away_from_player(pcx, pcy, min_dist=90)

        elif now - self._retreat_timer < 400:
            # Recul bref après charge : s'éloigne un peu
            angle = math.atan2(bcy-pcy, bcx-pcx)
            self.x += math.cos(angle) * 3
            self.y += math.sin(angle) * 3
            self.clamp()

        else:
            # Déclenche une charge toutes les 2s si assez loin
            if now - self.last_atk > 2000 and dist_to_player > 150:
                self.last_atk   = now
                angle = math.atan2(pcy-bcy, pcx-bcx)
                self._charge_vx = math.cos(angle) * (20 if self.hp > self.MAX_HP*0.5 else 28)
                self._charge_vy = math.sin(angle) * (20 if self.hp > self.MAX_HP*0.5 else 28)
                self._charging      = True
                self._charge_timer  = now

        self._move_proj()



#  BOSS 2 — GOLEM  (onde de choc + pilons)


class BossGolem(BaseBoss):
    NAME = "Golem"; COLOR = (100, 100, 180); OUTLINE = (50, 50, 120)
    MAX_HP = 1500; SIZE = 90

    def __init__(self, px, py):
        super().__init__(px, py)
        self._shockwave_timer = 0
        self._slam_timer      = 0

    def update(self, pcx, pcy, now, gs):
        self.move_toward(pcx, pcy, 1.4)

        # Onde de choc toutes les 2.5s : 8 projectiles
        if now - self._shockwave_timer > 2500:
            self._shockwave_timer = now
            for i in range(8):
                angle = i * math.pi / 4
                self.projectiles.append({
                    "x": self.x+self.SIZE/2, "y": self.y+self.SIZE/2,
                    "vx": math.cos(angle)*6, "vy": math.sin(angle)*6,
                    "dmg": 15, "r": 12,
                })

        # Pilon ciblé toutes les 4s : 3 projectiles vers le joueur
        if now - self._slam_timer > 4000:
            self._slam_timer = now
            bcx, bcy = self.center()
            base_angle = math.atan2(pcy-bcy, pcx-bcx)
            for off in (-0.2, 0, 0.2):
                a = base_angle + off
                self.projectiles.append({
                    "x": bcx, "y": bcy,
                    "vx": math.cos(a)*8, "vy": math.sin(a)*8,
                    "dmg": 20, "r": 14,
                })

        self._move_proj()



#  BOSS 3 — MAGE  (spirale + nova de zone + bouclier)


class BossMage(BaseBoss):
    NAME = "Mage"; COLOR = (80, 0, 200); OUTLINE = (40, 0, 140)
    MAX_HP = 800; SIZE = 65

    def __init__(self, px, py):
        super().__init__(px, py)
        self._spiral_angle  = 0.0
        self._spiral_timer  = 0
        self._nova_timer    = 0   # attaque de zone nova
        self._shield_active = False
        self._shield_timer  = 0
        self._shield_hp     = 0

    def update(self, pcx, pcy, now, gs):
        bcx, bcy = self.center()
        dist = math.hypot(pcx-bcx, pcy-bcy)

        # Maintient distance
        if dist < 260:
            angle = math.atan2(bcy-pcy, bcx-pcx)
            self.x += math.cos(angle)*3.0
            self.y += math.sin(angle)*3.0
            self.clamp()
        elif dist > 320:
            self.move_toward(pcx, pcy, 2.5)

        # Bouclier toutes les 12s
        if now - self._shield_timer > 12000 and not self._shield_active:
            self._shield_active = True
            self._shield_hp     = 40   # absorbe plus de dégâts
            self._shield_timer  = now

        # Spirale toutes les 180ms (plus rapide)
        if now - self._spiral_timer > 180:
            self._spiral_timer = now
            self._spiral_angle += 0.35
            bcx2, bcy2 = self.center()
            for offset in (0, math.pi, math.pi/2, 3*math.pi/2):
                a = self._spiral_angle + offset
                self.projectiles.append({
                    "x": bcx2, "y": bcy2,
                    "vx": math.cos(a)*5, "vy": math.sin(a)*5,
                    "dmg": 10, "r": 8,
                })

        # NOVA DE ZONE : toutes les 5s, 12 projectiles en étoile
        if now - self._nova_timer > 5000:
            self._nova_timer = now
            bcx2, bcy2 = self.center()
            for i in range(12):
                a = i * math.pi / 6
                # Nova lente mais large
                self.projectiles.append({
                    "x": bcx2, "y": bcy2,
                    "vx": math.cos(a)*3.5, "vy": math.sin(a)*3.5,
                    "dmg": 18, "r": 14,
                })
            # Deuxième vague décalée (ring intérieur)
            for i in range(6):
                a = i * math.pi / 3 + math.pi/6
                self.projectiles.append({
                    "x": bcx2, "y": bcy2,
                    "vx": math.cos(a)*6, "vy": math.sin(a)*6,
                    "dmg": 12, "r": 10,
                })

        self._move_proj()

    def take_damage(self, dmg):
        if self._shield_active:
            self._shield_hp -= dmg
            if self._shield_hp <= 0:
                self._shield_active = False
        else:
            self.hp -= dmg



#  BOSS 4 — NECROMANT  (invocateur + rafales)


class BossNecromant(BaseBoss):
    NAME = "Necromant"; COLOR = (20, 100, 20); OUTLINE = (10, 60, 10)
    MAX_HP = 700; SIZE = 65
    MAX_SUMMONS = 10

    def __init__(self, px, py):
        super().__init__(px, py)
        self._summon_timer   = 0
        self._teleport_timer = 0
        self._volley_timer   = 0
        self.summon_count    = 0

    def update(self, pcx, pcy, now, gs):
        # Téléportation toutes les 6s
        if now - self._teleport_timer > 6000:
            self._teleport_timer = now
            for _ in range(50):
                nx = random.randint(100, MAP_W-100)
                ny = random.randint(100, MAP_H-100)
                if math.hypot(nx-pcx, ny-pcy) > 350:
                    self.x, self.y = float(nx), float(ny)
                    break

        # Invocation toutes les 3s
        if now - self._summon_timer > 3000 and self.summon_count < self.MAX_SUMMONS:
            self._summon_timer = now
            from entities import BasicEnemy, FastEnemy
            for _ in range(3):
                cls = random.choice([BasicEnemy, FastEnemy])
                e = cls.spawn_at_border(pcx, pcy)
                if e:
                    gs.enemies.append(e)
                    self.summon_count += 1

        # Volée de projectiles toutes les 2s (5 projectiles)
        if now - self._volley_timer > 2000:
            self._volley_timer = now
            bcx, bcy = self.center()
            base_angle = math.atan2(pcy-bcy, pcx-bcx)
            for spread in (-0.4, -0.2, 0, 0.2, 0.4):
                a = base_angle + spread
                self.projectiles.append({
                    "x": bcx, "y": bcy,
                    "vx": math.cos(a)*6, "vy": math.sin(a)*6,
                    "dmg": 12, "r": 8,
                })

        self._move_proj()


#  BOSS 5 — TITAN  (tout + rage)


class BossTitan(BaseBoss):
    NAME = "TITAN"; COLOR = (180, 0, 180); OUTLINE = (100, 0, 100)
    MAX_HP = 2500; SIZE = 100

    def __init__(self, px, py):
        super().__init__(px, py)
        self._spiral_angle  = 0.0
        self._spiral_timer  = 0
        self._nova_timer    = 0
        self._charge_vx     = 0.0
        self._charge_vy     = 0.0
        self._charging      = False
        self._charge_timer  = 0
        self._retreat_timer = 0
        self._summon_timer  = 0
        self._rage          = False

    def update(self, pcx, pcy, now, gs):
        if not self._rage and self.hp <= self.MAX_HP * 0.5:
            self._rage = True

        speed = 3.5 if not self._rage else 6.0
        bcx, bcy = self.center()
        dist_to_player = math.hypot(pcx-bcx, pcy-bcy)

        # Charge (même correctif que Berserker)
        if self._charging:
            self.x += self._charge_vx
            self.y += self._charge_vy
            self.clamp()
            if now - self._charge_timer > 450:
                self._charging      = False
                self._retreat_timer = now
                self._push_away_from_player(pcx, pcy, min_dist=110)
        elif now - self._retreat_timer < 350:
            angle = math.atan2(bcy-pcy, bcx-pcx)
            self.x += math.cos(angle)*4; self.y += math.sin(angle)*4
            self.clamp()
        else:
            if dist_to_player > 120:
                self.move_toward(pcx, pcy, speed)
            else:
                orbit_angle = math.atan2(bcy-pcy, bcx-pcx) + 0.03
                self.x = pcx + math.cos(orbit_angle)*130 - self.SIZE/2
                self.y = pcy + math.sin(orbit_angle)*130 - self.SIZE/2
                self.clamp()

            if now - self._charge_timer > (1500 if self._rage else 2200) and dist_to_player > 130:
                self._charge_timer = now
                a = math.atan2(pcy-bcy, pcx-bcx)
                spd = 24 if self._rage else 18
                self._charge_vx = math.cos(a)*spd
                self._charge_vy = math.sin(a)*spd
                self._charging  = True

        # Spirale
        interval = 120 if self._rage else 250
        if now - self._spiral_timer > interval:
            self._spiral_timer = now
            self._spiral_angle += 0.45
            bcx2, bcy2 = self.center()
            arms = 8 if self._rage else 4
            for i in range(arms):
                a = self._spiral_angle + i*(2*math.pi/arms)
                self.projectiles.append({
                    "x": bcx2, "y": bcy2,
                    "vx": math.cos(a)*6, "vy": math.sin(a)*6,
                    "dmg": 15, "r": 10,
                })

        # Nova de zone toutes les 4s
        if now - self._nova_timer > 4000:
            self._nova_timer = now
            bcx2, bcy2 = self.center()
            count = 16 if self._rage else 10
            for i in range(count):
                a = i * 2*math.pi/count
                self.projectiles.append({
                    "x": bcx2, "y": bcy2,
                    "vx": math.cos(a)*4, "vy": math.sin(a)*4,
                    "dmg": 20, "r": 13,
                })

        # Invocation en rage
        if self._rage and now - self._summon_timer > 4000:
            self._summon_timer = now
            from entities import FastEnemy, RangedEnemy
            for _ in range(4):
                cls = random.choice([FastEnemy, RangedEnemy])
                e = cls.spawn_at_border(pcx, pcy)
                if e: gs.enemies.append(e)

        self._move_proj()



#  TABLE DES BOSS


BOSS_SEQUENCE = [
    BossBerserker,
    BossGolem,
    BossMage,
    BossNecromant,
    BossTitan,
]
