"""
items.py — Systeme d'items passifs style Hollow Survivors.

Chaque item a 5 niveaux. Certains ont des effets persistants (stats),
d'autres ont des effets actifs geres par ItemSystem.tick().

Structure d'un item :
  {
    "id":    str unique
    "nom":   str
    "desc":  str  (description niveau actuel)
    "icon":  str  (emoji)
    "color": tuple RGB
    "level": int  (0-4, niveau actuel)
    "type":  "passive" | "active" | "on_kill" | "on_hit" | "aura"
  }
"""

import math, random, pygame
from settings import MAP_W, MAP_H


#  DEFINITIONS DES ITEMS  (5 niveaux chacun)


ITEM_DEFS = {

    "dent_vampire": {
        "nom": "Dent de Vampire", "icon": "🦷", "color": (200,40,80),
        "type": "on_hit",
        "desc_levels": [
            "Recupere 1/4 des degats infliges (CD 0.5s)",
            "Recupere 1/4 des degats infliges (CD 0.25s)",
            "Recupere 1/2 des degats infliges (CD 0.25s)",
            "Recupere 1/2 des degats infliges (CD 0.125s)",
            "Recupere TOUS les degats infliges (CD 0.125s)",
        ],
        # ratio de soin / cooldown en ms
        "heal_ratio": [0.25, 0.25, 0.50, 0.50, 1.0],
        "heal_cd_ms": [500,  250,  250,  125,  125],
    },

    "balle_collante": {
        "nom": "Balle Collante", "icon": "🔵", "color": (80,180,255),
        "type": "on_hit",
        "desc_levels": [
            "Ralentit les ennemis touches de 10%",
            "Ralentit les ennemis touches de 30%",
            "Ralentit les ennemis touches de 40%",
            "Ralentit les ennemis touches de 60%",
            "Ralentit les ennemis touches de 70%",
        ],
        "slow_ratio": [0.10, 0.30, 0.40, 0.60, 0.70],
        "slow_dur_ms": 1500,
    },

    "cercle_ombre": {
        "nom": "Cercle d'Ombre", "icon": "⭕", "color": (80,0,160),
        "type": "aura",
        "desc_levels": [
            "Aura : 100px, 2 degats / 0.5s",
            "Aura : 150px, 3 degats / 0.25s",
            "Aura : 150px, 4 degats / 0.25s",
            "Aura : 200px, 5 degats / 0.125s",
            "Aura : 200px, 5 degats / 0.125s + soin 1HP/2s",
        ],
        "radius":   [100, 150, 150, 200, 200],
        "damage":   [2,   3,   4,   5,   5],
        "tick_ms":  [500, 250, 250, 125, 125],
        "regen":    [0,   0,   0,   0,   1],   # HP/2s au niveau 5
    },

    "phaseur_casse": {
        "nom": "Phaseur Casse", "icon": "💠", "color": (120,200,255),
        "type": "active",
        "desc_levels": [
            "Invincible 3s toutes les 30s",
            "Invincible 4s toutes les 25s",
            "Invincible 4s toutes les 20s",
            "Invincible 4s toutes les 15s",
            "Invincible 5s toutes les 15s",
        ],
        "invinc_ms":  [3000, 4000, 4000, 4000, 5000],
        "cd_ms":      [30000,25000,20000,15000,15000],
    },

    "armure_plaque": {
        "nom": "Armure de Plaque", "icon": "🛡", "color": (160,160,180),
        "type": "passive",
        "desc_levels": [
            "Reduit les degats subis de 10%",
            "Reduit les degats subis de 20%",
            "Reduit les degats subis de 30%",
            "Reduit les degats subis de 40%",
            "Reduit les degats subis de 50%",
        ],
        "dmg_reduction": [0.10, 0.20, 0.30, 0.40, 0.50],
    },

    "cardio": {
        "nom": "Cardio-Accelerateur", "icon": "❤‍🔥", "color": (255,80,40),
        "type": "passive",   # bonus calcule chaque frame
        "desc_levels": [
            "+10% degats par tranche de 10% HP manquant",
            "+20% degats par tranche de 10% HP manquant",
            "+30% degats par tranche de 10% HP manquant",
            "+50% degats par tranche de 10% HP manquant",
            "+70% degats par tranche de 10% HP manquant",
        ],
        "ratio_per_tenth": [0.10, 0.20, 0.30, 0.50, 0.70],
    },

    "chaussures_sang": {
        "nom": "Chaussures Assoiffees", "icon": "👟", "color": (200,50,50),
        "type": "on_kill",
        "desc_levels": [
            "+10% vitesse pendant 3s apres un kill",
            "+20% vitesse pendant 3s apres un kill",
            "+20% vitesse pendant 4s apres un kill",
            "+30% vitesse pendant 4s apres un kill",
            "+40% vitesse pendant 4s apres un kill",
        ],
        "speed_bonus": [0.10, 0.20, 0.20, 0.30, 0.40],
        "dur_ms":      [3000, 3000, 4000, 4000, 4000],
    },

    "barriere_sang": {
        "nom": "Barriere Sanguinolente", "icon": "🩸", "color": (160,20,20),
        "type": "on_kill",
        "desc_levels": [
            "-10% degats recus pendant 2s apres un kill",
            "-20% degats recus pendant 2s apres un kill",
            "-20% degats recus pendant 3s apres un kill",
            "-30% degats recus pendant 3s apres un kill",
            "-40% degats recus pendant 4s apres un kill",
        ],
        "dmg_reduc":  [0.10, 0.20, 0.20, 0.30, 0.40],
        "dur_ms":     [2000, 2000, 3000, 3000, 4000],
    },

    "lame_brulante": {
        "nom": "Lame Brulante", "icon": "🔥", "color": (255,140,20),
        "type": "on_kill",
        "desc_levels": [
            "+10% degats pendant 3s apres un kill",
            "+10% degats pendant 4s apres un kill",
            "+30% degats pendant 4s apres un kill",
            "+50% degats pendant 4s apres un kill",
            "+70% degats pendant 6s apres un kill",
        ],
        "dmg_bonus": [0.10, 0.10, 0.30, 0.50, 0.70],
        "dur_ms":    [3000, 4000, 4000, 4000, 6000],
    },

    "grimoire": {
        "nom": "Grimoire Ancien", "icon": "📖", "color": (100,60,200),
        "type": "active",   # tire automatiquement
        "desc_levels": [
            "Toutes les 3s : 2 projectiles vers l'ennemi le plus proche (x0.5 degats)",
            "Toutes les 2s : 2 projectiles (x0.5 degats)",
            "Toutes les 2s : 2 projectiles (x1 degat)",
            "Toutes les 1.5s : 2 projectiles (x1.5 degats)",
            "Toutes les 1s : 3 projectiles (x1.5 degats)",
        ],
        "cd_ms":       [3000, 2000, 2000, 1500, 1000],
        "proj_count":  [2,    2,    2,    2,    3],
        "dmg_ratio":   [0.5,  0.5,  1.0,  1.5,  1.5],
    },

    "boule_feu": {
        "nom": "Boule de Feu", "icon": "🔮", "color": (255,100,20),
        "type": "active",   # orbite temporaire avec cooldown
        "desc_levels": [
            "Orbite 80px : 2 degats, dure 4s, CD 12s",
            "Orbite 80px : 2 degats, dure 6s, CD 12s",
            "Orbite 80px : 3 degats, dure 8s, CD 12s",
            "Orbite 80px : 3 degats, dure 10s, CD 12s",
            "Orbite 80px : 4 degats, dure 12s, CD 12s",
        ],
        "damage":   [2,     2,     3,     3,     4],
        "dur_ms":   [4000,  6000,  8000,  10000, 12000],
        "cd_ms":    [12000, 12000, 12000, 12000, 12000],
        "orbit_r":  80,
        "orbit_spd": math.pi,  # rad/s → 2s par tour
    },

    "sablier_brise": {
        "nom": "Sablier Brise", "icon": "⏳", "color": (255,220,100),
        "type": "passive",
        "desc_levels": [
            "Reduit tous les cooldowns de 10%",
            "Reduit tous les cooldowns de 20%",
            "Reduit tous les cooldowns de 30%",
            "Reduit tous les cooldowns de 40%",
            "Reduit tous les cooldowns de 60%",
        ],
        "cd_reduction": [0.10, 0.20, 0.30, 0.40, 0.60],
    },

    "goutte_jouvence": {
        "nom": "Goutte de Jouvence", "icon": "💧", "color": (100,220,255),
        "type": "passive",
        "desc_levels": [
            "1 revie : restaure 20% HP",
            "2 revies (sans rechargement) : 20% HP",
            "2 revies (rechargement) : 20% HP",
            "2 revies (sans rechargement) : 40% HP",
            "2 revies (rechargement) : 60% HP",
        ],
        "revive_count":  [1, 2, 2, 2, 2],
        "heal_pct":      [0.20, 0.20, 0.20, 0.40, 0.60],
        "resets":        [False, False, True, False, True],
    },

    "bouclier_phenix": {
        "nom": "Bouclier du Phoenix", "icon": "🦅", "color": (255,160,40),
        "type": "on_hit",
        "desc_levels": [
            "Renvoie 25% des degats recus (zone 60px), -5% degats recus",
            "Renvoie 50% des degats recus (zone 60px), -10% degats recus",
            "Renvoie 50% des degats recus (zone 80px), -15% degats recus",
            "Renvoie 100% des degats recus (zone 80px), -20% degats recus",
            "Renvoie 125% des degats recus (zone 100px), -30% degats recus",
        ],
        "reflect_ratio": [0.25, 0.50, 0.50, 1.00, 1.25],
        "reflect_r":     [60,   60,   80,   80,   100],
        "dmg_reduction": [0.05, 0.10, 0.15, 0.20, 0.30],
    },

    "sou_fetiche": {
        "nom": "Sou Fetiche", "icon": "🪙", "color": (255,200,0),
        "type": "passive",
        "desc_levels": [
            "Pieces gagnees x1.5",
            "Pieces gagnees x1.6",
            "Pieces gagnees x1.8",
            "Pieces gagnees x1.9",
            "Pieces gagnees x2",
        ],
        "gold_mult": [1.5, 1.6, 1.8, 1.9, 2.0],
    },

    "viseur_fele": {
        "nom": "Viseur Fele", "icon": "🎯", "color": (180,255,180),
        "type": "passive",
        "desc_levels": [
            "+10px de portee",
            "+15px de portee",
            "+20px de portee",
            "+30px de portee",
            "+60px de portee",
        ],
        "range_bonus": [10, 15, 20, 30, 60],
    },

    "cape_regenerante": {
        "nom": "Cape Regenerante", "icon": "🧣", "color": (80,200,120),
        "type": "passive",
        "desc_levels": [
            "Regenere 5% HP/s",
            "Regenere 7% HP/s",
            "Regenere 10% HP/s",
            "Regenere 12% HP/s",
            "Regenere 15% HP toutes les 0.5s",
        ],
        "regen_pct":  [0.05, 0.07, 0.10, 0.12, 0.15],
        "regen_cd_ms":[1000, 1000, 1000, 1000, 500],
    },
}



