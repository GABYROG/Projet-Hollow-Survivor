"""entities.py — Toutes les entites du jeu."""

import math, random, pygame
from settings import (MAP_W, MAP_H, PLAYER_W, PLAYER_H, PLAYER_SPEED,
                      PLAYER_MAX_HP, ARROW_SPEED, BASKET_W, BASKET_H,
                      BASKET_HEAL, MAX_WEAPONS)



#  HITBOX


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = float(x),float(y),float(w),float(h)

    def collides(self, o):
        return (self.x < o.x+o.w and self.x+self.w > o.x and
                self.y < o.y+o.h and self.y+self.h > o.y)

    def center(self):
        return self.x+self.w/2, self.y+self.h/2

    def overlap(self, o):
        ox = min(self.x+self.w, o.x+o.w) - max(self.x, o.x)
        oy = min(self.y+self.h, o.y+o.h) - max(self.y, o.y)
        return ox, oy


#  PARTICULES


class Particle:
    __slots__ = ["x","y","vx","vy","life","max_life","size","color","glow"]

    def __init__(self, x, y, color, vx=None, vy=None, life=28, size=4, glow=False):
        self.x, self.y   = float(x), float(y)
        self.vx = vx if vx is not None else random.uniform(-2.5, 2.5)
        self.vy = vy if vy is not None else random.uniform(-3.5, 0.5)
        self.life = self.max_life = life
        self.size  = size
        self.color = color
        self.glow  = glow

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.12; self.vx *= 0.94
        self.life -= 1
        return self.life > 0

    def draw(self, surf, cam_x, cam_y):
        ratio = self.life / self.max_life
        alpha = int(255 * ratio)
        s     = max(1, int(self.size * ratio))
        sx    = int(self.x - cam_x); sy = int(self.y - cam_y)
        if not (-20 <= sx <= 1300 and -20 <= sy <= 740): return
        tmp = pygame.Surface((s*4, s*4), pygame.SRCALPHA)
        if self.glow:
            pygame.draw.circle(tmp, (*self.color[:3], alpha//3), (s*2,s*2), s*2)
        pygame.draw.circle(tmp, (*self.color[:3], alpha), (s*2,s*2), s)
        surf.blit(tmp, (sx-s*2, sy-s*2))


class DamageNumber:
    def __init__(self, x, y, value, crit=False, color=None):
        self.x, self.y = float(x), float(y)
        self.vy   = -2.2; self.life = 52
        self.value = value; self.crit = crit
        self.color = color or ((255,220,50) if crit else (255,255,255))

    def update(self):
        self.y += self.vy; self.vy *= 0.94; self.life -= 1
        return self.life > 0

    def draw(self, surf, cam_x, cam_y, font):
        a   = int(255 * self.life/52)
        txt = f"{'★' if self.crit else ''}{self.value}"
        f   = pygame.font.SysFont("Arial", 24 if self.crit else 18, bold=True)
        s   = f.render(txt, True, self.color)
        s.set_alpha(a)
        surf.blit(s, (int(self.x-cam_x-s.get_width()//2),
                      int(self.y-cam_y-s.get_height()//2)))



#  GEMME XP


class XPGem:
    # Rarete -> (couleur, valeur_xp, radius)
    TYPES = {
        "common":    ((60, 200, 255), 1,  5),
        "rare":      ((120, 80, 255), 3,  7),
        "epic":      ((220, 80, 255), 8,  9),
        "legendary": ((255,200,  50), 20, 11),
    }

    def __init__(self, x, y, rarity="common"):
        self.x, self.y  = float(x), float(y)
        self.rarity      = rarity
        self.color, self.xp, self.radius = self.TYPES[rarity]
        self.bob_offset  = random.uniform(0, math.pi*2)
        # Petite impulsion initiale
        a = random.uniform(0, math.pi*2)
        spd = random.uniform(1.5, 4.0)
        self.vx = math.cos(a)*spd; self.vy = math.sin(a)*spd

    def update(self):
        # Friction
        self.vx *= 0.88; self.vy *= 0.88
        self.x  += self.vx; self.y += self.vy


#  JOUEUR

class Player:
    def __init__(self):
        self.x, self.y     = float(MAP_W//2), float(MAP_H//2)
        self.speed         = PLAYER_SPEED
        self.max_hp        = float(PLAYER_MAX_HP)
        self.hp            = float(PLAYER_MAX_HP)
        self.move_left = self.move_right = self.move_up = self.move_down = False
        self.facing        = 1   # 1=droite -1=gauche

        # Armes automatiques actives (liste de wid, max MAX_WEAPONS)
        self.weapons          = ["epee"]
        self.weapon_timers    = {}   # {wid: ms}
        self.weapon_levels    = {}   # {wid: 0-4}
        self.weapon_mods      = {}
        self.unlocked_weapons = {"epee"}
        self.orbit_angles     = {}   # {wid: angle courant}

        # Stats
        self.bonus_dmg        = 0
        self.atk_speed_mult   = 1.0
        self.xp_mult          = 1.0
        self.pickup_radius    = 90.0
        self.regen_rate       = 0.0   # HP/s
        self.regen_accum      = 0.0
        self.crit_chance      = 0.05
        self.area_mult        = 1.0
        self.proj_speed_mult  = 1.0
        self.bleed_stacks     = {}   # {enemy_id: (dmg, end_ms)}
        self.poison_stacks    = {}

        # Etat visuel
        self.hit_flash        = 0
        self.invincible_ms    = 0   # timestamp fin invincibilite
        self.walk_cycle       = 0.0  # animation marche

    def hitbox(self):  return Rect(self.x, self.y, PLAYER_W, PLAYER_H)
    def center(self):  return self.x+PLAYER_W/2, self.y+PLAYER_H/2
    def is_alive(self): return self.hp > 0

    def move(self):
        dx = dy = 0.0
        if self.move_left:  dx -= 1.0
        if self.move_right: dx += 1.0
        if self.move_up:    dy -= 1.0
        if self.move_down:  dy += 1.0
        moving = dx != 0 or dy != 0
        if dx != 0 and dy != 0: dx *= 0.7071; dy *= 0.7071
        if dx != 0: self.facing = 1 if dx > 0 else -1
        self.x = max(0.0, min(self.x + dx*self.speed, float(MAP_W-PLAYER_W)))
        self.y = max(0.0, min(self.y + dy*self.speed, float(MAP_H-PLAYER_H)))
        if moving: self.walk_cycle += 0.25

    def take_damage(self, dmg, now_ms):
        if now_ms < self.invincible_ms: return False
        self.hp  -= dmg
        self.hit_flash     = 10
        self.invincible_ms = now_ms + 700
        return True

    def tick(self, now_ms, dt_s):
        if self.hit_flash > 0: self.hit_flash -= 1
        # Regen
        if self.regen_rate > 0:
            self.regen_accum += self.regen_rate * dt_s
            if self.regen_accum >= 1.0:
                heal = int(self.regen_accum)
                self.hp = min(self.max_hp, self.hp + heal)
                self.regen_accum -= heal

    def clamp(self):
        self.x = max(0.0, min(self.x, float(MAP_W-PLAYER_W)))
        self.y = max(0.0, min(self.y, float(MAP_H-PLAYER_H)))

    def add_weapon(self, wid):
        if wid not in self.weapons and len(self.weapons) < MAX_WEAPONS:
            self.weapons.append(wid)
            self.unlocked_weapons.add(wid)
            return True
        return False



#  ENNEMIS — classe de base


class BaseEnemy:
    HP=8; SPEED=2.8; DMG=1; ATK_CD=900; XP=1; SIZE=36
    COLOR=(200,55,55); OUTLINE=(140,25,25); LABEL=""
    KB_RESIST=1.0   # resistance au knockback (>1 = lourd)
    WORTH=1         # multiplicateur d'or

    def __init__(self, x, y):
        self.x, self.y   = float(x), float(y)
        self.hp          = self.HP
        self.last_atk    = 0
        self.projectiles = []
        self.flash       = 0
        self.bleed_end   = 0   # ms fin du saignement
        self.bleed_dmg   = 0
        self.poison_end  = 0
        self.poison_dmg  = 0

    def hitbox(self):
        s = self.SIZE
        return Rect(self.x, self.y, s, s)

    def center(self):
        s = self.SIZE
        return self.x+s/2, self.y+s/2

    def is_dead(self): return self.hp <= 0

    def take_hit(self, dmg, angle=0, force=0):
        self.hp    -= dmg
        self.flash  = 6
        if force > 0:
            self.x += math.cos(angle)*force/self.KB_RESIST
            self.y += math.sin(angle)*force/self.KB_RESIST
            self.clamp()

    def apply_bleed(self, dmg, end_ms):
        self.bleed_dmg = dmg; self.bleed_end = end_ms

    def apply_poison(self, dmg, end_ms):
        self.poison_dmg = dmg; self.poison_end = end_ms

    def clamp(self):
        s = self.SIZE
        self.x = max(0.0, min(self.x, float(MAP_W-s)))
        self.y = max(0.0, min(self.y, float(MAP_H-s)))

    def move_toward(self, tx, ty, spd_f=1.0):
        ecx,ecy = self.center(); dx,dy = tx-ecx,ty-ecy
        dist = math.hypot(dx,dy)
        if dist > 1:
            step = min(self.SPEED*spd_f, dist)
            self.x += dx/dist*step; self.y += dy/dist*step

    def tick_dots(self, now, gs):
        """Applique les dots (bleed/poison) chaque frame."""
        if self.bleed_end > now and now % 60 < 2:
            self.hp -= self.bleed_dmg
        if self.poison_end > now and now % 40 < 2:
            self.hp -= self.poison_dmg

    def update(self, pcx, pcy, now, gs, spd_f=1.0):
        self.move_toward(pcx, pcy, spd_f)
        if self.flash > 0: self.flash -= 1
        self.tick_dots(now, gs)

    @classmethod
    def spawn_at_border(cls, px, py):
        """Spawn sur les bords de l'ecran visible, loin du joueur."""
        from settings import WIDTH, HEIGHT
        for _ in range(200):
            angle = random.uniform(0, math.pi*2)
            dist  = random.uniform(480, 700)
            x = px + math.cos(angle)*dist
            y = py + math.sin(angle)*dist
            if 0 <= x <= MAP_W-cls.SIZE and 0 <= y <= MAP_H-cls.SIZE:
                return cls(float(x), float(y))
        return None


class BasicEnemy(BaseEnemy):
    HP=10; SPEED=2.8; DMG=8;  ATK_CD=900;  XP=1; SIZE=34
    COLOR=(200,55,55); OUTLINE=(140,25,25); KB_RESIST=1.0

class FastEnemy(BaseEnemy):
    HP=5;  SPEED=5.8; DMG=6;  ATK_CD=600;  XP=2; SIZE=22
    COLOR=(255,165,0); OUTLINE=(200,110,0); KB_RESIST=0.6; LABEL="⚡"

class TankEnemy(BaseEnemy):
    HP=60; SPEED=1.3; DMG=20; ATK_CD=1500; XP=6; SIZE=64
    COLOR=(70,70,200); OUTLINE=(40,40,140); KB_RESIST=5.0; LABEL="🛡"

class RangedEnemy(BaseEnemy):
    HP=8;  SPEED=1.6; DMG=0;  ATK_CD=1800; XP=3; SIZE=30
    COLOR=(150,50,220); OUTLINE=(100,20,170); KB_RESIST=0.8; LABEL="🏹"
    PREF_DIST=300; PROJ_SPD=5.5

    def update(self, pcx, pcy, now, gs, spd_f=1.0):
        if self.flash > 0: self.flash -= 1
        self.tick_dots(now, gs)
        ecx,ecy = self.center()
        dist = math.hypot(pcx-ecx, pcy-ecy)
        if dist < self.PREF_DIST-60:
            ang = math.atan2(ecy-pcy, ecx-pcx)
            self.x += math.cos(ang)*self.SPEED*spd_f
            self.y += math.sin(ang)*self.SPEED*spd_f
        elif dist > self.PREF_DIST+60:
            self.move_toward(pcx, pcy, spd_f)
        if now - self.last_atk >= self.ATK_CD:
            self.last_atk = now
            ang = math.atan2(pcy-ecy, pcx-ecx)
            spd = self.PROJ_SPD * spd_f
            self.projectiles.append({"x":ecx,"y":ecy,
                "vx":math.cos(ang)*spd,"vy":math.sin(ang)*spd,"dmg":12,"r":7})
        for p in self.projectiles:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]
        self.projectiles = [p for p in self.projectiles
                            if 0<=p["x"]<=MAP_W and 0<=p["y"]<=MAP_H]
        self.clamp()



#  PROJECTILE JOUEUR


class Projectile:
    def __init__(self, x, y, vx, vy, dmg, color=(255,220,80),
                 r=6, pierce=0, chain=0, explode=False):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.dmg   = dmg; self.color = color; self.r = r
        self.angle = math.atan2(vy, vx)
        self.pierce_left = pierce
        self.chain_left  = chain
        self.explode     = explode
        self.hit_ids     = set()

    def update(self, spd_f=1.0):
        self.x += self.vx*spd_f; self.y += self.vy*spd_f

    def hitbox(self): return Rect(self.x-self.r,self.y-self.r,self.r*2,self.r*2)
    def in_bounds(self): return 0<=self.x<=MAP_W and 0<=self.y<=MAP_H


#  PANIER DE SOIN


class Basket:
    def __init__(self, x, y):
        self.x, self.y = x, y; self.active = True

    def hitbox(self):
        return Rect(self.x-BASKET_W//2, self.y-BASKET_H//2, BASKET_W, BASKET_H)

    def try_heal(self, player):
        if self.active and player.hitbox().collides(self.hitbox()):
            player.hp = min(player.max_hp, player.hp + BASKET_HEAL)
            self.active = False
