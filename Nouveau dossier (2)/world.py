"""
world.py — Generation procedurale de la map et stockage des donnees statiques.

Classe principale : MapData
  - Genere tuiles, decors, positions de paniers (seed fixe = identique a chaque partie)
  - Construit la surface de sol pre-rendue (performances)
  - Expose les listes : trees, rocks, bushes, fences, basket_positions
"""

import random
import math
import pygame

from settings import (
    MAP_W, MAP_H, MAP_SEED,
    SAFE_RADIUS, BASKET_COUNT,
)


class MapData:
    """Contient toutes les donnees statiques generees de la map."""

    def __init__(self):
        self.grass_tiles     = []   # (x, y, color)
        self.path_tiles      = []   # (x, y, color)
        self.flower_tiles    = []   # (x, y, color)
        self.trees           = []   # (cx, cy, r_tronc, r_feuillage, color)
        self.rocks           = []   # (cx, cy, rx, ry, color)
        self.bushes          = []   # (cx, cy, r, color)
        self.fences          = []   # (x1, y1, x2, y2)
        self.basket_positions = []  # (x, y)

        self._generate()
        self.surface = self._build_surface()

    # ── Utilitaire ──

    def _in_safe_zone(self, x: float, y: float) -> bool:
        return math.hypot(x - MAP_W // 2, y - MAP_H // 2) < SAFE_RADIUS

    # ── Generation ──

    def _generate(self):
        rng = random.Random(MAP_SEED)
        sq  = 50

        # Sol
        grass_cols = [
            (122, 201, 87), (106, 176, 76), (114, 196, 78),
            (128, 208, 85), (104, 168, 69),
        ]
        path_col1 = (196, 164, 107)
        path_col2 = (184, 150,  90)

        for x in range(0, MAP_W, sq):
            for y in range(0, MAP_H, sq):
                if x // sq % 8 in (3, 4) or y // sq % 8 in (3, 4):
                    col = path_col1 if (x // sq + y // sq) % 2 == 0 else path_col2
                    self.path_tiles.append((x, y, col))
                else:
                    self.grass_tiles.append((x, y, rng.choice(grass_cols)))

        # Fleurs
        flower_cols = [
            (255, 107, 157), (255, 215, 0), (255, 140, 66),
            (201, 240, 255), (255, 255, 255),
        ]
        for _ in range(500):
            x = rng.randint(0, MAP_W - 4)
            y = rng.randint(0, MAP_H - 4)
            if not self._in_safe_zone(x, y):
                self.flower_tiles.append((x, y, rng.choice(flower_cols)))

        # Arbres
        tree_greens = [
            (45, 138, 45), (37, 110, 37), (58, 170, 58),
            (31, 107, 31), (76, 175, 76),
        ]
        for _ in range(80):
            cx = rng.randint(60, MAP_W - 60)
            cy = rng.randint(60, MAP_H - 60)
            if self._in_safe_zone(cx, cy):
                continue
            self.trees.append((
                cx, cy,
                rng.randint(7, 11),
                rng.randint(22, 34),
                rng.choice(tree_greens),
            ))

        # Rochers
        rock_cols = [
            (136, 136, 136), (119, 119, 119), (153, 153, 153),
            (106, 106, 106), (170, 170, 170),
        ]
        for _ in range(50):
            cx = rng.randint(40, MAP_W - 40)
            cy = rng.randint(40, MAP_H - 40)
            if self._in_safe_zone(cx, cy):
                continue
            self.rocks.append((
                cx, cy,
                rng.randint(12, 24),
                rng.randint(8, 18),
                rng.choice(rock_cols),
            ))

        # Buissons
        bush_cols = [
            (46, 125, 50), (56, 142, 60),
            (27,  94, 32), (76, 175, 80),
        ]
        for _ in range(60):
            cx = rng.randint(30, MAP_W - 30)
            cy = rng.randint(30, MAP_H - 30)
            if self._in_safe_zone(cx, cy):
                continue
            self.bushes.append((cx, cy, rng.randint(10, 20), rng.choice(bush_cols)))

        # Clotures
        for _ in range(40):
            x1 = rng.randint(50, MAP_W - 150)
            y1 = rng.randint(50, MAP_H - 50)
            if rng.random() > 0.5:
                self.fences.append((x1, y1, x1 + 100, y1))
            else:
                self.fences.append((x1, y1, x1, y1 + 100))

        # Paniers de fruits
        for _ in range(BASKET_COUNT):
            for _ in range(100):
                x = rng.randint(80, MAP_W - 80)
                y = rng.randint(80, MAP_H - 80)
                if not self._in_safe_zone(x, y):
                    self.basket_positions.append((float(x), float(y)))
                    break

    # ── Surface pre-rendue ──

    def _build_surface(self) -> pygame.Surface:
        """
        Dessine toutes les tuiles et fleurs sur une surface unique.
        Appele une seule fois au demarrage — evite de redessiner
        des centaines de rectangles a chaque frame.
        """
        print("Generation de la surface de map...")
        surf = pygame.Surface((MAP_W, MAP_H))
        sq   = 50
        for (x, y, col) in self.path_tiles + self.grass_tiles:
            pygame.draw.rect(surf, col, (x, y, sq, sq))
        for (x, y, col) in self.flower_tiles:
            pygame.draw.ellipse(surf, col, (x, y, 5, 5))
        print("Map generee.")
        return surf
    
class LavaMapData:
    

    def __init__(self):
        self.grass_tiles      = []   # (x, y, color)
        self.path_tiles       = []   # (x, y, color)
        self.flower_tiles     = []   # (x, y, color)
        self.trees            = []   # (cx, cy, r_tronc, r_feuillage, color)
        self.rocks            = []   # (cx, cy, rx, ry, color)
        self.bushes           = []   # (cx, cy, r, color)
        self.fences           = []   # (x1, y1, x2, y2)
        self.basket_positions = []   # (x, y)

        self._generate()
        self.surface = self._build_surface()

    # ── Utilitaire ──

    def _in_safe_zone(self, x: float, y: float) -> bool:
        return math.hypot(x - MAP_W // 2, y - MAP_H // 2) < SAFE_RADIUS

    # ── Generation ──

    def _generate(self):
        rng = random.Random(MAP_SEED + 1)
        sq  = 50

        # Sol basaltique 
        basalt_cols = [
            (30, 12, 5), (25, 10, 3), (35, 14, 6),
            (28, 11, 4), (22, 9, 2),
        ]
        # Chemins de lave 
        lava_col1 = (210, 70, 10)
        lava_col2 = (190, 55, 5)

        for x in range(0, MAP_W, sq):
            for y in range(0, MAP_H, sq):
                if x // sq % 8 in (3, 4) or y // sq % 8 in (3, 4):
                    col = lava_col1 if (x // sq + y // sq) % 2 == 0 else lava_col2
                    self.path_tiles.append((x, y, col))
                else:
                    self.grass_tiles.append((x, y, rng.choice(basalt_cols)))

        # Braises / etincelles 
        ember_cols = [
            (255, 80, 0), (255, 140, 0), (255, 200, 0),
            (200, 40, 0), (255, 60, 10),
        ]
        for _ in range(500):
            x = rng.randint(0, MAP_W - 4)
            y = rng.randint(0, MAP_H - 4)
            if not self._in_safe_zone(x, y):
                self.flower_tiles.append((x, y, rng.choice(ember_cols)))

        #  pics de roche
        rock_dark_cols = [
            (60, 20, 5), (50, 15, 3), (70, 25, 8),
            (45, 12, 2), (80, 30, 10),
        ]
        for _ in range(80):
            cx = rng.randint(60, MAP_W - 60)
            cy = rng.randint(60, MAP_H - 60)
            if self._in_safe_zone(cx, cy):
                continue
            self.trees.append((
                cx, cy,
                rng.randint(7, 11),
                rng.randint(22, 34),
                rng.choice(rock_dark_cols),
            ))

        # Rochers volcaniques 
        volcano_rock_cols = [
            (55, 18, 5), (45, 14, 3), (65, 22, 7),
            (40, 12, 2), (70, 25, 8),
        ]
        for _ in range(50):
            cx = rng.randint(40, MAP_W - 40)
            cy = rng.randint(40, MAP_H - 40)
            if self._in_safe_zone(cx, cy):
                continue
            self.rocks.append((
                cx, cy,
                rng.randint(12, 24),
                rng.randint(8, 18),
                rng.choice(volcano_rock_cols),
            ))

        # Flaques de lave 
        lava_pool_cols = [
            (210, 60, 5), (230, 80, 10),
            (190, 45, 3), (255, 100, 15),
        ]
        for _ in range(60):
            cx = rng.randint(30, MAP_W - 30)
            cy = rng.randint(30, MAP_H - 30)
            if self._in_safe_zone(cx, cy):
                continue
            self.bushes.append((cx, cy, rng.randint(10, 20), rng.choice(lava_pool_cols)))

        # Clotures 
        for _ in range(40):
            x1 = rng.randint(50, MAP_W - 150)
            y1 = rng.randint(50, MAP_H - 50)
            if rng.random() > 0.5:
                self.fences.append((x1, y1, x1 + 100, y1))
            else:
                self.fences.append((x1, y1, x1, y1 + 100))

        # Paniers de fruits 
        for _ in range(BASKET_COUNT):
            for _ in range(100):
                x = rng.randint(80, MAP_W - 80)
                y = rng.randint(80, MAP_H - 80)
                if not self._in_safe_zone(x, y):
                    self.basket_positions.append((float(x), float(y)))
                    break

    # ── Surface pre-rendue ──

    def _build_surface(self) -> pygame.Surface:
       
        print("Generation de la surface de map lave...")
        surf = pygame.Surface((MAP_W, MAP_H))
        sq   = 50
        for (x, y, col) in self.path_tiles + self.grass_tiles:
            pygame.draw.rect(surf, col, (x, y, sq, sq))
        for (x, y, col) in self.flower_tiles:
            pygame.draw.ellipse(surf, col, (x, y, 5, 5))
        print("Map lave generee.")
        return surf