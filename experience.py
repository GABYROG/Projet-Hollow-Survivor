"""experience.py — Gemmes XP au sol, niveaux, offres d'amelioration."""

import math, random
from entities import XPGem

# ── Seuils XP (formule : prev + 10 + lvl*5) ──
def _threshold(lvl):
    t = 0; step = 10
    for i in range(lvl):
        t += step; step += 5
    return t

# ── Rarete des cartes ──
RARITY_COMMON    = "Commun"
RARITY_RARE      = "Rare"
RARITY_EPIC      = "Epique"
RARITY_LEGENDARY = "Legendaire"

RARITY_COLORS = {
    RARITY_COMMON:    (120, 120, 140),
    RARITY_RARE:      (50,  120, 220),
    RARITY_EPIC:      (160,  50, 220),
    RARITY_LEGENDARY: (255, 180,  30),
}

RARITY_WEIGHTS = {
    RARITY_COMMON: 55, RARITY_RARE: 28,
    RARITY_EPIC: 13,   RARITY_LEGENDARY: 4,
}


class XPSystem:
    def __init__(self):
        self.xp            = 0
        self.level         = 0
        self.gems          = []   # XPGem sur la map
        self.pending_offer = None
        self.reroll_cost   = 50
        self._pending_levels = 0  # level-ups en attente

    # ── Gemmes ──
    def drop_gems(self, enemy):
        xp_val = getattr(enemy, "XP", 1)
        ecx, ecy = enemy.center()
        # 1 gemme par xp, rarete selon valeur
        for _ in range(max(1, xp_val//3 + 1)):
            if xp_val >= 6:   rarity = random.choices(["common","rare","epic"],    [40,45,15])[0]
            elif xp_val >= 3: rarity = random.choices(["common","rare"],            [60,40])[0]
            else:             rarity = "common"
            self.gems.append(XPGem(ecx, ecy, rarity))

    def update_pickup(self, player):
        """Deplace les gemmes vers le joueur si dans le rayon de pickup."""
        pcx, pcy  = player.center()
        radius    = player.pickup_radius
        attracted = []
        remaining = []
        for gem in self.gems:
            gem.update()
            dx = pcx - gem.x; dy = pcy - gem.y
            dist = math.hypot(dx, dy)
            if dist < radius:
                attracted.append(gem)
            elif dist < radius * 3:
                # Aimantation progressive
                spd = (1 - dist/(radius*3)) * 8
                gem.x += dx/dist*spd; gem.y += dy/dist*spd
                remaining.append(gem)
            else:
                remaining.append(gem)

        # Collecte
        leveled = False
        for gem in attracted:
            gained = int(gem.xp * player.xp_mult)
            self.xp += gained
            nxt = _threshold(self.level + 1)
            while self.xp >= nxt:
                self.level += 1
                self._pending_levels += 1
                nxt = _threshold(self.level + 1)
                leveled = True

        self.gems = remaining

        if self._pending_levels > 0 and self.pending_offer is None:
            self.pending_offer = self._make_offer(player)
            self._pending_levels -= 1
            return True
        return leveled

    def progress(self):
        prev = _threshold(self.level)
        nxt  = _threshold(self.level + 1)
        return self.xp - prev, nxt - prev

    def reroll(self, player):
        if player.hp < self.reroll_cost: return False  # pas d'or ici, on utilise hp fictif
        self.pending_offer = self._make_offer(player)
        self.reroll_cost   = min(500, int(self.reroll_cost * 1.8))
        return True

    def apply_choice(self, idx, player, gs):
        if not self.pending_offer or idx >= len(self.pending_offer):
            return
        upg = self.pending_offer[idx]
        _apply_upgrade(upg, player, gs)
        if upg.get("type") == "weapon_upgrade":
            wid = upg["weapon"]
            player.weapon_levels[wid] = player.weapon_levels.get(wid, 0) + 1
        elif upg.get("type") == "item":
            from items import apply_item_upgrade
            apply_item_upgrade(upg["item_id"], player, gs)
        self.pending_offer = None
        if self._pending_levels > 0:
            self.pending_offer = self._make_offer(player)
            self._pending_levels -= 1

    # ── Generation d'offre ──
    def _make_offer(self, player):
        from upgrades import STAT_UPGRADES, WEAPON_UPGRADES, NEW_WEAPON_UPGRADES
        from items import get_item_upgrades
        pool = []; seen = set()

        def push(upg, rarity=None):
            if upg["id"] in seen: return
            seen.add(upg["id"])
            e = dict(upg)
            e["rarity"] = rarity or random.choices(
                list(RARITY_WEIGHTS), weights=list(RARITY_WEIGHTS.values()))[0]
            pool.append(e)

        # 1. Amelioration arme active (toutes celles equipees)
        for wid in player.weapons:
            lvl = player.weapon_levels.get(wid, 0)
            if lvl < 5 and wid in WEAPON_UPGRADES:
                rar = [RARITY_COMMON,RARITY_RARE,RARITY_EPIC,RARITY_EPIC,RARITY_LEGENDARY][lvl]
                for c in WEAPON_UPGRADES[wid][lvl]:
                    push(dict(c, type="weapon_upgrade", weapon=wid, level=lvl+1), rar)

        # 2. Nouvelles armes non debloquees (si slot libre)
        from settings import MAX_WEAPONS
        if len(player.weapons) < MAX_WEAPONS:
            locked = [nw for nw in NEW_WEAPON_UPGRADES
                      if nw["weapon_id"] not in player.unlocked_weapons]
            random.shuffle(locked)
            for nw in locked[:2]:
                push(nw, RARITY_RARE)

        # 3. Items passifs — passes depuis gs via player._item_sys
        item_sys = getattr(player, "_item_sys", None)
        item_offers = get_item_upgrades(item_sys) if item_sys else get_item_upgrades(None)
        for io in item_offers:
            push(io)

        # 4. Stats
        stats = list(STAT_UPGRADES); random.shuffle(stats)
        for s in stats: push(s)

        random.shuffle(pool)
        result = pool[:3]
        while len(result) < 3:
            from upgrades import STAT_UPGRADES as SA
            fb = dict(random.choice(SA), rarity=RARITY_COMMON)
            if fb["id"] not in {r["id"] for r in result}:
                result.append(fb)
        return result



#  APPLICATION DES AMELIORATIONS


def _apply_upgrade(upg, player, gs):
    t = upg.get("type","stat")
    if t == "stat":
        upg["apply"](player)
    elif t == "new_weapon":
        player.add_weapon(upg["weapon_id"])
    elif t == "weapon_upgrade":
        upg["apply"](player)
