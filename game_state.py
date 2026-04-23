"""
game_state.py — Classe GameState : conteneur de tout l'etat de la session.

Contient :
  - Les donnees persistantes (or, high score, ameliorations)
  - Les donnees de la partie en cours (joueur, ennemis, fleches, paniers)
  - L'etat de l'ecran courant (menu / weapon_select / playing / game_over)
"""

import pygame

from settings import WEAPON_ORDER, GOLD_GAIN_BASE
from entities import Player, Enemy, Arrow, Basket
from world    import MapData


class GameState:
    """
    Conteneur central de toute la logique de session.

    Etats possibles de screen_state :
      "menu"          — ecran principal avec ameliorations
      "weapon_select" — choix de l'arme avant la partie
      "playing"       — partie en cours
      "game_over"     — ecran de fin de partie
    """

    def __init__(self, map_data: MapData):
        self.map_data     = map_data
        self.screen_state = "menu"

        # ── Donnees persistantes (survivent entre les parties) ──
        self.high_score = 0
        self.gold       = 0
        self.gold_gain  = GOLD_GAIN_BASE

        # ── Etat de la partie courante ──
        self.player  : Player       = None
        self.enemies : list[Enemy]  = []
        self.arrows  : list[Arrow]  = []
        self.baskets : list[Basket] = []

        self.score           = 0
        self.last_spawn_time = 0

        # Layout de l'ecran de selection d'arme (pour detection clic souris)
        self.weapon_select_layout = None


    #  INITIALISATION D'UNE NOUVELLE PARTIE


    def start_new_game(self, weapon: str):
        """Remet a zero toutes les donnees de partie et lance avec l'arme choisie."""
        self.score = 0

        # Joueur
        self.player        = Player()
        self.player.weapon = weapon

        # Ennemis / fleches vides
        self.enemies = []
        self.arrows  = []

        # Paniers remis actifs
        self.baskets = [Basket(x, y) for x, y in self.map_data.basket_positions]

        # Premier ennemi et timer de spawn
        self._try_spawn_enemy()
        self.last_spawn_time = pygame.time.get_ticks()

        self.screen_state = "playing"


    #  SPAWN ENNEMIS


    def _try_spawn_enemy(self):
        """Essaie de faire apparaitre un ennemi loin du joueur."""
        enemy = Enemy.spawn_far_from(self.player.x, self.player.y)
        if enemy:
            self.enemies.append(enemy)

    def tick_spawn(self, now: int, interval: int, max_count: int):
        """Appele chaque frame — spawn un ennemi si le timer est ecoule."""
        if now - self.last_spawn_time >= interval and len(self.enemies) < max_count:
            self._try_spawn_enemy()
            self.last_spawn_time = now


    #  SCORE & OR


    def on_kill(self):
        """Appele a chaque mort d'ennemi."""
        self.score += 1
        self.gold  += self.gold_gain
        if self.score > self.high_score:
            self.high_score = self.score


    #  AMELIORATIONS (depuis le menu)

    def buy_speed(self, cost: int = 100) -> bool:
        if self.gold >= cost:
            self.gold -= cost
            # La vitesse sera appliquee au prochain Player cree
            Player.speed = getattr(Player, "speed", 10) + 2
            return True
        return False

    def buy_gold_gain(self, cost: int = 100) -> bool:
        if self.gold >= cost:
            self.gold     -= cost
            self.gold_gain += 5
            return True
        return False

    def buy_max_hp(self, cost: int = 100) -> bool:
        if self.gold >= cost:
            self.gold -= cost
            # Augmente le max HP pour les prochaines parties
            Player.max_hp = getattr(Player, "max_hp", 5) + 1
            return True
        return False


    #  CAMERA


    def get_camera(self) -> tuple[int, int]:
        """Retourne (cam_x, cam_y) centres sur le joueur."""
        from settings import WIDTH, HEIGHT
        cam_x = max(0, min(int(self.player.x) - WIDTH  // 2, MAP_W - WIDTH))
        cam_y = max(0, min(int(self.player.y) - HEIGHT // 2, MAP_H - HEIGHT))
        return cam_x, cam_y


# Import tardif pour eviter la reference circulaire
from settings import MAP_W, MAP_H