#  SYSTEME D'ITEMS (attache au player)


class ItemSystem:
    """Gere tous les items passifs equipes par le joueur."""

    def __init__(self):
        # {item_id: level (0-4)}
        self.equipped: dict[str,int] = {}

        # Timers internes
        self._timers:  dict[str,int] = {}   # {key: timestamp_ms}

        # Etats temporaires (on_kill / phaseur)
        self.speed_boost_end    = 0     # ms
        self.speed_boost_ratio  = 0.0
        self.dmg_reduc_end      = 0     # ms (barriere)
        self.dmg_reduc_ratio    = 0.0
        self.dmg_boost_end      = 0     # ms (lame brulante)
        self.dmg_boost_ratio    = 0.0
        self.invincible_end     = 0     # ms (phaseur)

        # Boule de feu : orbite temporaire
        self.fireball_active    = False
        self.fireball_end       = 0
        self.fireball_angle     = 0.0

        # Revies restants
        self.revives_left       = 0
        self.revive_heal_pct    = 0.0
        self.revive_resets      = False

        # Dent de vampire : timer de soin
        self._vamp_cd_end       = 0

        # Cercle d'ombre : timer de tick
        self._aura_tick_end     = 0
        self._aura_regen_end    = 0

        # Grimoire : timer de tir
        self._grimoire_end      = 0

        # Boule de feu : cooldown
        self._fireball_cd_end   = 0

        # Slowness sur ennemis {enemy_id: (slow_ratio, end_ms)}
        self.slowed_enemies: dict[int, tuple] = {}

        # Malus sang (munitions sanglantes — si jamais ajoute)
        self.self_dmg_ratio = 0.0

    def has(self, item_id) -> bool:
        return item_id in self.equipped

    def level(self, item_id) -> int:
        return self.equipped.get(item_id, -1)

    def add_or_upgrade(self, item_id):
        cur = self.equipped.get(item_id, -1)
        if cur < 4:
            self.equipped[item_id] = cur + 1
            self._on_equip(item_id, cur+1)

    def _on_equip(self, item_id, level):
        """Applique les effets one-shot a l'equipement."""
        defn = ITEM_DEFS.get(item_id, {})
        if item_id == "goutte_jouvence":
            self.revives_left   = defn["revive_count"][level]
            self.revive_heal_pct= defn["heal_pct"][level]
            self.revive_resets  = defn["resets"][level]

    # ── Tick principal (appele chaque frame depuis physics.py) ──

    def tick(self, player, enemies, gs, now: int, dt_s: float):
        """Met a jour tous les effets actifs et auras."""
        self._tick_aura(player, enemies, gs, now)
        self._tick_grimoire(player, enemies, gs, now)
        self._tick_fireball(player, enemies, gs, now, dt_s)
        self._tick_phaseur(player, now)
        self._tick_cape(player, now)
        self._update_slowness(enemies, now)

    # ── Aura (cercle d'ombre) ──

    def _tick_aura(self, player, enemies, gs, now):
        if not self.has("cercle_ombre"): return
        lvl  = self.level("cercle_ombre")
        defn = ITEM_DEFS["cercle_ombre"]
        r    = defn["radius"][lvl]
        dmg  = defn["damage"][lvl]
        tick = defn["tick_ms"][lvl]

        if now >= self._aura_tick_end:
            self._aura_tick_end = now + tick
            pcx, pcy = player.center()
            dead = []
            for i, e in enumerate(enemies):
                ecx, ecy = e.center()
                if math.hypot(ecx-pcx, ecy-pcy) <= r:
                    e.take_hit(dmg, math.atan2(ecy-pcy,ecx-pcx), 0)
                    if e.is_dead(): dead.append(i)
            for i in reversed(dead):
                from physics import _kill_enemy
                _kill_enemy(gs, i)

        # Regen niveau 5
        regen = defn["regen"][lvl]
        if regen > 0 and now >= self._aura_regen_end:
            self._aura_regen_end = now + 2000
            player.hp = min(player.max_hp, player.hp + regen)

    # ── Grimoire ──

    def _tick_grimoire(self, player, enemies, gs, now):
        if not self.has("grimoire"): return
        lvl  = self.level("grimoire")
        defn = ITEM_DEFS["grimoire"]
        if now < self._grimoire_end: return
        self._grimoire_end = now + defn["cd_ms"][lvl]

        if not enemies: return
        target = min(enemies, key=lambda e: math.hypot(
            *[a-b for a,b in zip(e.center(), player.center())]))
        ecx,ecy = target.center()
        pcx,pcy = player.center()
        base_dmg = max(1, int(player.bonus_dmg * defn["dmg_ratio"][lvl] + 4))
        count    = defn["proj_count"][lvl]
        from entities import Projectile
        for k in range(count):
            spread = (k - (count-1)/2) * 0.15
            angle  = math.atan2(ecy-pcy, ecx-pcx) + spread
            vx     = math.cos(angle)*14
            vy     = math.sin(angle)*14
            gs.projectiles.append(Projectile(pcx,pcy,vx,vy,base_dmg,
                                             (120,80,255),7))

    # ── Boule de feu ──

    def _tick_fireball(self, player, enemies, gs, now, dt_s):
        if not self.has("boule_feu"): return
        lvl  = self.level("boule_feu")
        defn = ITEM_DEFS["boule_feu"]

        # Activation
        if not self.fireball_active and now >= self._fireball_cd_end:
            self.fireball_active = True
            self.fireball_end    = now + defn["dur_ms"][lvl]
            self._fireball_cd_end = now + defn["dur_ms"][lvl] + defn["cd_ms"][lvl]

        if not self.fireball_active:
            return
        if now >= self.fireball_end:
            self.fireball_active = False
            return

        # Rotation
        self.fireball_angle += defn["orbit_spd"] * dt_s
        pcx,pcy = player.center()
        r   = defn["orbit_r"]
        fx  = pcx + math.cos(self.fireball_angle)*r
        fy  = pcy + math.sin(self.fireball_angle)*r
        fb  = __import__("entities").Rect(fx-10,fy-10,20,20)
        dmg = defn["damage"][lvl]
        dead = []
        for i,e in enumerate(enemies):
            if fb.collides(e.hitbox()):
                e.take_hit(dmg, self.fireball_angle, 5)
                if e.is_dead(): dead.append(i)
        for i in reversed(dead):
            from physics import _kill_enemy
            _kill_enemy(gs, i)

    # ── Phaseur ──

    def _tick_phaseur(self, player, now):
        if not self.has("phaseur_casse"): return
        lvl  = self.level("phaseur_casse")
        defn = ITEM_DEFS["phaseur_casse"]
        key  = "phaseur_last"
        last = self._timers.get(key, 0)
        if now - last >= defn["cd_ms"][lvl]:
            self._timers[key] = now
            self.invincible_end = now + defn["invinc_ms"][lvl]
            # Flash visuel
            player.hit_flash = 0

    # ── Cape regenerante ──

    def _tick_cape(self, player, now):
        if not self.has("cape_regenerante"): return
        lvl  = self.level("cape_regenerante")
        defn = ITEM_DEFS["cape_regenerante"]
        key  = "cape_last"
        last = self._timers.get(key, 0)
        if now - last >= defn["regen_cd_ms"][lvl]:
            self._timers[key] = now
            regen = player.max_hp * defn["regen_pct"][lvl]
            player.hp = min(player.max_hp, player.hp + regen)

    # ── Ralentissement ──

    def _update_slowness(self, enemies, now):
        self.slowed_enemies = {eid:(r,e) for eid,(r,e)
                               in self.slowed_enemies.items() if e > now}


    #  CALLBACKS EXTERIEURS


    def on_hit_enemy(self, player, enemy, dmg_dealt, now):
        """Appele par physics quand le joueur touche un ennemi."""
        # Dent de vampire
        if self.has("dent_vampire") and now >= self._vamp_cd_end:
            lvl  = self.level("dent_vampire")
            defn = ITEM_DEFS["dent_vampire"]
            heal = dmg_dealt * defn["heal_ratio"][lvl]
            player.hp = min(player.max_hp, player.hp + heal)
            self._vamp_cd_end = now + defn["heal_cd_ms"][lvl]

        # Balle collante
        if self.has("balle_collante"):
            lvl  = self.level("balle_collante")
            slow = ITEM_DEFS["balle_collante"]["slow_ratio"][lvl]
            dur  = ITEM_DEFS["balle_collante"]["slow_dur_ms"]
            self.slowed_enemies[id(enemy)] = (slow, now + dur)
            enemy.SPEED = max(0.3, enemy.__class__.SPEED * (1 - slow))

        # Bouclier du phoenix : renvoie degats
        if self.has("bouclier_phenix"):
            lvl    = self.level("bouclier_phenix")
            defn   = ITEM_DEFS["bouclier_phenix"]
            # sera gere dans on_player_hit pour les degats reçus

    def on_player_hit(self, player, dmg, enemies, gs, now):
        """Appele quand le joueur prend des degats (avant application)."""
        actual_dmg = dmg

        # Armure de plaque
        if self.has("armure_plaque"):
            lvl    = self.level("armure_plaque")
            reduc  = ITEM_DEFS["armure_plaque"]["dmg_reduction"][lvl]
            actual_dmg *= (1 - reduc)

        # Barriere sanguinolente (after kill)
        if now < self.dmg_reduc_end:
            actual_dmg *= (1 - self.dmg_reduc_ratio)

        # Phaseur actif
        if now < self.invincible_end:
            return 0   # invincible

        # Bouclier du phoenix
        if self.has("bouclier_phenix"):
            lvl    = self.level("bouclier_phenix")
            defn   = ITEM_DEFS["bouclier_phenix"]
            actual_dmg *= (1 - defn["dmg_reduction"][lvl])
            # Renvoie zone
            reflect_dmg = dmg * defn["reflect_ratio"][lvl]
            r = defn["reflect_r"][lvl]
            pcx, pcy = player.center()
            dead = []
            for i, e in enumerate(enemies):
                ecx,ecy = e.center()
                if math.hypot(ecx-pcx,ecy-pcy) <= r:
                    e.take_hit(int(reflect_dmg), math.atan2(ecy-pcy,ecx-pcx), 0)
                    if e.is_dead(): dead.append(i)
            for i in reversed(dead):
                from physics import _kill_enemy
                _kill_enemy(gs, i)

        return max(0, int(actual_dmg))

    def on_kill(self, player, now):
        """Appele quand le joueur tue un ennemi."""
        # Chaussures assoiffees
        if self.has("chaussures_sang"):
            lvl  = self.level("chaussures_sang")
            defn = ITEM_DEFS["chaussures_sang"]
            self.speed_boost_ratio = defn["speed_bonus"][lvl]
            self.speed_boost_end   = now + defn["dur_ms"][lvl]

        # Barriere sanguinolente
        if self.has("barriere_sang"):
            lvl  = self.level("barriere_sang")
            defn = ITEM_DEFS["barriere_sang"]
            self.dmg_reduc_ratio = defn["dmg_reduc"][lvl]
            self.dmg_reduc_end   = now + defn["dur_ms"][lvl]

        # Lame brulante
        if self.has("lame_brulante"):
            lvl  = self.level("lame_brulante")
            defn = ITEM_DEFS["lame_brulante"]
            self.dmg_boost_ratio = defn["dmg_bonus"][lvl]
            self.dmg_boost_end   = now + defn["dur_ms"][lvl]

        # Revie (rechargement)
        if (self.has("goutte_jouvence") and
                ITEM_DEFS["goutte_jouvence"]["resets"][self.level("goutte_jouvence")]):
            max_r = ITEM_DEFS["goutte_jouvence"]["revive_count"][self.level("goutte_jouvence")]
            self.revives_left = max_r

    def try_revive(self, player) -> bool:
        """Appele quand le joueur meurt. Retourne True si revie disponible."""
        if self.revives_left > 0:
            self.revives_left -= 1
            player.hp = max(1, int(player.max_hp * self.revive_heal_pct))
            player.invincible_ms = pygame.time.get_ticks() + 2000
            return True
        return False

    # ── Getters pour physics ──

    def get_speed_mult(self, now) -> float:
        base = 1.0
        if now < self.speed_boost_end:
            base += self.speed_boost_ratio
        return base

    def get_dmg_mult(self, player, now) -> float:
        mult = 1.0
        # Lame brulante
        if now < self.dmg_boost_end:
            mult += self.dmg_boost_ratio
        # Cardio
        if self.has("cardio"):
            lvl     = self.level("cardio")
            missing = max(0, 1 - player.hp/player.max_hp)
            tenths  = int(missing * 10)
            mult   += tenths * ITEM_DEFS["cardio"]["ratio_per_tenth"][lvl]
        # Sablier (applique sur CD, pas sur les degats, gere ailleurs)
        return mult

    def get_cd_mult(self) -> float:
        if not self.has("sablier_brise"): return 1.0
        lvl = self.level("sablier_brise")
        return 1.0 - ITEM_DEFS["sablier_brise"]["cd_reduction"][lvl]

    def get_gold_mult(self) -> float:
        if not self.has("sou_fetiche"): return 1.0
        return ITEM_DEFS["sou_fetiche"]["gold_mult"][self.level("sou_fetiche")]

    def is_invincible(self, now) -> bool:
        return now < self.invincible_end



#  GENERATION D'OFFRE D'ITEM POUR LE LEVEL-UP


def get_item_upgrades(item_system) -> list:
    """Retourne une liste d'ameliorations d'items disponibles."""
    offers = []
    for item_id, defn in ITEM_DEFS.items():
        cur_lvl = item_system.equipped.get(item_id, -1)
        if cur_lvl < 4:
            next_lvl = cur_lvl + 1
            offers.append({
                "id":      f"item_{item_id}_{next_lvl}",
                "nom":     defn["nom"] + (f" (niv.{next_lvl+1})" if cur_lvl >= 0 else " (nouveau)"),
                "desc":    defn["desc_levels"][next_lvl],
                "icon":    defn["icon"],
                "type":    "item",
                "item_id": item_id,
                "rarity":  ["Commun","Commun","Rare","Epique","Legendaire"][next_lvl],
                "apply":   lambda p, iid=item_id, gs=None: None,   # gere par apply_item_upgrade
            })
    random.shuffle(offers)
    return offers[:4]   # 4 items max dans le pool


def apply_item_upgrade(item_id, player, gs):
    """Applique un upgrade d'item."""
    gs.item_system.add_or_upgrade(item_id)
